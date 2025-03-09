import os
import sqlite3
import pandas as pd
from tabulate import tabulate

def view_database(db_path: str = "./output/feed/feed.db"):
    """查看数据库内容"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # 查询所有表
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"数据库中的表: {', '.join([t[0] for t in tables])}\n")
        
        # 查询 entries 表的结构
        cursor.execute("PRAGMA table_info(entries)")
        columns = cursor.fetchall()
        
        print("表结构:")
        column_info = [(col['cid'], col['name'], col['type']) for col in columns]
        print(tabulate(column_info, headers=["ID", "列名", "类型"]))
        print("\n")
        
        # 查询数据统计
        cursor.execute("SELECT COUNT(*) FROM entries")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entries WHERE isDownload = 1")
        downloaded_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entries WHERE isTranscription = 1")
        transcribed_count = cursor.fetchone()[0]
        
        print(f"总条目数: {total_count}")
        print(f"已下载条目数: {downloaded_count}")
        print(f"已转写条目数: {transcribed_count}")
        print("\n")
        
        # 查询 feed 分组统计
        cursor.execute("""
        SELECT feed_title, COUNT(*) as count
        FROM entries
        WHERE feed_title IS NOT NULL
        GROUP BY feed_title
        """)
        
        feeds = cursor.fetchall()
        if feeds:
            feed_stats = [(feed[0], feed[1]) for feed in feeds]
            print("Feed 统计:")
            print(tabulate(feed_stats, headers=["Feed 名称", "条目数"]))
            print("\n")
        
        # 查询最新的 10 条记录
        cursor.execute("""
        SELECT id, title, publishedAt, isDownload, isTranscription, feed_title
        FROM entries
        ORDER BY publishedAt DESC
        LIMIT 10
        """)
        
        latest_entries = cursor.fetchall()
        if latest_entries:
            entries_data = []
            for entry in latest_entries:
                entries_data.append([
                    entry['id'][:8] + "...",  # 截断 ID 以便显示
                    entry['title'][:30] + "..." if len(entry['title']) > 30 else entry['title'],
                    entry['publishedAt'],
                    "是" if entry['isDownload'] == 1 else "否",
                    "是" if entry['isTranscription'] == 1 else "否",
                    entry['feed_title']
                ])
            
            print("最新 10 条记录:")
            print(tabulate(entries_data, headers=["ID", "标题", "发布日期", "已下载", "已转写", "Feed"]))
        
        conn.close()
        
    except Exception as e:
        print(f"查询数据库失败: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    view_database() 