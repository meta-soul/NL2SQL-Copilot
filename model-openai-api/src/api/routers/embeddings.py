from fastapi import APIRouter
from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse

from context import context
from api.auth import check_token
from api.model import EmbeddingBody
from api.response import generate_embedding_response
from utils import torch_gc

router = APIRouter()

@router.post("/v1/embeddings")
async def embeddings(body: EmbeddingBody, request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(torch_gc)

    check_token(request.headers, context.auth_tokens)

    if not context.emb_models:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Embeddings model not load!")

    if body.model not in context.emb_models:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Embeddings model not found!")

    model_point = context.embs_model[body.model]
    if "embedding" not in model_point.tags:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not support embedding!")

    embeddings = model_point.model.encode(body.input)

    data = []
    if isinstance(body.input, str):
        data.append({
            "object": "embedding",
            "index": 0,
            "embedding": embeddings.tolist(),
        })
    else:
        for i, embed in enumerate(embeddings):
            data.append({
                "object": "embedding",
                "index": i,
                "embedding": embed.tolist(),
            })

    return JSONResponse(status_code=200, content=generate_embedding_response(data, model=body.model))
