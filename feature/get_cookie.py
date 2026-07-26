"""
使用 Playwright 获取问财 Cookie
================================

重要：此脚本需要真实浏览器交互，不能在 headless 模式下工作！

使用步骤：
1. 运行脚本: uv run python feature/get_cookie.py
2. 浏览器会打开问财网站
3. 如果未登录，用手机扫码登录
4. 在搜索框输入任意查询（如"贵州茅台"）并搜索
5. 等待脚本自动提取 Cookie 和 hexin-v
6. 完成后浏览器会自动关闭
"""

import asyncio
import json
import time
from pathlib import Path


async def get_cookie_interactive():
    """
    交互式获取 Cookie
    - 打开浏览器
    - 等待用户操作（登录/查询）
    - 拦截请求获取完整信息
    """
    from playwright.async_api import async_playwright

    captured = {
        'url': None,
        'cookie': None,
        'hexin-v': None,
        'user-agent': None,
    }

    async with async_playwright() as p:
        # 启动非无头浏览器
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()

        # 拦截请求
        async def on_request(request):
            if "/customized/chart/get-robot-data" in request.url and request.method == "POST":
                headers = request.headers
                captured['url'] = request.url
                captured['cookie'] = headers.get('cookie', '')
                captured['hexin-v'] = headers.get('hexin-v', '')
                captured['user-agent'] = headers.get('user-agent', '')
                print("\n" + "=" * 60)
                print("✅ 成功拦截到 API 请求！")
                print("=" * 60)
                print(f"\n提取的信息:")
                print(f"  Cookie: {captured['cookie'][:80]}...")
                print(f"  hexin-v: {captured['hexin-v']}")
                
                # 保存文件
                save_files(captured)
                
                print("\n3秒后关闭浏览器...")
                await asyncio.sleep(3)
                await browser.close()
                raise KeyboardInterrupt("完成")

        page.on("request", on_request)

        print("=" * 60)
        print("问财 Cookie 获取工具")
        print("=" * 60)
        print()
        print("请按以下步骤操作：")
        print()
        print("1. 如果浏览器弹出登录窗口，请用手机扫码登录")
        print("2. 登录后，在搜索框输入: 贵州茅台")
        print("3. 点击搜索按钮")
        print("4. 等待脚本自动提取 Cookie")
        print()
        print("脚本会自动检测并提取信息，无需手动操作")
        print("=" * 60)
        print()

        # 访问问财
        await page.goto("https://www.iwencai.com", timeout=60000)
        print(f"当前页面: {page.url}")
        
        # 等待用户操作（最多3分钟）
        print("\n等待用户操作中... (按 Ctrl+C 可退出)")
        try:
            # 持续等待直到拦截到请求
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt as e:
            if str(e) != "完成":
                print("\n用户取消")
            await browser.close()
        except Exception as e:
            print(f"\n错误: {e}")
            await browser.close()


def save_files(captured: dict):
    """保存提取的文件"""
    # 保存 Cookie
    if captured.get('cookie'):
        Path("cookie.txt").write_text(captured['cookie'])
        print(f"\n已保存: cookie.txt")

    # 保存 hexin-v
    if captured.get('hexin-v'):
        Path("hexin_v.txt").write_text(captured['hexin-v'])
        print(f"已保存: hexin_v.txt")

    # 保存完整信息
    Path("request_info.json").write_text(
        json.dumps(captured, indent=2, ensure_ascii=False)
    )
    print(f"已保存: request_info.json")

    # 测试 Cookie
    test_cookie(captured.get('cookie'), captured.get('hexin-v'))


def test_cookie(cookie: str, hexin_v: str):
    """测试 Cookie"""
    import requests

    if not cookie:
        print("\n❌ Cookie 为空，无法测试")
        return

    url = 'https://www.iwencai.com/customized/chart/get-robot-data'

    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'hexin-v': hexin_v or 'A4rf0LbO1KA5k1gMX6VVpUJo3Xspew-8APyCeRTDN5FoESSl_Ate5dCP0s3n',
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

    print("\n正在测试 Cookie...")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if 'data' in result:
                print("✅ Cookie 有效！")
                print(f"   user_id: {result['data'].get('user_id')}")
            else:
                print("❌ Cookie 无效（返回数据异常）")
        else:
            print(f"❌ Cookie 无效 (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def sync_main():
    """同步入口"""
    try:
        asyncio.run(get_cookie_interactive())
    except KeyboardInterrupt:
        print("\n已退出")


if __name__ == "__main__":
    sync_main()
