import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import akshare as ak
from utils.etf_analysis_shared import load_etf_data as shared_load_etf_data

# 设置页面配置
st.set_page_config(
    page_title="海龟交易法则",
    page_icon="🐢",
    layout="wide"
)

# ETF配置（与ETF技术分析页面保持一致）
ETF_CONFIG = {
    "科创50ETF (588000)": "588000",
    "中证500ETF (510500)": "510500", 
    "上证50ETF (510050)": "510050",
    "创业板ETF (159915)": "159915",
    "沪深300ETF (510300)": "510300",
    "深证100ETF (159901)": "159901"
}

# 自定义CSS样式
st.markdown("""
<style>
    .turtle-header {
        background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 50%, #81C784 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(46, 125, 50, 0.3);
    }
    
    .rule-card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .rule-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(76, 175, 80, 0.2);
    }
    
    .strategy-box {
        background: linear-gradient(135deg, #e8f5e8, #f1f8e9);
        padding: 2rem;
        border-radius: 1rem;
        border: 2px solid #4CAF50;
        margin: 1.5rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.8rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-top: 3px solid #4CAF50;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: 1px solid #ffc107;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # 缓存1小时
def load_data(symbol, data_type="etf", period="daily", days=250):
    """加载数据，仅支持ETF"""
    try:
        # 使用共享的ETF数据加载函数
        df = shared_load_etf_data(symbol, period, days)
        if df is not None and not df.empty:
            # 统一列名为英文
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open', 
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            })
            df['date'] = pd.to_datetime(df['date'])
            return df.sort_values('date').reset_index(drop=True)
        return None
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        return None

def calculate_atr(high, low, close, period=20):
    """计算平均真实波幅(ATR)"""
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = true_range.rolling(window=period).mean()
    
    return atr

def calculate_donchian_channels(high, low, period=20):
    """计算唐奇安通道"""
    upper_channel = high.rolling(window=period).max()
    lower_channel = low.rolling(window=period).min()
    
    return upper_channel, lower_channel

def turtle_strategy_signals(data, entry_period=20, exit_period=10, atr_period=20):
    """海龟交易信号计算"""
    # 计算ATR
    data['ATR'] = calculate_atr(data['high'], data['low'], data['close'], atr_period)
    
    # 计算唐奇安通道
    data['entry_high'], data['entry_low'] = calculate_donchian_channels(
        data['high'], data['low'], entry_period
    )
    data['exit_high'], data['exit_low'] = calculate_donchian_channels(
        data['high'], data['low'], exit_period
    )
    
    # 生成交易信号
    data['long_entry'] = data['close'] > data['entry_high'].shift(1)
    data['long_exit'] = data['close'] < data['exit_low'].shift(1)
    data['short_entry'] = data['close'] < data['entry_low'].shift(1)
    data['short_exit'] = data['close'] > data['exit_high'].shift(1)
    
    return data

def main():
    # 页面标题
    st.markdown("""
    <div class="turtle-header">
        <h1 style="font-size: 3rem; margin-bottom: 1rem;">🐢 海龟交易法则</h1>
        <p style="font-size: 1.3rem; opacity: 0.9;">
            经典趋势跟踪策略 | 突破系统交易法则 | 风险管理核心
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 导航选项卡
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 法则介绍", "📊 策略回测", "⚙️ 参数设置", 
        "📈 实时信号", "🎯 风险管理"
    ])
    
    with tab1:
        show_turtle_rules()
    
    with tab2:
        show_strategy_backtest()
    
    with tab3:
        show_parameter_settings()
    
    with tab4:
        show_real_time_signals()
    
    with tab5:
        show_risk_management()

