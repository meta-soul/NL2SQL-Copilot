def path_prefix_norm(url_path):
    url_path = url_path.strip()
    if not url_path:
        return ""
    if not url_path.startswith('/'):
        url_path = '/' + url_path
    return url_path.rstrip('/')

if __name__ == '__main__':
    import requests
    res = requests.post(f"http://127.0.0.1:18022/v1/schema_linking",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer ak_84ff9c1c-4758-494b-b6fd-2f21f06650c3"
                        },
                        json={
                            "model": "schema_linking_big",
                            "question": "一共有多少黄色眼睛的超级英雄",
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
                                                "primary_key": True,
                                                "reference_key": "",
                                                "comment": "列名：颜色id；注释：颜色id"
                                            },
                                            {
                                                "column": "colour",
                                                "type": "varchar",
                                                "primary_key": False,
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
                                                "primary_key": True,
                                                "reference_key": "",
                                                "comment": ""
                                            },
                                            {
                                                "column": "superhero_name",
                                                "type": "varchar",
                                                "primary_key": False,
                                                "reference_key": "",
                                                "comment": ""
                                            },
                                            {
                                                "column": "full_name",
                                                "type": "varchar",
                                                "primary_key": False,
                                                "reference_key": "",
                                                "comment": ""
                                            },
                                            {
                                                "column": "gender_id",
                                                "type": "int",
                                                "primary_key": False,
                                                "reference_key": "gender.id",
                                                "comment": ""
                                            },
                                            {
                                                "column": "eye_colour_id",
                                                "type": "int",
                                                "primary_key": False,
                                                "reference_key": "colour.id",
                                                "comment": ""
                                            },
                                            {
                                                "column": "hair_colour_id",
                                                "type": "int",
                                                "primary_key": False,
                                                "reference_key": "colour.id",
                                                "comment": ""
                                            },
                                            {
                                                "column": "skin_colour_id",
                                                "type": "int",
                                                "primary_key": False,
                                                "reference_key": "colour.id",
                                                "comment": ""
                                            },
                                            {
                                                "column": "race_id",
                                                "type": "int",
                                                "primary_key": False,
                                                "reference_key": "race.id",
                                                "comment": ""
                                            },
                                            {
                                                "column": "publisher_id",
                                                "type": "int",
                                                "primary_key": False,
                                                "reference_key": "publisher.id",
                                                "comment": ""
                                            },
                                            {
                                                "column": "alignment_id",
                                                "type": "int",
                                                "primary_key": False,
                                                "reference_key": "alignment.id",
                                                "comment": ""
                                            },
                                            {
                                                "column": "height_cm",
                                                "type": "int",
                                                "primary_key": False,
                                                "reference_key": "",
                                                "comment": ""
                                            },
                                            {
                                                "column": "weight_kg",
                                                "type": "int",
                                                "primary_key": False,
                                                "reference_key": "",
                                                "comment": ""
                                            }
                                        ]
                                    }
                                ]
                            }
                        }).json()

    print(res)
