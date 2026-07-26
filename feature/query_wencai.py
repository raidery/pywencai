"""
问财数据查询高级接口
====================

基于 query.py 的封装，提供更简单的使用方式

使用示例
--------
```python
from feature.query_wencai import WencaiQuery, query

# 方式1: 函数调用（需传入 cookie）
result = query(
    query='涨幅2%-5% 量比大于1',
    cookie='your_cookie'
)
print(result['datas'])

# 方式2: 类封装（cookie 可复用）
client = WencaiQuery(cookie='your_cookie')
result = client.query('涨幅2%-5%')
result = client.query('量比大于2')  # 复用 cookie

# 方式3: 从文件读取 cookie
client = WencaiQuery.from_cookie_file('cookie.txt')
result = client.query('涨幅2%-5%')
```
"""

from typing import Dict, List, Optional, Union

from .query import (
    API_URL,
    HEXIN_V_TOKEN,
    build_headers,
    build_payload,
    get_date_suffix,
    get_field,
    parse_response,
    print_result,
    query_wencai as _query_wencai,
    save_result,
    fmt_value,
)


# ==================== 快捷函数 ====================

def query(
    query: str,
    cookie: str,
    perpage: int = 100,
    page: int = 1,
    hexin_v: Optional[str] = None,
    timeout: int = 30,
) -> Dict:
    """
    查询问财数据（快捷函数）

    Args:
        query: 查询条件（自然语言）
        cookie: 问财 Cookie
        perpage: 每页数量，默认 100
        page: 页码，默认 1
        hexin_v: hexin-v token
        timeout: 超时时间（秒）

    Returns:
        dict: 包含 datas, row_count, condition, raw_response

    Example:
        >>> result = query('涨幅2%-5%', cookie='your_cookie')
        >>> for stock in result['datas']:
        ...     print(stock['股票简称'])
    """
    return _query_wencai(query, cookie, perpage, page, hexin_v, timeout)


# ==================== 类封装 ====================

