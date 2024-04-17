from typing import List, Dict, Any
from nl2sql.models.chat import ChatRequest
from nl2sql.schema import create_database_from_str

import os
import json
import requests
from copy import deepcopy

from loguru import logger


class PreProcessorChatPayloadParser(object):
    _processor_name = "pre_chat_payload_parser"
    _processor_desc = "Parse user raw prompt from OpenAI Chat request body."

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, payload: Dict[str, Any], context={}):
        return self.run(payload, context=context)

    def run(self, payload: Dict[str, Any], context={}):
        chat = ChatRequest(payload)
        return {
            "raw_prompt": chat.get_content()
        }


class PreProcessorPromptParser(object):
    _processor_name = "pre_prompt_parser"
    _processor_desc = "Parse"

    def __init__(self, prompt_version="v3", *args, **kwargs):
        self.prompt_version = prompt_version

    def __call__(self, payload: Dict[str, Any], context={}):
        return self.run(payload, context=context)

    def run(self, payload: Dict[str, Any], context={}):
        raw_prompt = context.get("raw_prompt", "")
        lines = [line.strip() for line in raw_prompt.split('\n') if line.strip()]

        db, question = None, ""
        if self.prompt_version == "v0" and len(lines) >= 1:
            # S2S model's prompt
            # Example:
            # Question: 部门中有多少人年龄大于56岁？ <sep> Tables: department: Department_ID | department id , Name | name , Creation | creation , Ranking | ranking , Budget_in_Billions | budget in billions , Num_Employees | num employees ; head: head_ID | head id , name | name , born_state | born state , age | age ; management: department_ID | department id , head_ID | head id , temporary_acting | temporary acting ; primary keys: department.Department_ID , head.head_ID , management.department_ID ; foreign keys: management.head_ID = head.head_ID , management.department_ID = department.Department_ID <sep>
            lines = [line.strip() for line in lines[0].split('<sep>') if line.strip()]
            question, db_str = "", ""
            for line in lines:
                if line.lower().startswith('question:'):
                    question = line[len('question:'):].strip()
                elif line.lower().startswith('tables:'):
                    db_str = line[len('tables:'):].strip()
            
            try:
                db = create_database_from_str("base", "example", db_str)
            except Exception as e:
                db = None
        elif self.prompt_version == "v3" and len(lines) >= 3:
            # Chat2DB v3
            # Example:
            # 根据以下 table properties 和 Question, 将自然语言转换成SQL查询. 备注: 无. version: v3
            # POSTGRESQL SQL database: superhero, with their properties:
            #
            # CREATE TABLE colour (
            #    id integer 0 PRI not null  COMMENT 列名：颜色id；注释：颜色id,
            #    CONSTRAINT colour_pkey PRIMARY KEY (id)
            # );
            # COMMENT ON TABLE colour IS '表名：颜色；注释：超级英雄的皮肤/眼睛/头发/等的颜色'
            #
            # Question: 一共有多少黄色眼睛的超级英雄
            header = lines[1]
            db_type = header.split()[0]
            db_name = header.split(':')[1].split(',')[0].strip() if len(header.split(':')) > 1 else ""
            db_str = '\n'.join(lines[2:-1])  # the other lines exclude the last are db schemas
            question = lines[-1]
            if question.lower().startswith('question:'):
                question = question[len('question:'):].strip()
            else:
                question = ""

            try:
                db = create_database_from_str(db_type, db_name, db_str)
            except Exception as e:
                logger.error(f"[pre_processor = {self._processor_name}] [error={e}]")
                #db = None
                raise e

        return {
            "db": db,
            "question": question
        }


class PreProcessorSchemaLinkingParser(object):
    _processor_name = "pre_schema_linking_parser"
    _processor_desc = "Schema link the db with question."

    def __init__(self, base_url="http://127.0.0.1:18022", url_path="/v1/schema_linking", 
            use_schema_linking_min_tables=5, model_name="schema-linking-big", 
            table_threshold=0.0, column_threshold=0.0, max_table_nums=100, max_column_nums=50,
            timeout=5, *args, **kwargs):
        self.base_url = base_url
        self.url_path = url_path
        self.use_min_tables = use_schema_linking_min_tables
        self.model_name = model_name
        self.table_threshold = table_threshold
        self.column_threshold = column_threshold
        self.max_table_nums = max_table_nums
        self.max_column_nums = max_column_nums
        self.timeout = timeout

    def request_schema_linking_result(self, question, db):
        try:
            url = f"{self.base_url}{self.url_path}"
            payload = {
                "model": self.model_name,
                "question": question,
                "db": db,
                "table_threshold": self.table_threshold,
                "column_threshold": self.column_threshold,
                "show_table_nums": self.max_table_nums,
                "show_column_nums": self.max_column_nums,
            }
            res = requests.post(url,
                json=payload, timeout=self.timeout).json()
            return res["data"][0]["final_schema_link_tables"], res["data"][0]["final_schema_link_columns"]
        except Exception as e:
            logger.error(f"[pre_processor = {self._processor_name}] [error={e}] [url={url}] [payload={payload}]")
            raise e

    def __call__(self, payload: Dict[str, Any], context={}):
        return self.run(payload, context=context)

    def run(self, payload: Dict[str, Any], context={}):
        db = context.get("db", None)
        question = context.get("question", "")

        if db is None or len(db.tables) <= self.use_min_tables:
            return {}

        linked_tables, linked_columns = self.request_schema_linking_result(question, db.to_dict())
        if not linked_tables:
            return {}

        db.update(linked_tables, linked_columns)
        return {"db": db}


class PreProcessorPromptGenerator(object):
    _processor_name = "pre_prompt_generator"
    _processor_desc = "Generate the prompt for nl2sql model api."

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, payload: Dict[str, Any], context={}):
        return self.run(payload, context=context)

    def run(self, payload: Dict[str, Any], context={}):
        service = context['service']
        db = context.get("db", None)
        question = context.get("question", "")

        schema = ""
        if db:
            schema = db.to_str(service.database_stringify, service.table_stringify,
                               service.column_stringify, service.database_stringify_kwargs,
                               service.table_stringify_kwargs, service.column_stringify_kwargs)

        service_prompt = service.make_prompt(schema, question, **service.make_prompt_kwargs)

        return {
            "service_prompt": service_prompt
        }


class PreProcessorChatPayloadGenerator(object):
    _processor_name = "pre_chat_payload_generator"
    _processor_desc = "Generate the chat request payload for nl2sql model api."

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, payload: Dict[str, Any], context={}):
        return self.run(payload, context=context)

    def run(self, payload: Dict[str, Any], context={}):
        service_prompt = context.get("service_prompt", "")

        chat = ChatRequest(payload)
        chat.set_content(service_prompt)
        return {
            "service_payload": chat.get_payload()
        }
