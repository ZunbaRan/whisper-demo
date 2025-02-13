from typing import Optional
from datetime import datetime
import requests
from fastapi import HTTPException
from .models import FollowEntriesResponse

class FollowService:
    BASE_URL = 'https://api.follow.is'
    
    @staticmethod
    def create_headers(cookie: str) -> dict:
        return {
            'accept': 'application/json',
            'content-type': 'application/json',
            'cookie': cookie,
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
            'x-app-name': 'Follow Web',
            'x-app-version': '0.3.3-beta.0'
        }
    
    @staticmethod
    async def feed_req(
        cookie: str,
        is_archived: bool = False,
        view: int = 4,
        published_after: Optional[str] = None
    ) -> FollowEntriesResponse:
        try:
            headers = FollowService.create_headers(cookie)
            
            payload = {
                "isArchived": is_archived,
                "view": view
            }
            
            if published_after:
                payload["publishedAfter"] = published_after
            
            response = requests.post(
                f'{FollowService.BASE_URL}/entries',
                headers=headers,
                json=payload
            )
            
            try:
                response.raise_for_status()
                return FollowEntriesResponse(**response.json())
            except requests.HTTPError as e:
                error_detail = f"HTTP {response.status_code}"
                try:
                    error_detail += f": {response.json()}"
                except:
                    error_detail += f": {response.text}"
                raise HTTPException(status_code=response.status_code, detail=error_detail)
            
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch entries: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    async def fetch_entries_with_count(cookie: str, num: int) -> FollowEntriesResponse:
        # 第一次调用，不带 publishedAfter
        result = await FollowService.feed_req(cookie)
        all_entries = result.data
        
        # 如果返回的数量小于请求的数量，继续获取
        while len(all_entries) < num:
            if not all_entries:  # 如果没有更多数据了
                break
                
            # 获取最后一条记录的发布时间
            last_published_at = all_entries[-1].entries.publishedAt
            
            # 使用最后一条记录的时间进行下一次请求
            next_result = await FollowService.feed_req(
                cookie=cookie,
                published_after=last_published_at
            )
            
            if not next_result.data:  # 如果没有新数据了
                break
                
            all_entries.extend(next_result.data)
        
        # 截取所需数量的条目
        all_entries = all_entries[:num]
        
        return FollowEntriesResponse(
            code=0,
            data=all_entries
        ) 