def show_turtle_rules():
    """显示海龟交易法则介绍"""
    st.markdown("## 🎯 海龟交易法则核心理念")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="rule-card">
            <h3>🔍 市场选择</h3>
            <p><strong>流动性原则</strong>：选择流动性强、波动适中的市场</p>
            <p><strong>多元化</strong>：分散投资于不同市场和品种</p>
            <p><strong>趋势性</strong>：选择具有明显趋势特征的标的</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="rule-card">
            <h3>📈 入市规则</h3>
            <p><strong>突破入市</strong>：价格突破20日最高价做多</p>
            <p><strong>反向突破</strong>：价格跌破20日最低价做空</p>
            <p><strong>过滤机制</strong>：避免假突破的过滤条件</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="rule-card">
            <h3>🛑 止损规则</h3>
            <p><strong>ATR止损</strong>：以2倍ATR作为止损距离</p>
            <p><strong>及时止损</strong>：严格执行止损，不抱侥幸心理</p>
            <p><strong>移动止损</strong>：盈利后逐步调整止损位</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="rule-card">
            <h3>🎯 头寸规模</h3>
            <p><strong>风险单位</strong>：每次交易风险不超过账户的1%</p>
            <p><strong>ATR计算</strong>：根据ATR计算合理的头寸大小</p>
            <p><strong>分批建仓</strong>：分多次建立完整头寸</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="rule-card">
            <h3>🔄 加仓规则</h3>
            <p><strong>趋势确认</strong>：价格继续朝有利方向突破时加仓</p>
            <p><strong>ATR间隔</strong>：每隔0.5倍ATR加仓一次</p>
            <p><strong>最大头寸</strong>：单个标的最多4个单位</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="rule-card">
            <h3>📉 出市规则</h3>
            <p><strong>趋势反转</strong>：价格跌破10日最低价平多仓</p>
            <p><strong>止损出场</strong>：触及止损位立即出场</p>
            <p><strong>时间止损</strong>：长期横盘时主动退出</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 策略优势
    st.markdown("## ✨ 海龟交易法则的优势")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #4CAF50;">🎯</h3>
            <h4>系统性强</h4>
            <p>完整的交易体系，规则明确具体</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #4CAF50;">📊</h3>
            <h4>趋势跟踪</h4>
            <p>能够捕捉大部分主要趋势行情</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #4CAF50;">🛡️</h3>
            <h4>风控严格</h4>
            <p>严格的风险管理和头寸控制</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #4CAF50;">⚙️</h3>
            <h4>易于执行</h4>
            <p>规则简单明了，容易程序化</p>
        </div>
        """, unsafe_allow_html=True)

def show_strategy_backtest():
    """显示策略回测"""
    st.markdown("## 📊 海龟交易策略回测分析")
    
    # 仅使用ETF选项
    all_symbols = ETF_CONFIG.copy()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_symbol = st.selectbox("选择回测标的", list(all_symbols.keys()))
    with col2:
        period = st.selectbox("数据周期", ["daily", "weekly"], index=0)
    with col3:
        days = st.slider("历史数据天数", 100, 500, 250, 10)
    
    if st.button("开始回测", type="primary"):
        try:
            symbol_code = all_symbols[selected_symbol]
            with st.spinner("正在获取数据..."):
                # 只加载ETF数据
                data = load_data(symbol_code, "etf", period, days)
            
            if data is not None and len(data) > 50:
                # 计算海龟策略信号
                data = turtle_strategy_signals(data)
                
                # 显示回测结果
                show_backtest_results(data, selected_symbol)
                
            else:
                st.error("数据获取失败或数据量不足，请检查网络连接或更换时间范围")
                
        except Exception as e:
            st.error(f"回测过程中出现错误: {str(e)}")

def show_backtest_results(data, symbol_name):
    """显示回测结果"""
    # 绘制价格图表和信号
    fig = go.Figure()
    
    # 添加价格线
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['close'],
        mode='lines',
        name='收盘价',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # 添加唐奇安通道
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['entry_high'],
        mode='lines',
        name='入市通道上轨',
        line=dict(color='#ff7f0e', width=1, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['entry_low'],
        mode='lines',
        name='入市通道下轨',
        line=dict(color='#ff7f0e', width=1, dash='dash')
    ))
    
    # 添加交易信号
    long_entries = data[data['long_entry']]
    if len(long_entries) > 0:
        fig.add_trace(go.Scatter(
            x=long_entries['date'],
            y=long_entries['close'],
            mode='markers',
            name='做多信号',
            marker=dict(color='red', size=8, symbol='triangle-up')
        ))
    
    short_entries = data[data['short_entry']]
    if len(short_entries) > 0:
        fig.add_trace(go.Scatter(
            x=short_entries['date'],
            y=short_entries['close'],
            mode='markers',
            name='做空信号',
            marker=dict(color='green', size=8, symbol='triangle-down')
        ))
    
    fig.update_layout(
        title=f"{symbol_name} - 海龟交易策略信号图",
        xaxis_title="日期",
        yaxis_title="价格",
        height=600,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 计算策略统计
    total_signals = len(data[data['long_entry'] | data['short_entry']])
    long_signals = len(data[data['long_entry']])
    short_signals = len(data[data['short_entry']])
    avg_atr = data['ATR'].mean()
    
    # 显示统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总信号数", total_signals)
    with col2:
        st.metric("做多信号", long_signals)
    with col3:
        st.metric("做空信号", short_signals)
    with col4:
        st.metric("平均ATR", f"{avg_atr:.2f}")
    
    # 显示最近信号详情
    st.markdown("### 📊 最近5个信号")
    signal_data = data[data['long_entry'] | data['short_entry']].tail(5)
    if not signal_data.empty:
        signal_df = signal_data[['date', 'close', 'long_entry', 'short_entry', 'ATR']].copy()
        signal_df['信号类型'] = signal_df.apply(
            lambda row: '🔴 做多' if row['long_entry'] else '🟢 做空', axis=1
        )
        signal_df = signal_df.rename(columns={
            'date': '日期',
            'close': '价格',
            'ATR': 'ATR值'
        })
        st.dataframe(signal_df[['日期', '价格', '信号类型', 'ATR值']], use_container_width=True)
    else:
        st.info("近期没有交易信号")

def show_parameter_settings():
    """显示参数设置"""
    st.markdown("## ⚙️ 海龟交易参数设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="strategy-box">
            <h3>📈 入市参数</h3>
        </div>
        """, unsafe_allow_html=True)
        
        entry_period = st.slider("入市突破周期", 10, 50, 20, help="价格突破N日最高/最低价时入市")
        exit_period = st.slider("出市突破周期", 5, 30, 10, help="价格突破N日最低/最高价时出市")
        atr_period = st.slider("ATR计算周期", 10, 50, 20, help="计算平均真实波幅的周期")
        
        st.markdown("""
        <div class="strategy-box">
            <h3>🎯 风险参数</h3>
        </div>
        """, unsafe_allow_html=True)
        
        risk_per_trade = st.slider("单笔风险百分比", 0.5, 5.0, 1.0, 0.1, help="每笔交易的风险占总资金的百分比")
        max_units = st.slider("最大头寸单位", 1, 8, 4, help="单个标的最大持仓单位数")
        atr_stop_multiple = st.slider("ATR止损倍数", 1.0, 4.0, 2.0, 0.1, help="止损距离为N倍ATR")
    
    with col2:
        st.markdown("""
        <div class="strategy-box">
            <h3>📊 加仓参数</h3>
        </div>
        """, unsafe_allow_html=True)
        
        add_unit_atr = st.slider("加仓ATR间隔", 0.25, 1.0, 0.5, 0.05, help="每隔N倍ATR加仓一次")
        enable_pyramid = st.checkbox("启用金字塔加仓", True, help="是否允许分批加仓")
        
        st.markdown("""
        <div class="strategy-box">
            <h3>🔧 其他参数</h3>
        </div>
        """, unsafe_allow_html=True)
        
        enable_filter = st.checkbox("启用突破过滤", False, help="避免假突破的过滤机制")
        min_volatility = st.slider("最小波动率要求", 0.0, 5.0, 1.0, 0.1, help="标的最小历史波动率要求")
    
    # 参数说明
    st.markdown("## 📝 参数说明")
    
    st.markdown("""
    <div class="warning-box">
        <h4>⚠️ 重要提醒</h4>
        <p>• <strong>入市周期</strong>：较长周期能减少假突破，但可能错过快速行情</p>
        <p>• <strong>风险控制</strong>：单笔风险建议不超过2%，严格控制总体风险敞口</p>
        <p>• <strong>ATR倍数</strong>：止损倍数过小容易被震出，过大则风险增加</p>
        <p>• <strong>加仓策略</strong>：只在盈利的头寸上加仓，亏损头寸严禁加仓</p>
    </div>
    """, unsafe_allow_html=True)

