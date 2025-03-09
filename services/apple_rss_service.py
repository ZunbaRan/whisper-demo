import os
import yaml
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
from fastapi import HTTPException
from services.db_service import DBService

class AppleRssService:
    def __init__(self, config_path: str = "./config/appleRsslink.yml"):
        """初始化 Apple RSS 服务"""
        self.config_path = config_path
        self.db_service = DBService()
        self.namespaces = {
            'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'atom': 'http://www.w3.org/2005/Atom',
            'media': 'http://search.yahoo.com/mrss/',
            'googleplay': 'http://www.google.com/schemas/play-podcasts/1.0'
        }
    
    def load_config(self) -> List[Dict[str, Dict[str, str]]]:
        """加载 YAML 配置文件"""
        try:
            if not os.path.exists(self.config_path):
                print(f"配置文件不存在: {self.config_path}")
                return []
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
            if not config:
                print("配置文件为空")
                return []
                
            return config
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
    
    async def download_rss_xml(self, url: str) -> Optional[str]:
        """下载 RSS XML 内容"""
        try:
            print(f"开始下载 RSS: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        print(f"成功下载 RSS，内容长度: {len(xml_content)} 字符")
                        return xml_content
                    else:
                        print(f"下载 RSS 失败: HTTP {response.status}")
                        return None
        except Exception as e:
            print(f"下载 RSS 异常: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def parse_rss_xml(self, xml_content: str, feed_title: str) -> List[Dict[str, Any]]:
        """解析 RSS XML 内容"""
        try:
            print(f"开始解析 RSS 内容: {feed_title}")
            
            # 解析 XML
            root = ET.fromstring(xml_content)
            
            # 获取所有 item 元素
            items = root.findall('.//item')
            print(f"找到 {len(items)} 个节目条目")
            
            entries = []
            for item in items:
                try:
                    # 提取基本信息
                    title = self._get_element_text(item, './title')
                    pub_date = self._get_element_text(item, './pubDate')
                    
                    # 提取 iTunes 特定信息
                    summary = self._get_element_text(item, './itunes:summary', self.namespaces)
                    image = self._get_element_attribute(item, './itunes:image', 'href', self.namespaces)
                    
                    # 提取 enclosure 信息
                    enclosure = item.find('./enclosure')
                    enclosure_url = enclosure.get('url') if enclosure is not None else None
                    enclosure_type = enclosure.get('type') if enclosure is not None else None
                    
                    # 提取 GUID 作为唯一标识符
                    guid = self._get_element_text(item, './guid')
                    if not guid:
                        # 如果没有 GUID，生成一个基于标题和发布日期的唯一 ID
                        guid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{title}_{pub_date}"))
                    
                    # 格式化日期
                    formatted_date = self._format_pub_date(pub_date)
                    
                    # 创建条目
                    entry = {
                        'id': guid,
                        'title': title,
                        'publishedAt': formatted_date,
                        'url': enclosure_url,
                        'mime_type': enclosure_type,
                        'summary': summary,
                        'image': image,
                        'feed_title': feed_title,
                        'isDownload': 'false',
                        'isTranscription': 'false'
                    }
                    
                    entries.append(entry)
                except Exception as e:
                    print(f"解析条目失败: {str(e)}")
                    continue
            
            print(f"成功解析 {len(entries)} 个条目")
            return entries
        except Exception as e:
            print(f"解析 RSS 内容失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def _get_element_text(self, element, xpath, namespaces=None) -> Optional[str]:
        """获取元素文本内容"""
        el = element.find(xpath, namespaces)
        return el.text.strip() if el is not None and el.text else None
    
    def _get_element_attribute(self, element, xpath, attr, namespaces=None) -> Optional[str]:
        """获取元素属性值"""
        el = element.find(xpath, namespaces)
        return el.get(attr) if el is not None else None
    
    def _format_pub_date(self, pub_date: Optional[str]) -> Optional[str]:
        """格式化发布日期"""
        if not pub_date:
            return None
        
        try:
            # 尝试解析多种日期格式
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',  # RFC 822 格式
                '%a, %d %b %Y %H:%M:%S %Z',  # 带时区名称
                '%a, %d %b %Y %H:%M:%S -0000',  # 特定格式
                '%Y-%m-%dT%H:%M:%S%z',  # ISO 8601
                '%Y-%m-%dT%H:%M:%SZ'  # ISO 8601 UTC
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(pub_date, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            # 如果所有格式都失败，返回原始字符串
            return pub_date
        except Exception:
            return pub_date
    
    def save_entries_to_db(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """保存条目到数据库"""
        if not entries:
            return []
        
        # 确保数据库表结构支持新字段
        self._ensure_db_structure()
        
        # 使用专门的方法保存 RSS 条目
        return self.db_service.save_rss_entries(entries)
    
    def _ensure_db_structure(self):
        """确保数据库表结构支持 RSS 条目的所有字段"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查是否存在 summary, image, feed_title 列
                cursor.execute("PRAGMA table_info(entries)")
                columns = {row['name'] for row in cursor.fetchall()}
                
                # 添加缺失的列
                if 'summary' not in columns:
                    cursor.execute("ALTER TABLE entries ADD COLUMN summary TEXT")
                
                if 'image' not in columns:
                    cursor.execute("ALTER TABLE entries ADD COLUMN image TEXT")
                
                if 'feed_title' not in columns:
                    cursor.execute("ALTER TABLE entries ADD COLUMN feed_title TEXT")
                
                conn.commit()
        except Exception as e:
            print(f"确保数据库结构失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    async def process_all_feeds(self) -> Dict[str, Any]:
        """处理所有 RSS 源"""
        config = self.load_config()
        if not config:
            raise HTTPException(status_code=400, detail="No RSS feeds configured")
        
        results = {
            "total_feeds": len(config),
            "processed_feeds": 0,
            "total_entries": 0,
            "new_entries": 0,
            "feeds": []
        }
        
        for feed_config in config:
            for feed_id, feed_info in feed_config.items():
                feed_title = feed_info.get('title', 'Unknown')
                feed_url = feed_info.get('url')
                
                if not feed_url:
                    print(f"跳过没有 URL 的源: {feed_id}")
                    continue
                
                print(f"\n=== 处理 RSS 源: {feed_title} ===")
                
                # 下载 XML
                xml_content = await self.download_rss_xml(feed_url)
                if not xml_content:
                    print(f"无法下载 RSS 内容: {feed_url}")
                    results["feeds"].append({
                        "id": feed_id,
                        "title": feed_title,
                        "status": "failed",
                        "error": "Failed to download RSS content"
                    })
                    continue
                
                # 解析 XML
                entries = self.parse_rss_xml(xml_content, feed_title)
                
                # 保存到数据库
                new_entries = self.save_entries_to_db(entries)
                
                feed_result = {
                    "id": feed_id,
                    "title": feed_title,
                    "status": "success",
                    "total_entries": len(entries),
                    "new_entries": len(new_entries)
                }
                
                results["feeds"].append(feed_result)
                results["processed_feeds"] += 1
                results["total_entries"] += len(entries)
                results["new_entries"] += len(new_entries)
                
                print(f"处理完成: {feed_title}")
                print(f"总条目数: {len(entries)}")
                print(f"新条目数: {len(new_entries)}")
        
        print("\n=== 所有 RSS 源处理完成 ===")
        print(f"处理的源数量: {results['processed_feeds']}")
        print(f"总条目数: {results['total_entries']}")
        print(f"新条目数: {results['new_entries']}")
        
        return results
    
    async def process_single_feed(self, feed_name: str) -> Dict[str, Any]:
        """处理单个 RSS 源"""
        config = self.load_config()
        if not config:
            raise HTTPException(status_code=400, detail="No RSS feeds configured")
        
        # 查找指定名称的 feed
        feed_config = None
        feed_id = None
        feed_info = None
        
        for item in config:
            for key, value in item.items():
                if key == feed_name:
                    feed_config = item
                    feed_id = key
                    feed_info = value
                    break
            if feed_config:
                break
        
        if not feed_config:
            raise HTTPException(status_code=404, detail=f"Feed '{feed_name}' not found in configuration")
        
        feed_title = feed_info.get('title', 'Unknown')
        feed_url = feed_info.get('url')
        
        if not feed_url:
            raise HTTPException(status_code=400, detail=f"No URL found for feed '{feed_name}'")
        
        print(f"\n=== 处理 RSS 源: {feed_title} ===")
        
        # 下载 XML
        xml_content = await self.download_rss_xml(feed_url)
        if not xml_content:
            error_msg = f"无法下载 RSS 内容: {feed_url}"
            print(error_msg)
            return {
                "id": feed_id,
                "title": feed_title,
                "status": "failed",
                "error": error_msg
            }
        
        # 解析 XML
        entries = self.parse_rss_xml(xml_content, feed_title)
        
        # 保存到数据库
        new_entries = self.save_entries_to_db(entries)
        
        result = {
            "id": feed_id,
            "title": feed_title,
            "status": "success",
            "total_entries": len(entries),
            "new_entries": len(new_entries)
        }
        
        print(f"处理完成: {feed_title}")
        print(f"总条目数: {len(entries)}")
        print(f"新条目数: {len(new_entries)}")
        
        return result
    
    async def download_feed_audio(self, feed_name: str) -> Dict[str, Any]:
        """下载指定 feed 的未下载音频文件"""
        from services.download_service import DownloadService
        download_service = DownloadService()
        
        # 获取指定 feed 的未下载条目
        entries = self.db_service.get_entries_by_query(
            "feed_title = ? AND isDownload = 0",
            (feed_name,)
        )
        
        if not entries:
            return {
                "message": f"没有需要下载的 RSS 条目 (feed: {feed_name})",
                "success": [],
                "failed": []
            }
        
        print(f"\n=== 开始下载 {feed_name} 的音频文件 ===")
        print(f"找到 {len(entries)} 个未下载的条目")
        
        # 使用下载服务处理这些条目
        success_files = []
        failed_files = []
        
        for entry in entries:
            try:
                print(f"\n下载: {entry['title']}")
                result = await download_service.download_single_file(entry["id"])
                if result["success"]:
                    success_files.append(entry["title"])
                    print(f"下载成功: {entry['title']}")
                else:
                    failed_files.append(entry["title"])
                    print(f"下载失败: {entry['title']} - {result.get('error', '未知错误')}")
            except Exception as e:
                print(f"下载异常: {str(e)}")
                import traceback
                print(traceback.format_exc())
                failed_files.append(entry["title"])
        
        print(f"\n=== 下载完成 ===")
        print(f"成功: {len(success_files)} 个文件")
        print(f"失败: {len(failed_files)} 个文件")
        
        return {
            "success": success_files,
            "failed": failed_files
        }
    
    async def transcribe_feed_audio(self, feed_name: str) -> Dict[str, Any]:
        """转写指定 feed 的已下载但未转写的音频文件"""
        from services.transcription_service import TranscriptionService
        from core.transcriber import TranscriptionConfig
        from config.paths import PROJECT_ROOT
        
        # 配置信息
        MODELS_DIR = PROJECT_ROOT + "/models"
        WHISPER_MODEL_NAME = "large-v3-turbo"
        ALIGN_MODEL_DIR = f"{MODELS_DIR}/wav2vec2_base"
        PYANNOTE_CONFIG_PATH = PROJECT_ROOT + "/config/pyannote_config.yaml"
        
        # 基础配置
        config = TranscriptionConfig(
            whisper_model_name=WHISPER_MODEL_NAME,
            whisper_download_root=MODELS_DIR,
            device="cuda",
            device_index=0,
            compute_type="float16",
            align_model_dir=ALIGN_MODEL_DIR,
            pyannote_config_path=PYANNOTE_CONFIG_PATH,
            language="en",
            diarize=True,
            output_dir="./output",
            output_format="json",
        )
        
        transcription_service = TranscriptionService(config)
        
        # 获取已下载但未转写的条目
        entries = self.db_service.get_entries_by_query(
            "feed_title = ? AND isDownload = 1 AND isTranscription = 0",
            (feed_name,)
        )
        
        if not entries:
            return {
                "message": f"没有需要转写的 RSS 条目 (feed: {feed_name})",
                "success": [],
                "failed": []
            }
        
        print(f"\n=== 开始转写 {feed_name} 的音频文件 ===")
        print(f"找到 {len(entries)} 个需要转写的条目")
        
        # 转写音频文件
        success_files = []
        failed_files = []
        
        from utils.file_utils import clean_filename
        
        for entry in entries:
            try:
                title = entry["title"]
                clean_title = clean_filename(title)
                file_path = f"./output/feed/audio/{clean_title}.mp3"
                
                print(f"\n转写: {title}")
                result = await transcription_service.process_single_file(entry, file_path)
                
                if result.get("success", False):
                    success_files.append(title)
                    print(f"转写成功: {title}")
                else:
                    failed_files.append(title)
                    print(f"转写失败: {title} - {result.get('error', '未知错误')}")
            except Exception as e:
                print(f"转写异常: {str(e)}")
                import traceback
                print(traceback.format_exc())
                failed_files.append(entry["title"])
        
        print(f"\n=== 转写完成 ===")
        print(f"成功: {len(success_files)} 个文件")
        print(f"失败: {len(failed_files)} 个文件")
        
        return {
            "success": success_files,
            "failed": failed_files
        }
    
    async def process_feed_workflow(self, feed_name: str) -> Dict[str, Any]:
        """处理指定 feed 的完整工作流：获取数据、下载并转写"""
        results = {
            "feed": feed_name,
            "steps": []
        }
        
        # 步骤 1: 处理 RSS 源
        print(f"\n=== 步骤 1: 处理 RSS 源 {feed_name} ===")
        try:
            rss_result = await self.process_single_feed(feed_name)
            results["steps"].append({
                "name": "process_rss",
                "status": "success" if rss_result.get("status") == "success" else "failed",
                "details": rss_result
            })
        except Exception as e:
            print(f"处理 RSS 源失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            results["steps"].append({
                "name": "process_rss",
                "status": "failed",
                "error": str(e)
            })
            # 如果 RSS 处理失败，直接返回结果
            return results
        
        # 步骤 2: 下载音频文件
        print(f"\n=== 步骤 2: 下载 {feed_name} 的音频文件 ===")
        try:
            download_result = await self.download_feed_audio(feed_name)
            results["steps"].append({
                "name": "download_audio",
                "status": "success" if download_result.get("success") else "failed",
                "details": download_result
            })
        except Exception as e:
            print(f"下载音频文件失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            results["steps"].append({
                "name": "download_audio",
                "status": "failed",
                "error": str(e)
            })
        
        # 步骤 3: 转写音频文件
        print(f"\n=== 步骤 3: 转写 {feed_name} 的音频文件 ===")
        try:
            transcribe_result = await self.transcribe_feed_audio(feed_name)
            results["steps"].append({
                "name": "transcribe_audio",
                "status": "success" if transcribe_result.get("success") else "failed",
                "details": transcribe_result
            })
        except Exception as e:
            print(f"转写音频文件失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            results["steps"].append({
                "name": "transcribe_audio",
                "status": "failed",
                "error": str(e)
            })
        
        return results 