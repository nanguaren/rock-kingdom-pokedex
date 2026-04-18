import streamlit as st
import pandas as pd
import json
import os
import sys

# 1. 环境准备
sys.path.append(os.getcwd())
try:
    from data_loader import load_data
    from type_chart import TYPE_MAP, get_effectiveness
except ImportError:
    st.error("❌ 核心文件缺失：请确保根目录下有 data_loader.py 和 type_chart.py")
    st.stop()

# --- 页面配置 ---
st.set_page_config(page_title="联防实验室 Pro", layout="wide")

# --- 强力深色 CSS (锁定样式，防止渲染抖动) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1, h2, h3, p, span, label { color: #FAFAFA !important; }
    .slot-label {
        text-align: center;
        background-color: #161B22;
        padding: 5px;
        border-radius: 5px;
        border: 1px solid #30363D;
        margin-bottom: 5px;
        font-weight: bold;
        font-size: 14px;
    }
    .pvp-table {
        width: 100%; border-collapse: collapse; color: white;
        background-color: #161B22; font-size: 12px; margin-top: 20px;
    }
    .pvp-table th, .pvp-table td { border: 1px solid #30363D; padding: 8px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. 数据与存档逻辑
df, _ = load_data()
SAVE_FILE = "data/saved_teams.json"

if not os.path.exists("data"): os.makedirs("data")
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, 'w', encoding='utf-8') as f: json.dump({}, f)

# --- 【重点优化】: 构造“编号 - 名字”的搜索列表 ---
# 这样在 selectbox 里打编号或名字都能搜到
df_sorted = df.sort_values(by='编号_显示')
search_options = ["-- 空置 --"] + [f"{row['编号_显示']} - {row['名称']}" for _, row in df_sorted.iterrows()]

# 初始化 Session State (存储的是 编号-名字 字符串)
if 'current_team_v2' not in st.session_state:
    st.session_state.current_team_v2 = ["-- 空置 --"] * 6


def save_team(name):
    if not name: return
    with open(SAVE_FILE, 'r', encoding='utf-8') as f: teams = json.load(f)
    teams[name] = st.session_state.current_team_v2
    with open(SAVE_FILE, 'w', encoding='utf-8') as f: json.dump(teams, f, ensure_ascii=False)
    st.toast(f"✅ 阵容 '{name}' 保存成功！")


def load_team(name):
    with open(SAVE_FILE, 'r', encoding='utf-8') as f: teams = json.load(f)
    if name in teams:
        st.session_state.current_team_v2 = teams[name]
        st.rerun()


# --- 页面头部 ---
st.title("🛡️ 联防实验室 (竞技 Pro 版)")

with st.expander("📂 阵容存档与读取"):
    c1, c2 = st.columns([3, 1])
    with c1:
        t_name = st.text_input("阵容备注名", key="team_save_input")
    with c2:
        if st.button("💾 保存阵容", use_container_width=True): save_team(t_name)

    with open(SAVE_FILE, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    if saved_data:
        sel_load = st.selectbox("载入历史阵容", options=["-- 请选择 --"] + list(saved_data.keys()))
        if sel_load != "-- 请选择 --":
            if st.button("📂 确认载入", use_container_width=True): load_team(sel_load)

st.divider()

# 3. 核心 UI：六格位 (支持双向搜索)
st.subheader("👥 阵容成员 (输入名字或编号搜索)")
cols = st.columns(6)

for i in range(6):
    with cols[i]:
        st.markdown(f'<div class="slot-label">Slot {i + 1}</div>', unsafe_allow_html=True)

        # 获取当前值并容错处理
        current_val = st.session_state.current_team_v2[i]
        if current_val not in search_options:
            current_val = "-- 空置 --"

        selected = st.selectbox(
            f"Select_{i}",
            options=search_options,
            index=search_options.index(current_val),
            key=f"search_slot_{i}",
            label_visibility="collapsed"
        )
        st.session_state.current_team_v2[i] = selected

# 4. 数据解析
# 从 "001 - 喵喵" 中提取出 "喵喵"
active_team_names = []
for item in st.session_state.current_team_v2:
    if item != "-- 空置 --":
        name_only = item.split(" - ")[-1]  # 取横杠后的名字
        active_team_names.append(name_only)

if not active_team_names:
    st.info("💡 提示：在上方格子中输入编号（如 001）或名字，快速组建你的联防小队。")
    st.stop()

# 5. 联防矩阵计算
team_df = df[df['名称'].isin(active_team_names)]
all_types = list(TYPE_MAP.keys())

# 构造 HTML 表格
html_table = '<table class="pvp-table"><thead><tr><th>精灵 \\ 攻击</th>'
for t in all_types: html_table += f'<th>{t}</th>'
html_table += '</tr></thead><tbody>'

matrix_stats = []
for _, p in team_df.iterrows():
    p_types = p['属性'].split('+') if '+' in str(p['属性']) else [p['属性']]
    html_table += f'<tr><td><strong>{p["名称"]}</strong></td>'
    p_effs = []
    for atk_t in all_types:
        eff = get_effectiveness(atk_t, p_types)
        p_effs.append(eff)
        # 倍率着色逻辑
        bg = "#ff4b4b" if eff > 1 else ("#2ecc71" if 0 < eff < 1 else ("#3498db" if eff == 0 else "transparent"))
        html_table += f'<td style="background-color:{bg}; color:white; font-weight:bold;">{eff}</td>'
    matrix_stats.append(p_effs)
    html_table += '</tr>'
html_table += '</tbody></table>'

# 6. 稳定渲染区
# 用当前队伍的 hash 做 key，防止 React 节点冲突
analysis_hash = hash("".join(active_team_names))
with st.container(key=f"stable_analysis_{analysis_hash}"):
    st.subheader("📊 全队抗性表现")
    st.markdown(html_table, unsafe_allow_html=True)

    st.divider()
    st.subheader("🔍 战术诊断报告")

    m_df = pd.DataFrame(matrix_stats, columns=all_types)
    dangers, safes = [], []
    for t in all_types:
        w_cnt = (m_df[t] > 1).sum()
        r_cnt = (m_df[t] < 1).sum()
        if w_cnt >= 3: dangers.append(f"• **{t}系危机**：队内有 {w_cnt} 只精灵被克制")
        if r_cnt >= 4: safes.append(f"• **{t}系联防**：队内有 {r_cnt} 只精灵具有抗性")

    c_a, c_b = st.columns(2)
    with c_a:
        if dangers:
            st.error("#### ❌ 共同弱点\n\n" + "\n\n".join(dangers))
        else:
            st.success("#### ✅ 阵容无属性死角")
    with c_b:
        if safes:
            st.info("#### ✅ 联防优势\n\n" + "\n\n".join(safes))
        else:
            st.write("当前暂无突出抗性覆盖。")