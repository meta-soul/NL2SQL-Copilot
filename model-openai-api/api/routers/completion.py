import json

from fastapi import APIRouter
from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from context import context
from api.auth import check_token
from api.model import CompletionBody
from api.response import (generate_response, generate_stream_response_start, 
    generate_stream_response, generate_stream_response_stop)
from utils import torch_gc


router = APIRouter()

@router.post("/v1/completions")
async def completions(body: CompletionBody, request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(torch_gc)

    check_token(request.headers, context.auth_tokens)

    if not context.llm_models:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "LLM model not load!")

    if body.model not in context.llm_models:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "LLM model not found!")

    model_point = context.llm_models[body.model]
    if "completion" not in model_point.tags:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not support completion!")

    print(f"prompt = {body.prompt}")

    if body.stream:
        async def eval_llm():
            for response in model_point.model.do_completion_stream(
                    model_point.model, model_point.tokenizer, body.prompt, [], {
                        "temperature": body.temperature,
                        "top_p": body.top_p,
                        "max_tokens": body.max_tokens,
                    }):
                yield json.dumps(generate_stream_response(response, chat=False, model=body.model), ensure_ascii=False)
            yield json.dumps(generate_stream_response_stop(chat=False, model=body.model), ensure_ascii=False)
            yield "[DONE]"
        return EventSourceResponse(eval_llm(), ping=10000)
    else:
        response = model_point.model.do_completion(model_point.model, model_point.tokenizer, body.prompt, [], {
            "temperature": body.temperature,
            "top_p": body.top_p,
            "max_tokens": body.max_tokens,
        })
        return JSONResponse(content=generate_response(response, chat=False, model=body.model))
