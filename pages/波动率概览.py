import streamlit as st

st.set_page_config(page_title="波动率概览", page_icon="🌐", layout="wide")

def main():
    st.markdown("## 波动率概览")
    st.caption("来源：OpenVLab 市场 | 嵌入站点供快速查看")

    st.markdown(
        "参考站点：[`https://www.openvlab.cn/market`](https://www.openvlab.cn/market)")

    st.markdown("---")
    st.info("如页面未正常显示，可切换为本地代理嵌入以规避嵌入限制（合规自评后使用）。")

    # 采用 components.html 嵌入外部页面；可选启用本地反代
    try:
        import streamlit.components.v1 as components
        use_proxy = st.toggle("使用本地代理嵌入（需要本机端口可用）", value=False)
        if use_proxy:
            try:
                from utils.reverse_proxy import ensure_proxy_running
                base = ensure_proxy_running()
                src = f"{base}/ovlab/market"
            except Exception:
                st.error("本地代理启动失败，已回退直连模式。")
                src = "https://www.openvlab.cn/market"
        else:
            src = "https://www.openvlab.cn/market"

        components.html(
            f'<iframe src="{src}" style="width:100%; height:86vh; border:none;"></iframe>',
            height=800,
            scrolling=True,
        )
    except Exception:
        st.error("嵌入失败，可点击上方链接在新窗口打开。")

if __name__ == "__main__":
    main()


