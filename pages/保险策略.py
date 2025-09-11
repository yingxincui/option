
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math

# 设置页面配置
st.set_page_config(
    page_title="期权保险策略",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .strategy-box {
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .risk-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .formula-box {
        background-color: #e8f4fd;
        border: 1px solid #bee5eb;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
    }
    .example-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .calculation-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

def calculate_protective_put_payoff(spot_price, strike_price, put_premium, stock_shares=100):
    """
    计算保护性看跌期权的收益
    """
    stock_prices = np.linspace(spot_price * 0.5, spot_price * 1.5, 100)
    
    # 股票收益
    stock_payoff = (stock_prices - spot_price) * stock_shares
    
    # 看跌期权收益
    put_payoff = np.maximum(strike_price - stock_prices, 0) * stock_shares - put_premium * stock_shares
    
    # 总收益
    total_payoff = stock_payoff + put_payoff
    
    return stock_prices, stock_payoff, put_payoff, total_payoff

def calculate_collar_payoff(spot_price, put_strike, call_strike, put_premium, call_premium, stock_shares=100):
    """
    计算领子策略的收益
    """
    stock_prices = np.linspace(spot_price * 0.5, spot_price * 1.5, 100)
    
    # 股票收益
    stock_payoff = (stock_prices - spot_price) * stock_shares
    
    # 看跌期权收益
    put_payoff = np.maximum(put_strike - stock_prices, 0) * stock_shares - put_premium * stock_shares
    
    # 看涨期权收益
    call_payoff = -np.maximum(stock_prices - call_strike, 0) * stock_shares + call_premium * stock_shares
    
    # 总收益
    total_payoff = stock_payoff + put_payoff + call_payoff
    
    return stock_prices, stock_payoff, put_payoff, call_payoff, total_payoff

def calculate_covered_call_payoff(spot_price, call_strike, call_premium, stock_shares=100):
    """
    计算备兑看涨期权的收益
    """
    stock_prices = np.linspace(spot_price * 0.5, spot_price * 1.5, 100)
    
    # 股票收益
    stock_payoff = (stock_prices - spot_price) * stock_shares
    
    # 看涨期权收益
    call_payoff = -np.maximum(stock_prices - call_strike, 0) * stock_shares + call_premium * stock_shares
    
    # 总收益
    total_payoff = stock_payoff + call_payoff
    
    return stock_prices, stock_payoff, call_payoff, total_payoff

def main():
    # 主标题
    st.markdown('<h1 class="main-header">🛡️ 期权保险策略详解</h1>', unsafe_allow_html=True)
    
    # 页面导航
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <a href="/" style="display: inline-block; padding: 10px 20px; margin: 5px; background: #1f77b4; color: white; text-decoration: none; border-radius: 5px;">🏠 返回首页</a>
        <a href="/期权基础知识" style="display: inline-block; padding: 10px 20px; margin: 5px; background: #28a745; color: white; text-decoration: none; border-radius: 5px;">📚 期权基础</a>
        <a href="/期权风险分析" style="display: inline-block; padding: 10px 20px; margin: 5px; background: #ffc107; color: black; text-decoration: none; border-radius: 5px;">📊 风险分析</a>
    </div>
    """, unsafe_allow_html=True)
    
    # 策略选择
    st.markdown('<h2 class="section-header">📋 策略选择</h2>', unsafe_allow_html=True)
    
    strategy_type = st.selectbox(
        "选择要分析的保险策略：",
        ["保护性看跌期权", "备兑看涨期权", "领子策略", "保险策略对比"]
    )
    
    # 参数设置
    st.markdown('<h2 class="section-header">⚙️ 参数设置</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        spot_price = st.number_input("当前股价 (元)", value=50.0, min_value=1.0, step=0.1)
        stock_shares = st.number_input("持有股数", value=100, min_value=1, step=1)
    
    with col2:
        if strategy_type in ["保护性看跌期权", "领子策略"]:
            put_strike = st.number_input("看跌期权行权价 (元)", value=45.0, min_value=1.0, step=0.1)
            put_premium = st.number_input("看跌期权权利金 (元)", value=2.0, min_value=0.1, step=0.1)
        
        if strategy_type in ["备兑看涨期权", "领子策略"]:
            call_strike = st.number_input("看涨期权行权价 (元)", value=55.0, min_value=1.0, step=0.1)
            call_premium = st.number_input("看涨期权权利金 (元)", value=1.5, min_value=0.1, step=0.1)
    
    with col3:
        if strategy_type == "保护性看跌期权":
            st.info("**保护性看跌期权**\n\n- 持有股票 + 买入看跌期权\n- 提供下跌保护\n- 限制上涨收益")
        elif strategy_type == "备兑看涨期权":
            st.info("**备兑看涨期权**\n\n- 持有股票 + 卖出看涨期权\n- 增加收入\n- 限制上涨收益")
        elif strategy_type == "领子策略":
            st.info("**领子策略**\n\n- 持有股票 + 买入看跌 + 卖出看涨\n- 双向保护\n- 限制收益和损失")
    
    # 策略分析
    if strategy_type == "保护性看跌期权":
        analyze_protective_put(spot_price, put_strike, put_premium, stock_shares)
    elif strategy_type == "备兑看涨期权":
        analyze_covered_call(spot_price, call_strike, call_premium, stock_shares)
    elif strategy_type == "领子策略":
        analyze_collar(spot_price, put_strike, call_strike, put_premium, call_premium, stock_shares)
    elif strategy_type == "保险策略对比":
        compare_insurance_strategies(spot_price, stock_shares)

def analyze_protective_put(spot_price, put_strike, put_premium, stock_shares):
    """分析保护性看跌期权策略"""
    
    st.markdown('<h2 class="section-header">🛡️ 保护性看跌期权策略分析</h2>', unsafe_allow_html=True)
    
    # 策略说明
    st.markdown("""
    <div class="strategy-box">
        <h3>📖 策略原理</h3>
        <p><strong>保护性看跌期权</strong>是投资者在持有股票的同时，买入相应数量的看跌期权，以保护股票投资免受价格下跌的风险。</p>
        <p><strong>适用场景：</strong>看好某只股票但担心短期下跌风险，希望获得下跌保护的同时保留上涨收益。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 计算收益
    stock_prices, stock_payoff, put_payoff, total_payoff = calculate_protective_put_payoff(
        spot_price, put_strike, put_premium, stock_shares
    )
    
    # 关键指标计算
    breakeven_price = spot_price + put_premium
    max_loss = (spot_price - put_strike) * stock_shares + put_premium * stock_shares
    max_gain = float('inf')  # 理论上无上限
    
    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{breakeven_price:.2f}</div>
            <div class="metric-label">盈亏平衡点 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{max_loss:.0f}</div>
            <div class="metric-label">最大损失 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">∞</div>
            <div class="metric-label">最大收益 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        protection_cost = put_premium * stock_shares
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{protection_cost:.0f}</div>
            <div class="metric-label">保险成本 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 收益图表
    fig = go.Figure()
    
    # 股票收益
    fig.add_trace(go.Scatter(
        x=stock_prices, y=stock_payoff,
        mode='lines',
        name='股票收益',
        line=dict(color='blue', width=2)
    ))
    
    # 看跌期权收益
    fig.add_trace(go.Scatter(
        x=stock_prices, y=put_payoff,
        mode='lines',
        name='看跌期权收益',
        line=dict(color='red', width=2)
    ))
    
    # 总收益
    fig.add_trace(go.Scatter(
        x=stock_prices, y=total_payoff,
        mode='lines',
        name='总收益',
        line=dict(color='green', width=3)
    ))
    
    # 零收益线
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # 当前股价线
    fig.add_vline(x=spot_price, line_dash="dash", line_color="orange", opacity=0.7)
    
    fig.update_layout(
        title="保护性看跌期权收益分析",
        xaxis_title="股价 (元)",
        yaxis_title="收益 (元)",
        hovermode='x unified',
        width=800,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 策略优缺点
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="strategy-box">
            <h3>✅ 优点</h3>
            <ul>
                <li>提供下跌保护，限制最大损失</li>
                <li>保留股票上涨的无限收益潜力</li>
                <li>适合长期看好但担心短期波动的投资者</li>
                <li>策略简单易懂，容易执行</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="risk-box">
            <h3>⚠️ 缺点</h3>
            <ul>
                <li>需要支付权利金，增加投资成本</li>
                <li>如果股价上涨，收益会被权利金成本稀释</li>
                <li>时间价值衰减会影响期权价值</li>
                <li>需要选择合适的行权价和到期时间</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # 实际案例
    st.markdown("""
    <div class="example-box">
        <h3>📝 实际案例</h3>
        <p><strong>案例：</strong>投资者持有100股某股票，当前价格50元，担心短期下跌风险。</p>
        <p><strong>操作：</strong>买入1张行权价45元的看跌期权，权利金2元。</p>
        <p><strong>结果分析：</strong></p>
        <ul>
            <li>如果股价跌至40元：股票损失1000元，看跌期权收益300元，总损失700元</li>
            <li>如果股价涨至60元：股票收益1000元，看跌期权损失200元，总收益800元</li>
            <li>盈亏平衡点：52元（50+2）</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def analyze_covered_call(spot_price, call_strike, call_premium, stock_shares):
    """分析备兑看涨期权策略"""
    
    st.markdown('<h2 class="section-header">📞 备兑看涨期权策略分析</h2>', unsafe_allow_html=True)
    
    # 策略说明
    st.markdown("""
    <div class="strategy-box">
        <h3>📖 策略原理</h3>
        <p><strong>备兑看涨期权</strong>是投资者在持有股票的同时，卖出相应数量的看涨期权，通过收取权利金来增加收入。</p>
        <p><strong>适用场景：</strong>对股票持中性或略微看涨态度，希望通过卖出看涨期权增加收入，同时愿意在股价上涨时以固定价格卖出股票。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 计算收益
    stock_prices, stock_payoff, call_payoff, total_payoff = calculate_covered_call_payoff(
        spot_price, call_strike, call_premium, stock_shares
    )
    
    # 关键指标计算
    breakeven_price = spot_price - call_premium
    max_gain = (call_strike - spot_price) * stock_shares + call_premium * stock_shares
    max_loss = spot_price * stock_shares - call_premium * stock_shares  # 如果股价跌至0
    
    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{breakeven_price:.2f}</div>
            <div class="metric-label">盈亏平衡点 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{max_gain:.0f}</div>
            <div class="metric-label">最大收益 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{max_loss:.0f}</div>
            <div class="metric-label">最大损失 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        income = call_premium * stock_shares
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{income:.0f}</div>
            <div class="metric-label">权利金收入 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 收益图表
    fig = go.Figure()
    
    # 股票收益
    fig.add_trace(go.Scatter(
        x=stock_prices, y=stock_payoff,
        mode='lines',
        name='股票收益',
        line=dict(color='blue', width=2)
    ))
    
    # 看涨期权收益
    fig.add_trace(go.Scatter(
        x=stock_prices, y=call_payoff,
        mode='lines',
        name='看涨期权收益',
        line=dict(color='red', width=2)
    ))
    
    # 总收益
    fig.add_trace(go.Scatter(
        x=stock_prices, y=total_payoff,
        mode='lines',
        name='总收益',
        line=dict(color='green', width=3)
    ))
    
    # 零收益线
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # 当前股价线
    fig.add_vline(x=spot_price, line_dash="dash", line_color="orange", opacity=0.7)
    
    fig.update_layout(
        title="备兑看涨期权收益分析",
        xaxis_title="股价 (元)",
        yaxis_title="收益 (元)",
        hovermode='x unified',
        width=800,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 策略优缺点
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="strategy-box">
            <h3>✅ 优点</h3>
            <ul>
                <li>通过卖出看涨期权获得权利金收入</li>
                <li>降低股票的持有成本</li>
                <li>适合对股票持中性或略微看涨的投资者</li>
                <li>策略相对保守，风险较低</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="risk-box">
            <h3>⚠️ 缺点</h3>
            <ul>
                <li>限制了股票的上涨收益潜力</li>
                <li>如果股价大幅上涨，会错失额外收益</li>
                <li>如果股价下跌，权利金收入只能部分抵消损失</li>
                <li>需要承担股票下跌的无限风险</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # 实际案例
    st.markdown("""
    <div class="example-box">
        <h3>📝 实际案例</h3>
        <p><strong>案例：</strong>投资者持有100股某股票，当前价格50元，认为股价短期内不会大幅上涨。</p>
        <p><strong>操作：</strong>卖出1张行权价55元的看涨期权，权利金1.5元。</p>
        <p><strong>结果分析：</strong></p>
        <ul>
            <li>如果股价涨至60元：股票收益1000元，看涨期权损失350元，总收益650元</li>
            <li>如果股价跌至40元：股票损失1000元，看涨期权收益150元，总损失850元</li>
            <li>盈亏平衡点：48.5元（50-1.5）</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def analyze_collar(spot_price, put_strike, call_strike, put_premium, call_premium, stock_shares):
    """分析领子策略"""
    
    st.markdown('<h2 class="section-header">👔 领子策略分析</h2>', unsafe_allow_html=True)
    
    # 策略说明
    st.markdown("""
    <div class="strategy-box">
        <h3>📖 策略原理</h3>
        <p><strong>领子策略</strong>是投资者在持有股票的同时，买入看跌期权提供下跌保护，卖出看涨期权获得权利金收入，形成双向保护。</p>
        <p><strong>适用场景：</strong>对股票持中性态度，希望获得双向保护，同时愿意限制收益和损失的范围。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 计算收益
    stock_prices, stock_payoff, put_payoff, call_payoff, total_payoff = calculate_collar_payoff(
        spot_price, put_strike, call_strike, put_premium, call_premium, stock_shares
    )
    
    # 关键指标计算
    net_premium = call_premium - put_premium
    breakeven_price = spot_price - net_premium
    max_gain = (call_strike - spot_price) * stock_shares + net_premium * stock_shares
    max_loss = (spot_price - put_strike) * stock_shares - net_premium * stock_shares
    
    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{breakeven_price:.2f}</div>
            <div class="metric-label">盈亏平衡点 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{max_gain:.0f}</div>
            <div class="metric-label">最大收益 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{max_loss:.0f}</div>
            <div class="metric-label">最大损失 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        net_income = net_premium * stock_shares
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{net_income:.0f}</div>
            <div class="metric-label">净权利金收入 (元)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 收益图表
    fig = go.Figure()
    
    # 股票收益
    fig.add_trace(go.Scatter(
        x=stock_prices, y=stock_payoff,
        mode='lines',
        name='股票收益',
        line=dict(color='blue', width=2)
    ))
    
    # 看跌期权收益
    fig.add_trace(go.Scatter(
        x=stock_prices, y=put_payoff,
        mode='lines',
        name='看跌期权收益',
        line=dict(color='red', width=2)
    ))
    
    # 看涨期权收益
    fig.add_trace(go.Scatter(
        x=stock_prices, y=call_payoff,
        mode='lines',
        name='看涨期权收益',
        line=dict(color='orange', width=2)
    ))
    
    # 总收益
    fig.add_trace(go.Scatter(
        x=stock_prices, y=total_payoff,
        mode='lines',
        name='总收益',
        line=dict(color='green', width=3)
    ))
    
    # 零收益线
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # 当前股价线
    fig.add_vline(x=spot_price, line_dash="dash", line_color="orange", opacity=0.7)
    
    fig.update_layout(
        title="领子策略收益分析",
        xaxis_title="股价 (元)",
        yaxis_title="收益 (元)",
        hovermode='x unified',
        width=800,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 策略优缺点
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="strategy-box">
            <h3>✅ 优点</h3>
            <ul>
                <li>提供双向保护，限制最大损失和收益</li>
                <li>通过卖出看涨期权获得权利金收入</li>
                <li>适合对股票持中性态度的投资者</li>
                <li>风险相对较低，收益相对稳定</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="risk-box">
            <h3>⚠️ 缺点</h3>
            <ul>
                <li>限制了股票的上涨收益潜力</li>
                <li>如果股价大幅上涨，会错失额外收益</li>
                <li>策略相对复杂，需要管理两个期权</li>
                <li>需要选择合适的行权价组合</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # 实际案例
    st.markdown("""
    <div class="example-box">
        <h3>📝 实际案例</h3>
        <p><strong>案例：</strong>投资者持有100股某股票，当前价格50元，希望获得双向保护。</p>
        <p><strong>操作：</strong>买入1张行权价45元的看跌期权（权利金2元），卖出1张行权价55元的看涨期权（权利金1.5元）。</p>
        <p><strong>结果分析：</strong></p>
        <ul>
            <li>如果股价涨至60元：股票收益1000元，看跌期权损失200元，看涨期权损失350元，总收益450元</li>
            <li>如果股价跌至40元：股票损失1000元，看跌期权收益300元，看涨期权收益150元，总损失550元</li>
            <li>盈亏平衡点：49.5元（50-0.5）</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def compare_insurance_strategies(spot_price, stock_shares):
    """对比不同保险策略"""
    
    st.markdown('<h2 class="section-header">📊 保险策略对比分析</h2>', unsafe_allow_html=True)
    
    # 策略对比表格
    comparison_data = {
        '策略名称': ['保护性看跌期权', '备兑看涨期权', '领子策略'],
        '最大收益': ['无限', '有限', '有限'],
        '最大损失': ['有限', '无限', '有限'],
        '权利金成本': ['支付', '收取', '净收取'],
        '适用场景': ['看涨但担心下跌', '中性或略微看涨', '中性态度'],
        '风险等级': ['中等', '低', '低'],
        '收益潜力': ['高', '中等', '低']
    }
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True)
    
    # 策略选择建议
    st.markdown("### 💡 策略选择建议")
    
    st.markdown("**选择保护性看跌期权的情况：**")
    st.markdown("- 长期看好某只股票，但担心短期下跌风险")
    st.markdown("- 愿意支付权利金成本来获得下跌保护")
    st.markdown("- 希望保留股票的无限上涨收益潜力")
    
    st.markdown("**选择备兑看涨期权的情况：**")
    st.markdown("- 对股票持中性或略微看涨态度")
    st.markdown("- 希望通过卖出看涨期权增加收入")
    st.markdown("- 愿意在股价上涨时以固定价格卖出股票")
    
    st.markdown("**选择领子策略的情况：**")
    st.markdown("- 对股票持中性态度，希望获得双向保护")
    st.markdown("- 愿意限制收益和损失的范围")
    st.markdown("- 希望通过期权组合降低整体风险")
    
    # 风险管理建议
    st.markdown("### ⚠️ 风险管理建议")
    st.markdown("- **选择合适的行权价：** 根据对股价的预期选择合适的行权价")
    st.markdown("- **注意时间价值：** 期权的时间价值会随着到期日的临近而衰减")
    st.markdown("- **控制仓位大小：** 不要将所有资金都用于期权策略")
    st.markdown("- **及时调整策略：** 根据市场变化及时调整或平仓")
    st.markdown("- **了解交易成本：** 考虑手续费、滑点等交易成本")

if __name__ == "__main__":
    main()