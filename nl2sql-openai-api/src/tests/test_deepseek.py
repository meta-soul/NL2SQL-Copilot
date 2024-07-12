# export DS_API_KEY=sk-xxxxxxxxx
# python test_deepseek.py
import os
from langchain_openai import ChatOpenAI
api_key = os.getenv("DS_API_KEY")
llm = ChatOpenAI(base_url="https://api.deepseek.com",
                 api_key=api_key,
                 model="deepseek-coder")

coding_requirement = \
'''
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

Retrieve the scores of a student named Xiao Ming
'''

messages = [
    (
        "system",
        "You are a helpful coding assistant that can use sql languange, please give sql code according to the user requirements.",
    ),
    ("human", coding_requirement),
]
ai_msg = llm.invoke(messages)
print(ai_msg)
print()
print(ai_msg.content)
