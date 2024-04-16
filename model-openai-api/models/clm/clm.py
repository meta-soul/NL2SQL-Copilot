#!/usr/bin/env python
# coding=utf-8
import torch
import os
from typing import Dict, Union, Optional

import torch
from torch.nn import Module
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig

from .chat import do_chat, do_chat_stream

def init_clm(model_path: str, running_device: str = "GPU", gpus: int = 1, 
        dtype=torch.float16, quantization_bit: int = None, **kwargs):
    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True, 
        cache_dir=kwargs.get("cache_dir"), 
        force_download=kwargs.get("force_download", False))

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True,
         cache_dir=kwargs.get("cache_dir"), 
         force_download=kwargs.get("force_download", False))

    gpu_id = kwargs.get("gpu_id", None)
    if running_device.upper() == "GPU":
        model = load_model_on_gpus(model_path, gpus, 
            config=config, quantization_bit=quantization_bit, dtype=dtype, gpu_id=gpu_id)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_path, config=config, 
            trust_remote_code=True, torch_dtype=dtype,
            cache_dir=kwargs.get("cache_dir"))
        model = model.float()

    model.eval()
    model.running_device = ("cuda" if gpu_id is None else f"cuda:{gpu_id}") if running_device == "gpu" else "cpu"
    model.do_chat = do_chat
    model.do_chat_stream = do_chat_stream
    model.do_completion = model.do_chat
    model.do_completion_stream = model.do_chat_stream
    return tokenizer, model


def auto_configure_device_map(num_gpus: int, num_layers: int) -> Dict[str, int]:
    # total layers = num_layers(hidden) + word_embeddings + lm_head
    per_gpu_layers = (num_layers+2) / num_gpus

    # the input_ids will be put on the device same as model.device
    # and word_embeddings/lm_head should also be on the same device
    device_map = {'transformer.word_embeddings': 0,
                  'transformer.final_layernorm': 0, 'lm_head': 0}

    used = 2
    gpu_target = 0
    for i in range(num_layers):
        if used >= per_gpu_layers:
            gpu_target += 1
            used = 0
        assert gpu_target < num_gpus
        device_map[f'transformer.layers.{i}'] = gpu_target
        used += 1

    return device_map


def load_model_on_gpus(checkpoint_path: Union[str, os.PathLike], 
                       num_gpus: int = 2,
                       device_map: Optional[Dict[str, int]] = None, 
                       config: Optional[AutoConfig] = None, 
                       quantization_bit: int = None,
                       dtype = torch.float16,
                       gpu_id = None,
                       **kwargs) -> Module:
    if num_gpus < 2 and device_map is None:
        model = AutoModelForCausalLM.from_pretrained(
            checkpoint_path, config=config, 
            trust_remote_code=True, torch_dtype=dtype, 
            device_map="auto" if gpu_id is None else gpu_id, **kwargs)
        #model.cuda()
    else:
        if num_gpus > torch.cuda.device_count():
            raise Exception(f"need {num_gpus} GPU, but only has {torch.cuda.device_count()}")

        from accelerate import dispatch_model

        model = AutoModelForCausalLM.from_pretrained(
            checkpoint_path, config=config, 
            trust_remote_code=True, torch_dtype=dtype, **kwargs)

        num_layers = config.num_hidden_layers if config is not None else 32
        if device_map is None:
            device_map = auto_configure_device_map(num_gpus, num_layers)

        model = dispatch_model(model, device_map=device_map)

    return model
