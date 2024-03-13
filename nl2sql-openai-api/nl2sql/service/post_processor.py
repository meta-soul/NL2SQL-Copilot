import json

import orjson

from typing import List


class PostProcessorChatBytesParser(object):

    _processor_name = 'post_chat_bytes_parser'
    _processor_desc = 'Extract the SQL response content and return as Chat stream bytes.'

    def __init__(self, decoder_version="v1", *args, **kwargs):
        self.decoder_version = decoder_version

    def __call__(self, aiter_bytes, context={}):
        return self.run(aiter_bytes, context=context)

    def run(self, aiter_bytes, context={}):
        async def gen():
            prefix = ""
            prefix_mark = "| SQL:"
            eos_token = "</s>"
            is_prefix = True
            is_first = True
            async for chunk in aiter_bytes:
                if self.decoder_version == "v1":
                    yield chunk
                elif self.decoder_version == "v2":
                    # TODO: check some tokens missed
                    line = chunk.decode("utf-8").strip()
                    if line.startswith("data: "):
                        if is_first:
                            is_first = False
                            yield chunk
                        if not is_prefix:
                            yield chunk
                        else:
                            try:
                                row = orjson.loads(line[len('data: '):].strip())
                                content = row["choices"][0]["delta"].get("content", "")
                                prefix += content
                                i = prefix.find(prefix_mark)
                                if i > 0:
                                    is_prefix = False
                                    content = prefix[i+len(prefix_mark):]
                                    if content:
                                        row["choices"][0]["delta"]["content"] = content
                                        yield b"data: " + orjson.dumps(row) + b"\r\n"
                            except:
                                yield chunk
                    else:
                        try:
                            row = orjson.loads(line)
                            content = row["choices"][0]["message"]["content"]
                            i = content.find(prefix_mark)
                            if i > 0:
                                content = content[i+len(prefix_mark):].strip()
                            if content.endswith(eos_token):
                                content = content[:-len(eos_token)].strip()
                            row["choices"][0]["message"]["content"] = content
                            yield orjson.dumps(row)
                        except:
                            yield chunk
                else:
                    yield chunk
        return {"response": gen()}
