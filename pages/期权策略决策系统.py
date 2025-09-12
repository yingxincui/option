import streamlit as st
import pandas as pd
import numpy as np
from utils.etf_analysis_shared import load_etf_data, calculate_technical_indicators
from utils.etf_analysis_shared import create_etf_chart
from pages.etf技术分析 import ETF_CONFIG

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
st.markdown(f"**标的**：{sel_label}  |  **总信号分**：{score:+d}")
st.markdown(f"**核心策略**：{advice}")
st.markdown(f"**策略说明**：{explain}")
if extra:
    st.markdown("**执行要点**：")
    for x in extra:
        st.markdown(f"- {x}")

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
st.subheader(f"{sel_label} · 日线主图")
main_fig = create_etf_chart(df, f"{sel_label} 技术分析图表")
if main_fig:
    st.plotly_chart(main_fig, use_container_width=True)

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
