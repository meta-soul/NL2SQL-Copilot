import subprocess
import requests


def chat_with_chatgpt(prompt):
    res = requests.post(
        # "http://im-api.dmetasoul.com/nl2sql/v1/chat/completions",
        "http://127.0.0.1:18021/nl2sql/intermediate/v1/chat/completions",
          headers = {
              "Content-Type": "application/json",
              "Authorization": f"Bearer ak_84ff9c1c-4758-494b-b6fd-2f21f06650c3"
          },
          json={
              "model": "gpt-3.5-turbo",
              # "messages":  [{"role": "user", "content": "Question: 名人堂一共多少球员 <sep> Tables: hall_of_fame: player_id , yearid , votedby , ballots , needed , votes , inducted , category , needed_note ; player: player_id , birth_year , birth_month , birth_day , birth_country , birth_state , birth_city , death_year , death_month , death_day , death_country , death_state , death_city , name_first , name_last , name_given , weight ; player_award: player_id , award_id , year , league_id , tie , notes ; player_award_vote: award_id , year , league_id , player_id , points_won , points_max , votes_first ; salary: year , team_id , league_id , player_id , salary ; primary keys: hall_of_fame.player_id , player.player_id , player_award.player_id , player_award_vote.player_id , salary.player_id ; foreign keys: player.player_id = hall_of_fame.player_id , player_award.player_id = hall_of_fame.player_id , player_award_vote.player_id = hall_of_fame.player_id , salary.player_id = hall_of_fame.player_id <sep>"}],
              "messages":[
        {
            "role": "user",
            "content": '''根据以下 table properties 和 Question, 将自然语言转换成SQL查询. 备注: 无. version: v3\nMYSQL SQL database: DEMO, with their properties:\n\nCREATE TABLE `buyer` (\n
  `id` int NOT NULL,\n  `name` varchar(255) DEFAULT NULL,\n  `gender` varchar(255) DEFAULT NULL,\n  PRIMARY KEY (`id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci\
n\nCREATE TABLE `example_table` (\n  `id` int DEFAULT NULL COMMENT '唯一标识',\n  `name` varchar(50) DEFAULT NULL COMMENT '姓名'\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0
900_ai_ci COMMENT='这是一个示例表'\n\nCREATE TABLE `inventory` (\n  `id` int NOT NULL,\n  `product_id` int DEFAULT NULL,\n  `quantity` int DEFAULT NULL,\n  PRIMARY KEY (`id`),\n  KEY `pro
duct_id` (`product_id`),\n  CONSTRAINT `inventory_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci\n\nCRE
ATE TABLE `merchant` (\n  `id` int NOT NULL,\n  `name` varchar(255) DEFAULT NULL,\n  `address` varchar(255) DEFAULT NULL,\n  `contact_number` varchar(255) DEFAULT NULL,\n  PRIMARY KEY (`i
d`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci\n\nCREATE TABLE `order_delivery` (\n  `id` int NOT NULL,\n  `order_id` int DEFAULT NULL,\n  `delivery_date` date DE
FAULT NULL,\n  PRIMARY KEY (`id`),\n  KEY `order_id` (`order_id`),\n  CONSTRAINT `order_delivery_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)\n) ENGINE=InnoDB DEFAULT CHARS
ET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci\n\nCREATE TABLE `orders` (\n  `id` int NOT NULL,\n  `buyer_id` int DEFAULT NULL,\n  `product_id` int DEFAULT NULL,\n  `quantity` int DEFAULT NULL,\n 
 `order_date` date DEFAULT NULL,\n  PRIMARY KEY (`id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci\n\nCREATE TABLE `product` (\n  `id` int NOT NULL,\n  `name` varc
har(255) DEFAULT NULL,\n  `price` decimal(10,2) DEFAULT NULL,\n  `merchant_id` int DEFAULT NULL,\n  PRIMARY KEY (`id`),\n  KEY `merchant_id` (`merchant_id`),\n  CONSTRAINT `product_ibfk_1
` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci\n\nCREATE TABLE `score` (\n  `id` int NOT NULL AUTO_INCREMEN
T COMMENT '成绩ID',\n  `student_id` int DEFAULT NULL COMMENT '学生ID',\n  `grade` varchar(10) DEFAULT NULL COMMENT '年级',\n  `class` varchar(10) DEFAULT NULL COMMENT '班级',\n  `year` in
t DEFAULT NULL COMMENT '年份',\n  `chinese_score` int DEFAULT NULL COMMENT '语文成绩',\n  `math_score` int DEFAULT NULL COMMENT '数学成绩',\n  `english_score` int DEFAULT NULL COMMENT '英
语成绩',\n  `science_score` int DEFAULT NULL COMMENT '理综成绩',\n  `humanities_score` int DEFAULT NULL COMMENT '文综成绩',\n  `overall_score` int DEFAULT NULL COMMENT '综合成绩',\n  PRIM
ARY KEY (`id`),\n  KEY `student_id` (`student_id`),\n  CONSTRAINT `score_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `student` (`id`)\n) ENGINE=InnoDB AUTO_INCREMENT=95 DEFAULT CHARSET=
utf8mb4 COLLATE=utf8mb4_0900_ai_ci\n\nCREATE TABLE `student` (\n  `id` int NOT NULL AUTO_INCREMENT COMMENT '学生ID',\n  `name` varchar(50) DEFAULT NULL COMMENT '学生姓名',\n  `gender` var
char(10) DEFAULT NULL COMMENT '学生性别',\n  PRIMARY KEY (`id`)\n) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学生表'\n\n\nQuestion: 学生的数学成绩怎么样？'''
        }
    ],
        "temperature": 0.1,
          }).json()

    return res

print(chat_with_chatgpt(1))