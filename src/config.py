"""
Configuration module for chl_yantai_project.

This module defines project-wide path configurations and directory structure.
All paths are relative to the project root and are automatically created if they don't exist.

Constants:
    BASE_DIR: Project root directory
    DATA_DIR: Data directory
    RAW_DIR: Raw data directory
    PROCESSED_DIR: Processed data directory
    SAMPLES_DIR: Sample data directory
    SRC_DIR: Source code directory
    APP_DIR: Streamlit application directory
    OUTPUT_DIR: Output directory
    FIGURES_DIR: Figures output directory
    MAPS_DIR: Maps output directory
    REPORTS_DIR: Reports output directory
    PROJECT_NAME: Project display name
"""

from pathlib import Path

# 项目根目录（src 的上一级），不依赖用户目录；与 train/analysis/preprocess 内 __file__ 解析一致
BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLES_DIR = DATA_DIR / "samples"

SRC_DIR = BASE_DIR / "src"
APP_DIR = BASE_DIR / "app"

OUTPUT_DIR = BASE_DIR / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
MAPS_DIR = OUTPUT_DIR / "maps"
REPORTS_DIR = OUTPUT_DIR / "reports"

PROJECT_NAME = "烟台近岸海域叶绿素a遥感分析与可视化系统"

for folder in [
    DATA_DIR,
    RAW_DIR,
    PROCESSED_DIR,
    SAMPLES_DIR,
    OUTPUT_DIR,
    FIGURES_DIR,
    MAPS_DIR,
    REPORTS_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)