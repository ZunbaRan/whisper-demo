from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class Media(BaseModel):
    url: Optional[str] = None
    type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    blurhash: Optional[str] = None

class Attachment(BaseModel):
    url: Optional[str] = None
    mime_type: Optional[str] = None
    size_in_bytes: Optional[str] = None
    duration_in_seconds: Optional[Union[str, int]] = None

class Entry(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    guid: Optional[str] = None
    author: Optional[str] = None
    authorUrl: Optional[str] = None
    authorAvatar: Optional[str] = None
    insertedAt: Optional[str] = None
    publishedAt: Optional[str] = None
    media: Optional[List[Media]] = None
    categories: Optional[Any] = None
    attachments: Optional[List[Attachment]] = None
    extra: Optional[Any] = None
    language: Optional[str] = None

class Feed(BaseModel):
    type: Optional[str] = None
    id: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    siteUrl: Optional[str] = None
    image: Optional[str] = None
    errorMessage: Optional[str] = None
    errorAt: Optional[str] = None
    ownerUserId: Optional[str] = None

class Subscription(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None

class FollowEntryItem(BaseModel):
    read: Optional[bool] = None
    view: Optional[int] = None
    entries: Optional[Entry] = None
    feeds: Optional[Feed] = None
    collections: Optional[Dict[str, Any]] = None
    subscriptions: Optional[Subscription] = None
    settings: Optional[Dict[str, Any]] = {}

class FollowEntriesResponse(BaseModel):
    code: Optional[int] = None
    data: Optional[List[FollowEntryItem]] = None 