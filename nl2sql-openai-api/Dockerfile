FROM python:3.8.12

WORKDIR /opt/nl2sql/nl2sql-openai-api

COPY ./requirements.txt /opt/nl2sql/nl2sql-openai-api/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /opt/nl2sql/nl2sql-openai-api/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY ./conf/config-docker.toml /opt/nl2sql/nl2sql-openai-api/conf/config.toml

COPY ./src /opt/nl2sql/nl2sql-openai-api/src

ENV PYTHONPATH=./src

CMD ["python3", "-u", "src/main.py", "--config", "conf/config.toml", "--port", "80"]
