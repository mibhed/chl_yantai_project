import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from pathlib import Path
import subprocess
import io
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
SAMPLES_PATH = BASE_DIR / "data" / "samples" / "mock_rrs_chla_samples.csv"
REPORT_DIR = BASE_DIR / "outputs" / "reports"
FIGURE_DIR = BASE_DIR / "outputs" / "figures"
MAP_DIR = BASE_DIR / "outputs" / "maps"
MODEL_REPORT_PATH = REPORT_DIR / "model_comparison.csv"
PRED_PATH = REPORT_DIR / "best_model_predictions.csv"
SCATTER_PATH = FIGURE_DIR / "best_model_scatter.png"
ERROR_HIST_PATH = FIGURE_DIR / "best_model_error_hist.png"

st.set_page_config(
    page_title="烟台近岸叶绿素a分析系统",
    layout="wide",
    initial_sidebar_state="expanded",
)
def ensure_analysis_outputs(region: str, year: int, month: int, model: str = "RF", progress_bar=None, status_text=None, force_regenerate: bool = False):
    """如果当前区域/年份/月的关键输出不存在，则自动生成。使用选定的模型进行预测。"""
    annual_summary_path = REPORT_DIR / f"annual_summary_{region}_{year}_{model}.csv"
    summary_path = REPORT_DIR / f"summary_{region}_{year}_{month:02d}_{model}.csv"
    monthly_path = REPORT_DIR / f"monthly_series_{region}_{year}_{model}.csv"
    map_path = MAP_DIR / f"mock_chla_map_{region}_{year}_{month:02d}_{model}.png"
    multi_region_path = REPORT_DIR / f"multi_region_series_{year}_{model}.csv"
    multi_year_path = REPORT_DIR / f"multi_year_series_{region}_2020_2025_{model}.csv"

    needed_files = [annual_summary_path, summary_path, monthly_path, map_path, multi_region_path, multi_year_path]

    # 如果不强制重新生成且文件都存在，则返回已存在
    if not force_regenerate and all(p.exists() for p in needed_files):
        return True, "已存在（直接读取）"

    try:
        from src.train import train_single_model
        from src.analysis import (
            generate_chla_grid_with_model, save_mock_map, summarize_grid,
            save_single_summary, generate_monthly_series_with_model,
            generate_multi_region_series_with_model, generate_multi_year_series_with_model,
            generate_annual_summary
        )
        
        if SAMPLES_PATH.exists():
            # 步骤2：读取样本数据
            if status_text:
                status_text.text("读取样本数据... 20%")
            if progress_bar:
                progress_bar.progress(20)
            
            df = pd.read_csv(SAMPLES_PATH)
            
            # 步骤3：训练模型
            if status_text:
                status_text.text(f"训练 {model} 模型... 40%")
            if progress_bar:
                progress_bar.progress(40)
            
            pipeline, feature_cols = train_single_model(df, model_name=model)
            
            # 步骤4：生成空间网格
            if status_text:
                status_text.text("生成空间分布网格... 50%")
            if progress_bar:
                progress_bar.progress(50)
            
            lon_grid, lat_grid, chl = generate_chla_grid_with_model(
                pipeline, feature_cols, region, year, month
            )
            
            # 步骤5：生成地图
            if status_text:
                status_text.text("生成空间分布地图... 60%")
            if progress_bar:
                progress_bar.progress(60)
            
            plt.figure(figsize=(8, 6))
            mesh = plt.pcolormesh(lon_grid, lat_grid, chl, shading="auto")
            plt.colorbar(mesh, label="Chl-a (mg/m³)")
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            plt.title(f"{region} {year}-{month:02d} {model} 模型预测叶绿素a空间分布")
            plt.tight_layout()
            plt.savefig(map_path, dpi=200)
            plt.close()
            
            # 步骤6：生成月度统计
            if status_text:
                status_text.text("生成月度统计数据... 70%")
            if progress_bar:
                progress_bar.progress(70)
            
            summary = summarize_grid(region, year, month, chl)
            save_single_summary(region, year, month, summary, model)
            
            # 步骤7：生成年度摘要
            if status_text:
                status_text.text("生成年度摘要... 80%")
            if progress_bar:
                progress_bar.progress(80)
            
            monthly_path, monthly_df = generate_monthly_series_with_model(pipeline, feature_cols, region, year, model)
            generate_annual_summary(region, year, monthly_df, model)
            
            # 步骤8：生成多区域和多年数据
            if status_text:
                status_text.text("生成多区域和多年对比数据... 90%")
            if progress_bar:
                progress_bar.progress(90)
            
            generate_multi_region_series_with_model(pipeline, feature_cols, year, model)
            generate_multi_year_series_with_model(pipeline, feature_cols, region, 2020, 2025, model)
            
            return True, f"使用 {model} 模型生成成功"
        else:
            return False, "样本文件不存在"
    except Exception as e:
        return False, str(e)
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
generate_button = False
with st.sidebar:
    st.markdown("## 参数面板")
    year = st.selectbox("选择年份", [2020, 2021, 2022, 2023, 2024, 2025], index=5)
    month = st.selectbox("选择月份", list(range(1, 13)), index=8)
    region = st.selectbox("选择区域", ["烟台近岸整体", "芝罘湾", "四十里湾", "养马岛附近"])
    model = st.selectbox("选择模型", ["MLR", "RF", "GP", "XGB", "LGB", "ET"])
    st.markdown("---")
    generate_button = st.button("生成分析结果")
    st.caption("当前版本：V10 文件导入导出与多模型对比")

