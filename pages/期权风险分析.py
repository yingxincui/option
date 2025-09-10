import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
import os

# 确保可导入项目内工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_option_greeks_by_underlying, get_available_etf_names, get_options_by_etf, merge_option_data


st.set_page_config(
    page_title="期权合约分析",
    page_icon="📊",
    layout="wide",
)


def analyze_option_characteristics(df):
    """
    分析期权合约特征
    
    参数：
        df: 期权数据DataFrame
    
    返回：
        pandas.DataFrame: 添加了特征分析的DataFrame
    """
    if df.empty:
        return df
    
    df_analysis = df.copy()
    
    # 确保数值列为数值类型
    numeric_columns = ['Delta', '实际杠杆比率', 'Vega', 'Theta', '最新价']
    for col in numeric_columns:
        if col in df_analysis.columns:
            df_analysis[col] = pd.to_numeric(df_analysis[col], errors='coerce')
    
    # 初始化特征列
    df_analysis['合约特征'] = ''
    
    # 分析每个合约的特征
    for idx, row in df_analysis.iterrows():
        characteristics = []
        
        # Delta分析
        delta = row.get('Delta', 0)
        if pd.notna(delta):
            if abs(delta) > 0.7:
                characteristics.append("📈高Delta")
            elif abs(delta) > 0.5:
                characteristics.append("📊中Delta")
            else:
                characteristics.append("📉低Delta")
        
        # 杠杆分析
        leverage = row.get('实际杠杆比率', 0)
        if pd.notna(leverage):
            if leverage > 15:
                characteristics.append("⚡超高杠杆")
            elif leverage > 10:
                characteristics.append("🔥高杠杆")
            elif leverage > 5:
                characteristics.append("⚖️中杠杆")
            else:
                characteristics.append("🛡️低杠杆")
        
        # Vega分析
        vega = row.get('Vega', 0)
        if pd.notna(vega):
            if vega > df_analysis['Vega'].quantile(0.8):
                characteristics.append("🌊高Vega")
            elif vega > df_analysis['Vega'].quantile(0.5):
                characteristics.append("🌊中Vega")
            else:
                characteristics.append("🌊低Vega")
        
        # Theta分析（时间衰减）
        theta = row.get('Theta', 0)
        if pd.notna(theta):
            if abs(theta) > 0.5:
                characteristics.append("⏰高时间衰减")
            elif abs(theta) > 0.2:
                characteristics.append("⏱️中时间衰减")
            else:
                characteristics.append("⏳低时间衰减")
        
        # 期权类型
        option_name = row.get('期权名称', '')
        if '购' in option_name:
            characteristics.append("📈看涨")
        elif '沽' in option_name:
            characteristics.append("📉看跌")
        
        # 风险等级评估
        risk_level = "🟢低风险"
        if (abs(delta) > 0.7 and leverage > 10) or leverage > 15:
            risk_level = "🔴高风险"
        elif (abs(delta) > 0.5 and leverage > 5) or leverage > 10:
            risk_level = "🟡中风险"
        
        characteristics.append(f"({risk_level})")
        
        # 组合特征
        df_analysis.at[idx, '合约特征'] = " | ".join(characteristics)
    
    return df_analysis


