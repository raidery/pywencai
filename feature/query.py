"""
问财数据查询核心模块
====================

直接调用问财 get-robot-data API 获取选股数据

API 信息
--------
- URL: POST https://www.iwencai.com/customized/chart/get-robot-data
- 协议: HTTPS
- 认证: Cookie + hexin-v token

请求参数
--------
- add_info: str - 附加配置
- perpage: int - 每页数量，最大 100
- page: int - 页码
- source: str - 来源，固定 "Ths_iwencai_Xuangu"
- version: str - 版本，固定 "2.0"
- secondary_intent: str - 查询类型，默认 "stock"
- question: str - 查询条件

响应结构
--------
response['data']['answer'][0]['txt'][0]['content']
    ↓ JSON 解析
components[0]['data']
    ├── datas: List[dict] - 股票数据
    ├── meta.extra.row_count: int - 总记录数
    └── meta.extra.condition: list - 解析后的条件

字段说明
--------
问财返回的字段包含日期后缀，例如：
- 涨跌幅:前复权[20260724]
- 量比[20260724]
- 换手率[20260724]
- a股市值(不含限售股)[20260724]

常用字段（不带日期）：
- 股票代码 / code
- 股票简称 / stock_name
- 最新价
- 涨跌幅
"""

import json
import subprocess
from typing import Dict, List, Optional, Union

import requests


# ==================== 常量配置 ====================

API_URL = 'https://www.iwencai.com/customized/chart/get-robot-data'

DEFAULT_HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/json',
    'referer': 'https://www.iwencai.com/screener/result',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
}

# 默认硬编码的 token（可能过期）
DEFAULT_HEXIN_V = 'A6NNt8lRze8ELIHboy7c2rMbNOxImDWIcSp7DtUA_j141c0SXWjHKoH8C3Pm'

# hexin-v.js 路径
HEXIN_V_JS_PATH = None  # 会在 init 时设置


# ==================== 工具函数 ====================

def get_hexin_v() -> str:
    """
    获取 hexin-v token

    优先使用 hexin-v.js 动态生成，如果失败则使用默认的 token

    Returns:
        str: hexin-v token
    """
    global HEXIN_V_JS_PATH
    
    # 尝试动态生成
    if HEXIN_V_JS_PATH:
        try:
            import subprocess
            token = subprocess.check_output(
                ['node', HEXIN_V_JS_PATH],
                stderr=subprocess.DEVNULL,
                timeout=10
            ).decode().strip()
            if token and len(token) > 20:
                return token
        except Exception:
            pass
    
    # 降级使用默认 token
    return DEFAULT_HEXIN_V


def build_headers(cookie: str, hexin_v: str = None) -> Dict[str, str]:
    """
    构建 HTTP 请求头

    Args:
        cookie: 问财 Cookie
        hexin_v: hexin-v token（可选，不传则自动获取）

    Returns:
        dict: HTTP 请求头
    """
    if hexin_v is None:
        hexin_v = get_hexin_v()
    
    return {
        **DEFAULT_HEADERS,
        'hexin-v': hexin_v,
        'cookie': cookie,
    }


def build_payload(
    query: str,
    perpage: int = 100,
    page: int = 1,
    secondary_intent: str = 'stock',
) -> Dict[str, Union[str, int]]:
    """
    构建请求体

    Args:
        query: 查询条件（自然语言）
        perpage: 每页数量
        page: 页码
        secondary_intent: 查询类型

    Returns:
        dict: 请求体
    """
    return {
        'add_info': '{"urp":{"scene":1,"company":1,"business":1},"contentType":"json","searchInfo":true}',
        'perpage': str(perpage),
        'page': page,
        'source': 'Ths_iwencai_Xuangu',
        'log_info': '{"input_type":"click"}',
        'version': '2.0',
        'secondary_intent': secondary_intent,
        'question': query,
    }


def parse_response(result: Dict) -> Dict:
    """
    解析问财 API 响应

    Args:
        result: 原始响应 dict

    Returns:
        dict: 解析后的结果
        {
            'datas': List[dict],  # 股票数据
            'row_count': int,       # 总记录数
            'condition': list,      # 解析后的条件
            'raw_response': dict,   # 原始响应
        }
    """
    # 获取 answer
    answer = result.get('data', {}).get('answer', [{}])[0]
    txt_list = answer.get('txt', [])

    if not txt_list:
        return {
            'datas': [],
            'row_count': 0,
            'condition': [],
            'raw_response': result,
        }

    # 解析 content（可能是字符串或字典）
    raw_content = txt_list[0].get('content')
    if isinstance(raw_content, str):
        content = json.loads(raw_content)
    else:
        content = raw_content or {}

    # 获取 components
    components = content.get('components', [])

    if not components:
        return {
            'datas': [],
            'row_count': 0,
            'condition': [],
            'raw_response': result,
        }

    # 获取数据
    first_comp = components[0]
    comp_data = first_comp.get('data', {})
    meta = comp_data.get('meta', {})
    extra = meta.get('extra', {})

    # 解析 condition
    condition_raw = extra.get('condition', '[]')
    condition = json.loads(condition_raw) if isinstance(condition_raw, str) else condition_raw

    datas = comp_data.get('datas', [])
    row_count = extra.get('row_count', len(datas))

    return {
        'datas': datas,
        'row_count': row_count,
        'condition': condition,
        'raw_response': result,
    }


# ==================== 核心函数 ====================

