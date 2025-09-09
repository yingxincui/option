import streamlit as st
import akshare as ak
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from st_copy_to_clipboard import st_copy_to_clipboard

def display_dataframe_with_copy(df, title="数据表格", key_suffix=""):
    """
    显示带复制按钮的DataFrame
    
    Args:
        df: pandas DataFrame
        title: 表格标题
        key_suffix: 用于区分不同表格的唯一后缀
    """
    if df is None or df.empty:
        st.warning("没有数据可显示")
        return
    
    # 创建两列布局
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f"**{title}**")
    
    with col2:
        # 将DataFrame转换为CSV格式用于复制
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        st_copy_to_clipboard(csv_data)
    
    # 显示表格
    st.dataframe(df, use_container_width=True)

def create_put_call_ratio_chart(df, name_col, ratio_col, exchange_name="交易所", chart_suffix=""):
    """
    创建认沽/认购比柱状图的共用函数
    
    Args:
        df: pandas DataFrame
        name_col: ETF名称列名
        ratio_col: 认沽认购比列名
        exchange_name: 交易所名称
    """
    if df is None or df.empty or name_col not in df.columns or ratio_col not in df.columns:
        st.warning("数据不足，无法生成图表")
        return
    
    st.markdown("#### 📊 认沽/认购比柱状图")
    
    # 创建认沽/认购比柱状图
    fig = go.Figure()
    
    # 按认沽/认购比排序
    sorted_df = df.sort_values(ratio_col, ascending=False)
    
    # 添加柱状图
    fig.add_trace(go.Bar(
        x=sorted_df[name_col],
        y=sorted_df[ratio_col],
        name='认沽/认购比',
        marker_color=['#ff6b6b' if x > 115 else '#ffa726' if x > 100 else '#66bb6a' for x in sorted_df[ratio_col]],
        text=sorted_df[ratio_col].round(2),
        textposition='outside'
    ))
    
    # 添加参考线
    fig.add_hline(y=100, line_dash="dash", line_color="blue", 
                 annotation_text="100%均衡线", annotation_position="top right")
    fig.add_hline(y=115, line_dash="dash", line_color="red", 
                 annotation_text="115%谨慎阈值", annotation_position="top right")
    
    # 更新布局
    fig.update_layout(
        title=f"{exchange_name}ETF认沽/认购比分析",
        xaxis_title="ETF名称",
        yaxis_title="认沽/认购比值 (%)",
        height=500,
        xaxis_tickangle=-45,
        showlegend=False,
        yaxis=dict(
            range=[0, max(sorted_df[ratio_col]) * 1.1]  # 留出空间显示文字
        )
    )
    
    # 添加颜色说明
    st.markdown("""
    **颜色说明：**
    - 🟢 绿色：多空均衡（≤100%）
    - 🟠 橙色：市场谨慎（100%-115%）
    - 🔴 红色：偏空情绪（>115%）
    """)
    
    st.plotly_chart(fig, use_container_width=True, key=f"put_call_ratio_{exchange_name}_{chart_suffix}")

def create_open_interest_stacked_chart(df, name_col, call_oi_col, put_oi_col, exchange_name="交易所", chart_suffix=""):
    """
    创建未平仓合约多空分布对比条形图的共用函数
    
    Args:
        df: pandas DataFrame
        name_col: ETF名称列名
        call_oi_col: 认购未平仓合约列名
        put_oi_col: 认沽未平仓合约列名
        exchange_name: 交易所名称
    """
    if df is None or df.empty or name_col not in df.columns or call_oi_col not in df.columns or put_oi_col not in df.columns:
        st.warning("数据不足，无法生成持仓量分布图表")
        return
    
    st.markdown("#### 📊 持仓量多空分布对比条形图")
    
    # 创建对比条形图
    fig = go.Figure()
    
    # 按总未平仓合约数排序
    df_with_total = df.copy()
    df_with_total['总未平仓'] = df_with_total[call_oi_col] + df_with_total[put_oi_col]
    sorted_df = df_with_total.sort_values('总未平仓', ascending=False)
    
    # 添加认购未平仓合约
    fig.add_trace(go.Bar(
        name='认购未平仓',
        x=sorted_df[name_col],
        y=sorted_df[call_oi_col],
        marker_color='#2E8B57',  # 深绿色
        text=sorted_df[call_oi_col].apply(lambda x: f"{x:,}"),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>认购未平仓: %{y:,} 张<extra></extra>'
    ))
    
    # 添加认沽未平仓合约
    fig.add_trace(go.Bar(
        name='认沽未平仓',
        x=sorted_df[name_col],
        y=sorted_df[put_oi_col],
        marker_color='#DC143C',  # 深红色
        text=sorted_df[put_oi_col].apply(lambda x: f"{x:,}"),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>认沽未平仓: %{y:,} 张<extra></extra>'
    ))
    
    # 更新布局
    fig.update_layout(
        title=f"{exchange_name}ETF未平仓合约多空分布",
        xaxis_title="ETF名称",
        yaxis_title="未平仓合约数量 (张)",
        barmode='group',  # 并排模式
        height=500,
        xaxis_tickangle=-45,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            range=[0, max(max(sorted_df[call_oi_col]), max(sorted_df[put_oi_col])) * 1.1]  # 留出空间显示文字
        )
    )
    
    # 添加说明
    st.markdown("""
    **颜色说明：**
    - 🟢 深绿色：认购未平仓合约（看涨持仓）
    - 🔴 深红色：认沽未平仓合约（看跌持仓）
    - 并排对比：直观显示多空力量对比
    - 高度对比：直接比较认购认沽持仓量
    """)
    
    st.plotly_chart(fig, use_container_width=True, key=f"open_interest_{exchange_name}_{chart_suffix}")

def create_volume_turnover_dual_axis_chart(df, name_col, volume_col, turnover_col, exchange_name="交易所", chart_suffix=""):
    """
    创建成交额与成交量对比图表的共用函数（左右并排显示）
    
    Args:
        df: pandas DataFrame
        name_col: ETF名称列名
        volume_col: 成交量列名
        turnover_col: 成交额列名
        exchange_name: 交易所名称
    """
    if df is None or df.empty or name_col not in df.columns or volume_col not in df.columns or turnover_col not in df.columns:
        st.warning("数据不足，无法生成成交额与成交量对比图表")
        return
    
    st.markdown("#### 📊 成交额与成交量对比图表")
    
    # 按成交额从大到小排序
    sorted_df = df.sort_values(turnover_col, ascending=False)
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        # 成交额柱状图
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            name='成交额(万元)',
            x=sorted_df[name_col],
            y=sorted_df[turnover_col],
            marker_color='#1f77b4',  # 蓝色
            text=sorted_df[turnover_col].apply(lambda x: f"{x:,}"),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>成交额: %{y:,} 万元<extra></extra>'
        ))
        
        fig1.update_layout(
            title=f"{exchange_name}ETF成交额对比",
            xaxis_title="ETF名称",
            yaxis_title="成交额 (万元)",
            height=500,
            xaxis_tickangle=-45,
            showlegend=False
        )
        
        st.plotly_chart(fig1, use_container_width=True, key=f"turnover_{exchange_name}_{chart_suffix}")
    
    with col2:
        # 成交量柱状图
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name='成交量(张)',
            x=sorted_df[name_col],
            y=sorted_df[volume_col],
            marker_color='#ff7f0e',  # 橙色
            text=sorted_df[volume_col].apply(lambda x: f"{x:,}"),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>成交量: %{y:,} 张<extra></extra>'
        ))
        
        fig2.update_layout(
            title=f"{exchange_name}ETF成交量对比",
            xaxis_title="ETF名称",
            yaxis_title="成交量 (张)",
            height=500,
            xaxis_tickangle=-45,
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True, key=f"volume_{exchange_name}_{chart_suffix}")
    
    # 添加说明
    st.markdown("""
    **图表说明：**
    - 🔵 左图：成交额（万元）- 显示资金参与度
    - 🟠 右图：成交量（张）- 显示交易活跃度
    - 并排对比：直观显示各ETF的流动性和资金参与度
    - 高度对比：成交额高说明资金集中，成交量高说明交易活跃
    """)

