"""
从浏览器 Network 请求中提取完整信息
=====================================

使用方法：
1. 在浏览器中登录问财
2. F12 -> Network -> 刷新页面
3. 找一个 POST /customized/chart/get-robot-data 请求
4. 右键 -> Copy -> Copy as cURL
5. 粘贴到下面的 curl_command 变量中
6. 运行脚本提取 Cookie 和 hexin-v
"""

import re
import subprocess
import json


def extract_from_curl(curl_command: str) -> dict:
    """
    从 curl 命令中提取 Cookie 和 hexin-v

    Args:
        curl_command: curl 命令（从浏览器复制）

    Returns:
        dict: {'cookie': ..., 'hexin-v': ..., 'url': ...}
    """
    result = {}

    # 提取 URL
    url_match = re.search(r"curl\s+'(https?://[^']+)'", curl_command)
    if not url_match:
        url_match = re.search(r"curl\s+\"(https?://[^\"]+)\"", curl_command)
    if not url_match:
        url_match = re.search(r"https?://[^\s\\]+", curl_command)

    if url_match:
        result['url'] = url_match.group(0).rstrip("'\"\\")

    # 提取 Cookie
    cookie_match = re.search(r"--cookie\s+['\"]([^'\"]+)['\"]", curl_command, re.IGNORECASE)
    if cookie_match:
        result['cookie'] = cookie_match.group(1)
    else:
        # 尝试从 -H 'Cookie: xxx' 中提取
        cookie_header = re.search(r"-H\s+['\"]Cookie:\s*([^'\"]+)['\"]", curl_command, re.IGNORECASE)
        if cookie_header:
            result['cookie'] = cookie_header.group(1)

    # 提取 hexin-v
    hexin_match = re.search(r"-H\s+['\"]hexin-v:\s*([^'\"]+)['\"]", curl_command, re.IGNORECASE)
    if hexin_match:
        result['hexin-v'] = hexin_match.group(1)

    # 提取 User-Agent
    ua_match = re.search(r"-H\s+['\"]User-Agent:\s*([^'\"]+)['\"]", curl_command, re.IGNORECASE)
    if ua_match:
        result['user-agent'] = ua_match.group(1)

    return result


def test_cookie(cookie: str, hexin_v: str = None) -> bool:
    """
    测试 Cookie 是否有效

    Args:
        cookie: Cookie 字符串
        hexin_v: hexin-v token

    Returns:
        bool: 是否有效
    """
    import requests

    url = 'https://www.iwencai.com/customized/chart/get-robot-data'

    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'referer': 'https://www.iwencai.com/screener/result',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
        'cookie': cookie,
    }

    if hexin_v:
        headers['hexin-v'] = hexin_v
    else:
        # 使用默认的 hexin-v
        headers['hexin-v'] = 'A4rf0LbO1KA5k1gMX6VVpUJo3Xspew-8APyCeRTDN5FoESSl_Ate5dCP0s3n'

    data = {
        'add_info': '{"urp":{"scene":1,"company":1,"business":1},"contentType":"json","searchInfo":true}',
        'perpage': '100',
        'page': 1,
        'source': 'Ths_iwencai_Xuangu',
        'log_info': '{"input_type":"click"}',
        'version': '2.0',
        'secondary_intent': 'stock',
        'question': '贵州茅台'
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        return response.status_code == 200
    except Exception:
        return False


def save_config(cookie: str, hexin_v: str = None):
    """保存配置到文件"""
    config = {
        'cookie': cookie,
        'hexin-v': hexin_v or 'A4rf0LbO1KA5k1gMX6VVpUJo3Xspew-8APyCeRTDN5FoESSl_Ate5dCP0s3n',
    }

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print(f"配置已保存到 config.json")


# 示例 curl 命令（请替换为从浏览器复制的命令）
EXAMPLE_CURL = """
curl 'https://www.iwencai.com/customized/chart/get-robot-data' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'content-type: application/json' \
  -H 'cookie: other_uid=xxx; user=xxx; ...' \
  -H 'hexin-v: A4rf0LbO1KA5k1gMX6VVpUJo3Xspew-8APyCeRTDN5FoESSl_Ate5dCP0s3n' \
  -H 'referer: https://www.iwencai.com/screener/result' \
  -H 'user-agent: Mozilla/5.0 ...' \
  --data-raw '{"add_info":"...","question":"贵州茅台",...}'
"""


if __name__ == "__main__":
    print("=" * 60)
    print("从浏览器提取 Cookie 和 hexin-v")
    print("=" * 60)
    print()
    print("使用方法：")
    print("1. 登录 https://www.iwencai.com")
    print("2. F12 -> Network -> 刷新页面")
    print("3. 找到 POST /customized/chart/get-robot-data 请求")
    print("4. 右键 -> Copy -> Copy as cURL (bash)")
    print("5. 粘贴到下面的 curl_command 变量中")
    print()
    print("请编辑此脚本，将 EXAMPLE_CURL 替换为实际的 curl 命令")
    print("=" * 60)

    # 提示用户编辑脚本
    print("\n请将 curl 命令粘贴到脚本中，然后重新运行")
