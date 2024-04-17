if not __package__:
    from pre_processor import (PreProcessorChatPayloadParser, PreProcessorPromptParser, 
        PreProcessorPromptGenerator, PreProcessorChatPayloadGenerator,PreProcessorSchemaLinkingParser)
    from post_processor import PostProcessorChatBytesParser
else:
    from .pre_processor import (PreProcessorChatPayloadParser, PreProcessorPromptParser, 
        PreProcessorPromptGenerator, PreProcessorChatPayloadGenerator,PreProcessorSchemaLinkingParser)
    from .post_processor import PostProcessorChatBytesParser


processors = {}
# 解析 Chat Payload，得到提交的原始 prompt
processors[PreProcessorChatPayloadParser._processor_name] = PreProcessorChatPayloadParser
# 从原始 prompt 中解析出 db schema 和 question 等结构化输入
processors[PreProcessorPromptParser._processor_name] = PreProcessorPromptParser
# 对 db schema 和 question 进行 schema link 处理
processors[PreProcessorSchemaLinkingParser._processor_name] = PreProcessorSchemaLinkingParser
# 生成需要传递给 model api 的推理 prompt
processors[PreProcessorPromptGenerator._processor_name] = PreProcessorPromptGenerator
# 生成需要传递给 model api 的 Chat Payload
processors[PreProcessorChatPayloadGenerator._processor_name] = PreProcessorChatPayloadGenerator
# 从 model api 响应内容中提取 SQL 并作为 Chat bytes 返回
processors[PostProcessorChatBytesParser._processor_name] = PostProcessorChatBytesParser

def create_processor(name, *args, **kwargs):
    for proc_name, proc_cls in processors.items():
        if name == proc_name:
            return proc_cls(*args, **kwargs)
    return None
