import sys
sys.path.append('./')

import re

from nl2sql.schema.mysql import TableSchema, DatabaseSchema

s = r"""CREATE TABLE `race` (
  `id` int NOT NULL COMMENT '列名：种族id；注释：种族id',
  `race` varchar(256) DEFAULT NULL COMMENT '列名：种族；注释：超级英雄的种族\n常识：\n在超级英雄的故事背景下，超级英雄的种族是指超级英雄根据这些身体特征所属的特定人群。\n比如种族：Alien、Cyborg、Gungan等。',
  PRIMARY KEY (`id`)
);

CREATE TABLE `superhero` (
  `id` int NOT NULL COMMENT '列名：超级英雄id；注释：超级英雄id',
  `superhero_name` varchar(256) DEFAULT NULL COMMENT '列名：超级英雄的名字；注释：超级英雄的名字',
  `full_name` varchar(256) DEFAULT NULL COMMENT '列名：超级英雄的全名；注释：超级英雄的全名',
  `gender_id` int DEFAULT NULL COMMENT '列名：性别id；注释：性别id',
  `eye_colour_id` int DEFAULT NULL COMMENT '列名：眼睛颜色id；注释：眼睛颜色id',
  `hair_colour_id` int DEFAULT NULL COMMENT '列名：头发颜色id；注释：头发颜色id',
  `skin_colour_id` int DEFAULT NULL COMMENT '列名：皮肤颜色id；注释：皮肤颜色id',
  `race_id` int DEFAULT NULL COMMENT '列名：种族id；注释：种族id',
  `publisher_id` int DEFAULT NULL COMMENT '列名：发行商id；注释：发行商id',
  `alignment_id` int DEFAULT NULL COMMENT '列名：阵营id；注释：阵营id',
  `height_cm` int DEFAULT NULL COMMENT '列名：身高；注释：身高，单位厘米（cm）',
  `weight_kg` int DEFAULT NULL COMMENT '列名：体重；注释：体重，单位公斤（kg）',
  PRIMARY KEY (`id`),
  KEY `gender_id` (`gender_id`),
  KEY `eye_colour_id` (`eye_colour_id`),
  KEY `hair_colour_id` (`hair_colour_id`),
  KEY `skin_colour_id` (`skin_colour_id`),
  KEY `race_id` (`race_id`),
  KEY `publisher_id` (`publisher_id`),
  KEY `alignment_id` (`alignment_id`),
  CONSTRAINT `superhero_ibfk_1` FOREIGN KEY (`gender_id`) REFERENCES `gender` (`id`),
  CONSTRAINT `superhero_ibfk_2` FOREIGN KEY (`eye_colour_id`) REFERENCES `colour` (`id`),
  CONSTRAINT `superhero_ibfk_3` FOREIGN KEY (`hair_colour_id`) REFERENCES `colour` (`id`),
  CONSTRAINT `superhero_ibfk_4` FOREIGN KEY (`skin_colour_id`) REFERENCES `colour` (`id`),
  CONSTRAINT `superhero_ibfk_5` FOREIGN KEY (`race_id`) REFERENCES `race` (`id`),
  CONSTRAINT `superhero_ibfk_6` FOREIGN KEY (`publisher_id`) REFERENCES `publisher` (`id`),
  CONSTRAINT `superhero_ibfk_7` FOREIGN KEY (`alignment_id`) REFERENCES `alignment` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COMMENT='表名：超级英雄；注释：超级英雄的记录表，记录了超级英雄的详细信息，比如名字、全名、眼睛颜色id、头发颜色id、皮肤颜色id、种族id、发行商id、阵营id以及身高和体重等。'"""


db = DatabaseSchema.parse_from_str('superhero', s)
print(db)
print(db.name, db.comment, db.type)
print(db.get_primary_keys())
print(db.get_foreign_keys())

tbl = db.tables['superhero']
print(tbl)
print(tbl.get_primary_keys())
print(tbl.get_foreign_keys())

#exit()
#
#import sqlparse
#def get_table_name(tokens):
#    for token in reversed(tokens):
#        if token.ttype is None:
#            return token.value
#    return " "
#
#parse = sqlparse.parse(s)
#for stmt in parse:
#    # Get all the tokens except whitespaces
#    tokens = [t for t in sqlparse.sql.TokenList(stmt.tokens) if t.ttype != sqlparse.tokens.Whitespace]
#    is_create_stmt = False
#    for i, token in enumerate(tokens):
#        # Is it a create statements ?
#        if token.match(sqlparse.tokens.DDL, 'CREATE'):
#            is_create_stmt = True
#            continue
#        
#        # If it was a create statement and the current token starts with "("
#        if is_create_stmt and token.value.startswith("("):
#            # Get the table name by looking at the tokens in reverse order till you find
#            # a token with None type
#            print (f"table: {get_table_name(tokens[:i])}")
#
#            # Now parse the columns
#            txt = token.value
#            columns = txt[1:txt.rfind(")")].replace("\n","").split(",")
#            for column in columns:
#                c = ' '.join(column.split()).split()
#                c_name = c[0].replace('\"',"")
#                c_type = c[1]  # For condensed type information 
#                # OR 
#                #c_type = " ".join(c[1:]) # For detailed type information 
#                print (f"column: {c_name}")
#                print (f"date type: {c_type}")
#            print ("---"*20)
#            break
