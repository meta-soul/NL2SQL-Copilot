from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field


# Schema Linking Payload
class SchemaLinkingBody(BaseModel):

    model: str
    # Python 3.8 does not support str | List[str]
    question: Any
    db:Any
    table_threshold: float = -1
    column_threshold: float = -1
    show_table_nums: int = -1
    show_column_nums: int = -1
    sort:bool = None



