import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.etf_analysis_shared import load_etf_data, calculate_technical_indicators
from utils.etf_analysis_shared import create_etf_chart

# ETF配置（与ETF技术分析页面保持一致）
ETF_CONFIG = {
    "科创50ETF (588000)": "588000",
    "中证500ETF (510500)": "510500", 
    "上证50ETF (510050)": "510050",
    "创业板ETF (159915)": "159915",
    "沪深300ETF (510300)": "510300",
    "深证100ETF (159901)": "159901"
}

# 支撑点和压力点分析函数
def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> dict:
    """
    计算支撑点和压力点
    """
    if df is None or df.empty or len(df) < window:
        return {}
    
    # 获取最近数据进行分析
    recent_df = df.tail(min(100, len(df)))  # 最近100个交易日
    
    # 方法1：基于局部高低点识别支撑阻力
    highs = []
    lows = []
    
    for i in range(window//2, len(recent_df) - window//2):
        # 寻找局部高点
        if recent_df.iloc[i]['最高'] == recent_df.iloc[i-window//2:i+window//2+1]['最高'].max():
            highs.append(recent_df.iloc[i]['最高'])
        
        # 寻找局部低点
        if recent_df.iloc[i]['最低'] == recent_df.iloc[i-window//2:i+window//2+1]['最低'].min():
            lows.append(recent_df.iloc[i]['最低'])
    
    # 方法2：基于价格密集区域
    prices = pd.concat([recent_df['最高'], recent_df['最低'], recent_df['收盘']])
    price_range = prices.max() - prices.min()
    bins = 20  # 将价格区间分为20个区间
    price_counts, bin_edges = np.histogram(prices, bins=bins)
    
    # 找到价格密集区域（交易频繁的价格区间）
    density_threshold = np.percentile(price_counts, 70)  # 前30%的密集区域
    dense_areas = []
    for i, count in enumerate(price_counts):
        if count >= density_threshold:
            dense_areas.append((bin_edges[i] + bin_edges[i+1]) / 2)
    
    # 方法3：基于均线和布林带
    latest = recent_df.iloc[-1]
    current_price = latest['收盘']
    
    # 整合所有支撑阻力位
    all_levels = []
    
    # 添加局部高低点
    all_levels.extend([(price, '局部高点', '阻力') for price in highs if abs(price - current_price) / current_price <= 0.15])
    all_levels.extend([(price, '局部低点', '支撑') for price in lows if abs(price - current_price) / current_price <= 0.15])
    
    # 添加密集区域
    all_levels.extend([(price, '价格密集区', '支撑/阻力') for price in dense_areas if abs(price - current_price) / current_price <= 0.15])
    
    # 添加技术指标位
    ma_levels = []
    for ma_period in [5, 10, 20, 60]:
        ma_key = f'MA{ma_period}'
        if ma_key in latest and not pd.isna(latest[ma_key]):
            ma_value = latest[ma_key]
            if abs(ma_value - current_price) / current_price <= 0.1:  # 10%范围内的均线
                level_type = '支撑' if ma_value < current_price else '阻力'
                all_levels.append((ma_value, f'{ma_key}均线', level_type))
    
    # 添加布林带
    if not pd.isna(latest.get('BB_Upper', np.nan)) and not pd.isna(latest.get('BB_Lower', np.nan)):
        bb_upper = latest['BB_Upper']
        bb_lower = latest['BB_Lower']
        bb_middle = latest.get('BB_Middle', np.nan)
        
        if abs(bb_upper - current_price) / current_price <= 0.1:
            all_levels.append((bb_upper, '布林上轨', '阻力'))
        if abs(bb_lower - current_price) / current_price <= 0.1:
            all_levels.append((bb_lower, '布林下轨', '支撑'))
        if not pd.isna(bb_middle) and abs(bb_middle - current_price) / current_price <= 0.1:
            level_type = '支撑' if bb_middle < current_price else '阻力'
            all_levels.append((bb_middle, '布林中轨', level_type))
    
    # 去重和排序
    # 按价格分组，合并相近的价位
    price_tolerance = current_price * 0.01  # 1%的容忍度
    grouped_levels = []
    
    if all_levels:
        all_levels.sort(key=lambda x: x[0])  # 按价格排序
        
        current_group = [all_levels[0]]
        for level in all_levels[1:]:
            if abs(level[0] - current_group[0][0]) <= price_tolerance:
                current_group.append(level)
            else:
                # 处理当前组
                avg_price = np.mean([l[0] for l in current_group])
                sources = list(set([l[1] for l in current_group]))
                types = list(set([l[2] for l in current_group]))
                grouped_levels.append((avg_price, ' + '.join(sources), '/'.join(types)))
                current_group = [level]
        
        # 处理最后一组
        if current_group:
            avg_price = np.mean([l[0] for l in current_group])
            sources = list(set([l[1] for l in current_group]))
            types = list(set([l[2] for l in current_group]))
            grouped_levels.append((avg_price, ' + '.join(sources), '/'.join(types)))
    
    # 分离支撑和阻力
    supports = [(price, source) for price, source, type_ in grouped_levels if '支撑' in type_ and price < current_price]
    resistances = [(price, source) for price, source, type_ in grouped_levels if '阻力' in type_ and price > current_price]
    
    # 排序：支撑从高到低，阻力从低到高
    supports.sort(key=lambda x: x[0], reverse=True)
    resistances.sort(key=lambda x: x[0])
    
    return {
        'supports': supports[:5],  # 最近的5个支撑位
        'resistances': resistances[:5],  # 最近的5个阻力位
        'current_price': current_price,
        'all_levels': grouped_levels
    }

st.set_page_config(page_title="期权策略决策系统", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
  .main-header { font-size: 2.2rem; font-weight: 800; color: #1f77b4; text-align: center; margin: 0.5rem 0 1.0rem; }
  .metric-card { color: #fff; padding: 0.9rem; border-radius: 8px; text-align:center; min-height: 140px; display: flex; flex-direction: column; justify-content: space-between; }
  .metric-pos { background: linear-gradient(135deg, #ff6b6b 0%, #c73866 100%); }
  .metric-neg { background: linear-gradient(135deg, #2fbf71 0%, #0d976c 100%); }
  .metric-neu { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
  .metric-val { font-size: 1.4rem; font-weight: 700; }
  .metric-lbl { font-size: 0.9rem; opacity: 0.95; }
  .metric-body { font-size:12px; line-height:1.35; margin-top:6px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🧭 期权策略决策系统（日线·五因子共振）</div>', unsafe_allow_html=True)

# 选择标的（与ETF技术分析一致）
st.sidebar.header("⚙️ 参数")
etf_options = list(ETF_CONFIG.keys())
sel_label = st.sidebar.selectbox("选择ETF标的", etf_options, index=etf_options.index("创业板ETF (159915)") if "创业板ETF (159915)" in etf_options else 0)
period = "daily"
days = st.sidebar.slider("历史数据天数", 120, 500, 250, step=10)

symbol = ETF_CONFIG[sel_label]
with st.spinner("加载数据..."):
    df = load_etf_data(symbol, period, days)
if df is None or df.empty:
    st.error("⚠️ 无法加载ETF数据，请稍后重试")
    st.stop()

df = calculate_technical_indicators(df)
latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) >= 2 else latest

# 计算支撑点和压力点分析
support_resistance = calculate_support_resistance(df)

# 五维信号计算规则
# 1) 趋势（MA）
ma_bull = (latest['收盘'] > latest['MA20']) and (latest['MA5'] > latest['MA10'] > latest['MA20'])
ma_bear = (latest['收盘'] < latest['MA20']) and (latest['MA5'] < latest['MA10'] < latest['MA20'])
ma_sig = 1 if ma_bull else (-1 if ma_bear else 0)

# 2) 动能（MACD）
macd_above0 = latest['MACD'] > 0
macd_bullish = latest['MACD'] > latest['MACD_Signal']
macd_below0 = latest['MACD'] < 0
macd_bearish = latest['MACD'] < latest['MACD_Signal']
macd_sig = 1 if (macd_above0 and macd_bullish) else (-1 if (macd_below0 and macd_bearish) else 0)

# 3) 位置（布林）
bb_mid = latest.get('BB_Middle', np.nan)
bb_up = latest.get('BB_Upper', np.nan)
bb_low = latest.get('BB_Lower', np.nan)
price = latest['收盘']

pos_long = (not np.isnan(bb_mid)) and (price > bb_mid) and (price <= bb_up)
pos_short = (not np.isnan(bb_mid)) and (price < bb_mid) and (price >= bb_low)
pos_neutral_extreme = (not np.isnan(bb_up) and price > bb_up) or (not np.isnan(bb_low) and price < bb_low)
pos_sig = 0 if pos_neutral_extreme else (1 if pos_long else (-1 if pos_short else 0))

# 4) 能量（量能）
vol_ma5 = latest.get('Volume_MA5', np.nan)
vol_ratio = (latest['成交量'] / vol_ma5) if vol_ma5 and not np.isnan(vol_ma5) and vol_ma5 != 0 else np.nan
is_up_day = latest['收盘'] >= latest['开盘']
energy_long = (not np.isnan(vol_ratio)) and (vol_ratio > 1.2) and is_up_day
energy_short = (not np.isnan(vol_ratio)) and (vol_ratio > 1.2) and (not is_up_day)
energy_sig = 1 if energy_long else (-1 if energy_short else 0)

# 5) 波动率（新增）
hv20_current = latest.get('HV20', np.nan)
hv20_prev = prev.get('HV20', np.nan) if len(df) >= 2 else np.nan
bb_width_current = latest.get('BB_Width', np.nan)
bb_width_ma5 = latest.get('BB_Width_MA5', np.nan)

# 判定波动率变化
hv_change = 0
bb_change = 0
if not pd.isna(hv20_current) and not pd.isna(hv20_prev):
    hv_change = 1 if hv20_current > hv20_prev * 1.05 else (-1 if hv20_current < hv20_prev * 0.95 else 0)
if not pd.isna(bb_width_current) and not pd.isna(bb_width_ma5):
    bb_change = 1 if bb_width_current > bb_width_ma5 * 1.1 else (-1 if bb_width_current < bb_width_ma5 * 0.9 else 0)

# 波动率信号（+1有利卖方，-1有利买方）
if hv_change > 0 or bb_change > 0:
    volatility_sig = 1  # 波动率增加，有利卖方
elif hv_change < 0 or bb_change < 0:
    volatility_sig = -1  # 波动率回落，有利买方
else:
    volatility_sig = 0  # 波动率平稳

# 总分（五维）
score = ma_sig + macd_sig + pos_sig + energy_sig + volatility_sig

# 卡片配色选择函数
def cls(sig: int) -> str:
    return "metric-pos" if sig > 0 else ("metric-neg" if sig < 0 else "metric-neu")

# 创建增强的K线图，包含支撑压力线
def create_enhanced_etf_chart(df: pd.DataFrame, title: str, support_resistance: dict) -> go.Figure | None:
    """
    创建包含支撑压力线的增强K线图
    """
    if df is None or df.empty:
        return None
    
    fig = go.Figure()
    
    # 添加K线
    fig.add_trace(go.Candlestick(
        x=df["日期"], 
        open=df["开盘"], 
        high=df["最高"], 
        low=df["最低"], 
        close=df["收盘"], 
        name="K线",
        increasing_line_color="red", 
        decreasing_line_color="green",
    ))
    
    # 添加均线
    fig.add_trace(go.Scatter(x=df["日期"], y=df["MA5"], mode="lines", name="MA5", line=dict(width=1, color='orange')))
    fig.add_trace(go.Scatter(x=df["日期"], y=df["MA10"], mode="lines", name="MA10", line=dict(width=1, color='blue')))
    fig.add_trace(go.Scatter(x=df["日期"], y=df["MA20"], mode="lines", name="MA20", line=dict(width=1, color='purple')))
    
    # 添加布林带
    fig.add_trace(go.Scatter(x=df["日期"], y=df["BB_Upper"], mode="lines", name="布林上轨", 
                           line=dict(dash="dash", width=1, color='gray'), opacity=0.7))
    fig.add_trace(go.Scatter(x=df["日期"], y=df["BB_Lower"], mode="lines", name="布林下轨", 
                           line=dict(dash="dash", width=1, color='gray'), opacity=0.7, 
                           fill="tonexty", fillcolor="rgba(128,128,128,0.1)"))
    
    # 添加支撑线
    if support_resistance and support_resistance.get('supports'):
        for i, (price, source) in enumerate(support_resistance['supports'][:3]):
            fig.add_hline(y=price, line_dash='solid', line_color='green', line_width=2, opacity=0.8,
                         annotation_text=f'S{i+1}: {price:.2f}', annotation_position='left')
    
    # 添加压力线
    if support_resistance and support_resistance.get('resistances'):
        for i, (price, source) in enumerate(support_resistance['resistances'][:3]):
            fig.add_hline(y=price, line_dash='solid', line_color='red', line_width=2, opacity=0.8,
                         annotation_text=f'R{i+1}: {price:.2f}', annotation_position='right')
    
    fig.update_layout(
        title=title, 
        xaxis_title="日期", 
        yaxis_title="价格", 
        height=600, 
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

# 期权策略盈亏图绘制函数
def create_strategy_payoff_chart(strategy_name: str, current_price: float) -> go.Figure:
    """
    创建期权策略盈亏图
    """
    # 价格范围：当前价格的±30%
    price_range = np.linspace(current_price * 0.7, current_price * 1.3, 100)
    
    fig = go.Figure()
    
    if "牛市看涨价差" in strategy_name or "Bull Call Spread" in strategy_name:
        # 牛市看涨价差：买入低行权价Call，卖出高行权价Call
        k1 = current_price * 0.98  # 买入Call行权价（略低于当前价）
        k2 = current_price * 1.05  # 卖出Call行权价（高于当前价）
        premium_paid = current_price * 0.02  # 净权利金支出
        
        payoff = np.where(price_range <= k1, -premium_paid,
                 np.where(price_range >= k2, (k2 - k1) - premium_paid,
                         (price_range - k1) - premium_paid))
        
        title = f"牛市看涨价差策略盈亏图\n买入{k1:.2f}Call，卖出{k2:.2f}Call"
        
    elif "熊市看跌价差" in strategy_name or "Bear Put Spread" in strategy_name:
        # 熊市看跌价差：买入高行权价Put，卖出低行权价Put
        k1 = current_price * 1.02  # 买入Put行权价（高于当前价）
        k2 = current_price * 0.95  # 卖出Put行权价（低于当前价）
        premium_paid = current_price * 0.02  # 净权利金支出
        
        payoff = np.where(price_range >= k1, -premium_paid,
                 np.where(price_range <= k2, (k1 - k2) - premium_paid,
                         (k1 - price_range) - premium_paid))
        
        title = f"熊市看跌价差策略盈亏图\n买入{k1:.2f}Put，卖出{k2:.2f}Put"
        
    elif "卖出看跌" in strategy_name or "Sell Put" in strategy_name:
        # 卖出看跌期权
        k = current_price * 0.95  # Put行权价
        premium_received = current_price * 0.02  # 收取权利金
        
        payoff = np.where(price_range >= k, premium_received,
                         premium_received - (k - price_range))
        
        title = f"卖出看跌期权策略盈亏图\n卖出{k:.2f}Put"
        
    elif "卖出看涨" in strategy_name or "Sell Call" in strategy_name:
        # 卖出看涨期权
        k = current_price * 1.05  # Call行权价
        premium_received = current_price * 0.02  # 收取权利金
        
        payoff = np.where(price_range <= k, premium_received,
                         premium_received - (price_range - k))
        
        title = f"卖出看涨期权策略盈亏图\n卖出{k:.2f}Call"
        
    elif "铁蝶" in strategy_name or "Iron Butterfly" in strategy_name:
        # 铁蝶式：卖出ATM Call/Put，买入OTM Call/Put保护
        atm = current_price
        otm_call = current_price * 1.05
        otm_put = current_price * 0.95
        net_premium = current_price * 0.015  # 净收取权利金
        
        payoff = np.where(price_range <= otm_put, 
                         net_premium - (otm_put - price_range),
                 np.where(price_range >= otm_call,
                         net_premium - (price_range - otm_call),
                         net_premium))
        
        title = f"铁蝶式策略盈亏图\n卖出{atm:.2f}跨式，买入{otm_put:.2f}Put/{otm_call:.2f}Call保护"
        
    elif "宽跨式" in strategy_name:
        if "卖出" in strategy_name or "Short" in strategy_name:
            # 卖出宽跨式
            call_strike = current_price * 1.05
            put_strike = current_price * 0.95
            net_premium = current_price * 0.025  # 净收取权利金
            
            payoff = np.where(price_range <= put_strike,
                             net_premium - (put_strike - price_range),
                     np.where(price_range >= call_strike,
                             net_premium - (price_range - call_strike),
                             net_premium))
            
            title = f"卖出宽跨式策略盈亏图\n卖出{put_strike:.2f}Put + {call_strike:.2f}Call"
        else:
            # 买入宽跨式
            call_strike = current_price * 1.05
            put_strike = current_price * 0.95
            net_premium = current_price * 0.025  # 净支付权利金
            
            payoff = np.where(price_range <= put_strike,
                             (put_strike - price_range) - net_premium,
                     np.where(price_range >= call_strike,
                             (price_range - call_strike) - net_premium,
                             -net_premium))
            
            title = f"买入宽跨式策略盈亏图\n买入{put_strike:.2f}Put + {call_strike:.2f}Call"
    else:
        # 默认：简单的线性盈亏
        payoff = np.zeros_like(price_range)
        title = "策略盈亏图"
    
    # 绘制盈亏线
    colors = ['green' if p >= 0 else 'red' for p in payoff]
    fig.add_trace(go.Scatter(
        x=price_range,
        y=payoff,
        mode='lines',
        name='策略盈亏',
        line=dict(width=3, color='blue'),
        fill='tozeroy',
        fillcolor='rgba(0,100,255,0.1)'
    ))
    
    # 添加盈亏平衡线
    fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.8)
    
    # 添加当前价格线
    fig.add_vline(x=current_price, line_dash='dot', line_color='orange', 
                  annotation_text=f'当前价格: {current_price:.2f}', 
                  annotation_position='top')
    
    # 找到盈亏平衡点
    zero_crossings = []
    for i in range(len(payoff)-1):
        if (payoff[i] <= 0 <= payoff[i+1]) or (payoff[i] >= 0 >= payoff[i+1]):
            if abs(payoff[i]) < abs(payoff[i+1]):
                zero_crossings.append(price_range[i])
            else:
                zero_crossings.append(price_range[i+1])
    
    # 标记盈亏平衡点
    for point in zero_crossings:
        fig.add_vline(x=point, line_dash='dashdot', line_color='purple', opacity=0.6,
                      annotation_text=f'平衡点: {point:.2f}', annotation_position='bottom')
    
    fig.update_layout(
        title=title,
        xaxis_title='标的价格',
        yaxis_title='策略盈亏',
        height=400,
        showlegend=False,
        hovermode='x unified',
        plot_bgcolor='rgba(240,240,240,0.1)'
    )
    
    return fig

# —— 将“决策建议”放在最上方（标题下、卡片上） ——
advice = ""
explain = ""
extra = []

if score >= 4:
    advice = "牛市看涨价差 + 卖出看跌 (Bull Call Spread + Sell Put)"
    explain = "极强多头信号+高波动率环境，组合策略可同时受益于方向性和波动率。"
    extra = [
        "🎯 **入场策略**：买入平值/轻度虚值Call价差，同时卖出虚值Put收取高权利金",
        "💰 **仓位管理**：单次投入不超过总资金的10%，价差与卖Put资金分配3:2",
        "⚠️ **风险控制**：设置15%止损线，波动率回落超过20%时对卖Put进行对冲",
        "🚨 **善后措施**：若被Put指派，可寻机卖出Call降低持仓成本；趋势逆转时立即平仓所有头寸"
    ]
elif score <= -4:
    advice = "熊市看跌价差 + 卖出看涨 (Bear Put Spread + Sell Call)"
    explain = "极强空头信号+高波动率环境，组合策略对冲下跌风险同时收取高权利金。"
    extra = [
        "🎯 **入场策略**：买入平值/轻度虚值Put价差，同时卖出虚值Call收取权利金",
        "💰 **仓位管理**：严格控制单次投入，不超过总资金的12%，预留追保资金",
        "⚠️ **风险控制**：反弹至MA20附近即平仓，设置20%止损线",
        "🚨 **善后措施**：若被Call指派，可考虑交割后再卖Put；趋势反转时快速止损"
    ]
elif score == 3:
    advice = "牛市看涨价差 (Bull Call Spread)"
    explain = "较强多头信号，但波动率环境不是特别有利，选择价差策略控制风险。"
    extra = [
        "🎯 **入场策略**：买入平值/轻度虚值Call，卖出更高行权价Call",
        "💰 **成本控制**：选择流动性好的合约，价差成本不超过单笔资金的8%",
        "⚠️ **盈亏管理**：达到最大盈利的70%时平仓，亏损达50%时止损",
        "🚨 **善后措施**：若突破卖出Call行权价，可补买Call对冲或直接平仓"
    ]
elif score == 2:
    advice = "卖出看跌期权 (Sell Put)"
    explain = "温和多头信号，适合通过卖出Put赚取时间价值，被指派可相对低价接货。"
    extra = [
        "🎯 **入场策略**：卖出虚值度在Δ=0.2-0.3的Put期权，确保有足够安全边际",
        "💰 **保证金管理**：预留足够的保证金，建议为名义金额的50%以上",
        "⚠️ **风险监控**：波动率急升超过30%时考虑买入Put对冲，转为Collar策略",
        "🚨 **善后措施**：被指派后可寻机卖出Call降低成本，或设置止损价位防范继续下跌"
    ]
elif score == -2:
    advice = "卖出看涨期权 (Sell Call)"
    explain = "温和空头信号，适合卖出Call赚取时间价值，但需防范趋势逆转风险。"
    extra = [
        "🎯 **入场策略**：在反弹至均线附近卖出Call，选择Δ=0.2-0.3的虚值合约",
        "💰 **资金管理**：严格限制单次卖出数量，预留对冲资金防范突破",
        "⚠️ **严格止损**：设置15%止损线，突破关键技术位立即平仓",
        "🚨 **善后措施**：被指派后在高位交割，可考虑再卖Put做双卖策略"
    ]
elif score == -3:
    advice = "熊市看跌价差 (Bear Put Spread)"
    explain = "较强空头信号，通过价差策略获取下跌收益同时控制风险。"
    extra = [
        "🎯 **入场策略**：买入平值/轻度虚值Put，卖出更低行权价Put构建价差",
        "💰 **成本优化**：选择残值较高的合约，降低建仓成本提高性价比",
        "⚠️ **盈亏管理**：目标盈利为最大盈利的60-70%，亏损达40%时止损",
        "🚨 **善后措施**：趋势反转时快速平仓，可考虑转为相反方向的价差策略"
    ]
else:  # -1 ~ +1
    # 根据波动率分量精调策略
    if volatility_sig == 1:
        advice = "卖出宽跨式 / 铁蝶式 (Short Strangle / Iron Butterfly)"
        explain = "方向不明但高波动率环境，适合通过卖方策略赚取波动率回归收益。"
        extra = [
            "🎯 **入场策略**：卖出跨式（同时卖Call和Put）或铁蝶式（加保护腿）",
            "💰 **保证金管理**：确保有足够保证金，预留双向突破时的对冲资金",
            "⚠️ **区间监控**：设置上下边界，任一方向突破边界即及时对冲",
            "🚨 **善后措施**：突破区间后可调整为Delta中性策略，或转为单向价差"
        ]
    elif volatility_sig == -1:
        advice = "买入宽跨式 / 长期权 (Long Strangle / Long Options)"
        explain = "方向不明但低波动率环境，买入便宜期权等待方向性突破和波动率回升。"
        extra = [
            "🎯 **入场策略**：买入跨式（同时买Call和Put）或单买高Gamma期权",
            "💰 **成本控制**：利用低波动率阶段低成本建仓，不超过单笔资金的10%",
            "⚠️ **时间管理**：选择残值较长的合约，给予充足的等待时间",
            "🚨 **善后措施**：方向确定后可调整为单向策略，及时获取方向性收益"
        ]
    else:
        advice = "铁蝶式价差 (Iron Butterfly)"
        explain = "方向不明且波动率平稳，选择中性策略赚取稳定的时间价值衰减。"
        extra = [
            "🎯 **入场策略**：在当前价格附近构建铁蝶式，卖出ATM同时买入OTM保护",
            "💰 **风险收益**：最大风险可控，最大收益为收取的净权利金",
            "⚠️ **区间管理**：价格需维持在上下保护腿之间，关注关键技术位",
            "🚨 **善后措施**：到期日价格偏离中心时，可考虑交割或对冲操作"
        ]

st.markdown("---")
st.subheader("🎯 决策建议（置顶）")

# 使用列布局：左侧显示策略信息，右侧显示盈亏图
col_strategy, col_chart = st.columns([1.2, 1])

with col_strategy:
    st.markdown(f"**标的**：{sel_label}  |  **总信号分**：{score:+d}")
    st.markdown(f"**核心策略**：{advice}")
    st.markdown(f"**策略说明**：{explain}")
    if extra:
        st.markdown("**执行要点**：")
        for x in extra:  # 显示所有执行要点，不再折叠
            st.markdown(f"- {x}")

with col_chart:
    try:
        # 绘制对应策略的盈亏图
        payoff_fig = create_strategy_payoff_chart(advice, latest['收盘'])
        st.plotly_chart(payoff_fig, use_container_width=True, key="strategy_payoff_chart")
    except Exception as e:
        st.info(f"盈亏图暂时无法显示: {e}")

# 展示指标与信号（五维+总分）
c1, c2, c3, c4, c5, c6 = st.columns(6)

ma_state = "多头" if ma_sig == 1 else ("空头" if ma_sig == -1 else "震荡")
macd_state = ("上方" if macd_above0 else "下方" if macd_below0 else "附近") + "/" + ("多头" if macd_bullish else "空头" if macd_bearish else "中性")
pos_state = ("中轨~上轨" if pos_long else ("下轨~中轨" if pos_short else ("极端区外" if pos_neutral_extreme else "中性")))
vol_ratio_disp = f"{vol_ratio:.2f}" if isinstance(vol_ratio, (int, float, np.floating)) and not np.isnan(vol_ratio) else "-"

with c1:
    st.markdown(
        f"""
        <div class='metric-card {cls(ma_sig)}'>
            <div class='metric-val'>{ma_sig:+d}｜{ma_state}</div>
            <div class='metric-lbl'>趋势(MA)</div>
            <div class='metric-body'>
                收盘 {latest['收盘']:.2f}<br/>
                MA5 {latest['MA5']:.2f} ｜ MA10 {latest['MA10']:.2f}<br/>
                MA20 {latest['MA20']:.2f}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class='metric-card {cls(macd_sig)}'>
            <div class='metric-val'>{macd_sig:+d}｜{macd_state}</div>
            <div class='metric-lbl'>动能(MACD)</div>
            <div class='metric-body'>
                MACD {latest['MACD']:.4f}<br/>
                Signal {latest['MACD_Signal']:.4f}<br/>
                Hist {latest['MACD_Histogram']:.4f}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class='metric-card {cls(pos_sig)}'>
            <div class='metric-val'>{pos_sig:+d}｜{pos_state}</div>
            <div class='metric-lbl'>位置(BOLL)</div>
            <div class='metric-body'>
                收盘 {price:.2f}<br/>
                中轨 {bb_mid if np.isnan(bb_mid) else f'{bb_mid:.2f}'} ｜ 上轨 {bb_up if np.isnan(bb_up) else f'{bb_up:.2f}'}<br/>
                下轨 {bb_low if np.isnan(bb_low) else f'{bb_low:.2f}'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div class='metric-card {cls(energy_sig)}'>
            <div class='metric-val'>{energy_sig:+d}｜{'阳' if is_up_day else '阴'}</div>
            <div class='metric-lbl'>能量(Volume)</div>
            <div class='metric-body'>
                量 {int(latest['成交量']) if not np.isnan(latest['成交量']) else '-'}<br/>
                MA5 {int(vol_ma5) if vol_ma5 and not np.isnan(vol_ma5) else '-'} ｜ 量比 {vol_ratio_disp}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c5:
    volatility_state = "有利卖方" if volatility_sig == 1 else ("有利买方" if volatility_sig == -1 else "中性")
    hv_disp = f"{hv20_current:.1f}%" if isinstance(hv20_current, (int, float, np.floating)) and not np.isnan(hv20_current) else "-"
    bb_width_disp = f"{bb_width_current:.2f}%" if isinstance(bb_width_current, (int, float, np.floating)) and not np.isnan(bb_width_current) else "-"
    
    st.markdown(
        f"""
        <div class='metric-card {cls(volatility_sig)}'>
            <div class='metric-val'>{volatility_sig:+d}｜{volatility_state}</div>
            <div class='metric-lbl'>波动率(HV)</div>
            <div class='metric-body'>
                HV20 {hv_disp}<br/>
                布林宽度 {bb_width_disp}<br/>
                {'HV↑' if hv_change > 0 else ('HV↓' if hv_change < 0 else 'HV↔')} / {'BB↑' if bb_change > 0 else ('BB↓' if bb_change < 0 else 'BB↔')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c6:
    total_cls = cls(score)
    st.markdown(
        f"""
        <div class='metric-card {total_cls}'>
            <div class='metric-val'>{score:+d}</div>
            <div class='metric-lbl'>总信号分</div>
            <div class='metric-body'>
                MA {ma_sig:+d} ｜ MACD {macd_sig:+d}<br/>
                BOLL {pos_sig:+d} ｜ VOL {energy_sig:+d}<br/>
                HV {volatility_sig:+d}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 在卡片下方加入标的K线主图
st.markdown("---")
st.subheader(f"{sel_label} · 日线主图（含支撑压力位）")
main_fig = create_enhanced_etf_chart(df, f"{sel_label} 技术分析图表", support_resistance)
if main_fig:
    st.plotly_chart(main_fig, use_container_width=True)

# 支撑点和压力点分析
st.markdown("---")
st.subheader("🎯 支撑压力点分析")

if support_resistance and support_resistance.get('supports') or support_resistance.get('resistances'):
    col_support, col_resistance = st.columns(2)
    
    with col_support:
        st.markdown("#### 📈 关键支撑位")
        supports = support_resistance.get('supports', [])
        if supports:
            for i, (price, source) in enumerate(supports, 1):
                current_price = support_resistance.get('current_price', latest['收盘'])
                distance_pct = ((current_price - price) / current_price) * 100
                st.markdown(
                    f"**S{i}**: {price:.2f} ({source})  "
                    f"📍 距离当前价格 **{distance_pct:.1f}%**"
                )
        else:
            st.info("暂无明显支撑位")
    
    with col_resistance:
        st.markdown("#### 📉 关键压力位")
        resistances = support_resistance.get('resistances', [])
        if resistances:
            for i, (price, source) in enumerate(resistances, 1):
                current_price = support_resistance.get('current_price', latest['收盘'])
                distance_pct = ((price - current_price) / current_price) * 100
                st.markdown(
                    f"**R{i}**: {price:.2f} ({source})  "
                    f"📍 距离当前价格 **+{distance_pct:.1f}%**"
                )
        else:
            st.info("暂无明显压力位")
    
    # 期权策略建议基于支撑压力位
    st.markdown("#### 🎲 基于支撑压力位的期权策略建议")
    
    current_price = support_resistance.get('current_price', latest['收盘'])
    supports = support_resistance.get('supports', [])
    resistances = support_resistance.get('resistances', [])
    
    strategy_suggestions = []
    
    # 分析当前价格与支撑压力的关系
    if supports:
        nearest_support = supports[0][0]  # 最近的支撑位
        support_distance = ((current_price - nearest_support) / current_price) * 100
        
        if support_distance <= 3:  # 接近支撑位（3%以内）
            strategy_suggestions.append(
                f"💡 **接近关键支撑{nearest_support:.2f}**：可考虑卖出虚值Put策略，行权价设在{nearest_support:.2f}附近"
            )
            strategy_suggestions.append(
                f"⚠️ **风险提示**：若跌破支撑位，应及时止损或买入Put对冲"
            )
    
    if resistances:
        nearest_resistance = resistances[0][0]  # 最近的压力位
        resistance_distance = ((nearest_resistance - current_price) / current_price) * 100
        
        if resistance_distance <= 3:  # 接近压力位（3%以内）
            strategy_suggestions.append(
                f"💡 **接近关键压力{nearest_resistance:.2f}**：可考虑卖出虚值Call策略，行权价设在{nearest_resistance:.2f}附近"
            )
            strategy_suggestions.append(
                f"⚠️ **风险提示**：若突破压力位，应及时止损或买入Call对冲"
            )
    
    # 区间交易策略
    if supports and resistances:
        support_price = supports[0][0]
        resistance_price = resistances[0][0]
        range_pct = ((resistance_price - support_price) / current_price) * 100
        
        if range_pct >= 5:  # 区间足够大（5%以上）
            strategy_suggestions.append(
                f"🎯 **区间交易策略**：在{support_price:.2f}-{resistance_price:.2f}区间内，"
                f"可构建宽跨式卖方策略（卖出{support_price:.2f}Put + {resistance_price:.2f}Call）"
            )
    
    if strategy_suggestions:
        for suggestion in strategy_suggestions:
            st.markdown(f"- {suggestion}")
    else:
        st.info("当前价格位置暂无特别的支撑压力位策略建议")
else:
    st.info("支撑压力分析数据不足，建议增加历史数据天数")

# 核心技术指标表格
st.subheader("📋 核心技术指标与含义（含判定规则与结果）")

def _fmt(val, nd=2):
    try:
        if pd.isna(val):
            return "-"
        return f"{float(val):.{nd}f}"
    except Exception:
        return str(val)

# 关键规则判定文本
ma_rule = "收盘 > MA20 且 MA5 > MA10 > MA20"
ma_result_base = "多头(满足)" if ma_bull else ("空头(满足)" if ma_bear else "中性")
ma_emoji = "🔥" if ma_bull else ("🧊" if ma_bear else "⚪")
ma_result = f"{ma_emoji} {ma_result_base}"
ma_num = ma_sig

macd_rule = "MACD > 0（零轴上）且 MACD > MACD_Signal（DIF>DEA）"
macd_base = "多头(满足)" if (macd_above0 and macd_bullish) else ("空头(满足)" if (macd_below0 and macd_bearish) else "中性")
macd_emoji = "🔥" if (macd_above0 and macd_bullish) else ("🧊" if (macd_below0 and macd_bearish) else "⚪")
macd_result = f"{macd_emoji} {macd_base}"
macd_num = macd_sig

boll_rule = "收盘 > 中轨 且 位于中轨~上轨；或 收盘 < 中轨 且 位于下轨~中轨"
if pos_long:
    boll_base = "偏多(中轨~上轨)"; boll_emoji = "🔥"; boll_num = 1
elif pos_short:
    boll_base = "偏空(下轨~中轨)"; boll_emoji = "🧊"; boll_num = -1
elif pos_neutral_extreme:
    boll_base = "极端区(带外)"; boll_emoji = "🚨"; boll_num = 0
else:
    boll_base = "中性"; boll_emoji = "⚪"; boll_num = 0
boll_result = f"{boll_emoji} {boll_base}"

vol_rule = "量比>1.2（放量）且 收阳 为多头；量比>1.2 且 收阴 为空头"
if energy_long:
    vol_base = "多头放量(满足)"; vol_emoji = "🔥"; vol_num = 1
elif energy_short:
    vol_base = "空头放量(满足)"; vol_emoji = "🧊"; vol_num = -1
else:
    vol_base = "中性/量平淡"; vol_emoji = "⚪"; vol_num = 0
vol_result = f"{vol_emoji} {vol_base}"

# RSI判定
rsi_value = latest.get('RSI', np.nan)
rsi_rule = "RSI < 30 超卖(偏多)；RSI > 70 超买(偏空)；30-70 中性"
rsi_base = "中性"; rsi_emoji = "⚪"; rsi_num = 0
if not pd.isna(rsi_value):
    if rsi_value < 30:
        rsi_base = "超卖(偏多)"; rsi_emoji = "🔥"; rsi_num = 1
    elif rsi_value > 70:
        rsi_base = "超买(偏空)"; rsi_emoji = "🧊"; rsi_num = -1
    else:
        rsi_base = "中性"; rsi_emoji = "⚪"; rsi_num = 0
rsi_result = f"{rsi_emoji} {rsi_base}"

# KDJ判定（随机指标）
k_value = latest.get('K', np.nan)
d_value = latest.get('D', np.nan)
j_value = latest.get('J', np.nan)

# KDJ超买超卖判定
kdj_rule = "K/D < 20 超卖(偏多)；K/D > 80 超买(偏空)；20-80 中性；金叉/死叉确认"
kdj_base = "中性"; kdj_emoji = "⚪"; kdj_num = 0

if not pd.isna(k_value) and not pd.isna(d_value):
    # 判断超买超卖
    if k_value < 20 and d_value < 20:
        kdj_base = "超卖(偏多)"; kdj_emoji = "🔥"; kdj_num = 1
    elif k_value > 80 and d_value > 80:
        kdj_base = "超买(偏空)"; kdj_emoji = "🧊"; kdj_num = -1
    else:
        # 判断金叉死叉（需要前一日数据）
        if len(df) >= 2:
            prev_k = prev.get('K', np.nan)
            prev_d = prev.get('D', np.nan)
            
            if not pd.isna(prev_k) and not pd.isna(prev_d):
                # 金叉：K线从下方穿越D线
                if prev_k <= prev_d and k_value > d_value:
                    if k_value < 20:  # 低位金叉
                        kdj_base = "低位金叉(强买入)"; kdj_emoji = "🔥"; kdj_num = 1
                    else:
                        kdj_base = "金叉(偏多)"; kdj_emoji = "🔥"; kdj_num = 1
                # 死叉：K线从上方穿越D线
                elif prev_k >= prev_d and k_value < d_value:
                    if k_value > 80:  # 高位死叉
                        kdj_base = "高位死叉(强卖出)"; kdj_emoji = "🧊"; kdj_num = -1
                    else:
                        kdj_base = "死叉(偏空)"; kdj_emoji = "🧊"; kdj_num = -1
                else:
                    # 无交叉，判断当前位置
                    if k_value > d_value:
                        kdj_base = "K>D(偏多)"; kdj_emoji = "🔥"; kdj_num = 1
                    else:
                        kdj_base = "K<D(偏空)"; kdj_emoji = "🧊"; kdj_num = -1

kdj_result = f"{kdj_emoji} {kdj_base}"

# KDJ背离分析
def detect_kdj_divergence(df: pd.DataFrame, window: int = 10) -> dict:
    """
    检测KDJ背离现象
    """
    if df is None or len(df) < window + 5:
        return {"type": "无背离", "strength": 0, "description": "数据不足"}
    
    # 获取最近的数据
    recent_data = df.tail(window + 5)
    prices = recent_data['收盘'].values
    k_values = recent_data.get('K', pd.Series([np.nan] * len(recent_data))).values
    d_values = recent_data.get('D', pd.Series([np.nan] * len(recent_data))).values
    
    # 检查数据有效性
    if np.isnan(k_values).all() or np.isnan(d_values).all():
        return {"type": "无背离", "strength": 0, "description": "KDJ数据无效"}
    
    # 寻找价格的高点和低点
    price_highs = []
    price_lows = []
    kdj_highs = []
    kdj_lows = []
    
    for i in range(2, len(prices) - 2):
        # 寻找价格高点
        if prices[i] > prices[i-1] and prices[i] > prices[i+1] and prices[i] > prices[i-2] and prices[i] > prices[i+2]:
            price_highs.append((i, prices[i]))
            if not np.isnan(k_values[i]):
                kdj_highs.append((i, k_values[i]))
        
        # 寻找价格低点
        if prices[i] < prices[i-1] and prices[i] < prices[i+1] and prices[i] < prices[i-2] and prices[i] < prices[i+2]:
            price_lows.append((i, prices[i]))
            if not np.isnan(k_values[i]):
                kdj_lows.append((i, k_values[i]))
    
    # 检测顶背离（价格创新高，KDJ不创新高）
    if len(price_highs) >= 2 and len(kdj_highs) >= 2:
        # 取最近的两个高点
        recent_price_highs = sorted(price_highs, key=lambda x: x[0])[-2:]
        recent_kdj_highs = sorted(kdj_highs, key=lambda x: x[0])[-2:]
        
        if (len(recent_price_highs) >= 2 and len(recent_kdj_highs) >= 2 and
            recent_price_highs[1][1] > recent_price_highs[0][1] and  # 价格创新高
            recent_kdj_highs[1][1] < recent_kdj_highs[0][1]):       # KDJ不创新高
            
            # 计算背离强度
            price_diff = (recent_price_highs[1][1] - recent_price_highs[0][1]) / recent_price_highs[0][1] * 100
            kdj_diff = recent_kdj_highs[0][1] - recent_kdj_highs[1][1]
            
            if price_diff > 2 and kdj_diff > 5:  # 显著背离
                return {
                    "type": "顶背离", 
                    "strength": -1, 
                    "description": f"价格涨{price_diff:.1f}%但KDJ回落{kdj_diff:.1f}点(强卖出信号)"
                }
            elif price_diff > 1 and kdj_diff > 3:  # 轻微背离
                return {
                    "type": "顶背离", 
                    "strength": -1, 
                    "description": f"价格涨{price_diff:.1f}%但KDJ回落{kdj_diff:.1f}点(卖出信号)"
                }
    
    # 检测底背离（价格创新低，KDJ不创新低）
    if len(price_lows) >= 2 and len(kdj_lows) >= 2:
        # 取最近的两个低点
        recent_price_lows = sorted(price_lows, key=lambda x: x[0])[-2:]
        recent_kdj_lows = sorted(kdj_lows, key=lambda x: x[0])[-2:]
        
        if (len(recent_price_lows) >= 2 and len(recent_kdj_lows) >= 2 and
            recent_price_lows[1][1] < recent_price_lows[0][1] and   # 价格创新低
            recent_kdj_lows[1][1] > recent_kdj_lows[0][1]):        # KDJ不创新低
            
            # 计算背离强度
            price_diff = (recent_price_lows[0][1] - recent_price_lows[1][1]) / recent_price_lows[0][1] * 100
            kdj_diff = recent_kdj_lows[1][1] - recent_kdj_lows[0][1]
            
            if price_diff > 2 and kdj_diff > 5:  # 显著背离
                return {
                    "type": "底背离", 
                    "strength": 1, 
                    "description": f"价格跌{price_diff:.1f}%但KDJ上升{kdj_diff:.1f}点(强买入信号)"
                }
            elif price_diff > 1 and kdj_diff > 3:  # 轻微背离
                return {
                    "type": "底背离", 
                    "strength": 1, 
                    "description": f"价格跌{price_diff:.1f}%但KDJ上升{kdj_diff:.1f}点(买入信号)"
                }
    
    return {"type": "无背离", "strength": 0, "description": "未发现明显背离现象"}

# 执行背离分析
kdj_divergence = detect_kdj_divergence(df)
divergence_type = kdj_divergence["type"]
divergence_strength = kdj_divergence["strength"]
divergence_desc = kdj_divergence["description"]

# 背离分析结果
divergence_rule = "顶背离：价格新高但KDJ不新高(卖出信号)；底背离：价格新低但KDJ不新低(买入信号)"
if divergence_type == "顶背离":
    divergence_emoji = "🧊"
    divergence_result = f"{divergence_emoji} {divergence_type}({divergence_desc})"
elif divergence_type == "底背离":
    divergence_emoji = "🔥"
    divergence_result = f"{divergence_emoji} {divergence_type}({divergence_desc})"
else:
    divergence_emoji = "⚪"
    divergence_result = f"{divergence_emoji} {divergence_type}({divergence_desc})"

# ADX判定（趋势强度指标）
adx_value = latest.get('ADX', np.nan)
di_plus = latest.get('DI_plus', np.nan)
di_minus = latest.get('DI_minus', np.nan)
adx_rule = "ADX < 25 震荡趋势；ADX > 25 有趋势；ADX > 40 强趋势；结合+DI和-DI判定方向"
adx_base = "中性"; adx_emoji = "⚪"; adx_num = 0
if not pd.isna(adx_value):
    if adx_value < 25:
        adx_base = "震荡趋势(无明确方向)"; adx_emoji = "⚪"; adx_num = 0
    elif adx_value > 40:
        # 强趋势，判断方向
        if not pd.isna(di_plus) and not pd.isna(di_minus):
            if di_plus > di_minus:
                adx_base = "强上升趋势"; adx_emoji = "🔥"; adx_num = 1
            else:
                adx_base = "强下降趋势"; adx_emoji = "🧊"; adx_num = -1
        else:
            adx_base = "强趋势(方向待定)"; adx_emoji = "🚨"; adx_num = 0
    else:  # 25 <= adx <= 40
        # 中等趋势，判断方向
        if not pd.isna(di_plus) and not pd.isna(di_minus):
            if di_plus > di_minus:
                adx_base = "中等上升趋势"; adx_emoji = "🔥"; adx_num = 1
            else:
                adx_base = "中等下降趋势"; adx_emoji = "🧊"; adx_num = -1
        else:
            adx_base = "中等趋势(方向待定)"; adx_emoji = "⚪"; adx_num = 0
adx_result = f"{adx_emoji} {adx_base}"

# 波动率显示用变量（使用五维信号中的数据）
vol_volatility_rule = "历史波动率上升+布林带放宽为波动率增加；反之为波动率回落"
if volatility_sig == 1:
    vol_volatility_base = "波动率增加(对卖方有利)"; vol_volatility_emoji = "🔥"
elif volatility_sig == -1:
    vol_volatility_base = "波动率回落(对买方有利)"; vol_volatility_emoji = "🧊"
else:
    vol_volatility_base = "波动率平稳"; vol_volatility_emoji = "⚪"
vol_volatility_result = f"{vol_volatility_emoji} {vol_volatility_base}"

indicators_rows = [
    {"🔎": "💰", "指标": "收盘价", "数值": _fmt(latest.get("收盘")), "判定规则": "-", "判定结果": "-", "数值评分": ""},
    {"🔎": "🏁", "指标": "开盘价", "数值": _fmt(latest.get("开盘")), "判定规则": "-", "判定结果": "-", "数值评分": ""},
    {"🔎": "📈", "指标": "MA5", "数值": _fmt(latest.get("MA5")), "判定规则": ma_rule, "判定结果": ma_result, "数值评分": ma_num},
    {"🔎": "📈", "指标": "MA10", "数值": _fmt(latest.get("MA10")), "判定规则": ma_rule, "判定结果": ma_result, "数值评分": ma_num},
    {"🔎": "📈", "指标": "MA20", "数值": _fmt(latest.get("MA20")), "判定规则": ma_rule, "判定结果": ma_result, "数值评分": ma_num},
    {"🔎": "⚡", "指标": "MACD", "数值": _fmt(latest.get("MACD"), 4), "判定规则": macd_rule, "判定结果": macd_result, "数值评分": macd_num},
    {"🔎": "⚡", "指标": "Signal(DEA)", "数值": _fmt(latest.get("MACD_Signal"), 4), "判定规则": macd_rule, "判定结果": macd_result, "数值评分": macd_num},
    {"🔎": "⚡", "指标": "Histogram", "数值": _fmt(latest.get("MACD_Histogram"), 4), "判定规则": macd_rule, "判定结果": macd_result, "数值评分": macd_num},
    {"🔎": "🎯", "指标": "布林中轨", "数值": _fmt(bb_mid), "判定规则": boll_rule, "判定结果": boll_result, "数值评分": boll_num},
    {"🔎": "🎯", "指标": "布林上轨", "数值": _fmt(bb_up), "判定规则": boll_rule, "判定结果": boll_result, "数值评分": boll_num},
    {"🔎": "🎯", "指标": "布林下轨", "数值": _fmt(bb_low), "判定规则": boll_rule, "判定结果": boll_result, "数值评分": boll_num},
    {"🔎": "📊", "指标": "成交量", "数值": _fmt(latest.get("成交量"), 0), "判定规则": vol_rule, "判定结果": vol_result, "数值评分": vol_num},
    {"🔎": "📊", "指标": "量MA5", "数值": _fmt(vol_ma5, 0), "判定规则": vol_rule, "判定结果": vol_result, "数值评分": vol_num},
    {"🔎": "📊", "指标": "量比", "数值": (vol_ratio_disp if isinstance(vol_ratio_disp, str) else _fmt(vol_ratio, 2)), "判定规则": vol_rule, "判定结果": vol_result, "数值评分": vol_num},
    {"🔎": "🌊", "指标": "RSI(14)", "数值": _fmt(rsi_value), "判定规则": rsi_rule, "判定结果": rsi_result, "数值评分": rsi_num},
    {"🔎": "🌀", "指标": "KDJ-K值", "数值": _fmt(k_value), "判定规则": kdj_rule, "判定结果": kdj_result, "数值评分": kdj_num},
    {"🔎": "🌀", "指标": "KDJ-D值", "数值": _fmt(d_value), "判定规则": kdj_rule, "判定结果": kdj_result, "数值评分": kdj_num},
    {"🔎": "🌀", "指标": "KDJ-J值", "数值": _fmt(j_value), "判定规则": kdj_rule, "判定结果": kdj_result, "数值评分": kdj_num},
    {"🔎": "🔮", "指标": "KDJ背离分析", "数值": divergence_type, "判定规则": divergence_rule, "判定结果": divergence_result, "数值评分": divergence_strength},
    {"🔎": "⚡", "指标": "ADX(趋势强度)", "数值": _fmt(adx_value), "判定规则": adx_rule, "判定结果": adx_result, "数值评分": adx_num},
    {"🔎": "⚡", "指标": "+DI(上升力度)", "数值": _fmt(di_plus), "判定规则": adx_rule, "判定结果": adx_result, "数值评分": adx_num},
    {"🔎": "⚡", "指标": "-DI(下降力度)", "数值": _fmt(di_minus), "判定规则": adx_rule, "判定结果": adx_result, "数值评分": adx_num},
    {"🔎": "🌪", "指标": "历史波动率HV20", "数值": f"{_fmt(hv20_current)}%", "判定规则": vol_volatility_rule, "判定结果": vol_volatility_result, "数值评分": volatility_sig},
    {"🔎": "🌪", "指标": "布林带宽度", "数值": f"{_fmt(bb_width_current)}%", "判定规则": vol_volatility_rule, "判定结果": vol_volatility_result, "数值评分": volatility_sig},
]

ind_df = pd.DataFrame(indicators_rows)

# 新增：量价关系判定
prev_close = prev.get("收盘", np.nan)
prev_vol = prev.get("成交量", np.nan)
vol_price_rule = "上涨且放量为强；下跌且放量为弱；缩量则为弱确认"
vol_price_base = "中性"; vol_price_emoji = "⚪"; vol_price_num = 0
if not pd.isna(latest.get("收盘")) and not pd.isna(prev_close) and not pd.isna(latest.get("成交量")) and not pd.isna(prev_vol):
    up = latest["收盘"] >= prev_close
    vol_up = latest["成交量"] > prev_vol
    if up and vol_up:
        vol_price_base = "价涨量增（强确认）"; vol_price_emoji = "🔥"; vol_price_num = 1
    elif (not up) and vol_up:
        vol_price_base = "价跌量增（弱势/风险）"; vol_price_emoji = "🧊"; vol_price_num = -1
    elif up and (not vol_up):
        vol_price_base = "价涨量缩（上行动能弱）"; vol_price_emoji = "⚪"; vol_price_num = 0
    elif (not up) and (not vol_up):
        vol_price_base = "价跌量缩（下行动能弱）"; vol_price_emoji = "⚪"; vol_price_num = 0

ind_df = pd.concat([
    ind_df,
    pd.DataFrame([{ "🔎": "📉", "指标": "量价关系", "数值": f"收盘 {'↑' if (not pd.isna(prev_close) and latest['收盘']>=prev_close) else '↓'} / 成交量 {'↑' if (not pd.isna(prev_vol) and latest['成交量']>prev_vol) else '↓'}", "判定规则": vol_price_rule, "判定结果": f"{vol_price_emoji} {vol_price_base}", "数值评分": vol_price_num }])
], ignore_index=True)

# 条件渲染：根据判定结果给行着色

def _row_style(row: pd.Series):
    text = str(row.get("判定结果", ""))
    if ("🔥" in text) or ("多头" in text) or ("偏多" in text) or ("强确认" in text):
        color = "rgba(255, 107, 107, 0.12)"  # 红：积极
    elif ("🧊" in text) or ("空头" in text) or ("偏空" in text) or ("弱势" in text):
        color = "rgba(47, 191, 113, 0.12)"   # 绿：消极
    elif ("🚨" in text) or ("极端" in text):
        color = "rgba(255, 193, 7, 0.15)"    # 黄：极端
    else:
        color = "rgba(102, 126, 234, 0.10)"  # 紫：中性
    return [f"background-color: {color}"] * len(row)

styled = (
    ind_df.style
        .apply(_row_style, axis=1)
        .set_properties(subset=["判定结果", "数值评分"], **{"font-weight": "600"})
)

# 去除滚动条：使用 HTML 渲染
try:
    styled = styled.hide(axis='index')
except Exception:
    try:
        styled = styled.hide_index()
    except Exception:
        pass

table_css = """
<style>
  table { width: 100% !important; }
  thead th { position: sticky; top: 0; background: #f8f9fa; }
  td, th { text-align: left; }
  td:nth-child(6), th:nth-child(6) { text-align: center; }
</style>
"""

# 添加下载功能
st.markdown("#### 📥 数据下载")
col1, col2, col3 = st.columns([1, 1, 3])

# 准备下载用的数据（去除emoji，便于Excel处理）
download_df = ind_df.copy()
download_df['类别'] = download_df['🔎']
download_df = download_df.drop('🔎', axis=1)
# 添加当前时间和标的信息
current_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
download_df.insert(0, '分析时间', current_time)
download_df.insert(1, '标的名称', sel_label)
download_df.insert(2, '总信号分', score)

# 准备AI分析用的文本数据
copy_text = f"""请基于以下期权策略技术分析数据，推荐最适合的期权交易策略：

【分析对象】{sel_label}
【分析时间】{current_time}
【总信号分】{score:+d} 分（范围：-5到+5）
【当前策略建议】{advice}

【详细技术指标数据】
"""

for _, row in download_df.iterrows():
    copy_text += f"• {row['指标']}：{row['数值']} | {row['判定结果']} | 评分：{row['数值评分']}\n"

copy_text += f"""

【五维分析得分】
• 趋势(MA)：{ma_sig:+d}
• 动能(MACD)：{macd_sig:+d} 
• 位置(BOLL)：{pos_sig:+d}
• 能量(VOL)：{energy_sig:+d}
• 波动率(HV)：{volatility_sig:+d}

【分析要求】
1. 基于五维技术指标，评估当前市场状态
2. 结合总信号分，推荐最适合的期权策略组合
3. 考虑风险控制和资金管理建议
4. 提供具体的入场时机和止损点位
5. 如有不同观点，请说明理由和替代方案
"""

with col1:
    # CSV下载
    csv_data = download_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📊 下载CSV",
        data=csv_data,
        file_name=f"期权策略技术指标_{sel_label.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        help="下载技术指标数据为CSV格式"
    )

with col2:
    # Excel下载
    from io import BytesIO
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        download_df.to_excel(writer, sheet_name='技术指标', index=False)
        # 添加策略建议到第二个sheet
        strategy_df = pd.DataFrame({
            '分析时间': [current_time],
            '标的名称': [sel_label],
            '总信号分': [score],
            '核心策略': [advice],
            '策略说明': [explain]
        })
        strategy_df.to_excel(writer, sheet_name='策略建议', index=False)
    excel_buffer.seek(0)
    
    st.download_button(
        label="📈 下载Excel",
        data=excel_buffer.getvalue(),
        file_name=f"期权策略分析_{sel_label.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="下载完整分析报告为Excel格式（包含技术指标和策略建议）"
    )

# 显示查看 AI 分析文本的选项
with st.expander("📄 查看 AI 分析提示词", expanded=False):
    st.text_area(
        "AI分析提示词（可复制给AI助手分析）：",
        copy_text,
        height=250,
        help="请全选(Ctrl+A)并复制(Ctrl+C)此内容，然后粘贴给AI助手进行深度分析",
        key="ai_analysis_text_area"
    )
    st.info("""
    💡 **使用说明：**
    1. 点击上方文本框，使用 Ctrl+A 全选所有内容
    2. 使用 Ctrl+C 复制文本  
    3. 将复制的内容粘贴给任何AI助手（如ChatGPT、Claude等）
    4. AI会基于这些数据为您提供专业的期权策略建议
    """)

st.markdown("")
st.markdown(table_css + styled.to_html(), unsafe_allow_html=True)

st.markdown("---")

# 极端行情提示（布林带外）
if pos_neutral_extreme:
    st.warning("价格位于布林带之外（极端区），注意：上轨之外慎追多、下轨之外慎追空；可考虑相应方向的卖方策略以博取回归。")

# 明细区（可选）
with st.expander("📚 规则与映射说明", expanded=False):
    st.markdown("""
### 一、核心逻辑
- 完全基于日线数据，摒弃噪音；五维度（趋势/动能/位置/能量/波动率）各自输出 +1 / 0 / -1 信号，相加得到总信号分。

### 二、五维信号判定规则（全部基于日线）
1) 趋势维度 MA Trend
- 看多 (+1)：收盘价 > MA20 且 MA5 > MA10 > MA20（标准多头排列）
- 看空 (-1)：收盘价 < MA20 且 MA5 < MA10 < MA20（标准空头排列）
- 中性 (0)：上述条件均不满足（均线纠缠/震荡）

2) 动能维度 MACD Momentum
- 看多 (+1)：MACD > 0（零轴上）且 MACD > MACD_Signal（DIF>DEA，金叉/保持多头）
- 看空 (-1)：MACD < 0（零轴下）且 MACD < MACD_Signal（DIF<DEA，死叉/保持空头）
- 中性 (0)：MACD在零轴附近徘徊或方向不明

3) 位置维度 Bollinger Position
- 看多 (+1)：收盘价 > BOLL_MID（中轨）且 价格位于中轨~上轨之间
- 看空 (-1)：收盘价 < BOLL_MID（中轨）且 价格位于下轨~中轨之间
- 中性 (0)：价格紧贴中轨或已冲出布林带外（极端超买/超卖）

4) 能量维度 Volume Force
- 看多 (+1)：当日成交量 > 近5日均量 × 1.2（放量）且 当日收阳
- 看空 (-1)：当日成交量 > 近5日均量 × 1.2（放量）且 当日收阴
- 中性 (0)：量比≤1.2 或 放量但K线形态不明（如十字星）

5) 波动率维度 Volatility (🆕 新增)
- 有利卖方 (+1)：HV20上升>5% 或 布林带宽度>均值×1.1（波动率增加，期权价格上升）
- 有利买方 (-1)：HV20下降>5% 或 布林带宽度<均值×0.9（波动率回落，期权价格便宜）
- 中性 (0)：波动率变化在正常范围内

### 二、辅助技术指标规则（参考性判断）

6) KDJ随机指标 (Stochastic Oscillator)
- **超买超卖判断**：
  - 超卖区域：K值或D值 < 20，为潜在买入信号
  - 超买区域：K值或D值 > 80，为潜在卖出信号
  - 正常区间：20-80之间为中性区域

- **金叉与死叉**：
  - 金叉（买入信号）：K线自下向上穿越D线
    - 低位金叉（K<20）：信号更强，看涨概率高
    - 高位金叉（K>50）：信号较弱，可能为反弹
  - 死叉（卖出信号）：K线自上向下穿越D线
    - 高位死叉（K>80）：信号更强，看跌概率高
    - 低位死叉（K<50）：信号较弱，可能为回调

- **背离现象**（可靠性最高的信号）：
  - 顶背离：股价创新高但KDJ指标不创新高，预示上涨动能衰竭
  - 底背离：股价创新低但KDJ指标不创新低，预示下跌动能衰竭

- **期权策略应用**：
  - 低位金叉时：可考虑买入Call或卖出Put策略
  - 高位死叉时：可考虑买入Put或卖出Call策略
  - 背离信号：是趋势反转的重要预警，建议调整仓位结构

### 三、策略映射
- 总信号分 = 趋势 + 动能 + 位置 + 能量 + 波动率 ∈ [-5, +5]
- ≥ +4（极强多头）：牛市看涨价差 + 卖出看跌（Bull Call Spread + Sell Put）
  - 说明：用价差控制回撤与波动率风险；可卖Put收取高权利金
- = +3（较强多头）：牛市看涨价差（Bull Call Spread）
- = +2（温和看多）：卖出看跌期权（Sell Put）
  - 说明：看跌不跌赚时间价值；被指派则较低价接货
- -1 ~ +1（震荡/不明）：根据波动率分量精调策略
  - 波动率+1：卖出宽跨式/铁蝶（Short Strangle/Iron Butterfly）
  - 波动率-1：买入宽跨式/长期权（Long Strangle/Long Options）
  - 波动率 0：铁蝶式价差（Iron Butterfly）
- = -2（温和看空）：卖出看涨期权（Sell Call）
  - 说明：看涨不涨赚时间价值；趋势逆转需纪律止损
- = -3（较强空头）：熊市看跌价差（Bear Put Spread）
- ≤ -4（极强空头）：熊市看跌价差 + 卖出看涨（Bear Put Spread + Sell Call）
  - 说明：方向明确但控风险优先，避免单腿大暴露

### 四、极端情形与提示（布林带外）
- 极度超买（上轨之外）：慎追多；可考虑卖出看涨期权表达回归预期
- 极度超卖（下轨之外）：慎追空；可考虑卖出看跌期权表达回归预期

### 五、风险与使用说明
- 本系统仅基于日线数据做教育研究参考；实盘需结合事件风险、隐含波动率、流动性与持仓规模管理。
- 建议配合止损/止盈线与滚动移仓机制；高波动期间谨慎使用纯卖方策略，优先价差化或加买腿对冲。
""")
