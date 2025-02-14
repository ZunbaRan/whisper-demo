from typing import Optional, List, Any, Dict
from datetime import datetime
import requests
from fastapi import HTTPException
from .models import FollowEntriesResponse
import os
import csv
from core.transcriber import Transcriber, TranscriptionConfig
from utils.json_utils import extract_segments_info, format_transcription_to_text
import time
import aiohttp
import aiofiles
import pandas as pd
import asyncio
import humanize  # 用于格式化文件大小

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
        is_archived: bool = True,
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
            
            print(f"发送请求: {FollowService.BASE_URL}/entries")
            print(f"请求参数: {payload}")
            
            response = requests.post(
                f'{FollowService.BASE_URL}/entries',
                headers=headers,
                json=payload
            )
            
            try:
                response.raise_for_status()
                result = FollowEntriesResponse(**response.json())
                print(f"请求成功，返回数据条数: {len(result.data) if result.data else 0}")
                
                # 处理本地化存储
                FollowService.save_entries_to_tsv(result.data)
                
                return result
            except requests.HTTPError as e:
                print(f"HTTP错误: {e}")
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
                    existing_entries[cleaned_row['id']] = cleaned_row
        
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
            if new_entry['id'] != 'null' and new_entry['id'] not in existing_entries:
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
            fieldnames = ['id', 'title', 'publishedAt', 'url', 'mime_type', 'isDownload']  # 添加 isDownload 到字段列表
            with open(tsv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()
                writer.writerows(all_entries)
    
    @staticmethod
    async def fetch_entries_with_count(cookie: str, num: int) -> FollowEntriesResponse:
        print(f"\n=== 开始获取数据，目标数量: {num} ===")
        
        # 第一次调用，不带 publishedAfter
        print("\n1. 第一次请求数据")
        result = await FollowService.feed_req(cookie)
        all_entries = result.data
        print(f"获取到 {len(all_entries)} 条数据")
        
        request_count = 1
        # 如果返回的数量小于请求的数量，继续获取
        while len(all_entries) < num:
            if not all_entries:  # 如果没有更多数据了
                print("没有更多数据，退出循环")
                break
            
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
            print(f"目标数据量: {num}")
            print(f"使用的时间戳: {published_after}")
            
            # 使用有效的时间进行下一次请求
            next_result = await FollowService.feed_req(
                cookie=cookie,
                published_after=published_after
            )
            
            if not next_result.data:  # 如果没有新数据了
                print("本次请求没有返回数据，退出循环")
                break
            
            print(f"本次获取到 {len(next_result.data)} 条新数据")
            all_entries.extend(next_result.data)
            request_count += 1
            
            # 添加请求间隔，避免请求过于频繁
            await asyncio.sleep(1)
        
        # 截取所需数量的条目
        all_entries = all_entries[:num]
        
        print(f"\n=== 数据获取完成 ===")
        print(f"总请求次数: {request_count}")
        print(f"最终获取数据量: {len(all_entries)}")
        if len(all_entries) < num:
            print(f"注意: 实际获取数据量少于目标数量，可能已经获取了所有可用数据")
        
        return FollowEntriesResponse(
            code=0,
            data=all_entries
        )

class TranscriptionService:
    def __init__(self, config: TranscriptionConfig):
        self.config = config
        self.transcriber = Transcriber(config)
        
    async def process_audio_transcription(self, audio_path: str) -> Dict[str, Any]:
        """处理音频转写的核心逻辑"""
        # 转写步骤
        print("\n=== 开始转写 ===")
        start_time = time.time()
        transcriptions = self.transcriber.transcribe(audio_path=audio_path)
        transcribe_time = time.time() - start_time
        print(f"转写耗时: {transcribe_time:.2f}秒")

        # 对齐步骤
        print("\n=== 开始对齐 ===")
        start_time = time.time()
        transcriptions = self.transcriber.align_transcriptions(transcriptions)
        align_time = time.time() - start_time
        print(f"对齐耗时: {align_time:.2f}秒")

        # 说话人分离步骤
        print("\n=== 开始分离说话人 ===")
        start_time = time.time()
        transcriptions = self.transcriber.diarize_transcriptions(transcriptions)
        diarize_time = time.time() - start_time
        print(f"分离耗时: {diarize_time:.2f}秒")

        # 写入步骤
        start_time = time.time()
        self.transcriber.write_transcriptions(transcriptions=transcriptions)
        write_time = time.time() - start_time

        # 计算总时间
        total_time = transcribe_time + align_time + diarize_time + write_time
        
        return {
            "transcribe_time": round(transcribe_time, 2),
            "align_time": round(align_time, 2),
            "diarize_time": round(diarize_time, 2),
            "write_time": round(write_time, 2),
            "total_time": round(total_time, 2)
        }

    async def transcribe_audio(self, audio_path: str):
        """处理单个音频文件的转写请求"""
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        try:
            # 处理音频转写
            times = await self.process_audio_transcription(audio_path)
            
            # 获取输出文件路径
            filename = os.path.basename(audio_path)
            base_name = os.path.splitext(filename)[0]
            output_file = os.path.join("output", f"{base_name}.json")
            
            # 处理JSON并创建简化版本
            simplified_output_file = extract_segments_info(output_file)
            
            return {
                "status": "success",
                "message": "Transcription completed successfully",
                **times,
                "output_file": output_file,
                "simplified_output_file": simplified_output_file
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    async def batch_transcribe_downloaded_audio(self) -> Dict[str, List[str]]:
        """批量处理下载的音频文件"""
        audio_dir = "./output/feed/audio"
        if not os.path.exists(audio_dir):
            raise HTTPException(status_code=404, detail="Audio directory not found")
            
        success_files = []
        failed_files = []
        
        # 获取所有MP3文件
        audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.mp3')]
        
        if not audio_files:
            print("没有找到需要转写的音频文件")
            return {"success": [], "failed": []}
            
        print(f"\n=== 开始批量转写 {len(audio_files)} 个文件 ===")
        
        for index, audio_file in enumerate(audio_files, 1):
            audio_path = os.path.join(audio_dir, audio_file)
            base_name = os.path.splitext(audio_file)[0]
            txt_output_path = os.path.join(audio_dir, f"{base_name}.txt")
            
            # 如果已经存在对应的txt文件，跳过处理
            if os.path.exists(txt_output_path):
                print(f"\n[{index}/{len(audio_files)}] {audio_file} 已经转写过，跳过")
                continue
                
            print(f"\n[{index}/{len(audio_files)}] 开始处理: {audio_file}")
            
            try:
                # 转写音频
                result = await self.transcribe_audio(audio_path)
                
                # 将简化的JSON转换为文本格式
                format_transcription_to_text(
                    result['simplified_output_file'],
                    txt_output_path
                )
                
                success_files.append(base_name)
                print(f"处理完成: {txt_output_path}")
                
            except Exception as e:
                print(f"处理失败: {str(e)}")
                failed_files.append(base_name)
        
        print(f"\n=== 批量转写完成 ===")
        print(f"成功: {len(success_files)} 个文件")
        print(f"失败: {len(failed_files)} 个文件")
        
        return {
            "success": success_files,
            "failed": failed_files
        }

class DownloadService:
    def __init__(self):
        self.download_dir = "./output/feed/audio"
        os.makedirs(self.download_dir, exist_ok=True)
        
    async def download_pending_files(self) -> Dict[str, List[str]]:
        """下载所有未下载的音频文件"""
        tsv_path = "./output/feed/feed.tsv"
        if not os.path.exists(tsv_path):
            raise HTTPException(status_code=404, detail="Feed TSV file not found")
            
        # 读取TSV文件，确保 isDownload 列作为字符串处理
        df = pd.read_csv(tsv_path, sep='\t', dtype={'isDownload': str, 'id': str})  # 确保 id 也是字符串类型
        
        # 获取未下载的音频文件
        pending_files = df[
            (df['isDownload'].fillna('false').str.lower() == 'false') &  # 处理可能的空值
            (df['url'] != 'null') & 
            (df['mime_type'].str.contains('audio', na=False))
        ]
        
        total_files = len(pending_files)
        if total_files == 0:
            print("没有需要下载的文件")
            return {"success": [], "failed": []}
            
        print(f"\n=== 开始下载 {total_files} 个文件 ===")
        
        success_files = []
        failed_files = []
        
        async with aiohttp.ClientSession() as session:
            for index, row in pending_files.iterrows():
                file_id = str(row['id'])  # 确保 file_id 是字符串
                url = row['url']
                title = row['title']
                output_path = os.path.join(self.download_dir, f"{file_id}.mp3")
                
                print(f"\n[{index + 1}/{total_files}] 开始下载: {title}")
                print(f"文件ID: {file_id}")
                print(f"URL: {url}")
                
                try:
                    start_time = time.time()
                    downloaded_size = 0
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            # 获取文件总大小
                            total_size = int(response.headers.get('content-length', 0))
                            
                            # 打开文件准备写入
                            async with aiofiles.open(output_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                                    downloaded_size += len(chunk)
                                    
                                    # 计算下载进度和速度
                                    elapsed_time = time.time() - start_time
                                    if elapsed_time > 0:
                                        speed = downloaded_size / elapsed_time
                                        progress = (downloaded_size / total_size * 100) if total_size > 0 else 0
                                        
                                        # 清除当前行并打印进度
                                        print(f'\r下载进度: {progress:.1f}% | '
                                              f'速度: {humanize.naturalsize(speed)}/s | '
                                              f'已下载: {humanize.naturalsize(downloaded_size)} / {humanize.naturalsize(total_size)}',
                                              end='', flush=True)
                            
                            print(f"\n下载完成: {output_path}")
                            
                            # 更新TSV文件中的isDownload状态
                            df.loc[df['id'] == file_id, 'isDownload'] = 'true'
                            success_files.append(str(file_id))  # 确保添加的是字符串
                        else:
                            print(f"\n下载失败: HTTP状态码 {response.status}")
                            failed_files.append(str(file_id))  # 确保添加的是字符串
                except Exception as e:
                    print(f"\n下载文件 {file_id} 失败: {str(e)}")
                    failed_files.append(str(file_id))  # 确保添加的是字符串
                
                # 等待一小段时间再下载下一个文件
                await asyncio.sleep(1)
        
        # 保存更新后的TSV文件
        df.to_csv(tsv_path, sep='\t', index=False)
        
        # 打印最终统计信息
        print(f"\n=== 下载完成 ===")
        print(f"成功: {len(success_files)} 个文件")
        print(f"失败: {len(failed_files)} 个文件")
        
        return {
            "success": [str(id) for id in success_files],  # 确保所有 ID 都是字符串
            "failed": [str(id) for id in failed_files]     # 确保所有 ID 都是字符串
        } 