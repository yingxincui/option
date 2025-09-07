import streamlit as st
import akshare as ak
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# 设置页面配置
st.set_page_config(
    page_title="ETF技术分析",
    page_icon="📈",
    layout="wide"
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .signal-bullish {
        color: #00ff00;
        font-weight: bold;
    }
    .signal-bearish {
        color: #ff0000;
        font-weight: bold;
    }
    .signal-neutral {
        color: #ffa500;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ETF配置
ETF_CONFIG = {
    "科创50ETF (588000)": "588000",
    "中证500ETF (510500)": "510500", 
    "上证50ETF (510050)": "510050",
    "创业板ETF (159915)": "159915",
    "沪深300ETF (510300)": "510300",
    "深证100ETF (159901)": "159901"
}

def load_etf_data(symbol, period="daily", days=250):
    """加载ETF历史数据"""
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        with st.spinner(f"正在加载 {symbol} 的历史数据..."):
            df = ak.fund_etf_hist_em(
                symbol=symbol, 
                period=period, 
                start_date=start_date, 
                end_date=end_date, 
                adjust="qfq"  # 前复权
            )
            
        if df is not None and not df.empty:
            # 转换日期格式
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期').reset_index(drop=True)
            st.success(f"成功加载 {len(df)} 条历史数据")
            return df
        else:
            st.error("数据加载失败")
            return None
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        return None

def calculate_technical_indicators(df):
    """计算技术指标"""
    if df is None or df.empty:
        return df
    
    # 计算移动平均线
    df['MA5'] = df['收盘'].rolling(window=5).mean()
    df['MA10'] = df['收盘'].rolling(window=10).mean()
    df['MA20'] = df['收盘'].rolling(window=20).mean()
    df['MA60'] = df['收盘'].rolling(window=60).mean()
    
    # 计算MACD
    exp1 = df['收盘'].ewm(span=12).mean()
    exp2 = df['收盘'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # 计算RSI
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算KDJ（9,3,3）
    low_n = df['最低'].rolling(window=9).min()
    high_n = df['最高'].rolling(window=9).max()
    rsv = (df['收盘'] - low_n) / (high_n - low_n).replace(0, np.nan) * 100
    df['K'] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/3, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    # 计算布林带
    df['BB_Middle'] = df['收盘'].rolling(window=20).mean()
    bb_std = df['收盘'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # 计算成交量移动平均
    df['Volume_MA5'] = df['成交量'].rolling(window=5).mean()
    df['Volume_MA10'] = df['成交量'].rolling(window=10).mean()
    
    # 计算OBV及其均线
    price_change = df['收盘'].diff().fillna(0)
    direction = np.where(price_change > 0, 1, np.where(price_change < 0, -1, 0))
    df['OBV'] = (direction * df['成交量']).cumsum()
    df['OBV_MA10'] = df['OBV'].rolling(10).mean()
    
    return df

def analyze_technical_signals(df):
    """分析技术信号"""
    if df is None or df.empty or len(df) < 20:
        return {}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    signals = {}
    
    # 均线分析
    current_price = latest['收盘']
    ma5 = latest['MA5']
    ma10 = latest['MA10'] 
    ma20 = latest['MA20']
    
    # 均线位置
    signals['price_above_ma5'] = current_price > ma5
    signals['price_above_ma10'] = current_price > ma10
    signals['price_above_ma20'] = current_price > ma20
    
    # 多头排列
    signals['bullish_alignment'] = ma5 > ma10 > ma20
    
    # 均线金叉死叉
    signals['ma5_ma10_golden_cross'] = (latest['MA5'] > latest['MA10']) and (prev['MA5'] <= prev['MA10'])
    signals['ma5_ma10_death_cross'] = (latest['MA5'] < latest['MA10']) and (prev['MA5'] >= prev['MA10'])
    
    signals['ma10_ma20_golden_cross'] = (latest['MA10'] > latest['MA20']) and (prev['MA10'] <= prev['MA20'])
    signals['ma10_ma20_death_cross'] = (latest['MA10'] < latest['MA20']) and (prev['MA10'] >= prev['MA20'])
    
    # MACD分析
    signals['macd_golden_cross'] = (latest['MACD'] > latest['MACD_Signal']) and (prev['MACD'] <= prev['MACD_Signal'])
    signals['macd_death_cross'] = (latest['MACD'] < latest['MACD_Signal']) and (prev['MACD'] >= prev['MACD_Signal'])
    signals['macd_above_zero'] = latest['MACD'] > 0
    
    # RSI分析
    rsi = latest['RSI']
    signals['rsi_oversold'] = rsi < 30
    signals['rsi_overbought'] = rsi > 70
    signals['rsi_neutral'] = 30 <= rsi <= 70
    
    # 布林带分析
    signals['price_above_bb_upper'] = current_price > latest['BB_Upper']
    signals['price_below_bb_lower'] = current_price < latest['BB_Lower']
    signals['price_in_bb'] = latest['BB_Lower'] <= current_price <= latest['BB_Upper']
    
    # 成交量分析
    volume_ratio = latest['成交量'] / latest['Volume_MA5']
    signals['volume_surge'] = volume_ratio > 1.5
    signals['volume_shrink'] = volume_ratio < 0.8
    
    return signals

def create_etf_chart(df, symbol_name):
    """创建ETF技术分析图表"""
    if df is None or df.empty:
        return None
    
    fig = go.Figure()
    
    # 添加K线图
    fig.add_trace(go.Candlestick(
        x=df['日期'],
        open=df['开盘'],
        high=df['最高'],
        low=df['最低'],
        close=df['收盘'],
        name='K线',
        increasing_line_color='red',
        decreasing_line_color='green'
    ))
    
    # 添加移动平均线
    fig.add_trace(go.Scatter(
        x=df['日期'], y=df['MA5'], 
        mode='lines', name='MA5', 
        line=dict(color='blue', width=1)
    ))
    fig.add_trace(go.Scatter(
        x=df['日期'], y=df['MA10'], 
        mode='lines', name='MA10', 
        line=dict(color='orange', width=1)
    ))
    fig.add_trace(go.Scatter(
        x=df['日期'], y=df['MA20'], 
        mode='lines', name='MA20', 
        line=dict(color='purple', width=1)
    ))
    
    # 添加布林带
    fig.add_trace(go.Scatter(
        x=df['日期'], y=df['BB_Upper'], 
        mode='lines', name='布林上轨', 
        line=dict(color='gray', width=1, dash='dash'),
        opacity=0.7
    ))
    fig.add_trace(go.Scatter(
        x=df['日期'], y=df['BB_Lower'], 
        mode='lines', name='布林下轨', 
        line=dict(color='gray', width=1, dash='dash'),
        opacity=0.7,
        fill='tonexty',
        fillcolor='rgba(128,128,128,0.1)'
    ))
    
    fig.update_layout(
        title=f"{symbol_name} 技术分析图表",
        xaxis_title="日期",
        yaxis_title="价格",
        height=600,
        hovermode='x unified'
    )
    
    return fig

def create_macd_chart(df, symbol_name):
    """创建MACD图表"""
    if df is None or df.empty:
        return None
    
    fig = go.Figure()
    
    # MACD线
    fig.add_trace(go.Scatter(
        x=df['日期'], y=df['MACD'], 
        mode='lines', name='MACD', 
        line=dict(color='blue', width=2)
    ))
    
    # 信号线
    fig.add_trace(go.Scatter(
        x=df['日期'], y=df['MACD_Signal'], 
        mode='lines', name='Signal', 
        line=dict(color='red', width=2)
    ))
    
    # 柱状图
    colors = ['green' if val >= 0 else 'red' for val in df['MACD_Histogram']]
    fig.add_trace(go.Bar(
        x=df['日期'], y=df['MACD_Histogram'], 
        name='Histogram', 
        marker_color=colors,
        opacity=0.7
    ))
    
    # 零轴线
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
    fig.update_layout(
        title=f"{symbol_name} MACD指标",
        xaxis_title="日期",
        yaxis_title="MACD",
        height=300,
        hovermode='x unified'
    )
    
    return fig

def create_volume_chart(df, symbol_name):
    """创建成交量图表"""
    if df is None or df.empty:
        return None
    
    fig = go.Figure()
    
    # 成交量柱状图
    colors = ['red' if df.iloc[i]['收盘'] >= df.iloc[i]['开盘'] else 'green' 
              for i in range(len(df))]
    
    fig.add_trace(go.Bar(
        x=df['日期'], y=df['成交量'], 
        name='成交量', 
        marker_color=colors,
        opacity=0.7
    ))
    
    # 成交量移动平均线
    fig.add_trace(go.Scatter(
        x=df['日期'], y=df['Volume_MA5'], 
        mode='lines', name='成交量MA5', 
        line=dict(color='blue', width=2)
    ))
    
    fig.update_layout(
        title=f"{symbol_name} 成交量分析",
        xaxis_title="日期",
        yaxis_title="成交量",
        height=300,
        hovermode='x unified'
    )
    
    return fig

def display_comprehensive_analysis(df, signals, symbol_name):
    """显示融合的综合技术分析和总体结论"""
    if df is None or df.empty or len(df) < 20:
        return
    
    st.subheader(f"🔍 {symbol_name} 综合技术分析")
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    current_price = latest['收盘']
    ma5 = latest['MA5']
    ma10 = latest['MA10']
    ma20 = latest['MA20']
    macd = latest['MACD']
    macd_signal = latest['MACD_Signal']
    rsi = latest['RSI']
    volume_ratio = latest['成交量'] / latest['Volume_MA5']
    price_change = latest['涨跌幅']
    
    # 计算共振分析
    # 趋势型
    trend_points = 0
    trend_msgs = []
    if (latest['MA5'] > latest['MA10'] > latest['MA20']):
        trend_points += 1
        trend_msgs.append("多头排列")
    if latest['MACD'] > 0:
        trend_points += 1
        trend_msgs.append("MACD>0")
    if (latest['MACD'] > latest['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']):
        trend_msgs.append("MACD金叉")
    trend_status = "偏多" if trend_points >= 2 else ("中性" if trend_points == 1 else "偏空")
    
    # 摆动型
    osc_points = 0
    osc_msgs = []
    if latest.get('RSI', 50) >= 50:
        osc_points += 1
        osc_msgs.append("RSI≥50")
    if ('K' in latest and 'D' in latest) and (latest['K'] > latest['D'] and prev['K'] <= prev['D']):
        osc_points += 1
        osc_msgs.append("KDJ金叉")
    if latest.get('RSI', 50) < 30:
        osc_points += 1
        osc_msgs.append("RSI超卖")
    osc_status = "偏多" if osc_points >= 2 else ("中性" if osc_points == 1 else "偏空")
    
    # 能量型
    energy_points = 0
    energy_msgs = []
    vol_ratio = latest['成交量'] / max(latest['Volume_MA5'], 1)
    if vol_ratio > 1.2:
        energy_points += 1
        energy_msgs.append(f"量比≈{vol_ratio:.2f}放大")
    if 'OBV' in df.columns and 'OBV_MA10' in df.columns and latest['OBV'] > latest['OBV_MA10']:
        energy_points += 1
        energy_msgs.append("OBV在均线上方")
    energy_status = "偏多" if energy_points >= 2 else ("中性" if energy_points == 1 else "偏空")
    
    # 空间型
    space_points = 0
    space_msgs = []
    if latest['收盘'] >= latest['BB_Middle']:
        space_points += 1
        space_msgs.append("收盘≥中轨")
    bb_range = max(latest['BB_Upper'] - latest['BB_Lower'], 1e-9)
    if (latest['收盘'] - latest['BB_Lower']) / bb_range < 0.2:
        space_points += 1
        space_msgs.append("接近下轨支撑")
    space_status = "偏多" if space_points >= 2 else ("中性" if space_points == 1 else "偏空")
    
    # 计算共振评分
    bull_count = sum(s == '偏多' for s in [trend_status, osc_status, energy_status, space_status])
    neutral_count = sum(s == '中性' for s in [trend_status, osc_status, energy_status, space_status])
    resonance_score = bull_count * 2 + neutral_count
    
    # 计算综合评分（传统评分系统）
    score = 0
    max_score = 10
    
    # 价格位置评分 (3分)
    if current_price > ma20:
        if current_price > ma10:
            if current_price > ma5:
                score += 3  # 所有均线之上
            else:
                score += 2  # MA10、MA20之上
        else:
            score += 1  # 仅MA20之上
    else:
        score += 0  # 所有均线之下
    
    # 均线排列评分 (2分)
    if ma5 > ma10 > ma20:
        score += 2  # 多头排列
    elif ma5 < ma10 < ma20:
        score += 0  # 空头排列
    else:
        score += 1  # 均线交织
    
    # MACD评分 (2分)
    if macd > 0 and macd > macd_signal:
        score += 2  # 零轴上方金叉
    elif macd > 0:
        score += 1  # 零轴上方
    elif macd > macd_signal:
        score += 1  # 零轴下方金叉
    else:
        score += 0  # 零轴下方死叉
    
    # RSI评分 (1分)
    if 30 <= rsi <= 70:
        score += 1  # 中性区间
    elif rsi < 30:
        score += 0.5  # 超卖
    else:
        score += 0  # 超买
    
    # 成交量评分 (1分)
    if volume_ratio > 1.5:
        score += 1  # 放量
    elif volume_ratio > 0.8:
        score += 0.5  # 正常
    else:
        score += 0  # 缩量
    
    # 涨跌幅评分 (1分)
    if price_change > 2:
        score += 1  # 大涨
    elif price_change > 0:
        score += 0.5  # 小涨
    elif price_change > -2:
        score += 0  # 小跌
    else:
        score += 0  # 大跌
    
    # 根据评分确定总体结论
    score_percentage = (score / max_score) * 100
    
    # 共振结论
    if bull_count >= 3:
        resonance_conclusion = "强共振（看多）"
        resonance_icon, resonance_color = "🚀", "green"
    elif bull_count == 2:
        resonance_conclusion = "中度共振（偏多）"
        resonance_icon, resonance_color = "📈", "#2ca02c"
    elif bull_count == 1:
        resonance_conclusion = "弱共振（中性略多）"
        resonance_icon, resonance_color = "⚪", "#ff7f0e"
    else:
        resonance_conclusion = "无共振/偏空"
        resonance_icon, resonance_color = "🔻", "red"
    
    # 总体结论
    if score_percentage >= 80:
        overall_status = "技术面强势，建议积极关注"
        status_emoji = "🚀"
        status_color = "green"
    elif score_percentage >= 60:
        overall_status = "技术面偏强，可适度关注"
        status_emoji = "📈"
        status_color = "lightgreen"
    elif score_percentage >= 40:
        overall_status = "技术面中性，观望为主"
        status_emoji = "⚪"
        status_color = "orange"
    elif score_percentage >= 20:
        overall_status = "技术面偏弱，谨慎操作"
        status_emoji = "📉"
        status_color = "red"
    else:
        overall_status = "技术面弱势，建议回避"
        status_emoji = "🔴"
        status_color = "darkred"
    
    # 显示综合结论
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### {status_emoji} {overall_status}")
        st.markdown(f"**综合评分**: {score:.1f}/{max_score} ({score_percentage:.1f}%)")
        st.markdown(f"**{resonance_icon} 指标共振**: <span style='color:{resonance_color}; font-weight:600'>{resonance_conclusion}</span>（得分 {resonance_score}/8）", unsafe_allow_html=True)
    
    with col2:
        # 创建评分进度条
        st.markdown("**技术评分**")
        progress = score / max_score
        st.progress(progress)
        
        # 关键指标
        st.markdown("**关键指标**")
        st.write(f"当前价格: {current_price:.3f}")
        st.write(f"涨跌幅: {price_change:.2f}%")
        st.write(f"RSI: {rsi:.1f}")
        st.write(f"量比: {volume_ratio:.2f}")
    
    # 四象限详细分析
    st.markdown("---")
    st.markdown("### 📊 四象限技术分析")
    
    # 添加共振分析依据说明（默认折叠）
    with st.expander("📚 共振分析依据说明", expanded=False):
        st.markdown("""
        **指标共振系统**是基于四大类技术指标的综合分析框架，通过多维度指标的一致性来判断市场趋势强度：
        
        #### 📈 趋势型指标（看方向）
        - **功能**：判断市场当前处于上升、下降还是震荡趋势
        - **主要指标**：移动平均线(MA)、MACD、布林带中轨
        - **评分标准**：
          - 多头排列(MA5>MA10>MA20) +1分
          - MACD>0 +1分
          - MACD金叉 +1分
        - **共振示例**：短期均线上穿长期均线(金叉)，同时MACD也在零轴上方出现金叉
        
        #### 📊 摆动型指标（看位置）
        - **功能**：判断当前价格在短期内的相对位置，是否处于极端状态
        - **主要指标**：RSI、KDJ、威廉指标
        - **评分标准**：
          - RSI≥50 +1分
          - KDJ金叉 +1分
          - RSI超卖(<30) +1分
        - **共振示例**：RSI和KDJ同时从超卖区向上拐头，预示下跌可能结束
        
        #### ⚡ 能量型指标（看力度）
        - **功能**：分析价格变动背后的成交量支撑力度，确认趋势的强弱
        - **主要指标**：成交量、OBV、资金流量指标
        - **评分标准**：
          - 量比>1.2 +1分
          - OBV在均线上方 +1分
        - **共振示例**：价格突破关键阻力位上涨，同时成交量显著放大，OBV指标也同步创出新高
        
        #### 🎯 空间型指标（看支撑压力）
        - **功能**：识别关键的价格支撑位和压力位
        - **主要指标**：布林带、黄金分割线、前期高低点
        - **评分标准**：
          - 收盘≥中轨 +1分
          - 接近下轨支撑 +1分
        - **共振示例**：价格回调至重要的黄金分割位或前期平台支撑位，同时其他技术指标也发出买入信号
        
        #### 🔄 共振评分机制
        - **强共振（看多）**：3-4个象限偏多，得分6-8分
        - **中度共振（偏多）**：2个象限偏多，得分4-5分
        - **弱共振（中性略多）**：1个象限偏多，得分2-3分
        - **无共振/偏空**：0个象限偏多，得分0-1分
        
        **注意**：共振分析需要多个指标同时发出相同信号才能确认，单一指标容易产生假信号。
        """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**📈 趋势型（方向）**")
        st.markdown(f"状态：<span style='color:{"green" if trend_status == "偏多" else "orange" if trend_status == "中性" else "red"}'>{trend_status}</span>", unsafe_allow_html=True)
        st.write("• 均线排列：", "✅" if signals['bullish_alignment'] else "❌", "多头排列" if signals['bullish_alignment'] else "非多头排列")
        st.write("• 价格位置：", "✅" if signals['price_above_ma20'] else "❌", f"价格在MA20{'之上' if signals['price_above_ma20'] else '之下'}")
        st.write("• MACD状态：", "✅" if signals['macd_above_zero'] else "❌", f"MACD{'零轴上方' if signals['macd_above_zero'] else '零轴下方'}")
        if trend_msgs:
            st.write("• 共振信号：", "；".join(trend_msgs))
    
    with col2:
        st.markdown("**📊 摆动型（位置）**")
        st.markdown(f"状态：<span style='color:{"green" if osc_status == "偏多" else "orange" if osc_status == "中性" else "red"}'>{osc_status}</span>", unsafe_allow_html=True)
        if rsi < 30:
            st.write("• RSI：", "🟢 超卖 (< 30)")
        elif rsi > 70:
            st.write("• RSI：", "🔴 超买 (> 70)")
        else:
            st.write("• RSI：", "⚪ 中性 (30-70)")
        
        if 'K' in latest and 'D' in latest:
            kdj_signal = "金叉" if latest['K'] > latest['D'] else "死叉" if latest['K'] < latest['D'] else "无交叉"
            st.write("• KDJ：", f"⚪ {kdj_signal}")
        
        if osc_msgs:
            st.write("• 共振信号：", "；".join(osc_msgs))
    
    with col3:
        st.markdown("**⚡ 能量型（力度）**")
        st.markdown(f"状态：<span style='color:{"green" if energy_status == "偏多" else "orange" if energy_status == "中性" else "red"}'>{energy_status}</span>", unsafe_allow_html=True)
        if signals['volume_surge']:
            st.write("• 成交量：", "📈 放大")
        elif signals['volume_shrink']:
            st.write("• 成交量：", "📉 萎缩")
        else:
            st.write("• 成交量：", "📊 正常")
        
        if 'OBV' in df.columns and 'OBV_MA10' in df.columns:
            obv_signal = "上方" if latest['OBV'] > latest['OBV_MA10'] else "下方"
            st.write("• OBV：", f"📊 位于均线{obv_signal}")
        
        if energy_msgs:
            st.write("• 共振信号：", "；".join(energy_msgs))
    
    with col4:
        st.markdown("**🎯 空间型（支撑压力）**")
        st.markdown(f"状态：<span style='color:{"green" if space_status == "偏多" else "orange" if space_status == "中性" else "red"}'>{space_status}</span>", unsafe_allow_html=True)
        if signals['price_above_bb_upper']:
            st.write("• 布林带：", "🔴 突破上轨")
        elif signals['price_below_bb_lower']:
            st.write("• 布林带：", "🟢 跌破下轨")
        else:
            st.write("• 布林带：", "⚪ 在带内")
        
        st.write("• 价格位置：", "✅" if latest['收盘'] >= latest['BB_Middle'] else "❌", f"收盘{'在' if latest['收盘'] >= latest['BB_Middle'] else '低于'}中轨")
        
        if space_msgs:
            st.write("• 共振信号：", "；".join(space_msgs))
    
    # 金叉死叉信号汇总
    st.markdown("---")
    st.markdown("### 🔄 金叉死叉信号汇总")
    
    cross_signals = []
    if signals['ma5_ma10_golden_cross']:
        cross_signals.append("🟢 MA5上穿MA10")
    elif signals['ma5_ma10_death_cross']:
        cross_signals.append("🔴 MA5下穿MA10")
    
    if signals['ma10_ma20_golden_cross']:
        cross_signals.append("🟢 MA10上穿MA20")
    elif signals['ma10_ma20_death_cross']:
        cross_signals.append("🔴 MA10下穿MA20")
    
    if signals['macd_golden_cross']:
        cross_signals.append("🟢 MACD金叉")
    elif signals['macd_death_cross']:
        cross_signals.append("🔴 MACD死叉")
    
    if 'K' in latest and 'D' in latest and (latest['K'] > latest['D'] and prev['K'] <= prev['D']):
        cross_signals.append("🟢 KDJ金叉")
    elif 'K' in latest and 'D' in latest and (latest['K'] < latest['D'] and prev['K'] >= prev['D']):
        cross_signals.append("🔴 KDJ死叉")
    
    if cross_signals:
        st.write("当前信号：", " | ".join(cross_signals))
    else:
        st.write("当前信号：⚪ 无交叉信号")
    
    # 投资建议
    st.markdown("---")
    st.markdown("### 💡 投资建议")
    
    # 做多/做空建议
    if score_percentage >= 80:
        direction = "强烈做多"
        direction_emoji = "🚀"
        direction_color = "green"
        option_advice = "买入当月实值一档看涨期权"
        etf_advice = "可考虑买入ETF现货"
        risk_level = "中等风险"
    elif score_percentage >= 60:
        direction = "适度做多"
        direction_emoji = "📈"
        direction_color = "lightgreen"
        option_advice = "可考虑买入当月平值看涨期权"
        etf_advice = "可适度买入ETF现货"
        risk_level = "中低风险"
    elif score_percentage >= 40:
        direction = "观望"
        direction_emoji = "👀"
        direction_color = "orange"
        option_advice = "建议观望，等待明确信号"
        etf_advice = "建议观望，等待趋势明确"
        risk_level = "低风险"
    elif score_percentage >= 20:
        direction = "适度做空"
        direction_emoji = "📉"
        direction_color = "red"
        option_advice = "可考虑买入当月实值一档看跌期权"
        etf_advice = "建议减仓或观望"
        risk_level = "中高风险"
    else:
        direction = "强烈做空"
        direction_emoji = "🔴"
        direction_color = "darkred"
        option_advice = "可考虑买入当月平值看跌期权"
        etf_advice = "建议清仓或做空"
        risk_level = "高风险"
    
    # 显示做多/做空建议
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**{direction_emoji} 操作方向**")
        st.markdown(f"<span style='color: {direction_color}; font-size: 18px; font-weight: bold;'>{direction}</span>", unsafe_allow_html=True)
        st.write(f"风险等级: {risk_level}")
    
    with col2:
        st.markdown("**📊 期权建议**")
        st.write(option_advice)
        if score_percentage >= 60:
            st.write("• 建议选择实值或平值期权")
            st.write("• 注意时间价值损耗")
        elif score_percentage <= 40:
            st.write("• 建议选择看跌期权")
            st.write("• 注意波动率风险")
    
    with col3:
        st.markdown("**📈 ETF现货建议**")
        st.write(etf_advice)
        if score_percentage >= 60:
            st.write("• 可分批建仓")
            st.write("• 设置止损位")
        elif score_percentage <= 40:
            st.write("• 建议减仓操作")
            st.write("• 等待技术面改善")
    
    # 风险提示
    st.markdown("---")
    st.markdown("### ⚠️ 风险提示")
    st.markdown("""
    - 以上建议仅供参考，不构成投资建议
    - 期权投资风险较高，请根据自身风险承受能力谨慎操作
    - 建议设置止损位，控制风险
    - 市场有风险，投资需谨慎
    """)



def display_main_chart_conclusion(df, signals, symbol_name):
    """显示主图表分析结论"""
    st.markdown("---")
    st.markdown("### 📊 主图表分析结论")
    
    latest = df.iloc[-1]
    current_price = latest['收盘']
    ma5 = latest['MA5']
    ma10 = latest['MA10']
    ma20 = latest['MA20']
    
    # 价格位置分析
    if current_price > ma20:
        if current_price > ma10:
            if current_price > ma5:
                price_position = "价格位于所有均线之上，技术面强势"
                price_emoji = "🚀"
            else:
                price_position = "价格在MA5之下但MA10、MA20之上，短期调整"
                price_emoji = "⚠️"
        else:
            price_position = "价格在MA10之下但MA20之上，中期调整"
            price_emoji = "📉"
    else:
        price_position = "价格在所有均线之下，技术面弱势"
        price_emoji = "🔴"
    
    # 均线排列分析
    if ma5 > ma10 > ma20:
        ma_alignment = "多头排列，趋势向上"
        ma_emoji = "✅"
    elif ma5 < ma10 < ma20:
        ma_alignment = "空头排列，趋势向下"
        ma_emoji = "❌"
    else:
        ma_alignment = "均线交织，趋势不明"
        ma_emoji = "⚪"
    
    # 布林带分析
    bb_upper = latest['BB_Upper']
    bb_lower = latest['BB_Lower']
    if current_price > bb_upper:
        bb_position = "价格突破布林上轨，可能超买"
        bb_emoji = "🔴"
    elif current_price < bb_lower:
        bb_position = "价格跌破布林下轨，可能超卖"
        bb_emoji = "🟢"
    else:
        bb_position = "价格在布林带内，正常波动"
        bb_emoji = "⚪"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**{price_emoji} 价格位置**")
        st.write(price_position)
    
    with col2:
        st.markdown(f"**{ma_emoji} 均线排列**")
        st.write(ma_alignment)
    
    with col3:
        st.markdown(f"**{bb_emoji} 布林带位置**")
        st.write(bb_position)

def display_macd_chart_conclusion(df, signals, symbol_name):
    """显示MACD图表分析结论"""
    st.markdown("---")
    st.markdown("### 📈 MACD分析结论")
    
    latest = df.iloc[-1]
    macd = latest['MACD']
    macd_signal = latest['MACD_Signal']
    macd_hist = latest['MACD_Histogram']
    
    # MACD位置分析
    if macd > 0:
        if macd > macd_signal:
            macd_position = "MACD在零轴上方且金叉，多头强势"
            macd_emoji = "🚀"
        else:
            macd_position = "MACD在零轴上方但死叉，多头调整"
            macd_emoji = "⚠️"
    else:
        if macd > macd_signal:
            macd_position = "MACD在零轴下方但金叉，空头转多"
            macd_emoji = "🟢"
        else:
            macd_position = "MACD在零轴下方且死叉，空头强势"
            macd_emoji = "🔴"
    
    # MACD柱状图分析
    if macd_hist > 0:
        if macd_hist > latest['MACD_Histogram']:
            hist_trend = "MACD柱状图放大，动能增强"
            hist_emoji = "📈"
        else:
            hist_trend = "MACD柱状图缩小，动能减弱"
            hist_emoji = "📉"
    else:
        hist_trend = "MACD柱状图为负，空头动能"
        hist_emoji = "🔴"
    
    # 趋势强度分析
    recent_macd = df['MACD'].tail(5)
    if recent_macd.iloc[-1] > recent_macd.iloc[-5]:
        trend_strength = "MACD近期呈上升趋势"
        trend_emoji = "🟢"
    elif recent_macd.iloc[-1] < recent_macd.iloc[-5]:
        trend_strength = "MACD近期呈下降趋势"
        trend_emoji = "🔴"
    else:
        trend_strength = "MACD近期横盘整理"
        trend_emoji = "⚪"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**{macd_emoji} MACD位置**")
        st.write(macd_position)
    
    with col2:
        st.markdown(f"**{hist_emoji} 柱状图**")
        st.write(hist_trend)
    
    with col3:
        st.markdown(f"**{trend_emoji} 趋势强度**")
        st.write(trend_strength)

def display_volume_chart_conclusion(df, signals, symbol_name):
    """显示成交量图表分析结论"""
    st.markdown("---")
    st.markdown("### 📊 成交量分析结论")
    
    latest = df.iloc[-1]
    current_volume = latest['成交量']
    volume_ma5 = latest['Volume_MA5']
    volume_ma10 = latest['Volume_MA10']
    
    # 成交量水平分析
    volume_ratio_5 = current_volume / volume_ma5
    volume_ratio_10 = current_volume / volume_ma10
    
    if volume_ratio_5 > 2.0:
        volume_level = "成交量显著放大，资金关注度高"
        volume_emoji = "🔥"
    elif volume_ratio_5 > 1.5:
        volume_level = "成交量温和放大，资金关注度提升"
        volume_emoji = "📈"
    elif volume_ratio_5 > 0.8:
        volume_level = "成交量正常，资金关注度一般"
        volume_emoji = "⚪"
    else:
        volume_level = "成交量萎缩，资金关注度低"
        volume_emoji = "📉"
    
    # 成交量趋势分析
    recent_volume = df['成交量'].tail(5)
    if recent_volume.iloc[-1] > recent_volume.iloc[-5]:
        volume_trend = "成交量呈上升趋势"
        trend_emoji = "🟢"
    elif recent_volume.iloc[-1] < recent_volume.iloc[-5]:
        volume_trend = "成交量呈下降趋势"
        trend_emoji = "🔴"
    else:
        volume_trend = "成交量横盘整理"
        trend_emoji = "⚪"
    
    # 量价关系分析
    price_change = latest['涨跌幅']
    if price_change > 0 and volume_ratio_5 > 1.2:
        price_volume = "量价齐升，上涨动能强劲"
        pv_emoji = "🚀"
    elif price_change < 0 and volume_ratio_5 > 1.2:
        price_volume = "量价齐跌，下跌动能强劲"
        pv_emoji = "🔴"
    elif price_change > 0 and volume_ratio_5 < 0.8:
        price_volume = "价升量缩，上涨动能不足"
        pv_emoji = "⚠️"
    elif price_change < 0 and volume_ratio_5 < 0.8:
        price_volume = "价跌量缩，下跌动能不足"
        pv_emoji = "🟢"
    else:
        price_volume = "量价关系正常"
        pv_emoji = "⚪"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**{volume_emoji} 成交量水平**")
        st.write(volume_level)
        st.write(f"当前成交量: {current_volume:,}")
        st.write(f"5日均量: {volume_ma5:,.0f}")
    
    with col2:
        st.markdown(f"**{trend_emoji} 成交量趋势**")
        st.write(volume_trend)
        st.write(f"5日量比: {volume_ratio_5:.2f}")
        st.write(f"10日量比: {volume_ratio_10:.2f}")
    
    with col3:
        st.markdown(f"**{pv_emoji} 量价关系**")
        st.write(price_volume)
        st.write(f"涨跌幅: {price_change:.2f}%")

def main():
    # 主标题
    st.markdown('<h1 class="main-header">📈 ETF技术分析</h1>', unsafe_allow_html=True)
    
    # 侧边栏配置
    st.sidebar.header("⚙️ 分析配置")
    
    # ETF选择
    selected_etf = st.sidebar.selectbox(
        "选择ETF标的",
        options=list(ETF_CONFIG.keys()),
        index=0
    )
    
    # 添加快速选择按钮
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("选择科创50ETF"):
            selected_etf = "科创50ETF (588000)"
    with col2:
        if st.button("选择沪深300ETF"):
            selected_etf = "沪深300ETF (510300)"
    
    # 分析周期
    period = st.sidebar.selectbox(
        "分析周期",
        options=["daily", "weekly", "monthly"],
        index=0
    )
    
    # 历史数据天数
    days = st.sidebar.slider(
        "历史数据天数",
        min_value=60,
        max_value=500,
        value=250,
        step=10
    )
    
    # 刷新按钮
    if st.sidebar.button("🔄 刷新分析", type="primary"):
        st.rerun()
    
    # 加载数据
    etf_symbol = ETF_CONFIG[selected_etf]
    df = load_etf_data(etf_symbol, period, days)
    
    if df is not None and not df.empty:
        # 计算技术指标
        df = calculate_technical_indicators(df)
        
        # 分析技术信号
        signals = analyze_technical_signals(df)
        
        # 显示当前价格信息
        latest = df.iloc[-1]
        st.subheader("📊 当前价格信息")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("当前价格", f"{latest['收盘']:.3f}")
        with col2:
            st.metric("涨跌幅", f"{latest['涨跌幅']:.2f}%")
        with col3:
            st.metric("成交量", f"{latest['成交量']:,}")
        with col4:
            st.metric("换手率", f"{latest['换手率']:.2f}%")
        
        # 显示融合的综合技术分析和总体结论
        display_comprehensive_analysis(df, signals, selected_etf)
        
        # 显示图表
        st.subheader("📈 技术分析图表")
        
        # 主图表
        main_chart = create_etf_chart(df, selected_etf)
        if main_chart:
            st.plotly_chart(main_chart, use_container_width=True)
            # 主图表结论
            display_main_chart_conclusion(df, signals, selected_etf)
        
        # MACD图表
        macd_chart = create_macd_chart(df, selected_etf)
        if macd_chart:
            st.plotly_chart(macd_chart, use_container_width=True)
            # MACD图表结论
            display_macd_chart_conclusion(df, signals, selected_etf)
        
        # 成交量图表
        volume_chart = create_volume_chart(df, selected_etf)
        if volume_chart:
            st.plotly_chart(volume_chart, use_container_width=True)
            # 成交量图表结论
            display_volume_chart_conclusion(df, signals, selected_etf)
        
        # 显示历史数据
        st.subheader("📋 历史数据")
        
        # 创建美化的历史数据表格
        display_df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量', '涨跌幅', 'MA5', 'MA10', 'MA20', 'MACD', 'RSI']].tail(20).copy()
        
        # 格式化数据
        display_df['日期'] = display_df['日期'].dt.strftime('%Y-%m-%d')
        display_df['开盘'] = display_df['开盘'].round(3)
        display_df['最高'] = display_df['最高'].round(3)
        display_df['最低'] = display_df['最低'].round(3)
        display_df['收盘'] = display_df['收盘'].round(3)
        display_df['MA5'] = display_df['MA5'].round(3)
        display_df['MA10'] = display_df['MA10'].round(3)
        display_df['MA20'] = display_df['MA20'].round(3)
        display_df['MACD'] = display_df['MACD'].round(4)
        display_df['RSI'] = display_df['RSI'].round(1)
        display_df['涨跌幅'] = display_df['涨跌幅'].round(2)
        
        # 添加样式
        def highlight_changes(val):
            if isinstance(val, (int, float)) and '涨跌幅' in str(val):
                if val > 0:
                    return 'color: green; font-weight: bold;'
                elif val < 0:
                    return 'color: red; font-weight: bold;'
            return ''
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
        
        # 数据下载
        st.subheader("💾 数据下载")
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载历史数据CSV文件",
            data=csv,
            file_name=f"{selected_etf}_{etf_symbol}_历史数据.csv",
            mime="text/csv"
        )
    
    else:
        st.warning("⚠️ 无法加载ETF数据，请检查网络连接或参数设置")

if __name__ == "__main__":
    main()
