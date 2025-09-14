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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 3rem;
        letter-spacing: -0.02em;
    }
    
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 30%, #f093fb 70%, #f5576c 100%);
        padding: 4rem 2rem;
        border-radius: 2rem;
        color: white;
        text-align: center;
        margin: 3rem 0;
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
    }
    
    .hero-content {
        position: relative;
        z-index: 1;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 2.5rem;
        border-radius: 1.5rem;
        margin: 1.5rem 0;
        transition: all 0.4s ease;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .glass-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    .premium-nav {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 1.5rem;
        margin: 4rem 0;
        padding: 2rem;
        background: linear-gradient(145deg, #f8fafc, #e2e8f0);
        border-radius: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .premium-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 1rem 2rem;
        margin: 0.5rem;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        text-decoration: none;
        border-radius: 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        font-size: 0.95rem;
        letter-spacing: 0.025em;
        min-width: 200px;
    }
    
    .premium-button:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
        color: white;
        text-decoration: none;
    }
    
    .premium-button.primary {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        box-shadow: 0 8px 25px rgba(240, 147, 251, 0.4);
        transform: scale(1.1);
        font-weight: 700;
    }
    
    .premium-button.primary:hover {
        box-shadow: 0 15px 35px rgba(240, 147, 251, 0.6);
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 2rem;
        margin: 3rem 0;
        padding: 2rem;
    }
    
    .stat-card {
        background: linear-gradient(145deg, #ffffff, #f1f5f9);
        padding: 2rem;
        border-radius: 1.5rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.8);
        transition: all 0.3s ease;
        border-top: 4px solid #667eea;
    }
    
    .stat-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    .stat-number {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
    }
    
    .stat-label {
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
        gap: 2rem;
        margin: 3rem 0;
    }
    
    .premium-feature-card {
        background: linear-gradient(145deg, #ffffff, #f8fafc);
        padding: 2.5rem;
        border-radius: 1.5rem;
        border: 1px solid rgba(255,255,255,0.8);
        box-shadow: 0 12px 35px rgba(0,0,0,0.08);
        transition: all 0.4s ease;
        border-top: 4px solid #667eea;
    }
    
    .premium-feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        background: linear-gradient(145deg, #ffffff, #f1f5f9);
        border-top: 4px solid #f093fb;
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .feature-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        font-family: 'Inter', sans-serif;
    }
    
    .feature-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .feature-list li {
        padding: 0.5rem 0;
        color: #64748b;
        font-weight: 500;
        position: relative;
        padding-left: 0.5rem;
    }
    
    .tech-advantages {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 4rem 2rem;
        border-radius: 2rem;
        margin: 4rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .advantage-card {
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .advantage-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.12);
    }
    
    .advantage-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .section-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
        text-align: center;
        margin-bottom: 3rem;
        font-family: 'Inter', sans-serif;
        position: relative;
    }
    
    .footer-premium {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 2rem;
        margin-top: 4rem;
        text-align: center;
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(102, 126, 234, 0); }
        100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
    }
    
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.5rem;
        }
        .hero-section {
            padding: 2rem 1rem;
        }
        .premium-nav {
            padding: 1rem;
        }
        .premium-button {
            min-width: 180px;
            padding: 0.8rem 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 主标题
    st.markdown('<h1 class="main-header">🎆 智能金融分析平台</h1>', unsafe_allow_html=True)
    
    # 英雄区域
    st.markdown("""
    <div class="hero-section">
        <div class="hero-content">
            <h2 style="font-size: 3rem; margin-bottom: 1.5rem; font-weight: 700; letter-spacing: -0.02em;">🚀 专业级金融数据分析</h2>
            <p style="font-size: 1.4rem; margin-bottom: 2rem; opacity: 0.95; line-height: 1.6;">
                集成了期权分析、ETF技术分析、智能决策等全方位金融服务<br>
                基于先进的量化模型和人工智能技术，为您提供精准的投资分析和决策支持
            </p>
            <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-top: 2rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">📈</span>
                    <span style="font-weight: 600;">AI智能分析</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">🔍</span>
                    <span style="font-weight: 600;">深度数据挖掘</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">📊</span>
                    <span style="font-weight: 600;">实时可视化</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">💡</span>
                    <span style="font-weight: 600;">精准决策</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 重点推荐
    st.markdown('<div class="pulse">', unsafe_allow_html=True)
    st.success("🎆 热门推荐：【期权策略决策系统】- 基于AI的智能期权策略分析平台，助您精准把握市场机会！")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 平台统计
    st.markdown('<h2 class="section-title">📊 平台数据概览</h2>', unsafe_allow_html=True)
    st.markdown("""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">12</div>
            <div class="stat-label">智能分析模块</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">6</div>
            <div class="stat-label">主流ETF标的</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">20+</div>
            <div class="stat-label">技术指标</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">AI</div>
            <div class="stat-label">智能决策引擎</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 页面导航
    st.markdown('<h2 class="section-title">🚀 功能导航</h2>', unsafe_allow_html=True)
    st.markdown("""
    <div class="premium-nav">
        <a href="/01_期权策略决策系统" class="premium-button primary pulse">🧭 期权策略决策</a>
        <a href="/02_每日统计" class="premium-button">📊 每日统计</a>
        <a href="/03_ETF技术分析" class="premium-button">📈 ETF技术分析</a>
        <a href="/04_ETF对比分析" class="premium-button">📊 ETF对比分析</a>
        <a href="/05_海龟交易法则" class="premium-button">🐢 海龟交易法则</a>
        <a href="/期权基础知识" class="premium-button">📚 期权基础知识</a>
        <a href="/期权风险分析" class="premium-button">📊 期权合约分析</a>
        <a href="/保险策略" class="premium-button">🛡️ 期权保险策略</a>
        <a href="/价差策略" class="premium-button">📈 期权价差策略</a>
        <a href="/创业板期权波动率指数_QVIX" class="premium-button">📈 创业板QVIX</a>
        <a href="/波动率概览" class="premium-button">🌐 波动率概览</a>
        <a href="/期权交易心法精要" class="premium-button">🧠 期权交易心法</a>
    </div>
    """, unsafe_allow_html=True)
    
    # 功能特色
    st.markdown('<h2 class="section-title">🌆 核心功能</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="premium-feature-card">
            <div class="feature-icon">🧭</div>
            <h3 class="feature-title">期权策略决策</h3>
            <p>• 日线多因子共振分析</p>
            <p>• 趋势/动能/位置/能量全维度</p>
            <p>• AI智能策略自动映射</p>
            <p>• 实时风险提示与增强</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="premium-feature-card">
            <div class="feature-icon">📚</div>
            <h3 class="feature-title">期权基础知识</h3>
            <p>• 期权概念深度详解</p>
            <p>• 交易策略全面介绍</p>
            <p>• 希腊字母智能分析</p>
            <p>• 风险管理指南</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="premium-feature-card">
            <div class="feature-icon">📊</div>
            <h3 class="feature-title">每日统计</h3>
            <p>• 上交所期权实时数据</p>
            <p>• 深交所期权实时数据</p>
            <p>• 多维度交互可视化</p>
            <p>• 实时市场状态监控</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="premium-feature-card">
            <div class="feature-icon">🧠</div>
            <h3 class="feature-title">期权交易心法</h3>
            <p>• 交易心态修炼与纪律</p>
            <p>• 高级组合策略技巧</p>
            <p>• 最佳时机与移仓技巧</p>
            <p>• 专业交易哲学总结</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="premium-feature-card">
            <div class="feature-icon">📈</div>
            <h3 class="feature-title">ETF技术分析</h3>
            <p>• 四象限技术分析框架</p>
            <p>• 20+种技术指标共振</p>
            <p>• 智能信号识别系统</p>
            <p>• AI驱动投资建议</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="premium-feature-card">
            <div class="feature-icon">🐢</div>
            <h3 class="feature-title">海龟交易法则</h3>
            <p>• 经典趋势跟踪策略系统</p>
            <p>• 完整的风险管理体系</p>
            <p>• 程序化交易规则</p>
            <p>• 实时信号监控和回测</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 技术优势
    st.markdown('<h2 class="section-title">⚡ 技术优势</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="advantage-card">
            <div class="advantage-icon">🚀</div>
            <h3>高性能架构</h3>
            <p>✨ 智能数据缓存机制</p>
            <p>✨ 异步数据加载技术</p>
            <p>✨ 响应式界面设计</p>
            <p>✨ 实时数据更新推送</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="advantage-card">
            <div class="advantage-icon">🔍</div>
            <h3>深度分析</h3>
            <p>✨ 多维度技术指标</p>
            <p>✨ AI智能信号识别</p>
            <p>✨ 共振分析系统</p>
            <p>✨ 量化评分模型</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="advantage-card">
            <div class="advantage-icon">📊</div>
            <h3>可视化体验</h3>
            <p>✨ 交互式图表</p>
            <p>✨ 多类型图表支持</p>
            <p>✨ 自定义样式</p>
            <p>✨ 数据导出功能</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 使用说明
    st.markdown('<h2 class="section-title">📚 使用指南</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card">
        <h3 style="color: #1e293b; margin-bottom: 1.5rem; font-size: 1.5rem;">🚀 快速入门</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-bottom: 2rem;">
            <div>
                <h4 style="color: #667eea; margin-bottom: 1rem;">🎯 1. 选择分析模块</h4>
                <p>点击上方导航按钮，进入相应的智能分析页面</p>
            </div>
            <div>
                <h4 style="color: #667eea; margin-bottom: 1rem;">⚙️ 2. 配置分析参数</h4>
                <p>在侧边栏设置日期、标的等关键参数</p>
            </div>
            <div>
                <h4 style="color: #667eea; margin-bottom: 1rem;">📈 3. 查看分析结果</h4>
                <p>系统自动生成分析结果和可视化图表</p>
            </div>
            <div>
                <h4 style="color: #667eea; margin-bottom: 1rem;">📁 4. 导出数据</h4>
                <p>支持CSV、Excel等格式数据导出</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 免责声明
    st.markdown('<h2 class="section-title">⚠️ 风险提示</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fee2e2, #fecaca); padding: 2rem; border-radius: 1.5rem; border-left: 4px solid #f87171; margin: 2rem 0;">
        <h3 style="color: #991b1b; margin-bottom: 1.5rem; font-size: 1.3rem;">🚨 重要声明</h3>
        <div style="color: #7f1d1d; line-height: 1.8;">
            <p><strong>• 投资风险提示：</strong>本平台仅供学习和研究使用，不构成任何投资建议</p>
            <p><strong>• 数据准确性：</strong>所有数据和分析结果仅供参考，不保证绝对准确性</p>
            <p><strong>• 谨慎决策：</strong>投资有风险，入市需谨慎，请根据自身风险承受能力做出决策</p>
            <p><strong>• 独立判断：</strong>用户应基于自身分析和判断做出投资决策，自负盈亏</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 页脚
    st.markdown("""
    <div class="footer-premium">
        <div style="margin-bottom: 2rem;">
            <h3 style="margin-bottom: 1rem; font-size: 1.5rem;">🌟 专业金融分析平台</h3>
            <p style="opacity: 0.9; margin-bottom: 1.5rem;">基于先进的人工智能技术和量化分析模型构建</p>
            <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-bottom: 2rem;">
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🔬</div>
                    <div>技术驱动</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📊</div>
                    <div>数据精准</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🎯</div>
                    <div>决策智能</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🛡️</div>
                    <div>风控完善</div>
                </div>
            </div>
        </div>
        <div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top: 1.5rem; opacity: 0.8;">
            <p style="margin-bottom: 0.5rem;">© 2024 智能金融分析平台 | 基于Streamlit与AI技术构建</p>
            <p style="font-size: 0.9rem; opacity: 0.7;">数据来源：上海证券交易所、深圳证券交易所、东方财富等官方渠道</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()