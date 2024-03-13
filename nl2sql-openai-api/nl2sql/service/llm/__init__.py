from nl2sql.service.base import ServiceBase


class LLMService(ServiceBase):
    """
    prompt v3: table and column with original name + primary-foregin key
    prompt v4: codex/openai style prompt
    """

    @property
    def column_stringify_kwargs(self):
        return {"prompt_version": self.prompt_args.get('version', 'v3')}

    @property
    def table_stringify_kwargs(self):
        return {"prompt_version": self.prompt_args.get('version', 'v3')}

    @property
    def database_stringify_kwargs(self):
        return {"prompt_version": self.prompt_args.get('version', 'v3')}

    @property
    def make_prompt_kwargs(self):
        return {"prompt_version": self.prompt_args.get('version', 'v3')}

    def column_stringify(self, col, prompt_version="v3", **kwargs):
        return col.name
    
    def table_stringify(self, tbl, columns=[], prompt_version="v3", **kwargs):
        tbl_name, tbl_comment = tbl.name, tbl.comment
        if prompt_version == 'v4':
            return f"# Table {tbl_name}, columns = [ {', '.join(columns)} ]"

        return f"{tbl_name}: {' , '.join(columns)}"
    
    def database_stringify(self, db, tables=[], prompt_version="v3", **kwargs):
        db_name, db_comment, db_type = db.name, db.comment, db.type
        if prompt_version == "v4":
            return f"# {db_type} SQL tables, with their properties:\n" + "\n".join(tables)

        tables = tables[:]
        pkeys = db.get_primary_keys()
        if pkeys:
            tables.append(f"primary keys: {' , '.join(pkeys)}")
        fkeys = db.get_foreign_keys()
        fkeys = [f"{fk} = {rk}" for fk, rk in fkeys]
        if fkeys:
            tables.append(f"foreign keys: {' , '.join(fkeys)}")
        return f"Tables: {' ; '.join(tables)}"
    
    def make_prompt(self, schema, question, prompt_version="v1", **kwargs):
        if prompt_version == "v4":
            return "# Text to SQL 任务，根据输入的自然语言和数据表结构，生成 SQL" + "\n" + schema + "\n" + f"# Create a query for question: {question}"

        return f"将自然语言问题 Question 转换为SQL语句，数据库的表结构由 Tables 提供。仅返回SQL语句，不要进行解释。\nQuestion: {question} <sep> {schema} <sep>"
