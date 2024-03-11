from fastapi import APIRouter

from context import context
from utils import ORG_NAME, torch_gc, current_time
from api.auth import check_token

router = APIRouter()

@router.get("/v1/models")
def get_models():
    ret = {"data": [], "object": "list"}
    for name, mpoint in list(context.llm_models.items()) + list(context.emb_models.items()):
        ctime = current_time()
        ret['data'].append({
            "created": ctime,
            "id": name,
            "object": "model",
            "owned_by": ORG_NAME,
            "permission": [
                {
                    "created": ctime,
                    "id": "modelperm-fTUZTbzFp7uLLTeMSo9ks6oT",
                    "object": "model_permission",
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": False,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False
                }
            ],
            "root": name,
            "parent": None,
        })

    return ret
