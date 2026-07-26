"""
使用 Playwright 拦截并提取完整的 API 请求信息
==============================================

运行此脚本后：
1. 浏览器会打开问财
2. 执行一次查询操作
3. 脚本会自动提取 Cookie 和 hexin-v
"""

import asyncio
import json
from pathlib import Path


async def intercept_request(save_path: str = "request_info.json"):
    """
    拦截 API 请求并提取信息

    Args:
        save_path: 保存路径
    """
    from playwright.async_api import async_playwright

    captured_request = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 拦截请求
        def handle_request(request):
            if "/customized/chart/get-robot-data" in request.url:
                print(f"\n拦截到请求: {request.url[:80]}...")
                captured_request['url'] = request.url
                captured_request['method'] = request.method
                captured_request['headers'] = dict(request.headers)
                captured_request['post_data'] = request.post_data

        page.on("request", handle_request)

        print("正在访问问财...")
        await page.goto("https://www.iwencai.com", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        print("\n请在浏览器中执行一次查询操作")
        print("例如：在搜索框输入 '贵州茅台' 并点击搜索")
        print("等待拦截到请求后，脚本会自动提取信息...")

        # 等待拦截到请求
        max_wait = 180  # 3分钟
        waited = 0
        while not captured_request and waited < max_wait:
            await asyncio.sleep(1)
            waited += 1
            if waited % 10 == 0:
                print(f"等待中... ({waited}秒)")

        if captured_request:
            print("\n成功拦截到请求！")

            # 提取关键信息
            headers = captured_request.get('headers', {})
            cookie = headers.get('cookie', '')
            hexin_v = headers.get('hexin-v', '')

            print(f"\n提取的信息:")
            print(f"  Cookie: {cookie[:100]}...")
            print(f"  hexin-v: {hexin_v}")

            # 保存完整信息
            with open(save_path, 'w') as f:
                json.dump(captured_request, f, indent=2, ensure_ascii=False)
            print(f"\n完整信息已保存到: {save_path}")

            # 保存 Cookie
            cookie_path = "cookie.txt"
            Path(cookie_path).write_text(cookie)
            print(f"Cookie 已保存到: {cookie_path}")

            # 保存 hexin-v
            hexin_path = "hexin_v.txt"
            Path(hexin_path).write_text(hexin_v)
            print(f"hexin-v 已保存到: {hexin_path}")

            # 测试 Cookie
            print("\n正在测试 Cookie...")
            await test_cookie(cookie, hexin_v)

        else:
            print("\n未拦截到请求，超时")

        await asyncio.sleep(2)
        await browser.close()


async def test_cookie(cookie: str, hexin_v: str):
    """测试 Cookie"""
    import requests

    url = 'https://www.iwencai.com/customized/chart/get-robot-data'

    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'hexin-v': hexin_v,
        'referer': 'https://www.iwencai.com/screener/result',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
        'cookie': cookie,
    }

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
        if response.status_code == 200:
            result = response.json()
            if 'data' in result:
                print("✅ Cookie 有效！")
                print(f"   user_id: {result['data'].get('user_id')}")
                return True
        print(f"❌ Cookie 无效 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

    return False


def sync_intercept(save_path: str = "request_info.json"):
    """同步入口"""
    asyncio.run(intercept_request(save_path))


if __name__ == "__main__":
    print("=" * 60)
    print("问财请求拦截工具")
    print("=" * 60)
    print()
    print("此脚本会：")
    print("1. 打开浏览器访问问财")
    print("2. 等待你执行一次查询")
    print("3. 自动提取 Cookie 和 hexin-v")
    print()
    print("请确保已登录问财")
    print("=" * 60)
    print()

    sync_intercept()
