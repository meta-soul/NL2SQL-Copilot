from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field

# Embedding Payload
class EmbeddingBody(BaseModel):
    model: str
    # Python 3.8 does not support str | List[str]
    input: Any

# Chat Payload
class Message(BaseModel):
    role: str
    content: str


class ChatCompletionBody(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False
    max_tokens: Optional[int]
    temperature: Optional[float]
    top_p: Optional[float]
    stop: Union[List[str], str, None] = None

# Completion Payload
class CompletionBody(BaseModel):
    model: str = Field(
        title="ID of the model to use.", 
        description="You can use the List models API to see all of your available models."
    )
    prompt: Union[str, List[str]] = Field(
        title="string or array", 
        description="The prompt(s) to generate completions for, encoded as a string, array of strings, array of tokens, or array of token arrays."
    )
    stream: Optional[bool] = Field(
        default=False, 
        title="Whether to stream back partial progress. If set, tokens will be sent as data-only server-sent events as they become available, with the stream terminated by a data: [DONE] message."
    )
    max_tokens: Optional[int] = Field(
        default=16, 
        title="The maximum number of tokens to generate in the completion.", 
        description="The token count of your prompt plus max_tokens cannot exceed the model's context length."
    )
    temperature: Optional[float] = Field(
        default=0.7, 
        title="What sampling temperature to use, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."
    )
    top_p: Optional[float] = Field(
        default=1.0, 
        title="An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. We generally recommend altering this or temperature but not both."
    )
    stop: Union[List[str], str, None] = None
