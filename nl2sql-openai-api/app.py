#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import random
import string
from typing import List, Optional, Any, Union

from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from context import context
from api.routers import forward
from api.routers.chat import router as chat_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# chat for every service and url path
for service in context.services:
    name = service.name
    prefix = context.route_prefix + service.route_prefix
    app.include_router(chat_router, prefix=prefix, tags=[f"chat-{name}"])

# the general forward for every service and url path
#app.add_route(context.route_prefix + "/{api_path:path}",
#    forward.forward,
#    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"]
#)
