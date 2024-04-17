FROM python:3.8.12

WORKDIR /opt/nl2sql/schemalink-service-api

COPY ./requirements.txt /opt/nl2sql/schemalink-service-api/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /opt/nl2sql/schemalink-service-api/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY ./conf/config-docker.toml /opt/nl2sql/schemalink-service-api/conf/config.toml

COPY ./models/schema-linking-v1 /opt/nl2sql/schemalink-service-api/models/schema-linking-v1

COPY ./src /opt/nl2sql/schemalink-service-api/src

ENV PYTHONPATH=./src

CMD ["python3", "-u", "src/main.py", "--config", "conf/config.toml", "--port", "80"]
