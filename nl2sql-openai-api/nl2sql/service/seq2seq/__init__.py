from nl2sql.service.base import ServiceBase


class Seq2seqService(ServiceBase):
    """
    prompt v1: table and column with nl name
    prompt v2: table and column with original name
    prompt v3: table and column with original name + primary-foregin key
    prompt v4: codex/openai style prompt
    prompt v5: table and column with original name + primary-foregin key + comment
    """

    @property
    def column_stringify_kwargs(self):
        return {"prompt_version": self.prompt_args.get('version', 'v2')}

    @property
    def table_stringify_kwargs(self):
        return {"prompt_version": self.prompt_args.get('version', 'v2')}

    @property
    def database_stringify_kwargs(self):
        return {"prompt_version": self.prompt_args.get('version', 'v2')}

    @property
    def make_prompt_kwargs(self):
        return {"prompt_version": self.prompt_args.get('version', 'v2')}

    def column_stringify(self, col, prompt_version="v1", **kwargs):
        return col.name
    
    def table_stringify(self, tbl, columns=[], prompt_version="v1", **kwargs):
        tbl_name, tbl_comment = tbl.name, tbl.comment
        if prompt_version in ['v1', 'v2', 'v3']:
            return f"{tbl_name}: {' , '.join(columns)}"
        elif prompt_version == 'v4':
            return f"# Table {tbl_name}, columns = [ {', '.join(columns)} ]"
        return f"{tbl_name}: {' , '.join(columns)}"
    
    def database_stringify(self, db, tables=[], prompt_version="v1", **kwargs):
        db_name, db_comment, db_type = db.name, db.comment, db.type
        if prompt_version in ['v1', 'v2']:
            return f"Tables: {' ; '.join(tables)}"
        elif prompt_version == 'v3':
            tables = tables[:]
            pkeys = db.get_primary_keys()
            if pkeys:
                tables.append(f"primary keys: {' , '.join(pkeys)}")
            fkeys = db.get_foreign_keys()
            fkeys = [f"{fk} = {rk}" for fk, rk in fkeys]
            if fkeys:
                tables.append(f"foreign keys: {' , '.join(fkeys)}")
            return f"Tables: {' ; '.join(tables)}"
        elif prompt_version == "v4":
            return f"# {db_type} SQL tables, with their properties:\n" + "\n".join(tables)
        return f"Tables: {' ; '.join(tables)}"
    
    def make_prompt(self, schema, question, prompt_version="v1", **kwargs):
        if prompt_version in ['v1', 'v2', 'v3']:
            return f"Question: {question} <sep> {schema} <sep>"
        elif prompt_version == "v4":
            return schema + "\n" + f"# Create a query for question: {question}"
        return f"Question: {question} <sep> {schema} <sep>"
