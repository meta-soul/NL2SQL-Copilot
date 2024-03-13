#!usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class OpenaiService:
    name: str
    type: str
    base_url: str
    timeout: int
    route_prefix: str
    conf: Dict

@dataclass
class Context:
    host: str
    port: int
    route_prefix: str
    services: List[OpenaiService] = field(default_factory=list)

# a global instance to keep context info
context = Context("0.0.0.0", 10821, "", [])
