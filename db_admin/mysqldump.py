from mariadb import connect

class ExportedData:
    def __init__(self):
        self.data = []
        
    def write(self, data):
        self.data.append(data)
        
    def read(self):
        return "\n\n".join(self.data)

class Dumper:
    def __init__(self, host, port, user, password, database):
        self.mysql_args = {"host": host, "port": port, "user": user, "password": password, "database": database}
        self.mysql = None
        self.tables = []
        self._dump = ExportedData()
        
    def __enter__(self):
        self.mysql = connect(**self.mysql_args)
        self.getTables()
        return self
        
    def __exit__(self, exc_type, exc, tb):
        self.mysql.close()
        if exc:
            raise
        
    def getTables(self):
        with self.mysql.cursor() as cur:
            cur.execute("SHOW TABLES;")
            self.tables = list(cur.fetchall())
            
    def dump(self):
        tb = ", ".join([f"`{t[0]}` READ" for t in self.tables])
        with self.mysql.cursor() as cur:
            cur.execute(f"LOCK TABLES {tb};")
            cur.execute("SET SQL_QUOTE_SHOW_CREATE=1;")
            cur.execute("SET SESSION character_set_results = 'utf8mb4';")
            for table in self.tables:
                table = table[0]
                cur.execute(f"SHOW CREATE TABLE `{table}`;")
                data = cur.fetchall()
                self._dump.write(data[0][1]+";")
                cur.execute(f"SELECT * FROM `{table}`;")
                data = cur.fetchall()
                if data:
                    rows = []
                    for row in data:
                        row = list(row)
                        for idx, col in enumerate(row):
                            if col is True:
                                row[idx] = 1
                            elif col is False:
                                row[idx] = 0
                        row = [repr(col) for col in row]
                        row = ",".join(row)
                        row = f"({row})"
                        rows.append(row)
                    rows = ",".join(rows)
                    self._dump.write(f"INSERT INTO `{table}` VALUES {rows};")
            cur.execute("UNLOCK TABLES;")
        return self._dump.read()