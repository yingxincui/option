import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import date as _date

st.set_page_config(page_title="创业板期权波动率指数 QVIX", page_icon="📈", layout="wide")

@st.cache_data(ttl=60 * 60)
def load_qvix_data() -> pd.DataFrame:
    try:
        import akshare as ak
    except Exception as e:
        st.error("未安装或导入 akshare 失败，请先在环境中安装 akshare。")
        raise
    df = ak.index_option_cyb_qvix()
    # 规范列并处理日期
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    # 保障列存在
    for col in ["open", "high", "low", "close"]:
        if col not in df.columns:
            df[col] = np.nan
    # 仅保留 2022-10-01 及之后的数据
    cutoff = _date(2022, 10, 1)
    if "date" in df.columns:
        df = df[df["date"] >= cutoff]
    return df.sort_values("date").reset_index(drop=True)

@st.cache_data(ttl=60)
def load_qvix_min_data() -> pd.DataFrame:
    try:
        import akshare as ak
    except Exception:
        st.error("未安装或导入 akshare 失败，请先在环境中安装 akshare。")
        raise
    df = ak.index_option_cyb_min_qvix()
    # 规范列
    if "time" in df.columns:
        # 保留原始字符串时间以符合展示习惯
        df["time"] = df["time"].astype(str)
    if "qvix" not in df.columns:
        df["qvix"] = np.nan
    return df.reset_index(drop=True)

def render_header():
    st.markdown("## 创业板 期权波动率指数（QVIX）")
    st.caption("数据来源：`http://1.optbbs.com/s/vix.shtml?CYB`（通过 Akshare 获取）")

def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    # 已取消筛选与视图切换，保留函数以兼容，但不使用
    return df

def render_stats(df: pd.DataFrame):
    if df.empty:
        st.info("无数据")
        return
    # 百分位计算（基于当前筛选区间）
    pct_text = "-"
    show_risk = False
    if df['close'].notna().any():
        latest = float(df['close'].dropna().iloc[-1])
        closes = df['close'].dropna().astype(float)
        if len(closes) > 0:
            percentile = 100.0 * (closes <= latest).sum() / len(closes)
            pct_text = f"{percentile:.1f}%"
            show_risk = percentile >= 80.0

    if show_risk:
        st.warning(f"当前收盘位于所选区间的第 {pct_text} 百分位，风险提示：高位波动。")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("最新收盘", f"{df['close'].dropna().iloc[-1]:.2f}" if df['close'].notna().any() else "-")
    with col2:
        st.metric("区间最高", f"{df['high'].max():.2f}" if df['high'].notna().any() else "-")
    with col3:
        st.metric("区间最低", f"{df['low'].min():.2f}" if df['low'].notna().any() else "-")
    with col4:
        st.metric("收盘百分位", pct_text)

def _add_vol_bands(fig, df: pd.DataFrame, low_thresh: float, high_thresh: float, y_cap: float | None = 80.0):
    if df.empty:
        return
    # 兼容不同输入数据列（如分时仅有 qvix 或 close）
    cols_for_max = [c for c in ["high", "close", "qvix"] if c in df.columns]
    cols_for_min = [c for c in ["low", "close", "qvix"] if c in df.columns]
    if not cols_for_max or not cols_for_min:
        return
    y_max_data = float(pd.concat([df[c] for c in cols_for_max], axis=0).max(skipna=True))
    y_min_data = float(pd.concat([df[c] for c in cols_for_min], axis=0).min(skipna=True))
    y_min = min(y_min_data, low_thresh)
    y_max = max(y_max_data, high_thresh)
    pad = max((y_max - y_min) * 0.08, 0.5)
    y_min_pad = y_min - pad
    y_max_pad = y_max + pad

    # 纵坐标上限（可选）
    y_top = min(float(y_cap), y_max_pad) if y_cap is not None else y_max_pad
    if y_min_pad >= y_top:
        y_min_pad = max(0.0, y_top - 10.0)

    # 背景区间（置于下层）
    fig.add_hrect(y0=y_min_pad, y1=min(low_thresh, y_top), fillcolor="#4caf50", opacity=0.08, line_width=0, layer="below")
    fig.add_hrect(y0=min(low_thresh, y_top), y1=min(high_thresh, y_top), fillcolor="#ff9800", opacity=0.08, line_width=0, layer="below")
    fig.add_hrect(y0=min(high_thresh, y_top), y1=y_top, fillcolor="#f44336", opacity=0.08, line_width=0, layer="below")
    # 阈值线
    fig.add_hline(y=min(low_thresh, y_top), line_dash="dot", line_color="#4caf50", layer="below")
    fig.add_hline(y=min(high_thresh, y_top), line_dash="dot", line_color="#f44336", layer="below")

    # 固定 Y 轴范围，避免上方留白
    fig.update_yaxes(range=[y_min_pad, y_top])

    # 注释（不影响坐标范围）
    fig.add_annotation(text=f"低波≤{low_thresh:.1f}", xref="paper", x=0.995, y=min(low_thresh, y_top),
                       yref="y", showarrow=False, xanchor="right", font=dict(color="#2e7d32", size=11))
    fig.add_annotation(text=f"中波{low_thresh:.1f}-{high_thresh:.1f}", xref="paper", x=0.995, y=min((low_thresh+high_thresh)/2, y_top),
                       yref="y", showarrow=False, xanchor="right", font=dict(color="#ef6c00", size=11))
    fig.add_annotation(text=f"高波≥{high_thresh:.1f}", xref="paper", x=0.995, y=min(high_thresh, y_top),
                       yref="y", showarrow=False, xanchor="right", font=dict(color="#b71c1c", size=11))

