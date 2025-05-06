
from typing import List
from pydantic import BaseModel


    
class References(BaseModel):
    site: str
    url: str
    content: str
    title: str

class SearchRes(BaseModel):
    query: str
    summary_content: str
    search_references: List[References]

