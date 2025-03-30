"""深度研究服务的数据模型"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """聊天消息模型"""
    role: str
    content: str
    reasoning_content: Optional[str] = None


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[Message] = Field(default_factory=list)
    model: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """聊天响应模型"""
    choices: List[Dict[str, Any]]
    id: Optional[str] = None
    object: str = "chat.completion"
    created: Optional[int] = None
    model: Optional[str] = None 