from flask import Flask, request, abort
from mariadb import connect, InterfaceError
from functools import wraps
from os import environ
from re import compile
from json import dumps as jdumps

_re = compile('[^a-z0-9]+')

class LinkShortenerApi(Flask):
    def process_response(self, response):
        super(LinkShortenerApi, self).process_response(response)
        response.headers['Server'] = "BasaltMiner"
        response.headers['Access-Control-Allow-Origin'] = "*"
        response.headers['Access-Control-Allow-Headers'] = "*"
        response.headers['Access-Control-Allow-Methods'] = "*"
        response.headers['Content-Security-Policy'] = "connect-src *;"
        return response

app = LinkShortenerApi(__name__)

app.config["DB_USER"] = environ.get("DB_USER")
app.config["DB_HOST"] = environ.get("DB_HOST")
app.config["DB_PASS"] = environ.get("DB_PASS")
app.config["DB_NAME"] = environ.get("DB_NAME")
app.config["READ_KEY"] = environ.get("READ_KEY")
app.config["WRITE_KEY"] = environ.get("WRITE_KEY")

class Singleton(object):
    _instances = {}
    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cls] = instance
        return cls._instances[cls]

# MySQL
class DataBase(Singleton):
	_database = None

	@property
	def mysql(self):
		if not self._database:
			self._database = connect(host=app.config["DB_HOST"], port=3306, user=app.config["DB_USER"], password=app.config["DB_PASS"], database=app.config["DB_NAME"], autocommit=True)
		try:
			self._database.ping()
		except InterfaceError:
			self._database = connect(host=app.config["DB_HOST"], port=3306, user=app.config["DB_USER"], password=app.config["DB_PASS"], database=app.config["DB_NAME"], autocommit=True)
		return self._database

db = DataBase()

def login_required(access):
	def _login_required(f):
		@wraps(f)
		def wrapped(*args, **kwargs):
			if access not in ["READ", "WRITE"]:
				return abort(500)
			if "Authorization" not in request.headers:
				return abort(401)
			if request.headers["Authorization"] != app.config[f"{access}_KEY"]:
				return abort(403)
			return f(*args, **kwargs)
		return wrapped
	return _login_required

@app.route('/read/<string:code>')
@login_required("READ")
def read_code(code):
	code = _re.sub('', code)
	with db.mysql.cursor() as cur:
		cur.execute(f"SELECT `url` FROM `links` WHERE `code`=\"{code}\"")
		data = cur.fetchall()
		if not data:
			return abort(404)
		cur.execute(f"UPDATE `links` SET `uses`=`uses`+1 WHERE `code`=\"code\"")
	return jdumps({"url": data[0][0]})

@app.route('/write/<string:code>', methods=["POST"])
@login_required("WRITE")
def write_code(code):
	code = _re.sub('', code)
	url = request.form.get("url")
	if not url:
		return "url must be in form body", 400
	with db.mysql.cursor() as cur:
		cur.execute(f"SELECT `url` FROM `links` WHERE `code`=\"code\";")
		data = cur.fetchall()
		if data:
			return "Row with this code exists", 400
		cur.execute(f"INSERT INTO `links` (`code`, `url`) VALUES (\"{code}\", \"{url}\");")
	return "ok"

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5050)
