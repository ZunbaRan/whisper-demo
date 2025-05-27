import os
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from utils.file_utils import clean_filename

class DBService:

    def __init__(self, db_path: str = "@data/rss_database.db"):
        """初始化数据库服务"""
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.ensure_db_exists()
    
    def init_db(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                publishedAt TEXT,
                url TEXT,
                mime_type TEXT,
                isDownload BOOLEAN DEFAULT 0,
                isTranscription BOOLEAN DEFAULT 0
            )
            ''')
            conn.commit()

    
    def get_entries_count(self, feed_title: Optional[str] = None) -> int:
        """获取条目总数"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if feed_title:
                    cursor.execute("SELECT COUNT(*) as count FROM entries WHERE title = ?", (f"%{feed_title}%",))
                else:
                    cursor.execute("SELECT COUNT(*) as count FROM entries")
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            print(f"获取条目总数失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return 0 
    
    def ensure_db_exists(self):
        """确保数据库目录存在并初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 如果数据库不存在，创建表结构
        if not os.path.exists(self.db_path):
            self.init_db()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    def import_from_tsv(self, tsv_path: str = "./output/feed/feed.tsv"):
        """从TSV文件导入数据到数据库"""
        if not os.path.exists(tsv_path):
            print(f"TSV文件不存在: {tsv_path}")
            return False
        
        try:
            # 读取TSV文件
            df = pd.read_csv(tsv_path, sep='\t')
            
            # 转换布尔值列
            df['isDownload'] = df['isDownload'].apply(lambda x: 1 if str(x).lower() == 'true' else 0)
            if 'isTranscription' in df.columns:
                df['isTranscription'] = df['isTranscription'].apply(lambda x: 1 if str(x).lower() == 'true' else 0)
            else:
                df['isTranscription'] = 0
            
            # 将数据导入到数据库
            with self.get_connection() as conn:
                # 先清空表
                conn.execute("DELETE FROM entries")
                
                # 插入数据
                df.to_sql('entries', conn, if_exists='append', index=False)
                
            print(f"成功从TSV导入了 {len(df)} 条记录到数据库")
            return True
        except Exception as e:
            print(f"导入TSV数据失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def export_to_tsv(self, tsv_path: str = "./output/feed/feed.tsv"):
        """将数据库数据导出到TSV文件"""
        try:
            with self.get_connection() as conn:
                # 查询所有数据
                df = pd.read_sql("SELECT * FROM entries ORDER BY publishedAt DESC", conn)
                
                # 转换布尔值列为字符串
                df['isDownload'] = df['isDownload'].apply(lambda x: 'true' if x == 1 else 'false')
                df['isTranscription'] = df['isTranscription'].apply(lambda x: 'true' if x == 1 else 'false')
                
                # 导出到TSV
                os.makedirs(os.path.dirname(tsv_path), exist_ok=True)
                df.to_csv(tsv_path, sep='\t', index=False)
                
            print(f"成功将 {len(df)} 条记录从数据库导出到TSV")
            return True
        except Exception as e:
            print(f"导出数据到TSV失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def save_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """保存条目到数据库，返回新增的条目"""
        if not entries:
            return []
        
        new_entries = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取现有的ID列表
                cursor.execute("SELECT id FROM entries")
                existing_ids = {row['id'] for row in cursor.fetchall()}
                
                # 处理每个条目
                for entry in entries:
                    # 检查ID是否已存在
                    if entry['id'] not in existing_ids:
                        # 转换布尔值
                        is_download = 1 if str(entry.get('isDownload', 'false')).lower() == 'true' else 0
                        is_transcription = 1 if str(entry.get('isTranscription', 'false')).lower() == 'true' else 0
                        
                        # 插入新条目
                        cursor.execute('''
                        INSERT INTO entries (id, title, publishedAt, url, mime_type, isDownload, isTranscription)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            entry['id'],
                            entry['title'],
                            entry.get('publishedAt', ''),
                            entry.get('url', ''),
                            entry.get('mime_type', ''),
                            is_download,
                            is_transcription
                        ))
                        new_entries.append(entry)
                
                conn.commit()
            
            print(f"成功保存了 {len(new_entries)} 条新记录到数据库")
            return new_entries
        except Exception as e:
            print(f"保存条目到数据库失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def get_all_entries(self) -> List[Dict[str, Any]]:
        """获取所有条目"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, title, publishedAt, url, mime_type, 
                       isDownload, isTranscription
                FROM entries
                ORDER BY publishedAt DESC
                ''')
                
                # 转换结果为字典列表
                result = []
                for row in cursor.fetchall():
                    entry = dict(row)
                    # 转换布尔值为字符串
                    entry['isDownload'] = 'true' if entry['isDownload'] == 1 else 'false'
                    entry['isTranscription'] = 'true' if entry['isTranscription'] == 1 else 'false'
                    result.append(entry)
                
                return result
        except Exception as e:
            print(f"获取所有条目失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def get_pending_downloads(self) -> List[Dict[str, Any]]:
        """获取待下载的条目"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, title, publishedAt, url, mime_type
                FROM entries
                WHERE isDownload = 0 
                  AND url IS NOT NULL 
                  AND url != 'null'
                  AND mime_type LIKE '%audio%'
                ORDER BY publishedAt DESC
                ''')
                
                # 转换结果为字典列表
                result = []
                for row in cursor.fetchall():
                    result.append(dict(row))
                
                return result
        except Exception as e:
            print(f"获取待下载条目失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def update_download_status(self, entry_id: str, status: bool) -> bool:
        """更新条目的下载状态"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 更新状态
                cursor.execute(
                    "UPDATE entries SET isDownload = ? WHERE id = ?",
                    (1 if status else 0, entry_id)
                )
                
                conn.commit()
                
                # 检查是否有行被更新
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新下载状态失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def update_transcription_status(self, entry_id: str, status: bool) -> bool:
        """更新条目的转写状态"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 更新状态
                cursor.execute(
                    "UPDATE entries SET isTranscription = ? WHERE id = ?",
                    (1 if status else 0, entry_id)
                )
                
                conn.commit()
                
                # 检查是否有行被更新
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新转写状态失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def get_entry_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取条目"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, title, publishedAt, url, mime_type, 
                       isDownload, isTranscription, feed_title
                FROM entries
                WHERE id = ?
                ''', (entry_id,))
                
                row = cursor.fetchone()
                if row:
                    entry = dict(row)
                    # 转换布尔值为字符串
                    entry['isDownload'] = 'true' if entry['isDownload'] == 1 else 'false'
                    entry['isTranscription'] = 'true' if entry['isTranscription'] == 1 else 'false'
                    return entry
                return None
        except Exception as e:
            print(f"获取条目失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def get_entry_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """根据标题获取条目"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, title, publishedAt, url, mime_type, 
                       isDownload, isTranscription
                FROM entries
                WHERE title = ?
                ''', (title,))
                
                row = cursor.fetchone()
                if row:
                    entry = dict(row)
                    # 转换布尔值为字符串
                    entry['isDownload'] = 'true' if entry['isDownload'] == 1 else 'false'
                    entry['isTranscription'] = 'true' if entry['isTranscription'] == 1 else 'false'
                    return entry
                return None
        except Exception as e:
            print(f"获取条目失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def find_entry_by_clean_title(self, clean_title: str) -> Optional[Dict[str, Any]]:
        """根据清理后的标题查找条目"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, title FROM entries")
                
                for row in cursor.fetchall():
                    if clean_filename(row['title']) == clean_title:
                        # 找到匹配的条目，获取完整信息
                        return self.get_entry_by_id(row['id'])
                
                return None
        except Exception as e:
            print(f"查找条目失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def fix_transcription_status(self, output_dir: str = "./output") -> int:
        """修正转写状态，根据输出目录中的文本文件"""
        try:
            # 获取所有文本文件
            txt_files = set()
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if file.endswith('.txt') and not file.endswith('_simplified.txt'):
                        txt_files.add(os.path.splitext(file)[0])
            
            print(f"在输出目录中找到 {len(txt_files)} 个文本文件")
            
            updated_count = 0
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, title FROM entries")
                
                for row in cursor.fetchall():
                    clean_title = clean_filename(row['title'])
                    if clean_title in txt_files:
                        # 更新状态
                        conn.execute('''
                        UPDATE entries
                        SET isDownload = 1, isTranscription = 1
                        WHERE id = ?
                        ''', (row['id'],))
                        updated_count += 1
                        print(f"更新状态: {row['title']}")
                
                conn.commit()
            
            print(f"共更新了 {updated_count} 条记录的状态")
            return updated_count
        except Exception as e:
            print(f"修正转写状态失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return 0
    
    def save_rss_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """保存 RSS 条目到数据库，处理额外的字段，并进行重复校验"""
        if not entries:
            return []
        
        new_entries = []
        duplicates = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for entry in entries:
                    # 首先检查 ID 是否已存在
                    cursor.execute("SELECT id FROM entries WHERE id = ?", (entry['id'],))
                    existing_id = cursor.fetchone()
                    
                    if existing_id:
                        print(f"跳过已存在的条目 ID: {entry['id']} - {entry['title']}")
                        duplicates.append(entry)
                        continue
                    
                    # 然后检查 feed_title 和 title 组合是否已存在
                    if 'feed_title' in entry and 'title' in entry:
                        cursor.execute(
                            "SELECT id FROM entries WHERE feed_title = ? AND title = ?", 
                            (entry['feed_title'], entry['title'])
                        )
                        existing_combo = cursor.fetchone()
                        
                        if existing_combo:
                            print(f"跳过重复条目 (相同 feed 和标题): {entry['feed_title']} - {entry['title']}")
                            duplicates.append(entry)
                            continue
                    
                    # 准备插入语句和参数
                    fields = ['id', 'title', 'publishedAt', 'url', 'mime_type', 
                             'isDownload', 'isTranscription', 'summary', 'image', 'feed_title']
                    
                    # 确保所有字段都有值
                    values = []
                    placeholders = []
                    columns = []
                    
                    for field in fields:
                        if field in entry:
                            columns.append(field)
                            placeholders.append('?')
                            
                            # 转换布尔值字段
                            if field in ['isDownload', 'isTranscription']:
                                values.append(1 if entry[field] == 'true' else 0)
                            else:
                                values.append(entry[field])
                    
                    # 构建 SQL 语句
                    sql = f"INSERT INTO entries ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    
                    # 执行插入
                    cursor.execute(sql, values)
                    new_entries.append(entry)
                    print(f"添加新条目: {entry['title']}")
                
                conn.commit()
                
            print(f"总共添加了 {len(new_entries)} 条新条目")
            print(f"跳过了 {len(duplicates)} 条重复条目")
            return new_entries
        except Exception as e:
            print(f"保存 RSS 条目失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def get_entries_by_query(self, query: str, params: tuple = (), limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """根据查询条件获取条目，支持限制数量"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建查询
                sql = f"""
                SELECT id, title, publishedAt, url, mime_type, 
                       isDownload, isTranscription, summary, image, feed_title
                FROM entries
                WHERE {query}
                """
                
                # 添加排序
                sql += " ORDER BY publishedAt DESC"
                
                # 添加限制
                if limit is not None:
                    sql += f" LIMIT {limit}"
                
                # 执行查询
                cursor.execute(sql, params)
                
                # 处理结果
                entries = []
                for row in cursor.fetchall():
                    entry = dict(row)
                    # 转换布尔值为字符串
                    entry['isDownload'] = 'true' if entry['isDownload'] == 1 else 'false'
                    entry['isTranscription'] = 'true' if entry['isTranscription'] == 1 else 'false'
                    entries.append(entry)
                
                return entries
        except Exception as e:
            print(f"查询条目失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def get_entries(self, feed_title:Optional[str] = None,
                    search_value: Optional[str] = None,
                    limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取数据库中的条目，支持分页"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if search_value:
                    cursor.execute("""
                    SELECT * FROM entries
                    WHERE  (title LIKE ? OR id LIKE ?)
                    ORDER BY publishedAt DESC
                    LIMIT? OFFSET?
                    """, ( f"%{search_value}%", f"%{search_value}%", limit, offset))
                elif feed_title:
                    cursor.execute("""
                    SELECT * FROM entries
                    WHERE feed_title =?
                    ORDER BY publishedAt DESC
                    LIMIT? OFFSET?
                    """, (feed_title, limit, offset))
                else:
                    cursor.execute("""
                    SELECT * FROM entries
                    ORDER BY publishedAt DESC
                    LIMIT ? OFFSET ?
                    """, (limit, offset))
                
                entries = []
                for row in cursor.fetchall():
                    entry = dict(row)
                    # 转换布尔值为字符串
                    entry['isDownload'] = 'true' if entry['isDownload'] == 1 else 'false'
                    entry['isTranscription'] = 'true' if entry['isTranscription'] == 1 else 'false'
                    entries.append(entry)
                
                return entries
        except Exception as e:
            print(f"获取条目失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 总条目数
                cursor.execute("SELECT COUNT(*) FROM entries")
                total_count = cursor.fetchone()[0]
                
                # 已下载条目数
                cursor.execute("SELECT COUNT(*) FROM entries WHERE isDownload = 1")
                downloaded_count = cursor.fetchone()[0]
                
                # 已转写条目数
                cursor.execute("SELECT COUNT(*) FROM entries WHERE isTranscription = 1")
                transcribed_count = cursor.fetchone()[0]
                
                # 按 feed_title 分组统计
                cursor.execute("""
                SELECT feed_title, COUNT(*) as count
                FROM entries
                WHERE feed_title IS NOT NULL
                GROUP BY feed_title
                """)
                
                feeds = []
                for row in cursor.fetchall():
                    feeds.append({
                        "title": row[0],
                        "count": row[1]
                    })
                
                return {
                    "total_entries": total_count,
                    "downloaded_entries": downloaded_count,
                    "transcribed_entries": transcribed_count,
                    "feeds": feeds
                }
        except Exception as e:
            print(f"获取统计信息失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {
                "error": str(e),
                "total_entries": 0,
                "downloaded_entries": 0,
                "transcribed_entries": 0,
                "feeds": []
            }
    
    def update_entry_status(self, entry_id: str, download_status: Optional[bool] = None, transcription_status: Optional[bool] = None) -> bool:
        """更新条目的状态（下载和/或转写）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建 SQL 语句
                sql_parts = []
                params = []
                
                if download_status is not None:
                    sql_parts.append("isDownload = ?")
                    params.append(1 if download_status else 0)
                
                if transcription_status is not None:
                    sql_parts.append("isTranscription = ?")
                    params.append(1 if transcription_status else 0)
                
                if not sql_parts:
                    print("警告: 没有提供要更新的状态")
                    return False
                
                # 完成 SQL 语句
                sql = f"UPDATE entries SET {', '.join(sql_parts)} WHERE id = ?"
                params.append(entry_id)
                
                # 执行更新
                cursor.execute(sql, params)
                conn.commit()
                
                # 检查是否有行被更新
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新条目状态失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def find_entry_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """通过标题查找条目"""
        entries = self.get_entries_by_query("title = ?", (title,))
        return entries[0] if entries else None
    
    def clear_database(self) -> bool:
        """清空数据库中的所有数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取所有表名
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                # 开启外键约束
                cursor.execute("PRAGMA foreign_keys = OFF")
                
                # 删除每个表中的数据
                for table in tables:
                    table_name = table[0]
                    if table_name != "sqlite_sequence":  # 跳过 SQLite 内部表
                        cursor.execute(f"DELETE FROM {table_name}")
                
                # 检查 sqlite_sequence 表是否存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
                if cursor.fetchone():
                    # 如果存在，则删除其中的数据
                    cursor.execute("DELETE FROM sqlite_sequence")
                
                # 恢复外键约束
                cursor.execute("PRAGMA foreign_keys = ON")
                
                conn.commit()
                return True
        except Exception as e:
            print(f"清空数据库失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def save_rss_feed(self, title: str, url: str) -> Optional[Dict[str, Any]]:
        """保存 RSS 源到数据库"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查是否已存在
                cursor.execute("SELECT * FROM rss_feeds WHERE title = ? OR url = ?", (title, url))
                existing = cursor.fetchone()
                
                if existing:
                    return dict(existing)
                
                # 插入新记录
                cursor.execute(
                    "INSERT INTO rss_feeds (title, url) VALUES (?, ?)",
                    (title, url)
                )
                
                feed_id = cursor.lastrowid
                conn.commit()
                
                # 返回新创建的记录
                cursor.execute("SELECT * FROM rss_feeds WHERE id = ?", (feed_id,))
                return dict(cursor.fetchone())
        except Exception as e:
            print(f"保存 RSS 源失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def get_all_rss_feeds(self) -> List[Dict[str, Any]]:
        """获取所有 RSS 源"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM rss_feeds ORDER BY title")
                
                feeds = []
                for row in cursor.fetchall():
                    feeds.append(dict(row))
                
                return feeds
        except Exception as e:
            print(f"获取 RSS 源失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def delete_rss_feed(self, feed_id: int) -> bool:
        """删除 RSS 源"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM rss_feeds WHERE id = ?", (feed_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除 RSS 源失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def create_tables(self):
        """创建必要的数据库表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建 entries 表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS entries (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    publishedAt TEXT,
                    url TEXT,
                    mime_type TEXT,
                    isDownload INTEGER DEFAULT 0,
                    isTranscription INTEGER DEFAULT 0,
                    summary TEXT,
                    description TEXT,
                    image TEXT,
                    feed_title TEXT
                )
                ''')
                
                # 创建 rss_feeds 表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS rss_feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE,
                    url TEXT UNIQUE
                )
                ''')
                
                # 检查并添加缺少的列
                self._ensure_column_exists(conn, 'entries', 'summary', 'TEXT')
                self._ensure_column_exists(conn, 'entries', 'description', 'TEXT')
                self._ensure_column_exists(conn, 'entries', 'image', 'TEXT')
                self._ensure_column_exists(conn, 'entries', 'feed_title', 'TEXT')
                
                conn.commit()
        except Exception as e:
            print(f"创建数据库表失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def _ensure_column_exists(self, conn, table_name, column_name, column_type):
        """确保表中存在指定的列，如果不存在则添加"""
        try:
            cursor = conn.cursor()
            
            # 检查列是否存在
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]
            
            if column_name not in columns:
                print(f"添加列 {column_name} 到表 {table_name}")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        except Exception as e:
            print(f"检查/添加列失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def save_entry(self, entry: Dict[str, Any]) -> bool:
        """保存单个条目到数据库"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查条目是否已存在
                cursor.execute("SELECT id FROM entries WHERE id = ?", (entry['id'],))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有条目
                    cursor.execute('''
                    UPDATE entries
                    SET title = ?, publishedAt = ?, url = ?, mime_type = ?,
                        summary = ?, description = ?, image = ?, feed_title = ?
                    WHERE id = ?
                    ''', (
                        entry['title'],
                        entry['publishedAt'],
                        entry['url'],
                        entry['mime_type'],
                        entry.get('summary'),
                        entry.get('description'),
                        entry.get('image'),
                        entry.get('feed_title'),
                        entry['id']
                    ))
                else:
                    # 插入新条目
                    cursor.execute('''
                    INSERT INTO entries (
                        id, title, publishedAt, url, mime_type,
                        isDownload, isTranscription, summary, description, image, feed_title
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        entry['id'],
                        entry['title'],
                        entry['publishedAt'],
                        entry['url'],
                        entry['mime_type'],
                        1 if entry.get('isDownload') == 'true' else 0,
                        1 if entry.get('isTranscription') == 'true' else 0,
                        entry.get('summary'),
                        entry.get('description'),
                        entry.get('image'),
                        entry.get('feed_title')
                    ))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"保存条目失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False 