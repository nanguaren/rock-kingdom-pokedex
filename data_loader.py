import pandas as pd
import streamlit as st
import os


@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")

    if not os.path.exists(data_dir):
        return None, None

    files = os.listdir(data_dir)

    def read_file(keyword):
        target = next((f for f in files if keyword in f.lower()), None)
        if not target: return None
        path = os.path.join(data_dir, target)
        if path.endswith('.xlsx'):
            return pd.read_excel(path)
        # CSV 尝试多种编码
        for enc in ['utf-8-sig', 'gbk', 'utf-8']:
            try:
                return pd.read_csv(path, encoding=enc)
            except:
                continue
        return None

    # 1. 读取精灵数据
    df_stats = read_file("pokemon_stats")
    if df_stats is not None:
        df_stats['编号_显示'] = df_stats['编号'].astype(str).str.zfill(3)

    # 2. 读取技能数据 (优先读 wiki 那份，因为它有“可学习精灵”列)
    df_skills = read_file("skills_wiki")
    if df_skills is None:
        df_skills = read_file("skills")

    if df_skills is not None:
        # 统一列名映射，确保代码能读到
        rename_map = {
            '技能名': '技能名称',
            '耗能': '消耗能',
            '分类': '类型',
            '技能描述': '效果描述'
        }
        df_skills.rename(columns=rename_map, inplace=True)
        # 统一属性名
        if '属性' in df_skills.columns:
            df_skills['属性'] = df_skills['属性'].astype(str).str.replace('系', '')

    return df_stats, df_skills