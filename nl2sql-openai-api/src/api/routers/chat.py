import json

import httpx
from httpx._decoders import LineDecoder
from loguru import logger
import orjson
from orjson import JSONDecodeError
from fastapi import APIRouter
from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer
from starlette.background import BackgroundTask
from sse_starlette.sse import EventSourceResponse

from context import context
from api.model import ChatCompletionBody
from nl2sql.service import create_service

router = APIRouter()
security = HTTPBearer()


def parse_chat_completions(bytes_: bytes):
    def _parse_iter_line_content(line: str):
        try:
            line_dict = orjson.loads(line)
            return line_dict["choices"][0]["delta"]["content"]
        except JSONDecodeError:
            return ""
        except KeyError:
            return ""

    decoder = LineDecoder()
    target_info = dict()
    txt_lines = decoder.decode(bytes_.decode("utf-8"))
    if not txt_lines:
        txt_lines = [bytes_.decode("utf-8")]
    if len(txt_lines) == 0:
        return target_info

    line0 = txt_lines[0]
    _start_token = "data: "
    if line0.startswith(_start_token):
        is_stream = True
        line0 = orjson.loads(line0[len(_start_token) :])
        msg = line0["choices"][0]["delta"]
    else:
        is_stream = False
        line0 = orjson.loads("".join(txt_lines))
        msg = line0["choices"][0]["message"]

    target_info["id"] = line0["id"]
    target_info["created"] = line0["created"]
    target_info["model"] = line0["model"]
    target_info["role"] = msg["role"]
    target_info["content"] = msg.get("content", "")
    target_info["usage"] = {
        "prompt_tokens": line0.get('usage', {}).get('prompt_tokens', 0),
        "completion_tokens": line0.get('usage', {}).get('completion_tokens', 0),
        "total_tokens": line0.get('usage', {}).get('total_tokens', 0),
    }

    if not is_stream:
        return target_info

    # loop for stream
    for line in txt_lines[1:]:
        if line in ("", "\n", "\n\n"):
            continue
        elif line.startswith(_start_token):
            target_info["content"] += _parse_iter_line_content(
                line[len(_start_token) :]
            )
        else:
            logger.warning(f"[parse_chat_completions] [error=line not startswith data: {line}]")
    return target_info


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionBody, request: Request, background_tasks: BackgroundTasks,
                           authorization: str = Depends(security)):
    """类似 OpenAI Chat API，具体参考：https://platform.openai.com/docs/api-reference/chat/create"""
    # parse service and payload
    url_path = request.url.path
    url_path = url_path[len(context.route_prefix):]

    service_name, base_url, timeout, service_type, service_conf = "", "", 300, "", {}
    for service in context.services:
        if not url_path.startswith(service.route_prefix):
            continue
        url_path = url_path[len(service.route_prefix):]
        service_name = service.name
        service_type = service.type
        base_url = service.base_url
        timeout = service.timeout
        service_conf = service.conf

    if not base_url or not url_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request url is invalid!"
        )

    try:
        payload = await request.json()
    except Exception as e:
        payload = {}
    headers = {k: v for k, v in dict(request.headers).items() if k in ["content-type", "authorization"]}

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body is empty!"
        )

    logger.info(
        f"[service={service_name}] [request url={request.url.path}] [request method={request.method}] [request payload={payload}]")

    service = create_service(service_name, service_type, conf=service_conf)
    service_status = "disabled" if service is None else body.service_status

    if service_status != "disabled":
        # service pre-process: make a new request payload for service
        pre_res = service.pre_process(payload)
        payload = pre_res.get('service_payload', payload)
        # service process: request model inference
        r = await service.process(base_url, url_path, request, headers, payload, timeout)
        aiter_bytes = r.aiter_bytes()  # an async generator
        # service post-process: extract the result sql
        post_res = service.post_process(aiter_bytes, pre_res=pre_res)
        aiter_bytes = post_res.get("response", aiter_bytes)
    else:
        # directly forward client request to the model inference service
        # service process: request nl2sql model api
        try:
            client = httpx.AsyncClient(base_url=base_url,
                                       http1=True, http2=False)

            query = None if not request.url.query else request.url.query.encode("utf-8")
            url = httpx.URL(path=url_path, query=query)

            req = client.build_request(
                request.method,
                url,
                headers=headers,
                # content=request.stream(),
                json=payload,
                timeout=timeout,
            )

            logger.info(
                f"[service={service_name}] [forward url={req.url}] [forward method={req.method}] [forward payload={payload}]")

            r = await client.send(req, stream=True)
            aiter_bytes = r.aiter_bytes()  # an async generator
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            error_info = (
                f"{type(e)}: {e} | "
                f"Please check if host={request.client.host} can access [{base_url}] successfully?"
            )
            logger.error(error_info)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_info
            )
        except Exception as e:
            logger.exception(f"{type(e)}:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e
            )

    logger.info(f"[service={service_name}] [forward response status={r.status_code}]")

    async def post_process_aiter_bytes(aiter_bytes):
        bytes_ = b""
        async for chunk in aiter_bytes:
            bytes_ += chunk
            yield chunk
        
        try:
            response = parse_chat_completions(bytes_)
        except Exception as e:
            logger.warning(f"[service={service_name}] [forward response content, error={e}]")
        else:
            logger.info(f"[service={service_name}] [forward response content={response}]")

    aiter_bytes = post_process_aiter_bytes(aiter_bytes)

    return StreamingResponse(
        aiter_bytes,
        status_code=r.status_code,
        media_type=r.headers.get("content-type"),
        background=BackgroundTask(r.aclose),
    )
