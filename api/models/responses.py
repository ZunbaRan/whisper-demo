from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class TranscriptionResponse(BaseModel):
    """音频转写响应模型"""
    status: str
    message: str
    output_file: str
    simplified_output_file: str
    transcription_time: Optional[float] = None
    processing_time: Optional[float] = None

class BatchTranscriptionResponse(BaseModel):
    """批量转写响应模型"""
    success: List[str]
    failed: List[str]

class SingleDownloadResponse(BaseModel):
    """单个文件下载响应模型"""
    success: bool
    title: str
    file_path: Optional[str] = None
    error: Optional[str] = None

class DownloadResponse(BaseModel):
    """批量下载响应模型"""
    success: List[str]
    failed: List[str]

class FollowEntry(BaseModel):
    """Follow 条目模型"""
    id: str
    title: str
    publishedAt: datetime
    url: Optional[str] = None
    mime_type: Optional[str] = None

class FollowEntriesResponse(BaseModel):
    """Follow 条目响应模型"""
    code: int
    data: List[FollowEntry] 