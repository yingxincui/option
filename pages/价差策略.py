import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 页面配置
st.set_page_config(
    page_title="期权价差策略",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 样式
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 2rem; }
    .section-header { font-size: 1.8rem; font-weight: bold; color: #2c3e50; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.0rem; border-radius: 0.5rem; text-align: center; margin: 0.25rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .metric-value { font-size: 1.5rem; font-weight: bold; margin-bottom: 0.25rem; }
    .metric-label { font-size: 0.9rem; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

# 计算函数

def calc_bull_call(spot, k_long, k_short, prem_long, prem_short, qty=100):
    prices = np.linspace(spot * 0.7, spot * 1.3, 121)
    long_pay = np.maximum(prices - k_long, 0) * qty - prem_long * qty
    short_pay = -np.maximum(prices - k_short, 0) * qty + prem_short * qty
    total = long_pay + short_pay
    return prices, long_pay, short_pay, total

def calc_bear_put(spot, k_long, k_short, prem_long, prem_short, qty=100):
    prices = np.linspace(spot * 0.7, spot * 1.3, 121)
    long_pay = np.maximum(k_long - prices, 0) * qty - prem_long * qty
    short_pay = -np.maximum(k_short - prices, 0) * qty + prem_short * qty
    total = long_pay + short_pay
    return prices, long_pay, short_pay, total

def calc_iron_condor(spot, p_long, p_short, c_short, c_long, pL, pS, cS, cL, qty=100):
    prices = np.linspace(spot * 0.6, spot * 1.4, 161)
    put_long = np.maximum(p_long - prices, 0) * qty - pL * qty
    put_short = -np.maximum(p_short - prices, 0) * qty + pS * qty
    call_short = -np.maximum(prices - c_short, 0) * qty + cS * qty
    call_long = np.maximum(prices - c_long, 0) * qty - cL * qty
    total = put_long + put_short + call_short + call_long
    return prices, put_long, put_short, call_short, call_long, total

def calc_butterfly(spot, k_low, k_mid, k_high, prem_low, prem_mid, prem_high, qty=100):
    prices = np.linspace(spot * 0.7, spot * 1.3, 121)
    low_call = np.maximum(prices - k_low, 0) * qty - prem_low * qty
    mid_call = -2 * np.maximum(prices - k_mid, 0) * qty + 2 * prem_mid * qty
    high_call = np.maximum(prices - k_high, 0) * qty - prem_high * qty
    total = low_call + mid_call + high_call
    return prices, low_call, mid_call, high_call, total

# 页面主体

def main():
    st.markdown('<h1 class="main-header">📈 期权价差策略详解</h1>', unsafe_allow_html=True)

    st.markdown('<h2 class="section-header">📋 策略选择</h2>', unsafe_allow_html=True)
    strategy = st.selectbox(
        "选择要分析的价差策略：",
        ["牛市看涨价差", "熊市看跌价差", "铁鹰价差", "蝶式价差", "价差策略对比"]
    )

    st.markdown('<h2 class="section-header">⚙️ 参数设置</h2>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        spot = st.number_input("当前股价 (元)", value=50.0, min_value=1.0, step=0.1)
        qty = st.number_input("合约数量", value=100, min_value=1, step=1)

    with c2:
        if strategy == "牛市看涨价差":
            k_long = st.number_input("买入看涨行权价 (元)", value=45.0, min_value=1.0, step=0.1)
            k_short = st.number_input("卖出看涨行权价 (元)", value=55.0, min_value=1.0, step=0.1)
            prem_long = st.number_input("买入看涨权利金 (元)", value=3.0, min_value=0.0, step=0.1)
            prem_short = st.number_input("卖出看涨权利金 (元)", value=1.0, min_value=0.0, step=0.1)
        elif strategy == "熊市看跌价差":
            k_long = st.number_input("买入看跌行权价 (元)", value=55.0, min_value=1.0, step=0.1)
            k_short = st.number_input("卖出看跌行权价 (元)", value=45.0, min_value=1.0, step=0.1)
            prem_long = st.number_input("买入看跌权利金 (元)", value=3.0, min_value=0.0, step=0.1)
            prem_short = st.number_input("卖出看跌权利金 (元)", value=1.0, min_value=0.0, step=0.1)
        elif strategy == "铁鹰价差":
            p_long = st.number_input("买入看跌行权价 (元)", value=40.0, min_value=1.0, step=0.1)
            p_short = st.number_input("卖出看跌行权价 (元)", value=45.0, min_value=1.0, step=0.1)
            c_short = st.number_input("卖出看涨行权价 (元)", value=55.0, min_value=1.0, step=0.1)
            c_long = st.number_input("买入看涨行权价 (元)", value=60.0, min_value=1.0, step=0.1)
            pL = st.number_input("买入看跌权利金 (元)", value=0.5, min_value=0.0, step=0.1)
            pS = st.number_input("卖出看跌权利金 (元)", value=1.5, min_value=0.0, step=0.1)
            cS = st.number_input("卖出看涨权利金 (元)", value=1.5, min_value=0.0, step=0.1)
            cL = st.number_input("买入看涨权利金 (元)", value=0.5, min_value=0.0, step=0.1)
        elif strategy == "蝶式价差":
            k_low = st.number_input("低行权价 (元)", value=40.0, min_value=1.0, step=0.1)
            k_mid = st.number_input("中间行权价 (元)", value=50.0, min_value=1.0, step=0.1)
            k_high = st.number_input("高行权价 (元)", value=60.0, min_value=1.0, step=0.1)
            prem_low = st.number_input("低行权价权利金 (元)", value=2.0, min_value=0.0, step=0.1)
            prem_mid = st.number_input("中间行权价权利金 (元)", value=1.0, min_value=0.0, step=0.1)
            prem_high = st.number_input("高行权价权利金 (元)", value=0.5, min_value=0.0, step=0.1)

    with c3:
        if strategy == "牛市看涨价差":
            st.info("**牛市看涨价差**\n\n- 买入低行权价看涨期权\n- 卖出高行权价看涨期权\n- 适合看涨但预期涨幅有限")
        elif strategy == "熊市看跌价差":
            st.info("**熊市看跌价差**\n\n- 买入高行权价看跌期权\n- 卖出低行权价看跌期权\n- 适合看跌但预期跌幅有限")
        elif strategy == "铁鹰价差":
            st.info("**铁鹰价差**\n\n- 买入两端期权\n- 卖出中间行权价期权\n- 适合中性区间波动")
        elif strategy == "蝶式价差":
            st.info("**蝶式价差**\n\n- 买入两端期权\n- 卖出中间期权(2张)\n- 适合预期价格稳定")

    # 分析
    if strategy == "牛市看涨价差":
        prices, long_call, short_call, total = calc_bull_call(spot, k_long, k_short, prem_long, prem_short, qty)
        net_debit = (prem_long - prem_short)
        breakeven = k_long + net_debit
        max_gain = (k_short - k_long - net_debit) * qty
        max_loss = net_debit * qty

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{breakeven:.2f}</div><div class='metric-label'>盈亏平衡点(元)</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{max_gain:.0f}</div><div class='metric-label'>最大收益(元)</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{max_loss:.0f}</div><div class='metric-label'>最大损失(元)</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{net_debit:.2f}</div><div class='metric-label'>净权利金(元/股)</div></div>", unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=prices, y=long_call, mode='lines', name='买入看涨收益', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=prices, y=short_call, mode='lines', name='卖出看涨收益', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=prices, y=total, mode='lines', name='总收益', line=dict(color='green', width=3)))
        fig.add_hline(y=0, line_dash='dash', line_color='gray')
        fig.add_vline(x=spot, line_dash='dash', line_color='orange')
        fig.update_layout(title='牛市看涨价差收益分析', xaxis_title='股价(元)', yaxis_title='收益(元)', hovermode='x unified', height=480)
        st.plotly_chart(fig, use_container_width=True)

    elif strategy == "熊市看跌价差":
        prices, long_put, short_put, total = calc_bear_put(spot, k_long, k_short, prem_long, prem_short, qty)
        net_debit = (prem_long - prem_short)
        breakeven = k_long - net_debit
        max_gain = (k_long - k_short - net_debit) * qty
        max_loss = net_debit * qty

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{breakeven:.2f}</div><div class='metric-label'>盈亏平衡点(元)</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{max_gain:.0f}</div><div class='metric-label'>最大收益(元)</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{max_loss:.0f}</div><div class='metric-label'>最大损失(元)</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{net_debit:.2f}</div><div class='metric-label'>净权利金(元/股)</div></div>", unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=prices, y=long_put, mode='lines', name='买入看跌收益', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=prices, y=short_put, mode='lines', name='卖出看跌收益', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=prices, y=total, mode='lines', name='总收益', line=dict(color='green', width=3)))
        fig.add_hline(y=0, line_dash='dash', line_color='gray')
        fig.add_vline(x=spot, line_dash='dash', line_color='orange')
        fig.update_layout(title='熊市看跌价差收益分析', xaxis_title='股价(元)', yaxis_title='收益(元)', hovermode='x unified', height=480)
        st.plotly_chart(fig, use_container_width=True)

    elif strategy == "铁鹰价差":
        prices, put_long, put_short, call_short, call_long, total = calc_iron_condor(spot, p_long, p_short, c_short, c_long, pL, pS, cS, cL, qty)
        net_credit = (pS + cS) - (pL + cL)
        width_put = (p_short - p_long)
        width_call = (c_long - c_short)
        max_loss = max(width_put, width_call) * qty - net_credit * qty
        max_gain = net_credit * qty

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{net_credit:.2f}</div><div class='metric-label'>净权利金(元/股)</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{max_gain:.0f}</div><div class='metric-label'>最大收益(元)</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{max_loss:.0f}</div><div class='metric-label'>最大损失(元)</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{p_short:.0f}-{c_short:.0f}</div><div class='metric-label'>理论盈利区间(元)</div></div>", unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=prices, y=put_long, mode='lines', name='买入看跌收益', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=prices, y=put_short, mode='lines', name='卖出看跌收益', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=prices, y=call_short, mode='lines', name='卖出看涨收益', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=prices, y=call_long, mode='lines', name='买入看涨收益', line=dict(color='purple')))
        fig.add_trace(go.Scatter(x=prices, y=total, mode='lines', name='总收益', line=dict(color='green', width=3)))
        fig.add_hline(y=0, line_dash='dash', line_color='gray')
        fig.add_vline(x=spot, line_dash='dash', line_color='orange')
        fig.update_layout(title='铁鹰价差收益分析', xaxis_title='股价(元)', yaxis_title='收益(元)', hovermode='x unified', height=500)
        st.plotly_chart(fig, use_container_width=True)

    elif strategy == "蝶式价差":
        prices, low_call, mid_call, high_call, total = calc_butterfly(spot, k_low, k_mid, k_high, prem_low, prem_mid, prem_high, qty)
        net_debit = (prem_low + prem_high) - 2 * prem_mid
        width = (k_mid - k_low)
        max_gain = (width - net_debit) * qty
        max_loss = net_debit * qty

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{k_mid:.2f}</div><div class='metric-label'>最佳价格(元)</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{max_gain:.0f}</div><div class='metric-label'>最大收益(元)</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{max_loss:.0f}</div><div class='metric-label'>最大损失(元)</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{net_debit:.2f}</div><div class='metric-label'>净权利金(元/股)</div></div>", unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=prices, y=low_call, mode='lines', name='买入低行权看涨', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=prices, y=mid_call, mode='lines', name='卖出中间行权看涨(×2)', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=prices, y=high_call, mode='lines', name='买入高行权看涨', line=dict(color='purple')))
        fig.add_trace(go.Scatter(x=prices, y=total, mode='lines', name='总收益', line=dict(color='green', width=3)))
        fig.add_hline(y=0, line_dash='dash', line_color='gray')
        fig.add_vline(x=spot, line_dash='dash', line_color='orange')
        fig.update_layout(title='蝶式价差收益分析', xaxis_title='股价(元)', yaxis_title='收益(元)', hovermode='x unified', height=480)
        st.plotly_chart(fig, use_container_width=True)

    elif strategy == "价差策略对比":
        st.markdown("### 💡 策略选择建议")
        st.markdown("**牛市看涨价差：**")
        st.markdown("- 看涨但预期涨幅有限")
        st.markdown("- 希望降低成本并限制风险")
        st.markdown("- 接受收益上限")

        st.markdown("**熊市看跌价差：**")
        st.markdown("- 看跌但预期跌幅有限")
        st.markdown("- 希望降低成本并限制风险")
        st.markdown("- 接受收益上限")

        st.markdown("**铁鹰价差：**")
        st.markdown("- 中性区间波动预期")
        st.markdown("- 追求稳定的权利金收入")
        st.markdown("- 接受区间外的有限损失")

        st.markdown("**蝶式价差：**")
        st.markdown("- 预期价格在特定价位附近稳定")
        st.markdown("- 追求该价位附近的最大收益")
        st.markdown("- 接受偏离价位时收益快速下降")

        st.markdown("### ⚠️ 风险管理建议")
        st.markdown("- 选择合理行权价间距，兼顾成本与风险")
        st.markdown("- 注意时间价值衰减对净头寸的影响")
        st.markdown("- 控制仓位，分批建立或调整")
        st.markdown("- 重大波动时优先减仓或滚动调整")
        st.markdown("- 关注交易成本、滑点对实际收益的影响")

if __name__ == "__main__":
    main()
