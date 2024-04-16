import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from .chat import do_chat, do_chat_stream

def init_seq2seq(model_path: str, device: str, num_gpus: int, **kwargs):
    if device == "cpu":
        hf_kwargs = {}
    elif device == "gpu":
        hf_kwargs = {"torch_dtype": torch.float16}
        #hf_kwargs["device_map"] = "sequential" # This is important for not the same VRAM sizes
    else:
        raise ValueError(f"Invalid device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(model_path, cache_dir=kwargs.get('cache_dir'))
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path, cache_dir=kwargs.get('cache_dir'), **hf_kwargs)

    gpu_id = kwargs.get("gpu_id", None)
    model.eval()
    model.running_device = ("cuda" if gpu_id is None else f"cuda:{gpu_id}") if device == "gpu" else "cpu"
    model.to(model.running_device)
    model.encoder = model.get_encoder()
    model.decoder = model.get_decoder()
    model.do_chat = do_chat
    model.do_chat_stream = do_chat_stream
    #model.do_completion = model.do_chat
    #model.do_completion_stream = model.do_chat_stream
    return tokenizer, model