def show_real_time_signals():
    """显示实时信号"""
    st.markdown("## 📈 实时海龟交易信号")
    
    # 仅使用ETF标的
    all_symbols = ETF_CONFIG.copy()
    
    if st.button("刷新信号", type="primary"):
        signal_data = []
        
        with st.spinner("正在获取实时数据..."):
            for name, code in all_symbols.items():
                try:
                    # 加载ETF数据
                    data = load_data(code, "etf", "daily", 50)
                    
                    if data is not None and len(data) > 30:
                        # 计算指标
                        data = turtle_strategy_signals(data)
                        latest = data.iloc[-1]
                        
                        # 判断信号
                        signal = "无信号"
                        if latest['long_entry']:
                            signal = "🔴 做多信号"
                        elif latest['short_entry']:
                            signal = "🟢 做空信号"
                        elif latest['long_exit']:
                            signal = "🟡 多头出场"
                        elif latest['short_exit']:
                            signal = "🟡 空头出场"
                        
                        signal_data.append({
                            "标的": name,
                            "当前价格": f"{latest['close']:.2f}",
                            "20日高点": f"{latest['entry_high']:.2f}",
                            "20日低点": f"{latest['entry_low']:.2f}",
                            "ATR": f"{latest['ATR']:.2f}",
                            "信号": signal
                        })
                        
                except Exception as e:
                    st.warning(f"{name} 数据获取失败: {str(e)}")
        
        if signal_data:
            # 显示ETF信号
            df = pd.DataFrame(signal_data)
            st.markdown("### 🎯 ETF信号")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("未能获取任何有效数据")
    
    # 信号说明
    st.markdown("""
    ### 📋 信号说明
    - 🔴 **做多信号**：价格突破20日最高价，建议建立多头头寸
    - 🟢 **做空信号**：价格跌破20日最低价，建议建立空头头寸  
    - 🟡 **出场信号**：价格触及出场条件，建议平仓
    - **无信号**：当前无明确交易信号，保持观望
    """)

