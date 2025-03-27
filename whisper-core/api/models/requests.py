from pydantic import BaseModel

class TranscriptionRequest(BaseModel):
    """音频转写请求模型"""
    audio_path: str
    settings: dict = {}

class FollowRequest(BaseModel):
    """Follow 请求模型"""
    cookie: str
    is_archived: bool = False
    view: int = 4

class FollowCountRequest(BaseModel):
    """Follow 批量请求模型"""
    cookie: str
    num: int = 10
    fetch_mode: str = "tillExistOne" 