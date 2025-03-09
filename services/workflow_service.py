from typing import Dict, List, Any, Optional
import os
from fastapi import HTTPException
from services.transcription_service import TranscriptionService
from services.download_service import DownloadService
from services.db_service import DBService
from utils.file_utils import clean_filename

class WorkflowService:
    def __init__(self, transcription_service: TranscriptionService):
        self.transcription_service = transcription_service
        self.download_service = DownloadService()
        self.db_service = DBService()
    
    async def run_feed_workflow(self, feed_name: str, limit: int = 10) -> Dict[str, Any]:
        """处理指定 feed 的工作流程"""
        try:
            print(f"\n=== 开始处理 {feed_name} 工作流程 ===")
            
            # 1. 从数据库获取未处理的条目
            print(f"\n1. 获取 {feed_name} 的未处理条目 (最多 {limit} 条)")
            entries = self.db_service.get_entries_by_query(
                "feed_title = ? AND (isDownload = 0 OR isTranscription = 0)",
                (feed_name,),
                limit=limit
            )
            
            if not entries:
                print(f"没有找到 {feed_name} 的未处理条目")
                return {
                    "feed": feed_name,
                    "message": "No entries to process",
                    "processed": 0,
                    "success": [],
                    "failed": []
                }
            
            print(f"找到 {len(entries)} 条未处理的条目")
            
            # 2. 处理每个条目
            success_entries = []
            failed_entries = []
            
            for entry in entries:
                entry_id = entry["id"]
                title = entry["title"]
                clean_title = clean_filename(title)
                file_path = os.path.join(self.download_service.download_dir, f"{clean_title}.mp3")
                
                try:
                    # 检查是否需要下载
                    if entry["isDownload"] == "false":
                        print(f"\n2. 下载音频文件: {title}")
                        download_result = await self.download_service.download_single_file(entry_id)
                        
                        if not download_result["success"]:
                            print(f"下载失败: {title}")
                            failed_entries.append({
                                "id": entry_id,
                                "title": title,
                                "step": "download",
                                "error": download_result.get("error", "Unknown download error")
                            })
                            continue
                        
                        print(f"下载成功: {title}")
                    else:
                        print(f"\n2. 音频文件已下载: {title}")
                    
                    # 检查是否需要转写
                    if entry["isTranscription"] == "false":
                        print(f"\n3. 处理音频文件: {title}")
                        
                        # 检查文件是否存在
                        if not os.path.exists(file_path):
                            error_msg = f"音频文件不存在: {file_path}"
                            print(error_msg)
                            failed_entries.append({
                                "id": entry_id,
                                "title": title,
                                "step": "transcription",
                                "error": error_msg
                            })
                            continue
                        
                        # 转写音频
                        transcription_result = await self.transcription_service.process_single_file(entry, file_path)
                        
                        if not transcription_result.get("success", False):
                            print(f"转写失败: {title}")
                            failed_entries.append({
                                "id": entry_id,
                                "title": title,
                                "step": "transcription",
                                "error": transcription_result.get("error", "Unknown transcription error")
                            })
                            continue
                        
                        # 更新数据库中的转写状态
                        self.db_service.update_transcription_status(entry_id, True)
                        print(f"转写成功并更新状态: {title}")
                    else:
                        print(f"\n3. 音频文件已转写: {title}")
                    
                    # 处理成功
                    success_entries.append({
                        "id": entry_id,
                        "title": title
                    })
                    
                except Exception as e:
                    print(f"处理条目 {title} 失败: {str(e)}")
                    import traceback
                    print(f"错误详情:\n{traceback.format_exc()}")
                    failed_entries.append({
                        "id": entry_id,
                        "title": title,
                        "step": "processing",
                        "error": str(e)
                    })
            
            print(f"\n=== 工作流程完成 ===")
            print(f"成功处理: {len(success_entries)} 条")
            print(f"处理失败: {len(failed_entries)} 条")
            
            return {
                "feed": feed_name,
                "processed": len(entries),
                "success_count": len(success_entries),
                "failed_count": len(failed_entries),
                "success": success_entries,
                "failed": failed_entries
            }
            
        except Exception as e:
            print(f"工作流程执行失败: {str(e)}")
            import traceback
            print(f"错误详情:\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Workflow execution failed: {str(e)}"
            ) 