def get_risk_advice(signal, risk_level):
    """根据信号和风险等级提供建议"""
    if "做多" in signal:
        if risk_level == "高":
            return "谨慎做多，降低头寸"
        elif risk_level == "中":
            return "可适度做多"
        else:
            return "可做多，注意止损"
    elif "做空" in signal:
        return "观望或考虑期权策略"
    elif "出场" in signal:
        return "建议平仓"
    else:
        if risk_level == "高":
            return "高波动，观望为主"
        else:
            return "保持观望"

def show_risk_management():
    """显示风险管理"""
    st.markdown("## 🎯 海龟交易风险管理")
    
    # 风险管理计算器
    st.markdown("### 💰 头寸规模计算器")
    
    col1, col2 = st.columns(2)
    
    with col1:
        account_size = st.number_input("账户总资金", min_value=10000, value=100000, step=10000)
        risk_percent = st.slider("风险百分比 (%)", 0.5, 5.0, 1.0, 0.1)
        selected_etf = st.selectbox("选择ETF标的", list(ETF_CONFIG.keys()))
        atr_multiple = st.slider("止损ATR倍数", 1.0, 4.0, 2.0, 0.1)
    
    with col2:
        if st.button("获取实时数据并计算", type="primary"):
            try:
                symbol_code = ETF_CONFIG[selected_etf]
                with st.spinner("正在获取实时数据..."):
                    data = load_data(symbol_code, "etf", "daily", 50)
                
                if data is not None and len(data) > 30:
                    # 计算指标
                    data = turtle_strategy_signals(data)
                    latest = data.iloc[-1]
                    
                    current_price = latest['close']
                    atr_value = latest['ATR']
                    
                    # 计算结果
                    risk_amount = account_size * (risk_percent / 100)
                    stop_distance = atr_value * atr_multiple
                    position_size = int(risk_amount / stop_distance) if stop_distance > 0 else 0
                    position_value = position_size * current_price
                    
                    # 判断当前信号
                    current_signal = "无信号"
                    signal_color = "gray"
                    if latest['long_entry']:
                        current_signal = "🔴 做多信号"
                        signal_color = "red"
                    elif latest['short_entry']:
                        current_signal = "🟢 做空信号"
                        signal_color = "green"
                    elif latest['long_exit']:
                        current_signal = "🟡 多头出场"
                        signal_color = "orange"
                    elif latest['short_exit']:
                        current_signal = "🟡 空头出场"
                        signal_color = "orange"
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>{selected_etf} 风险管理计算结果</h4>
                        <p><strong>当前价格：</strong>¥{current_price:.2f}</p>
                        <p><strong>ATR值：</strong>{atr_value:.2f}</p>
                        <p><strong>当前信号：</strong><span style='color:{signal_color}'>{current_signal}</span></p>
                        <hr>
                        <p><strong>风险金额：</strong>¥{risk_amount:,.0f}</p>
                        <p><strong>止损距离：</strong>{stop_distance:.2f}</p>
                        <p><strong>建议头寸：</strong>{position_size:,}股</p>
                        <p><strong>头寸价值：</strong>¥{position_value:,.0f}</p>
                        <p><strong>账户风险敞口：</strong>{(position_value/account_size)*100:.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 风险提醒
                    if position_value / account_size > 0.3:
                        st.warning("⚠️ 警告：单笔头寸占账户比例过高，建议降低头寸规模")
                    elif current_signal != "无信号" and position_size > 0:
                        if "做多" in current_signal:
                            st.success(f"✅ 当前有做多信号，建议头寸：{position_size:,}股，止损价：{current_price - stop_distance:.2f}")
                        elif "做空" in current_signal:
                            st.info(f"ℹ️ 当前有做空信号，但ETF无法直接做空，建议观望或考虑期权策略")
                        elif "出场" in current_signal:
                            st.warning(f"⚠️ 当前有出场信号，建议平仓现有头寸")
                    
                else:
                    st.error("数据获取失败，无法计算风险参数")
            except Exception as e:
                st.error(f"计算过程中出现错误: {str(e)}")
    
    # 实时风险监控
    st.markdown("### 📊 实时风险监控")
    
    if st.button("刷新所有ETF风险状态", type="secondary"):
        risk_data = []
        
        with st.spinner("正在获取所有ETF数据..."):
            for name, code in ETF_CONFIG.items():
                try:
                    data = load_data(code, "etf", "daily", 30)
                    if data is not None and len(data) > 20:
                        data = turtle_strategy_signals(data)
                        latest = data.iloc[-1]
                        
                        # 计算风险指标
                        current_price = latest['close']
                        atr_value = latest['ATR']
                        volatility = (data['close'].pct_change().std() * np.sqrt(252)) * 100  # 年化波动率
                        
                        # 判断信号
                        signal = "无信号"
                        risk_level = "低"
                        if latest['long_entry']:
                            signal = "🔴 做多信号"
                            risk_level = "中"
                        elif latest['short_entry']:
                            signal = "🟢 做空信号"
                            risk_level = "中"
                        elif latest['long_exit'] or latest['short_exit']:
                            signal = "🟡 出场信号"
                            risk_level = "高"
                        
                        # 根据波动率调整风险等级
                        if volatility > 30:
                            risk_level = "高"
                        elif volatility > 20:
                            risk_level = "中" if risk_level == "低" else risk_level
                        
                        risk_data.append({
                            "ETF标的": name,
                            "当前价格": f"{current_price:.2f}",
                            "ATR值": f"{atr_value:.2f}",
                            "年化波动率": f"{volatility:.1f}%",
                            "当前信号": signal,
                            "风险等级": risk_level,
                            "建议操作": get_risk_advice(signal, risk_level)
                        })
                        
                except Exception as e:
                    st.warning(f"{name} 数据获取失败: {str(e)}")
        
        if risk_data:
            df = pd.DataFrame(risk_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.error("未能获取任何有效数据")
    
    # 风险管理原则
    st.markdown("### 🛡️ 核心风险管理原则")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="rule-card">
            <h4>🎯 头寸管理</h4>
            <ul>
                <li>单笔交易风险不超过账户的1-2%</li>
                <li>单个ETF最大头寸不超过4个单位</li>
                <li>高度相关ETF总头寸不超过6个单位</li>
                <li>所有头寸总风险不超过账户的20%</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="rule-card">
            <h4>📊 市场分散</h4>
            <ul>
                <li>分散投资于不同的行业和风格 ETF</li>
                <li>避免在相关性过高的ETF重复下注</li>
                <li>关注整体投资组合的风险敞口</li>
                <li>定期评估和调整投资组合</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="rule-card">
            <h4>🛑 止损纪律</h4>
            <ul>
                <li>严格按照ATR设置止损，不可随意修改</li>
                <li>绝不移动止损以增加损失</li>
                <li>亏损达到预设标准立即止损</li>
                <li>情绪化交易是最大的敌人</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="rule-card">
            <h4>⚖️ 资金管理</h4>
            <ul>
                <li>保持足够的现金储备</li>
                <li>避免过度杠杆和满仓操作</li>
                <li>连续亏损时适当减少头寸</li>
                <li>盈利时可适度增加风险敞口</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # 心理建设
    st.markdown("### 🧠 交易心理建设")

    st.markdown("""
    <div class="warning-box">
        <h4>💡 成功交易的心理要素</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
                <p><strong>🎯 纪律性</strong>：严格按照规则执行，不受情绪影响</p>
                <p><strong>🔄 一致性</strong>：持续应用相同的交易方法和风险管理</p>
                <p><strong>📊 客观性</strong>：基于数据和事实做决策，避免主观臆断</p>
            </div>
            <div>
                <p><strong>🛡️ 风险意识</strong>：时刻关注风险，保护资本是第一要务</p>
                <p><strong>📈 长期视角</strong>：关注长期收益，不因短期波动改变策略</p>
                <p><strong>🎓 持续学习</strong>：不断学习和改进，适应市场变化</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()