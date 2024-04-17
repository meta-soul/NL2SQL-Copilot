import json

import httpx
from loguru import logger
from fastapi import APIRouter
from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTask
from sse_starlette.sse import EventSourceResponse

from context import context
from api.model import ChatCompletionBody


async def forward(request: Request):
    """转发请求"""
    url_path = request.url.path
    url_path = url_path[len(context.route_prefix):]

    service_name, base_url, timeout = "", "", 300
    for service in context.services:
        if not url_path.startswith(service.route_prefix):
            continue
        service_name = service.name
        base_url = service.base_url
        timeout = service.timeout
        url_path = url_path[len(service.route_prefix):]
    
    try:
        payload = await request.json()
    except Exception as e:
        payload = {}
    headers = {k:v for k,v in dict(request.headers).items() if k in ["content-type", "authorization"]}

    if not base_url or not url_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Request url is invalid!"
        )

    #logger.info(f"[service={service_name}] [base_url={base_url}] [url_path={url_path}]")

    try:
        client = httpx.AsyncClient(base_url=base_url,
            http1=True, http2=False)

        query = None if not request.url.query else request.url.query.encode("utf-8")
        url = httpx.URL(path=url_path, query=query)

        req = client.build_request(
            request.method,
            url,
            headers=headers,
            content=request.stream(),
            timeout=timeout,
        )
        
        logger.info(f"[service={service_name}] [request url={req.url}] [request method={req.method}] [request payload={payload}]")

        r = await client.send(req, stream=True)
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

    aiter_bytes = r.aiter_bytes()

    logger.info(f"[service={service_name}] [response status={r.status_code}]")

    return StreamingResponse(
        aiter_bytes,
        status_code=r.status_code,
        media_type=r.headers.get("content-type"),
        background=BackgroundTask(r.aclose),
    )
