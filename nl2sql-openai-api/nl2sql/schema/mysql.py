import re
import sys

from .base import TableSchemaBase, DatabaseSchemaBase


class TableSchema(TableSchemaBase):

    @classmethod
    def parse_from_str(cls, create_table_sql):
        #from simple_ddl_parser import DDLParser
        #parser = DDLParser(create_table_sql+'', silent=True)
        #results = parser.run(output_mode='mysql')
        #print(results)

        #from sqlglot import parse_one
        #expr = parse_one(create_table_sql, read='mysql')
        #print(expr)

        lines = create_table_sql.split('\n')
        tbl_name, tbl_comment, columns, constraints = "", "", [], {}
        start_create_tbl = False
        for line in lines:
            line = line.strip().rstrip(',').strip()
            if not line:
                continue
            # CREATE TABLE `race` ( 
            if line.upper().startswith('CREATE TABLE ') and line.endswith('('):
                start_create_tbl = True
                tbl_name = line[len('CREATE TABLE '):-1].strip().strip('`').strip()
                continue
            if not start_create_tbl:
                continue
            # ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COMMENT='表名：超级英雄。'
            if line.upper().startswith(') ENGINE='):
                i = line.find('COMMENT=')
                if i > 0:
                    tbl_comment = line[i+len('COMMENT='):].strip().strip('"').strip("'").strip()
                break
            # CONSTRAINT
            is_constraint = False
            for keyword in ['PRIMARY KEY ', 'KEY ', 'CONSTRAINT ']:
                if line.upper().startswith(keyword):
                    is_constraint = True
            if is_constraint:
                if 'PRIMARY KEY' in line.upper():
                    i = line.upper().find('PRIMARY KEY')
                    if i >= 0:
                        pkey = line[i+len('PRIMARY KEY'):].strip().strip('(').strip(')').strip().strip('`').strip()
                        if pkey:
                            if pkey not in constraints:
                                constraints[pkey] = {}
                            constraints[pkey]['primary'] = True
                elif 'FOREIGN KEY' in line.upper():
                    i = line.upper().find('FOREIGN KEY')
                    j = line.upper().find('REFERENCES')
                    if i >= 0 and j > i and '(' in line[j+len('REFERENCES'):]:
                        fkey = line[i+len('FOREIGN KEY'):j].strip().strip('(').strip(')').strip().strip('`').strip()
                        rtbl = line[j+len('REFERENCES'):].strip().split('(')[0].strip().strip('`').strip()
                        rkey = line[j+len('REFERENCES'):].strip().split('(')[1].strip().strip(')').strip().strip('`').strip()
                        if fkey and rtbl and rkey:
                            if fkey not in constraints:
                                constraints[fkey] = {}
                            constraints[fkey]['reference'] = f"{rtbl}.{rkey}"
            else:
                #`weight_kg` int DEFAULT NULL COMMENT '列名：体重；注释：体重，单位公斤（kg）',
                if len(line.split(' ')) < 2:
                    continue
                col_name = line.split(' ')[0].strip('`')
                col_type = line.split(' ')[1].strip('`')
                col_comment = ""
                i = line.find('COMMENT ')
                if i > 0:
                    col_comment = line[i+len('COMMENT '):].strip().strip('"').strip("'").strip()
                columns.append([col_name, col_type, col_comment])
        if not tbl_name or not columns:
            return None

        tbl = cls(tbl_name, tbl_comment)
        for cn, ct, cc in columns:
            is_primary = constraints.get(cn, {}).get('primary', False)
            ref_key = constraints.get(cn, {}).get('reference', '')
            tbl.add_column(cn, col_comment=cc, col_type=ct, 
                primary_key=is_primary, reference_key=ref_key)

        return tbl


class DatabaseSchema(DatabaseSchemaBase):

    @classmethod
    def parse_from_str(cls, db_name, create_table_sql, db_type="mysql"):
        db = cls(db_name, db_type=db_type)
        ids = []
        i = 0
        start_str = "CREATE TABLE "
        while i < len(create_table_sql):
            m = re.search(f'^{start_str}', create_table_sql[i:], flags=re.I | re.M)
            if m:
                ids.append(i+m.start())
                i = i+m.start()+len(start_str)
            else:
                break
        
        ids.append(len(create_table_sql))
        for i, j in zip(ids[:-1], ids[1:]):
            sql = create_table_sql[i:j].strip()
            if not sql:
                continue
            tbl = TableSchema.parse_from_str(sql)
            if tbl is None:
                continue
            db.add_table(tbl)

        return db
