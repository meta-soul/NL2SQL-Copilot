import re
import sys

from .base import TableSchemaBase, DatabaseSchemaBase


class TableSchema(TableSchemaBase):


    @classmethod
    def parse_from_str(cls, create_table_sql, comments={}):
        lines = create_table_sql.split('\n')
        tbl_name, tbl_comment, columns, constraints = "", "", [], {}
        start_create_tbl = False
        for line in lines:
            line = line.strip().rstrip(',').strip()
            if not line:
                continue
            # CREATE TABLE race ( 
            if line.upper().startswith('CREATE TABLE ') and line.endswith('('):
                start_create_tbl = True
                tbl_name = line[len('CREATE TABLE '):-1].strip().strip('`').strip()
                continue
            if not start_create_tbl:
                continue
            # );
            if line.upper().startswith(');'):
                break
            is_constraint = False
            for keyword in ['PRIMARY KEY ', 'KEY ', 'CONSTRAINT ']:
                if line.upper().startswith(keyword):
                    is_constraint = True
            # CONSTRAINT
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
            # Column define
            else:
                #`weight_kg` int DEFAULT NULL COMMENT '列名：体重；注释：体重，单位公斤（kg）',
                if len(line.split(' ')) < 2:
                    continue
                col_name = line.split(' ')[0].strip('`')
                col_type = line.split(' ')[1].strip('`')
                if col_type.lower() == 'character':
                    col_type = 'varchar'
                if col_type.lower() == 'integer':
                    col_type = 'int'
                col_comment = ""
                i = line.find('COMMENT ')
                if i > 0:
                    col_comment = line[i+len('COMMENT '):].strip().strip('"').strip("'").strip()
                columns.append([col_name, col_type, col_comment])
        if not tbl_name or not columns:
            return None

        if not tbl_comment and tbl_name in comments:
            tbl_comment = comments[tbl_name]

        tbl = cls(tbl_name, tbl_comment)
        for cn, ct, cc in columns:
            if not cc and f"{tbl_name}.{cn}" in comments:
                cc = comments[f"{tbl_name}.{cn}"]
            is_primary = constraints.get(cn, {}).get('primary', False)
            ref_key = constraints.get(cn, {}).get('reference', '')
            tbl.add_column(cn, col_comment=cc, col_type=ct, 
                primary_key=is_primary, reference_key=ref_key)

        return tbl


class DatabaseSchema(DatabaseSchemaBase):


    @classmethod
    def parse_from_str(cls, db_name, create_table_sql, db_type="postgresql"):
        db = cls(db_name, db_type=db_type)
        ids = []
        i = 0
        start_str = "CREATE TABLE "
        while i < len(create_table_sql):
            m1 = re.search(f'^\s*{start_str}', create_table_sql[i:], flags=re.I | re.M)
            if m1:
                i = i+m1.start()
                m2 = re.search(r'\);[\r\n]*', create_table_sql[i:], flags=re.I | re.M)
                if m2:
                    j = i + m2.end()
                    ids.append((i, j))
                    i = j
                else:
                    i = i + len(start_str)
            else:
                break
        
        comments = {}
        for line in create_table_sql.split('\n'):
            line = line.strip()
            if not line:
                continue
                continue
            # COMMENT ON TABLE race IS '表名：超级英雄种族'
            if line.upper().startswith("COMMENT ON TABLE"):
                comment = line[len('COMMENT ON TABLE'):].strip().strip('"').strip("'").strip(',').strip()
                tbl_name = comment.split(' ')[0]
                i = comment.find("'")
                if i < 0:
                    continue
                comment = comment[i:].strip().strip('"').strip("'").strip()
                if comment:
                    comments[tbl_name] = comment
            #COMMENT ON COLUMN attribute.id IS '列名：id；注释：属性id'
            if line.upper().startswith("COMMENT ON COLUMN"):
                comment = line[len('COMMENT ON COLUMN'):].strip().strip('"').strip("'").strip(',').strip()
                if len(comment.split(' ')) < 2:
                    continue
                tbl_col = comment.split(' ')[0]
                i = comment.find("'")
                if i < 0:
                    continue
                comment = comment[i:].strip().strip('"').strip("'").strip()
                if comment:
                    comments[tbl_col] = comment

        for i, j in ids:
            sql = create_table_sql[i:j].strip()
            if not sql:
                continue
            #print(sql, i, j)
            tbl = TableSchema.parse_from_str(sql, comments)
            if tbl is None:
                continue
            db.add_table(tbl)

        return db
