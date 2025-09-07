#!/usr/bin/env python3
"""
金融数据分析平台启动脚本
支持多页面应用：期权分析、ETF技术分析、ETF对比分析
"""

import subprocess
import sys
import os

def main():
    """启动Streamlit应用"""
    try:
        # 检查是否在正确的目录
        if not os.path.exists("app.py"):
            print("错误：请在包含app.py的目录中运行此脚本")
            sys.exit(1)
        
        # 启动Streamlit应用
        print("🚀 启动金融数据分析平台...")
        print("📊 期权分析 - 主页面")
        print("📈 ETF技术分析 - /etf_analysis")
        print("📊 ETF对比分析 - /etf_comparison")
        print("\n正在启动应用，请稍候...")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
