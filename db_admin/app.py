from flask import Flask, render_template, request, redirect, session, url_for, Response
from mariadb import connect, InterfaceError
from functools import wraps
from handler import *
from mysqldump import Dumper
from datetime import datetime
from os import environ

app = Flask(__name__)
app.secret_key = environ.get("SECRET_KEY")
app.config["DB_USER"] = environ.get("DB_USER")
app.config["DB_HOST"] = environ.get("DB_HOST")
app.config["DB_PASS"] = environ.get("DB_PASS")
app.config["DB_NAME"] = environ.get("DB_NAME")
app.config["ADMIN_LOGIN"] = environ.get("ADMIN_LOGIN")
app.config["ADMIN_PASSWORD"] = environ.get("ADMIN_PASSWORD")

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

def login_required(f):
	@wraps(f)
	def wrapped(*args, **kwargs):
		if 'authorised' not in session:
			return render_template('login.html')
		return f(*args, **kwargs)
	return wrapped

@app.context_processor
def inject_tables_and_counts():
	data = count_all(db.mysql)
	return dict(tables_and_counts=data)

@app.route("/debug")
def debug():
	return str(app.config)

@app.route('/')
@app.route('/index')
@login_required
def index():
	return render_template('index.html')

@app.route("/table/<string:table>")
@login_required
def table(table):
	data = fetch_all(db.mysql, table)
	columns = get_columns(db.mysql, table)
	return render_template('table.html', data=data, table_count=len(data), table_name=table, columns=[column[0] for column in columns])


@app.route('/edit/<string:table>/<string:act>/<int:modifier_id>', methods=['GET', 'POST'])
@login_required
def edit(table, modifier_id, act):
	columns = get_columns(db.mysql, table)
	columns = [column[0] for column in columns]
	if act == "add":
		return render_template('edit.html', data="", act="add", table_name=table, columns=enumerate(columns), mod=columns[0])
	else:
		data = fetch_one(db.mysql, table, "id", modifier_id)
	
		if data:
			return render_template('edit.html', data=data, act=act, table_name=table, columns=enumerate(columns), mod=columns[0])
		else:
			return 'Error loading #%s' % modifier_id

@app.route('/save', methods=['GET', 'POST'])
@login_required
def save():
	table = request.args.get('table')
	if request.method == 'POST':
		post_data = request.form.to_dict()
		if request.args['act'] == 'add':
			insert_one(db.mysql, table, post_data)
		elif request.args['act'] == 'edit':
			update_one(db.mysql, table, post_data, request.args['mod'], request.args['mod_value'])
	else:
		if request.args['act'] == 'delete':
			table = request.args['table']
			delete_one(db.mysql, table, request.args['mod'], request.args['mod_value'])
	return redirect(f"/table/{table}")

@app.route('/sql', methods=['GET', 'POST'])
@login_required
def sql():
	if request.method == 'POST':
		code = request.form.get("code", "")
		out = execute_sql(db.mysql, code)
		if "out" in out and out["out"]:
			return render_template("execute_sql.html", output="<br><br>".join(out["out"]), code=code)
		elif "error" in out:
			return render_template("execute_sql.html", error=out["error"], code=code)
		else:
			return render_template("execute_sql.html", output="Code executed but nothing returned.", code=code)
	return render_template("execute_sql.html")

@app.route('/dump')
def dump():
	if "yep" in request.args:
		try:
			with Dumper(host=app.config["DB_HOST"], port=3306, user=app.config["DB_USER"], password=app.config["DB_PASS"], database=app.config["DB_NAME"]) as d:
				return Response(d.dump(), mimetype="text/sql", headers={"Content-disposition": f"attachment; filename=dump_{datetime.now().strftime('%d.%m.%Y_%H.%M.%S')}.sql"})
		except Exception as e:
			return render_template("dump.html", error=str(e))
	return render_template("dump.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == "GET":
		if 'authorised' in session:
			return redirect(url_for('index'))
		else:
			error = request.args['error'] if 'error' in request.args else ''
			return render_template('login.html', error=error)
	else:
		try:
			login = request.form['login']
			password = request.form['password']

			if login == app.config["ADMIN_LOGIN"] and password == app.config["ADMIN_PASSWORD"]:
				session['authorised'] = 'authorised',
				session['login'] = login
				return redirect(url_for('index'))
			else:
				return redirect(url_for('login', error='Wrong Login or Password.'))
		
		except Exception as e:
			return render_template('login.html', error=str(e))

@app.route('/logout')
@login_required
def logout():
	session.clear()
	return redirect(url_for('login'))

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5051)
