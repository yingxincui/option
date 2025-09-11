import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta


@st.cache_data(ttl=3600)
def load_etf_data(symbol: str, period: str = "daily", days: int = 250) -> pd.DataFrame | None:
	try:
		end_date = datetime.now().strftime("%Y%m%d")
		start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
		df = ak.fund_etf_hist_em(
			symbol=symbol,
			period=period,
			start_date=start_date,
			end_date=end_date,
			adjust="qfq",
		)
		if df is not None and not df.empty:
			df["日期"] = pd.to_datetime(df["日期"]).dt.tz_localize(None)
			return df.sort_values("日期").reset_index(drop=True)
	except Exception as e:
		# 不立即返回，尝试备用源
		st.warning(f"实时接口超时或失败，尝试启用新浪备用数据源… ({e})")

	# 备用：新浪 fund_etf_hist_sina
	try:
		from utils.option_utils import get_fund_etf_hist_sina
		# 将代码映射为新浪代码：常见规则 5xx/51x/56x等为上海，159xxx多为深圳
		code = str(symbol)
		if code.startswith("sh") or code.startswith("sz"):
			sina_symbol = code
		else:
			if code.startswith("5") or code.startswith("51") or code.startswith("56"):
				sina_symbol = f"sh{code}"
			elif code.startswith("1") or code.startswith("159"):
				sina_symbol = f"sz{code}"
			else:
				# 默认上交所前缀
				sina_symbol = f"sh{code}"

		df_sina = get_fund_etf_hist_sina(sina_symbol)
		if df_sina is None or df_sina.empty:
			return None

		# 重命名并对齐字段
		df_sina = df_sina.rename(columns={
			"date": "日期",
			"open": "开盘",
			"high": "最高",
			"low": "最低",
			"close": "收盘",
			"volume": "成交量",
		})
		df_sina["日期"] = pd.to_datetime(df_sina["日期"]).dt.tz_localize(None)
		df_sina = df_sina.sort_values("日期").reset_index(drop=True)

		# 仅保留最近 days 天
		cutoff = pd.Timestamp.now().tz_localize(None) - pd.Timedelta(days=days)
		df_sina = df_sina[df_sina["日期"] >= cutoff]

		# 频率转换
		if period in ("weekly", "monthly"):
			freq = "W" if period == "weekly" else "M"
			df_sina = (
				df_sina.set_index("日期").resample(freq).agg({
					"开盘": "first",
					"最高": "max",
					"最低": "min",
					"收盘": "last",
					"成交量": "sum",
				}).dropna(how="any").reset_index()
			)

		st.info("已启用新浪备用数据源（fund_etf_hist_sina）")
		return df_sina
	except Exception as e2:
		st.error(f"备用数据源也失败：{e2}")
		return None


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.copy()
    # 均线
    df["MA5"] = df["收盘"].rolling(5).mean()
    df["MA10"] = df["收盘"].rolling(10).mean()
    df["MA20"] = df["收盘"].rolling(20).mean()
    df["MA60"] = df["收盘"].rolling(60).mean()
    # MACD
    exp1 = df["收盘"].ewm(span=12).mean()
    exp2 = df["收盘"].ewm(span=26).mean()
    df["MACD"] = exp1 - exp2
    df["MACD_Signal"] = df["MACD"].ewm(span=9).mean()
    df["MACD_Histogram"] = df["MACD"] - df["MACD_Signal"]
    # RSI(14)
    delta = df["收盘"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    # KDJ(9,3,3)
    low_n = df["最低"].rolling(window=9).min()
    high_n = df["最高"].rolling(window=9).max()
    rsv = (df["收盘"] - low_n) / (high_n - low_n).replace(0, np.nan) * 100
    df["K"] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df["D"] = df["K"].ewm(alpha=1/3, adjust=False).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]
    # OBV 及均线
    price_change = df["收盘"].diff().fillna(0)
    direction = np.where(price_change > 0, 1, np.where(price_change < 0, -1, 0))
    df["OBV"] = (direction * df["成交量"]).cumsum()
    df["OBV_MA10"] = df["OBV"].rolling(10).mean()
    # 涨跌幅（%）
    df["涨跌幅"] = df["收盘"].pct_change() * 100
    # 布林带
    df["BB_Middle"] = df["收盘"].rolling(20).mean()
    bb_std = df["收盘"].rolling(20).std()
    df["BB_Upper"] = df["BB_Middle"] + bb_std * 2
    df["BB_Lower"] = df["BB_Middle"] - bb_std * 2
    # 成交量均线
    df["Volume_MA5"] = df["成交量"].rolling(5).mean()
    df["Volume_MA10"] = df["成交量"].rolling(10).mean()
    return df


