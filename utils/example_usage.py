"""
期权工具函数使用示例
"""

from option_utils import (
    get_option_expiry_months,
    format_expiry_months,
    get_all_option_expiry_months,
    get_option_expiry_months_by_exchange,
    get_nearest_expiry_month,
    get_expiry_months_count,
    validate_expiry_month,
    get_expiry_months_info,
    get_option_codes,
    get_all_option_codes,
    get_option_codes_by_underlying,
    get_option_codes_summary,
    search_option_codes,
    get_option_codes_by_expiry,
    get_option_greeks,
    get_multiple_option_greeks,
    get_option_greeks_summary,
    format_greeks_data,
    get_option_greeks_by_underlying
)


def main():
    """主函数 - 演示各种工具函数的使用"""
    
    print("=== 期权工具函数使用示例 ===\n")
    
    # 1. 获取50ETF到期月份
    print("1. 获取50ETF到期月份:")
    months_50 = get_option_expiry_months("50ETF")
    print(f"   原始格式: {months_50}")
    print(f"   格式化后: {format_expiry_months(months_50)}")
    print()
    
    # 2. 获取300ETF到期月份
    print("2. 获取300ETF到期月份:")
    months_300 = get_option_expiry_months("300ETF")
    print(f"   原始格式: {months_300}")
    print(f"   格式化后: {format_expiry_months(months_300)}")
    print()
    
    # 3. 获取所有品种的到期月份
    print("3. 获取所有品种的到期月份:")
    all_months = get_all_option_expiry_months()
    for symbol, data in all_months.items():
        print(f"   {symbol}: {data['formatted']}")
    print()
    
    # 4. 按交易所获取到期月份
    print("4. 按交易所获取到期月份:")
    sse_months = get_option_expiry_months_by_exchange("SSE")
    print(f"   上交所: {sse_months}")
    print()
    
    # 5. 获取最近的到期月份
    print("5. 获取最近的到期月份:")
    nearest_50 = get_nearest_expiry_month("50ETF", 1)  # 下个月
    nearest_300 = get_nearest_expiry_month("300ETF", 1)
    print(f"   50ETF下个月: {nearest_50}")
    print(f"   300ETF下个月: {nearest_300}")
    print()
    
    # 6. 获取到期月份数量
    print("6. 获取到期月份数量:")
    count_50 = get_expiry_months_count("50ETF")
    count_300 = get_expiry_months_count("300ETF")
    print(f"   50ETF: {count_50} 个月份")
    print(f"   300ETF: {count_300} 个月份")
    print()
    
    # 7. 验证到期月份
    print("7. 验证到期月份:")
    test_month = "202509"
    is_valid_50 = validate_expiry_month("50ETF", test_month)
    is_valid_300 = validate_expiry_month("300ETF", test_month)
    print(f"   {test_month} 在50ETF中有效: {is_valid_50}")
    print(f"   {test_month} 在300ETF中有效: {is_valid_300}")
    print()
    
    # 8. 获取到期月份详细信息
    print("8. 获取到期月份详细信息:")
    info_50 = get_expiry_months_info("50ETF")
    print(f"   50ETF详细信息: {info_50}")
    print()
    
    # 9. 获取期权合约代码
    print("9. 获取期权合约代码:")
    call_codes = get_option_codes(trade_date="202509", underlying="510300", option_type="看涨期权")
    put_codes = get_option_codes(trade_date="202509", underlying="510300", option_type="看跌期权")
    print(f"   看涨期权数量: {len(call_codes)}")
    print(f"   看跌期权数量: {len(put_codes)}")
    print(f"   看涨期权前5个: {call_codes['期权代码'].head().tolist()}")
    print(f"   看跌期权前5个: {put_codes['期权代码'].head().tolist()}")
    print()
    
    # 10. 获取所有期权合约代码
    print("10. 获取所有期权合约代码:")
    all_codes = get_all_option_codes(trade_date="202509", underlying="510300")
    print(f"   看涨期权: {len(all_codes['看涨期权'])} 个")
    print(f"   看跌期权: {len(all_codes['看跌期权'])} 个")
    print()
    
    # 11. 获取期权代码摘要
    print("11. 获取期权代码摘要:")
    summary = get_option_codes_summary(trade_date="202509", underlying="510300")
    print(f"   交易日期: {summary['trade_date']}")
    print(f"   标的代码: {summary['underlying']}")
    print(f"   看涨期权数量: {summary['call_count']}")
    print(f"   看跌期权数量: {summary['put_count']}")
    print(f"   总数量: {summary['total_count']}")
    print()
    
    # 12. 搜索期权代码
    print("12. 搜索期权代码:")
    search_results = search_option_codes(trade_date="202509", underlying="510300", search_term="10009")
    print(f"   搜索关键词: '10009'")
    print(f"   看涨期权匹配: {len(search_results['call_matches'])} 个")
    print(f"   看跌期权匹配: {len(search_results['put_matches'])} 个")
    print(f"   总匹配数: {search_results['total_matches']}")
    print()
    
    # 13. 获取多个标的的期权代码
    print("13. 获取多个标的的期权代码:")
    multi_underlying = get_option_codes_by_underlying(["510300", "510050"], "202509")
    for underlying, codes in multi_underlying.items():
        call_count = len(codes['看涨期权']) if not codes['看涨期权'].empty else 0
        put_count = len(codes['看跌期权']) if not codes['看跌期权'].empty else 0
        print(f"   {underlying}: 看涨{call_count}个, 看跌{put_count}个")
    print()
    
    # 14. 获取期权希腊字母信息
    print("14. 获取期权希腊字母信息:")
    greeks = get_option_greeks("10009180")
    if not greeks.empty:
        print(f"   期权代码: 10009180")
        print(f"   期权合约简称: {greeks[greeks['字段'] == '期权合约简称']['值'].iloc[0]}")
        print(f"   Delta: {greeks[greeks['字段'] == 'Delta']['值'].iloc[0]}")
        print(f"   Gamma: {greeks[greeks['字段'] == 'Gamma']['值'].iloc[0]}")
        print(f"   Theta: {greeks[greeks['字段'] == 'Theta']['值'].iloc[0]}")
        print(f"   Vega: {greeks[greeks['字段'] == 'Vega']['值'].iloc[0]}")
    print()
    
    # 15. 获取多个期权的希腊字母信息
    print("15. 获取多个期权的希腊字母信息:")
    symbols = ["10009179", "10009180", "10009181", "10009182"]
    multi_greeks = get_multiple_option_greeks(symbols)
    print(f"   成功获取 {len(multi_greeks)} 个期权的希腊字母信息")
    for symbol, data in multi_greeks.items():
        if not data.empty:
            delta = data[data['字段'] == 'Delta']['值'].iloc[0] if not data[data['字段'] == 'Delta'].empty else 'N/A'
            print(f"   {symbol}: Delta={delta}")
    print()
    
    # 16. 获取希腊字母信息摘要
    print("16. 获取希腊字母信息摘要:")
    greeks_summary = get_option_greeks_summary(symbols)
    if not greeks_summary.empty:
        print(f"   摘要表包含 {len(greeks_summary)} 个期权")
        print(f"   列名: {greeks_summary.columns.tolist()}")
    print()
    
    # 17. 格式化希腊字母数据
    print("17. 格式化希腊字母数据:")
    if not greeks.empty:
        formatted = format_greeks_data(greeks)
        print(f"   格式化后的数据: {formatted}")
    print()
    
    # 18. 获取指定标的的希腊字母信息
    print("18. 获取指定标的的希腊字母信息:")
    underlying_greeks = get_option_greeks_by_underlying(trade_date="202509", underlying="510300", limit=5)
    if not underlying_greeks.empty:
        print(f"   沪深300ETF希腊字母信息: {len(underlying_greeks)} 个期权")
        print(f"   列名: {underlying_greeks.columns.tolist()}")
    print()


if __name__ == "__main__":
    main()
