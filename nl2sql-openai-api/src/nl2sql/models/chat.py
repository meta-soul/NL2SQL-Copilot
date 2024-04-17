import copy

import orjson


class ChatRequest:

    def __init__(self, payload):
        self.model = payload['model']
        self.messages = []
        for m in payload['messages']:
            self.messages.append({'role': m['role'], 'content': m['content']})
        self.payload = payload

    def get_messages(self):
        return self.messages[:]

    def get_content(self):
        return "" if len(self.messages) == 0 else self.messages[-1]['content']

    def set_content(self, content, role='user'):
        if self.messages:
            self.messages[-1]['role'] = role
            self.messages[-1]['content'] = content
        else:
            self.messages.append({'role': role, 'content': content})

    def get_payload(self):
        payload = copy.deepcopy(self.payload)
        payload['messages'] = copy.deepcopy(self.messages)
        return payload


class ChatResponse:

    def __init__(self, lines=[]):
        self.model = ""
        self.role = ""
        self.content = ""

    def parse_lines(self, lines=[]):
        if not lines:
            return

        line0 = lines[0]
        _start_token = "data: "
        if line0.startswith(_start_token):
            is_stream = True
            line0 = orjson.loads(line0[len(_start_token) :])
            msg = line0["choices"][0]["delta"]
        else:
            is_stream = False
            line0 = orjson.loads("".join(lines))
            msg = line0["choices"][0]["message"]

        self.model = line0["model"]
        self.role = msg["role"]
        self.content = msg.get("content", "")

        if not is_stream:
            return

        # loop for stream
        for line in lines[1:]:
            if line in ("", "\n", "\n\n"):
                continue
            elif line.startswith(_start_token):
                try:
                    content = orjson.loads(line[len(_start_token):])["choices"][0]["delta"]["content"]
                except JSONDecodeError:
                    content = ""
                except KeyError:
                    content = ""
                except Exception:
                    content = ""
                self.content += content

    def get_content(self):
        return self.content
