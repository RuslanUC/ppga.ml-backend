from quart import Quart, request, abort, render_template, redirect
from functools import wraps
from os import environ
from re import compile
from json import dumps as jdumps
from pymongo import MongoClient
from random import choice
from tgbot import Api
from io import BytesIO
from motor.motor_asyncio import AsyncIOMotorClient
from asyncio import get_event_loop
from magic import from_buffer
from time import time
from urllib.parse import urlparse

_re = compile('[^a-zA-Z0-9]+')

class PepegaApi(Quart):
    async def process_response(self, response, request_context):
        await super(PepegaApi, self).process_response(response, request_context)
        response.headers['Access-Control-Allow-Origin'] = "*"
        response.headers['Access-Control-Allow-Headers'] = "*"
        response.headers['Access-Control-Allow-Methods'] = "*"
        return response

class ApiKey:
    def __init__(self, id, key):
        self.id = id
        self.key = key

app = PepegaApi("Pepega")
api = Api(environ.get("TG_BOT_TOKEN"))

class ApiKey:
    def __init__(self, id, key):
        self.id = id
        self.key = key

@app.before_serving
async def startup():
    global conn, db, images_coll, users_coll, links_coll
    loop = get_event_loop()
    conn = AsyncIOMotorClient(environ.get("MONGODB"), io_loop=loop)
    db = conn.files
    images_coll = db.files
    users_coll = db.users
    links_coll = db.links

def auth(f):
    @wraps(f)
    async def wrapped(*args, **kwargs):
        if not (apikey := request.headers.get("Authorization")):
            return jdumps({"success": False, "message": "Invalid api key"}), 401
        if apikey == "demo":
            kwargs["apikey"] = ApiKey(id=0, key="demo")
            return await f(*args, **kwargs)
        if not (r := await users_coll.find_one({"key": apikey})):
            return jdumps({"success": False, "message": "Invalid api key"}), 401
        kwargs["apikey"] = ApiKey(id=r["id"], key=apikey)
        return await f(*args, **kwargs)
    return wrapped

def get_domain(f):
    @wraps(f)
    async def wrapped(*args, **kwargs):
        kwargs["domain"] = urlparse(request.url_root).hostname
        return await f(*args, **kwargs)
    return wrapped

def require_domain(domain):
    def _require_domain(f):
        @wraps(f)
        async def wrapped(*args, **kwargs):
            if domain != urlparse(request.url_root).hostname:
                return redirect("https://pepega.ml")
            return await f(*args, **kwargs)
        return wrapped
    return _require_domain

@app.route('/r/<string:code>')
@app.route('/read/<string:code>')
@require_domain("ppga.ml")
async def read_code(code):
	code = _re.sub('', code)
	r = await links_coll.find_one({"code": code})
	if not r:
		return jdumps({"success": False, "message": "Code does not exist"}), 404
	await links_coll.update_one({"code": code}, {"$set": {"uses": r["uses"]+1}})
	return jdumps({"success": True, "url": r["url"]})

@app.route('/w/<string:code>', methods=["POST"])
@app.route('/write/<string:code>', methods=["POST"])
@require_domain("ppga.ml")
@auth
async def write_code(apikey, code):
	code = _re.sub('', code)
	json = await request.get_json(force=True)
	url = json.get("url")
	if not url:
		return jdumps({"success": False, "message": "Url must be in request body"}), 400
	await links_coll.insert_one({"code": code, "url": url, "author": apikey.id, "uses": 0})
	return jdumps({"success": True, "code": code})

@app.route('/r', methods=["POST"])
@app.route('/random', methods=["POST"])
@require_domain("ppga.ml")
@auth
async def write_random(apikey):
	code = id = "".join([choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(choice([5, 6]))])
	json = await request.get_json(force=True)
	url = json.get("url")
	if not url:
		return jdumps({"success": False, "message": "Url must be in request body"}), 400
	await links_coll.insert_one({"code": code, "url": url, "author": apikey.id, "uses": 0})
	return jdumps({"success": True, "code": code})

@app.route("/upload", methods=["POST"])
@require_domain("i.ppga.ml")
@auth
async def upload(apikey):
    files = await request.files
    file = files.get("file")
    if not file:
        return abort(400)
    ch = file.read(1024)
    type = from_buffer(ch, mime=True)
    if not type.startswith("image/"):
        return jdumps({"success": False, "error": "File mime type must be image/*"})
    filename = file.filename
    try:
        file = await api.sendFile(BytesIO(ch+file.read()), 492693958)
    except Exception as e:
        return jdumps({"success": False, "error": str(e)})
    id = "".join([choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(choice([5, 6, 7, 8]))])
    await images_coll.insert_one({"id": id, "file_name": filename, "file_id": file.id, "uploader": apikey.id, "time": round(time()-1648771200)})
    return jdumps({"success": True, "id": id})

@app.route("/<string:code>")
@get_domain
async def download_or_redirect(code, domain):
    if domain == "i.ppga.ml":
        r = await images_coll.find_one({"id": code})
        if not r:
            return abort(404)
        file_id = r["file_id"]
        file_name = r["file_name"]
        file = await api.getFile(file_id)
        stream = file.getStream()
        type = await stream.__anext__()
        if "download" in request.args:
            headers = {"Content-Disposition": f"attachment; filename={file_name}"}
        else:
            headers = {"Content-Type": type}
        return stream, 200, headers
    elif domain == "ppga.ml":
        code = _re.sub('', code)
        r = await links_coll.find_one({"code": code})
        if not r:
            return jdumps({"success": False, "message": "Code does not exist"}), 404
        await links_coll.update_one({"code": code}, {"$set": {"uses": r["uses"]+1}})
        return redirect(r["url"])

@app.route("/")
@require_domain("i.ppga.ml")
async def index():
    return await render_template("index.html")

@app.route("/alive")
async def alive():
    return "Pepega alive"

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5050) 