def create_volatility_smile_chart(df, etf_name):
    """
    创建期权微笑曲线图（隐含波动率 vs 行权价）
    
    参数：
        df: 期权数据DataFrame
        etf_name: ETF名称
    
    返回：
        plotly图表对象
    """
    if df.empty or '行权价' not in df.columns or '隐含波动率' not in df.columns:
        return None
    
    # 数据清理
    df_clean = df.copy()
    df_clean['行权价'] = pd.to_numeric(df_clean['行权价'], errors='coerce')
    df_clean['隐含波动率'] = pd.to_numeric(df_clean['隐含波动率'], errors='coerce')
    
    # 移除无效数据
    df_clean = df_clean.dropna(subset=['行权价', '隐含波动率'])
    
    if df_clean.empty:
        return None
    
    # 获取标的价格（用于计算相对行权价）
    underlying_price = None
    if '标的最新价' in df_clean.columns:
        underlying_price = df_clean['标的最新价'].iloc[0]
    elif '标的最新价_premium' in df_clean.columns:
        underlying_price = df_clean['标的最新价_premium'].iloc[0]
    
    # 按到期月份分组
    df_clean['到期月份'] = df_clean['期权名称'].str.extract(r'(\d+)月')
    months = sorted(df_clean['到期月份'].dropna().unique())
    
    if not months:
        return None
    
    # 创建子图
    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=len(months), cols=1,
        subplot_titles=[f"{month}月到期期权微笑曲线" for month in months],
        vertical_spacing=0.1
    )
    
    colors = px.colors.qualitative.Set1
    
    for i, month in enumerate(months):
        month_data = df_clean[df_clean['到期月份'] == month].copy()
        if month_data.empty:
            continue
        
        # 分离看涨和看跌期权
        call_data = month_data[month_data['期权名称'].str.contains('购', na=False)]
        put_data = month_data[month_data['期权名称'].str.contains('沽', na=False)]
        
        # 看涨期权 - 按行权价排序
        if not call_data.empty:
            call_sorted = call_data.sort_values('行权价')
            fig.add_trace(
                go.Scatter(
                    x=call_sorted['行权价'],
                    y=call_sorted['隐含波动率'],
                    mode='markers+lines',
                    name=f'{month}月看涨',
                    marker=dict(
                        color=colors[i % len(colors)],
                        symbol='circle',
                        size=8
                    ),
                    line=dict(width=2),
                    hovertemplate='<b>%{text}</b><br>' +
                                 '行权价: %{x}<br>' +
                                 '隐含波动率: %{y:.2f}%<br>' +
                                 '<extra></extra>',
                    text=call_sorted['期权名称']
                ),
                row=i+1, col=1
            )
        
        # 看跌期权 - 按行权价排序
        if not put_data.empty:
            put_sorted = put_data.sort_values('行权价')
            fig.add_trace(
                go.Scatter(
                    x=put_sorted['行权价'],
                    y=put_sorted['隐含波动率'],
                    mode='markers+lines',
                    name=f'{month}月看跌',
                    marker=dict(
                        color=colors[i % len(colors)],
                        symbol='diamond',
                        size=8
                    ),
                    line=dict(width=2, dash='dash'),
                    hovertemplate='<b>%{text}</b><br>' +
                                 '行权价: %{x}<br>' +
                                 '隐含波动率: %{y:.2f}%<br>' +
                                 '<extra></extra>',
                    text=put_sorted['期权名称']
                ),
                row=i+1, col=1
            )
        
        # 添加标的价格参考线
        if underlying_price and pd.notna(underlying_price):
            fig.add_vline(
                x=underlying_price,
                line_dash="dot",
                line_color="red",
                annotation_text=f"标的价格: {underlying_price:.2f}",
                row=i+1, col=1
            )
    
    # 更新布局
    fig.update_layout(
        title=f"{etf_name} 期权微笑曲线图",
        height=300 * len(months),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # 更新x轴和y轴标签
    for i in range(len(months)):
        fig.update_xaxes(title_text="行权价", row=i+1, col=1)
        fig.update_yaxes(title_text="隐含波动率 (%)", row=i+1, col=1)
    
    return fig


def create_leverage_risk_chart(df, etf_name):
    """
    创建杠杆与风险分析气泡图
    
    参数：
        df: 期权数据DataFrame
        etf_name: ETF名称
    
    返回：
        plotly图表对象
    """
    if df.empty or '期权名称' not in df.columns:
        return None
    
    # 数据清理和准备
    df_copy = df.copy()
    
    # 提取到期月份
    df_copy['到期月份'] = df_copy['期权名称'].str.extract(r'(\d+)月')
    
    # 确保数值列为数值类型
    numeric_columns = ['Delta', '实际杠杆比率', 'Vega', 'Theta', '最新价']
    for col in numeric_columns:
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
    
    # 清理数据
    df_copy = df_copy.dropna(subset=['Delta', '实际杠杆比率'])
    
    if df_copy.empty:
        return None
    
    # 创建气泡图
    fig = go.Figure()
    
    # 按到期月份分组
    months = sorted(df_copy['到期月份'].dropna().unique())
    colors = px.colors.qualitative.Set1
    
    for i, month in enumerate(months):
        month_data = df_copy[df_copy['到期月份'] == month].copy()
        
        if month_data.empty:
            continue
        
        # 分离看涨和看跌期权
        call_data = month_data[month_data['期权名称'].str.contains('购', na=False)]
        put_data = month_data[month_data['期权名称'].str.contains('沽', na=False)]
        
        # 看涨期权
        if not call_data.empty:
            # 将 Vega 映射为像素尺寸
            vega_series = call_data['Vega'].fillna(0).clip(lower=0)
            vmin, vmax = float(vega_series.min()), float(vega_series.max())
            min_px, max_px = 6.0, 40.0
            if vmax - vmin > 1e-9:
                sizes = (vega_series - vmin) / (vmax - vmin) * (max_px - min_px) + min_px
            else:
                sizes = pd.Series([min_px] * len(vega_series), index=vega_series.index)
            customdata = call_data['Vega'].fillna(0).astype(float)
            fig.add_trace(go.Scatter(
                x=call_data['Delta'],
                y=call_data['实际杠杆比率'],
                mode='markers',
                name=f'{month}月看涨',
                marker=dict(
                    size=sizes,
                    sizemode='diameter',
                    sizemin=5,
                    color=colors[i % len(colors)],
                    symbol='circle',
                    line=dict(width=1, color='white'),
                    opacity=0.7
                ),
                text=call_data['期权名称'],
                customdata=customdata,
                hovertemplate='<b>%{text}</b><br>' +
                             'Delta: %{x:.4f}<br>' +
                             '实际杠杆: %{y:.2f}<br>' +
                             'Vega: %{customdata:.4f}<br>' +
                             '<extra></extra>'
            ))
        
        # 看跌期权
        if not put_data.empty:
            vega_series = put_data['Vega'].fillna(0).clip(lower=0)
            vmin, vmax = float(vega_series.min()), float(vega_series.max())
            min_px, max_px = 6.0, 40.0
            if vmax - vmin > 1e-9:
                sizes = (vega_series - vmin) / (vmax - vmin) * (max_px - min_px) + min_px
            else:
                sizes = pd.Series([min_px] * len(vega_series), index=vega_series.index)
            customdata = put_data['Vega'].fillna(0).astype(float)
            fig.add_trace(go.Scatter(
                x=put_data['Delta'],
                y=put_data['实际杠杆比率'],
                mode='markers',
                name=f'{month}月看跌',
                marker=dict(
                    size=sizes,
                    sizemode='diameter',
                    sizemin=5,
                    color=colors[i % len(colors)],
                    symbol='diamond',
                    line=dict(width=1, color='white'),
                    opacity=0.7
                ),
                text=put_data['期权名称'],
                customdata=customdata,
                hovertemplate='<b>%{text}</b><br>' +
                             'Delta: %{x:.4f}<br>' +
                             '实际杠杆: %{y:.2f}<br>' +
                             'Vega: %{customdata:.4f}<br>' +
                             '<extra></extra>'
            ))
    
    # 更新布局
    fig.update_layout(
        title=f"{etf_name} 杠杆与风险分析气泡图",
        xaxis_title="Delta (方向风险)",
        yaxis_title="实际杠杆比率",
        width=800,
        height=600,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    
    # 添加风险区域标注
    fig.add_annotation(
        x=0.8, y=0.9,
        xref="paper", yref="paper",
        text="高风险区域<br>(高Delta+高杠杆)",
        showarrow=True,
        arrowhead=2,
        arrowcolor="red",
        bgcolor="rgba(255,0,0,0.1)",
        bordercolor="red"
    )
    
    fig.add_annotation(
        x=0.2, y=0.1,
        xref="paper", yref="paper",
        text="低风险区域<br>(低Delta+低杠杆)",
        showarrow=True,
        arrowhead=2,
        arrowcolor="green",
        bgcolor="rgba(0,255,0,0.1)",
        bordercolor="green"
    )
    
    return fig


def main():
    st.markdown('<h1 style="text-align:center;">📊 期权合约分析</h1>', unsafe_allow_html=True)

    # 侧边栏：筛选条件
    st.sidebar.header("筛选条件")
    
    # 获取可用的ETF名称
    try:
        etf_names = get_available_etf_names()
    except Exception:
        etf_names = []
    
    if not etf_names:
        st.error("无法获取ETF列表")
        return
    
    # ETF选择器
    selected_etf = st.sidebar.selectbox("选择ETF", etf_names, index=0)
    
    # 期权类型筛选
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 期权类型筛选")
    
    option_type = st.sidebar.radio(
        "选择期权类型",
        ["📈 看涨期权", "📉 看跌期权", "🔄 全部"],
        index=0,  # 默认选择看涨期权
        help="选择要分析的期权类型"
    )
    
    # 月份筛选
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 到期月份筛选")
    
    # 先获取数据以提取月份选项
    try:
        with st.spinner("正在获取数据..."):
            df_all = merge_option_data(selected_etf)
    except Exception as e:
        st.error(f"数据获取失败: {e}")
        return

    if df_all is None or (isinstance(df_all, pd.DataFrame) and df_all.empty):
        st.warning(f"未获取到 {selected_etf} 的期权数据")
        return
    
    # 根据期权类型筛选
    if option_type == "📈 看涨期权":
        df_all = df_all[df_all['期权名称'].str.contains('购', na=False)]
    elif option_type == "📉 看跌期权":
        df_all = df_all[df_all['期权名称'].str.contains('沽', na=False)]
    # 如果是"全部"，则不进行筛选
    
    # 提取月份选项
    df_all['到期月份'] = df_all['期权名称'].str.extract(r'(\d+)月')
    available_months = sorted(df_all['到期月份'].dropna().unique())
    
    if available_months:
        # 获取当前月份
        from datetime import datetime
        current_month = str(datetime.now().month)
        
        # 如果当前月份在可用月份中，则默认选择当前月份
        if current_month in available_months:
            default_months = [current_month]
        else:
            # 如果当前月份不在可用月份中，选择第一个可用月份
            default_months = [available_months[0]]
        
        # 月份多选框
        selected_months = st.sidebar.multiselect(
            "选择到期月份",
            available_months,
            default=default_months,  # 默认选择当月
            help="可以选择一个或多个月份进行筛选，默认选择当月"
        )
        
        # 根据选择的月份筛选数据
        if selected_months:
            df = df_all[df_all['到期月份'].isin(selected_months)].reset_index(drop=True)
        else:
            df = df_all
            st.sidebar.warning("请至少选择一个月份")
    else:
        df = df_all
        st.sidebar.warning("无法提取到期月份信息")

    # 刷新按钮
    if st.sidebar.button("🔄 刷新数据", type="primary"):
        st.rerun()

    # 数据展示
    option_type_display = option_type.split(' ')[1] if ' ' in option_type else option_type
    st.subheader(f"📋 {selected_etf} {option_type_display} 期权合约数据（希腊字母等）")

    # 期权微笑曲线图
    st.subheader("😊 期权微笑曲线图")
    try:
        smile_chart = create_volatility_smile_chart(df, selected_etf)
        if smile_chart:
            st.plotly_chart(smile_chart, use_container_width=True)
            
            # 添加图表说明
            st.markdown("""
            **😊 微笑曲线说明：**
            - **X轴 (行权价)**：期权的执行价格
            - **Y轴 (隐含波动率)**：市场对未来波动率的预期
            - **实线**：看涨期权（购）
            - **虚线**：看跌期权（沽）
            - **红色竖线**：标的价格参考线
            
            **🎯 分析要点：**
            - **微笑形状**：OTM期权隐含波动率通常高于ATM期权
            - **左偏/右偏**：反映市场对下跌/上涨的恐惧程度
            - **曲线陡峭度**：反映市场对极端价格变动的预期
            - **看涨看跌差异**：反映市场情绪和供需关系
            """)
        else:
            st.warning("无法生成微笑曲线图，请检查数据格式")
    except Exception as e:
        st.error(f"生成微笑曲线图失败: {e}")
    
    st.markdown("---")
    
    # 杠杆与风险分析气泡图
    st.subheader("📊 杠杆与风险分析气泡图")
    try:
        risk_chart = create_leverage_risk_chart(df, selected_etf)
        if risk_chart:
            st.plotly_chart(risk_chart, use_container_width=True)
            
            
            # 添加图表说明
            st.markdown("""
            **📈 图表说明：**
            - **X轴 (Delta)**：方向风险，表示期权价格对标的资产价格变化的敏感度
            - **Y轴 (实际杠杆比率)**：杠杆倍数，表示投资期权的杠杆效应
            - **气泡大小 (Vega)**：波动率风险，气泡越大表示对波动率变化越敏感
            - **气泡颜色**：区分不同到期月份
            - **形状**：圆形=看涨期权，菱形=看跌期权
            
            **🎯 分析要点：**
            - **右上角**：高Delta+高杠杆，方向敏感度高，潜在收益和风险最大
            - **大气泡**：高Vega，适合波动率交易
            - **左下角**：低风险区域，适合保守策略
            """)
        else:
            st.warning("无法生成杠杆风险分析图，请检查数据格式")
    except Exception as e:
        st.error(f"生成杠杆风险分析图失败: {e}")
    
    st.markdown("---")

    # 添加合约特征分析
    display_df = analyze_option_characteristics(df)
    
    # 尝试对常见数值列做基本格式化（若存在）
    numeric_cols = [
        "最新价", "涨跌幅", "行权价", "Delta", "Gamma", "Theta", "Vega", "隐含波动率", "剩余天数"
    ]
    for col in numeric_cols:
        if col in display_df.columns:
            with pd.option_context('mode.use_inf_as_na', True):
                display_df[col] = pd.to_numeric(display_df[col], errors='coerce')

    # 排序优先展示重要列
    preferred_order = [
        "期权代码", "期权名称", "标的名称", "期权类型", "到期日", "行权价",
        "最新价", "涨跌幅", "隐含波动率", "时间价值", "内在价值", "理论价格", 
        "标的最新价", "标的近一年波动率", "折溢价率", "盈亏平衡价", "标的涨跌幅",
        "Delta", "Gamma", "Theta", "Vega", "Rho", "剩余天数"
    ]
    ordered_cols = [c for c in preferred_order if c in display_df.columns]
    other_cols = [c for c in display_df.columns if c not in ordered_cols]
    display_df = display_df[ordered_cols + other_cols] if ordered_cols else display_df
    
    # 将合约特征列移到期权名称后面
    if '合约特征' in display_df.columns:
        cols = list(display_df.columns)
        if '期权合约简称' in cols and '合约特征' in cols:
            name_idx = cols.index('期权合约简称')
            feature_idx = cols.index('合约特征')
            # 移除合约特征列
            cols.pop(feature_idx)
            # 在期权合约简称后面插入合约特征列
            cols.insert(name_idx + 1, '合约特征')
            display_df = display_df[cols]

    # 基本数值格式
    fmt_cols_2 = ["最新价", "行权价", "时间价值", "内在价值", "理论价格", "标的最新价", "盈亏平衡价"]
    fmt_cols_4 = ["Delta", "Gamma", "Theta", "Vega", "Rho"]
    
    for c in fmt_cols_2:
        if c in display_df.columns:
            display_df[c] = display_df[c].map(lambda x: f"{x:.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)
    
    for c in fmt_cols_4:
        if c in display_df.columns:
            display_df[c] = display_df[c].map(lambda x: f"{x:.4f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)
    
    # 处理百分比格式的列
    if "涨跌幅" in display_df.columns:
        display_df["涨跌幅"] = display_df["涨跌幅"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) and isinstance(x, (int, float)) else x)
    
    if "隐含波动率" in display_df.columns:
        display_df["隐含波动率"] = display_df["隐含波动率"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) and isinstance(x, (int, float)) else x)
    
    if "标的近一年波动率" in display_df.columns:
        display_df["标的近一年波动率"] = display_df["标的近一年波动率"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) and isinstance(x, (int, float)) else x)
    
    if "折溢价率" in display_df.columns:
        display_df["折溢价率"] = display_df["折溢价率"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) and isinstance(x, (int, float)) else x)
    
    if "标的涨跌幅" in display_df.columns:
        display_df["标的涨跌幅"] = display_df["标的涨跌幅"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) and isinstance(x, (int, float)) else x)

    # 表格美化 - 根据数字特征添加样式
    def style_dataframe(df):
        """根据数字特征美化DataFrame"""
        def highlight_high_values(val):
            """高值标红"""
            if pd.isna(val):
                return ''
            try:
                if isinstance(val, str) and '%' in val:
                    num_val = float(val.replace('%', ''))
                    if num_val > 10:  # 涨跌幅、波动率等超过10%
                        return 'background-color: #ffebee; color: #c62828; font-weight: bold'
                elif isinstance(val, (int, float)) and val > 0:
                    if val > 100:  # 杠杆比率等超过100
                        return 'background-color: #ffebee; color: #c62828; font-weight: bold'
                    elif val > 50:  # 中等高值
                        return 'background-color: #fff3e0; color: #ef6c00'
            except:
                pass
            return ''
        
        def highlight_low_values(val):
            """低值标绿"""
            if pd.isna(val):
                return ''
            try:
                if isinstance(val, str) and '%' in val:
                    num_val = float(val.replace('%', ''))
                    if num_val < -5:  # 大幅下跌
                        return 'background-color: #e8f5e8; color: #2e7d32; font-weight: bold'
                elif isinstance(val, (int, float)) and val < 0:
                    return 'background-color: #e8f5e8; color: #2e7d32'
            except:
                pass
            return ''
        
        def highlight_risk_level(val):
            """风险等级着色"""
            if pd.isna(val):
                return ''
            if isinstance(val, str):
                if '高风险' in val:
                    return 'background-color: #ffebee; color: #c62828; font-weight: bold'
                elif '中风险' in val:
                    return 'background-color: #fff3e0; color: #ef6c00; font-weight: bold'
                elif '低风险' in val:
                    return 'background-color: #e8f5e8; color: #2e7d32; font-weight: bold'
            return ''
        
        # 应用样式
        styled_df = df.style
        
        # 数值列高亮
        numeric_cols = ['涨跌幅', '隐含波动率', '标的近一年波动率', '折溢价率', '标的涨跌幅', '实际杠杆比率']
        for col in numeric_cols:
            if col in df.columns:
                styled_df = styled_df.applymap(highlight_high_values, subset=[col])
                styled_df = styled_df.applymap(highlight_low_values, subset=[col])
        
        # 杠杆比率特殊处理
        if '实际杠杆比率' in df.columns:
            styled_df = styled_df.applymap(
                lambda x: 'background-color: #ffebee; color: #c62828; font-weight: bold' 
                if pd.notna(x) and isinstance(x, (int, float)) and x > 20 else '',
                subset=['实际杠杆比率']
            )
        
        # 风险等级着色
        if '合约特征' in df.columns:
            styled_df = styled_df.applymap(highlight_risk_level, subset=['合约特征'])
        
        # 希腊字母列着色
        greek_cols = ['Delta', 'Gamma', 'Theta', 'Vega', 'Rho']
        for col in greek_cols:
            if col in df.columns:
                styled_df = styled_df.applymap(
                    lambda x: 'background-color: #e3f2fd; color: #1565c0' 
                    if pd.notna(x) and isinstance(x, (int, float)) and abs(x) > 0.5 else '',
                    subset=[col]
                )
        
        # 价格列着色
        price_cols = ['最新价', '理论价格', '标的最新价', '盈亏平衡价']
        for col in price_cols:
            if col in df.columns:
                styled_df = styled_df.applymap(
                    lambda x: 'background-color: #f3e5f5; color: #7b1fa2' 
                    if pd.notna(x) and isinstance(x, (int, float)) and x > 0 else '',
                    subset=[col]
                )
        
        return styled_df
    
    # 应用美化样式
    styled_df = style_dataframe(display_df)
    st.dataframe(styled_df, use_container_width=True, height=520)
    
    # 添加特征说明
    st.markdown("""
    **📋 合约特征说明：**
    - **📈Delta等级**：📈高Delta(>0.7) | 📊中Delta(0.5-0.7) | 📉低Delta(<0.5)
    - **⚡杠杆等级**：⚡超高杠杆(>15) | 🔥高杠杆(10-15) | ⚖️中杠杆(5-10) | 🛡️低杠杆(<5)
    - **🌊Vega等级**：🌊高Vega(前20%) | 🌊中Vega(20%-50%) | 🌊低Vega(后50%)
    - **⏰时间衰减**：⏰高时间衰减(>0.5) | ⏱️中时间衰减(0.2-0.5) | ⏳低时间衰减(<0.2)
    - **🎯风险等级**：🔴高风险(高Delta+高杠杆) | 🟡中风险(中Delta+中杠杆) | 🟢低风险(其他)
    
    **💎 价值分析说明：**
    - **时间价值**：期权剩余有效期内的价值，随到期时间减少而衰减
    - **内在价值**：期权立即履行时的价值，看涨期权=max(标的价格-行权价,0)，看跌期权=max(行权价-标的价格,0)
    - **隐含波动率**：市场对未来波动率的预期，影响期权定价
    - **理论价格**：Black-Scholes模型计算的理论价格，用于判断期权是否被高估或低估
    - **标的近一年波动率**：历史波动率，用于对比隐含波动率
    
    **💰 折溢价分析说明：**
    - **行权价**：期权合约规定的执行价格
    - **折溢价率**：投资者以现价买入期权并持有至到期时，标的需要上升或下跌多少才能使投资保本
    - **盈亏平衡价**：期权投资者实现投资收益为零时标的证券的价格
    - **标的名称**：期权对应的标的资产名称
    - **标的最新价**：标的资产当前价格
    - **标的涨跌幅**：标的资产当日的涨跌幅，用于判断市场情绪
    
    **📊 希腊字母说明：**
    - **Rho**：无风险利率变化对期权价格的影响程度
    """)


if __name__ == "__main__":
    main()


