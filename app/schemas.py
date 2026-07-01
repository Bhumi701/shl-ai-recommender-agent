from typing import List, Literal, Optional
from pydantic import BaseModel

class Recommendation(BaseModel):
    name: str
    url: str
    test_type: str

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    recommendations: Optional[List[Recommendation]] = []

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation] = []
    end_of_conversation: bool = False