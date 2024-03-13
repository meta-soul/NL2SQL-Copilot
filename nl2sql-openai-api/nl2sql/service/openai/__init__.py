from nl2sql.service.base import ServiceBase


class OpenaiService(ServiceBase):
    """
    prompt v1: codex
    prompt v2: gpt-3.5-turbo
    """

    @property
    def column_stringify_kwargs(self):
        return {"prompt_version": self.prompt_args['version']}

    @property
    def table_stringify_kwargs(self):
        return {"prompt_version": self.prompt_args['version']}

    @property
    def database_stringify_kwargs(self):
        return {"prompt_version": self.prompt_args['version']}

    @property
    def make_prompt_kwargs(self):
        return {"prompt_version": self.prompt_args['version']}

    def column_stringify(self, col, prompt_version="v1", **kwargs):
        if prompt_version == "v2":
            return col.name
        return col.name
    
    def table_stringify(self, tbl, columns=[], prompt_version="v1", **kwargs):
        tbl_name, tbl_comment = tbl.name, tbl.comment
        if prompt_version == "v2":
            return f"Table {tbl_name}, columns = [ {', '.join(columns)} ]"
        return f"# Table {tbl_name}, columns = [ {', '.join(columns)} ]"
    
    def database_stringify(self, db, tables=[], prompt_version="v1", **kwargs):
        db_name, db_comment, db_type = db.name, db.comment, db.type
        if prompt_version == "v2":
            return f"{db_type} 表信息如下：\n\n" + "\n".join(tables)
        return f"# {db_type} SQL tables, with their properties:\n" + "\n".join(tables)
    
    def make_prompt(self, schema, question, prompt_version="v1", **kwargs):
        if prompt_version == "v2":
            return "".join([
                "根据question和数据库的表信息，生成 SQL\n\n",
                f"{schema}\n\n",
                f"Question：{question}\n\n",
                "SQL："
            ])
        return schema + "\n" + f"# Create a query for question: {question}"
