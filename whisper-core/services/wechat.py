import requests
import re
import asyncio
import datetime
from crawl4ai import *
from bs4 import BeautifulSoup


async def search_by_crawl4ai(urls: [], format_type='markdown'):
    result_json = {}
    async with AsyncWebCrawler() as crawler:
        urls = urls
        results = await crawler.arun_many(urls)
        for crawler_result in results:
            if format_type == 'markdown':
                result_json[crawler_result.url] = crawler_result.markdown
            else:
                result_json[crawler_result.url] = crawler_result.json
    return result_json


def find_time_convert(text):
    pattern = r"timeConvert\('(\d+)'\)"
    match = re.search(pattern, text)
    if match:
        timestamp = int(match.group(1))
        # 使用 datetime 模块的 fromtimestamp 方法将时间戳转换为 datetime 对象
        dt_object = datetime.datetime.fromtimestamp(timestamp)
        # 使用 strftime 方法将 datetime 对象格式化为 'yyyy-MM-dd' 格式的字符串
        return dt_object.strftime('%Y-%m-%d')
    return ''


def get_article_content(url: str, headers=None):
    """获取单个文章的内容
    
    Args:
        url: 文章URL
        headers: 请求头
    
    Returns:
        dict: 包含文章信息的字典，如果获取失败返回None
    """
    global final_url
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Cookie': 'SNUID=598887DDA5A3885A7CFC9BACA501CE70; ABTEST=0|1739422434|v1; SUID=FC2D23798E52A20B0000000067AD7AE2'
        }
    
    try:
        article_response = requests.get(url, headers=headers, allow_redirects=True)
        if article_response.status_code == 200:
            script_content = article_response.text
            # 获取重定向URL
            matches = re.findall(r"url\s*\+=\s*'(.*?)'", script_content, re.DOTALL)
            
            if url.startswith('https://mp.weixin.qq.com/s/'):
                final_url = url
            else:
                if matches:
                    final_url = ''.join(matches).replace('@', '')
                    final_url = re.sub(r'\s+', '', final_url)
                
            # 获取文章内容
            content_result = asyncio.run(search_by_crawl4ai([final_url]))
                
            return {
                    'link': final_url,
                    'redict_link': url,
                    'content': content_result.get(final_url, '')
                }
        else:
            print(f"无法访问文章页面: {url}, 状态码: {article_response.status_code}\n")
            return None
    except Exception as e:
        print(f"获取文章内容时发生错误: {str(e)}")
        return None


def search_weixin_articles(query, size=5):
    result_array = []
    urls = []
    base_search_url = "https://weixin.sogou.com/weixin"
    params = {
        'ie': 'utf8',
        's_from': 'input',
        '_sug_': 'y',
        '_sug_type_': '',
        'type': '2',
        'query': query,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Cookie': 'SNUID=598887DDA5A3885A7CFC9BACA501CE70; ABTEST=0|1739422434|v1; SUID=FC2D23798E52A20B0000000067AD7AE2'
    }

    # 发送搜索请求
    response = requests.get(base_search_url, headers=headers, params=params)
    if response.status_code != 200:
        print("搜索请求失败:", response.status_code)
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all('div', class_='txt-box')

    for article in articles:
        if len(result_array) >= size:
            break
            
        link = article.h3.a['href']
        if not link.startswith('http'):
            link = "https://weixin.sogou.com" + link

        article_content = get_article_content(link, headers)
        if article_content:
            urls.append(article_content['link'])
            article_json = {
                'title': article.h3.a.text.strip(),
                'author': article.find('span', class_='all-time-y2').text.strip(),
                'date': find_time_convert(article.find("span", class_='s2').find('script').text.strip()),
                'link': article_content['link'],
                'redict_link': article_content['redict_link'],
                'content': article_content['content']
            }
            result_array.append(article_json)

    return result_array


if __name__ == '__main__':
    # 使用方法示例
    # # 1. 搜索文章
    # search_result = search_weixin_articles('焦虑', 2)
    # for e in search_result:
    #     print(e)
        
    # 2. 获取单个文章内容
    article_url = "https://mp.weixin.qq.com/s/5ZsXhTe9uprF6iYC4xfVdQ"  # 替换为实际的文章URL
    article_content = get_article_content(article_url)
    if article_content:
        print(article_content)
