# 期权工具函数包

这个包包含了用于处理期权相关数据的工具函数，主要功能是获取和管理期权合约的到期月份信息。

## 文件结构

```
utils/
├── __init__.py          # 包初始化文件
├── option_utils.py      # 主要工具函数
├── example_usage.py     # 使用示例
└── README.md           # 说明文档
```

## 主要功能

### 1. 到期月份管理

#### `get_option_expiry_months(symbol="50ETF")`
获取指定期权品种的到期月份列表

**参数：**
- `symbol`: 期权品种，支持 "50ETF" 或 "300ETF"

**返回：**
- `list`: 到期月份列表，格式如 `['202509', '202510', '202512', '202603']`

**示例：**
```python
months = get_option_expiry_months("50ETF")
print(months)  # ['202509', '202510', '202512', '202603']
```

#### `format_expiry_months(months)`
格式化到期月份列表为可读格式

**参数：**
- `months`: 原始月份列表

**返回：**
- `list`: 格式化后的月份列表，格式如 `['2025年09月', '2025年10月', '2025年12月', '2026年03月']`

**示例：**
```python
formatted = format_expiry_months(['202509', '202510'])
print(formatted)  # ['2025年09月', '2025年10月']
```

#### `get_all_option_expiry_months()`
获取所有期权品种的到期月份

**返回：**
- `dict`: 包含各品种到期月份的字典

#### `get_option_expiry_months_by_exchange(exchange="SSE")`
按交易所获取期权到期月份

**参数：**
- `exchange`: 交易所，支持 "SSE"（上交所）或 "SZSE"（深交所）

**返回：**
- `dict`: 包含各品种到期月份的字典

#### `get_nearest_expiry_month(symbol="50ETF", months_ahead=1)`
获取最近的到期月份

**参数：**
- `symbol`: 期权品种
- `months_ahead`: 向前查找几个月，默认为1（下个月）

**返回：**
- `str`: 最近的到期月份

#### `get_expiry_months_count(symbol="50ETF")`
获取期权品种的到期月份数量

**参数：**
- `symbol`: 期权品种

**返回：**
- `int`: 到期月份数量

#### `validate_expiry_month(symbol="50ETF", month="202509")`
验证到期月份是否有效

**参数：**
- `symbol`: 期权品种
- `month`: 要验证的月份

**返回：**
- `bool`: 是否为有效的到期月份

#### `get_expiry_months_info(symbol="50ETF")`
获取期权品种的到期月份详细信息

**参数：**
- `symbol`: 期权品种

**返回：**
- `dict`: 包含到期月份详细信息的字典

### 2. 期权合约代码管理

#### `get_option_codes(trade_date="202509", underlying="510300", option_type="看涨期权")`
获取指定条件下的期权合约代码

**参数：**
- `trade_date`: 交易日期，格式如 "202509"
- `underlying`: 标的代码，如 "510300"（沪深300ETF）
- `option_type`: 期权类型，"看涨期权" 或 "看跌期权"

**返回：**
- `pandas.DataFrame`: 包含期权代码的DataFrame

**示例：**
```python
call_codes = get_option_codes(trade_date="202509", underlying="510300", option_type="看涨期权")
print(call_codes.head())
#    序号      期权代码
# 0   1  10009179
# 1   2  10009180
# 2   3  10008811
```

#### `get_all_option_codes(trade_date="202509", underlying="510300")`
获取指定条件下的所有期权合约代码（看涨+看跌）

**参数：**
- `trade_date`: 交易日期，格式如 "202509"
- `underlying`: 标的代码，如 "510300"（沪深300ETF）

**返回：**
- `dict`: 包含看涨和看跌期权代码的字典

**示例：**
```python
all_codes = get_all_option_codes(trade_date="202509", underlying="510300")
print(f"看涨期权: {len(all_codes['看涨期权'])} 个")
print(f"看跌期权: {len(all_codes['看跌期权'])} 个")
```

#### `get_option_codes_by_underlying(underlying_list, trade_date="202509")`
获取多个标的的所有期权合约代码

**参数：**
- `underlying_list`: 标的代码列表，如 ["510300", "510050"]
- `trade_date`: 交易日期，格式如 "202509"

**返回：**
- `dict`: 包含各标的期权代码的字典

#### `get_option_codes_summary(trade_date="202509", underlying="510300")`
获取期权合约代码摘要信息

**参数：**
- `trade_date`: 交易日期
- `underlying`: 标的代码

**返回：**
- `dict`: 包含摘要信息的字典

**示例：**
```python
summary = get_option_codes_summary(trade_date="202509", underlying="510300")
print(f"看涨期权数量: {summary['call_count']}")
print(f"看跌期权数量: {summary['put_count']}")
print(f"总数量: {summary['total_count']}")
```

#### `search_option_codes(trade_date="202509", underlying="510300", search_term="")`
搜索期权合约代码

**参数：**
- `trade_date`: 交易日期
- `underlying`: 标的代码
- `search_term`: 搜索关键词（在期权代码中搜索）

**返回：**
- `dict`: 包含搜索结果的字典

**示例：**
```python
results = search_option_codes(trade_date="202509", underlying="510300", search_term="10009")
print(f"匹配数量: {results['total_matches']}")
```

#### `get_option_codes_by_expiry(trade_date="202509", underlying="510300", expiry_month="")`
根据到期月份获取期权合约代码

