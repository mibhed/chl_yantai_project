from pathlib import Path

BASE_DIR = Path.home() / "projects" / "chl_yantai_project"

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