class WencaiQuery:
    """
    问财查询客户端

    封装 cookie 和常用配置，支持多次查询

    Attributes:
        cookie: 问财 Cookie
        hexin_v: hexin-v token
        perpage: 每页数量
        timeout: 请求超时时间

    Example:
        >>> client = WencaiQuery(cookie='your_cookie')
        >>> result = client.query('涨幅2%-5%')
        >>> print(f"找到 {result['row_count']} 只")
    """

    def __init__(
        self,
        cookie: str,
        hexin_v: str = HEXIN_V_TOKEN,
        perpage: int = 100,
        timeout: int = 30,
    ):
        """
        初始化问财查询客户端

        Args:
            cookie: 问财 Cookie（必须有效）
            hexin_v: hexin-v token
            perpage: 每页数量
            timeout: 超时时间（秒）
        """
        self.cookie = cookie
        self.hexin_v = hexin_v
        self.perpage = perpage
        self.timeout = timeout

    @classmethod
    def from_cookie_file(cls, filepath: str, **kwargs) -> 'WencaiQuery':
        """
        从文件读取 Cookie 创建客户端

        Args:
            filepath: Cookie 文件路径
            **kwargs: 其他参数传递给 __init__

        Returns:
            WencaiQuery: 新实例

        Example:
            >>> client = WencaiQuery.from_cookie_file('cookie.txt')
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            cookie = f.read().strip()
        return cls(cookie=cookie, **kwargs)

    def query(
        self,
        query_str: str,
        perpage: Optional[int] = None,
        page: int = 1,
    ) -> Dict:
        """
        执行查询

        Args:
            query_str: 查询条件（自然语言）
            perpage: 每页数量，None 则使用默认值
            page: 页码

        Returns:
            dict: 查询结果
        """
        return _query_wencai(
            query=query_str,
            cookie=self.cookie,
            perpage=perpage or self.perpage,
            page=page,
            hexin_v=self.hexin_v,
            timeout=self.timeout,
        )

    def get_all(self, query_str: str, max_pages: int = 10) -> List[dict]:
        """
        获取所有数据（自动翻页）

        Args:
            query_str: 查询条件
            max_pages: 最大页数限制，防止无限翻页

        Returns:
            list: 所有股票数据

        Example:
            >>> client = WencaiQuery(cookie='your_cookie')
            >>> stocks = client.get_all('涨幅2%-5%')
            >>> print(f"共获取 {len(stocks)} 只股票")
        """
        # 第一页
        result = self.query(query_str, page=1)
        datas = result.get('datas', [])
        row_count = result.get('row_count', len(datas))

        if row_count <= len(datas):
            return datas

        # 翻页获取
        perpage = perpage or self.perpage
        total_pages = min(max_pages, (row_count + perpage - 1) // perpage)

        for page in range(2, total_pages + 1):
            page_result = self.query(query_str, page=page)
            page_datas = page_result.get('datas', [])
            if page_datas:
                datas.extend(page_datas)
            if len(datas) >= row_count:
                break

        return datas

    def print_result(self, query_str: str, **kwargs) -> None:
        """
        执行查询并打印结果

        Args:
            query_str: 查询条件
            **kwargs: 传递给 query 的其他参数
        """
        result = self.query(query_str, **kwargs)
        print_result(result)

    def save_result(self, query_str: str, filepath: str, **kwargs) -> None:
        """
        执行查询并保存结果

        Args:
            query_str: 查询条件
            filepath: 保存路径
            **kwargs: 传递给 query 的其他参数
        """
        result = self.query(query_str, **kwargs)
        save_result(result, filepath)


# ==================== 预定义查询 ====================

class StockFilters:
    """
    常用选股条件预设

    Example:
        >>> client = WencaiQuery(cookie='your_cookie')
        >>> result = client.query(StockFilters.RISING_2_5 + ' 量比大于1')
    """

    # 涨幅相关
    RISING_2_5 = '涨幅2%-5%'
    RISING_3_5 = '涨幅3%-5%'
    RISING_5_10 = '涨幅5%-10%'
    FALLING_2_5 = '跌幅2%-5%'

    # 量比相关
    VOLUME_RATIO_1 = '量比大于1'
    VOLUME_RATIO_2 = '量比大于2'
    VOLUME_RATIO_3 = '量比大于3'

    # 换手率相关
    TURNOVER_3_15 = '换手率3%-15%'
    TURNOVER_5_20 = '换手率5%-20%'

    # 市值相关
    FLOAT_MARKET_30_150 = '流通市值30亿-150亿'
    FLOAT_MARKET_50_200 = '流通市值50亿-200亿'

    # 技术指标
    ABOVE_5_MA = '股价在5日线上'
    ABOVE_10_MA = '股价在10日线上'
    MA5_UP = '5日均线向上'
    MA10_UP = '10日均线向上'
    NEW_HIGH = '创当日新高'


# ==================== 主程序 ====================

if __name__ == '__main__':
    print('问财数据查询工具')
    print('=' * 60)
    print()
    print('使用方式:')
    print('-' * 60)
    print('''
# 方式1: 快捷函数
from feature.query_wencai import query
result = query('涨幅2%-5%', cookie='your_cookie')

# 方式2: 类封装
from feature.query_wencai import WencaiQuery
client = WencaiQuery(cookie='your_cookie')
result = client.query('涨幅2%-5%')
client.print_result('涨幅2%-5%')
client.save_result('涨幅2%-5%', 'result.json')

# 方式3: 从文件读取 cookie
client = WencaiQuery.from_cookie_file('cookie.txt')
result = client.query('涨幅2%-5%')

# 使用预定义条件
from feature.query_wencai import StockFilters, WencaiQuery
client = WencaiQuery(cookie='your_cookie')
query_str = f'{StockFilters.RISING_2_5} {StockFilters.VOLUME_RATIO_1}'
result = client.query(query_str)
''')
    print('-' * 60)
