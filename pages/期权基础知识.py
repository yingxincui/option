import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# 设置页面配置
st.set_page_config(
    page_title="期权基础知识",
    page_icon="📚",
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
    .concept-box {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    }
    .formula-box {
        background-color: #e8f4fd;
        border: 1px solid #bee5eb;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def create_payoff_diagram():
    """创建期权盈亏图"""
    # 创建价格范围
    S = np.linspace(0, 200, 100)
    K = 100  # 行权价
    
    # 看涨期权多头
    call_long = np.maximum(S - K, 0) - 5  # 假设期权费为5
    
    # 看涨期权空头
    call_short = -(np.maximum(S - K, 0)) + 5
    
    # 看跌期权多头
    put_long = np.maximum(K - S, 0) - 5
    
    # 看跌期权空头
    put_short = -(np.maximum(K - S, 0)) + 5
    
    fig = go.Figure()
    
    # 添加看涨期权多头
    fig.add_trace(go.Scatter(
        x=S, y=call_long,
        mode='lines',
        name='看涨期权多头',
        line=dict(color='green', width=3)
    ))
    
    # 添加看涨期权空头
    fig.add_trace(go.Scatter(
        x=S, y=call_short,
        mode='lines',
        name='看涨期权空头',
        line=dict(color='red', width=3)
    ))
    
    # 添加看跌期权多头
    fig.add_trace(go.Scatter(
        x=S, y=put_long,
        mode='lines',
        name='看跌期权多头',
        line=dict(color='blue', width=3)
    ))
    
    # 添加看跌期权空头
    fig.add_trace(go.Scatter(
        x=S, y=put_short,
        mode='lines',
        name='看跌期权空头',
        line=dict(color='orange', width=3)
    ))
    
    # 添加零线
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.add_vline(x=K, line_dash="dash", line_color="gray", annotation_text="行权价")
    
    fig.update_layout(
        title="期权盈亏图（行权价=100，期权费=5）",
        xaxis_title="标的资产价格",
        yaxis_title="盈亏",
        width=800,
        height=500
    )
    
    return fig

def create_greeks_diagram():
    """创建希腊字母示意图"""
    # Delta
    S = np.linspace(80, 120, 50)
    K = 100
    call_delta = np.where(S > K, 1, 0)  # 简化版Delta
    put_delta = np.where(S < K, -1, 0)  # 简化版Delta
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=S, y=call_delta,
        mode='lines',
        name='看涨期权Delta',
        line=dict(color='green', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=S, y=put_delta,
        mode='lines',
        name='看跌期权Delta',
        line=dict(color='red', width=3)
    ))
    
    fig.update_layout(
        title="Delta示意图",
        xaxis_title="标的资产价格",
        yaxis_title="Delta值",
        width=600,
        height=400
    )
    
    return fig

def main():
    st.markdown('<h1 class="main-header">📚 期权基础知识讲解</h1>', unsafe_allow_html=True)
    
    # 目录
    st.markdown("""
    ## 📋 目录
    1. [期权基本概念](#1-期权基本概念)
    2. [期权类型与分类](#2-期权类型与分类)
    3. [期权价格构成](#3-期权价格构成)
    4. [期权交易策略](#4-期权交易策略)
    5. [希腊字母(Greeks)](#5-希腊字母)
    6. [期权风险与注意事项](#6-期权风险与注意事项)
    7. [实战案例分析](#7-实战案例分析)
    """)
    
    # 1. 期权基本概念
    st.markdown('<h2 class="section-header" id="1-期权基本概念">1. 期权基本概念</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 什么是期权？
    """)
    
    st.markdown("""
    <div class="concept-box">
    <strong>期权(Option)</strong>是一种金融衍生品，它给予持有者在特定时间内以特定价格买入或卖出标的资产的权利，但不是义务。
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **期权的核心要素：**
        - **标的资产**：期权合约所对应的资产（如股票、ETF、指数等）
        - **行权价格**：期权合约规定的买卖价格
        - **到期时间**：期权合约的有效期限
        - **期权费**：购买期权需要支付的成本
        - **合约单位**：每份期权合约对应的标的资产数量
        """)
    
    with col2:
        st.markdown("""
        **期权的基本特征：**
        - **权利性**：期权是权利，不是义务
        - **时间性**：期权有明确的到期时间
        - **杠杆性**：用较少的资金控制更多的资产
        - **风险有限**：买方最大损失为期权费
        - **收益无限**：理论上收益没有上限
        """)
    
    # 2. 期权类型与分类
    st.markdown('<h2 class="section-header" id="2-期权类型与分类">2. 期权类型与分类</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 按权利类型分类
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📈 看涨期权 (Call Option)**
        - 给予持有者以行权价**买入**标的资产的权利
        - 当标的资产价格上涨时获利
        - 适合看多市场的投资者
        """)
    
    with col2:
        st.markdown("""
        **📉 看跌期权 (Put Option)**
        - 给予持有者以行权价**卖出**标的资产的权利
        - 当标的资产价格下跌时获利
        - 适合看空市场的投资者
        """)
    
    st.markdown("""
    ### 按行权时间分类
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **⏰ 美式期权 (American Option)**
        - 在到期日前的任何时间都可以行权
        - 灵活性更高，但价格通常更高
        - 中国A股期权多为美式期权
        """)
    
    with col2:
        st.markdown("""
        **📅 欧式期权 (European Option)**
        - 只能在到期日当天行权
        - 价格相对较低
        - 主要用于指数期权
        """)
    
    st.markdown("""
    ### 按行权价格分类
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **💰 实值期权 (In-the-Money)**
        - 看涨期权：标的价格 > 行权价
        - 看跌期权：标的价格 < 行权价
        - 具有内在价值
        """)
    
    with col2:
        st.markdown("""
        **⚖️ 平值期权 (At-the-Money)**
        - 标的价格 = 行权价
        - 内在价值为零
        - 只有时间价值
        """)
    
    with col3:
        st.markdown("""
        **💸 虚值期权 (Out-of-the-Money)**
        - 看涨期权：标的价格 < 行权价
        - 看跌期权：标的价格 > 行权价
        - 内在价值为零
        """)
    
    # 3. 期权价格构成
    st.markdown('<h2 class="section-header" id="3-期权价格构成">3. 期权价格构成</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 期权价格 = 内在价值 + 时间价值
    """)
    
    st.markdown("""
    <div class="formula-box">
    <strong>期权价格 = 内在价值 + 时间价值</strong><br><br>
    
    <strong>内在价值：</strong><br>
    - 看涨期权内在价值 = max(标的价格 - 行权价, 0)<br>
    - 看跌期权内在价值 = max(行权价 - 标的价格, 0)<br><br>
    
    <strong>时间价值：</strong><br>
    - 期权价格 - 内在价值<br>
    - 反映期权到期前标的资产价格变动的可能性<br>
    - 随着到期时间临近而衰减
    </div>
    """, unsafe_allow_html=True)
    
    # 影响期权价格的因素
    st.markdown("""
    ### 影响期权价格的主要因素
    """)
    
    factors_data = {
        '因素': ['标的资产价格', '行权价格', '到期时间', '波动率', '无风险利率', '股息'],
        '看涨期权影响': ['正相关', '负相关', '正相关', '正相关', '正相关', '负相关'],
        '看跌期权影响': ['负相关', '正相关', '正相关', '正相关', '负相关', '正相关'],
        '说明': [
            '价格越高，看涨期权价值越高',
            '行权价越高，看涨期权价值越低',
            '时间越长，期权价值越高',
            '波动率越高，期权价值越高',
            '利率越高，看涨期权价值越高',
            '股息越高，看涨期权价值越低'
        ]
    }
    
    factors_df = pd.DataFrame(factors_data)
    st.dataframe(factors_df, use_container_width=True)
    
    # 4. 期权交易策略
    st.markdown('<h2 class="section-header" id="4-期权交易策略">4. 期权交易策略</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 基本交易策略
    """)
    
    strategies = [
        {
            '策略名称': '买入看涨期权',
            '适用场景': '强烈看多',
            '最大损失': '期权费',
            '最大收益': '无限',
            '盈亏平衡点': '行权价 + 期权费',
            '风险等级': '低'
        },
        {
            '策略名称': '买入看跌期权',
            '适用场景': '强烈看空',
            '最大损失': '期权费',
            '最大收益': '行权价 - 期权费',
            '盈亏平衡点': '行权价 - 期权费',
            '风险等级': '低'
        },
        {
            '策略名称': '卖出看涨期权',
            '适用场景': '看平或看跌',
            '最大损失': '无限',
            '最大收益': '期权费',
            '盈亏平衡点': '行权价 + 期权费',
            '风险等级': '高'
        },
        {
            '策略名称': '卖出看跌期权',
            '适用场景': '看平或看涨',
            '最大损失': '行权价 - 期权费',
            '最大收益': '期权费',
            '盈亏平衡点': '行权价 - 期权费',
            '风险等级': '中'
        }
    ]
    
    strategies_df = pd.DataFrame(strategies)
    st.dataframe(strategies_df, use_container_width=True)
    
    # 期权盈亏图
    st.markdown("""
    ### 期权盈亏图
    """)
    st.plotly_chart(create_payoff_diagram(), use_container_width=True)
    
    # 5. 希腊字母
    st.markdown('<h2 class="section-header" id="5-希腊字母">5. 希腊字母(Greeks)</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    希腊字母是衡量期权价格对各个风险因素敏感度的重要指标。
    """)
    
    greeks_data = {
        '希腊字母': ['Delta (Δ)', 'Gamma (Γ)', 'Theta (Θ)', 'Vega (ν)', 'Rho (ρ)'],
        '含义': [
            '期权价格对标的资产价格的敏感度',
            'Delta对标的资产价格的敏感度',
            '期权价格对时间流逝的敏感度',
            '期权价格对波动率的敏感度',
            '期权价格对利率的敏感度'
        ],
        '看涨期权': ['0到1', '正值', '负值', '正值', '正值'],
        '看跌期权': ['-1到0', '正值', '负值', '正值', '负值'],
        '重要性': ['高', '中', '高', '高', '低']
    }
    
    greeks_df = pd.DataFrame(greeks_data)
    st.dataframe(greeks_df, use_container_width=True)
    
    # Delta示意图
    st.plotly_chart(create_greeks_diagram(), use_container_width=True)
    
    # 6. 期权风险与注意事项
    st.markdown('<h2 class="section-header" id="6-期权风险与注意事项">6. 期权风险与注意事项</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 主要风险类型
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **⚠️ 买方风险**
        - 时间价值衰减风险
        - 方向判断错误风险
        - 流动性风险
        - 最大损失：期权费
        """)
    
    with col2:
        st.markdown("""
        **🚨 卖方风险**
        - 无限损失风险（看涨期权卖方）
        - 保证金风险
        - 被行权风险
        - 流动性风险
        """)
    
    st.markdown("""
    <div class="warning-box">
    <strong>⚠️ 重要提醒：</strong><br>
    1. 期权交易风险较高，新手建议先学习再实践<br>
    2. 卖方风险远大于买方，需要充足的资金和风险承受能力<br>
    3. 期权价格受多种因素影响，需要综合考虑<br>
    4. 建议设置止损，控制风险
    </div>
    """, unsafe_allow_html=True)
    
    # 7. 实战案例分析
    st.markdown('<h2 class="section-header" id="7-实战案例分析">7. 实战案例分析</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 案例1：买入看涨期权
    """)
    
    st.markdown("""
    **背景：** 某投资者看好沪深300ETF，当前价格3.5元，认为未来1个月可能涨到3.8元
    
    **操作：** 买入1个月后到期、行权价3.6元的看涨期权，期权费0.1元
    
    **分析：**
    - 盈亏平衡点：3.6 + 0.1 = 3.7元
    - 如果ETF涨到3.8元：收益 = (3.8 - 3.6) - 0.1 = 0.1元
    - 如果ETF跌到3.4元：损失 = 0.1元（期权费）
    - 最大损失：0.1元
    - 最大收益：理论上无限
    """)
    
    st.markdown("""
    <div class="success-box">
    <strong>💡 策略优势：</strong><br>
    - 风险有限，收益无限<br>
    - 适合强烈看多的投资者<br>
    - 资金占用少，杠杆效应明显
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 案例2：卖出看跌期权
    """)
    
    st.markdown("""
    **背景：** 某投资者认为沪深300ETF不会跌破3.2元，愿意在3.2元买入
    
    **操作：** 卖出1个月后到期、行权价3.2元的看跌期权，收取期权费0.05元
    
    **分析：**
    - 如果ETF保持在3.2元以上：收益 = 0.05元（期权费）
    - 如果ETF跌到3.1元：损失 = (3.2 - 3.1) - 0.05 = 0.05元
    - 如果ETF跌到3.0元：损失 = (3.2 - 3.0) - 0.05 = 0.15元
    - 最大收益：0.05元
    - 最大损失：3.2 - 0.05 = 3.15元
    """)
    
    st.markdown("""
    <div class="warning-box">
    <strong>⚠️ 风险提示：</strong><br>
    - 卖方需要承担较大风险<br>
    - 需要充足的保证金<br>
    - 适合有经验的投资者
    </div>
    """, unsafe_allow_html=True)
    
    # 总结
    st.markdown('<h2 class="section-header">📝 总结</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="concept-box">
    <strong>期权交易要点总结：</strong><br><br>
    
    1. <strong>理解基本概念：</strong>期权是权利不是义务，有明确的时间限制<br>
    2. <strong>掌握价格构成：</strong>内在价值 + 时间价值，受多种因素影响<br>
    3. <strong>选择合适策略：</strong>根据市场判断和风险承受能力选择策略<br>
    4. <strong>关注希腊字母：</strong>了解期权价格对各个因素的敏感度<br>
    5. <strong>控制风险：</strong>设置止损，不要过度杠杆<br>
    6. <strong>持续学习：</strong>期权交易需要不断学习和实践
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ---
    <div style="text-align: center; color: #666; margin-top: 2rem;">
    <p>📚 期权基础知识讲解完毕 | 投资有风险，入市需谨慎</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
