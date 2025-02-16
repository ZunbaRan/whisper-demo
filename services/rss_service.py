from typing import Optional, List, Any
import aiohttp
from fastapi import HTTPException
import os
import csv
from api.models import FollowEntriesResponse
from utils.file_utils import clean_filename
import asyncio
class RssService:
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
            headers = RssService.create_headers(cookie)
            
            payload = {
                "isArchived": is_archived,
                "view": view
            }
            
            if published_after:
                payload["publishedAfter"] = published_after
            
            print(f"发送请求: {RssService.BASE_URL}/entries")
            print(f"请求参数: {payload}")
            print(f"请求头: {headers}")  # 添加请求头信息的输出
            
            # 使用 aiohttp 替代 requests，因为我们在异步环境中
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{RssService.BASE_URL}/entries',
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        response_json = await response.json()
                        result = FollowEntriesResponse(**response_json)
                        print(f"请求成功，返回数据条数: {len(result.data) if result.data else 0}")
                        
                        # 处理本地化存储
                        RssService.save_entries_to_tsv(result.data)
                        
                        return result
                    else:
                        error_text = await response.text()
                        print(f"请求失败: HTTP {response.status}")
                        print(f"错误响应: {error_text}")
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"HTTP {response.status}: {error_text}"
                        )
        
        except aiohttp.ClientError as e:
            print(f"请求异常: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch entries: {str(e)}")
        except Exception as e:
            print(f"其他异常: {str(e)}")
            import traceback
            print(f"错误详情:\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def save_entries_to_tsv(entries: List[Any]) -> None:
        """将条目保存到TSV文件"""
        output_dir = "./output/feed"
        tsv_path = f"{output_dir}/feed.tsv"
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 读取现有数据（如果存在）
        existing_entries = {}
        if os.path.exists(tsv_path):
            with open(tsv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    # 清理现有数据中的特殊字符和'null'字符串
                    cleaned_row = {
                        k: (v.strip() if v and v.lower() != 'null' else 'null')
                        for k, v in row.items()
                    }
                    # 确保现有数据有 isDownload 字段
                    if 'isDownload' not in cleaned_row:
                        cleaned_row['isDownload'] = 'false'
                    existing_entries[clean_filename(cleaned_row['title'])] = cleaned_row
        
        # 准备新数据
        new_entries = []
        for entry in entries:
            entry_data = entry.entries
            attachments = getattr(entry_data, 'attachments', [])
            attachment = attachments[0] if attachments else {}
            
            # 获取并清理字段值
            def clean_value(value):
                if value is None:
                    return 'null'
                # 清理字符串中的特殊字符和空白
                cleaned = str(value).strip().replace('\ufffd', '').replace('\u2019', "'")
                return cleaned if cleaned else 'null'
            
            new_entry = {
                'id': clean_value(getattr(entry_data, 'id', None)),
                'title': clean_value(getattr(entry_data, 'title', None)),
                'publishedAt': clean_value(getattr(entry_data, 'publishedAt', None)),
                'url': clean_value(getattr(attachment, 'url', None)),
                'mime_type': clean_value(getattr(attachment, 'mime_type', None)),
                'isDownload': 'false'  # 新增数据默认为 false
            }
            
            # 如果条目不存在，添加到新数据列表
            clean_title = clean_filename(new_entry['title'])
            if new_entry['title'] != 'null' and clean_title not in existing_entries:
                new_entries.append(new_entry)
        
        # 合并现有数据和新数据
        all_entries = list(existing_entries.values()) + new_entries
        
        # 按 publishedAt 降序排序，处理'null'值
        all_entries.sort(
            key=lambda x: x['publishedAt'] if x['publishedAt'] != 'null' else '',
            reverse=True
        )
        
        # 写入所有数据到TSV文件
        if all_entries:
            fieldnames = ['id', 'title', 'publishedAt', 'url', 'mime_type', 'isDownload']
            with open(tsv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()
                writer.writerows(all_entries)

    @staticmethod
    async def fetch_entries_with_count(
        cookie: str, 
        num: Optional[int] = None,
        fetch_mode: str = "all"  # 可选值: "all" 或 "tillExistOne"
    ) -> FollowEntriesResponse:
        print(f"\n=== 开始获取数据 ===")
        if num:
            print(f"目标数量: {num}")
        print(f"获取模式: {fetch_mode}")
        
        # 第一次调用，不带 publishedAfter
        print("\n1. 第一次请求数据")
        result = await RssService.feed_req(cookie)
        all_entries = result.data
        print(f"获取到 {len(all_entries)} 条数据")
        
        # 检查是否需要继续获取数据
        def should_continue():
            if not all_entries:
                print("没有更多数据，退出循环")
                return False
            
            if num and len(all_entries) >= num:
                print(f"已达到目标数量 {num}，退出循环")
                return False
            
            # 如果是 tillExistOne 模式，检查最后一批数据是否有已存在的条目
            if fetch_mode == "tillExistOne":
                tsv_path = "./output/feed/feed.tsv"
                if os.path.exists(tsv_path):
                    with open(tsv_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f, delimiter='\t')
                        existing_titles = {clean_filename(row['title']) for row in reader}
                        
                    # 检查最后一批数据是否有重复
                    latest_batch = result.data if result else []
                    for entry in latest_batch:
                        clean_title = clean_filename(getattr(entry.entries, 'title', ''))
                        if clean_title in existing_titles:
                            print(f"发现已存在的条目标题: {getattr(entry.entries, 'title', '')}，退出循环")
                            return False
            
            return True
        
        request_count = 1
        # 如果需要继续获取
        while should_continue():
            # 获取最后一条记录的发布时间
            last_published_at = all_entries[-1].entries.publishedAt
            
            # 获取有效的 publishedAt
            valid_published_at = None
            for entry in reversed(all_entries):
                if entry.entries.publishedAt is not None:
                    valid_published_at = entry.entries.publishedAt
                    break
            
            published_after = valid_published_at or last_published_at
            print(f"\n{request_count + 1}. 发起后续请求")
            print(f"当前数据量: {len(all_entries)}")
            if num:
                print(f"目标数据量: {num}")
            print(f"使用的时间戳: {published_after}")
            
            # 使用有效的时间进行下一次请求
            next_result = await RssService.feed_req(
                cookie=cookie,
                published_after=published_after
            )
            
            if not next_result.data:  # 如果没有新数据了
                print("本次请求没有返回数据，退出循环")
                break
            
            print(f"本次获取到 {len(next_result.data)} 条新数据")
            all_entries.extend(next_result.data)
            request_count += 1
            
            # 更新用于下一次检查的 result
            result = next_result
            
            # 添加请求间隔，避免请求过于频繁
            await asyncio.sleep(1)
        
        # 如果设置了数量限制，截取所需数量的条目
        if num:
            all_entries = all_entries[:num]
        
        print(f"\n=== 数据获取完成 ===")
        print(f"总请求次数: {request_count}")
        print(f"最终获取数据量: {len(all_entries)}")
        if num and len(all_entries) < num:
            print(f"注意: 实际获取数据量少于目标数量，可能已经获取了所有可用数据")
        
        return FollowEntriesResponse(
            code=0,
            data=all_entries
        )