from typing import Dict, List
from fastapi import HTTPException
import os
from .rss_service import RssService
from .download_service import DownloadService
from .transcription_service import TranscriptionService
from utils.file_utils import clean_filename

class WorkflowService:
    def __init__(self, transcription_service: TranscriptionService = None):
        self.rss_service = RssService()
        self.download_service = DownloadService()
        # 如果传入了 transcription_service 就使用传入的，否则创建新的
        self.transcription_service = transcription_service or TranscriptionService()

    async def run_complete_workflow(self, cookie: str, mode: str = "increment") -> Dict[str, List[str]]:
        """运行完整的工作流程"""
        try:
            print("\n=== 开始完整工作流程 ===")
            
            # 1. 获取RSS数据
            print("\n1. 获取数据")
            result = await self.rss_service.fetch_entries_with_count(
                cookie=cookie,
                num=None,
                fetch_mode="tillExistOne",
                mode=mode
            )
            # 如果 mode 为 increment
            success_files = []
            failed_files = []
            for entry in result:
                try:
                    print(f"\n2. 下载音频文件: {entry['title']}")
                    download_result = await self.download_service.download_single_file(entry["id"])
                    if download_result["success"]:
                        success_files.append(entry["title"])
                    else:
                        failed_files.append(entry["title"])
                        continue

                    file_path = os.path.join(self.download_service.download_dir, f"{clean_filename(entry['title'])}.mp3")
                    print(f"\n3. 处理音频文件: {entry['title']}")
                    result = await self.transcription_service.process_single_file(entry["title"], file_path)
                    if result["success"]:
                        success_files.append(entry["title"])
                    else:
                        failed_files.append(entry["title"])
                except Exception as e:
                    print(f"处理条目 {entry['title']} 失败: {str(e)}")
                    failed_files.append(entry["title"])
                    continue
                    
            # 2. 下载音频文件
            # print("\n2. 下载音频文件")
            # download_result = await self.download_service.download_pending_files()
                
            # 3. 处理音频文件
            # 
            # for title in download_result["success"]:
            #     file_path = os.path.join(self.download_service.download_dir, f"{clean_filename(title)}.mp3")
            #     result = await self.transcription_service.process_single_file(title, file_path)
            #     
            #     if result["success"]:
            #         success_files.append(title)
            #     else:
            #         failed_files.append(title)
            
            return {
                "success": success_files,
                "failed": failed_files
            }
            
        except Exception as e:
            print(f"工作流程执行失败: {str(e)}")
            import traceback
            print(f"错误详情:\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Workflow execution failed: {str(e)}"
            ) 