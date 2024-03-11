#!usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ModelFootpoint:
    name: str
    type: str
    model: any = None
    tokenizer: any = None
    tags: List[str] = field(default_factory=list)
    gen_kwargs: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Context:
    host: str = ""
    port: int = None
    cache_dir: str = "./.cache"
    llm_models: Dict[str, ModelFootpoint] = field(default_factory=dict)
    emb_models: Dict[str, ModelFootpoint] = field(default_factory=dict)
    auth_tokens: List[str] = field(default_factory=list)

# a global instance to keep context info
context = Context("127.0.0.1", None, "./.cache", {}, {}, [])
