from typing import List, Optional, Any, Union

from utils import (rand_id, current_time, CHAT_MODEL_NAME, 
    GPT_MODEL_NAME, EMB_MODEL_NAME)

def generate_embedding_response(data: List[Union[float, List[float]]], model: str = ""):
    return {
        "object": "list",
        "data": data,
        "model": model or EMB_MODEL_NAME,
        # TODO
        "usage": {
            "prompt_tokens": 0,
            "total_tokens": 0
        }
    }

def generate_response(content: str, chat: bool = True, model: str = ""):
    """
    生成非流式的响应内容，同时支持对话和补全模型
    """
    if chat:
        return {
            "id": f"chatcmpl-{rand_id()}",
            "object": "chat.completion",
            "created": current_time(),
            "model": model or CHAT_MODEL_NAME,
            # TODO: usage
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
            "choices": [{
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop", "index": 0}
            ]
        }
    else:
        return {
            "id": f"cmpl-{rand_id()}",
            "object": "text_completion",
            "created": current_time(),
            "model": model or GPT_MODEL_NAME,
            "choices": [
                {
                "text": content,
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop"
                }
            ],
            # TODO: usage 
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }


def generate_stream_response_start(content: str = "", chat: bool = True, model: str = ""):
    """
    流式响应头，仅用于对话模型，响应内容为空
    """
    assert chat, "Only support for chat response!"
    return {
        "id": f"chatcmpl-{rand_id()}",
        "object": "chat.completion.chunk", 
        "created": current_time(),
        "model": model or CHAT_MODEL_NAME,
        "choices": [{"delta": {"role": "assistant"}, "index": 0, "finish_reason": None}]
    }


def generate_stream_response(content: str, chat: bool = True, model: str = ""):
    """
    流式响应块，同时用于对话和补全模型
    """
    if chat:
        return {
            "id": f"chatcmpl-{rand_id()}",
            "object": "chat.completion.chunk",
            "created": current_time(),
            "model": model or CHAT_MODEL_NAME,
            "choices": [{
                "delta": {"content": content}, "index": 0, "finish_reason": None
            }],
        }
    else:
        return {
            "id":f"cmpl-{rand_id()}",
            "object":"text_completion",
            "created":current_time(),
            "choices":[{
                "text": content,
                "index": 0,
                "logprobs": None,
                "finish_reason": None,
            }],
            "model": model or GPT_MODEL_NAME
        }


def generate_stream_response_stop(content: str = "", chat: bool = True, model: str = ""):
    """
    流式响应尾，同时用于对话和补全模型，响应内容为空
    """
    if chat:
        return {"id": f"chatcmpl-{rand_id()}",
            "object": "chat.completion.chunk", 
            "created": current_time(),
            "model": model or CHAT_MODEL_NAME,
            "choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}]
        }
    else:
        return {
            "id":f"cmpl-{rand_id()}",
            "object":"text_completion",
            "created":current_time(),
            "choices":[
                {"text":"","index":0,"logprobs":None,"finish_reason":"stop"}],
            "model": model or GPT_MODEL_NAME,
        }
