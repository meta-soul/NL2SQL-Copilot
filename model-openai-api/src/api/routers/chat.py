import json

from fastapi import APIRouter
from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from context import context
from api.auth import check_token
from api.model import ChatCompletionBody
from api.response import (generate_response, generate_stream_response_start, 
    generate_stream_response, generate_stream_response_stop)
from utils import torch_gc


router = APIRouter()

@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionBody, request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(torch_gc)

    check_token(request.headers, context.auth_tokens)

    if not context.llm_models:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "LLM model not load!")

    if body.model not in context.llm_models:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "LLM model not found!")
    model_point = context.llm_models[body.model]

    if "chat" not in model_point.tags:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Model isn't support chat!")

    if len(body.messages) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Messages empty!")

    msg = body.messages[-1]
    if msg.role != 'user':
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No User question Found!")
    question = msg.content

    history = []
    user_question = ''
    for message in body.messages:
        if message.role == 'system':
            history.append((message.content, "OK"))
        elif message.role == 'user':
            user_question = message.content
        elif message.role == 'assistant':
            assistant_answer = message.content
            history.append((user_question, assistant_answer))

    model_name = body.model
    gen_kwargs = {
        "temperature": body.temperature,
        "top_p": body.top_p,
        "max_tokens": body.max_tokens,
        "stop": body.stop or model_point.gen_kwargs.get("stop_token", None),
        "start": model_point.gen_kwargs.get("start_token", None),
    }
    print(f"prompt = {question}, history = {history}, model = {model_name}, gen_kwargs = {gen_kwargs}")

    if body.stream:
        async def eval_llm():
            first = True
            for response in model_point.model.do_chat_stream(
                    model_point.model, model_point.tokenizer, 
                    question, history, gen_kwargs):
                if first:
                    first = False
                    yield json.dumps(generate_stream_response_start(model=model_name),
                                    ensure_ascii=False)
                yield json.dumps(generate_stream_response(response, model=model_name), ensure_ascii=False)
            yield json.dumps(generate_stream_response_stop(model=model_name), ensure_ascii=False)
            yield "[DONE]"
        return EventSourceResponse(eval_llm(), ping=10000)
    else:
        response = model_point.model.do_chat(model_point.model, model_point.tokenizer, 
            question, history, gen_kwargs)
        return JSONResponse(content=generate_response(response, model=model_name))
