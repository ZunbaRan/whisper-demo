from google import genai
from google.genai import types

from google.genai import _api_client


def patch_client_with_proxy(client, proxy_url):
    """
    为现有的client实例增加代理设置
    
    Args:
        client: google.genai.Client实例
        proxy_url: 代理URL，例如 "http://username:password@host:port"
    
    Returns:
        修改后的client实例
    """
    # 创建带有代理配置的http_options
    http_options = types.HttpOptions(
        client_args={"proxy": proxy_url}
    )
    
    # 修改客户端实例中的_http_options
    patched = _api_client._patch_http_options(
        client._api_client._http_options,
        http_options
    )

    client._api_client._http_options = patched
    
    # 重新创建带有代理的httpx客户端
    client_args, async_client_args = client._api_client._ensure_ssl_ctx(
        client._api_client._http_options
    )
    
    # 关闭现有连接
    client._api_client._httpx_client.close()
    client._api_client._async_httpx_client.aclose()
    
    # 创建新的连接池
    from google.genai._api_client import SyncHttpxClient, AsyncHttpxClient
    client._api_client._httpx_client = SyncHttpxClient(**client_args)
    client._api_client._async_httpx_client = AsyncHttpxClient(**async_client_args)
    
    return client

# 使用示例
"""
# 使用patch函数修改实例
client = genai.Client(api_key='GEMINI_API_KEY')
client = patch_client_with_proxy(client, "http://127.0.0.1:7890")
response = client.models.generate_content(
    model=model,
    contents=prompt,
    stream=True
)
""" 