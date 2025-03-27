from typing import Dict, List, Any, Optional, Tuple
import os
from fastapi import HTTPException
from services.transcription_service import TranscriptionService
from services.download_service import DownloadService
from services.db_service import DBService
from utils.file_utils import clean_filename
import traceback
import logging

class WorkflowService:
    def __init__(self, transcription_service: TranscriptionService):
        self.transcription_service = transcription_service
        self.download_service = DownloadService()
        self.db_service = DBService()
    
    async def _process_entry(self, entry: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        处理单个条目的通用逻辑
        
        Args:
            entry: 数据库条目信息
            
        Returns:
            Tuple[Dict, bool]: (处理结果, 是否成功)
        """
        entry_id = entry["id"]
        title = entry["title"]
        clean_title = clean_filename(title)
        file_path = os.path.join(self.download_service.download_dir, f"{clean_title}.mp3")
        
        result = {
            "id": entry_id,
            "title": title,
            "steps": []
        }
        
        try:
            # 1. 下载处理
            if entry["isDownload"] == "false":
                logging.info(f"下载音频文件: {title}")
                download_result = await self.download_service.download_single_file(entry_id)
                
                if not download_result["success"]:
                    error_msg = download_result.get("error", "Unknown download error")
                    logging.error(f"下载失败: {title}, 错误: {error_msg}")
                    result["steps"].append({
                        "step": "download",
                        "success": False,
                        "error": error_msg
                    })
                    return result, False
                
                logging.info(f"下载成功: {title}")
                result["steps"].append({
                    "step": "download",
                    "success": True
                })
            else:
                logging.info(f"音频文件已下载: {title}")
                result["steps"].append({
                    "step": "download",
                    "success": True,
                    "skipped": True
                })
            
            # 2. 转写处理
            if entry["isTranscription"] == "false":
                logging.info(f"处理音频文件: {title}")
                
                if not os.path.exists(file_path):
                    error_msg = f"音频文件不存在: {file_path}"
                    logging.error(error_msg)
                    result["steps"].append({
                        "step": "transcription",
                        "success": False,
                        "error": error_msg
                    })
                    return result, False
                
                transcription_result = await self.transcription_service.process_single_file(entry, file_path)
                
                if not transcription_result.get("success", False):
                    error_msg = transcription_result.get("error", "Unknown transcription error")
                    logging.error(f"转写失败: {title}, 错误: {error_msg}")
                    result["steps"].append({
                        "step": "transcription",
                        "success": False,
                        "error": error_msg
                    })
                    return result, False
                
                self.db_service.update_transcription_status(entry_id, True)
                logging.info(f"转写成功并更新状态: {title}")
                result["steps"].append({
                    "step": "transcription",
                    "success": True
                })
            else:
                logging.info(f"音频文件已转写: {title}")
                result["steps"].append({
                    "step": "transcription",
                    "success": True,
                    "skipped": True
                })
            
            result["success"] = True
            return result, True
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"处理条目失败: {error_msg}\n{traceback.format_exc()}")
            result["success"] = False
            result["error"] = error_msg
            return result, False

    async def process_single_entry(self, entry_id: str) -> Dict[str, Any]:
        """处理单个条目的工作流程"""
        try:
            logging.info(f"\n=== 开始处理条目 ID: {entry_id} ===")
            
            # 获取条目信息
            entry = self.db_service.get_entry_by_id(entry_id)
            if not entry:
                raise HTTPException(
                    status_code=404,
                    detail=f"Entry with ID {entry_id} not found"
                )
            
            # 处理条目
            result, _ = await self._process_entry(entry)
            logging.info(f"\n=== 条目处理完成 ===")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = str(e)
            logging.error(f"工作流程执行失败: {error_msg}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Workflow execution failed: {error_msg}"
            )

    async def run_feed_workflow(self, feed_name: str, limit: int = 10) -> Dict[str, Any]:
        """处理指定 feed 的工作流程"""
        try:
            logging.info(f"\n=== 开始处理 {feed_name} 工作流程 ===")
            
            # 1. 获取未处理的条目
            logging.info(f"\n1. 获取 {feed_name} 的未处理条目 (最多 {limit} 条)")
            entries = self.db_service.get_entries_by_query(
                "feed_title = ? AND (isDownload = 0 OR isTranscription = 0)",
                (feed_name,),
                limit=limit
            )
            
            if not entries:
                logging.info(f"没有找到 {feed_name} 的未处理条目")
                return {
                    "feed": feed_name,
                    "message": "No entries to process",
                    "processed": 0,
                    "success": [],
                    "failed": []
                }
            
            logging.info(f"找到 {len(entries)} 条未处理的条目")
            
            # 2. 处理每个条目
            success_entries = []
            failed_entries = []
            
            for entry in entries:
                result, success = await self._process_entry(entry)
                if success:
                    success_entries.append({
                        "id": result["id"],
                        "title": result["title"]
                    })
                else:
                    failed_entries.append({
                        "id": result["id"],
                        "title": result["title"],
                        "steps": result["steps"],
                        "error": result.get("error")
                    })
            
            logging.info(f"\n=== 工作流程完成 ===")
            logging.info(f"成功处理: {len(success_entries)} 条")
            logging.info(f"处理失败: {len(failed_entries)} 条")
            
            return {
                "feed": feed_name,
                "processed": len(entries),
                "success_count": len(success_entries),
                "failed_count": len(failed_entries),
                "success": success_entries,
                "failed": failed_entries
            }
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"工作流程执行失败: {error_msg}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Workflow execution failed: {error_msg}"
            ) 