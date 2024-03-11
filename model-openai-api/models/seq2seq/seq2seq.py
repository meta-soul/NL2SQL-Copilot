import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from .chat import do_chat, do_chat_stream

def init_seq2seq(model_path: str, device: str, num_gpus: int, **kwargs):
    if device == "cpu":
        kwargs = {}
    elif device == "gpu":
        kwargs = {"torch_dtype": torch.float16}
        kwargs["device_map"] = "sequential"  # This is important for not the same VRAM sizes
    else:
        raise ValueError(f"Invalid device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(model_path, cache_dir=kwargs.get('cache_dir'))
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path, **kwargs)

    model.running_device = "cuda" if device == "gpu" else "cpu"
    model.encoder = model.get_encoder()
    model.decoder = model.get_decoder()
    model.do_chat = do_chat
    model.do_chat_stream = do_chat_stream
    #model.do_completion = model.do_chat
    #model.do_completion_stream = model.do_chat_stream
    return tokenizer, model
