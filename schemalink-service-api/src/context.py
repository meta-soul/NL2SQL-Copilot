#!usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ModelFootpoint:
    name: str
    type: str
    model: any = None
    tokenizer: any = None
    table_threshold: float = 0
    column_threshold: float = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class Context:
    schema_linking_model: Dict[str, ModelFootpoint] = field(default_factory=dict)
    auth_tokens: List[str] = field(default_factory=list)
    service_args: Dict = field(default_factory=dict)
    result_args: Dict = field(default_factory=dict)


# a global instance to keep context info
context = Context({}, [], {})