def create_etf_chart(df: pd.DataFrame, title: str) -> go.Figure | None:
    if df is None or df.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["日期"], open=df["开盘"], high=df["最高"], low=df["最低"], close=df["收盘"], name="K线",
        increasing_line_color="red", decreasing_line_color="green",
    ))
    fig.add_trace(go.Scatter(x=df["日期"], y=df["MA5"], mode="lines", name="MA5", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=df["日期"], y=df["MA10"], mode="lines", name="MA10", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=df["日期"], y=df["MA20"], mode="lines", name="MA20", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=df["日期"], y=df["BB_Upper"], mode="lines", name="布林上轨", line=dict(dash="dash", width=1), opacity=0.7))
    fig.add_trace(go.Scatter(x=df["日期"], y=df["BB_Lower"], mode="lines", name="布林下轨", line=dict(dash="dash", width=1), opacity=0.7, fill="tonexty", fillcolor="rgba(128,128,128,0.1)"))
    fig.update_layout(title=title, xaxis_title="日期", yaxis_title="价格", height=600, hovermode="x unified")
    return fig


def analyze_technical_signals(df: pd.DataFrame) -> dict:
    if df is None or df.empty or len(df) < 20:
        return {}
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    signals: dict = {}
    # 均线位置
    signals['price_above_ma5'] = latest['收盘'] > latest['MA5']
    signals['price_above_ma10'] = latest['收盘'] > latest['MA10']
    signals['price_above_ma20'] = latest['收盘'] > latest['MA20']
    # 多头/金叉
    signals['bullish_alignment'] = latest['MA5'] > latest['MA10'] > latest['MA20']
    signals['ma5_ma10_golden_cross'] = (latest['MA5'] > latest['MA10']) and (prev['MA5'] <= prev['MA10'])
    signals['ma5_ma10_death_cross'] = (latest['MA5'] < latest['MA10']) and (prev['MA5'] >= prev['MA10'])
    signals['ma10_ma20_golden_cross'] = (latest['MA10'] > latest['MA20']) and (prev['MA10'] <= prev['MA20'])
    signals['ma10_ma20_death_cross'] = (latest['MA10'] < latest['MA20']) and (prev['MA10'] >= prev['MA20'])
    # MACD
    signals['macd_golden_cross'] = (latest['MACD'] > latest['MACD_Signal']) and (prev['MACD'] <= prev['MACD_Signal'])
    signals['macd_death_cross'] = (latest['MACD'] < latest['MACD_Signal']) and (prev['MACD'] >= prev['MACD_Signal'])
    signals['macd_above_zero'] = latest['MACD'] > 0
    # 布林
    signals['price_above_bb_upper'] = latest['收盘'] > latest.get('BB_Upper', np.nan)
    signals['price_below_bb_lower'] = latest['收盘'] < latest.get('BB_Lower', np.nan)
    signals['price_in_bb'] = not signals['price_above_bb_upper'] and not signals['price_below_bb_lower']
    # 成交量
    vol_ma5 = latest.get('Volume_MA5', np.nan)
    signals['volume_surge'] = (latest['成交量'] / vol_ma5) > 1.5 if vol_ma5 and not np.isnan(vol_ma5) else False
    signals['volume_shrink'] = (latest['成交量'] / vol_ma5) < 0.8 if vol_ma5 and not np.isnan(vol_ma5) else False
    return signals


