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
                    raise Exception("文件下载失败：文件不存在")
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

    async def download_pending_files(self) -> Dict[str, List[str]]:
        """下载所有未下载的音频文件"""
        tsv_path = "./output/feed/feed.tsv"
        if not os.path.exists(tsv_path):
            raise HTTPException(status_code=404, detail="Feed TSV file not found")
            
        # 读取TSV文件
        df = pd.read_csv(tsv_path, sep='\t', dtype={'isDownload': str, 'title': str})
        
        # 获取未下载的音频文件
        pending_files = df[
            (df['isDownload'].fillna('false').str.lower() == 'false') &
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
                title = row['title']
                clean_title = clean_filename(title)
                url = row['url']
                output_path = os.path.join(self.download_dir, f"{clean_title}.mp3")
                
                print(f"\n[{index + 1}/{total_files}] 开始下载: {title}")
                print(f"清理后的文件名: {clean_title}")
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
                                        
                                        print(f'\r下载进度: {progress:.1f}% | '
                                              f'速度: {humanize.naturalsize(speed)}/s | '
                                              f'已下载: {humanize.naturalsize(downloaded_size)} / {humanize.naturalsize(total_size)}',
                                              end='', flush=True)
                            
                            print(f"\n下载完成: {output_path}")
                            
                            # 更新TSV文件中的isDownload状态
                            df.loc[df['title'] == title, 'isDownload'] = 'true'
                            success_files.append(title)
                        else:
                            print(f"\n下载失败: HTTP状态码 {response.status}")
                            failed_files.append(title)
                except Exception as e:
                    print(f"\n下载文件失败: {str(e)}")
                    failed_files.append(title)
                
                await asyncio.sleep(1)
        
        # 保存更新后的TSV文件
        df.to_csv(tsv_path, sep='\t', index=False)
        
        print(f"\n=== 下载完成 ===")
        print(f"成功: {len(success_files)} 个文件")
        print(f"失败: {len(failed_files)} 个文件")
        
        return {
            "success": success_files,
            "failed": failed_files
        }

    async def download_single_file(self, target_id: str) -> Dict[str, Any]:
        """下载指定ID的音频文件"""
        tsv_path = "./output/feed/feed.tsv"
        if not os.path.exists(tsv_path):
            raise HTTPException(status_code=404, detail="Feed TSV file not found")
        
        # 读取TSV文件
        df = pd.read_csv(tsv_path, sep='\t', dtype={'id': str, 'isDownload': str, 'title': str})
        
        # 查找指定ID的记录
        target_row = df[df['id'] == target_id]
        if target_row.empty:
            raise HTTPException(status_code=404, detail=f"Entry with ID {target_id} not found")
        
        # 获取文件信息
        row = target_row.iloc[0]
        title = row['title']
        url = row['url']
        mime_type = row['mime_type']
        
        # 检查是否是音频文件
        if not pd.isna(mime_type) and 'audio' not in mime_type.lower():
            raise HTTPException(status_code=400, detail=f"File with ID {target_id} is not an audio file")
        
        # 检查URL是否有效
        if pd.isna(url) or url.lower() == 'null':
            raise HTTPException(status_code=400, detail=f"No valid URL found for ID {target_id}")
        
        print(f"\n=== 开始下载单个文件 ===")
        print(f"ID: {target_id}")
        print(f"标题: {title}")
        
        clean_title = clean_filename(title)
        output_path = os.path.join(self.download_dir, f"{clean_title}.mp3")
        
        print(f"清理后的文件名: {clean_title}")
        print(f"URL: {url}")
        
        try:
            # 检查是否是 stitcher2.acast.com 的 URL
            if 'stitcher2.acast.com' in url or 'sphinx.acast.com' in url:
                print("检测到 acast 链接，使用 PowerShell 方式下载...")
                result = await self.download_file(url, output_path)
                
                if result.get("success", False):
                    # 更新TSV文件中的isDownload状态
                    df.loc[df['id'] == target_id, 'isDownload'] = 'true'
                    df.to_csv(tsv_path, sep='\t', index=False)
                    
                    return {
                        "success": True,
                        "title": title,
                        "file_path": output_path,
                        "file_size_mb": result.get("file_size_mb")
                    }
                else:
                    return {
                        "success": False,
                        "title": title,
                        "error": result.get("message", "Unknown error")
                    }
            else:
                # 使用原有的下载方式
                start_time = time.time()
                downloaded_size = 0
                
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
                            
                            # 更新TSV文件中的isDownload状态
                            df.loc[df['id'] == target_id, 'isDownload'] = 'true'
                            df.to_csv(tsv_path, sep='\t', index=False)
                            
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
