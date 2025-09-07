import streamlit as st
import akshare as ak
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np

# 设置页面配置
st.set_page_config(
    page_title="金融数据分析平台",
    page_icon="📊",
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stSelectbox > div > div {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

def load_option_data(symbol, end_month):
    """加载期权数据"""
    try:
        with st.spinner(f"正在加载 {symbol} 的期权数据..."):
            df = ak.option_finance_board(symbol=symbol, end_month=end_month)
            return df
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        return None

def load_risk_indicator_data(date):
    """加载期权风险指标数据"""
    try:
        with st.spinner(f"正在加载 {date} 的风险指标数据..."):
            df = ak.option_risk_indicator_sse(date=date)
            # 添加调试信息
            if df is not None and not df.empty:
                st.success(f"成功加载 {len(df)} 条风险指标数据")
                # 检查列名
                expected_columns = ['TRADE_DATE', 'SECURITY_ID', 'CONTRACT_ID', 'CONTRACT_SYMBOL', 
                                  'DELTA_VALUE', 'THETA_VALUE', 'GAMMA_VALUE', 'VEGA_VALUE', 
                                  'RHO_VALUE', 'IMPLC_VOLATLTY']
                actual_columns = list(df.columns)
                if actual_columns != expected_columns:
                    st.warning(f"列名不匹配！期望: {expected_columns}, 实际: {actual_columns}")
            return df
    except Exception as e:
        st.error(f"风险指标数据加载失败: {str(e)}")
        # 添加更详细的错误信息
        st.error(f"请检查日期 {date} 是否为有效交易日")
        return None

def merge_option_and_risk_data(option_df, risk_df):
    """合并期权数据和风险指标数据"""
    if option_df is None or option_df.empty or risk_df is None or risk_df.empty:
        return None
    
    try:
        # 使用合约交易代码作为关联键
        # 期权数据中的合约交易代码列名是 '合约交易代码'
        # 风险指标数据中的合约代码列名是 'CONTRACT_ID'
        
        # 重命名列以便关联
        option_df_clean = option_df.copy()
        risk_df_clean = risk_df.copy()
        
        # 确保合约代码列名一致
        if '合约交易代码' in option_df_clean.columns:
            option_df_clean = option_df_clean.rename(columns={'合约交易代码': 'CONTRACT_ID'})
        
        # 合并数据
        merged_df = pd.merge(
            option_df_clean, 
            risk_df_clean, 
            on='CONTRACT_ID', 
            how='inner',  # 只保留两个数据源都有的合约
            suffixes=('_option', '_risk')
        )
        
        return merged_df
    except Exception as e:
        st.error(f"数据合并失败: {str(e)}")
        return None

def create_option_chart(df, chart_type="价格走势"):
    """创建期权图表"""
    if df is None or df.empty:
        return None
    
    # 分离看涨和看跌期权
    call_options = df[df['合约交易代码'].str.contains('C')]
    put_options = df[df['合约交易代码'].str.contains('P')]
    
    if chart_type == "价格走势":
        fig = go.Figure()
        
        # 添加看涨期权
        if not call_options.empty:
            fig.add_trace(go.Scatter(
                x=call_options['行权价'],
                y=call_options['当前价'],
                mode='markers+lines',
                name='看涨期权',
                marker=dict(color='red', size=8),
                line=dict(color='red', width=2)
            ))
        
        # 添加看跌期权
        if not put_options.empty:
            fig.add_trace(go.Scatter(
                x=put_options['行权价'],
                y=put_options['当前价'],
                mode='markers+lines',
                name='看跌期权',
                marker=dict(color='green', size=8),
                line=dict(color='green', width=2)
            ))
        
        fig.update_layout(
            title="期权价格 vs 行权价",
            xaxis_title="行权价",
            yaxis_title="当前价",
            hovermode='closest',
            height=500
        )
        
    elif chart_type == "涨跌幅分布":
        fig = px.histogram(
            df, 
            x='涨跌幅', 
            color='合约交易代码',
            title="涨跌幅分布",
            nbins=20
        )
        fig.update_layout(height=500)
        
    elif chart_type == "成交量分析":
        fig = px.bar(
            df, 
            x='合约交易代码', 
            y='数量',
            title="期权成交量",
            color='当前价',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=500, xaxis_tickangle=-45)
    
    return fig

def create_risk_indicator_chart(df, chart_type="Delta分布"):
    """创建风险指标图表"""
    if df is None or df.empty:
        return None
    
    # 检查必要的列是否存在
    required_columns = ['DELTA_VALUE', 'GAMMA_VALUE', 'THETA_VALUE', 'VEGA_VALUE', 'RHO_VALUE', 'IMPLC_VOLATLTY']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"缺少必要的列: {missing_columns}")
        return None
    
    if chart_type == "Delta分布":
        fig = px.histogram(
            df, 
            x='DELTA_VALUE', 
            title="Delta值分布",
            nbins=30,
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(height=400)
        
    elif chart_type == "隐含波动率":
        fig = px.scatter(
            df, 
            x='DELTA_VALUE', 
            y='IMPLC_VOLATLTY',
            title="Delta vs 隐含波动率",
            color='GAMMA_VALUE',
            size='VEGA_VALUE',
            hover_data=['CONTRACT_SYMBOL', 'THETA_VALUE', 'RHO_VALUE']
        )
        fig.update_layout(height=500)
        
    elif chart_type == "希腊字母热力图":
        # 创建希腊字母相关性热力图
        greek_columns = ['DELTA_VALUE', 'GAMMA_VALUE', 'THETA_VALUE', 'VEGA_VALUE', 'RHO_VALUE']
        corr_matrix = df[greek_columns].corr()
        
        fig = px.imshow(
            corr_matrix,
            title="希腊字母相关性热力图",
            color_continuous_scale='RdBu',
            aspect="auto"
        )
        fig.update_layout(height=400)
        
    elif chart_type == "Gamma vs Vega":
        fig = px.scatter(
            df, 
            x='GAMMA_VALUE', 
            y='VEGA_VALUE',
            title="Gamma vs Vega",
            color='IMPLC_VOLATLTY',
            size='DELTA_VALUE',
            hover_data=['CONTRACT_SYMBOL', 'THETA_VALUE', 'RHO_VALUE']
        )
        fig.update_layout(height=500)
        
    elif chart_type == "Theta分析":
        fig = px.box(
            df, 
            y='THETA_VALUE',
            title="Theta值分布箱线图"
        )
        fig.update_layout(height=400)
    
    return fig

def create_merged_chart(df, chart_type="价格与Delta关系"):
    """创建关联数据的图表"""
    if df is None or df.empty:
        return None
    
    # 检查必要的列是否存在
    required_columns = ['当前价', 'DELTA_VALUE', 'GAMMA_VALUE', 'THETA_VALUE', 'VEGA_VALUE', 'IMPLC_VOLATLTY']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"缺少必要的列: {missing_columns}")
        return None
    
    if chart_type == "价格与Delta关系":
        fig = px.scatter(
            df, 
            x='当前价', 
            y='DELTA_VALUE',
            title="期权价格 vs Delta值",
            color='IMPLC_VOLATLTY',
            size='GAMMA_VALUE',
            hover_data=['CONTRACT_ID', '行权价', 'THETA_VALUE', 'VEGA_VALUE']
        )
        fig.update_layout(height=500)
        
    elif chart_type == "隐含波动率与价格":
        fig = px.scatter(
            df, 
            x='当前价', 
            y='IMPLC_VOLATLTY',
            title="期权价格 vs 隐含波动率",
            color='DELTA_VALUE',
            size='VEGA_VALUE',
            hover_data=['CONTRACT_ID', '行权价', 'GAMMA_VALUE', 'THETA_VALUE']
        )
        fig.update_layout(height=500)
        
    elif chart_type == "希腊字母与价格":
        # 创建多个子图显示希腊字母与价格的关系
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Delta vs 价格', 'Gamma vs 价格', 'Theta vs 价格', 'Vega vs 价格'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Delta vs 价格
        fig.add_trace(
            go.Scatter(x=df['当前价'], y=df['DELTA_VALUE'], mode='markers', 
                      name='Delta', marker=dict(color='red')),
            row=1, col=1
        )
        
        # Gamma vs 价格
        fig.add_trace(
            go.Scatter(x=df['当前价'], y=df['GAMMA_VALUE'], mode='markers', 
                      name='Gamma', marker=dict(color='blue')),
            row=1, col=2
        )
        
        # Theta vs 价格
        fig.add_trace(
            go.Scatter(x=df['当前价'], y=df['THETA_VALUE'], mode='markers', 
                      name='Theta', marker=dict(color='green')),
            row=2, col=1
        )
        
        # Vega vs 价格
        fig.add_trace(
            go.Scatter(x=df['当前价'], y=df['VEGA_VALUE'], mode='markers', 
                      name='Vega', marker=dict(color='orange')),
            row=2, col=2
        )
        
        fig.update_layout(height=600, title_text="希腊字母与期权价格关系")
        
    elif chart_type == "风险收益分析":
        # 计算风险收益指标
        df_analysis = df.copy()
        df_analysis['风险收益比'] = df_analysis['当前价'] / df_analysis['VEGA_VALUE'].replace(0, 0.001)
        df_analysis['时间价值'] = df_analysis['当前价'] * abs(df_analysis['THETA_VALUE'])
        
        fig = px.scatter(
            df_analysis, 
            x='风险收益比', 
            y='时间价值',
            title="风险收益分析",
            color='DELTA_VALUE',
            size='当前价',
            hover_data=['CONTRACT_ID', '行权价', 'IMPLC_VOLATLTY']
        )
        fig.update_layout(height=500)
        
    elif chart_type == "波动率微笑":
        # 按行权价分组显示隐含波动率
        fig = px.scatter(
            df, 
            x='行权价', 
            y='IMPLC_VOLATLTY',
            title="波动率微笑",
            color='当前价',
            size='VEGA_VALUE',
            hover_data=['CONTRACT_ID', 'DELTA_VALUE', 'GAMMA_VALUE']
        )
        fig.update_layout(height=500)
    
    return fig

def main():
    # 主标题
    st.markdown('<h1 class="main-header">📊 金融数据分析平台</h1>', unsafe_allow_html=True)
    
    # 页面导航
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <a href="/" style="margin: 0 15px; padding: 10px 20px; background-color: #1f77b4; color: white; text-decoration: none; border-radius: 5px;">期权分析</a>
        <a href="/etf技术分析" style="margin: 0 15px; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">ETF技术分析</a>
        <a href="/etf对比分析" style="margin: 0 15px; padding: 10px 20px; background-color: #ffc107; color: black; text-decoration: none; border-radius: 5px;">ETF对比分析</a>
        <a href="/期权基础知识" style="margin: 0 15px; padding: 10px 20px; background-color: #6f42c1; color: white; text-decoration: none; border-radius: 5px;">期权基础知识</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2 class="main-header">📊 期权数据可视化分析</h2>', unsafe_allow_html=True)
    
    # 侧边栏配置
    st.sidebar.header("⚙️ 数据配置")
    
    # 期权标的选择
    option_symbols = {
        "华泰柏瑞沪深300ETF期权": "华泰柏瑞沪深300ETF期权",
        "华夏上证50ETF期权": "华夏上证50ETF期权",
        "嘉实沪深300ETF期权": "嘉实沪深300ETF期权"
    }
    
    selected_symbol = st.sidebar.selectbox(
        "选择期权标的",
        options=list(option_symbols.keys()),
        index=0
    )
    
    # 到期月份选择
    end_month = st.sidebar.text_input(
        "到期月份 (格式: YYMM, 如: 2212)",
        value="2212"
    )
    
    # 风险指标日期选择
    st.sidebar.subheader("📊 风险指标配置")
    
    # 获取最近的交易日（智能检测，排除周末）
    def get_latest_trading_day():
        """获取最近的交易日"""
        today = datetime.now().date()
        
        # 从今天开始往前找最近的交易日（排除周末）
        for i in range(10):  # 最多往前找10天
            test_date = today - timedelta(days=i)
            # 排除周末（周六=5, 周日=6）
            if test_date.weekday() < 5:  # 周一到周五
                return test_date
        
        # 如果都找不到，返回最近的周五
        days_since_friday = (today.weekday() + 3) % 7
        return today - timedelta(days=days_since_friday)
    
    # 使用最近的交易日作为默认值
    default_date = get_latest_trading_day()
    risk_date = st.sidebar.date_input(
        "风险指标日期",
        value=default_date,
        max_value=datetime.now().date()
    )
    risk_date_str = risk_date.strftime("%Y%m%d")
    
    # 显示当前选择的日期信息
    st.sidebar.info(f"📅 当前选择日期: {risk_date.strftime('%Y年%m月%d日')}")
    
    # 提示用户选择有效交易日
    if risk_date.weekday() >= 5:  # 周末
        st.sidebar.warning("⚠️ 选择的是周末，可能没有交易数据")
    else:
        st.sidebar.success("✅ 选择的是工作日，应该有交易数据")
    
    # 刷新按钮
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 刷新数据", type="primary"):
            st.rerun()
    with col2:
        if st.button("📅 重置为最近交易日"):
            st.rerun()
    
    # 自动刷新设置
    auto_refresh = st.sidebar.checkbox("自动刷新 (30秒)", value=False)
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # 加载数据
    df = load_option_data(option_symbols[selected_symbol], end_month)
    risk_df = load_risk_indicator_data(risk_date_str)
    
    # 合并期权数据和风险指标数据
    merged_df = None
    if df is not None and not df.empty and risk_df is not None and not risk_df.empty:
        merged_df = merge_option_and_risk_data(df, risk_df)
        if merged_df is not None and not merged_df.empty:
            st.success(f"✅ 成功关联 {len(merged_df)} 个合约的数据")
        else:
            st.warning("⚠️ 期权数据和风险指标数据无法关联，可能是合约代码不匹配")
    
    if df is not None and not df.empty:
        # 数据概览
        st.subheader("📈 数据概览")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总合约数", len(df))
        
        with col2:
            call_count = len(df[df['合约交易代码'].str.contains('C')])
            st.metric("看涨期权", call_count)
        
        with col3:
            put_count = len(df[df['合约交易代码'].str.contains('P')])
            st.metric("看跌期权", put_count)
        
        with col4:
            avg_price = df['当前价'].mean()
            st.metric("平均价格", f"{avg_price:.4f}")
        
        # 数据筛选
        st.subheader("🔍 数据筛选")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            option_type = st.selectbox("期权类型", ["全部", "看涨期权", "看跌期权"])
        
        with col2:
            min_price = st.number_input("最小价格", value=0.0, step=0.001)
        
        with col3:
            max_price = st.number_input("最大价格", value=float(df['当前价'].max()), step=0.001)
        
        # 应用筛选
        filtered_df = df.copy()
        
        if option_type == "看涨期权":
            filtered_df = filtered_df[filtered_df['合约交易代码'].str.contains('C')]
        elif option_type == "看跌期权":
            filtered_df = filtered_df[filtered_df['合约交易代码'].str.contains('P')]
        
        filtered_df = filtered_df[
            (filtered_df['当前价'] >= min_price) & 
            (filtered_df['当前价'] <= max_price)
        ]
        
        # 显示筛选后的数据
        st.subheader("📋 期权数据表")
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400
        )
        
        # 图表分析
        st.subheader("📊 图表分析")
        
        chart_type = st.selectbox(
            "选择图表类型",
            ["价格走势", "涨跌幅分布", "成交量分析"]
        )
        
        fig = create_option_chart(filtered_df, chart_type)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # 详细分析
        st.subheader("🔬 详细分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**看涨期权统计**")
            call_options = filtered_df[filtered_df['合约交易代码'].str.contains('C')]
            if not call_options.empty:
                st.write(f"- 平均价格: {call_options['当前价'].mean():.4f}")
                st.write(f"- 平均涨跌幅: {call_options['涨跌幅'].mean():.2f}%")
                st.write(f"- 最高价格: {call_options['当前价'].max():.4f}")
                st.write(f"- 最低价格: {call_options['当前价'].min():.4f}")
            else:
                st.write("无看涨期权数据")
        
        with col2:
            st.write("**看跌期权统计**")
            put_options = filtered_df[filtered_df['合约交易代码'].str.contains('P')]
            if not put_options.empty:
                st.write(f"- 平均价格: {put_options['当前价'].mean():.4f}")
                st.write(f"- 平均涨跌幅: {put_options['涨跌幅'].mean():.2f}%")
                st.write(f"- 最高价格: {put_options['当前价'].max():.4f}")
                st.write(f"- 最低价格: {put_options['当前价'].min():.4f}")
            else:
                st.write("无看跌期权数据")
        
        # 数据下载
        st.subheader("💾 数据下载")
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载期权数据CSV文件",
            data=csv,
            file_name=f"option_data_{selected_symbol}_{end_month}.csv",
            mime="text/csv"
        )
    
    # 风险指标分析
    if risk_df is not None and not risk_df.empty:
        st.subheader("📊 期权风险指标分析")
        
        # 风险指标概览
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("总合约数", len(risk_df))
        
        with col2:
            avg_delta = risk_df['DELTA_VALUE'].mean()
            st.metric("平均Delta", f"{avg_delta:.3f}")
        
        with col3:
            avg_gamma = risk_df['GAMMA_VALUE'].mean()
            st.metric("平均Gamma", f"{avg_gamma:.3f}")
        
        with col4:
            avg_theta = risk_df['THETA_VALUE'].mean()
            st.metric("平均Theta", f"{avg_theta:.3f}")
        
        with col5:
            avg_vega = risk_df['VEGA_VALUE'].mean()
            st.metric("平均Vega", f"{avg_vega:.3f}")
        
        # 风险指标筛选
        st.subheader("🔍 风险指标筛选")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_delta = st.number_input("最小Delta", value=float(risk_df['DELTA_VALUE'].min()), step=0.01)
            max_delta = st.number_input("最大Delta", value=float(risk_df['DELTA_VALUE'].max()), step=0.01)
        
        with col2:
            min_iv = st.number_input("最小隐含波动率", value=0.0, step=0.01)
            max_iv = st.number_input("最大隐含波动率", value=float(risk_df['IMPLC_VOLATLTY'].max()), step=0.01)
        
        with col3:
            min_gamma = st.number_input("最小Gamma", value=float(risk_df['GAMMA_VALUE'].min()), step=0.001)
            max_gamma = st.number_input("最大Gamma", value=float(risk_df['GAMMA_VALUE'].max()), step=0.001)
        
        # 应用风险指标筛选
        filtered_risk_df = risk_df[
            (risk_df['DELTA_VALUE'] >= min_delta) & 
            (risk_df['DELTA_VALUE'] <= max_delta) &
            (risk_df['IMPLC_VOLATLTY'] >= min_iv) & 
            (risk_df['IMPLC_VOLATLTY'] <= max_iv) &
            (risk_df['GAMMA_VALUE'] >= min_gamma) & 
            (risk_df['GAMMA_VALUE'] <= max_gamma)
        ]
        
        # 显示筛选后的风险指标数据
        st.subheader("📋 风险指标数据表")
        st.dataframe(
            filtered_risk_df,
            use_container_width=True,
            height=400
        )
        
        # 风险指标图表分析
        st.subheader("📊 风险指标图表分析")
        
        risk_chart_type = st.selectbox(
            "选择风险指标图表类型",
            ["Delta分布", "隐含波动率", "希腊字母热力图", "Gamma vs Vega", "Theta分析"]
        )
        
        risk_fig = create_risk_indicator_chart(filtered_risk_df, risk_chart_type)
        if risk_fig:
            st.plotly_chart(risk_fig, use_container_width=True)
        
        # 风险指标详细分析
        st.subheader("🔬 风险指标详细分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Delta分析**")
            st.write(f"- 平均Delta: {filtered_risk_df['DELTA_VALUE'].mean():.3f}")
            st.write(f"- Delta标准差: {filtered_risk_df['DELTA_VALUE'].std():.3f}")
            st.write(f"- 最大Delta: {filtered_risk_df['DELTA_VALUE'].max():.3f}")
            st.write(f"- 最小Delta: {filtered_risk_df['DELTA_VALUE'].min():.3f}")
            
            st.write("**Gamma分析**")
            st.write(f"- 平均Gamma: {filtered_risk_df['GAMMA_VALUE'].mean():.3f}")
            st.write(f"- Gamma标准差: {filtered_risk_df['GAMMA_VALUE'].std():.3f}")
            st.write(f"- 最大Gamma: {filtered_risk_df['GAMMA_VALUE'].max():.3f}")
            st.write(f"- 最小Gamma: {filtered_risk_df['GAMMA_VALUE'].min():.3f}")
        
        with col2:
            st.write("**Theta分析**")
            st.write(f"- 平均Theta: {filtered_risk_df['THETA_VALUE'].mean():.3f}")
            st.write(f"- Theta标准差: {filtered_risk_df['THETA_VALUE'].std():.3f}")
            st.write(f"- 最大Theta: {filtered_risk_df['THETA_VALUE'].max():.3f}")
            st.write(f"- 最小Theta: {filtered_risk_df['THETA_VALUE'].min():.3f}")
            
            st.write("**隐含波动率分析**")
            st.write(f"- 平均隐含波动率: {filtered_risk_df['IMPLC_VOLATLTY'].mean():.3f}")
            st.write(f"- 隐含波动率标准差: {filtered_risk_df['IMPLC_VOLATLTY'].std():.3f}")
            st.write(f"- 最大隐含波动率: {filtered_risk_df['IMPLC_VOLATLTY'].max():.3f}")
            st.write(f"- 最小隐含波动率: {filtered_risk_df['IMPLC_VOLATLTY'].min():.3f}")
        
        # 风险指标数据下载
        st.subheader("💾 风险指标数据下载")
        risk_csv = filtered_risk_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载风险指标CSV文件",
            data=risk_csv,
            file_name=f"risk_indicators_{risk_date_str}.csv",
            mime="text/csv"
        )
    
    else:
        st.warning("⚠️ 无法加载风险指标数据，请检查日期设置或网络连接")
    
    # 关联数据分析
    if merged_df is not None and not merged_df.empty:
        st.subheader("🔗 关联数据分析")
        
        # 关联数据概览
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("关联合约数", len(merged_df))
        
        with col2:
            avg_price_delta = merged_df['当前价'].corr(merged_df['DELTA_VALUE'])
            st.metric("价格-Delta相关性", f"{avg_price_delta:.3f}")
        
        with col3:
            avg_iv = merged_df['IMPLC_VOLATLTY'].mean()
            st.metric("平均隐含波动率", f"{avg_iv:.3f}")
        
        with col4:
            avg_vega = merged_df['VEGA_VALUE'].mean()
            st.metric("平均Vega", f"{avg_vega:.3f}")
        
        # 关联数据筛选
        st.subheader("🔍 关联数据筛选")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_price = st.number_input("最小价格", value=0.0, step=0.001, key="merged_price_min")
            max_price = st.number_input("最大价格", value=float(merged_df['当前价'].max()), step=0.001, key="merged_price_max")
        
        with col2:
            min_delta = st.number_input("最小Delta", value=float(merged_df['DELTA_VALUE'].min()), step=0.01, key="merged_delta_min")
            max_delta = st.number_input("最大Delta", value=float(merged_df['DELTA_VALUE'].max()), step=0.01, key="merged_delta_max")
        
        with col3:
            min_iv = st.number_input("最小隐含波动率", value=0.0, step=0.01, key="merged_iv_min")
            max_iv = st.number_input("最大隐含波动率", value=float(merged_df['IMPLC_VOLATLTY'].max()), step=0.01, key="merged_iv_max")
        
        # 应用关联数据筛选
        filtered_merged_df = merged_df[
            (merged_df['当前价'] >= min_price) & 
            (merged_df['当前价'] <= max_price) &
            (merged_df['DELTA_VALUE'] >= min_delta) & 
            (merged_df['DELTA_VALUE'] <= max_delta) &
            (merged_df['IMPLC_VOLATLTY'] >= min_iv) & 
            (merged_df['IMPLC_VOLATLTY'] <= max_iv)
        ]
        
        # 显示筛选后的关联数据
        st.subheader("📋 关联数据表")
        st.dataframe(
            filtered_merged_df[['CONTRACT_ID', '当前价', '涨跌幅', '行权价', 'DELTA_VALUE', 'GAMMA_VALUE', 
                               'THETA_VALUE', 'VEGA_VALUE', 'IMPLC_VOLATLTY']],
            use_container_width=True,
            height=400
        )
        
        # 关联数据图表分析
        st.subheader("📊 关联数据图表分析")
        
        merged_chart_type = st.selectbox(
            "选择关联分析图表类型",
            ["价格与Delta关系", "隐含波动率与价格", "希腊字母与价格", "风险收益分析", "波动率微笑"]
        )
        
        merged_fig = create_merged_chart(filtered_merged_df, merged_chart_type)
        if merged_fig:
            st.plotly_chart(merged_fig, use_container_width=True)
        
        # 关联数据详细分析
        st.subheader("🔬 关联数据详细分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**价格与风险指标关系**")
            price_delta_corr = filtered_merged_df['当前价'].corr(filtered_merged_df['DELTA_VALUE'])
            price_iv_corr = filtered_merged_df['当前价'].corr(filtered_merged_df['IMPLC_VOLATLTY'])
            price_gamma_corr = filtered_merged_df['当前价'].corr(filtered_merged_df['GAMMA_VALUE'])
            
            st.write(f"- 价格-Delta相关性: {price_delta_corr:.3f}")
            st.write(f"- 价格-隐含波动率相关性: {price_iv_corr:.3f}")
            st.write(f"- 价格-Gamma相关性: {price_gamma_corr:.3f}")
            
            st.write("**期权类型分析**")
            call_options = filtered_merged_df[filtered_merged_df['CONTRACT_ID'].str.contains('C')]
            put_options = filtered_merged_df[filtered_merged_df['CONTRACT_ID'].str.contains('P')]
            
            if not call_options.empty:
                st.write(f"- 看涨期权平均Delta: {call_options['DELTA_VALUE'].mean():.3f}")
                st.write(f"- 看涨期权平均隐含波动率: {call_options['IMPLC_VOLATLTY'].mean():.3f}")
            
            if not put_options.empty:
                st.write(f"- 看跌期权平均Delta: {put_options['DELTA_VALUE'].mean():.3f}")
                st.write(f"- 看跌期权平均隐含波动率: {put_options['IMPLC_VOLATLTY'].mean():.3f}")
        
        with col2:
            st.write("**风险指标统计**")
            st.write(f"- Delta标准差: {filtered_merged_df['DELTA_VALUE'].std():.3f}")
            st.write(f"- Gamma标准差: {filtered_merged_df['GAMMA_VALUE'].std():.3f}")
            st.write(f"- Theta标准差: {filtered_merged_df['THETA_VALUE'].std():.3f}")
            st.write(f"- Vega标准差: {filtered_merged_df['VEGA_VALUE'].std():.3f}")
            
            st.write("**隐含波动率分析**")
            st.write(f"- 隐含波动率标准差: {filtered_merged_df['IMPLC_VOLATLTY'].std():.3f}")
            st.write(f"- 隐含波动率范围: {filtered_merged_df['IMPLC_VOLATLTY'].min():.3f} - {filtered_merged_df['IMPLC_VOLATLTY'].max():.3f}")
            
            # 计算波动率微笑指标
            iv_skew = filtered_merged_df['IMPLC_VOLATLTY'].skew()
            st.write(f"- 波动率偏度: {iv_skew:.3f}")
        
        # 关联数据下载
        st.subheader("💾 关联数据下载")
        merged_csv = filtered_merged_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载关联数据CSV文件",
            data=merged_csv,
            file_name=f"merged_option_risk_{selected_symbol}_{end_month}_{risk_date_str}.csv",
            mime="text/csv"
        )
    
    if df is None or df.empty:
        st.warning("⚠️ 无法加载期权数据，请检查网络连接或参数设置")
        
        # 显示示例数据
        st.subheader("📋 期权数据示例")
        sample_data = {
            "日期": ["20220810122445", "20220810122445", "20220810122445"],
            "合约交易代码": ["510300C2212M03500", "510300P2212M03500", "510300C2212M03600"],
            "当前价": [0.6766, 0.0263, 0.0000],
            "涨跌幅": [-5.13, 15.86, 0.00],
            "前结价": [0.7132, 0.0227, 0.6240],
            "行权价": [3.5, 3.5, 3.6],
            "数量": [30, 30, 30]
        }
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True)
        
        st.subheader("📊 风险指标数据示例")
        sample_risk_data = {
            "TRADE_DATE": ["2024-06-26", "2024-06-26", "2024-06-26"],
            "SECURITY_ID": ["10007437", "10007425", "10007333"],
            "CONTRACT_ID": ["510300C2212M03500", "510300P2212M03500", "510300C2212M03600"],
            "DELTA_VALUE": [0.163, -0.163, 0.164],
            "GAMMA_VALUE": [0.182, 0.182, 0.149],
            "THETA_VALUE": [-0.001, -0.001, -0.002],
            "VEGA_VALUE": [0.012, 0.012, 0.011],
            "RHO_VALUE": [0.001, -0.001, 0.001],
            "IMPLC_VOLATLTY": [0.182, 0.182, 0.149]
        }
        sample_risk_df = pd.DataFrame(sample_risk_data)
        st.dataframe(sample_risk_df, use_container_width=True)

if __name__ == "__main__":
    main()
