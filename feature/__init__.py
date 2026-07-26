"""
问财数据查询模块
=================

使用示例:
    from feature.query import query_wencai, print_result

    # 读取 cookie
    with open('cookie.txt') as f:
        cookie = f.read()

    # 查询
    result = query_wencai('涨幅2%-5%', cookie)
    print_result(result)
"""

from .query import (
    query_wencai,
    print_result,
    save_result,
    build_headers,
    build_payload,
    get_hexin_v,
    init,
    API_URL,
    DEFAULT_HEXIN_V,
    HEXIN_V_JS_PATH,
)

__all__ = [
    'query_wencai',
    'print_result',
    'save_result',
    'build_headers',
    'build_payload',
    'get_hexin_v',
    'init',
    'API_URL',
    'DEFAULT_HEXIN_V',
    'HEXIN_V_JS_PATH',
]
