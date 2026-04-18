import streamlit as st
import pandas as pd
import os
import glob
import sys

# 1. 核心数据导入逻辑
sys.path.append(os.getcwd())
try:
    from data_loader import load_data
    from type_chart import TYPE_MAP, get_effectiveness
except ImportError:
    st.error("❌ 核心文件缺失：请确保根目录下有 data_loader.py 和 type_chart.py")
    st.stop()

# --- 2. 页面配置 ---
st.set_page_config(page_title="洛克竞技图鉴 - 完整版", layout="wide")

# --- 3. 极简静止 CSS (无悬停、无阴影、文字清晰) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; color: #FAFAFA !important; }
    h1, h2, h3, p, span, div, label { color: #FAFAFA !important; }

    /* 精灵卡片：彻底静态，无边框变色，无阴影 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        transition: none !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #30363D !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* 属性标签 */
    .t-badge {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 3px;
        color: white !important;
        font-size: 11px;
        margin-right: 4px;
    }

    [data-testid="stSidebar"] { background-color: #161B22 !important; }
    input { color: #0E1117 !important; }
    </style>
    """, unsafe_allow_html=True)


# --- 4. 辅助函数 ---
def get_type_color(t):
    colors = {"火": "#FF4B4B", "水": "#3498db", "草": "#2ecc71", "电": "#f1c40f", "冰": "#74b9ff", "武": "#e67e22",
              "毒": "#a29bfe", "土": "#d35400", "翼": "#81ecec", "萌": "#fd79a8", "虫": "#badc58", "石": "#95a5a6",
              "幽灵": "#6c5ce7", "龙": "#0984e3", "机械": "#b2bec3", "光": "#ffeaa7", "普通": "#bdc3c7"}
    return colors.get(t, "#636e72")


def get_stat_color(val):
    if val >= 135: return "#00b894"  # 极高
    if val >= 110: return "#55efc4"  # 优秀
    if val >= 85:  return "#ffe14d"  # 一般
    return "#ff7675"  # 薄弱


def get_img(sid, sname):
    img_dir = os.path.join("data", "spirit_icons")
    path = glob.glob(os.path.join(img_dir, f"NO{sid}_{sname}.*"))
    if not path: path = glob.glob(os.path.join(img_dir, f"NO{sid}_*.*"))
    return path[0] if path else None


# --- 5. 核心：详情弹窗 (功能最全版) ---
@st.dialog("精灵竞技档案", width="large")
def show_details(p):
    st.subheader(f"{p['名称']} (No.{p['编号_显示']})")

    col_img, col_stats = st.columns([1, 1.4])

    # --- 左侧：图片与防御分析 ---
    with col_img:
        img = get_img(p['编号_显示'], p['名称'])
        if img: st.image(img, use_container_width=True)

        st.write("**🛡️ 属性防御扫描**")
        p_types = p['属性'].split('+') if '+' in str(p['属性']) else [p['属性']]
        weak, res = [], []
        for atk_t in TYPE_MAP.keys():
            eff = get_effectiveness(atk_t, p_types)
            if eff > 1:
                weak.append(f"{atk_t}{eff}x")
            elif 0 < eff < 1:
                res.append(f"{atk_t}{eff}x")

        if weak: st.error(f"弱点: {', '.join(weak)}")
        if res: st.success(f"抗性: {', '.join(res)}")

    # --- 右侧：种族值与【速度分析】 ---
    with col_stats:
        st.write("**📊 种族值面板**")
        stats_conf = [("HP", '生命种族值'), ("物攻", '物攻种族值'), ("物防", '物防种族值'),
                      ("魔攻", '魔攻种族值'), ("魔防", '魔防种族值'), ("速度", '速度种族值')]

        for label, col in stats_conf:
            val = int(p[col])
            c1, c2, c3 = st.columns([1, 4, 1])
            c1.caption(label)
            c2.progress(min(val / 200, 1.0))
            c3.markdown(f"<span style='color:{get_stat_color(val)}; font-weight:bold;'>{val}</span>",
                        unsafe_allow_html=True)

        # 🚀 核心功能：速度竞争分析
        st.divider()
        curr_speed = int(p['速度种族值'])
        # 计算环境排名
        all_speeds = df['速度种族值'].dropna().astype(int)
        rank_pct = (all_speeds < curr_speed).sum() / len(all_speeds) * 100

        st.write(f"⚡ **速度先手权**: `超越环境 {rank_pct:.1f}% 的精灵`")

        # 寻找邻近对手 (±1 速最终形态)
        final_df = df[df['进化阶段'].str.contains('最终|形态', na=False)]
        neighbors = final_df[
            (final_df['速度种族值'] >= curr_speed - 1) &
            (final_df['速度种族值'] <= curr_speed + 1) &
            (final_df['名称'] != p['名称'])
            ].sort_values(by='速度种族值', ascending=False)

        if not neighbors.empty:
            st.caption("🚨 邻近竞速预警 (±1速):")
            comp_txt = []
            for _, n in neighbors.head(6).iterrows():
                diff = int(n['速度种族值']) - curr_speed
                color = "red" if diff > 0 else ("green" if diff < 0 else "orange")
                comp_txt.append(f"{n['名称']}({int(n['速度种族值'])}) :{color}[({'+' if diff > 0 else ''}{diff})]")
            st.markdown(" | ".join(comp_txt))
        else:
            st.caption("此速度区间暂无主要对手")

    # --- 底部：技能分类 ---
    st.divider()
    if df_skills is not None:
        skills = df_skills[df_skills['可学习精灵'].str.contains(p['名称'], na=False)]
        if not skills.empty:
            st.write("**⚔️ 可学习技能 (按类型分类)**")
            p_df = skills[skills['类型'].str.contains('物', na=False)]
            m_df = skills[skills['类型'].str.contains('魔', na=False)]
            s_df = skills[~skills.index.isin(p_df.index) & ~skills.index.isin(m_df.index)]

            t1, t2, t3 = st.tabs([f"物理 ({len(p_df)})", f"魔法 ({len(m_df)})", f"变化 ({len(s_df)})"])

            def render(target):
                if target.empty:
                    st.caption("暂无数据")
                else:
                    st.dataframe(target[['技能名称', '属性', '威力', '效果描述']], use_container_width=True,
                                 hide_index=True)

            with t1:
                render(p_df)
            with t2:
                render(m_df)
            with t3:
                render(s_df)


# --- 6. 主页面布局 ---
df, df_skills = load_data()

if df is None:
    st.error("精灵数据加载失败，请检查数据文件。")
    st.stop()

with st.sidebar:
    st.header("🔍 精准检索")
    query = st.text_input("搜索名字/编号")
    t_filter = st.selectbox("属性筛选", ["全部"] + sorted(list(df['属性'].unique())))

# 筛选
f_df = df.copy()
if query:
    f_df = f_df[f_df['名称'].str.contains(query, na=False) | f_df['编号_显示'].str.contains(query, na=False)]
if t_filter != "全部":
    f_df = f_df[f_df['属性'] == t_filter]

# 列表展示 (6列宫格)
st.write(f"共筛选出 {len(f_df)} 个竞技单位")
cols_per_row = 6
for i in range(0, len(f_df), cols_per_row):
    batch = f_df.iloc[i: i + cols_per_row]
    cols = st.columns(cols_per_row)
    for idx, (orig_idx, item) in enumerate(batch.iterrows()):
        with cols[idx]:
            with st.container(border=True):
                img_p = get_img(item['编号_显示'], item['名称'])
                if img_p: st.image(img_p, use_container_width=True)
                st.markdown(f"**{item['名称']}**")
                st.caption(f"No.{item['编号_显示']} | {item['属性']}")
                # 稳定版 Key
                if st.button("详情", key=f"btn_{orig_idx}_{item['编号_显示']}", use_container_width=True):
                    show_details(item)
