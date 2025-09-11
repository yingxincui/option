"""
期权工具函数 - 使用东方财富期权风险分析接口
"""

import os
import time
from pathlib import Path
import pandas as pd
import streamlit as st

try:
	import akshare as ak
except ImportError:
	ak = None

# 本地缓存目录
_CACHE_DIR = Path(__file__).resolve().parent.parent / "data_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(name: str) -> Path:
	return _CACHE_DIR / f"{name}.csv"


def _save_cache(df: pd.DataFrame, name: str) -> None:
	try:
		if df is not None and not df.empty:
			df.to_csv(_cache_path(name), index=False, encoding="utf-8-sig")
	except Exception:
		pass


def _load_cache(name: str) -> pd.DataFrame:
	p = _cache_path(name)
	if p.exists():
		try:
			return pd.read_csv(p)
		except Exception:
			return pd.DataFrame()
	return pd.DataFrame()


def _fetch_with_retry(fetch_fn, cache_name: str, retries: int = 3, backoff_seconds: float = 1.5) -> pd.DataFrame:
	"""
	通用重试与本地缓存回退：
	- 最多重试 retries 次；
	- 失败则返回本地缓存（如有）；
	- 成功则刷新本地缓存。
	"""
	last_err = None
	for attempt in range(1, retries + 1):
		try:
			df = fetch_fn()
			if isinstance(df, pd.DataFrame) and not df.empty:
				_save_cache(df, cache_name)
				return df
			# 空数据也继续重试
		except Exception as e:
			last_err = e
		time.sleep(backoff_seconds * attempt)
	# 全部失败，尝试本地缓存
	cached = _load_cache(cache_name)
	if not cached.empty:
		st.info("已启用本地缓存数据（实时接口超时）。")
		return cached
	# 最终兜底：返回空表
	if last_err:
		st.warning(f"数据加载失败：{type(last_err).__name__}")
	return pd.DataFrame()


@st.cache_data(ttl=10 * 60)  # 接口结果缓存10分钟，减少频繁请求
def get_option_greeks_by_underlying() -> pd.DataFrame:
	"""
	获取期权风险数据（希腊字母等）。
	使用东方财富期权风险分析接口：ak.option_risk_analysis_em()
	"""
	if ak is None:
		return pd.DataFrame()
	return _fetch_with_retry(lambda: ak.option_risk_analysis_em(), "option_risk_analysis_em")


@st.cache_data(ttl=30 * 24 * 60 * 60)  # 缓存30天
def get_available_etf_names() -> list:
	"""
	获取所有可用的ETF名称列表（缓存30天）
	"""
	df = get_option_greeks_by_underlying()
	if df.empty or "期权名称" not in df.columns:
		return []
	etf_names = set()
	for name in df["期权名称"]:
		etf_name = str(name).split('购')[0].split('沽')[0]
		if etf_name:
			etf_names.add(etf_name)
	return sorted(list(etf_names))


def get_options_by_etf(etf_name: str) -> pd.DataFrame:
	"""
	根据ETF名称筛选对应的期权数据
	"""
	df = get_option_greeks_by_underlying()
	if df.empty or "期权名称" not in df.columns:
		return pd.DataFrame()
	mask = df["期权名称"].astype(str).str.contains(etf_name, na=False)
	return df[mask].reset_index(drop=True)


@st.cache_data(ttl=10 * 60)
def get_option_value_analysis() -> pd.DataFrame:
	"""
	获取期权价值分析数据（隐含波动率等）
	使用东方财富期权价值分析接口：ak.option_value_analysis_em()
	"""
	if ak is None:
		return pd.DataFrame()
	return _fetch_with_retry(lambda: ak.option_value_analysis_em(), "option_value_analysis_em")


@st.cache_data(ttl=10 * 60)
def get_option_premium_analysis() -> pd.DataFrame:
	"""
	获取期权折溢价分析数据
	使用东方财富期权折溢价接口：ak.option_premium_analysis_em()
	"""
	if ak is None:
		return pd.DataFrame()
	return _fetch_with_retry(lambda: ak.option_premium_analysis_em(), "option_premium_analysis_em")


def merge_option_data(etf_name: str) -> pd.DataFrame:
	"""
	合并期权风险数据、价值分析数据和折溢价分析数据
	"""
	# 获取风险数据
	risk_df = get_options_by_etf(etf_name)
	if risk_df.empty:
		return pd.DataFrame()
	# 获取价值分析数据
	value_df = get_option_value_analysis()
	if not value_df.empty and "期权代码" in value_df.columns:
		risk_df = risk_df.merge(
			value_df[[c for c in ["期权代码", "时间价值", "内在价值", "隐含波动率", "理论价格", "标的最新价", "标的近一年波动率"] if c in value_df.columns]],
			on="期权代码",
			how="left"
		)
	# 获取折溢价分析数据
	premium_df = get_option_premium_analysis()
	if not premium_df.empty and "期权代码" in premium_df.columns:
		risk_df = risk_df.merge(
			premium_df[[c for c in ["期权代码", "期权名称", "最新价", "涨跌幅", "行权价", "折溢价率",
						   "标的名称", "标的最新价", "标的涨跌幅", "盈亏平衡价", "到期日"] if c in premium_df.columns]],
			on="期权代码",
			how="left",
			suffixes=("", "_premium")
		)
	return risk_df


@st.cache_data(ttl=6 * 60 * 60)
def get_fund_etf_hist_sina(symbol: str) -> pd.DataFrame:
	"""
	备用接口：基金历史行情-新浪
	接口: ak.fund_etf_hist_sina(symbol="sh510050")
	返回列：date, open, high, low, close, volume（单位：手）
	"""
	if ak is None or not symbol:
		return pd.DataFrame()
	return _fetch_with_retry(lambda: ak.fund_etf_hist_sina(symbol=symbol), f"fund_etf_hist_sina_{symbol}")


