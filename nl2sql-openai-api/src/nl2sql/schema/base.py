import json

def str_norm(s):
    return s.replace('|', ' ').replace(',', ' ').replace(';', ' ').replace(':', ' ').strip()


class TableColumn:

    def __init__(self, name, comment="", type="", 
            primary_key=False, reference_key="", ref_tbl=None):
        self.name = str_norm(name)
        self.comment = str_norm(comment)
        self.type = type
        self.primary_key = bool(primary_key)
        self.reference_key = str(reference_key)
        self.ref_tbl = ref_tbl

    def to_dict(self):
        return {
            'column': self.name,
            'type': self.type,
            'primary_key': self.primary_key,
            'reference_key': self.reference_key,
            'comment': self.comment
        }

    def set_primary(self, status=True):
        self.primary_key = status

    def set_reference(self, ref_key):
        self.reference_key = str(ref_key)

    def to_str(self, column_stringify, column_stringify_kwargs={}):
        return column_stringify(self, **column_stringify_kwargs)

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)


class TableSchemaBase:

    def __init__(self, name, comment="", table_id=None, ref_db=None):
        self.name = str_norm(name)
        self.comment = str_norm(comment)
        self.table_id = table_id
        self.ref_db = ref_db
        self.columns = []
        self._ddl = ""

    @property
    def id(self):
        return self.table_id or self.name

    @property
    def ddl(self):
        # TODO: create ddl via the intermediate objects
        return self._ddl

    def to_dict(self):
        return {
            'table': self.name,
            'comment': self.comment,
            'columns': [c.to_dict() for c in self.columns],
        }

    def __iter__(self):
        for column in self.columns:
            yield column

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)

    def set_primary_keys(self, keys):
        if isinstance(keys, str):
            keys = [keys]

        keys = [str_norm(k) for k in keys]
        for column in self.columns:
            if column.name in keys:
                column.set_primary()

    def get_primary_keys(self):
        keys = []
        for col in self.columns:
            if col.primary_key:
                keys.append(f"{self.name}.{col.name}")
        return keys

    def set_foreign_keys(self, keys=[], ref_keys=[]):
        refs = {str_norm(key):ref_key for key, ref_key in zip(keys, ref_keys)}
        for column in self.columns:
            if column.name in refs:
                column.set_reference(refs[column.name])

    def get_foreign_keys(self):
        keys = []
        for col in self.columns:
            if col.reference_key:
                keys.append((f"{self.name}.{col.name}", col.reference_key))
        return keys

    def add_column(self, col_name, col_comment="", col_type="", primary_key=False, reference_key=""):
        col_i = len(self.columns)
        self.columns.append(TableColumn(col_name, col_comment, col_type,
            primary_key=primary_key, reference_key=reference_key, ref_tbl=self))
        return col_i

    def to_str(self, table_stringify, column_stringify, table_stringify_kwargs={}, column_stringify_kwargs={}):
        cols = []
        for col in self.columns:
            cols.append(col.to_str(column_stringify, column_stringify_kwargs))
        return table_stringify(self, cols, **table_stringify_kwargs)

    @classmethod
    def parse_from_str(cls, tbl_str, tbl_sep=':', col_sep=',', comment_sep='|'):
        tbl_name, cols = tbl_str.split(tbl_sep)[:2]
        if comment_sep in tbl_name:
            tbl_name, tbl_comment = tbl_name.split(comment_sep)[:2]
        else:
            tbl_comment = ""
        tbl = cls(tbl_name, tbl_comment)

        for col in cols.strip().split(col_sep):
            col = col.strip()
            if not col:
                continue
            col_x = [v.strip() for v in col.split(comment_sep) if v.strip()]
            if len(col_x) == 1:
                tbl.add_column(col_x[0])
            elif len(col_x) == 2:
                tbl.add_column(col_x[0], col_x[1])
            elif len(col_x) == 3:
                tbl.add_column(col_x[0], col_x[1], col_x[2])

        return tbl


