PORT=$1
API_SERVICE=$2
MODEL_NAME=$3
API_KEY=$4

if [ -z "${PORT}" ]; then
    PORT=18080
fi
if [ -z "${API_SERVICE}" ]; then
    API_SERVICE="intermediate"
fi
if [ -z "${MODEL_NAME}" ]; then
    #MODEL_NAME="gpt-3.5-turbo"
    MODEL_NAME="nl2sql-v2"
fi
if [ -z "${API_KEY}" ]; then
    API_KEY="ak_84ff9c1c-4758-494b-b6fd-2f21f06650c3"
fi

API_BASE="http://127.0.0.1:${PORT}"

# /basic with v0 prompt, same as offline model
echo "/v1/chat/completions"
curl ${API_BASE}/nl2sql/${API_SERVICE}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": '\"${MODEL_NAME}\"',
    "service_status": "disabled",
    "messages": [{"role": "user", "content": "Question: 所有章节的名称和描述是什么？ <sep> Tables: sections: section id , course id , section name , section description , other details <sep>"}]
  }'
echo -e "\n"
curl ${API_BASE}/nl2sql/${API_SERVICE}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": '\"${MODEL_NAME}\"',
    "messages": [{"role": "user", "content": "Question: 所有章节的名称和描述是什么？ <sep> Tables: sections: section id , course id , section name , section description , other details <sep>"}]
  }'
echo -e "\n"

# /intermediate and /openai with v3 prompt, same as chat2db
echo "/v1/chat/completions"
curl ${API_BASE}/nl2sql/${API_SERVICE}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": '\"${MODEL_NAME}\"',
    "stream": false,
    "messages": [{"role": "user", "content": "根据以下 table properties 和 Question, 将自然语言转换成SQL查询. 备注: 无. version: v3\nPOSTGRESQL SQL database: superhero, with their properties:\n\n CREATE TABLE colour ( \r\n id integer 0 PRI not null  COMMENT 列名：颜色id；注释：颜色id,\r\n colour character varying 0  null  COMMENT 列名：颜色种类；注释：超级英雄的皮肤/眼睛/头发/等的颜色,\r\n CONSTRAINT colour_pkey PRIMARY KEY (id)\r\n ); \r\n\r\n\r\n\r\nCOMMENT ON TABLE colour IS '"表名：颜色；注释：超级英雄的皮肤/眼睛/头发/等的颜色"'\r\n\r\nCOMMENT ON COLUMN colour.id IS '"列名：颜色id；注释：颜色id"',\r\nCOMMENT ON COLUMN colour.colour IS '"列名：颜色种类；注释：超级英雄的皮肤/眼睛/头发/等的颜色"'\n\n CREATE TABLE superhero ( \r\n id integer 0 PRI not null,\r\n superhero_name character varying 0  null,\r\n full_name character varying 0  null,\r\n gender_id integer 0 FRI null,\r\n eye_colour_id integer 0 FRI null,\r\n hair_colour_id integer 0 FRI null,\r\n skin_colour_id integer 0 FRI null,\r\n race_id integer 0 FRI null,\r\n publisher_id integer 0 FRI null,\r\n alignment_id integer 0 FRI null,\r\n height_cm integer 0  null,\r\n weight_kg integer 0  null,\r\n CONSTRAINT superhero_pkey PRIMARY KEY (id),\r\n CONSTRAINT superhero_gender_id_fkey FOREIGN KEY(gender_id) REFERENCES gender(id),\r\n CONSTRAINT superhero_eye_colour_id_fkey FOREIGN KEY(eye_colour_id) REFERENCES colour(id),\r\n CONSTRAINT superhero_hair_colour_id_fkey FOREIGN KEY(hair_colour_id) REFERENCES colour(id),\r\n CONSTRAINT superhero_skin_colour_id_fkey FOREIGN KEY(skin_colour_id) REFERENCES colour(id),\r\n CONSTRAINT superhero_race_id_fkey FOREIGN KEY(race_id) REFERENCES race(id),\r\n CONSTRAINT superhero_publisher_id_fkey FOREIGN KEY(publisher_id) REFERENCES publisher(id),\r\n CONSTRAINT superhero_alignment_id_fkey FOREIGN KEY(alignment_id) REFERENCES alignment(id)\r\n ); \r\n CREATE TABLE attribute (\r\n id integer 0 PRI not null  COMMENT '"列名：id；注释：属性id"',\r\n attribute_name character varying 0  null  COMMENT '"列名：属性；注释：超级英雄的属性 常见的属性有：智力/力量/速度/耐用性/力量/战斗等"',\r\n CONSTRAINT attribute_pkey PRIMARY KEY (id)\r\n);\r\n\r\n\r\nCOMMENT ON TABLE attribute IS '"表名：属性；注释：超级英雄的属性是定义他们是谁以及他们有能力的特征或品质"'\r\n\r\nCOMMENT ON COLUMN attribute.id IS '"列名：id；注释：属性id"',\r\nCOMMENT ON COLUMN attribute.attribute_name IS '"列名：属性；注释：超级英雄的属性 常见的属性有：智力/力量/速度/耐用性/力量/战斗等。"'; \r\n\r\n\r\n\r\n\r\n\n\n\nQuestion: 一共有多少黄色眼睛的超级英雄"}]
  }'
echo -e "\n"
