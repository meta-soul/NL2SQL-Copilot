#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import random
import string
from typing import List, Optional, Any, Union

from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware


from api.routers import schema_linking as schema_linking_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# 将一个路由器添加到 FastAPI 应用程序的方式
app.include_router(schema_linking_router.router)

