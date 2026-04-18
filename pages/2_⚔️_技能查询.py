import streamlit as st
import sys
import os

sys.path.append(os.getcwd())
from data_loader import load_data

st.set_page_config(page_title="技能查询", layout="wide")

_, df_skills = load_data()

st.title("⚔️ 技能词典")
s_query = st.text_input("搜索技能名称或效果描述...")

if df_skills is not None:
    f_skills = df_skills.copy()
    if s_query:
        f_skills = f_skills[
            f_skills['技能名称'].str.contains(s_query, na=False) |
            f_skills['效果描述'].str.contains(s_query, na=False)
            ]

    # 宫格展示技能
    cols_per_row = 4
    for i in range(0, len(f_skills), cols_per_row):
        row = f_skills.iloc[i: i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, (_, sk) in enumerate(row.iterrows()):
            with cols[idx]:
                with st.container(border=True):
                    st.subheader(f"⚔️ {sk['技能名称']}")
                    st.write(f"**属性:** {sk['属性']} | **威力:** {sk['威力']}")
                    st.write(f"**消耗:** {sk['消耗能']}")
                    with st.expander("详细效果"):
                        st.write(sk['效果描述'])
else:
    st.error("未找到技能数据文件。")