def render_line(df: pd.DataFrame, low_thresh: float, high_thresh: float):
    fig = px.line(df, x="date", y="close", title="QVIX 收盘走势（含阈值参考）", markers=False)
    _add_vol_bands(fig, df, low_thresh, high_thresh, y_cap=80.0)
    fig.update_layout(height=460, xaxis_title="日期", yaxis_title="指数",
                      margin=dict(t=40, b=40, l=40, r=20))
    st.plotly_chart(fig, use_container_width=True)

def render_candlestick(df: pd.DataFrame, low_thresh: float, high_thresh: float):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["date"],
                open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                name="QVIX"
            )
        ]
    )
    _add_vol_bands(fig, df, low_thresh, high_thresh, y_cap=80.0)
    fig.update_layout(title="QVIX K线图（含阈值参考）", height=480, xaxis_title="日期", yaxis_title="指数",
                      margin=dict(t=50, b=40, l=40, r=20))
    st.plotly_chart(fig, use_container_width=True)

def render_table_and_download(df: pd.DataFrame):
    st.dataframe(df, use_container_width=True, height=420)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("下载CSV", csv, file_name="QVIX_CYB.csv", mime="text/csv")

def render_intraday(low_thresh: float, high_thresh: float):
    with st.spinner("加载分时数据..."):
        df_min = load_qvix_min_data()
    if df_min.empty or df_min["qvix"].isna().all():
        st.info("暂无分时数据")
        return
    st.subheader("当日分时 QVIX")
    # 构造用于阈值范围计算的临时 DataFrame（包含 qvix 列名以便通用处理）
    df_tmp = pd.DataFrame({"qvix": df_min["qvix"].astype(float)})
    fig = px.line(df_min, x="time", y="qvix", title="当日分时 QVIX（含阈值参考）")
    _add_vol_bands(fig, df_tmp, low_thresh, high_thresh, y_cap=None)
    fig.update_layout(height=420, xaxis_title="时间", yaxis_title="指数",
                      margin=dict(t=40, b=40, l=40, r=20))
    st.plotly_chart(fig, use_container_width=True)
    # 表格与下载
    with st.expander("查看分时原始数据"):
        st.dataframe(df_min, use_container_width=True, height=360)
        csv = df_min.to_csv(index=False).encode("utf-8-sig")
        st.download_button("下载分时CSV", csv, file_name="QVIX_CYB_min.csv", mime="text/csv")

def main():
    render_header()
    with st.spinner("加载数据中..."):
        df = load_qvix_data()
    # 默认阈值与顺序展示
    low_thresh, high_thresh = 20.0, 30.0
    filtered = df

    # 统计与风险提示
    render_stats(filtered)

    # 收盘线图
    render_line(filtered, low_thresh, high_thresh)

    # K 线图
    render_candlestick(filtered, low_thresh, high_thresh)

    # 原始数据与下载
    st.markdown("---")
    with st.expander("查看原始数据"):
        render_table_and_download(filtered)


if __name__ == "__main__":
    main()


