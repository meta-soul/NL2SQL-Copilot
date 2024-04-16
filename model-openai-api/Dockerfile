FROM python:3.8.12

WORKDIR /opt/nl2sql/model-openai-api

COPY ./requirements.txt /opt/nl2sql/model-openai-api/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /opt/nl2sql/model-openai-api/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY ./conf/config-docker.toml /opt/nl2sql/model-openai-api/conf/config.toml

COPY ./models/nl2sql-chinese-basic /opt/nl2sql/model-openai-api/models/nl2sql-chinese-basic

COPY ./src /opt/nl2sql/model-openai-api/src

ENV PYTHONPATH=./src

CMD ["python3", "-u", "src/main.py", "--config", "conf/config.toml", "--llm_model", "nl2sql-v2", "--port", "80"]
