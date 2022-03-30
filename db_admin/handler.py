from sqlparse import split as sqlsplit
from prettytable import from_db_cursor

def fetch_all(mysql, table_name):
	with mysql.cursor() as cur:
		cur.execute(f"SELECT * FROM {table_name}")
		data = cur.fetchall()
	if data is None:
		return "Problem!"
	return data

def fetch_one(mysql, table_name, column, value):
	with mysql.cursor() as cur:
		cur.execute(f"SELECT * FROM {table_name} WHERE {column}=\"{value}\"")
		data = cur.fetchone()
	if data is None:
		return "Problem!"
	return data

def count_all(mysql):
	with mysql.cursor() as cur:
		cur.execute(f"SELECT `table_name`, `table_rows` FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = \"{mysql.database}\";")
		tables = cur.fetchall()
	return tables

def get_columns(mysql, table):
	with mysql.cursor() as cur:
		cur.execute(f"SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`=\"{mysql.database}\" AND `TABLE_NAME`=\"{table}\";")
		columns = cur.fetchall()
	return columns

def insert_one(mysql, table_name, data):
	columns = ','.join(data.keys())
	values = ','.join([str("'" + e + "'") for e in data.values()])
	try:
		with mysql.cursor() as cur:
			cur.execute(f"INSERT into {table_name} ({columns}) VALUES ({values})")
		return True
	except Exception as e:
		print("Problem inserting into db: " + str(e))
		return False

def update_one(mysql, table_name, data, mod, mod_value):
	data = ", ".join("{}= '{}'".format(k, v) for k, v in data.items())
	try:
		with mysql.cursor() as cur:
			cur.execute(f"UPDATE {table_name} SET {data} WHERE {mod}={mod_value} LIMIT 1")
		return True
	except Exception as e:
		print("Problem updating into db: " + str(e))
		return False

def delete_one(mysql, table_name, mod, mod_value):
	try:
		with mysql.cursor() as cur:
			cur.execute(f"DELETE FROM {table_name} WHERE {mod}={mod_value} LIMIT 1")
		return True
	except Exception as e:
		print("Problem deleting from db: " + str(e))
		return False

def execute_sql(mysql, code):
	try:
		output = []
		with mysql.cursor() as cur:
			for line in sqlsplit(code):
				cur.execute(line)
				tb = from_db_cursor(cur)
				if not tb:
					continue
				output.append(tb.get_string().replace("\n", "<br>"))
		return {"out": output}
	except Exception as e:
		return {"error": str(e)}