def create_trend_chart(df: pd.DataFrame, symbol_name: str):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=(f'{symbol_name} 趋势型指标分析', 'MACD指标'), row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df['日期'], open=df['开盘'], high=df['最高'], low=df['最低'], close=df['收盘'],
                                 name='K线', increasing_line_color='red', decreasing_line_color='green'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MA5'], name='MA5', line=dict(width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MA10'], name='MA10', line=dict(width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MA20'], name='MA20', line=dict(width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MA60'], name='MA60', line=dict(width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MACD'], name='MACD', line=dict(width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MACD_Signal'], name='Signal', line=dict(width=2)), row=2, col=1)
    colors = ['#dc3545' if val >= 0 else '#28a745' for val in df['MACD_Histogram']]
    fig.add_trace(go.Bar(x=df['日期'], y=df['MACD_Histogram'], name='Histogram', marker_color=colors, opacity=0.6), row=2, col=1)
    fig.add_hline(y=0, line_dash='dash', line_color='gray', row=2, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False, height=600, showlegend=True,
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def create_oscillator_chart(df: pd.DataFrame, symbol_name: str):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=(f'{symbol_name} 摆动型指标分析', 'RSI指标', 'KDJ指标'), row_heights=[0.4, 0.3, 0.3])
    fig.add_trace(go.Scatter(x=df['日期'], y=df['收盘'], name='收盘价', line=dict(width=2)), row=1, col=1)
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(x=df['日期'], y=df['RSI'], name='RSI', line=dict(width=2)), row=2, col=1)
    else:
        fig.add_trace(go.Scatter(x=df['日期'], y=[None]*len(df), name='RSI', line=dict(width=2)), row=2, col=1)
    fig.add_hline(y=70, line_dash='dash', line_color='red', row=2, col=1)
    fig.add_hline(y=30, line_dash='dash', line_color='green', row=2, col=1)
    if all(c in df.columns for c in ['K', 'D', 'J']):
        fig.add_trace(go.Scatter(x=df['日期'], y=df['K'], name='K', line=dict(width=2)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['日期'], y=df['D'], name='D', line=dict(width=2)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['日期'], y=df['J'], name='J', line=dict(width=2)), row=3, col=1)
        fig.add_hline(y=80, line_dash='dash', line_color='red', row=3, col=1)
        fig.add_hline(y=20, line_dash='dash', line_color='green', row=3, col=1)
    fig.update_layout(height=700, showlegend=True, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def create_energy_chart(df: pd.DataFrame, symbol_name: str):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=(f'{symbol_name} 能量型指标分析', '成交量', 'OBV指标'), row_heights=[0.4, 0.3, 0.3])
    fig.add_trace(go.Scatter(x=df['日期'], y=df['收盘'], name='收盘价', line=dict(width=2)), row=1, col=1)
    colors = ['#dc3545' if df['收盘'].iloc[i] >= df['收盘'].iloc[i-1] else '#28a745' for i in range(1, len(df))]
    colors.insert(0, '#dc3545')
    fig.add_trace(go.Bar(x=df['日期'], y=df['成交量'], name='成交量', marker_color=colors, opacity=0.7), row=2, col=1)
    if 'Volume_MA5' in df.columns:
        fig.add_trace(go.Scatter(x=df['日期'], y=df['Volume_MA5'], name='成交量MA5', line=dict(width=2)), row=2, col=1)
    if 'Volume_MA10' in df.columns:
        fig.add_trace(go.Scatter(x=df['日期'], y=df['Volume_MA10'], name='成交量MA10', line=dict(width=2)), row=2, col=1)
    if 'OBV' in df.columns:
        fig.add_trace(go.Scatter(x=df['日期'], y=df['OBV'], name='OBV', line=dict(width=2)), row=3, col=1)
        if 'OBV_MA10' in df.columns:
            fig.add_trace(go.Scatter(x=df['日期'], y=df['OBV_MA10'], name='OBV_MA10', line=dict(width=2)), row=3, col=1)
    fig.update_layout(height=700, showlegend=True, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def create_space_chart(df: pd.DataFrame, symbol_name: str):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=(f'{symbol_name} 空间型指标分析', '布林带指标'), row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df['日期'], open=df['开盘'], high=df['最高'], low=df['最低'], close=df['收盘'], name='K线',
                                 increasing_line_color='red', decreasing_line_color='green'), row=1, col=1)
    if all(c in df.columns for c in ['BB_Upper', 'BB_Lower', 'BB_Middle']):
        fig.add_trace(go.Scatter(x=df['日期'], y=df['BB_Upper'], name='布林上轨', line=dict(width=1, dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['日期'], y=df['BB_Middle'], name='布林中轨', line=dict(width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['日期'], y=df['BB_Lower'], name='布林下轨', line=dict(width=1, dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MA20'], name='MA20', line=dict(width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MA60'], name='MA60', line=dict(width=2)), row=1, col=1)
    if all(c in df.columns for c in ['BB_Upper', 'BB_Lower', 'BB_Middle']):
        bb_width = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']) * 100
        fig.add_trace(go.Scatter(x=df['日期'], y=bb_width, name='布林带宽度%', line=dict(width=2)), row=2, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False, height=600, showlegend=True,
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def render_full_etf_analysis(symbol_name: str, symbol_code: str, default_period: str = 'daily', default_days: int = 250):
    st.markdown(f"## {symbol_name} 技术分析")
    # 将筛选统一放到侧边栏，降低页面重复感
    st.sidebar.subheader(f"参数（{symbol_code}）")
    period = st.sidebar.selectbox(
        "分析周期",
        ["daily", "weekly", "monthly"],
        index=["daily", "weekly", "monthly"].index(default_period),
        key=f"period_select_{symbol_code}"
    )
    days = st.sidebar.slider(
        "历史数据天数",
        min_value=60,
        max_value=500,
        value=default_days,
        step=10,
        key=f"days_slider_{symbol_code}"
    )

    with st.spinner("加载数据..."):
        df = load_etf_data(symbol_code, period, days)
    if df is None or df.empty:
        st.warning("无数据")
        return
    df = calculate_technical_indicators(df)
    signals = analyze_technical_signals(df)

    # 综合结论
    st.subheader("📊 综合技术分析")
    # 可复用现有页面的综合结论，但为简洁此处仅放主图和分类图

    tab_main, tab_trend, tab_osc, tab_energy, tab_space = st.tabs(["主图", "趋势", "摆动", "能量", "空间"])

    with tab_main:
        main_fig = create_etf_chart(df, f"{symbol_name} 技术分析图表")
        if main_fig:
            st.plotly_chart(main_fig, use_container_width=True, key=f"plot_main_{symbol_code}")

    with tab_trend:
        trend_fig = create_trend_chart(df, symbol_name)
        st.plotly_chart(trend_fig, use_container_width=True, key=f"plot_trend_{symbol_code}")

    with tab_osc:
        osc_fig = create_oscillator_chart(df, symbol_name)
        st.plotly_chart(osc_fig, use_container_width=True, key=f"plot_osc_{symbol_code}")

    with tab_energy:
        energy_fig = create_energy_chart(df, symbol_name)
        st.plotly_chart(energy_fig, use_container_width=True, key=f"plot_energy_{symbol_code}")

    with tab_space:
        space_fig = create_space_chart(df, symbol_name)
        st.plotly_chart(space_fig, use_container_width=True, key=f"plot_space_{symbol_code}")

    # 数据与下载
    st.subheader("最近20日数据")
    show_cols = ["日期", "开盘", "最高", "最低", "收盘", "成交量", "MA5", "MA10", "MA20", "MACD", "RSI"]
    st.dataframe(df[show_cols].tail(20), use_container_width=True, height=420)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("下载CSV", csv, file_name=f"{symbol_name}_{symbol_code}.csv", mime="text/csv", key=f"download_{symbol_code}")


def render_etf_page(symbol_name: str, symbol_code: str, default_period: str = "daily", default_days: int = 250):
    # 保留向后兼容：简单版本
    render_full_etf_analysis(symbol_name, symbol_code, default_period, default_days)
    st.markdown(f"## {symbol_name} 技术分析")
    col_a, col_b = st.columns(2)
    with col_a:
        period = st.selectbox("分析周期", ["daily", "weekly", "monthly"], index=["daily", "weekly", "monthly"].index(default_period))
    with col_b:
        days = st.slider("历史数据天数", min_value=60, max_value=500, value=default_days, step=10)

    with st.spinner("加载数据..."):
        df = load_etf_data(symbol_code, period, days)
    if df is None or df.empty:
        st.warning("无数据")
        return
    df = calculate_technical_indicators(df)

    fig = create_etf_chart(df, f"{symbol_name} 技术分析图表")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("最近20日数据")
    show_cols = ["日期", "开盘", "最高", "最低", "收盘", "成交量", "MA5", "MA10", "MA20"]
    st.dataframe(df[show_cols].tail(20), use_container_width=True, height=420)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("下载CSV", csv, file_name=f"{symbol_name}_{symbol_code}.csv", mime="text/csv")


