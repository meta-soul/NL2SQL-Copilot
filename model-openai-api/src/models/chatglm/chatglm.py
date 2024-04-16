#!/usr/bin/env python
# coding=utf-8
## From: https://github.com/THUDM/ChatGLM-6B
import torch
import os
from typing import Dict, Union, Optional

from torch.nn import Module
from transformers import AutoModel, AutoTokenizer, AutoConfig

from .chat import do_chat, do_chat_stream

def load_ptuning_checkpoint(model, ptuning_checkpoint):
    if not ptuning_checkpoint:
        return model

    print(f">> Use chatglm ptuning checkpoint {ptuning_checkpoint}")
    prefix_state_dict = torch.load(os.path.join(ptuning_checkpoint, "pytorch_model.bin"))
    new_prefix_state_dict = {}
    for k, v in prefix_state_dict.items():
        if k.startswith("transformer.prefix_encoder."):
            new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
    model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
    return model


def init_chatglm(model_path: str, running_device: str, gpus: int, 
        ptuning_checkpoint: str = "", quantization_bit: int = None, 
        pre_seq_len: int = None, prefix_projection: bool = False, **kwargs):
    config = AutoConfig.from_pretrained(model_path, trust_remote_code=True, 
        cache_dir=kwargs.get("cache_dir"))
    config.pre_seq_len = pre_seq_len
    config.prefix_projection = prefix_projection

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True,
         cache_dir=kwargs.get("cache_dir"))

    gpu_id = kwargs.get("gpu_id", None)
    if running_device.upper() == "GPU":
        model = load_model_on_gpus(model_path, gpus, 
            config=config, ptuning_checkpoint=ptuning_checkpoint, 
            quantization_bit=quantization_bit, gpu_id=gpu_id)

        if ptuning_checkpoint and pre_seq_len:
            model.transformer.prefix_encoder.float()
    else:
        model = AutoModel.from_pretrained(model_path, config=config, 
            trust_remote_code=True,  cache_dir=kwargs.get("cache_dir"))
        model = load_ptuning_checkpoint(model, ptuning_checkpoint)
        model = model.float()

    model.eval()
    model.do_chat = do_chat
    model.do_chat_stream = do_chat_stream
    model.do_completion = model.do_chat
    model.do_completion_stream = model.do_chat_stream
    return tokenizer, model


def auto_configure_device_map(num_gpus: int) -> Dict[str, int]:
    # transformer.word_embeddings 占用1层
    # transformer.final_layernorm 和 lm_head 占用1层
    # transformer.layers 占用 28 层
    # 总共30层分配到num_gpus张卡上
    num_trans_layers = 28
    per_gpu_layers = 30 / num_gpus

    # bugfix: 在linux中调用torch.embedding传入的weight,input不在同一device上,导致RuntimeError
    # windows下 model.device 会被设置成 transformer.word_embeddings.device
    # linux下 model.device 会被设置成 lm_head.device
    # 在调用chat或者stream_chat时,input_ids会被放到model.device上
    # 如果transformer.word_embeddings.device和model.device不同,则会导致RuntimeError
    # 因此这里将transformer.word_embeddings,transformer.final_layernorm,lm_head都放到第一张卡上
    device_map = {'transformer.word_embeddings': 0,
                  'transformer.final_layernorm': 0, 'lm_head': 0}

    used = 2
    gpu_target = 0
    for i in range(num_trans_layers):
        if used >= per_gpu_layers:
            gpu_target += 1
            used = 0
        assert gpu_target < num_gpus
        device_map[f'transformer.layers.{i}'] = gpu_target
        used += 1

    return device_map


def load_model_on_gpus(checkpoint_path: Union[str, os.PathLike], num_gpus: int = 2,
                       device_map: Optional[Dict[str, int]] = None, 
                       config: Optional[AutoConfig] = None, 
                       ptuning_checkpoint: str = None, 
                       quantization_bit: int = None,
                       gpu_id: int = None,
                       **kwargs) -> Module:
    if num_gpus < 2 and device_map is None:
        model = AutoModel.from_pretrained(
            checkpoint_path, config=config, 
            trust_remote_code=True, **kwargs)
        
        if ptuning_checkpoint:
            model = load_ptuning_checkpoint(model, ptuning_checkpoint)

        if quantization_bit:
            model = model.quantize(quantization_bit)

        if gpu_id is not None:
            model = model.to(gpu_id)
            #model.device = f"cuda:{gpu_id}"

        model = model.half()
        #model.cuda()
    else:
        if num_gpus > torch.cuda.device_count():
            raise Exception(f"need {num_gpus} GPU, but only has {torch.cuda.device_count()}")

        from accelerate import dispatch_model

        model = AutoModel.from_pretrained(
            checkpoint_path, config=config, trust_remote_code=True, **kwargs).half()

        model = load_ptuning_checkpoint(model, ptuning_checkpoint)

        if device_map is None:
            device_map = auto_configure_device_map(num_gpus)

        model = dispatch_model(model, device_map=device_map)
        print(f"Device Map: {model.hf_device_map}\n")

    return model
