import time
import httpx
from loguru import logger
from fastapi import HTTPException, status

from nl2sql.service.processors import create_processor


class ServiceBase:

    def __init__(self, name, conf={}, **kwargs):
        self.name = name
        self.pre_processors = []
        self.post_processors = []
        self.prompt_args = conf.get('prompt', {})
        self.model_args = conf.get('model', {})
        for x in conf.get('pre', []):
            self.pre_processors.append(create_processor(x['name'], *x['args'], **x['kwargs']))
        for x in conf.get('post', []):
            self.post_processors.append(create_processor(x['name'], *x['args'], **x['kwargs']))

    def __str__(self):
        return "\n".join([
            f"service: {self.name}",
            f"pre_processors: {', '.join([p._processor_name for p in self.pre_processors])}",
            f"post_processors: {', '.join([p._processor_name for p in self.post_processors])}",
        ])

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

    def column_stringify(self, col, comment_sep=' | ', prompt_version="v1", **kwargs):
        col_str = ""
        #if col.comment and col.type:
        #    col_str = f" {col.name} {comment_sep} {col.comment} {comment_sep} {col.type} "
        #elif col.comment:
        #    col_str = f" {col.name} {comment_sep} {col.comment} "
        #else:
        #    col_str = f" {col.name} "
        col_str = col.name
        return col_str
    
    def table_stringify(self, tbl, columns=[], tbl_sep=':', col_sep=' , ', comment_sep=' | ', prompt_version="v1", **kwargs):
        tbl_name, tbl_comment = tbl.name, tbl.comment
        #if tbl_comment:
        #    tbl_name = f"{tbl_name} {comment_sep} {tbl_comment}"
        #else:
        #    tbl_name = f"{tbl_name}"
    
        tbl_str = tbl_name
        if columns:
            tbl_str = tbl_name + tbl_sep + " " + col_sep.join(columns).strip()
        return " " + tbl_str.strip() + " "
    
    def database_stringify(self, db, tables=[], db_sep=' ; ', prompt_version="v1", **kwargs):
        #db_name, db_comment, db_type = db.name, db.comment, db.type
        return db_sep.join(tables).strip()
    
    def make_prompt(self, schema, question, prompt_version="v1", **kwargs):
        """
        Example:
        Question: 所有章节的名称和描述是什么？ <sep> Tables: sections: section id , course id , section name , section description , other details <sep>
        """
        #return "\n".join([schema, question])
        return f"Question: {question} <sep> Tables: {schema} <sep>"

    def pre_process(self, payload):
        """Run the sequential pre-processors."""
        pre_res = {}
        pre_res['service'] = self
        for pre_f in self.pre_processors:
            during_time = time.time()
            try:
                res, status = pre_f(payload, context=pre_res), True
            except Exception as e:
                error = str(e)
                res, status = {}, False
            during_time = int((time.time() - during_time)*1000)
            if status:
                logger.info(f"[service = {self.name}] [pre_processor = {pre_f._processor_name}] [status = {status}] [during = {during_time}ms]")
            else:
                logger.info(f"[service = {self.name}] [pre_processor = {pre_f._processor_name}] [status = {status}] [during = {during_time}ms] [error={error}]")
            pre_res.update(res)
        return pre_res

    def post_process(self, aiter_bytes, pre_res={}):
        """Run the sequential post-processors."""
        post_res = {}
        post_res.update(pre_res)
        for post_f in self.post_processors:
            during_time = time.time()
            try:
                res, status = post_f(aiter_bytes, context=post_res), True
            except Exception as e:
                res, status = {}, False
            during_time = int((time.time() - during_time)*1000)
            logger.info(f"[service = {self.name}] [post_processor = {post_f._processor_name}] [status = {status}] [during = {during_time}ms]")
            post_res.update(res)
        return post_res

    async def process(self, base_url, url_path, request, headers, payload, timeout):
        """Send request to inference api."""
        try:
            client = httpx.AsyncClient(base_url=base_url,
                                       http1=True, http2=False)

            query = None if not request.url.query else request.url.query.encode("utf-8")
            url = httpx.URL(path=url_path, query=query)

            # update model name via service config
            payload['model'] = self.model_args.get('name', payload['model'])

            req = client.build_request(
                request.method,
                url,
                headers=headers,
                # content=request.stream(),
                json=payload,
                timeout=timeout,
            )

            logger.info(
                f"[service={self.name}] [forward url={req.url}] [forward method={req.method}] [forward payload={payload}]")

            r = await client.send(req, stream=True)
            return r
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            error_info = (
                f"{type(e)}: {e} | "
                f"Please check if host={request.client.host} can access [{base_url}] successfully?"
            )
            logger.error(error_info)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_info
            )
        except Exception as e:
            logger.exception(f"{type(e)}:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e
            )

        return None


if __name__ == '__main__':
    pass
