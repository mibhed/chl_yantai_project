import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
import subprocess

BASE_DIR = Path.home() / "projects" / "chl_yantai_project"
SAMPLES_PATH = BASE_DIR / "data" / "samples" / "mock_rrs_chla_samples.csv"
MODEL_REPORT_PATH = BASE_DIR / "outputs" / "reports" / "model_comparison.csv"
PRED_PATH = BASE_DIR / "outputs" / "reports" / "best_model_predictions.csv"
SCATTER_PATH = BASE_DIR / "outputs" / "figures" / "best_model_scatter.png"
ERROR_HIST_PATH = BASE_DIR / "outputs" / "figures" / "best_model_error_hist.png"
MAP_DIR = BASE_DIR / "outputs" / "maps"
REPORT_DIR = BASE_DIR / "outputs" / "reports"

st.set_page_config(
    page_title="烟台近岸叶绿素a分析系统",
    layout="wide",
    initial_sidebar_state="expanded",
)
def ensure_analysis_outputs(region: str, year: int, month: int):
    """如果当前区域/年份/月的关键输出不存在，则自动生成。"""
    annual_summary_path = REPORT_DIR / f"annual_summary_{region}_{year}.csv"
    summary_path = REPORT_DIR / f"summary_{region}_{year}_{month:02d}.csv"
    monthly_path = REPORT_DIR / f"monthly_series_{region}_{year}.csv"
    map_path = MAP_DIR / f"mock_chla_map_{region}_{year}_{month:02d}.png"

    needed_files = [annual_summary_path, summary_path, monthly_path, map_path]

    if all(p.exists() for p in needed_files):
        return True, "已存在"

    result = subprocess.run(
        [
            "python",
            "src/analysis.py",
            "--region", region,
            "--year", str(year),
            "--month", str(month),
        ],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return True, result.stdout.strip()
    return False, result.stderr.strip() if result.stderr else "生成失败"
# ========= 自定义样式 =========
st.markdown("""
<style>
:root {
    --primary: #0b5ed7;
    --secondary: #0aa2c0;
    --accent: #20c997;
    --bg-soft: #f4fbff;
    --card-bg: #ffffff;
    --text-main: #0f172a;
    --text-sub: #475569;
    --border-soft: #dbeafe;
}

html, body, [class*="css"] {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
}

.main {
    background: linear-gradient(180deg, #f7fcff 0%, #eef8ff 100%);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.banner {
    background: linear-gradient(135deg, #0b5ed7 0%, #0aa2c0 55%, #20c997 100%);
    padding: 28px 32px;
    border-radius: 22px;
    color: white;
    box-shadow: 0 10px 30px rgba(11, 94, 215, 0.22);
    margin-bottom: 20px;
}

.banner-title {
    font-size: 32px;
    font-weight: 800;
    line-height: 1.2;
    margin-bottom: 8px;
}

.banner-subtitle {
    font-size: 15px;
    opacity: 0.95;
    line-height: 1.8;
}

.section-title {
    font-size: 22px;
    font-weight: 800;
    color: var(--text-main);
    margin-top: 8px;
    margin-bottom: 10px;
}

.metric-card {
    background: var(--card-bg);
    border: 1px solid var(--border-soft);
    border-radius: 18px;
    padding: 18px 18px 14px 18px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
    min-height: 110px;
}

.metric-label {
    color: var(--text-sub);
    font-size: 13px;
    margin-bottom: 8px;
}

.metric-value {
    color: var(--text-main);
    font-size: 28px;
    font-weight: 800;
}

.metric-note {
    color: #0aa2c0;
    font-size: 12px;
    margin-top: 6px;
}

.info-card {
    background: white;
    border-left: 6px solid #0aa2c0;
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
    margin-bottom: 12px;
}

.small-note {
    color: #64748b;
    font-size: 13px;
}

.summary-box {
    background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%);
    border: 1px solid #dbeafe;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8fcff 0%, #eff8ff 100%);
}

[data-testid="stMetric"] {
    background: transparent;
    border: none;
    box-shadow: none;
}

div[data-baseweb="tab-list"] {
    gap: 10px;
}

button[data-baseweb="tab"] {
    border-radius: 12px !important;
    padding: 10px 16px !important;
    background: #f8fbff !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: #dff4ff !important;
    color: #0b5ed7 !important;
}

hr {
    margin-top: 0.8rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ========= 数据路径 =========
annual_summary_path = REPORT_DIR / "annual_summary_烟台近岸整体_2025.csv"

# ========= 侧边栏 =========
with st.sidebar:
    st.markdown("## 参数面板")
    year = st.selectbox("选择年份", [2020, 2021, 2022, 2023, 2024, 2025], index=5)
    month = st.selectbox("选择月份", list(range(1, 13)), index=8)
    region = st.selectbox("选择区域", ["烟台近岸整体", "芝罘湾", "四十里湾", "养马岛附近"])
    model = st.selectbox("选择模型", ["GP", "RF", "XGB", "MLR"])
    st.markdown("---")
    st.caption("当前版本：V9 海洋遥感展示增强版")
# 自动确保当前参数对应的输出文件存在
# 自动确保当前参数对应的输出文件存在
ok, msg = ensure_analysis_outputs(region, year, month)

# ========= 顶部横幅 =========
st.markdown(f"""
<div class="banner">
    <div class="banner-title">烟台近岸海域叶绿素 a 遥感分析与可视化系统</div>
    <div class="banner-subtitle">
        基于机器学习框架迁移的海岸带生态环境遥感分析原型系统<br>
        当前区域：<b>{region}</b>　|　年份：<b>{year}</b>　|　月份：<b>{month}</b>　|　主模型：<b>{model}</b>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-card">
    <b>项目定位：</b> 论文方法复现 + 区域迁移应用 + 时空分析与可视化展示。<br>
    <span class="small-note">当前系统已具备模型比较、验证图展示、空间分布、区域统计、多区域对比与年度对比功能。</span>
</div>
""", unsafe_allow_html=True)

# ========= 顶部摘要卡 =========
annual_summary_path = REPORT_DIR / f"annual_summary_{region}_{year}.csv"
annual_mean = "-"
peak_month = "-"
lowest_month = "-"
peak_value = "-"

if annual_summary_path.exists():
    annual_df = pd.read_csv(annual_summary_path)
    row = annual_df.iloc[0]
    annual_mean = row["annual_mean_chl_a"]
    peak_month = int(row["peak_month"])
    lowest_month = int(row["lowest_month"])
    peak_value = row["annual_max_monthly_mean"]
else:
    st.warning(f"当前区域 {region} / {year} 的年度摘要仍未生成成功。")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">研究区域</div>
        <div class="metric-value">{region}</div>
        <div class="metric-note">当前分析对象</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">年度均值</div>
        <div class="metric-value">{annual_mean}</div>
        <div class="metric-note">年尺度综合水平</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">峰值月份</div>
        <div class="metric-value">{peak_month}</div>
        <div class="metric-note">年内高值出现时间</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">最大月均值</div>
        <div class="metric-value">{peak_value}</div>
        <div class="metric-note">年度最高月均水平</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========= 标签页 =========
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["首页总览", "模型结果", "验证图", "样本预览", "空间分布与区域统计", "多区域/年度对比"]
)

with tab1:
    st.markdown('<div class="section-title">项目总览</div>', unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("""
        <div class="summary-box">
        <b>系统简介</b><br><br>
        本项目参考黄河口邻近海域叶绿素 a 机器学习反演研究框架，
        在缺少烟台本地原位 Chl-a 数据的前提下，
        采用“方法复现 + 区域迁移应用”的方式，
        构建了一个面向烟台近岸海域的遥感分析与可视化系统。<br><br>
        <b>当前系统能力：</b><br>
        1. 多模型训练结果展示<br>
        2. 最优模型验证图展示<br>
        3. 区域空间分布图生成<br>
        4. 区域月尺度变化分析<br>
        5. 多区域与多年份对比分析<br>
        6. 结果文件下载
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="summary-box">
        <b>适用方式</b><br><br>
        你可以通过左侧参数面板选择区域、年份、月份和模型，
        点击“生成当前区域分析结果”后，
        系统将自动生成对应的空间图、统计摘要、月尺度分析结果与年度摘要。<br><br>
        当前版本使用模拟数据驱动，
        后续只需替换为真实遥感特征数据，即可迁移为真实应用版。
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-title">模型结果</div>', unsafe_allow_html=True)
    if MODEL_REPORT_PATH.exists():
        results_df = pd.read_csv(MODEL_REPORT_PATH)
        st.dataframe(results_df, width="stretch")

        col_a, col_b = st.columns(2)
        with col_a:
            fig_r2 = px.bar(results_df, x="model", y="R2", title="模型 R² 对比", text="R2")
            st.plotly_chart(fig_r2, width="stretch")
        with col_b:
            fig_rmse = px.bar(results_df, x="model", y="RMSE", title="模型 RMSE 对比", text="RMSE")
            st.plotly_chart(fig_rmse, width="stretch")

        best_model = results_df.iloc[0]["model"]
        best_r2 = results_df.iloc[0]["R2"]

        st.markdown(f"""
        <div class="info-card">
            <b>自动结论：</b> 当前表现最好的模型为 <b>{best_model}</b>，
            在当前样本与流程下取得了 <b>R² = {best_r2}</b> 的效果，
            可作为系统默认主模型。
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="下载模型对比结果 CSV",
            data=results_df.to_csv(index=False).encode("utf-8"),
            file_name="model_comparison.csv",
            mime="text/csv"
        )
    else:
        st.warning("尚未找到模型训练结果文件，请先运行 python src/train.py")

with tab3:
    st.markdown('<div class="section-title">最佳模型验证图</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if SCATTER_PATH.exists():
            st.image(str(SCATTER_PATH), width="stretch")
            with open(SCATTER_PATH, "rb") as f:
                st.download_button("下载散点图 PNG", f, file_name="best_model_scatter.png", mime="image/png")
        else:
            st.warning("尚未找到散点图")

    with col2:
        if ERROR_HIST_PATH.exists():
            st.image(str(ERROR_HIST_PATH), width="stretch")
            with open(ERROR_HIST_PATH, "rb") as f:
                st.download_button("下载误差分布图 PNG", f, file_name="best_model_error_hist.png", mime="image/png")
        else:
            st.warning("尚未找到误差分布图")

    if PRED_PATH.exists():
        pred_df = pd.read_csv(PRED_PATH)
        st.markdown("### 预测结果预览")
        st.dataframe(pred_df.head(20), width="stretch")

with tab4:
    st.markdown('<div class="section-title">样本预览</div>', unsafe_allow_html=True)
    if SAMPLES_PATH.exists():
        samples_df = pd.read_csv(SAMPLES_PATH)
        st.dataframe(samples_df.head(20), width="stretch")

        stats_df = samples_df["chl_a"].describe().reset_index()
        stats_df.columns = ["统计量", "数值"]

        col1, col2 = st.columns([1.2, 1])
        with col1:
            st.markdown("### 样本数据预览")
            st.dataframe(samples_df.head(15), width="stretch")
        with col2:
            st.markdown("### Chl-a 统计摘要")
            st.dataframe(stats_df, width="stretch")

        st.download_button(
            label="下载模拟样本 CSV",
            data=samples_df.to_csv(index=False).encode("utf-8"),
            file_name="mock_rrs_chla_samples.csv",
            mime="text/csv"
        )
    else:
        st.warning("尚未找到样本文件，请先运行 python src/preprocess.py")

with tab5:
    st.markdown('<div class="section-title">空间分布与区域统计</div>', unsafe_allow_html=True)

    map_path = MAP_DIR / f"mock_chla_map_{region}_{year}_{month:02d}.png"
    summary_path = REPORT_DIR / f"summary_{region}_{year}_{month:02d}.csv"
    monthly_path = REPORT_DIR / f"monthly_series_{region}_{year}.csv"
    annual_summary_path = REPORT_DIR / f"annual_summary_{region}_{year}.csv"

    if st.button("重新生成当前区域分析结果", type="primary"):
        result = subprocess.run(
            [
                "python",
                "src/analysis.py",
                "--region", region,
                "--year", str(year),
                "--month", str(month),
            ],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            st.success("分析结果生成成功")
            st.code(result.stdout)
        else:
            st.error(result.stderr if result.stderr else "生成失败")

    left, right = st.columns([1.45, 1])

    with left:
        st.markdown("### 当前月份空间分布图")
        if map_path.exists():
            st.image(str(map_path), width="stretch")
            with open(map_path, "rb") as f:
                st.download_button("下载当前空间图 PNG", f, file_name=map_path.name, mime="image/png")
        else:
            st.info("当前区域和时间的空间图尚未生成。")

    with right:
        st.markdown("### 当前月份统计摘要")
        if summary_path.exists():
            summary_df = pd.read_csv(summary_path)
            row = summary_df.iloc[0]
            st.dataframe(summary_df, width="stretch")

            a, b = st.columns(2)
            a.metric("均值", row["mean_chl_a"])
            b.metric("标准差", row["std_chl_a"])
            c, d = st.columns(2)
            c.metric("最大值", row["max_chl_a"])
            d.metric("最小值", row["min_chl_a"])

            st.download_button(
                "下载当前月份统计 CSV",
                summary_df.to_csv(index=False).encode("utf-8"),
                file_name=summary_path.name,
                mime="text/csv"
            )
        else:
            st.info("当前统计摘要尚未生成。")

        st.markdown("### 年度摘要")
        if annual_summary_path.exists():
            annual_df = pd.read_csv(annual_summary_path)
            st.dataframe(annual_df, width="stretch")
        else:
            st.info("年度摘要尚未生成。")

    st.markdown("### 区域月尺度变化曲线")
    if monthly_path.exists():
        monthly_df = pd.read_csv(monthly_path)
        fig_monthly = px.line(
            monthly_df,
            x="month",
            y="mean_chl_a",
            markers=True,
            title=f"{region} {year} 年月均叶绿素a变化"
        )
        st.plotly_chart(fig_monthly, width="stretch")

        mean_val = round(float(monthly_df["mean_chl_a"].mean()), 4)
        max_month = int(monthly_df.loc[monthly_df["mean_chl_a"].idxmax(), "month"])
        min_month = int(monthly_df.loc[monthly_df["mean_chl_a"].idxmin(), "month"])

        st.markdown(f"""
        <div class="info-card">
            <b>自动结论：</b> {region} 在 {year} 年的月均 Chl-a 整体均值为 <b>{mean_val}</b>，
            其中高值主要出现在 <b>{max_month}</b> 月，低值主要出现在 <b>{min_month}</b> 月。
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            "下载区域月尺度统计 CSV",
            monthly_df.to_csv(index=False).encode("utf-8"),
            file_name=monthly_path.name,
            mime="text/csv"
        )
    else:
        st.info("当前区域月尺度统计尚未生成。")

with tab6:
    st.markdown('<div class="section-title">多区域 / 年度对比</div>', unsafe_allow_html=True)

    multi_region_path = REPORT_DIR / f"multi_region_series_{year}.csv"
    multi_year_path = REPORT_DIR / f"multi_year_series_{region}_2020_2025.csv"

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"### {year} 年多区域月均对比")
        if multi_region_path.exists():
            multi_region_df = pd.read_csv(multi_region_path)
            fig_region_compare = px.line(
                multi_region_df,
                x="month",
                y="mean_chl_a",
                color="region",
                markers=True,
                title=f"{year} 年多区域月均叶绿素a对比"
            )
            st.plotly_chart(fig_region_compare, width="stretch")

            annual_region_mean = (
                multi_region_df.groupby("region", as_index=False)["mean_chl_a"]
                .mean()
                .rename(columns={"mean_chl_a": "annual_mean_chl_a"})
                .sort_values("annual_mean_chl_a", ascending=False)
            )
            fig_region_bar = px.bar(
                annual_region_mean,
                x="region",
                y="annual_mean_chl_a",
                title=f"{year} 年区域年均叶绿素a对比",
                text="annual_mean_chl_a"
            )
            st.plotly_chart(fig_region_bar, width="stretch")
        else:
            st.info("多区域对比文件尚未生成。")

    with col_b:
        st.markdown(f"### {region} 2020-2025 年对比")
        if multi_year_path.exists():
            multi_year_df = pd.read_csv(multi_year_path)
            fig_year_compare = px.line(
                multi_year_df,
                x="month",
                y="mean_chl_a",
                color="year",
                markers=True,
                title=f"{region} 2020-2025 年月均叶绿素a对比"
            )
            st.plotly_chart(fig_year_compare, width="stretch")

            annual_year_mean = (
                multi_year_df.groupby("year", as_index=False)["mean_chl_a"]
                .mean()
                .rename(columns={"mean_chl_a": "annual_mean_chl_a"})
            )
            fig_year_bar = px.bar(
                annual_year_mean,
                x="year",
                y="annual_mean_chl_a",
                title=f"{region} 2020-2025 年年均叶绿素a对比",
                text="annual_mean_chl_a"
            )
            st.plotly_chart(fig_year_bar, width="stretch")
        else:
            st.info("多年份对比文件尚未生成。")

st.markdown("---")
st.success("第 9 版已完成：界面美化、总览卡片、自动结论摘要和下载功能增强。")