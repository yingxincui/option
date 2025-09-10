"""
期权工具函数 - 使用东方财富期权风险分析接口
"""

import pandas as pd
import streamlit as st

try:
    import akshare as ak
except ImportError:
    ak = None


def get_option_greeks_by_underlying() -> pd.DataFrame:
    """
    获取期权风险数据（希腊字母等）。
    使用东方财富期权风险分析接口：ak.option_risk_analysis_em()
    
    返回：
        pandas.DataFrame：期权风险数据，包含希腊字母等信息
    """
    if ak is None:
        return pd.DataFrame()
    
    try:
        df = ak.option_risk_analysis_em()
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=30 * 24 * 60 * 60)  # 缓存30天
def get_available_etf_names() -> list:
    """
    获取所有可用的ETF名称列表（缓存30天）

    返回：
        list：ETF名称列表，如 ['50ETF', '300ETF', '500ETF', '科创50', '科创板50']
    """
    df = get_option_greeks_by_underlying()
    if df.empty:
        return []

    etf_names = set()
    for name in df['期权名称']:
        # 提取ETF名称：在"购"或"沽"之前的部分
        etf_name = name.split('购')[0].split('沽')[0]
        etf_names.add(etf_name)

    return sorted(list(etf_names))


def get_options_by_etf(etf_name: str) -> pd.DataFrame:
    """
    根据ETF名称筛选对应的期权数据

    参数：
        etf_name (str): ETF名称，如 '50ETF', '300ETF', '科创50' 等

    返回：
        pandas.DataFrame：筛选后的期权数据
    """
    df = get_option_greeks_by_underlying()
    if df.empty:
        return pd.DataFrame()

    # 筛选包含指定ETF名称的期权
    mask = df['期权名称'].str.contains(etf_name, na=False)
    return df[mask].reset_index(drop=True)


def get_option_value_analysis() -> pd.DataFrame:
    """
    获取期权价值分析数据（隐含波动率等）
    使用东方财富期权价值分析接口：ak.option_value_analysis_em()

    返回：
        pandas.DataFrame：期权价值分析数据，包含隐含波动率、时间价值、内在价值等
    """
    if ak is None:
        return pd.DataFrame()

    try:
        df = ak.option_value_analysis_em()
        return df
    except Exception:
        return pd.DataFrame()


def get_option_premium_analysis() -> pd.DataFrame:
    """
    获取期权折溢价分析数据
    使用东方财富期权折溢价接口：ak.option_premium_analysis_em()

    返回：
        pandas.DataFrame：期权折溢价分析数据，包含折溢价率、盈亏平衡价等
    """
    if ak is None:
        return pd.DataFrame()

    try:
        df = ak.option_premium_analysis_em()
        return df
    except Exception:
        return pd.DataFrame()


def merge_option_data(etf_name: str) -> pd.DataFrame:
    """
    合并期权风险数据、价值分析数据和折溢价分析数据

    参数：
        etf_name (str): ETF名称

    返回：
        pandas.DataFrame：合并后的期权数据
    """
    # 获取风险数据
    risk_df = get_options_by_etf(etf_name)
    if risk_df.empty:
        return pd.DataFrame()
    
    # 获取价值分析数据
    value_df = get_option_value_analysis()
    if not value_df.empty:
        risk_df = risk_df.merge(
            value_df[['期权代码', '时间价值', '内在价值', '隐含波动率', '理论价格', '标的最新价', '标的近一年波动率']],
            on='期权代码',
            how='left'
        )
    
    # 获取折溢价分析数据
    premium_df = get_option_premium_analysis()
    if not premium_df.empty:
        risk_df = risk_df.merge(
            premium_df[['期权代码', '期权名称', '最新价', '涨跌幅', '行权价', '折溢价率', 
                       '标的名称', '标的最新价', '标的涨跌幅', '盈亏平衡价', '到期日']],
            on='期权代码',
            how='left',
            suffixes=('', '_premium')
        )
    
    return risk_df


