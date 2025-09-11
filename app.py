import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .feature-card {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
        transition: transform 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .nav-button {
        display: inline-block;
        padding: 15px 30px;
        margin: 10px;
        background: linear-gradient(45deg, #1f77b4, #28a745);
        color: white;
        text-decoration: none;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        color: white;
        text-decoration: none;
    }
    .stats-container {
        display: flex;
        justify-content: space-around;
        flex-wrap: wrap;
        margin: 2rem 0;
    }
    .stat-item {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 0.5rem;
        min-width: 150px;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .stat-label {
        font-size: 1rem;
        color: #666;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 主标题
    st.markdown('<h1 class="main-header">📊 金融数据分析平台</h1>', unsafe_allow_html=True)
    # 首次进入首页时，提示并提供直达 ETF 技术分析
    st.info("默认推荐进入 ETF 技术分析（已将创业板ETF设为默认）。您也可使用下方导航进入其他页面。")
    
    # 欢迎卡片
    st.markdown("""
    <div class="welcome-card">
        <h2 style="font-size: 2.5rem; margin-bottom: 1rem;">🚀 欢迎使用金融数据分析平台</h2>
        <p style="font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.9;">
            专业的金融数据分析工具，提供期权分析、ETF技术分析、每日统计等全方位服务
        </p>
        <div style="font-size: 1.1rem; opacity: 0.8;">
            📈 实时数据 | 🔍 深度分析 | 📊 可视化图表 | 💡 投资建议
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 平台统计
    st.markdown("""
    <div class="stats-container">
        <div class="stat-item">
            <div class="stat-number">8</div>
            <div class="stat-label">分析模块</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">6</div>
            <div class="stat-label">ETF标的</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">15+</div>
            <div class="stat-label">技术指标</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">实时</div>
            <div class="stat-label">数据更新</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 页面导航
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0;">
        <h2 style="color: #333; margin-bottom: 2rem;">🔗 快速导航</h2>
        <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 1rem;">
            <a href="/每日统计" class="nav-button">📊 每日统计</a>
            <a href="/etf技术分析" class="nav-button">📈 ETF技术分析（默认创业板）</a>
            <a href="/etf技术分析" class="nav-button">📈 ETF技术分析</a>
            <a href="/etf对比分析" class="nav-button">📊 ETF对比分析</a>
            <a href="/期权基础知识" class="nav-button">📚 期权基础知识</a>
            <a href="/期权风险分析" class="nav-button">📊 期权合约分析</a>
            <a href="/保险策略" class="nav-button">🛡️ 期权保险策略</a>
            <a href="/价差策略" class="nav-button">📈 期权价差策略</a>
            <a href="/创业板期权波动率指数_QVIX" class="nav-button">📈 创业板QVIX</a>
            <a href="/波动率概览" class="nav-button">🌐 波动率概览</a>
            <a href="/期权交易心法精要" class="nav-button">🧠 期权交易心法</a>
            <a href="/期权策略决策系统" class="nav-button">🧭 期权策略决策</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 功能特色
    st.markdown("## 🌟 平台特色")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 每日统计</h3>
            <p>• 上交所期权每日统计数据</p>
            <p>• 深交所期权每日统计数据</p>
            <p>• 多维度可视化分析</p>
            <p>• 实时市场概况</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>📈 ETF技术分析</h3>
            <p>• 四象限技术分析框架</p>
            <p>• 指标共振系统</p>
            <p>• 15+种技术指标</p>
            <p>• 智能投资建议</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 ETF对比分析</h3>
            <p>• 多ETF横向对比</p>
            <p>• 综合评分排名</p>
            <p>• 价格走势图表</p>
            <p>• 投资建议汇总</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>📚 期权基础知识</h3>
            <p>• 期权概念详解</p>
            <p>• 交易策略介绍</p>
            <p>• 希腊字母分析</p>
            <p>• 风险管理指南</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>🛡️ 期权保险策略</h3>
            <p>• 保护性看跌期权</p>
            <p>• 备兑看涨期权</p>
            <p>• 领子策略分析</p>
            <p>• 策略对比与选择</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>📈 期权价差策略</h3>
            <p>• 牛市看涨价差</p>
            <p>• 熊市看跌价差</p>
            <p>• 铁鹰、蝶式等组合</p>
            <p>• 收益结构与风险控制</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>🧠 期权交易心法</h3>
            <p>• 心态修炼与纪律</p>
            <p>• 组合策略与应对</p>
            <p>• 时机与移仓技巧</p>
            <p>• 交易哲学总结</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>🧭 期权策略决策</h3>
            <p>• 日线多因子共振</p>
            <p>• 趋势/动能/位置/能量</p>
            <p>• 策略自动映射</p>
            <p>• 风险提示与增强</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 技术优势
    st.markdown("## ⚡ 技术优势")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🚀 高性能
        - 数据缓存机制
        - 异步数据加载
        - 响应式界面设计
        - 实时数据更新
        """)
    
    with col2:
        st.markdown("""
        ### 🔍 深度分析
        - 多维度技术指标
        - 智能信号识别
        - 共振分析系统
        - 量化评分模型
        """)
    
    with col3:
        st.markdown("""
        ### 📊 可视化
        - 交互式图表
        - 多类型图表支持
        - 自定义样式
        - 数据导出功能
        """)
    
    # 使用说明
    st.markdown("## 📖 使用说明")
    
    st.markdown("""
    ### 快速开始
    1. **选择分析模块**：点击上方导航按钮进入相应分析页面
    2. **配置参数**：在侧边栏设置分析参数（日期、标的等）
    3. **查看结果**：系统自动生成分析结果和可视化图表
    4. **导出数据**：支持CSV格式数据导出
    
    ### 注意事项
    - 数据更新频率：ETF数据缓存1小时，每日统计实时更新
    - 网络要求：需要稳定的网络连接获取实时数据
    - 浏览器兼容：建议使用Chrome、Firefox等现代浏览器
    - 数据时效：交易日数据，非交易日可能无法获取最新数据
    """)
    
    # 免责声明
    st.markdown("## ⚠️ 免责声明")
    
    st.warning("""
    **重要提示**：
    - 本平台仅供学习和研究使用，不构成投资建议
    - 所有数据和分析结果仅供参考，不保证准确性
    - 投资有风险，入市需谨慎
    - 请根据自身风险承受能力谨慎操作
    """)
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <p>© 2024 金融数据分析平台 | 基于Streamlit和akshare构建</p>
        <p>数据来源：上海证券交易所、深圳证券交易所、东方财富等</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()