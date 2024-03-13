from .base import ServiceBase
from .openai import OpenaiService
from .seq2seq import Seq2seqService
from .llm import LLMService

def create_service(name, type, conf={}, **kwargs):
    if conf.get("status") == "disabled":
        return None
    if type == 'base':
        return ServiceBase(name, conf=conf, **kwargs)
    elif type == 'openai':
        return OpenaiService(name, conf=conf, **kwargs)
    elif type == 'seq2seq':
        return Seq2seqService(name, conf=conf, **kwargs)
    elif type == 'llm':
        return LLMService(name, conf=conf, **kwargs)
    return None