**参数：**
- `trade_date`: 交易日期
- `underlying`: 标的代码
- `expiry_month`: 到期月份，格式如 "202509"

**返回：**
- `dict`: 包含指定到期月份期权代码的字典

### 3. 期权希腊字母管理

#### `get_option_greeks(symbol)`
获取期权希腊字母信息

**参数：**
- `symbol`: 期权代码，如 "10009179"

**返回：**
- `pandas.DataFrame`: 包含希腊字母信息的DataFrame

**示例：**
```python
greeks = get_option_greeks("10009180")
print(greeks[greeks['字段'] == 'Delta']['值'].iloc[0])  # 1
print(greeks[greeks['字段'] == 'Gamma']['值'].iloc[0])  # 0
```

#### `get_multiple_option_greeks(symbols)`
获取多个期权的希腊字母信息

**参数：**
- `symbols`: 期权代码列表

**返回：**
- `dict`: 包含各期权希腊字母信息的字典

#### `get_option_greeks_summary(symbols)`
获取期权希腊字母信息摘要

**参数：**
- `symbols`: 期权代码列表

**返回：**
- `pandas.DataFrame`: 包含所有期权希腊字母信息的汇总表

**示例：**
```python
symbols = ["10009179", "10009180", "10009181", "10009182"]
summary = get_option_greeks_summary(symbols)
print(f"摘要表包含 {len(summary)} 个期权")
```

#### `format_greeks_data(greeks_df)`
格式化希腊字母数据为更易读的格式

**参数：**
- `greeks_df`: 希腊字母DataFrame

**返回：**
- `dict`: 格式化后的希腊字母数据

#### `get_option_greeks_by_underlying(trade_date="202509", underlying="510300", limit=10)`
获取指定标的的期权希腊字母信息

**参数：**
- `trade_date`: 交易日期
- `underlying`: 标的代码
- `limit`: 限制获取的期权数量

**返回：**
- `pandas.DataFrame`: 包含希腊字母信息的汇总表

**示例：**
```python
greeks = get_option_greeks_by_underlying(trade_date="202509", underlying="510300", limit=5)
print(f"获取到 {len(greeks)} 个期权的希腊字母信息")
```

## 使用示例

### 到期月份管理

```python
from utils.option_utils import get_option_expiry_months, format_expiry_months

# 获取50ETF到期月份
months = get_option_expiry_months("50ETF")
print(f"原始格式: {months}")

# 格式化显示
formatted = format_expiry_months(months)
print(f"格式化后: {formatted}")
```

### 期权合约代码管理

```python
from utils.option_utils import get_option_codes, get_all_option_codes

# 获取看涨期权代码
call_codes = get_option_codes(trade_date="202509", underlying="510300", option_type="看涨期权")
print(f"看涨期权数量: {len(call_codes)}")

# 获取所有期权代码
all_codes = get_all_option_codes(trade_date="202509", underlying="510300")
print(f"看涨期权: {len(all_codes['看涨期权'])} 个")
print(f"看跌期权: {len(all_codes['看跌期权'])} 个")
```

### 批量处理

```python
from utils.option_utils import get_all_option_expiry_months, get_option_codes_by_underlying

# 获取所有品种的到期月份
all_months = get_all_option_expiry_months()
for symbol, data in all_months.items():
    print(f"{symbol}: {data['formatted']}")

# 获取多个标的的期权代码
multi_codes = get_option_codes_by_underlying(["510300", "510050"], "202509")
for underlying, codes in multi_codes.items():
    call_count = len(codes['看涨期权']) if not codes['看涨期权'].empty else 0
    put_count = len(codes['看跌期权']) if not codes['看跌期权'].empty else 0
    print(f"{underlying}: 看涨{call_count}个, 看跌{put_count}个")
```

### 高级功能

```python
from utils.option_utils import get_nearest_expiry_month, validate_expiry_month, search_option_codes

# 获取下个月到期月份
next_month = get_nearest_expiry_month("50ETF", 1)
print(f"下个月到期: {next_month}")

# 验证月份是否有效
is_valid = validate_expiry_month("50ETF", "202509")
print(f"202509是否有效: {is_valid}")

# 搜索期权代码
search_results = search_option_codes(trade_date="202509", underlying="510300", search_term="10009")
print(f"匹配数量: {search_results['total_matches']}")
```

## 运行示例

要运行使用示例，请执行：

```bash
cd utils
python example_usage.py
```

## 注意事项

1. **缓存机制**: 所有数据获取函数都使用了 `@st.cache_data` 装饰器，缓存时间为1小时，避免重复请求
2. **错误处理**: 网络异常时会返回空列表或空字符串，不会中断程序执行
3. **数据源**: 使用 akshare 库获取数据，需要网络连接
4. **格式要求**: 月份格式为6位数字字符串（如 "202509"），年份在前，月份在后

## 依赖项

- `akshare`: 用于获取期权数据
- `streamlit`: 用于缓存功能
- `typing`: 用于类型提示

## 更新日志

- v1.0.0: 初始版本，包含基础到期月份获取功能
- v1.1.0: 添加格式化、批量获取、验证等高级功能
- v1.2.0: 新增期权合约代码管理功能，包括获取、搜索、批量处理等
- v1.3.0: 新增期权希腊字母管理功能，包括获取、格式化、批量处理等
- v1.3.1: 修复希腊字母数据转换中的索引错误问题
