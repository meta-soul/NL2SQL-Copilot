# export SC_API_KEY=sk-xxxxxxxxx
# python test_nl2sql_request.p

import os
import requests
import json

sc_api_key = os.getenv("SC_API_KEY")

url = "http://127.0.0.1:18080/nl2sql/chatglm/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {sc_api_key}"
}

coding_requirement = \
'''
根据以下 Table Schema 和 Question, 将自然语言转换成SQL查询. 备注: 无. version: v3

Table Schema
CREATE TABLE student (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Student ID',
  name VARCHAR(50) NOT NULL COMMENT 'Student Name',
  gender VARCHAR(10) NOT NULL COMMENT 'Student Gender',
  birthday DATE NOT NULL COMMENT 'Student Birthday',
  address VARCHAR(100) NOT NULL COMMENT 'Student Address',
  phone VARCHAR(20) NOT NULL COMMENT 'Student Contact'
) COMMENT 'Student Information Table';

CREATE TABLE course (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Course ID',
  name VARCHAR(50) NOT NULL COMMENT 'Course Name',
  teacher VARCHAR(50) NOT NULL COMMENT 'Course Teacher',
  credit INT NOT NULL COMMENT 'Course Credits'
) COMMENT 'Course Table';

CREATE TABLE student_course (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Relationship ID',
  student_id INT NOT NULL COMMENT 'Student ID',
  course_id INT NOT NULL COMMENT 'Course ID',
  FOREIGN KEY (student_id) REFERENCES student(id),
  FOREIGN KEY (course_id) REFERENCES course(id)
) COMMENT 'Student Course Enrollment Table';

CREATE TABLE score (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Score ID',
  student_id INT NOT NULL COMMENT 'Student ID',
  course_id INT NOT NULL COMMENT 'Course ID',
  score INT NOT NULL COMMENT 'Score',
  FOREIGN KEY (student_id) REFERENCES student(id),
  FOREIGN KEY (course_id) REFERENCES course(id)
) COMMENT 'Student Score Table';

Question: Retrieve the scores of a student named Xiao Ming
'''

data = {
    "model": "zhipuai/glm4-9B-chat",
    "stream": False,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful coding assistant that can use SQL language. Please give SQL code according to the user requirements."
        },
        {
            "role": "user",
            "content": coding_requirement
        }
    ]
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.text)