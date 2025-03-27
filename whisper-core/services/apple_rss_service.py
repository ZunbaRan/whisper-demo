import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
import requests
from services.db_service import DBService

class AppleRssService:
    def __init__(self):
        """初始化 Apple RSS 服务"""
        self.db_service = DBService()
        self.namespaces = {
            'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'atom': 'http://www.w3.org/2005/Atom',
            'media': 'http://search.yahoo.com/mrss/',
            'googleplay': 'http://www.google.com/schemas/play-podcasts/1.0'
        }
    
    async def process_single_feed(self, feed_name: str) -> Dict[str, Any]:
        """处理单个 RSS 源"""
        try:
            print(f"开始处理 RSS 源: {feed_name}")
            
            # 从数据库中获取 feed
            db_service = DBService()
            feeds = db_service.get_all_rss_feeds()
            print(f"数据库中找到 {len(feeds)} 个 RSS 源")
            
            feed_url = None
            for feed in feeds:
                if feed['title'] == feed_name:
                    feed_url = feed['url']
                    print(f"找到匹配的 RSS 源: {feed_name}, URL: {feed_url}")
                    break
            
            if not feed_url:
                print(f"未找到 RSS 源: {feed_name}")
                return {
                    "status": "error",
                    "message": f"未找到 RSS 源: {feed_name}"
                }
            
            # 获取 RSS 内容
            print(f"开始获取 RSS 内容: {feed_url}")
            import aiohttp
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(feed_url, timeout=30) as response:
                        print(f"RSS 请求状态码: {response.status}")
                        if response.status != 200:
                            return {
                                "status": "error",
                                "message": f"获取 RSS 内容失败: {response.status}"
                            }
                        
                        content = await response.text()
                        print(f"获取到 RSS 内容，长度: {len(content)} 字符")
                        print(f"RSS 内容前 100 个字符: {content[:100]}")
                except Exception as e:
                    print(f"获取 RSS 内容时发生异常: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    return {
                        "status": "error",
                        "message": f"获取 RSS 内容失败: {str(e)}"
                    }
            
            # 解析 RSS 内容
            try:
                print(f"开始解析 RSS 内容...")
                entries = self.parse_rss_xml(content, feed_name)
                print(f"解析完成，找到 {len(entries)} 个条目")
            except Exception as e:
                print(f"解析 RSS 内容失败: {str(e)}")
                import traceback
                print(traceback.format_exc())
                return {
                    "status": "error",
                    "message": f"解析 RSS 内容失败: {str(e)}"
                }
            
            # 保存到数据库
            print(f"开始保存 {len(entries)} 个条目到数据库")
            saved_entries = self.save_entries_to_db(entries)
            print(f"成功保存 {len(saved_entries)} 个条目到数据库")
            
            return {
                "status": "success",
                "feed": feed_name,
                "entries": saved_entries
            }
        except Exception as e:
            print(f"处理 RSS 源失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {
                "status": "error",
                "message": str(e)
            }
    
    def parse_rss_xml(self, xml_content: str, feed_title: str) -> List[Dict[str, Any]]:
        """解析 RSS XML 内容"""
        try:
            print(f"开始解析 RSS 内容: {feed_title}")
            
            # 如果 xml_content 是字节，转换为字符串
            if isinstance(xml_content, bytes):
                xml_content = xml_content.decode('utf-8')
                print("将字节内容转换为字符串")
            
            # 解析 XML
            try:
                print("开始解析 XML...")
                root = ET.fromstring(xml_content)
                print("XML 解析成功")
            except ET.ParseError as e:
                print(f"XML 解析错误: {str(e)}")
                print(f"XML 内容前 100 个字符: {xml_content[:100]}")
                # 尝试使用 lxml 解析，它更宽容
                try:
                    print("尝试使用 lxml 解析...")
                    from lxml import etree
                    root = etree.fromstring(xml_content.encode('utf-8'))
                    print("使用 lxml 解析成功")
                except Exception as lxml_error:
                    print(f"lxml 解析也失败: {str(lxml_error)}")
                    raise e
            
            # 获取所有 item 元素
            print("查找 item 元素...")
            items = root.findall('.//item')
            print(f"找到 {len(items)} 个节目条目")
            
            entries = []
            for i, item in enumerate(items):
                try:
                    print(f"解析第 {i+1} 个条目...")
                    # 提取基本信息
                    title = self._get_element_text(item, './title')
                    pub_date = self._get_element_text(item, './pubDate')
                    print(f"条目标题: {title}, 发布日期: {pub_date}")
                    
                    # 提取 description 和 iTunes 特定信息
                    description = self._get_element_text(item, './description')
                    summary = self._get_element_text(item, './itunes:summary', self.namespaces)
                    image = self._get_element_attribute(item, './itunes:image', 'href', self.namespaces)
                    
                    # 提取 enclosure 信息
                    enclosure = item.find('./enclosure')
                    enclosure_url = enclosure.get('url') if enclosure is not None else None
                    enclosure_type = enclosure.get('type') if enclosure is not None else None
                    print(f"音频 URL: {enclosure_url}, 类型: {enclosure_type}")
                    
                    # 提取 GUID 作为唯一标识符
                    guid = self._get_element_text(item, './guid')
                    if not guid:
                        # 如果没有 GUID，生成一个基于标题和发布日期的唯一 ID
                        guid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{title}_{pub_date}"))
                        print(f"生成 GUID: {guid}")
                    else:
                        print(f"使用原始 GUID: {guid}")
                    
                    # 格式化日期
                    formatted_date = self._format_pub_date(pub_date)
                    print(f"格式化日期: {formatted_date}")
                    
                    # 创建条目
                    entry = {
                        'id': guid,
                        'title': title,
                        'publishedAt': formatted_date,
                        'url': enclosure_url,
                        'mime_type': enclosure_type,
                        'summary': summary,
                        'description': description,
                        'image': image,
                        'feed_title': feed_title,
                        'isDownload': 'false',
                        'isTranscription': 'false'
                    }
                    
                    entries.append(entry)
                    print(f"第 {i+1} 个条目解析完成")
                except Exception as e:
                    print(f"解析第 {i+1} 个条目失败: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
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
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
            
            # 如果所有格式都失败，尝试更宽松的解析
            import dateutil.parser
            dt = dateutil.parser.parse(pub_date)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"日期解析失败 ({pub_date}): {str(e)}")
            return pub_date
    
    def save_entries_to_db(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """保存条目到数据库"""
        saved_entries = []
        for entry in entries:
            try:
                # 尝试保存条目
                self.db_service.save_entry(entry)
                saved_entries.append(entry)
            except Exception as e:
                print(f"保存条目失败 ({entry.get('title', 'Unknown')}): {str(e)}")
                import traceback
                print(traceback.format_exc())
        
        return saved_entries
    
    async def download_feed_audio(self, feed_name: str) -> Dict[str, Any]:
        """下载指定 feed 的未下载音频文件"""
        try:
            print(f"\n=== 开始下载 {feed_name} 的音频文件 ===")
            
            # 获取指定 feed 的未下载条目
            entries = self.db_service.get_entries_by_query(
                "feed_title = ? AND isDownload = 0 AND url IS NOT NULL AND url != 'null' AND mime_type LIKE '%audio%'",
                (feed_name,)
            )
            
            print(f"找到 {len(entries)} 个需要下载的条目")
            
            # 下载音频文件
            success_files = []
            failed_files = []
            
            from utils.file_utils import clean_filename
            
            for entry in entries:
                try:
                    title = entry["title"]
                    url = entry["url"]
                    
                    print(f"\n下载: {title}")
                    print(f"URL: {url}")
                    
                    # 创建输出目录
                    output_dir = "@data/feed/audio"
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # 清理文件名
                    clean_title = clean_filename(title)
                    output_path = f"{output_dir}/{clean_title}.mp3"
                    
                    # 下载文件
                    response = requests.get(url, stream=True)
                    if response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # 更新数据库状态
                        self.db_service.update_entry_status(entry["id"], download_status=True)
                        
                        success_files.append(title)
                        print(f"下载成功: {title}")
                    else:
                        failed_files.append(title)
                        print(f"下载失败: {title} - HTTP {response.status_code}")
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
        except Exception as e:
            print(f"下载音频文件失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {
                "error": str(e)
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