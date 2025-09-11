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

st.markdown('<div class="main-header">🧭 期权策略决策系统（日线·多因子共振）</div>', unsafe_allow_html=True)

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

# 四维信号计算规则
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

# 总分
score = ma_sig + macd_sig + pos_sig + energy_sig

# 卡片配色选择函数
def cls(sig: int) -> str:
    return "metric-pos" if sig > 0 else ("metric-neg" if sig < 0 else "metric-neu")

# —— 将“决策建议”放在最上方（标题下、卡片上） ——
advice = ""
explain = ""
extra = []

if score >= 3:
    advice = "牛市看涨价差 (Bull Call Spread)"
    explain = "强趋势做多，价差控制风险，稳步获取趋势利润。"
    extra = ["少量资金可尝试虚值Call增强", "设置回撤止盈/止损线"]
elif score <= -3:
    advice = "熊市看跌价差 (Bear Put Spread)"
    explain = "强趋势做空，价差控制风险，避免单腿暴露。"
    extra = ["反弹均线附近再加码", "关注波动率回落对价差的影响"]
elif score == 2:
    advice = "卖出看跌期权 (Sell Put)"
    explain = "温和看多，赚时间价值；被指派则相对低价接货。"
    extra = ["严格风控：波动率急升时及时对冲/平仓", "尽量选择流动性好的合约"]
elif score == -2:
    advice = "卖出看涨期权 (Sell Call)"
    explain = "温和看空，赚时间价值；趋势逆转风险较大，需纪律止损。"
    extra = ["反弹至均线压力区再布局", "必要时用买腿(买入Call)做对冲"]
else:
    advice = "铁蝶式价差 / 卖出宽跨式 (Iron Butterfly / Short Strangle)"
    explain = "震荡盘整，方向不明，赚取时间价值衰减。但需良好风控能力。"
    extra = ["关注事件驱动与隐波变化", "设置区间外强制止损与滚动移仓"]

st.markdown("---")
st.subheader("🎯 决策建议（置顶）")
st.markdown(f"**标的**：{sel_label}  |  **总信号分**：{score:+d}")
st.markdown(f"**核心策略**：{advice}")
st.markdown(f"**策略说明**：{explain}")
if extra:
    st.markdown("**执行要点**：")
    for x in extra:
        st.markdown(f"- {x}")

# 展示指标与信号（统一尺寸+配色）
c1, c2, c3, c4, c5 = st.columns(5)

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
    total_cls = cls(score)
    st.markdown(
        f"""
        <div class='metric-card {total_cls}'>
            <div class='metric-val'>{score:+d}</div>
            <div class='metric-lbl'>总信号分</div>
            <div class='metric-body'>
                MA {ma_sig:+d} ｜ MACD {macd_sig:+d}<br/>
                BOLL {pos_sig:+d} ｜ VOL {energy_sig:+d}
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

st.markdown(table_css + styled.to_html(), unsafe_allow_html=True)

st.markdown("---")

# 策略映射
advice = ""
explain = ""
extra = []

if score >= 3:
    advice = "牛市看涨价差 (Bull Call Spread)"
    explain = "强趋势做多，价差控制风险，稳步获取趋势利润。"
    extra = ["少量资金可尝试虚值Call增强", "设置回撤止盈/止损线"]
elif score <= -3:
    advice = "熊市看跌价差 (Bear Put Spread)"
    explain = "强趋势做空，价差控制风险，避免单腿暴露。"
    extra = ["反弹均线附近再加码", "关注波动率回落对价差的影响"]
elif score == 2:
    advice = "卖出看跌期权 (Sell Put)"
    explain = "温和看多，赚时间价值；被指派则相对低价接货。"
    extra = ["严格风控：波动率急升时及时对冲/平仓", "尽量选择流动性好的合约"]
elif score == -2:
    advice = "卖出看涨期权 (Sell Call)"
    explain = "温和看空，赚时间价值；趋势逆转风险较大，需纪律止损。"
    extra = ["反弹至均线压力区再布局", "必要时用买腿(买入Call)做对冲"]
else:
    advice = "铁蝶式价差 / 卖出宽跨式 (Iron Butterfly / Short Strangle)"
    explain = "震荡盘整，方向不明，赚取时间价值衰减。但需良好风控能力。"
    extra = ["关注事件驱动与隐波变化", "设置区间外强制止损与滚动移仓"]

st.subheader("🎯 决策建议")
st.markdown(f"**标的**：{sel_label}  |  **总信号分**：{score:+d}")
st.markdown(f"**核心策略**：{advice}")
st.markdown(f"**策略说明**：{explain}")
if extra:
    st.markdown("**执行要点**：")
    for x in extra:
        st.markdown(f"- {x}")

# 极端行情提示（布林带外）
if pos_neutral_extreme:
    st.warning("价格位于布林带之外（极端区），注意：上轨之外慎追多、下轨之外慎追空；可考虑相应方向的卖方策略以博取回归。")

# 明细区（可选）
with st.expander("📚 规则与映射说明", expanded=False):
    st.markdown("""
### 一、核心逻辑
- 完全基于日线数据，摒弃噪音；四维度（趋势/动能/位置/能量）各自输出 +1 / 0 / -1 信号，相加得到总信号分。

### 二、四维信号判定规则（全部基于日线）
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

### 三、策略映射
- 总信号分 = 趋势 + 动能 + 位置 + 能量 ∈ [-4, +4]
- ≥ +3（强趋势做多）：牛市看涨价差（Bull Call Spread）
  - 说明：用价差控制回撤与波动率风险；可小额 Long OTM Call 做加速增强
- = +2（温和看多）：卖出看跌期权（Sell Put）
  - 说明：看跌不跌赚时间价值；被指派则较低价接货
- -1 ~ +1（震荡/不明）：铁蝶式/卖出宽跨（Iron Butterfly / Short Strangle）
  - 说明：赚时间价值衰减；需较强风控与波动率管理能力
- = -2（温和看空）：卖出看涨期权（Sell Call）
  - 说明：看涨不涨赚时间价值；趋势逆转需纪律止损
- ≤ -3（强趋势做空）：熊市看跌价差（Bear Put Spread）
  - 说明：方向明确但控风险优先，避免单腿大暴露

### 四、极端情形与提示（布林带外）
- 极度超买（上轨之外）：慎追多；可考虑卖出看涨期权表达回归预期
- 极度超卖（下轨之外）：慎追空；可考虑卖出看跌期权表达回归预期

### 五、风险与使用说明
- 本系统仅基于日线数据做教育研究参考；实盘需结合事件风险、隐含波动率、流动性与持仓规模管理。
- 建议配合止损/止盈线与滚动移仓机制；高波动期间谨慎使用纯卖方策略，优先价差化或加买腿对冲。
""")
