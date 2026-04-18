import streamlit as st
import os

st.set_page_config(page_title="洛克王国图鉴系统", page_icon="🐾", layout="wide")

st.title("🐾 洛克王国图鉴系统")
st.markdown("""
### 系统模块介绍
请在**左侧边栏**选择功能：
* **📚 精灵图鉴**：宫格查看精灵，点击弹窗查看详情、种族值及可学习技能。
* **⚔️ 技能查询**：查看全技能效果及威力。
""")

st.divider()
st.subheader("📂 资源状态检查")
c1, c2 = st.columns(2)
with c1:
    if os.path.exists("data/pokemon_stats.xlsx"):
        st.success("✅ 精灵数据已就绪")
    else:
        st.error("❌ 缺少 data/pokemon_stats.xlsx")
with c2:
    if os.path.exists("data/spirit_icons"):
        st.success(f"✅ 图片库已就绪 ({len(os.listdir('data/spirit_icons'))}张)")
    else:
        st.warning("⚠️ 缺少图片文件夹 data/spirit_icons")