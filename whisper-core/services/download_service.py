from typing import Dict, List, Any, Optional
import os
import aiohttp
import aiofiles
import pandas as pd
import time
import humanize
from fastapi import HTTPException
from utils.file_utils import clean_filename
import asyncio
import subprocess
import json
import tempfile
from services.db_service import DBService

class DownloadService:
    def __init__(self):
        self.download_dir = "./output/feed/audio"
        os.makedirs(self.download_dir, exist_ok=True)
        # 优先使用环境变量中的代理设置
        self.proxy = os.environ.get('https_proxy') or os.environ.get('http_proxy') or "http://127.0.0.1:7890"

    async def get_redirect_url(self, url: str, use_proxy: bool = False) -> str:
        """获取重定向后的 URL"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            'Accept': '*/*',
        }
        proxy = self.proxy if use_proxy else None
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy, allow_redirects=False) as response:
                if response.status in (301, 302, 303, 307, 308):
                    return str(response.headers.get('Location'))
        return url

    async def download_file(self, url: str, output_path: str, use_proxy: bool = False) -> None:
        # 先尝试使用 power shell  irm 命令下载
        temp_files = []
        absolute_output_path = os.path.abspath(output_path)
        # 确保输出目录存在
        os.makedirs(os.path.dirname(absolute_output_path), exist_ok=True)
        try:
            print(f"尝试使用 PowerShell irm 下载文件: {url}")
            print(f"目标路径: {absolute_output_path}")

            # 构建 irm 命令，确保 URL 和路径被正确引用
            # PowerShell 中字符串内的双引号通常需要转义 ($") 或使用单引号包围整个命令
            # 但这里写入文件，直接使用双引号通常是安全的
            irm_script = f'irm "{url}" -OutFile "{absolute_output_path}"'
            print(f"生成的 PowerShell 脚本内容: {irm_script}")

            # 创建临时脚本文件，使用 UTF-8 编码
            with tempfile.NamedTemporaryFile(suffix='.ps1', mode='w', delete=False, encoding='utf-8-sig') as f:
                f.write(irm_script)
                irm_script_path = f.name
                temp_files.append(irm_script_path)

            print(f"临时脚本路径: {irm_script_path}")

            # 执行 irm 脚本
            process = subprocess.Popen(
                ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', irm_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # 让 stdout 和 stderr 直接解码为文本 (Python 3.7+)
                encoding='utf-8'  # 或者指定明确的编码，如 'gbk' 或 'cp936' 如果 PowerShell 输出是中文环境的默认编码
            )

            stdout, stderr = process.communicate()

            print(f"PowerShell stdout:\n{stdout}")

            if process.returncode == 0:
                if os.path.exists(absolute_output_path) and os.path.getsize(absolute_output_path) > 0:
                    print("irm 下载成功")
                    size = os.path.getsize(absolute_output_path)
                    return {
                        "success": True,
                        "message": "使用 irm 命令下载成功",
                        "file_size_mb": round(size / 1024 / 1024, 2),
                        "file_path": absolute_output_path
                    }
                else:
                    # returncode 是 0，但文件不存在或为空
                    print("irm 执行声称成功，但输出文件不存在或为空。")
                    print(f"检查路径: {absolute_output_path}")
                    if stderr:  # 即使成功，也可能有警告信息
                        print(f"PowerShell stderr (即使成功了也可能有内容):\n{stderr}")
                    return {
                        "success": False,
                        "message": "irm 执行声称成功，但输出文件不存在或为空。",
                        "stdout": stdout,
                        "stderr": stderr,
                        "returncode": process.returncode
                    }
            else:
                # irm 下载失败
                print("irm 下载失败")
                print(f"PowerShell returncode: {process.returncode}")
                print(f"PowerShell stderr:\n{stderr}")  # <--- 关键：打印错误信息
                return {
                    "success": False,
                    "message": "irm 命令下载失败",
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": process.returncode
                }

        except Exception as e:
            print(f"Python 执行 PowerShell irm 下载过程中发生异常: {str(e)}")
            return {
                "success": False,
                "message": f"Python 执行 PowerShell irm 下载过程中发生异常: {str(e)}",
                "stdout": "",
                "stderr": str(e),
                "returncode": -1  # 自定义错误码
            }
        finally:
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                        print(f"已删除临时脚本: {temp_file}")
                except Exception as e_unlink:
                    print(f"删除临时脚本 {temp_file} 失败: {e_unlink}")



        """使用 PowerShell 下载文件"""
        # 先获取重定向后的 URL
        final_url = await self.get_redirect_url(url, use_proxy)
        print(f"重定向后的 URL: {final_url}")
        
        # 创建 PowerShell 命令
        ps_script = f'''
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"

$headers = @{{
    "Accept"="*/*"
    "Accept-Encoding"="identity;q=1, *;q=0"
    "Accept-Language"="zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
    "Referer"="{final_url}"
    "Sec-Fetch-Dest"="video"
    "Sec-Fetch-Mode"="no-cors"
    "Sec-Fetch-Site"="same-origin"
    "sec-ch-ua"='"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"'
    "sec-ch-ua-mobile"="?0"
    "sec-ch-ua-platform"='"Windows"'
}}

$response = Invoke-WebRequest -UseBasicParsing -Uri "{final_url}" -WebSession $session -Headers $headers -OutFile "{output_path}"
'''
        
        # 将 PowerShell 脚本保存到临时文件
        with tempfile.NamedTemporaryFile(suffix='.ps1', mode='w', delete=False) as f:
            f.write(ps_script)
            ps_script_path = f.name

        try:
            print("开始使用 PowerShell 下载...")
            
            # 执行 PowerShell 脚本
            process = subprocess.Popen(
                ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', ps_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    print(f"下载成功！文件大小: {size/1024/1024:.2f}MB")
                    return {
                        "success": True,
                        "message": "文件下载成功",
                        "file_size_mb": round(size/1024/1024, 2),
                        "file_path": output_path
                    }
                else:
                    raise Exception("文件下载失败")
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                raise Exception(f"PowerShell 执行失败: {error_msg}")
                
        except Exception as e:
            print(f"下载失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Download failed: {str(e)}"
            )
        finally:
            # 清理临时文件
            try:
                os.unlink(ps_script_path)
            except:
                pass

    async def download_audio(self, url: str, title: str) -> Dict[str, str]:
        """下载音频文件的入口方法"""
        try:
            # 构建输出路径
            output_dir = "./output/feed/audio"
            output_path = os.path.join(output_dir, f"{title}.mp3")
            
            # 下载文件（首先尝试直接下载）
            await self.download_file(url, output_path)
            
            return {
                "status": "success",
                "message": "File downloaded successfully",
                "path": output_path
            }
        except Exception as e:
            print(f"下载文件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def download_single_file(self, target_id: str) -> Dict[str, Any]:
        """下载指定ID的音频文件"""
        db_service = DBService()
        
        # 查找指定ID的记录
        entry = db_service.get_entry_by_id(target_id)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Entry with ID {target_id} not found")
        
        # 获取文件信息
        title = entry['title']
        url = entry['url']
        mime_type = entry['mime_type']
        
        # 检查是否是音频文件
        if mime_type != 'null' and 'audio' not in mime_type.lower():
            raise HTTPException(status_code=400, detail=f"File with ID {target_id} is not an audio file")
        
        # 检查URL是否有效
        if url == 'null':
            raise HTTPException(status_code=400, detail=f"No valid URL found for ID {target_id}")
        
        print(f"\n=== 开始下载单个文件 ===")
        print(f"ID: {target_id}")
        print(f"标题: {title}")
        
        clean_title = clean_filename(title)
        output_path = os.path.join(self.download_dir, f"{clean_title}.mp3")
        
        print(f"清理后的文件名: {clean_title}")
        print(f"URL: {url}")
        
        try:
            result = await self.download_file(url, output_path, True)
            print(f"\n下载完成: {output_path}")

            # 更新数据库中的下载状态
            db_service.update_download_status(target_id, True)

            return {
                "success": True,
                "title": title,
                "file_path": output_path
            }
        except Exception as e:
            error_msg = f"下载文件失败: {str(e)}"
            print(f"\n{error_msg}")

        # 如果power shell 下载失败，尝试使用 aiohttp 下载

        # 使用原有的下载方式
        start_time = time.time()
        downloaded_size = 0
        try:
            async with aiohttp.ClientSession() as session:
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

                                    print(f'\r下载进度: {progress:.1f}% | '
                                          f'速度: {humanize.naturalsize(speed)}/s | '
                                          f'已下载: {humanize.naturalsize(downloaded_size)} / {humanize.naturalsize(total_size)}',
                                          end='', flush=True)

                        print(f"\n下载完成: {output_path}")

                        # 更新数据库中的下载状态
                        db_service.update_download_status(target_id, True)

                        return {
                            "success": True,
                            "title": title,
                            "file_path": output_path
                        }
                    else:
                        error_msg = f"下载失败: HTTP状态码 {response.status}"
                        print(f"\n{error_msg}")
                        raise HTTPException(status_code=response.status, detail=error_msg)

        except Exception as e:
            error_msg = f"下载文件失败: {str(e)}"
            print(f"\n{error_msg}")
            import traceback
            print(f"错误详情:\n{traceback.format_exc()}")
            return {
                "success": False,
                "title": title,
                "error": str(e)
            }
