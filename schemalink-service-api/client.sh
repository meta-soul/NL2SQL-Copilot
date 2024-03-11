PORT=$1
MODEL=$2

if [ -z "${PORT}" ]; then
    PORT=18022
fi
if [ -z "${MODEL}" ]; then
    MODEL="schema-linking-base"
fi

#API_BASE="https://api.openai.com"
API_BASE="http://127.0.0.1:${PORT}"
API_KEY="ak_84ff9c1c-4758-494b-b6fd-2f21f06650c3"
MODEL_NAME="${MODEL}"

echo "/v1/schema_linking"
curl ${API_BASE}/v1/schema_linking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": '\"${MODEL_NAME}\"',
    "question": "一共有多少黄色眼睛的超级英雄",
    "sort":true,
    "table_threshold": 0,
    "column_threshold": 0,
    "show_table_nums": 2,
    "show_column_nums": 5,
    "db": {
    "database": "superhero",
    "comment": "",
    "tables": [
        {
            "table": "colour",
            "comment": "",
            "columns": [
                {
                    "column": "id",
                    "type": "int",
                    "primary_key": true,
                    "reference_key": "",
                    "comment": "列名：颜色id；注释：颜色id"
                },
                {
                    "column": "colour",
                    "type": "varchar",
                    "primary_key": false,
                    "reference_key": "",
                    "comment": "列名：颜色种类；注释：超级英雄的皮肤/眼睛/头发/等的颜色"
                }
            ]
        },
        {
            "table": "superhero",
            "comment": "",
            "columns": [
                {
                    "column": "id",
                    "type": "int",
                    "primary_key": true,
                    "reference_key": "",
                    "comment": ""
                },
                {
                    "column": "superhero_name",
                    "type": "varchar",
                    "primary_key": false,
                    "reference_key": "",
                    "comment": ""
                },
                {
                    "column": "full_name",
                    "type": "varchar",
                    "primary_key": false,
                    "reference_key": "",
                    "comment": ""
                },
                {
                    "column": "gender_id",
                    "type": "int",
                    "primary_key": false,
                    "reference_key": "gender.id",
                    "comment": ""
                },
                {
                    "column": "eye_colour_id",
                    "type": "int",
                    "primary_key": false,
                    "reference_key": "colour.id",
                    "comment": ""
                },
                {
                    "column": "hair_colour_id",
                    "type": "int",
                    "primary_key": false,
                    "reference_key": "colour.id",
                    "comment": ""
                },
                {
                    "column": "skin_colour_id",
                    "type": "int",
                    "primary_key": false,
                    "reference_key": "colour.id",
                    "comment": ""
                },
                {
                    "column": "race_id",
                    "type": "int",
                    "primary_key": false,
                    "reference_key": "race.id",
                    "comment": ""
                },
                {
                    "column": "publisher_id",
                    "type": "int",
                    "primary_key": false,
                    "reference_key": "publisher.id",
                    "comment": ""
                },
                {
                    "column": "alignment_id",
                    "type": "int",
                    "primary_key": false,
                    "reference_key": "alignment.id",
                    "comment": ""
                },
                {
                    "column": "height_cm",
                    "type": "int",
                    "primary_key": false,
                    "reference_key": "",
                    "comment": ""
                },
                {
                    "column": "weight_kg",
                    "type": "int",
                    "primary_key": false,
                    "reference_key": "",
                    "comment": ""
                }
            ]
        }
    ]
}
  }'
echo -e "\n"
