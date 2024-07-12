# export SC_API_KEY=sk-xxxxxxxxx
# python test_siliconflow.py
import os
from langchain_openai import ChatOpenAI
sc_api_key = os.getenv("SC_API_KEY")
llm = ChatOpenAI(base_url="https://api.siliconflow.cn/v1",
                 api_key=sc_api_key,
                 model="zhipuai/glm4-9B-chat")

messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = llm.invoke(messages)
print(ai_msg)
print()
print(ai_msg.content)
