import os
import time
import string
import random

import torch

# default org and models name
ORG_NAME = os.environ.get('ORG_NAME', 'DMetalSoul')
GPT_MODEL_NAME = os.environ.get('GPT_MODEL_NAME', 'gpt-dmetalsoul')
CHAT_MODEL_NAME = os.environ.get('CHAT_MODEL_NAME', 'chat-dmetalsoul')
EMB_MODEL_NAME = os.environ.get('EMB_MODEL_NAME', 'embeding-dmetalsoul')

last_gc = 0

def torch_gc():
    # 使用 last_gc 变量来控制 gc 的频率，不多于 1min 一次
    global last_gc
    if time.time() - last_gc > 60:
        last_gc = time.time()
        if torch.cuda.is_available():
            device = torch.cuda.current_device()
            print(f"Emptying gpu cache {device}...")
            with torch.cuda.device(device):
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()

def current_time():
    return int(time.time())


def rand_id(n=29):
    return ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=n))

