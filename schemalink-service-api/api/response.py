from typing import List, Optional, Any, Union

from utils import rand_id, current_time

def generate_schema_linking_response(data: List[Union[float, List[float]]], model: str = ""):
    return {
        "object": "list",
        "data": data,
        "model": model,
    }