# 设置页面配置
st.set_page_config(
    page_title="每日统计",
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .exchange-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .data-table {
        font-size: 14px;
    }
    .data-table th {
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .data-table td {
        text-align: center;
        vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800)  # 缓存30分钟
def load_sse_daily_stats(date):
    """加载上交所期权每日统计数据"""
    try:
        with st.spinner(f"正在加载上交所 {date} 的每日统计数据..."):
            df = ak.option_daily_stats_sse(date=date)
            return df
    except Exception as e:
        st.error(f"上交所数据加载失败: {str(e)}")
        return None

@st.cache_data(ttl=1800)  # 缓存30分钟
def load_szse_daily_stats(date):
    """加载深交所期权每日统计数据"""
    try:
        with st.spinner(f"正在加载深交所 {date} 的每日统计数据..."):
            df = ak.option_daily_stats_szse(date=date)
            if df is not None and not df.empty:
                return df
            else:
                return None
    except Exception as e:
        st.error(f"深交所数据加载失败: {str(e)}")
        return None

def create_volume_chart(sse_df, szse_df, chart_type="成交量对比"):
    """创建成交量相关图表"""
    if sse_df is None or sse_df.empty:
        return None
    
    if chart_type == "成交量对比":
        # 合并两个交易所的数据
        sse_volume = sse_df[['合约标的名称', '总成交量']].copy()
        sse_volume['交易所'] = '上交所'
        sse_volume = sse_volume.rename(columns={'总成交量': '成交量'})
        
        if szse_df is not None and not szse_df.empty:
            # 查找深交所的列名
            name_col = None
            volume_col = None
            for col in szse_df.columns:
                if '名称' in col:
                    name_col = col
                elif '成交量' in col and '认购' not in col and '认沽' not in col:
                    volume_col = col
            
            if name_col is not None and volume_col is not None:
                szse_volume = szse_df[[name_col, volume_col]].copy()
                szse_volume['交易所'] = '深交所'
                szse_volume = szse_volume.rename(columns={volume_col: '成交量'})
            else:
                szse_volume = None
            
            combined_df = pd.concat([sse_volume, szse_volume], ignore_index=True)
        else:
            combined_df = sse_volume
        
        # 按成交量从大到小排序
        combined_df = combined_df.sort_values('成交量', ascending=False)
        
        fig = px.bar(
            combined_df, 
            x='合约标的名称', 
            y='成交量',
            color='交易所',
            title="上交所各ETF期权成交量对比",
            barmode='group'
        )
        fig.update_layout(
            height=500,
            xaxis_tickangle=-45,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
    elif chart_type == "认沽认购比":
        if sse_df is not None and not sse_df.empty:
            # 按认沽/认购比从大到小排序
            sorted_df = sse_df.sort_values('认沽/认购', ascending=False)
            
            fig = px.bar(
                sorted_df, 
                x='合约标的名称', 
                y='认沽/认购',
                title="上交所认沽/认购比例",
                color='认沽/认购',
                color_continuous_scale='RdYlBu_r'
            )
            fig.update_layout(
                height=500,
                xaxis_tickangle=-45
            )
        
    elif chart_type == "未平仓合约":
        if sse_df is not None and not sse_df.empty:
            # 按未平仓合约总数从大到小排序
            sorted_df = sse_df.sort_values('未平仓合约总数', ascending=False)
            
            fig = px.bar(
                sorted_df, 
                x='合约标的名称', 
                y='未平仓合约总数',
                title="上交所未平仓合约总数",
                color='未平仓合约总数',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(
                height=500,
                xaxis_tickangle=-45
            )
    
    return fig

def create_turnover_chart(sse_df, chart_type="成交额对比"):
    """创建成交额相关图表"""
    if sse_df is None or sse_df.empty:
        return None
    
    if chart_type == "成交额对比":
        # 按成交额从大到小排序
        sorted_df = sse_df.sort_values('总成交额', ascending=False)
        
        fig = px.bar(
            sorted_df, 
            x='合约标的名称', 
            y='总成交额',
            title="上交所各ETF期权成交额对比",
            color='总成交额',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            height=500,
            xaxis_tickangle=-45
        )
        
    elif chart_type == "成交额分布":
        # 按成交额从大到小排序
        sorted_df = sse_df.sort_values('总成交额', ascending=False)
        
        fig = px.pie(
            sorted_df, 
            values='总成交额', 
            names='合约标的名称',
            title="上交所成交额分布饼图"
        )
        fig.update_layout(height=500)
        
    elif chart_type == "合约数量":
        # 按合约数量从大到小排序
        sorted_df = sse_df.sort_values('合约数量', ascending=False)
        
        fig = px.bar(
            sorted_df, 
            x='合约标的名称', 
            y='合约数量',
            title="上交所各ETF期权合约数量",
            color='合约数量',
            color_continuous_scale='Greens'
        )
        fig.update_layout(
            height=500,
            xaxis_tickangle=-45
        )
    
    return fig

def create_put_call_chart(sse_df, chart_type="认沽认购分析"):
    """创建认沽认购相关图表"""
    if sse_df is None or sse_df.empty:
        return None
    
    if chart_type == "认沽认购分析":
        # 按总成交量从大到小排序
        sorted_df = sse_df.sort_values('总成交量', ascending=False)
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('认购成交量', '认沽成交量', '认沽/认购比例', '未平仓认沽认购比'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 认购成交量
        fig.add_trace(
            go.Bar(x=sorted_df['合约标的名称'], y=sorted_df['认购成交量'], name='认购成交量', marker_color='#1f77b4'),
            row=1, col=1
        )
        
        # 认沽成交量
        fig.add_trace(
            go.Bar(x=sorted_df['合约标的名称'], y=sorted_df['认沽成交量'], name='认沽成交量', marker_color='#ff7f0e'),
            row=1, col=2
        )
        
        # 认沽/认购比例
        fig.add_trace(
            go.Bar(x=sorted_df['合约标的名称'], y=sorted_df['认沽/认购'], name='认沽/认购比例', marker_color='#2ca02c'),
            row=2, col=1
        )
        
        # 未平仓认沽认购比
        if '未平仓认购合约数' in sorted_df.columns and '未平仓认沽合约数' in sorted_df.columns:
            put_call_ratio = sorted_df['未平仓认沽合约数'] / sorted_df['未平仓认购合约数']
            fig.add_trace(
                go.Bar(x=sorted_df['合约标的名称'], y=put_call_ratio, name='未平仓认沽认购比', marker_color='#d62728'),
                row=2, col=2
            )
        
        fig.update_layout(height=600, showlegend=False)
        fig.update_xaxes(tickangle=-45)
        
    elif chart_type == "认沽认购散点图":
        # 按总成交量从大到小排序
        sorted_df = sse_df.sort_values('总成交量', ascending=False)
        
        fig = px.scatter(
            sorted_df, 
            x='认购成交量', 
            y='认沽成交量',
            size='总成交量',
            color='认沽/认购',
            hover_name='合约标的名称',
            title="上交所认购成交量 vs 认沽成交量",
            color_continuous_scale='RdYlBu_r'
        )
        fig.update_layout(height=500)
    
    return fig

def create_szse_volume_chart(szse_df, chart_type="成交量对比"):
    """创建深交所成交量相关图表"""
    if szse_df is None or szse_df.empty:
        return None
    
    if chart_type == "成交量对比":
        # 查找成交量列
        volume_col = None
        name_col = None
        for col in szse_df.columns:
            if '成交量' in col and '认购' not in col and '认沽' not in col:
                volume_col = col
            elif '名称' in col:
                name_col = col
        
        if volume_col is not None and name_col is not None:
            # 按成交量从大到小排序
            sorted_df = szse_df.sort_values(volume_col, ascending=False)
            
            fig = px.bar(
                sorted_df, 
                x=name_col, 
                y=volume_col,
                title="深交所各ETF期权成交量对比",
                color=volume_col,
                color_continuous_scale='Greens'
            )
            fig.update_layout(
                height=500,
                xaxis_tickangle=-45
            )
        else:
            return None
        
    elif chart_type == "认沽认购比":
        # 查找认沽/认购持仓比列
        ratio_col = None
        name_col = None
        for col in szse_df.columns:
            if '认沽' in col and '认购' in col and '持仓' in col:
                ratio_col = col
            elif '名称' in col:
                name_col = col
        
        if ratio_col is not None and name_col is not None:
            # 按认沽/认购持仓比从大到小排序
            sorted_df = szse_df.sort_values(ratio_col, ascending=False)
            
            fig = px.bar(
                sorted_df, 
                x=name_col, 
                y=ratio_col,
                title="深交所认沽/认购持仓比",
                color=ratio_col,
                color_continuous_scale='RdYlBu_r'
            )
            fig.update_layout(
                height=500,
                xaxis_tickangle=-45
            )
        else:
            return None
        
    elif chart_type == "未平仓合约":
        # 查找未平仓合约总数列
        open_interest_col = None
        name_col = None
        for col in szse_df.columns:
            if '未平仓' in col and '总数' in col:
                open_interest_col = col
            elif '名称' in col:
                name_col = col
        
        if open_interest_col is not None and name_col is not None:
            # 按未平仓合约总数从大到小排序
            sorted_df = szse_df.sort_values(open_interest_col, ascending=False)
            
            fig = px.bar(
                sorted_df, 
                x=name_col, 
                y=open_interest_col,
                title="深交所未平仓合约总数",
                color=open_interest_col,
                color_continuous_scale='Viridis'
            )
            fig.update_layout(
                height=500,
                xaxis_tickangle=-45
            )
        else:
            return None
    
    return fig

def create_szse_put_call_chart(szse_df, chart_type="认沽认购分析"):
    """创建深交所认沽认购相关图表"""
    if szse_df is None or szse_df.empty:
        return None
    
    # 查找相关列
    name_col = None
    volume_col = None
    call_volume_col = None
    put_volume_col = None
    ratio_col = None
    call_open_col = None
    put_open_col = None
    
    for col in szse_df.columns:
        if '名称' in col:
            name_col = col
        elif '成交量' in col and '认购' not in col and '认沽' not in col:
            volume_col = col
        elif '认购' in col and '成交量' in col:
            call_volume_col = col
        elif '认沽' in col and '成交量' in col:
            put_volume_col = col
        elif '认沽' in col and '认购' in col and '持仓' in col:
            ratio_col = col
        elif '未平仓' in col and '认购' in col:
            call_open_col = col
        elif '未平仓' in col and '认沽' in col:
            put_open_col = col
    
    if chart_type == "认沽认购分析":
        if name_col is not None and volume_col is not None:
            # 按成交量从大到小排序
            sorted_df = szse_df.sort_values(volume_col, ascending=False)
            
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('认购成交量', '认沽成交量', '认沽/认购持仓比', '未平仓认沽认购比'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # 认购成交量
            if call_volume_col is not None:
                fig.add_trace(
                    go.Bar(x=sorted_df[name_col], y=sorted_df[call_volume_col], name='认购成交量', marker_color='#1f77b4'),
                    row=1, col=1
                )
            
            # 认沽成交量
            if put_volume_col is not None:
                fig.add_trace(
                    go.Bar(x=sorted_df[name_col], y=sorted_df[put_volume_col], name='认沽成交量', marker_color='#ff7f0e'),
                    row=1, col=2
                )
            
            # 认沽/认购持仓比
            if ratio_col is not None:
                fig.add_trace(
                    go.Bar(x=sorted_df[name_col], y=sorted_df[ratio_col], name='认沽/认购持仓比', marker_color='#2ca02c'),
                    row=2, col=1
                )
            
            # 未平仓认沽认购比
            if call_open_col is not None and put_open_col is not None:
                put_call_ratio = sorted_df[put_open_col] / sorted_df[call_open_col]
                fig.add_trace(
                    go.Bar(x=sorted_df[name_col], y=put_call_ratio, name='未平仓认沽认购比', marker_color='#d62728'),
                    row=2, col=2
                )
            
            fig.update_layout(height=600, showlegend=False)
            fig.update_xaxes(tickangle=-45)
        else:
            return None
        
    elif chart_type == "认沽认购散点图":
        if (name_col is not None and call_volume_col is not None and 
            put_volume_col is not None and volume_col is not None and ratio_col is not None):
            # 按成交量从大到小排序
            sorted_df = szse_df.sort_values(volume_col, ascending=False)
            
            fig = px.scatter(
                sorted_df, 
                x=call_volume_col, 
                y=put_volume_col,
                size=volume_col,
                color=ratio_col,
                hover_name=name_col,
                title="深交所认购成交量 vs 认沽成交量",
                color_continuous_scale='RdYlBu_r'
            )
            fig.update_layout(height=500)
        else:
            return None
    
    return fig

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

def calculate_market_indicators(sse_df, szse_df):
    """计算市场指标"""
    indicators = {}
    
    if sse_df is not None and not sse_df.empty:
        # 上交所指标
        indicators['sse'] = {
            'total_volume': sse_df['总成交量'].sum(),
            'total_turnover': sse_df['总成交额'].sum(),
            'total_contracts': sse_df['合约数量'].sum(),
            'avg_put_call_ratio': sse_df['认沽/认购'].mean(),
            'max_volume_etf': sse_df.loc[sse_df['总成交量'].idxmax(), '合约标的名称'],
            'max_turnover_etf': sse_df.loc[sse_df['总成交额'].idxmax(), '合约标的名称'],
            'total_open_interest': sse_df['未平仓合约总数'].sum()
        }
    
    if szse_df is not None and not szse_df.empty:
        # 查找深交所的列名
        name_col = None
        volume_col = None
        ratio_col = None
        open_interest_col = None
        
        for col in szse_df.columns:
            if '名称' in col:
                name_col = col
            elif '成交量' in col and '认购' not in col and '认沽' not in col:
                volume_col = col
            elif '认沽' in col and '认购' in col and '持仓' in col:
                ratio_col = col
            elif '未平仓' in col and '总数' in col:
                open_interest_col = col
        
        # 深交所指标
        indicators['szse'] = {
            'total_volume': szse_df[volume_col].sum() if volume_col else 0,
            'total_contracts': len(szse_df),
            'avg_put_call_ratio': szse_df[ratio_col].mean() if ratio_col else 0,
            'max_volume_etf': szse_df.loc[szse_df[volume_col].idxmax(), name_col] if name_col and volume_col else "未知",
            'total_open_interest': szse_df[open_interest_col].sum() if open_interest_col else 0
        }
    
    return indicators

def create_market_summary(indicators):
    """创建市场总结"""
    if not indicators:
        return None
    
    # 使用Streamlit原生组件显示市场总结
    st.markdown("### 📈 市场总结")
    
    if 'sse' in indicators:
        sse = indicators['sse']
        
        # 上交所数据卡片
        with st.container():
            st.markdown("#### 🏛️ 上海证券交易所")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("总成交量", f"{sse['total_volume']:,} 张")
                st.metric("总成交额", f"{sse['total_turnover']:,} 万元")
            
            with col2:
                st.metric("合约总数", f"{sse['total_contracts']:,} 个")
                st.metric("平均认沽认购比", f"{sse['avg_put_call_ratio']:.2f}")
            
            with col3:
                st.metric("成交量最大ETF", sse['max_volume_etf'])
                st.metric("成交额最大ETF", sse['max_turnover_etf'])
    
    if 'szse' in indicators:
        szse = indicators['szse']
        
        # 深交所数据卡片
        with st.container():
            st.markdown("#### 🏛️ 深圳证券交易所")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("总成交量", f"{szse['total_volume']:,} 张")
                st.metric("合约总数", f"{szse['total_contracts']:,} 个")
            
            with col2:
                st.metric("平均认沽认购比", f"{szse['avg_put_call_ratio']:.2f}")
                st.metric("成交量最大ETF", szse['max_volume_etf'])
    
    return True  # 返回True表示成功创建了总结

def main():
    # 主标题
    st.markdown('<h1 class="main-header">📊 期权每日统计</h1>', unsafe_allow_html=True)
    
    # 侧边栏配置
    st.sidebar.header("⚙️ 数据配置")
    
    # 日期选择
    default_date = get_latest_trading_day()
    selected_date = st.sidebar.date_input(
        "选择统计日期",
        value=default_date,
        max_value=datetime.now().date()
    )
    date_str = selected_date.strftime("%Y%m%d")
    
    # 对比日期选择
    st.sidebar.subheader("📊 数据对比")
    compare_enabled = st.sidebar.checkbox("启用数据对比", value=False)
    compare_date = None
    if compare_enabled:
        compare_date = st.sidebar.date_input(
            "选择对比日期",
            value=default_date - timedelta(days=1),
            max_value=datetime.now().date()
        )
        compare_date_str = compare_date.strftime("%Y%m%d")
    
    # 显示当前选择的日期信息
    st.sidebar.info(f"📅 当前选择日期: {selected_date.strftime('%Y年%m月%d日')}")
    
    # 提示用户选择有效交易日
    if selected_date.weekday() >= 5:  # 周末
        st.sidebar.warning("⚠️ 选择的是周末，可能没有交易数据")
    else:
        st.sidebar.success("✅ 选择的是工作日，应该有交易数据")
    
    # 刷新按钮
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 刷新数据", type="primary"):
            st.rerun()
    with col2:
        if st.button("🗑️ 清除缓存"):
            st.cache_data.clear()
            st.success("缓存已清除！")
            st.rerun()
    
    # 加载数据
    sse_df = load_sse_daily_stats(date_str)
    szse_df = load_szse_daily_stats(date_str)
    
    # 加载对比数据
    compare_sse_df = None
    compare_szse_df = None
    if compare_enabled and compare_date:
        compare_sse_df = load_sse_daily_stats(compare_date_str)
        compare_szse_df = load_szse_daily_stats(compare_date_str)
    
    # 计算市场指标
    indicators = calculate_market_indicators(sse_df, szse_df)
        
        # 市场洞察 - 期权市场情绪分析
    if sse_df is not None and not sse_df.empty or szse_df is not None and not szse_df.empty:
        st.subheader("💡 市场洞察 - 期权市场情绪分析")
        
        # 认沽认购比说明
        with st.expander("📚 认沽认购比说明", expanded=False):
            st.markdown("""
            **认沽认购比（Put/Call Ratio）** 是期权市场的重要情绪指标：
            
            **📊 计算公式：**
            - 认沽认购比 = 认沽期权成交量 ÷ 认购期权成交量
            
            **📈 指标含义：**
            - **< 70%**：市场情绪积极，看涨意愿强烈
            - **70% - 100%**：市场情绪相对均衡，多空力量平衡
            - **100% - 120%**：市场情绪谨慎，避险需求较高
            - **> 120%**：市场情绪悲观，看跌情绪浓厚
            
            **💡 投资参考：**
            - 认沽认购比过高时，可能预示着市场底部即将到来（反向指标）
            - 认沽认购比过低时，可能预示着市场顶部即将到来
            - 结合成交量和其他技术指标使用效果更佳
            
            **⚠️ 注意事项：**
            - 该指标仅反映短期市场情绪，不构成投资建议
            - 需要结合基本面分析和其他技术指标综合判断
            - 数据可能存在延迟，请以交易所官方数据为准
            """)
        
        # 未平仓合约说明
        with st.expander("📊 未平仓合约说明", expanded=False):
            st.markdown("""
            **未平仓合约（Open Interest）** 是期权市场的重要持仓指标：
            
            **📋 基本概念：**
            - **未平仓认购合约数**：尚未平仓的认购期权合约总数
            - **未平仓认沽合约数**：尚未平仓的认沽期权合约总数
            - **未平仓合约总数**：所有未平仓期权合约的总和
            
            **📈 指标含义：**
            - **未平仓认购合约数 > 未平仓认沽合约数**：市场看涨情绪较强
            - **未平仓认沽合约数 > 未平仓认购合约数**：市场看跌情绪较强，避险需求高
            - **未平仓合约总数增加**：市场参与度提高，流动性增强
            - **未平仓合约总数减少**：市场参与度降低，流动性减弱
            
            **💡 投资参考：**
            - **高未平仓认购**：可能预示着上涨压力，但需注意是否过度乐观
            - **高未平仓认沽**：可能预示着下跌风险，但也可作为反向指标
            - **未平仓合约集中**：在特定行权价附近，可能形成支撑或阻力位
            - **未平仓合约分散**：市场观点分歧较大，波动性可能增加
            
            **🔍 分析要点：**
            - 结合成交量分析，判断市场活跃度
            - 关注行权价分布，识别关键支撑阻力位
            - 观察未平仓合约变化趋势，判断市场情绪转换
            - 与认沽认购比结合使用，获得更全面的市场洞察
            
            **⚠️ 注意事项：**
            - 未平仓合约数据反映的是持仓情况，不是交易活跃度
            - 需要结合到期时间、行权价等因素综合分析
            - 数据可能存在延迟，请以交易所官方数据为准
            """)
        
        # 上交所分析
        if sse_df is not None and not sse_df.empty:
            st.markdown("#### 🏛️ 上海证券交易所分析")
            
            # 计算上交所核心指标
            sse_total_volume = sse_df['总成交量'].sum()
            sse_total_turnover = sse_df['总成交额'].sum()
            sse_avg_put_call_ratio = sse_df['认沽/认购'].mean()
            sse_max_volume_etf = sse_df.loc[sse_df['总成交量'].idxmax(), '合约标的名称']
            sse_max_turnover_etf = sse_df.loc[sse_df['总成交额'].idxmax(), '合约标的名称']
            
            # 上交所情绪分析
            sse_optimistic_etfs = sse_df[sse_df['认沽/认购'] < 70]
            sse_balanced_etfs = sse_df[(sse_df['认沽/认购'] >= 70) & (sse_df['认沽/认购'] <= 100)]
            sse_cautious_etfs = sse_df[(sse_df['认沽/认购'] > 100) & (sse_df['认沽/认购'] <= 120)]
            sse_pessimistic_etfs = sse_df[sse_df['认沽/认购'] > 120]
            
            # 上交所未平仓分析
            sse_high_put_oi_etfs = sse_df[sse_df['未平仓认沽合约数'] > sse_df['未平仓认购合约数']]
            sse_high_call_oi_etfs = sse_df[sse_df['未平仓认购合约数'] > sse_df['未平仓认沽合约数']]
            sse_total_open_interest = sse_df['未平仓合约总数'].sum()
            sse_avg_put_call_oi_ratio = (sse_df['未平仓认沽合约数'].sum() / sse_df['未平仓认购合约数'].sum()) * 100
            
            # 计算持仓集中度（前3名ETF的未平仓合约占比）
            sse_top3_oi_etfs = sse_df.nlargest(3, '未平仓合约总数')
            sse_concentration_ratio = (sse_top3_oi_etfs['未平仓合约总数'].sum() / sse_total_open_interest) * 100
            
            
            # 综合市场情绪分析 - 合并认沽认购比和未平仓合约分析
            st.write("**📊 综合市场情绪分析：**")
            
            # 为每个ETF生成综合分析
            def generate_comprehensive_analysis(row):
                analysis_parts = []
                
                # 认沽认购比分析
                put_call_ratio = row['认沽/认购']
                if put_call_ratio < 70:
                    analysis_parts.append(f"📈 看涨情绪强烈({put_call_ratio:.2f}%)")
                elif put_call_ratio <= 100:
                    analysis_parts.append(f"⚖️ 多空均衡({put_call_ratio:.2f}%)")
                elif put_call_ratio <= 120:
                    analysis_parts.append(f"⚠️ 市场谨慎({put_call_ratio:.2f}%)")
                else:
                    analysis_parts.append(f"📉 看跌情绪较重({put_call_ratio:.2f}%)")
                
                # 未平仓合约分析
                put_oi = row['未平仓认沽合约数']
                call_oi = row['未平仓认购合约数']
                if put_oi > call_oi:
                    oi_ratio = (put_oi / call_oi) * 100
                    analysis_parts.append(f"⚠️ 认沽持仓占优({oi_ratio:.1f}%)")
                elif call_oi > put_oi:
                    oi_ratio = (call_oi / put_oi) * 100
                    analysis_parts.append(f"📈 认购持仓占优({oi_ratio:.1f}%)")
                else:
                    analysis_parts.append("⚖️ 持仓均衡")
                
                return " | ".join(analysis_parts)
            
            # 为每个ETF生成分析并分组
            etf_analysis = []
            for _, row in sse_df.iterrows():
                analysis = generate_comprehensive_analysis(row)
                etf_analysis.append({
                    'name': f"{row['合约标的名称']}({row['合约标的代码']})",
                    'analysis': analysis,
                    'put_call_ratio': row['认沽/认购'],
                    'volume': row['总成交量']
                })
            
            # 按市场情绪分组
            def get_sentiment_group(analysis):
                if "看涨情绪强烈" in analysis:
                    return "看涨情绪强烈"
                elif "多空均衡" in analysis:
                    return "多空均衡"
                elif "市场谨慎" in analysis:
                    return "市场谨慎"
                elif "看跌情绪较重" in analysis:
                    return "看跌情绪较重"
                else:
                    return "其他"
            
            # 分组并排序
            groups = {}
            for etf in etf_analysis:
                group = get_sentiment_group(etf['analysis'])
                if group not in groups:
                    groups[group] = []
                groups[group].append(etf)
            
            # 按组内成交量排序
            for group in groups:
                groups[group].sort(key=lambda x: x['volume'], reverse=True)
            
            # 按组顺序显示（看涨->均衡->谨慎->看跌）
            group_order = ["看涨情绪强烈", "多空均衡", "市场谨慎", "看跌情绪较重", "其他"]
            for group in group_order:
                if group in groups and groups[group]:
                    st.write(f"**{group}ETF：**")
                    for etf in groups[group]:
                        # 解析分析内容，添加详细说明
                        analysis_parts = etf['analysis'].split(' | ')
                        detailed_analysis = []
                        for part in analysis_parts:
                            if "看涨情绪强烈" in part:
                                ratio = part.split('(')[1].split(')')[0]
                                detailed_analysis.append(f"{part}（认沽认购比{ratio}，看涨意愿强烈）")
                            elif "多空均衡" in part:
                                ratio = part.split('(')[1].split(')')[0]
                                detailed_analysis.append(f"{part}（认沽认购比{ratio}，多空力量平衡）")
                            elif "市场谨慎" in part:
                                ratio = part.split('(')[1].split(')')[0]
                                detailed_analysis.append(f"{part}（认沽认购比{ratio}，避险需求较高）")
                            elif "看跌情绪较重" in part:
                                ratio = part.split('(')[1].split(')')[0]
                                detailed_analysis.append(f"{part}（认沽认购比{ratio}，看跌情绪浓厚）")
                            elif "认购持仓占优" in part:
                                ratio = part.split('(')[1].split(')')[0].replace('%', '')
                                detailed_analysis.append(f"{part}（认购未平仓比认沽多{float(ratio)-100:.1f}个百分点）")
                            elif "认沽持仓占优" in part:
                                ratio = part.split('(')[1].split(')')[0].replace('%', '')
                                detailed_analysis.append(f"{part}（认沽未平仓比认购多{100-float(ratio):.1f}个百分点）")
                            elif "持仓均衡" in part:
                                detailed_analysis.append(f"{part}（认购认沽未平仓基本相等）")
                            else:
                                detailed_analysis.append(part)
                        
                        st.write(f"- **{etf['name']}**: {' | '.join(detailed_analysis)}")
                    st.write("")
            
            
            # 未平仓合约集中度分析
            st.write("**🎯 未平仓合约集中度分析：**")
            for _, row in sse_top3_oi_etfs.iterrows():
                oi_ratio = (row['未平仓合约总数'] / sse_total_open_interest) * 100
                st.write(f"- {row['合约标的名称']}({row['合约标的代码']}): {row['未平仓合约总数']:,} 张 ({oi_ratio:.1f}%)")
        
        # 深交所分析
        if szse_df is not None and not szse_df.empty:
            st.markdown("#### 🏛️ 深圳证券交易所分析")
            
            # 查找深交所的列名
            szse_name_col = None
            szse_volume_col = None
            szse_ratio_col = None
            szse_call_oi_col = None
            szse_put_oi_col = None
            szse_total_oi_col = None
            
            for col in szse_df.columns:
                if '名称' in col:
                    szse_name_col = col
                elif '成交量' in col and '认购' not in col and '认沽' not in col:
                    szse_volume_col = col
                elif '认沽' in col and '认购' in col and '持仓' in col:
                    szse_ratio_col = col
                elif '未平仓' in col and '认购' in col:
                    szse_call_oi_col = col
                elif '未平仓' in col and '认沽' in col:
                    szse_put_oi_col = col
                elif '未平仓' in col and '总数' in col:
                    szse_total_oi_col = col
            
            if szse_name_col and szse_volume_col and szse_ratio_col:
                # 计算深交所核心指标
                szse_total_volume = szse_df[szse_volume_col].sum()
                szse_avg_put_call_ratio = szse_df[szse_ratio_col].mean()
                szse_max_volume_etf = szse_df.loc[szse_df[szse_volume_col].idxmax(), szse_name_col]
                
                # 深交所未平仓分析
                szse_total_open_interest = szse_df[szse_total_oi_col].sum() if szse_total_oi_col else 0
                szse_high_put_oi_etfs = None
                szse_high_call_oi_etfs = None
                szse_top3_oi_etfs = None
                
                if szse_call_oi_col and szse_put_oi_col:
                    szse_high_put_oi_etfs = szse_df[szse_df[szse_put_oi_col] > szse_df[szse_call_oi_col]]
                    szse_high_call_oi_etfs = szse_df[szse_df[szse_call_oi_col] > szse_df[szse_put_oi_col]]
                
                if szse_total_oi_col:
                    szse_top3_oi_etfs = szse_df.nlargest(3, szse_total_oi_col)
                    szse_concentration_ratio = (szse_top3_oi_etfs[szse_total_oi_col].sum() / szse_total_open_interest) * 100 if szse_total_open_interest > 0 else 0
                
                # 深交所情绪分析
                szse_optimistic_etfs = szse_df[szse_df[szse_ratio_col] < 70]
                szse_balanced_etfs = szse_df[(szse_df[szse_ratio_col] >= 70) & (szse_df[szse_ratio_col] <= 100)]
                szse_cautious_etfs = szse_df[(szse_df[szse_ratio_col] > 100) & (szse_df[szse_ratio_col] <= 120)]
                szse_pessimistic_etfs = szse_df[szse_df[szse_ratio_col] > 120]
                
                
                # 综合市场情绪分析 - 合并认沽认购比和未平仓合约分析
                st.write("**📊 综合市场情绪分析：**")
                
                # 为每个ETF生成综合分析（深交所版本）
                def generate_szse_comprehensive_analysis(row):
                    analysis_parts = []
                    
                    # 认沽认购比分析
                    put_call_ratio = row[szse_ratio_col]
                    if put_call_ratio < 70:
                        analysis_parts.append(f"📈 看涨情绪强烈({put_call_ratio:.2f}%)")
                    elif put_call_ratio <= 100:
                        analysis_parts.append(f"⚖️ 多空均衡({put_call_ratio:.2f}%)")
                    elif put_call_ratio <= 120:
                        analysis_parts.append(f"⚠️ 市场谨慎({put_call_ratio:.2f}%)")
                    else:
                        analysis_parts.append(f"📉 看跌情绪较重({put_call_ratio:.2f}%)")
                    
                    # 未平仓合约分析（如果有数据）
                    if szse_call_oi_col and szse_put_oi_col and szse_call_oi_col in row.index and szse_put_oi_col in row.index:
                        put_oi = row[szse_put_oi_col]
                        call_oi = row[szse_call_oi_col]
                        if put_oi > call_oi:
                            oi_ratio = (put_oi / call_oi) * 100
                            analysis_parts.append(f"⚠️ 认沽持仓占优({oi_ratio:.1f}%)")
                        elif call_oi > put_oi:
                            oi_ratio = (call_oi / put_oi) * 100
                            analysis_parts.append(f"📈 认购持仓占优({oi_ratio:.1f}%)")
                        else:
                            analysis_parts.append("⚖️ 持仓均衡")
                    
                    return " | ".join(analysis_parts)
                
                # 为每个ETF生成分析并分组（深交所版本）
                szse_etf_analysis = []
                for _, row in szse_df.iterrows():
                    analysis = generate_szse_comprehensive_analysis(row)
                    szse_etf_analysis.append({
                        'name': row[szse_name_col],
                        'analysis': analysis,
                        'put_call_ratio': row[szse_ratio_col],
                        'volume': row[szse_volume_col]
                    })
                
                # 按市场情绪分组
                def get_szse_sentiment_group(analysis):
                    if "看涨情绪强烈" in analysis:
                        return "看涨情绪强烈"
                    elif "多空均衡" in analysis:
                        return "多空均衡"
                    elif "市场谨慎" in analysis:
                        return "市场谨慎"
                    elif "看跌情绪较重" in analysis:
                        return "看跌情绪较重"
                    else:
                        return "其他"
                
                # 分组并排序
                szse_groups = {}
                for etf in szse_etf_analysis:
                    group = get_szse_sentiment_group(etf['analysis'])
                    if group not in szse_groups:
                        szse_groups[group] = []
                    szse_groups[group].append(etf)
                
                # 按组内成交量排序
                for group in szse_groups:
                    szse_groups[group].sort(key=lambda x: x['volume'], reverse=True)
                
                # 按组顺序显示（看涨->均衡->谨慎->看跌）
                group_order = ["看涨情绪强烈", "多空均衡", "市场谨慎", "看跌情绪较重", "其他"]
                for group in group_order:
                    if group in szse_groups and szse_groups[group]:
                        st.write(f"**{group}ETF：**")
                        for etf in szse_groups[group]:
                            # 解析分析内容，添加详细说明
                            analysis_parts = etf['analysis'].split(' | ')
                            detailed_analysis = []
                            for part in analysis_parts:
                                if "看涨情绪强烈" in part:
                                    ratio = part.split('(')[1].split(')')[0]
                                    detailed_analysis.append(f"{part}（认沽认购比{ratio}，看涨意愿强烈）")
                                elif "多空均衡" in part:
                                    ratio = part.split('(')[1].split(')')[0]
                                    detailed_analysis.append(f"{part}（认沽认购比{ratio}，多空力量平衡）")
                                elif "市场谨慎" in part:
                                    ratio = part.split('(')[1].split(')')[0]
                                    detailed_analysis.append(f"{part}（认沽认购比{ratio}，避险需求较高）")
                                elif "看跌情绪较重" in part:
                                    ratio = part.split('(')[1].split(')')[0]
                                    detailed_analysis.append(f"{part}（认沽认购比{ratio}，看跌情绪浓厚）")
                                elif "认购持仓占优" in part:
                                    ratio = part.split('(')[1].split(')')[0].replace('%', '')
                                    detailed_analysis.append(f"{part}（认购未平仓比认沽多{float(ratio)-100:.1f}个百分点）")
                                elif "认沽持仓占优" in part:
                                    ratio = part.split('(')[1].split(')')[0].replace('%', '')
                                    detailed_analysis.append(f"{part}（认沽未平仓比认购多{100-float(ratio):.1f}个百分点）")
                                elif "持仓均衡" in part:
                                    detailed_analysis.append(f"{part}（认购认沽未平仓基本相等）")
                                else:
                                    detailed_analysis.append(part)
                            
                            st.write(f"- **{etf['name']}**: {' | '.join(detailed_analysis)}")
                        st.write("")
                
                
                # 未平仓合约集中度分析（如果有数据）
                if szse_top3_oi_etfs is not None and not szse_top3_oi_etfs.empty:
                    st.write("**🎯 未平仓合约集中度分析：**")
                    for _, row in szse_top3_oi_etfs.iterrows():
                        oi_ratio = (row[szse_total_oi_col] / szse_total_open_interest) * 100
                        st.write(f"- {row[szse_name_col]}: {row[szse_total_oi_col]:,} 张 ({oi_ratio:.1f}%)")
        
        st.markdown("---")
    
    # 数据对比显示
    if compare_enabled and compare_sse_df is not None and not compare_sse_df.empty:
        st.subheader("📊 数据对比分析")
        
        # 创建对比表格
        def create_comparison_table(current_df, compare_df, current_date, compare_date):
            if compare_df is None or compare_df.empty:
                return None
            
            # 合并数据用于对比
            current_summary = {
                '日期': current_date,
                '总成交量': current_df['总成交量'].sum(),
                '总成交额': current_df['总成交额'].sum(),
                '合约数量': current_df['合约数量'].sum(),
                '平均认沽认购比': current_df['认沽/认购'].mean(),
                '未平仓合约总数': current_df['未平仓合约总数'].sum()
            }
            
            compare_summary = {
                '日期': compare_date,
                '总成交量': compare_df['总成交量'].sum(),
                '总成交额': compare_df['总成交额'].sum(),
                '合约数量': compare_df['合约数量'].sum(),
                '平均认沽认购比': compare_df['认沽/认购'].mean(),
                '未平仓合约总数': compare_df['未平仓合约总数'].sum()
            }
            
            # 计算变化
            changes = {}
            for key in ['总成交量', '总成交额', '合约数量', '平均认沽认购比', '未平仓合约总数']:
                if key in current_summary and key in compare_summary:
                    current_val = current_summary[key]
                    compare_val = compare_summary[key]
                    if compare_val != 0:
                        change_pct = ((current_val - compare_val) / compare_val) * 100
                        changes[key] = change_pct
            else:
                        changes[key] = 0
            
            # 创建对比表格
            comparison_data = []
            for key in ['总成交量', '总成交额', '合约数量', '平均认沽认购比', '未平仓合约总数']:
                if key in current_summary and key in compare_summary:
                    change_pct = changes.get(key, 0)
                    change_color = "green" if change_pct > 0 else "red" if change_pct < 0 else "gray"
                    comparison_data.append({
                        '指标': key,
                        f'{current_date}': f"{current_summary[key]:,}",
                        f'{compare_date}': f"{compare_summary[key]:,}",
                        '变化率': f"{change_pct:+.2f}%",
                        '变化': change_pct
                    })
            
            return pd.DataFrame(comparison_data)
        
        comparison_df = create_comparison_table(sse_df, compare_sse_df, selected_date.strftime('%Y-%m-%d'), compare_date.strftime('%Y-%m-%d'))
        
        if comparison_df is not None:
            # 显示对比表格
            display_dataframe_with_copy(
                comparison_df[['指标', f'{selected_date.strftime("%Y-%m-%d")}', f'{compare_date.strftime("%Y-%m-%d")}', '变化率']],
                title="数据对比分析",
                key_suffix="comparison"
            )
            
            # 创建对比图表
            fig = go.Figure()
            
            # 添加当前日期数据
            fig.add_trace(go.Bar(
                name=f'{selected_date.strftime("%Y-%m-%d")}',
                x=comparison_df['指标'],
                y=comparison_df[f'{selected_date.strftime("%Y-%m-%d")}'],
                marker_color='#1f77b4'
            ))
            
            # 添加对比日期数据
            fig.add_trace(go.Bar(
                name=f'{compare_date.strftime("%Y-%m-%d")}',
                x=comparison_df['指标'],
                y=comparison_df[f'{compare_date.strftime("%Y-%m-%d")}'],
                marker_color='#ff7f0e'
            ))
            
            fig.update_layout(
                title="数据对比图表",
                xaxis_tickangle=-45,
                barmode='group',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True, key="comparison_chart")
    
    # 默认显示全部数据，按总成交量排序
    if sse_df is not None and not sse_df.empty:
        filtered_sse_df = sse_df.copy()
        # 按总成交量降序排序
        filtered_sse_df = filtered_sse_df.sort_values(by='总成交量', ascending=False)
    
        
        # 上交所数据展示
        st.subheader("🏛️ 上海证券交易所数据")
        
        # 使用Streamlit原生表格显示数据
        # 格式化数据用于显示
        display_df = filtered_sse_df.copy()
        
        # 添加文字结论列
        def generate_conclusion(row):
            conclusions = []
            
            # 认沽认购比分析（与上面综合分析保持一致）
            put_call_ratio = row['认沽/认购']
            if put_call_ratio < 70:
                conclusions.append(f"📈 看涨情绪强烈({put_call_ratio:.2f}%)")
            elif put_call_ratio <= 100:
                conclusions.append(f"⚖️ 多空均衡({put_call_ratio:.2f}%)")
            elif put_call_ratio <= 120:
                conclusions.append(f"⚠️ 市场谨慎({put_call_ratio:.2f}%)")
            else:
                conclusions.append(f"📉 看跌情绪较重({put_call_ratio:.2f}%)")
            
            # 未平仓合约分析（与上面综合分析保持一致）
            put_oi = row['未平仓认沽合约数']
            call_oi = row['未平仓认购合约数']
            if put_oi > call_oi:
                oi_ratio = (put_oi / call_oi) * 100
                conclusions.append(f"⚠️ 认沽持仓占优({oi_ratio:.1f}%)")
            elif call_oi > put_oi:
                oi_ratio = (call_oi / put_oi) * 100
                conclusions.append(f"📈 认购持仓占优({oi_ratio:.1f}%)")
            else:
                conclusions.append("⚖️ 持仓均衡")
            
            return " | ".join(conclusions)
        
        display_df['市场分析'] = display_df.apply(generate_conclusion, axis=1)
        
        # 格式化数字列
        numeric_columns = ['合约数量', '总成交额', '总成交量', '认购成交量', '认沽成交量', 
                          '未平仓合约总数', '未平仓认购合约数', '未平仓认沽合约数']
        
        for col in numeric_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{int(x):,}")
        
        # 格式化认沽/认购比例
        if '认沽/认购' in display_df.columns:
            display_df['认沽/认购'] = display_df['认沽/认购'].apply(lambda x: f"{x:.2f}")
        
        # 重命名列以更好地显示
        display_df = display_df.rename(columns={
            '合约标的代码': '代码',
            '合约标的名称': '名称',
            '合约数量': '合约数',
            '总成交额': '成交额(万元)',
            '总成交量': '成交量(张)',
            '认购成交量': '认购量(张)',
            '认沽成交量': '认沽量(张)',
            '认沽/认购': '认沽/认购比',
            '未平仓合约总数': '未平仓总数',
            '未平仓认购合约数': '未平仓认购',
            '未平仓认沽合约数': '未平仓认沽'
        })
        
        # 使用工具函数显示带复制按钮的表格
        display_dataframe_with_copy(
            display_df,
            title="上海证券交易所数据",
            key_suffix="sse_main"
        )
        
        # 使用共用函数创建认沽/认购比柱状图
        create_put_call_ratio_chart(
            sse_df, 
            '合约标的名称', 
            '认沽/认购', 
            '上交所',
            'main'
        )
        
        # 使用共用函数创建持仓量多空分布对比条形图
        create_open_interest_stacked_chart(
            sse_df,
            '合约标的名称',
            '未平仓认购合约数',
            '未平仓认沽合约数',
            '上交所',
            'main'
        )
        
        # 添加成交额与成交量双轴柱状图
        create_volume_turnover_dual_axis_chart(
            sse_df,
            '合约标的名称',
            '总成交量',
            '总成交额',
            '上交所',
            'main'
        )
    
    # 深交所数据展示
    if szse_df is not None and not szse_df.empty:
        st.subheader("🏛️ 深圳证券交易所数据")
        
        # 使用Streamlit原生表格显示深交所数据
        szse_display_df = szse_df.copy()
        
        # 添加文字结论列（深交所版本）
        def generate_szse_conclusion(row):
            conclusions = []
            
            # 成交量分析 - 查找包含"成交量"但不包含"认购"和"认沽"的列
            volume_col = None
            for col in row.index:
                if '成交量' in col and '认购' not in col and '认沽' not in col:
                    volume_col = col
                    break
            
            if volume_col is not None:
                volume = row[volume_col]
                if volume > 1000000:
                    conclusions.append("🔥 交易非常活跃")
                elif volume > 500000:
                    conclusions.append("📈 交易活跃")
                elif volume > 100000:
                    conclusions.append("📊 交易一般")
                else:
                    conclusions.append("📉 交易清淡")
            
            # 认沽认购比分析 - 查找包含"认沽"、"认购"和"持仓"的列
            put_call_ratio_col = None
            for col in row.index:
                if '认沽' in col and '认购' in col and '持仓' in col:
                    put_call_ratio_col = col
                    break
            
            if put_call_ratio_col is not None:
                put_call_ratio = row[put_call_ratio_col]
                if put_call_ratio < 70:
                    conclusions.append(f"📈 看涨情绪强烈({put_call_ratio:.2f}%)")
                elif put_call_ratio <= 100:
                    conclusions.append(f"⚖️ 多空均衡({put_call_ratio:.2f}%)")
                elif put_call_ratio <= 120:
                    conclusions.append(f"⚠️ 市场谨慎({put_call_ratio:.2f}%)")
                else:
                    conclusions.append(f"📉 看跌情绪较重({put_call_ratio:.2f}%)")
            
            # 未平仓合约分析 - 查找包含"未平仓"、"认购"和"认沽"的列
            call_oi_col = None
            put_oi_col = None
            for col in row.index:
                if '未平仓' in col and '认购' in col:
                    call_oi_col = col
                elif '未平仓' in col and '认沽' in col:
                    put_oi_col = col
            
            if call_oi_col is not None and put_oi_col is not None:
                put_oi = row[put_oi_col]
                call_oi = row[call_oi_col]
                if put_oi > call_oi:
                    oi_ratio = (put_oi / call_oi) * 100
                    conclusions.append(f"⚠️ 认沽持仓占优({oi_ratio:.1f}%)")
                elif call_oi > put_oi:
                    oi_ratio = (call_oi / put_oi) * 100
                    conclusions.append(f"📈 认购持仓占优({oi_ratio:.1f}%)")
                else:
                    conclusions.append("⚖️ 持仓均衡")
            
            return " | ".join(conclusions) if conclusions else "数据不足"
        
        szse_display_df['市场分析'] = szse_display_df.apply(generate_szse_conclusion, axis=1)
        
        # 先检查深交所数据的实际列名
        
        # 根据实际列名进行格式化
        # 检查并格式化数字列
        numeric_columns_to_format = []
        for col in szse_display_df.columns:
            if szse_display_df[col].dtype in ['int64', 'float64']:
                numeric_columns_to_format.append(col)
        
        for col in numeric_columns_to_format:
            szse_display_df[col] = szse_display_df[col].apply(lambda x: f"{int(x):,}")
        
        # 重命名列以更好地显示（根据实际列名）
        column_mapping = {}
        for col in szse_display_df.columns:
            if '代码' in col:
                column_mapping[col] = '代码'
            elif '名称' in col:
                column_mapping[col] = '名称'
            elif '成交量' in col and '认购' not in col and '认沽' not in col:
                column_mapping[col] = '成交量(张)'
            elif '认购' in col and '成交量' in col:
                column_mapping[col] = '认购量(张)'
            elif '认沽' in col and '成交量' in col:
                column_mapping[col] = '认沽量(张)'
            elif '认沽' in col and '认购' in col and '持仓' in col:
                column_mapping[col] = '认沽/认购比'
            elif '未平仓' in col and '总数' in col:
                column_mapping[col] = '未平仓总数'
            elif '未平仓' in col and '认购' in col:
                column_mapping[col] = '未平仓认购'
            elif '未平仓' in col and '认沽' in col:
                column_mapping[col] = '未平仓认沽'
        
        szse_display_df = szse_display_df.rename(columns=column_mapping)
        
        # 使用工具函数显示带复制按钮的表格
        display_dataframe_with_copy(
            szse_display_df,
            title="深圳证券交易所数据",
            key_suffix="szse_main"
        )
        
        # 查找深交所的列名
        szse_ratio_col = None
        szse_name_col = None
        szse_call_oi_col = None
        szse_put_oi_col = None
        for col in szse_df.columns:
            if '认沽' in col and '认购' in col and '持仓' in col:
                szse_ratio_col = col
            elif '名称' in col:
                szse_name_col = col
            elif '未平仓' in col and '认购' in col:
                szse_call_oi_col = col
            elif '未平仓' in col and '认沽' in col:
                szse_put_oi_col = col
        
        # 使用共用函数创建认沽/认购比柱状图
        create_put_call_ratio_chart(
            szse_df, 
            szse_name_col, 
            szse_ratio_col, 
            '深交所',
            'main'
        )
        
        # 使用共用函数创建持仓量多空分布对比条形图
        create_open_interest_stacked_chart(
            szse_df,
            szse_name_col,
            szse_call_oi_col,
            szse_put_oi_col,
            '深交所',
            'main'
        )
        
        # 查找深交所的成交额列
        szse_turnover_col = None
        for col in szse_df.columns:
            if '成交额' in col:
                szse_turnover_col = col
                break
        
        # 添加成交额与成交量双轴柱状图（如果有成交额数据）
        if szse_turnover_col:
            create_volume_turnover_dual_axis_chart(
                szse_df,
                szse_name_col,
                szse_volume_col,
                szse_turnover_col,
                '深交所',
                'main'
            )
        
        # 深交所数据下载
        szse_csv = szse_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载深交所数据CSV文件",
            data=szse_csv,
            file_name=f"szse_option_daily_stats_{date_str}.csv",
            mime="text/csv"
        )
    
    else:
        st.warning("⚠️ 无法加载深交所数据，请检查日期设置或网络连接")
        
        # 图表分析
        st.subheader("📊 图表分析")
        
        # 上交所图表分析
        st.markdown("#### 🏛️ 上海证券交易所图表分析")
        
        # 成交量分析
        st.markdown("##### 📈 成交量分析")
        col1, col2 = st.columns(2)
        
        with col1:
            # 成交量对比
            fig1 = create_volume_chart(sse_df, None, "成交量对比")
            if fig1:
                st.plotly_chart(fig1, use_container_width=True, key="sse_volume_1")
        
        with col2:
            # 认沽认购比
            fig2 = create_volume_chart(sse_df, None, "认沽认购比")
            if fig2:
                st.plotly_chart(fig2, use_container_width=True, key="sse_volume_2")
        
        # 未平仓合约
        fig3 = create_volume_chart(sse_df, None, "未平仓合约")
        if fig3:
            st.plotly_chart(fig3, use_container_width=True, key="sse_volume_3")
        
        # 成交额分析
        st.markdown("##### 💰 成交额分析")
        col3, col4 = st.columns(2)
        
        with col3:
            # 成交额对比
            fig4 = create_turnover_chart(sse_df, "成交额对比")
            if fig4:
                st.plotly_chart(fig4, use_container_width=True, key="sse_turnover_1")
        
        with col4:
            # 成交额分布
            fig5 = create_turnover_chart(sse_df, "成交额分布")
            if fig5:
                st.plotly_chart(fig5, use_container_width=True, key="sse_turnover_2")
        
        # 合约数量
        fig6 = create_turnover_chart(sse_df, "合约数量")
        if fig6:
            st.plotly_chart(fig6, use_container_width=True, key="sse_turnover_3")
        
        # 认沽认购分析
        st.markdown("##### ⚖️ 认沽认购分析")
        col5, col6 = st.columns(2)
        
        with col5:
            # 认沽认购分析
            fig7 = create_put_call_chart(sse_df, "认沽认购分析")
            if fig7:
                st.plotly_chart(fig7, use_container_width=True, key="sse_put_call_1")
        
        with col6:
            # 认沽认购散点图
            fig8 = create_put_call_chart(sse_df, "认沽认购散点图")
            if fig8:
                st.plotly_chart(fig8, use_container_width=True, key="sse_put_call_2")
        
        # 深交所图表分析
        if szse_df is not None and not szse_df.empty:
            st.markdown("#### 🏛️ 深圳证券交易所图表分析")
            
            # 成交量分析
            st.markdown("##### 📈 成交量分析")
            col7, col8 = st.columns(2)
            
            with col7:
                # 深交所成交量对比
                fig9 = create_szse_volume_chart(szse_df, "成交量对比")
                if fig9:
                    st.plotly_chart(fig9, use_container_width=True, key="szse_volume_1")
            
            with col8:
                # 深交所认沽认购比
                fig10 = create_szse_volume_chart(szse_df, "认沽认购比")
                if fig10:
                    st.plotly_chart(fig10, use_container_width=True, key="szse_volume_2")
            
            # 深交所未平仓合约
            fig11 = create_szse_volume_chart(szse_df, "未平仓合约")
            if fig11:
                st.plotly_chart(fig11, use_container_width=True, key="szse_volume_3")
            
            # 深交所认沽认购分析
            st.markdown("##### ⚖️ 认沽认购分析")
            col9, col10 = st.columns(2)
            
            with col9:
                # 深交所认沽认购分析
                fig12 = create_szse_put_call_chart(szse_df, "认沽认购分析")
                if fig12:
                    st.plotly_chart(fig12, use_container_width=True, key="szse_put_call_1")
            
            with col10:
                # 深交所认沽认购散点图
                fig13 = create_szse_put_call_chart(szse_df, "认沽认购散点图")
                if fig13:
                    st.plotly_chart(fig13, use_container_width=True, key="szse_put_call_2")
        
        # 详细分析
        
        # 数据下载
        st.subheader("💾 数据下载")
        csv = sse_df.to_csv(index=False, encoding='utf-8-sig')
        download_filename = f"sse_option_daily_stats_{date_str}.csv"
        
        st.download_button(
            label="下载上交所数据CSV文件",
            data=csv,
            file_name=download_filename,
            mime="text/csv"
        )

        # 使用Streamlit原生表格显示深交所数据
        szse_display_df = szse_df.copy()
        
        # 添加文字结论列（深交所版本）
        def generate_szse_conclusion(row):
            conclusions = []
            
            # 成交量分析 - 查找包含"成交量"但不包含"认购"和"认沽"的列
            volume_col = None
            for col in row.index:
                if '成交量' in col and '认购' not in col and '认沽' not in col:
                    volume_col = col
                    break
            
            if volume_col is not None:
                volume = row[volume_col]
                if volume > 1000000:
                    conclusions.append("🔥 交易非常活跃")
                elif volume > 500000:
                    conclusions.append("📈 交易活跃")
                elif volume > 100000:
                    conclusions.append("📊 交易一般")
                else:
                    conclusions.append("📉 交易清淡")
            
            # 认沽认购比分析 - 查找包含"认沽"、"认购"和"持仓"的列
            put_call_ratio_col = None
            for col in row.index:
                if '认沽' in col and '认购' in col and '持仓' in col:
                    put_call_ratio_col = col
                    break
            
            if put_call_ratio_col is not None:
                put_call_ratio = row[put_call_ratio_col]
                if put_call_ratio < 70:
                    conclusions.append(f"📈 看涨情绪强烈({put_call_ratio:.2f}%)")
                elif put_call_ratio <= 100:
                    conclusions.append(f"⚖️ 多空均衡({put_call_ratio:.2f}%)")
                elif put_call_ratio <= 120:
                    conclusions.append(f"⚠️ 市场谨慎({put_call_ratio:.2f}%)")
                else:
                    conclusions.append(f"📉 看跌情绪较重({put_call_ratio:.2f}%)")
            
            # 未平仓合约分析 - 查找包含"未平仓"、"认购"和"认沽"的列
            call_oi_col = None
            put_oi_col = None
            for col in row.index:
                if '未平仓' in col and '认购' in col:
                    call_oi_col = col
                elif '未平仓' in col and '认沽' in col:
                    put_oi_col = col
            
            if call_oi_col is not None and put_oi_col is not None:
                put_oi = row[put_oi_col]
                call_oi = row[call_oi_col]
                if put_oi > call_oi:
                    oi_ratio = (put_oi / call_oi) * 100
                    conclusions.append(f"⚠️ 认沽持仓占优({oi_ratio:.1f}%)")
                elif call_oi > put_oi:
                    oi_ratio = (call_oi / put_oi) * 100
                    conclusions.append(f"📈 认购持仓占优({oi_ratio:.1f}%)")
                else:
                    conclusions.append("⚖️ 持仓均衡")
            
            return " | ".join(conclusions) if conclusions else "数据不足"
        
        szse_display_df['市场分析'] = szse_display_df.apply(generate_szse_conclusion, axis=1)
        
        # 先检查深交所数据的实际列名
        
        # 根据实际列名进行格式化
        # 检查并格式化数字列
        numeric_columns_to_format = []
        for col in szse_display_df.columns:
            if szse_display_df[col].dtype in ['int64', 'float64']:
                numeric_columns_to_format.append(col)
        
        for col in numeric_columns_to_format:
            szse_display_df[col] = szse_display_df[col].apply(lambda x: f"{int(x):,}")
        
        # 重命名列以更好地显示（根据实际列名）
        column_mapping = {}
        for col in szse_display_df.columns:
            if '代码' in col:
                column_mapping[col] = '代码'
            elif '名称' in col:
                column_mapping[col] = '名称'
            elif '成交量' in col and '认购' not in col and '认沽' not in col:
                column_mapping[col] = '成交量(张)'
            elif '认购' in col and '成交量' in col:
                column_mapping[col] = '认购量(张)'
            elif '认沽' in col and '成交量' in col:
                column_mapping[col] = '认沽量(张)'
            elif '认沽' in col and '认购' in col and '持仓' in col:
                column_mapping[col] = '认沽/认购比'
            elif '未平仓' in col and '总数' in col:
                column_mapping[col] = '未平仓总数'
            elif '未平仓' in col and '认购' in col:
                column_mapping[col] = '未平仓认购'
            elif '未平仓' in col and '认沽' in col:
                column_mapping[col] = '未平仓认沽'
        
        szse_display_df = szse_display_df.rename(columns=column_mapping)
        
        # 使用工具函数显示带复制按钮的表格
        display_dataframe_with_copy(
            szse_display_df,
            title="深圳证券交易所数据",
            key_suffix="szse_main"
        )
        
        
        # 深交所数据下载
        szse_csv = szse_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载深交所数据CSV文件",
            data=szse_csv,
            file_name=f"szse_option_daily_stats_{date_str}.csv",
            mime="text/csv"
        )
    

    
        
    
    # 页脚信息
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>📊 期权每日统计系统 | 数据来源：akshare | 更新时间：{}</p>
        <p>💡 提示：数据可能存在延迟，请以交易所官方数据为准</p>
        <p>🔧 功能：数据筛选、对比分析、市场洞察、图表可视化</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()