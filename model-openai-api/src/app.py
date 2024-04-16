#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import random
import string
from typing import List, Optional, Any, Union

from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from api.routers import basic as basic_router
from api.routers import chat as chat_router
from api.routers import completion as completion_router
from api.routers import embeddings as embeddings_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


app.include_router(basic_router.router)
app.include_router(chat_router.router)
app.include_router(completion_router.router)
app.include_router(embeddings_router.router)
