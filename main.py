from flask import Flask, request
from functools import wraps
from os import environ
from re import compile
from json import dumps as jdumps
from pymongo import MongoClient
from random import choice

_re = compile('[^a-zA-Z0-9]+')

class LinkShortenerApi(Flask):
    def process_response(self, response):
        super(LinkShortenerApi, self).process_response(response)
        response.headers['Access-Control-Allow-Origin'] = "*"
        response.headers['Access-Control-Allow-Headers'] = "*"
        response.headers['Access-Control-Allow-Methods'] = "*"
        return response

class ApiKey:
    def __init__(self, id, key):
        self.id = id
        self.key = key

app = LinkShortenerApi(__name__)
conn = MongoClient(environ.get("MONGODB"))
db = conn.files
users_coll = db.users
links_coll = db.links

def auth_required(f):
	@wraps(f)
	def wrapped(*args, **kwargs):
		apikey = request.headers.get("Authorization")
		if not apikey:
			return jdumps({"success": False, "message": "Invalid api key"}), 401
		r = users_coll.find_one({"key": apikey})
		if not r:
			return jdumps({"success": False, "message": "Invalid api key"}), 401
		kwargs["apikey"] = ApiKey(id=r["id"], key=apikey)
		return f(*args, **kwargs)
	return wrapped

@app.route('/r/<string:code>')
@app.route('/read/<string:code>')
def read_code(code):
	code = _re.sub('', code)
	r = links_coll.find_one({"code": code})
	if not r:
		return jdumps({"success": False, "message": "Code does not exist"}), 404
	links_coll.update_one({"code": code}, {"$set": {"uses": r["uses"]+1}})
	return jdumps({"success": True, "url": r["url"]})

@app.route('/w/<string:code>', methods=["POST"])
@app.route('/write/<string:code>', methods=["POST"])
@auth_required
def write_code(apikey, code):
	code = _re.sub('', code)
	json = request.get_json(force=True)
	url = json.get("url")
	if not url:
		return jdumps({"success": False, "message": "Url must be in request body"}), 400
	links_coll.insert_one({"code": code, "url": url, "author": apikey.id, "uses": 0})
	return jdumps({"success": True, "code": code})

@app.route('/r', methods=["POST"])
@app.route('/random', methods=["POST"])
@auth_required
def write_random(apikey):
	code = id = "".join([choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(choice([5, 6]))])
	json = request.get_json(force=True)
	url = json.get("url")
	if not url:
		return jdumps({"success": False, "message": "Url must be in request body"}), 400
	links_coll.insert_one({"code": code, "url": url, "author": apikey.id, "uses": 0})
	return jdumps({"success": True, "code": code})

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5050)