def query_wencai(
    query: str,
    cookie: str,
    perpage: int = 100,
    page: int = 1,
    hexin_v: Optional[str] = None,
    timeout: int = 30,
) -> Dict:
    """
    查询问财数据

    Args:
        query: 查询条件（自然语言）
            示例:
                - '贵州茅台'
                - '7月份回购；7月跌幅超过20%'
                - '涨幅2%-5% 量比大于1 换手率3%-15%'

        cookie: 问财 Cookie（必须有效）
            获取方法:
                1. 登录 https://www.iwencai.com
                2. F12 打开开发者工具
                3. Network 标签
                4. 刷新页面
                5. 找一个 POST 请求
                6. 复制请求头的 Cookie 字段

        perpage: 每页数量，默认 100（问财最大支持 100）

        page: 页码，默认 1

        hexin_v: hexin-v token（可选）
            如果不传，会自动通过 hexin-v.js 动态生成

        timeout: 请求超时时间（秒），默认 30

    Returns:
        dict: 查询结果
        {
            'datas': List[dict],     # 股票列表
            'row_count': int,         # 总记录数
            'condition': list,        # 解析后的条件
            'raw_response': dict,     # 原始响应
        }

    Raises:
        requests.RequestException: 请求失败时抛出

    Example:
        >>> result = query_wencai(
        ...     query='涨幅2%-5% 量比大于1',
        ...     cookie='your_cookie'
        ... )
        >>> print(f"找到 {result['row_count']} 只股票")
        >>> for stock in result['datas'][:5]:
        ...     print(stock['股票简称'], stock['最新价'])
    """
    headers = build_headers(cookie, hexin_v)
    payload = build_payload(query, perpage, page)

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    result = response.json()
    return parse_response(result)


# ==================== 辅助函数 ====================

def get_date_suffix(datas: List[dict]) -> Optional[str]:
    """
    从数据中提取日期后缀

    问财返回的字段格式如: 涨跌幅:前复权[20260724]
    需要提取 [20260724] 部分

    Args:
        datas: 股票数据列表

    Returns:
        str or None: 日期后缀，如 '[20260724]'
    """
    if not datas:
        return None
    for key in datas[0].keys():
        if '[20' in key and ']' in key:
            return '[' + key.split('[')[1]
    return None


def get_field(stock: dict, field: str, date_suffix: Optional[str] = None) -> any:
    """
    获取字段值，自动尝试带日期后缀和不带后缀

    Args:
        stock: 股票数据 dict
        field: 字段名（不含日期）
        date_suffix: 日期后缀，如 '[20260724]'

    Returns:
        字段值，找不到返回 None
    """
    if date_suffix:
        value = stock.get(field + date_suffix)
        if value is not None:
            return value
    return stock.get(field)


def fmt_value(v, suffix: str = '') -> str:
    """
    格式化数值

    Args:
        v: 原始值
        suffix: 后缀，如 '%'

    Returns:
        str: 格式化后的字符串
    """
    if v is None or v == '':
        return 'N/A'
    try:
        val = float(v)
        if abs(val) >= 1e8:
            return f'{val/1e8:.2f}亿'
        return f'{val:.2f}{suffix}'
    except (ValueError, TypeError):
        return str(v)[:10]


def print_result(result: Dict, max_rows: int = 50) -> None:
    """
    打印查询结果表格

    Args:
        result: query_wencai 返回的结果
        max_rows: 最大显示行数
    """
    datas = result.get('datas', [])
    row_count = result.get('row_count', len(datas))

    print('=' * 90)
    print(f'查询结果: 共 {row_count} 条记录')
    print('=' * 90)

    if not datas:
        print('无数据')
        return

    date_suffix = get_date_suffix(datas)
    display_datas = datas[:max_rows] if max_rows else datas

    print()
    print(f'{"序号":<4} {"代码":<12} {"名称":<10} {"现价":<8} {"涨幅":<8} {"量比":<6} {"换手率":<8} {"流通市值":<12}')
    print('-' * 90)

    for i, stock in enumerate(display_datas):
        code = stock.get('股票代码', stock.get('code', ''))
        name = stock.get('股票简称', stock.get('stock_name', ''))
        price = get_field(stock, '最新价', date_suffix)
        pct = get_field(stock, '涨跌幅:前复权', date_suffix) or get_field(stock, '涨跌幅', date_suffix)
        vol_ratio = get_field(stock, '量比', date_suffix)
        turnover = get_field(stock, '换手率', date_suffix)
        market_cap = get_field(stock, 'a股市值(不含限售股)', date_suffix) or get_field(stock, '流通市值', date_suffix)

        print(
            f'{i+1:<4} {code:<12} {name:<10} '
            f'{fmt_value(price):<8} {fmt_value(pct, "%"):<8} '
            f'{fmt_value(vol_ratio):<6} {fmt_value(turnover, "%"):<8} '
            f'{fmt_value(market_cap):<12}'
        )

    if max_rows and len(datas) > max_rows:
        print(f'\n... 还有 {len(datas) - max_rows} 条记录')

    print('=' * 90)


def save_result(result: Dict, filepath: str) -> None:
    """
    保存查询结果到 JSON 文件

    Args:
        result: query_wencai 返回的结果
        filepath: 保存路径
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'结果已保存到: {filepath}')


# ==================== 初始化 ====================

def init(hexin_v_js_path: str = None):
    """
    初始化模块

    Args:
        hexin_v_js_path: hexin-v.js 文件路径
            如果不传，会自动查找 pywencai/hexin-v.js
    """
    global HEXIN_V_JS_PATH
    
    if hexin_v_js_path:
        HEXIN_V_JS_PATH = hexin_v_js_path
    else:
        # 自动查找
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        default_path = os.path.join(parent_dir, 'pywencai', 'hexin-v.js')
        if os.path.exists(default_path):
            HEXIN_V_JS_PATH = default_path


# 自动初始化
init()
