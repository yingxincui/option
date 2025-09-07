import streamlit as st
import akshare as ak
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# 设置页面配置
st.set_page_config(
    page_title="ETF对比分析",
    page_icon="📊",
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
    .comparison-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
    .signal-bullish {
        color: #28a745;
        font-weight: bold;
    }
    .signal-bearish {
        color: #dc3545;
        font-weight: bold;
    }
    .signal-neutral {
        color: #ffc107;
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

# 颜色规则配置
COLOR_RULES = {
    "上涨": "#dc3545",  # 红色
    "下跌": "#28a745",  # 绿色
    "金叉": "#dc3545",  # 红色箭头
    "死叉": "#28a745",  # 绿色箭头
    "MACD正": "#dc3545",  # 红色
    "MACD负": "#28a745"   # 绿色
}

def detect_ma_cross_signals(df):
    """检测MA金叉和死叉信号"""
    if df is None or df.empty or len(df) < 20:
        return [], []
    
    golden_crosses = []
    death_crosses = []
    
    # 检测MA5和MA10的金叉死叉
    if 'MA5' in df.columns and 'MA10' in df.columns:
        for i in range(1, len(df)):
            # 金叉：MA5从下方穿越MA10
            if (df['MA5'].iloc[i-1] <= df['MA10'].iloc[i-1] and 
                df['MA5'].iloc[i] > df['MA10'].iloc[i]):
                golden_crosses.append({
                    'date': df['日期'].iloc[i],
                    'price': df['收盘'].iloc[i],
                    'type': 'MA5-MA10金叉'
                })
            
            # 死叉：MA5从上方穿越MA10
            elif (df['MA5'].iloc[i-1] >= df['MA10'].iloc[i-1] and 
                  df['MA5'].iloc[i] < df['MA10'].iloc[i]):
                death_crosses.append({
                    'date': df['日期'].iloc[i],
                    'price': df['收盘'].iloc[i],
                    'type': 'MA5-MA10死叉'
                })
    
    # 检测MA10和MA20的金叉死叉
    if 'MA10' in df.columns and 'MA20' in df.columns:
        for i in range(1, len(df)):
            # 金叉：MA10从下方穿越MA20
            if (df['MA10'].iloc[i-1] <= df['MA20'].iloc[i-1] and 
                df['MA10'].iloc[i] > df['MA20'].iloc[i]):
                golden_crosses.append({
                    'date': df['日期'].iloc[i],
                    'price': df['收盘'].iloc[i],
                    'type': 'MA10-MA20金叉'
                })
            
            # 死叉：MA10从上方穿越MA20
            elif (df['MA10'].iloc[i-1] >= df['MA20'].iloc[i-1] and 
                  df['MA10'].iloc[i] < df['MA20'].iloc[i]):
                death_crosses.append({
                    'date': df['日期'].iloc[i],
                    'price': df['收盘'].iloc[i],
                    'type': 'MA10-MA20死叉'
                })
    
    return golden_crosses, death_crosses

def detect_macd_cross_signals(df):
    """检测MACD金叉和死叉信号"""
    if df is None or df.empty or len(df) < 20:
        return [], []
    
    golden_crosses = []
    death_crosses = []
    
    # 检测MACD金叉死叉
    if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
        for i in range(1, len(df)):
            # 金叉：MACD从下方穿越MACD_Signal
            if (df['MACD'].iloc[i-1] <= df['MACD_Signal'].iloc[i-1] and 
                df['MACD'].iloc[i] > df['MACD_Signal'].iloc[i]):
                golden_crosses.append({
                    'date': df['日期'].iloc[i],
                    'macd_value': df['MACD'].iloc[i],
                    'type': 'MACD金叉'
                })
            
            # 死叉：MACD从上方穿越MACD_Signal
            elif (df['MACD'].iloc[i-1] >= df['MACD_Signal'].iloc[i-1] and 
                  df['MACD'].iloc[i] < df['MACD_Signal'].iloc[i]):
                death_crosses.append({
                    'date': df['日期'].iloc[i],
                    'macd_value': df['MACD'].iloc[i],
                    'type': 'MACD死叉'
                })
    
    return golden_crosses, death_crosses

def create_price_chart(etf_name, df, signals):
    """创建ETF价格走势图"""
    if df is None or df.empty or len(df) < 20:
        return None
    
    # 创建子图：价格图、MACD图和成交量图
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{etf_name} 价格走势', 'MACD指标', '成交量'),
        row_heights=[0.5, 0.25, 0.25]
    )
    
    # 添加K线图
    fig.add_trace(
        go.Candlestick(
            x=df['日期'],
            open=df['开盘'],
            high=df['最高'],
            low=df['最低'],
            close=df['收盘'],
            name='K线',
            increasing_line_color=COLOR_RULES['上涨'],  # 红色
            decreasing_line_color=COLOR_RULES['下跌']   # 绿色
        ),
        row=1, col=1
    )
    
    # 添加移动平均线
    if 'MA5' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['日期'],
                y=df['MA5'],
                name='MA5',
                line=dict(color='#ff9800', width=2),
                opacity=0.8
            ),
            row=1, col=1
        )
    
    if 'MA10' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['日期'],
                y=df['MA10'],
                name='MA10',
                line=dict(color='#2196f3', width=2),
                opacity=0.8
            ),
            row=1, col=1
        )
    
    if 'MA20' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['日期'],
                y=df['MA20'],
                name='MA20',
                line=dict(color='#9c27b0', width=2),
                opacity=0.8
            ),
            row=1, col=1
        )
    
    # 检测MA金叉和死叉信号
    ma_golden_crosses, ma_death_crosses = detect_ma_cross_signals(df)
    
    # 添加MA金叉标识（红色箭头）
    if ma_golden_crosses:
        golden_dates = [cross['date'] for cross in ma_golden_crosses]
        golden_prices = [cross['price'] for cross in ma_golden_crosses]
        golden_texts = [cross['type'] for cross in ma_golden_crosses]
        
        fig.add_trace(
            go.Scatter(
                x=golden_dates,
                y=golden_prices,
                mode='markers',
                name='MA金叉',
                marker=dict(
                    symbol='arrow-up',
                    size=15,
                    color=COLOR_RULES['金叉'],
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>%{text}</b><br>日期: %{x}<br>价格: %{y:.3f}<extra></extra>',
                customdata=golden_texts
            ),
            row=1, col=1
        )
    
    # 添加MA死叉标识（绿色箭头）
    if ma_death_crosses:
        death_dates = [cross['date'] for cross in ma_death_crosses]
        death_prices = [cross['price'] for cross in ma_death_crosses]
        death_texts = [cross['type'] for cross in ma_death_crosses]
        
        fig.add_trace(
            go.Scatter(
                x=death_dates,
                y=death_prices,
                mode='markers',
                name='MA死叉',
                marker=dict(
                    symbol='arrow-down',
                    size=15,
                    color=COLOR_RULES['死叉'],
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>%{text}</b><br>日期: %{x}<br>价格: %{y:.3f}<extra></extra>',
                customdata=death_texts
            ),
            row=1, col=1
        )
    
    # 添加MACD指标
    if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
        # MACD线
        fig.add_trace(
            go.Scatter(
                x=df['日期'],
                y=df['MACD'],
                name='MACD',
                line=dict(color='#2196f3', width=2),
                opacity=0.8
            ),
            row=2, col=1
        )
        
        # MACD信号线
        fig.add_trace(
            go.Scatter(
                x=df['日期'],
                y=df['MACD_Signal'],
                name='MACD信号线',
                line=dict(color='#ff9800', width=2),
                opacity=0.8
            ),
            row=2, col=1
        )
        
        # 检测MACD金叉和死叉信号
        macd_golden_crosses, macd_death_crosses = detect_macd_cross_signals(df)
        
        # 添加MACD金叉标识（红色箭头）
        if macd_golden_crosses:
            macd_golden_dates = [cross['date'] for cross in macd_golden_crosses]
            macd_golden_values = [cross['macd_value'] for cross in macd_golden_crosses]
            macd_golden_texts = [cross['type'] for cross in macd_golden_crosses]
            
            fig.add_trace(
                go.Scatter(
                    x=macd_golden_dates,
                    y=macd_golden_values,
                    mode='markers',
                    name='MACD金叉',
                    marker=dict(
                        symbol='arrow-up',
                        size=12,
                        color=COLOR_RULES['金叉'],
                        line=dict(width=2, color='white')
                    ),
                    hovertemplate='<b>%{text}</b><br>日期: %{x}<br>MACD: %{y:.4f}<extra></extra>',
                    customdata=macd_golden_texts
                ),
                row=2, col=1
            )
        
        # 添加MACD死叉标识（绿色箭头）
        if macd_death_crosses:
            macd_death_dates = [cross['date'] for cross in macd_death_crosses]
            macd_death_values = [cross['macd_value'] for cross in macd_death_crosses]
            macd_death_texts = [cross['type'] for cross in macd_death_crosses]
            
            fig.add_trace(
                go.Scatter(
                    x=macd_death_dates,
                    y=macd_death_values,
                    mode='markers',
                    name='MACD死叉',
                    marker=dict(
                        symbol='arrow-down',
                        size=12,
                        color=COLOR_RULES['死叉'],
                        line=dict(width=2, color='white')
                    ),
                    hovertemplate='<b>%{text}</b><br>日期: %{x}<br>MACD: %{y:.4f}<extra></extra>',
                    customdata=macd_death_texts
                ),
                row=2, col=1
            )
        
        # MACD柱状图
        if 'MACD_Histogram' in df.columns:
            colors = [COLOR_RULES['MACD正'] if val >= 0 else COLOR_RULES['MACD负'] for val in df['MACD_Histogram']]
            fig.add_trace(
                go.Bar(
                    x=df['日期'],
                    y=df['MACD_Histogram'],
                    name='MACD柱状图',
                    marker_color=colors,
                    opacity=0.7
                ),
                row=2, col=1
            )
    
    # 添加成交量柱状图
    colors = [COLOR_RULES['上涨'] if close >= open else COLOR_RULES['下跌'] 
              for close, open in zip(df['收盘'], df['开盘'])]
    
    fig.add_trace(
        go.Bar(
            x=df['日期'],
            y=df['成交量'],
            name='成交量',
            marker_color=colors,
            opacity=0.7
        ),
        row=3, col=1
    )
    
    # 更新布局
    fig.update_layout(
        title=f'{etf_name} 技术分析图表',
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # 更新x轴和y轴标签
    fig.update_xaxes(title_text="日期", row=3, col=1)
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="成交量", row=3, col=1)
    
    return fig

@st.cache_data(ttl=86400)  # 缓存24小时
def load_etf_data(symbol, days=100):
    """加载ETF历史数据"""
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        df = ak.fund_etf_hist_em(
            symbol=symbol, 
            period="daily", 
            start_date=start_date, 
            end_date=end_date, 
            adjust="qfq"
        )
        
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期').reset_index(drop=True)
            return df
        return None
    except Exception as e:
        st.error(f"加载 {symbol} 数据失败: {str(e)}")
        return None

def calculate_technical_indicators(df):
    """计算技术指标"""
    if df is None or df.empty:
        return df
    
    # 计算移动平均线
    df['MA5'] = df['收盘'].rolling(window=5).mean()
    df['MA10'] = df['收盘'].rolling(window=10).mean()
    df['MA20'] = df['收盘'].rolling(window=20).mean()
    
    # 计算MACD
    exp1 = df['收盘'].ewm(span=12).mean()
    exp2 = df['收盘'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    
    # 计算RSI
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def analyze_etf_signals(df, symbol_name):
    """分析ETF技术信号"""
    if df is None or df.empty or len(df) < 20:
        return None
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    signals = {
        'symbol': symbol_name,
        'current_price': latest['收盘'],
        'change_pct': latest['涨跌幅'],
        'volume': latest['成交量'],
        'turnover': latest['换手率']
    }
    
    # 均线分析
    current_price = latest['收盘']
    ma5 = latest['MA5']
    ma10 = latest['MA10'] 
    ma20 = latest['MA20']
    
    signals['price_above_ma5'] = current_price > ma5
    signals['price_above_ma10'] = current_price > ma10
    signals['price_above_ma20'] = current_price > ma20
    signals['bullish_alignment'] = ma5 > ma10 > ma20
    
    # 均线数值
    signals['ma5_value'] = ma5
    signals['ma10_value'] = ma10
    signals['ma20_value'] = ma20
    
    # 金叉死叉
    signals['ma5_ma10_golden_cross'] = (latest['MA5'] > latest['MA10']) and (prev['MA5'] <= prev['MA10'])
    signals['ma5_ma10_death_cross'] = (latest['MA5'] < latest['MA10']) and (prev['MA5'] >= prev['MA10'])
    signals['ma10_ma20_golden_cross'] = (latest['MA10'] > latest['MA20']) and (prev['MA10'] <= prev['MA20'])
    signals['ma10_ma20_death_cross'] = (latest['MA10'] < latest['MA20']) and (prev['MA10'] >= prev['MA20'])
    
    # MACD分析
    signals['macd_golden_cross'] = (latest['MACD'] > latest['MACD_Signal']) and (prev['MACD'] <= prev['MACD_Signal'])
    signals['macd_death_cross'] = (latest['MACD'] < latest['MACD_Signal']) and (prev['MACD'] >= prev['MACD_Signal'])
    signals['macd_above_zero'] = latest['MACD'] > 0
    signals['macd_value'] = latest['MACD']
    signals['macd_signal_value'] = latest['MACD_Signal']
    
    # RSI分析
    rsi = latest['RSI']
    signals['rsi'] = rsi
    signals['rsi_oversold'] = rsi < 30
    signals['rsi_overbought'] = rsi > 70
    
    # 计算最近金叉日期
    def find_latest_golden_cross(df):
        """查找最近的金叉日期"""
        # 检查MA5-MA10金叉
        ma5_ma10_cross = df[(df['MA5'] > df['MA10']) & (df['MA5'].shift(1) <= df['MA10'].shift(1))]
        # 检查MA10-MA20金叉
        ma10_ma20_cross = df[(df['MA10'] > df['MA20']) & (df['MA10'].shift(1) <= df['MA20'].shift(1))]
        # 检查MACD金叉
        macd_cross = df[(df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))]
        
        # 合并所有金叉日期
        all_crosses = []
        if not ma5_ma10_cross.empty:
            all_crosses.extend(ma5_ma10_cross.index.tolist())
        if not ma10_ma20_cross.empty:
            all_crosses.extend(ma10_ma20_cross.index.tolist())
        if not macd_cross.empty:
            all_crosses.extend(macd_cross.index.tolist())
        
        if all_crosses:
            # 找到最近的金叉日期
            latest_cross_idx = max(all_crosses)
            latest_cross_date = df.loc[latest_cross_idx, '日期']
            # 计算距离今天的天数
            current_date = df.iloc[-1]['日期']
            days_ago = (current_date - latest_cross_date).days
            return days_ago
        else:
            return None
    
    signals['latest_golden_cross_days'] = find_latest_golden_cross(df)
    
    # 计算近20日涨幅
    if len(df) >= 20:
        current_price = latest['收盘']
        price_20_days_ago = df.iloc[-20]['收盘']
        change_20_days = ((current_price - price_20_days_ago) / price_20_days_ago) * 100
        signals['change_20_days'] = change_20_days
    else:
        signals['change_20_days'] = None
    
    # 成交量分析
    current_volume = latest['成交量']
    if len(df) >= 5:
        volume_ma5 = df['成交量'].rolling(window=5).mean().iloc[-1]
        volume_ratio = current_volume / volume_ma5 if volume_ma5 > 0 else 1
        
        if volume_ratio > 1.5:
            signals['volume_status'] = "放量"
        elif volume_ratio < 0.8:
            signals['volume_status'] = "缩量"
        else:
            signals['volume_status'] = "正常"
    else:
        signals['volume_status'] = "正常"
    
    # 计算综合评分
    score = 0
    if signals['price_above_ma5']: score += 1
    if signals['price_above_ma10']: score += 1
    if signals['price_above_ma20']: score += 1
    if signals['bullish_alignment']: score += 2
    if signals['ma5_ma10_golden_cross']: score += 2
    if signals['ma10_ma20_golden_cross']: score += 2
    if signals['macd_golden_cross']: score += 2
    if signals['macd_above_zero']: score += 1
    if signals['rsi_oversold']: score += 1
    if signals['rsi_overbought']: score -= 1
    
    signals['total_score'] = score
    
    return signals


def main():
    # 主标题
    st.markdown('<h1 class="main-header">📊 ETF对比分析</h1>', unsafe_allow_html=True)
    
    # 侧边栏配置
    st.sidebar.header("⚙️ 分析配置")
    
    # 选择要分析的ETF
    selected_etfs = st.sidebar.multiselect(
        "选择要对比的ETF",
        options=list(ETF_CONFIG.keys()),
        default=list(ETF_CONFIG.keys())  # 默认选择所有ETF
    )
    
    # 历史数据天数
    days = st.sidebar.slider(
        "历史数据天数",
        min_value=30,
        max_value=200,
        value=100,
        step=10
    )
    
    # 刷新按钮
    if st.sidebar.button("🔄 刷新分析", type="primary"):
        st.rerun()
    
    if not selected_etfs:
        st.warning("请至少选择一个ETF进行对比分析")
        return
    
    # 加载数据
    st.subheader("📈 数据加载中...")
    etf_data_dict = {}
    signals_list = []
    failed_etfs = []
    loaded_symbols = set()  # 用于跟踪已加载的ETF
    
    progress_bar = st.progress(0)
    total_etfs = len(selected_etfs)
    
    for i, etf_name in enumerate(selected_etfs):
        etf_symbol = ETF_CONFIG[etf_name]
        
        # 检查是否已经加载过这个ETF
        if etf_symbol in loaded_symbols:
            st.warning(f"跳过重复的ETF: {etf_name}")
            continue
        loaded_symbols.add(etf_symbol)
        
        try:
            with st.spinner(f"正在加载 {etf_name} 数据..."):
                df = load_etf_data(etf_symbol, days)
                
            if df is not None and not df.empty and len(df) >= 20:
                df = calculate_technical_indicators(df)
                etf_data_dict[etf_name] = df
                
                signals = analyze_etf_signals(df, etf_name)
                if signals is not None:
                    signals_list.append(signals)
                else:
                    failed_etfs.append(etf_name)
            else:
                failed_etfs.append(etf_name)
        except Exception as e:
            st.warning(f"加载 {etf_name} 失败: {str(e)}")
            failed_etfs.append(etf_name)
        
        progress_bar.progress((i + 1) / total_etfs)
    
    # 显示加载结果
    if failed_etfs:
        st.warning(f"以下ETF加载失败: {', '.join(failed_etfs)}")
    
    if not signals_list:
        st.error("无法加载任何ETF数据")
        return
    
    st.success(f"成功加载 {len(etf_data_dict)} 个ETF的数据")
    
    
    # 显示对比结果
    st.subheader("📊 对比分析结果")
    
    # 创建对比表格
    comparison_data = []
    processed_symbols = set()  # 用于跟踪已处理的ETF
    
    # 处理已加载的ETF数据
    for etf_name, df in etf_data_dict.items():
        if etf_name not in ETF_CONFIG:
            continue
            
        symbol = ETF_CONFIG[etf_name]
        
        # 检查是否已经处理过这个ETF
        if symbol in processed_symbols:
            continue
        processed_symbols.add(symbol)
        
        # 查找对应的信号数据
        signals = None
        for s in signals_list:
            if s and s.get('symbol') == etf_name:
                signals = s
                break
        
        # 确保信号数据完整
        if signals is None or not signals:
            continue
            
        # 验证必要字段
        required_fields = ['current_price', 'change_pct', 'ma5_value', 'ma10_value', 'ma20_value', 
                          'price_above_ma5', 'price_above_ma10', 'price_above_ma20', 'bullish_alignment',
                          'ma5_ma10_golden_cross', 'ma5_ma10_death_cross', 'ma10_ma20_golden_cross', 'ma10_ma20_death_cross',
                          'macd_golden_cross', 'macd_death_cross', 'macd_above_zero', 'macd_value', 'macd_signal_value',
                          'rsi', 'rsi_oversold', 'rsi_overbought', 'volume_status', 'turnover', 'latest_golden_cross_days', 
                          'change_20_days', 'total_score']
        
        missing_fields = [field for field in required_fields if field not in signals]
        if missing_fields:
            st.warning(f"跳过 {etf_name} - 缺少字段: {missing_fields}")
            continue
        
        # 均线分析状态 - 使用emoji图标
        ma_status = []
        if signals['price_above_ma5']:
            ma_status.append("✅MA5")
        else:
            ma_status.append("❌MA5")
        if signals['price_above_ma10']:
            ma_status.append("✅MA10")
        else:
            ma_status.append("❌MA10")
        if signals['price_above_ma20']:
            ma_status.append("✅MA20")
        else:
            ma_status.append("❌MA20")
        
        # 金叉死叉状态 - 使用emoji图标
        cross_status = []
        if signals['ma5_ma10_golden_cross']:
            cross_status.append("🟢5-10")
        elif signals['ma5_ma10_death_cross']:
            cross_status.append("🔴5-10")
        else:
            cross_status.append("⚪5-10")
            
        if signals['ma10_ma20_golden_cross']:
            cross_status.append("🟢10-20")
        elif signals['ma10_ma20_death_cross']:
            cross_status.append("🔴10-20")
        else:
            cross_status.append("⚪10-20")
        
        # MACD状态 - 使用emoji图标
        macd_status = []
        if signals['macd_golden_cross']:
            macd_status.append("🟢金叉")
        elif signals['macd_death_cross']:
            macd_status.append("🔴死叉")
        else:
            macd_status.append("⚪无交叉")
        
        if signals['macd_above_zero']:
            macd_status.append("✅>0")
        else:
            macd_status.append("❌<0")
        
        # RSI状态 - 使用emoji图标
        rsi_status = ""
        if signals['rsi_oversold']:
            rsi_status = "🟢超卖"
        elif signals['rsi_overbought']:
            rsi_status = "🔴超买"
        else:
            rsi_status = "⚪中性"
        
        # 投资建议逻辑
        investment_advice = ""
        advice_emoji = ""
        
        # 检查是否有金叉信号
        has_golden_cross = (signals['ma5_ma10_golden_cross'] or 
                           signals['ma10_ma20_golden_cross'] or 
                           signals['macd_golden_cross'])
        
        # 检查多头排列
        is_bullish = signals['bullish_alignment']
        
        # 检查价格位置
        price_above_ma20 = signals['price_above_ma20']
        
        # 检查RSI是否超卖
        is_oversold = signals['rsi_oversold']
        
        if has_golden_cross and is_bullish and price_above_ma20:
            investment_advice = "强烈建议买入当月实值一档看涨期权"
            advice_emoji = "🚀"
        elif has_golden_cross and price_above_ma20:
            investment_advice = "建议买入当月实值一档看涨期权"
            advice_emoji = "📈"
        elif is_oversold and price_above_ma20:
            investment_advice = "可考虑买入当月实值一档看涨期权"
            advice_emoji = "💡"
        elif is_bullish and price_above_ma20:
            investment_advice = "观望，等待更明确信号"
            advice_emoji = "👀"
        else:
            investment_advice = "暂不建议买入期权"
            advice_emoji = "⏸️"
        
        # 最近金叉天数显示
        latest_cross_days = signals['latest_golden_cross_days']
        if latest_cross_days is not None:
            if latest_cross_days == 0:
                cross_days_display = "今日"
            elif latest_cross_days == 1:
                cross_days_display = "1天前"
            else:
                cross_days_display = f"{latest_cross_days}天前"
        else:
            cross_days_display = "无金叉"
        
        # 近20日涨幅显示
        change_20_days = signals.get('change_20_days')
        if change_20_days is not None:
            change_20_days_display = f"{change_20_days:.2f}%"
        else:
            change_20_days_display = "N/A"
        
        comparison_data.append({
            '综合评分': signals['total_score'],
            'ETF标的': etf_name,
            '当前价格': f"{signals['current_price']:.3f}",
            '涨跌幅(%)': f"{signals['change_pct']:.2f}",
            '近20日涨幅(%)': change_20_days_display,
            'MA5': f"{signals['ma5_value']:.3f}",
            'MA10': f"{signals['ma10_value']:.3f}",
            'MA20': f"{signals['ma20_value']:.3f}",
            '均线状态': " ".join(ma_status),
            '金叉死叉': " ".join(cross_status),
            '多头排列': "✅" if signals['bullish_alignment'] else "❌",
            'MACD': f"{signals['macd_value']:.4f}",
            'MACD信号': f"{signals['macd_signal_value']:.4f}",
            'MACD状态': " ".join(macd_status),
            'RSI': f"{signals['rsi']:.1f}",
            'RSI状态': rsi_status,
            '最近金叉': cross_days_display,
            '成交量状态': signals['volume_status'],
            '换手率(%)': f"{signals['turnover']:.2f}",
            '投资建议': f"{advice_emoji} {investment_advice}"
        })
    
    # 验证数据
    if len(comparison_data) == 0:
        st.error("没有有效数据，请检查网络连接或数据源")
        st.write(f"调试信息:")
        st.write(f"- 已加载的ETF数量: {len(etf_data_dict)}")
        st.write(f"- 信号数据数量: {len(signals_list)}")
        st.write(f"- 已加载的ETF: {list(etf_data_dict.keys())}")
        st.write(f"- 信号数据的symbol: {[s.get('symbol') for s in signals_list if s]}")
        return
    
    # 确保只有6行数据
    if len(comparison_data) > 6:
        comparison_data = comparison_data[:6]
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # 检查DataFrame是否为空
    if comparison_df.empty:
        st.error("没有有效数据，请检查网络连接或数据源")
        return
    
    # 按综合评分排序
    if '综合评分' in comparison_df.columns:
        try:
            comparison_df = comparison_df.sort_values('综合评分', ascending=False)
        except Exception as e:
            st.warning(f"按综合评分排序失败: {e}")
    else:
        st.warning("缺少'综合评分'列，无法排序")
    
    # 验证表格行数
    if len(comparison_df) < 6:
        st.warning(f"⚠️ 数据不完整: 只有{len(comparison_df)}个ETF的数据，期望6个")
    
    # 美化表格显示
    st.markdown("""
    <style>
    .comparison-table {
        font-size: 14px;
    }
    .comparison-table th {
        background-color: #f8f9fa;
        font-weight: bold;
        text-align: center;
    }
    .comparison-table td {
        text-align: center;
        vertical-align: middle;
    }
    .score-high {
        background-color: #d4edda;
        font-weight: bold;
    }
    .score-medium {
        background-color: #fff3cd;
    }
    .score-low {
        background-color: #f8d7da;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 根据评分设置行样式
    def highlight_score(row):
        score = row['综合评分']
        if score >= 8:
            return ['score-high'] * len(row)
        elif score >= 5:
            return ['score-medium'] * len(row)
        else:
            return ['score-low'] * len(row)
    
    # 创建HTML表格
    def create_html_table(df):
        html = """
        <div style="overflow-x: auto; margin: 20px 0;">
            <table class="comparison-table" style="width: 100%; border-collapse: collapse; font-family: Arial, sans-serif;">
                <thead>
                    <tr style="background-color: #1f77b4; color: white;">
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">综合评分</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">ETF标的</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">当前价格</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">涨跌幅(%)</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">近20日涨幅(%)</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">MA5</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">MA10</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">MA20</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">均线状态</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">金叉死叉</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">多头排列</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">MACD</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">MACD信号</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">MACD状态</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">RSI</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">RSI状态</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">最近金叉</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">成交量状态</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">换手率(%)</th>
                        <th style="padding: 12px 8px; border: 1px solid #ddd; text-align: center;">投资建议</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for _, row in df.iterrows():
            # 根据评分设置行背景色
            score = row['综合评分']
            if score >= 8:
                row_style = "background-color: #d4edda; font-weight: bold;"
            elif score >= 5:
                row_style = "background-color: #fff3cd;"
            else:
                row_style = "background-color: #f8d7da;"
            
            # 安全处理涨跌幅颜色
            try:
                change_pct = float(row['涨跌幅(%)'])
                if change_pct < 0:
                    change_color = COLOR_RULES['下跌']  # 绿色
                elif change_pct > 0:
                    change_color = COLOR_RULES['上涨']  # 红色
                else:
                    change_color = "black"
            except:
                change_color = "black"
            
            # 安全处理近20日涨幅颜色
            try:
                change_20_days_str = str(row['近20日涨幅(%)']).replace('%', '')
                if change_20_days_str == 'N/A':
                    change_20_days_color = "gray"
                else:
                    change_20_days = float(change_20_days_str)
                    if change_20_days < 0:
                        change_20_days_color = COLOR_RULES['下跌']  # 绿色
                    elif change_20_days > 0:
                        change_20_days_color = COLOR_RULES['上涨']  # 红色
                    else:
                        change_20_days_color = "black"
            except:
                change_20_days_color = "gray"
            
            # 安全处理综合评分颜色
            try:
                if score >= 8:
                    score_color = "green"
                elif score >= 5:
                    score_color = "orange"
                else:
                    score_color = "red"
            except:
                score_color = "black"
            
            html += f"""
                    <tr style="{row_style}">
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; font-weight: bold; font-size: 16px; color: {score_color};">{str(row['综合评分'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{str(row['ETF标的'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center;">{str(row['当前价格'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; color: {change_color};">{str(row['涨跌幅(%)'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; color: {change_20_days_color}; font-weight: bold; font-size: 14px;">{str(row['近20日涨幅(%)'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center;">{str(row['MA5'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center;">{str(row['MA10'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center;">{str(row['MA20'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; font-size: 12px;">{str(row['均线状态'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; font-size: 12px;">{str(row['金叉死叉'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; font-size: 16px;">{str(row['多头排列'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center;">{str(row['MACD'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center;">{str(row['MACD信号'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; font-size: 12px;">{str(row['MACD状态'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center;">{str(row['RSI'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; font-size: 12px;">{str(row['RSI状态'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{str(row['最近金叉'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{str(row['成交量状态'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center;">{str(row['换手率(%)'])}</td>
                        <td style="padding: 10px 8px; border: 1px solid #ddd; text-align: center; font-size: 12px; font-weight: bold;">{str(row['投资建议'])}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        return html
    
    # 显示表格 - 使用美化的Streamlit表格
    # 添加表格样式
    st.markdown("""
    <style>
    .dataframe {
        font-size: 14px;
    }
    .dataframe th {
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .dataframe td {
        text-align: center;
        vertical-align: middle;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 使用Streamlit原生表格
    st.dataframe(
        comparison_df,
        use_container_width=True,
        height=400
    )
    
    # 添加表格说明（默认折叠）
    with st.expander("📋 表格说明", expanded=False):
        st.markdown("### 📊 列说明")
        
        st.markdown("#### 基础信息")
        st.markdown("""
        - **ETF标的**: 基金名称和代码
        - **当前价格**: 最新收盘价
        - **涨跌幅(%)**: 当日涨跌百分比，红色为上涨，绿色为下跌
        - **近20日涨幅(%)**: 20个交易日累计涨跌幅，红色为上涨，绿色为下跌
        """)
        
        st.markdown("#### 技术指标")
        st.markdown("""
        - **MA5/MA10/MA20**: 5日、10日、20日移动平均线
        - **均线状态**: ✅表示价格在均线之上，❌表示价格在均线之下
        - **金叉死叉**: 🟢表示金叉，🔴表示死叉，⚪表示无交叉
        - **多头排列**: ✅表示MA5>MA10>MA20，❌表示非多头排列
        - **MACD**: MACD指标值
        - **MACD信号**: MACD信号线值
        - **MACD状态**: 🟢表示金叉，🔴表示死叉，⚪表示无交叉；✅表示MACD>0，❌表示MACD<0
        - **RSI**: 相对强弱指数
        - **RSI状态**: 🟢表示超卖(<30)，🔴表示超买(>70)，⚪表示中性(30-70)
        """)
        
        st.markdown("#### 交易信息")
        st.markdown("""
        - **最近金叉**: 最近一次金叉信号距离今天的天数，包括MA5-MA10、MA10-MA20、MACD金叉
        - **成交量状态**: **放量**表示成交量放大，**缩量**表示成交量缩小，**正常**表示成交量正常
        - **换手率(%)**: 当日换手率
        """)
        
        st.markdown("#### 投资建议")
        st.markdown("""
        - **投资建议**: 基于技术指标的综合投资建议
          - 🚀 **强烈建议买入**: 多个指标同时发出买入信号
          - 📈 **建议买入**: 主要指标偏向买入
          - 💡 **可考虑买入**: 部分指标支持买入
          - 👀 **观望**: 指标信号不明确
          - ⏸️ **暂不建议**: 指标偏向卖出或谨慎
        - **综合评分**: 基于所有技术指标的综合评分(0-10分)，分数越高表示技术面越强
        """)
        
        st.markdown("#### 颜色规则")
        st.markdown("""
        - **上涨/金叉**: 红色 🔴
        - **下跌/死叉**: 绿色 🟢
        - **K线图**: 红色表示上涨，绿色表示下跌
        - **金叉死叉**: 红色向上箭头表示金叉，绿色向下箭头表示死叉
        - **MACD柱状图**: 红色表示正值，绿色表示负值
        - **成交量**: 红色表示上涨日，绿色表示下跌日
        """)
        
        st.info("💡 **使用提示**: 建议结合价格走势图和技术指标进行综合分析，单一指标仅供参考。")
    
    # 显示价格走势图
    st.subheader("📈 价格走势图")
    
    # 为每个ETF创建价格走势图
    for etf_name, df in etf_data_dict.items():
        if df is None or df.empty or len(df) < 20:
            continue
            
        # 查找对应的信号数据
        signals = None
        for s in signals_list:
            if s and s.get('symbol') == etf_name:
                signals = s
                break
        
        if signals is None:
            continue
            
        # 创建价格走势图
        chart = create_price_chart(etf_name, df, signals)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
            
            # 添加技术指标说明
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("当前价格", f"{signals['current_price']:.3f}")
            with col2:
                st.metric("涨跌幅", f"{signals['change_pct']:.2f}%")
            with col3:
                st.metric("综合评分", f"{signals['total_score']:.1f}")
            
            st.markdown("---")
    
    # 显示详细信号分析
    st.subheader("🔍 详细信号分析")
    
    for signals in signals_list:
        # 确保信号数据完整
        if signals is None or not signals or 'symbol' not in signals:
            continue
        with st.expander(f"{signals['symbol']} - 综合评分: {signals['total_score']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**均线分析**")
                st.write(f"价格>MA5: {'✅' if signals['price_above_ma5'] else '❌'}")
                st.write(f"价格>MA10: {'✅' if signals['price_above_ma10'] else '❌'}")
                st.write(f"价格>MA20: {'✅' if signals['price_above_ma20'] else '❌'}")
                st.write(f"多头排列: {'✅' if signals['bullish_alignment'] else '❌'}")
            
            with col2:
                st.write("**金叉死叉**")
                st.write(f"MA5金叉MA10: {'🟢' if signals['ma5_ma10_golden_cross'] else '🔴' if signals['ma5_ma10_death_cross'] else '⚪'}")
                st.write(f"MA10金叉MA20: {'🟢' if signals['ma10_ma20_golden_cross'] else '🔴' if signals['ma10_ma20_death_cross'] else '⚪'}")
                st.write(f"MACD金叉: {'🟢' if signals['macd_golden_cross'] else '🔴' if signals['macd_death_cross'] else '⚪'}")
                st.write(f"MACD>0: {'✅' if signals['macd_above_zero'] else '❌'}")
            
            with col3:
                st.write("**其他指标**")
                st.write(f"RSI: {signals['rsi']:.1f}")
                st.write(f"RSI超卖: {'✅' if signals['rsi_oversold'] else '❌'}")
                st.write(f"RSI超买: {'✅' if signals['rsi_overbought'] else '❌'}")
    
    
    # 数据下载
    st.subheader("💾 数据下载")
    
    # 合并所有ETF数据
    all_data = []
    for etf_name, df in etf_data_dict.items():
        if df is not None and not df.empty:
            df_copy = df.copy()
            df_copy['ETF'] = etf_name
            all_data.append(df_copy)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        csv = combined_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载对比数据CSV文件",
            data=csv,
            file_name=f"ETF对比分析_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