# 自动确保当前参数对应的输出文件存在
if generate_button:
    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 步骤1：检查文件是否存在
    status_text.text("检查现有文件... 10%")
    progress_bar.progress(10)
    
    # 强制重新生成，忽略已存在的文件
    ok, msg = ensure_analysis_outputs(region, year, month, model, progress_bar, status_text, force_regenerate=True)
    
    # 完成
    progress_bar.progress(100)
    status_text.text("处理完成！100%")
    
    # 显示生成结果
    if not ok:
        st.error(f"生成失败: {msg}")
    else:
        st.success(f"数据准备完成: {msg}")
        # 刷新页面以显示新生成的数据
        st.rerun()
else:
    # 点击按钮时才运行，不自动调用
    pass

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
    <span class="small-note">V10 新增：统一文件导入与导出、TIFF 预览、Excel 接入与导出、高清图导出、LGB/ET 模型对比。</span>
</div>
""", unsafe_allow_html=True)

# ========= 顶部摘要卡 =========
annual_summary_path = REPORT_DIR / f"annual_summary_{region}_{year}_{model}.csv"
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
    st.warning(f"当前区域 {region} / {year} / {model} 的年度摘要仍未生成成功。")

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
tab1, tab_import, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["首页总览", "文件导入与导出", "模型结果", "验证图", "样本预览", "空间分布与区域统计", "多区域/年度对比"]
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

# ========= 文件导入与导出 =========
with tab_import:
    st.markdown('<div class="section-title">文件导入与导出</div>', unsafe_allow_html=True)
    st.markdown("支持拖拽或选择多个文件，格式：CSV、Excel（.xlsx/.xls）、TIFF、常见图片（PNG/JPG）。")

    uploaded_files = st.file_uploader(
        "选择或拖拽文件到此处",
        type=["csv", "xlsx", "xls", "tif", "tiff", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="v10_file_import"
    )

    # Session state for training data from upload
    if "train_df_upload" not in st.session_state:
        st.session_state.train_df_upload = None

    if uploaded_files:
        for uf in uploaded_files:
            ext = Path(uf.name).suffix.lower()
            with st.expander(f"📄 {uf.name}", expanded=True):
                try:
                    if ext == ".csv":
                        df = pd.read_csv(uf)
                        st.dataframe(df.head(20), use_container_width=True)
                        if "chl_a" in df.columns:
                            if st.button(f"使用「{uf.name}」作为训练数据并训练模型", key=f"use_csv_{uf.name}"):
                                st.session_state.train_df_upload = df
                                try:
                                    from src.train import run_training
                                    run_training(df, dpi=200)
                                    st.success("训练完成，请到「模型结果」与「验证图」查看。")
                                except Exception as e:
                                    st.error(str(e))
                        else:
                            st.caption("表格中需包含 chl_a 列方可作为训练数据。")
                    elif ext in (".xlsx", ".xls"):
                        uf.seek(0)
                        xl = pd.ExcelFile(uf)
                        sheet = st.selectbox(f"选择 Sheet（{uf.name}）", xl.sheet_names, key=f"sheet_{uf.name}")
                        uf.seek(0)
                        df = pd.read_excel(uf, sheet_name=sheet)
                        st.dataframe(df.head(20), use_container_width=True)
                        if "chl_a" in df.columns:
                            if st.button(f"使用「{uf.name}」当前 Sheet 作为训练数据并训练", key=f"use_excel_{uf.name}_{sheet}"):
                                st.session_state.train_df_upload = df
                                try:
                                    from src.train import run_training
                                    run_training(df, dpi=200)
                                    st.success("训练完成，请到「模型结果」与「验证图」查看。")
                                except Exception as e:
                                    st.error(str(e))
                        else:
                            st.caption("表格中需包含 chl_a 列方可作为训练数据。")
                    elif ext in (".tif", ".tiff"):
                        try:
                            import tifffile
                            arr = tifffile.imread(uf)
                            if arr.ndim == 2:
                                band = arr
                            else:
                                band = arr[0] if arr.shape[0] <= 3 else arr[:, :, 0]
                            h, w = band.shape
                            max_side = 400
                            if max(h, w) > max_side:
                                step = max(1, max(h, w) // max_side)
                                band = band[::step, ::step]
                            import matplotlib.pyplot as plt
                            fig, ax = plt.subplots(figsize=(6, 5))
                            im = ax.imshow(band, cmap="viridis")
                            plt.colorbar(im, ax=ax, label="DN")
                            ax.set_title(f"TIFF 预览（{uf.name}）")
                            plt.tight_layout()
                            buf = io.BytesIO()
                            plt.savefig(buf, format="png", dpi=120)
                            plt.close()
                            buf.seek(0)
                            st.image(buf, use_container_width=True)
                        except Exception as e:
                            st.warning(f"TIFF 解析或预览失败: {e}")
                    elif ext in (".png", ".jpg", ".jpeg"):
                        st.image(uf, use_container_width=True, caption=uf.name)
                except Exception as e:
                    st.error(f"解析失败: {e}")

    st.markdown("---")
    st.markdown("### 导出")
    # Excel 导出
    if MODEL_REPORT_PATH.exists():
        results_df = pd.read_csv(MODEL_REPORT_PATH)
        buf_xlsx = io.BytesIO()
        with pd.ExcelWriter(buf_xlsx, engine="openpyxl") as w:
            results_df.to_excel(w, sheet_name="模型对比", index=False)
            if PRED_PATH.exists():
                pred_df = pd.read_csv(PRED_PATH)
                pred_df.to_excel(w, sheet_name="预测结果", index=False)
        buf_xlsx.seek(0)
        st.download_button("下载 Excel（模型对比 + 预测结果）", buf_xlsx, file_name="model_comparison_and_predictions.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    # 高清图导出
    dpi_export = st.selectbox("导出图片 DPI", [200, 300, 600], index=0, key="dpi_export")
    if st.button("生成并下载高清验证图"):
        try:
            from src.train import run_training
            df = st.session_state.get("train_df_upload")
            if df is None and SAMPLES_PATH.exists():
                df = pd.read_csv(SAMPLES_PATH)
            if df is None or "chl_a" not in df.columns:
                st.warning("请先上传包含 chl_a 的 CSV/Excel 并执行训练，或确保 data/samples 下有样本文件后运行 python src/train.py。")
            else:
                run_training(df, dpi=dpi_export)
                st.success(f"已按 DPI={dpi_export} 重新生成验证图，请使用下方按钮下载。")
        except Exception as e:
            st.error(str(e))
    if SCATTER_PATH.exists():
        with open(SCATTER_PATH, "rb") as f:
            st.download_button("下载散点图 PNG", f, file_name=f"best_model_scatter_dpi{dpi_export}.png", mime="image/png", key="dl_scatter_export")
    if ERROR_HIST_PATH.exists():
        with open(ERROR_HIST_PATH, "rb") as f:
            st.download_button("下载误差分布图 PNG", f, file_name=f"best_model_error_hist_dpi{dpi_export}.png", mime="image/png", key="dl_hist_export")

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
        buf_xlsx = io.BytesIO()
        with pd.ExcelWriter(buf_xlsx, engine="openpyxl") as w:
            results_df.to_excel(w, sheet_name="模型对比", index=False)
            if PRED_PATH.exists():
                pred_df = pd.read_csv(PRED_PATH)
                pred_df.to_excel(w, sheet_name="预测结果", index=False)
        buf_xlsx.seek(0)
        st.download_button("下载 Excel（模型对比 + 预测结果）", buf_xlsx, file_name="model_comparison_and_predictions.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_excel_tab2")
    else:
        st.warning("尚未找到模型训练结果文件，请先运行 python src/train.py 或在「文件导入与导出」中上传 CSV/Excel 后训练。")

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

    map_path = MAP_DIR / f"mock_chla_map_{region}_{year}_{month:02d}_{model}.png"
    summary_path = REPORT_DIR / f"summary_{region}_{year}_{month:02d}_{model}.csv"
    monthly_path = REPORT_DIR / f"monthly_series_{region}_{year}_{model}.csv"
    annual_summary_path = REPORT_DIR / f"annual_summary_{region}_{year}_{model}.csv"

    if st.button("重新生成当前区域分析结果", type="primary"):
        result = subprocess.run(
            [
                sys.executable,
                "src/analysis.py",
                "--region", region,
                "--year", str(year),
                "--month", str(month),
            ],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
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

    multi_region_path = REPORT_DIR / f"multi_region_series_{year}_{model}.csv"
    multi_year_path = REPORT_DIR / f"multi_year_series_{region}_2020_2025_{model}.csv"

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
st.success("V10：统一文件导入（CSV/Excel/TIFF/图片）、TIFF 解析预览、Excel 统计接入、Excel 与高清图导出、LightGBM 与 Extra Trees 模型对比。")