class DatabaseSchemaBase:

    def __init__(self, name, comment="", db_id=None, db_type=""):
        self.name = name
        self.comment = comment
        self.type = db_type
        self.db_id = db_id
        self.tables = {}

    @property
    def id(self):
        return self.db_id or self.name

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)

    def __iter__(self):
        for schema in self.tables.values():
            yield schema

    def add_table(self, schema:TableSchemaBase):
        self.tables[schema.id] = schema
        self.tables[schema.id].ref_db = self
        return self

    def update(self, schema_tables, schema_columns):
        new_tables={}
        for _, table in enumerate(self.tables.values()):
            table_name = table.name
            if table_name not in schema_tables:
                continue
            table_idx = schema_tables.index(table_name)
            columns = table.columns
            new_columns = []
            for column in columns:
                column_name = column.name
                if column_name not in schema_columns[table_idx]:
                    continue
                new_columns.append(column)
            table.columns = new_columns
            new_tables[table.id] = table
        self.tables = new_tables
        return self

    def get_primary_keys(self):
        keys = []
        for tbl in self.tables.values():
            keys.extend(tbl.get_primary_keys())
        return keys

    def get_foreign_keys(self):
        keys = []
        for tbl in self.tables.values():
            keys.extend(tbl.get_foreign_keys())
        return keys

    def to_dict(self):
        return {
            'database': self.name,
            'comment': self.comment,
            'tables': [s.to_dict() for s in self.tables.values()]
        }

    def to_str(self, database_stringify, table_stringify, column_stringify, 
            database_stringify_kwargs={}, table_stringify_kwargs={}, column_stringify_kwargs={}):
        tbls = []
        for tbl in self.tables.values():
            tbls.append(tbl.to_str(table_stringify, column_stringify, 
                table_stringify_kwargs=table_stringify_kwargs,
                column_stringify_kwargs=column_stringify_kwargs))
        return database_stringify(self, tbls, **database_stringify_kwargs)

    @classmethod
    def parse_from_str(cls, db_name, db_str, db_sep=';', tbl_sep=':', col_sep=',', comment_sep='|', 
            primary_token='primary keys', foreign_token='foreign keys', primary_sep='.', foreign_sep='='):
        db = cls(db_name)
        primary_str, foreign_str = "", ""
        for tbl_str in db_str.split(db_sep):
            tbl_str = tbl_str.strip()
            if not tbl_str:
                continue
            tbl_name = tbl_str.split(tbl_sep)[0]
            if tbl_name.lower() == primary_token:
                primary_str = tbl_str.split(tbl_sep)[1] if len(tbl_str.split(tbl_sep))>1 else ""
            elif tbl_name.lower() == foreign_token:
                foreign_str = tbl_str.split(tbl_sep)[1] if len(tbl_str.split(tbl_sep))>1 else ""
            else:
                schema = TableSchemaBase.parse_from_str(tbl_str, tbl_sep=tbl_sep, 
                    col_sep=col_sep, comment_sep=comment_sep)
            db.add_table(schema)
        primary_keys = [k.strip() for k in primary_str.split(col_sep) if k.strip()]
        for full_key in primary_keys:
            if primary_sep not in full_key:
                continue
            tbl_name, col_name = full_key.split(primary_sep)[:2]
            if tbl_name not in db.tables:
                continue
            db.tables[tbl_name].set_primary_keys([col_name])

        foreign_keys = [k.strip() for k in foreign_str.split(col_sep) if k.strip()]
        for full_key in foreign_keys:
            if foreign_sep not in full_key:
                continue
            full_key1, full_key2 = full_key.split(foreign_sep)[:2]
            if primary_sep in full_key1 and primary_sep in full_key2:
                tbl_name, col_name = full_key1.split(primary_sep)[:2]
                #ref_tbl_name, ref_col_name = full_key2.split(primary_sep)[:2]
                if tbl_name not in db.tables:
                    continue
                db.tables[tbl_name].set_foreign_keys([col_name], [full_key2])

        return db

def column_stringify(col, comment_sep='|', **kwargs):
    col_str = ""
    if col.comment and col.type:
        col_str = f" {col.name} {comment_sep} {col.comment} {comment_sep} {col.type} "
    elif col.comment:
        col_str = f" {col.name} {comment_sep} {col.comment} "
    else:
        col_str = f" {col.name} "
    return col_str

def table_stringify(tbl, columns=[], tbl_sep=':', col_sep=',', comment_sep='|', **kwargs):
    tbl_name, tbl_comment = tbl.name, tbl.comment
    if tbl_comment:
        tbl_name = f"{tbl_name} {comment_sep} {tbl_comment}"
    else:
        tbl_name = f"{tbl_name}"

    tbl_str = tbl_name
    if columns:
        tbl_str = tbl_name + tbl_sep + " " + col_sep.join(columns).strip()
    return " " + tbl_str + " "

def database_stringify(db, tables=[], db_sep=';', **kwargs):
    db_name, db_comment, db_type = db.name, db.comment, db.type
    return db_sep.join(tables).strip()

if __name__ == '__main__':
    tbl_schema = TableSchemaBase.parse_from_str('airport: id , City , Country , IATA , ICAO , name')
    print(tbl_schema)
    # print(tbl_schema.to_str(table_stringify, column_stringify))
    #
    # tbl_schema1 = TableSchemaBase.parse_from_str('airport1 | 机场: id | 机场id, City | 机场城市, Country | 机场国家, IATA | IATA 代码, ICAO | ICAO d代码, name | 机场名称')
    # print(tbl_schema1)
    # print(tbl_schema1.to_str(table_stringify, column_stringify))
    #
    # db_schema = DatabaseSchemaBase.parse_from_str('flight_company', 'airport: id , City , Country , IATA , ICAO , name ; operate_company: id , name , Type , Principal_activities , Incorporated_in , Group_Equity_Shareholding ; flight: id , Vehicle_Flight_number , Date , Pilot , Velocity , Altitude , airport_id , company_id')
    # print(db_schema)
    # for schema in db_schema:
    #    print(schema)
    # print(db_schema.to_str(database_stringify, table_stringify, column_stringify))

    db_schema = DatabaseSchemaBase.parse_from_str('example', 'department: Department_ID | department id , Name | name , Creation | creation , Ranking | ranking , Budget_in_Billions | budget in billions , Num_Employees | num employees ; head: head_ID | head id , name | name , born_state | born state , age | age ; management: department_ID | department id , head_ID | head id , temporary_acting | temporary acting ; primary keys: department.Department_ID , head.head_ID , management.department_ID ; foreign keys: management.head_ID = head.head_ID , management.department_ID = department.Department_ID')
    print(db_schema)
    print(db_schema.to_str(database_stringify, table_stringify, column_stringify))
