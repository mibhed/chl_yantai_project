"""
MODIS L2 → 叶绿素a遥感反演核心模块

实现从 MODIS L2 卫星影像到 Chl-a 分布图的端到端处理流程：

  MODIS L2 (NetCDF/HDF5)
       ↓
  读取 Rrs 波段 + 经纬度
       ↓
  按区域裁剪（可选）
       ↓
  按质量标志过滤（可选）
       ↓
  计算水色特征（含 NDCI 等）
       ↓
  加载 ML 模型
       ↓
  逐像素/批量预测 Chl-a
       ↓
  导出 Chl-a GeoTIFF
       ↓
  生成统计报告
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import warnings

try:
    import tifffile
    TIFFILE_AVAILABLE = True
except ImportError:
    TIFFILE_AVAILABLE = False

try:
    import rasterio
    from rasterio.transform import from_bounds
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "outputs" / "models"
MAPS_DIR = BASE_DIR / "outputs" / "maps"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MAPS_DIR.mkdir(parents=True, exist_ok=True)

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from lightgbm import LGBMRegressor
    HAS_LGB = True
except ImportError:
    HAS_LGB = False


# ============================================================
# 特征工程（与 preprocess.py 中的 _compute_derived_features 逻辑一致）
# ============================================================

def compute_rrs_features(rrs_bands: Dict[str, np.ndarray]) -> Tuple[Dict[str, np.ndarray], List[str]]:
    """
    从 Rrs 波段字典计算所有派生特征（含水色指数）。

    Parameters
    ----------
    rrs_bands : dict
        Rrs 波段字典，格式: {"Rrs_443": array_2d, ...}

    Returns
    -------
    tuple
        (特征字典, 特征名列表)
    """
    eps = 1e-6
    features = {}
    rrs = {k: rrs_bands.get(k) for k in [
        "Rrs_412", "Rrs_443", "Rrs_469", "Rrs_488",
        "Rrs_531", "Rrs_547", "Rrs_555", "Rrs_645", "Rrs_667", "Rrs_678"
    ]}

    # Band ratios
    if rrs["Rrs_443"] is not None and rrs["Rrs_555"] is not None:
        features["ratio_443_555"] = rrs["Rrs_443"] / (rrs["Rrs_555"] + eps)
    if rrs["Rrs_488"] is not None and rrs["Rrs_555"] is not None:
        features["ratio_488_555"] = rrs["Rrs_488"] / (rrs["Rrs_555"] + eps)
    if rrs["Rrs_531"] is not None and rrs["Rrs_547"] is not None:
        features["ratio_531_547"] = rrs["Rrs_531"] / (rrs["Rrs_547"] + eps)
    if rrs["Rrs_443"] is not None and rrs["Rrs_488"] is not None:
        features["ratio_443_488"] = rrs["Rrs_443"] / (rrs["Rrs_488"] + eps)

    # Band differences
    if rrs["Rrs_488"] is not None and rrs["Rrs_555"] is not None:
        features["diff_488_555"] = rrs["Rrs_488"] - rrs["Rrs_555"]
    if rrs["Rrs_555"] is not None and rrs["Rrs_645"] is not None:
        features["diff_555_645"] = rrs["Rrs_555"] - rrs["Rrs_645"]

    # Band sums
    if rrs["Rrs_443"] is not None and rrs["Rrs_488"] is not None:
        features["sum_443_488"] = rrs["Rrs_443"] + rrs["Rrs_488"]
    if rrs["Rrs_555"] is not None and rrs["Rrs_645"] is not None:
        features["sum_555_645"] = rrs["Rrs_555"] + rrs["Rrs_645"]

    # Triple combinations
    if all(rrs[k] is not None for k in ["Rrs_443", "Rrs_488", "Rrs_555"]):
        features["tri_443_488_555"] = rrs["Rrs_443"] - rrs["Rrs_488"] + rrs["Rrs_555"]
    if all(rrs[k] is not None for k in ["Rrs_488", "Rrs_555", "Rrs_645"]):
        features["tri_488_555_645"] = rrs["Rrs_488"] - rrs["Rrs_555"] + rrs["Rrs_645"]

    # Water-quality indices
    if rrs["Rrs_555"] is not None and rrs["Rrs_645"] is not None:
        denom = rrs["Rrs_555"] + rrs["Rrs_645"] + eps
        features["ndci"] = (rrs["Rrs_645"] - rrs["Rrs_555"]) / denom
        features["brr_red_green"] = rrs["Rrs_645"] / (rrs["Rrs_555"] + eps)

    if rrs["Rrs_555"] is not None and rrs["Rrs_678"] is not None:
        denom = rrs["Rrs_555"] + rrs["Rrs_678"] + eps
        features["ndci_678"] = (rrs["Rrs_678"] - rrs["Rrs_555"]) / denom

    if rrs["Rrs_443"] is not None and rrs["Rrs_555"] is not None:
        features["ci_green"] = rrs["Rrs_555"] - rrs["Rrs_443"]

    if rrs["Rrs_645"] is not None and rrs["Rrs_678"] is not None:
        features["ci_rededge"] = rrs["Rrs_678"] - rrs["Rrs_645"]

    if all(rrs[k] is not None for k in ["Rrs_443", "Rrs_488", "Rrs_555"]):
        denom = rrs["Rrs_443"] + rrs["Rrs_488"] + eps
        features["brr_green_blue"] = rrs["Rrs_555"] / denom

    feature_names = list(features.keys())
    return features, feature_names


# ============================================================
# 模型管理
# ============================================================

def build_model_pipeline(model_name: str = "RF", n_features: int = 26) -> Pipeline:
    """
    构建模型 Pipeline（与 train.py 保持一致）。

    Parameters
    ----------
    model_name : str
        模型名称：RF, ET, XGB, LGB, MLR, GP
    n_features : int
        特征数量（用于 PCA n_components 上限）

    Returns
    -------
    Pipeline
    """
    pca_n = min(16, n_features)

    configs = {
        "MLR": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=pca_n)),
            ("model", LinearRegression())
        ]),
        "RF": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=pca_n)),
            ("model", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=2))
        ]),
        "GP": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=pca_n)),
            ("model", GaussianProcessRegressor(
                kernel=C(1.0) * RBF(length_scale=1.0),
                alpha=0.1, normalize_y=True, random_state=42
            ))
        ]),
        "ET": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=pca_n)),
            ("model", ExtraTreesRegressor(n_estimators=200, random_state=42, n_jobs=2))
        ]),
    }

    if HAS_LGB and model_name == "LGB":
        configs["LGB"] = Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=pca_n)),
            ("model", LGBMRegressor(
                n_estimators=300, max_depth=4, learning_rate=0.05,
                subsample=0.9, colsample_bytree=0.9,
                random_state=42, n_jobs=2, verbosity=-1
            ))
        ])
        return configs["LGB"]

    if HAS_XGB and model_name == "XGB":
        configs["XGB"] = Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=pca_n)),
            ("model", XGBRegressor(
                n_estimators=300, max_depth=4, learning_rate=0.05,
                subsample=0.9, colsample_bytree=0.9,
                random_state=42, n_jobs=2
            ))
        ])
        return configs["XGB"]

    if model_name in configs:
        return configs[model_name]

    # 默认 RF
    return configs["RF"]


def train_chla_model(
    df: pd.DataFrame,
    model_name: str = "RF",
    save_path: Optional[Path] = None
) -> Tuple[Pipeline, List[str]]:
    """
    用样本数据训练 Chl-a 模型。

    Parameters
    ----------
    df : pd.DataFrame
        训练数据，含 Rrs 波段特征和 chl_a 列
    model_name : str
        模型名称
    save_path : Path, optional
        模型保存路径

    Returns
    -------
    tuple
        (训练好的 Pipeline, 特征名列表)
    """
    feature_cols = [c for c in df.columns if c != "chl_a"]
    X = df[feature_cols]
    y = df["chl_a"]

    pipeline = build_model_pipeline(model_name, len(feature_cols))
    pipeline.fit(X, y)

    if save_path:
        import pickle
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            pickle.dump({"pipeline": pipeline, "feature_cols": feature_cols}, f)

    return pipeline, feature_cols


def load_chla_model(model_path: Path) -> Tuple[Pipeline, List[str]]:
    """加载已保存的 Chl-a 模型。"""
    import pickle
    with open(model_path, "rb") as f:
        data = pickle.load(f)
    return data["pipeline"], data["feature_cols"]


# ============================================================
# 核心预测函数
# ============================================================

def predict_chla_map(
    rrs_bands: Dict[str, np.ndarray],
    model: Pipeline,
    feature_cols: List[str],
    qa_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    从 Rrs 波段批量预测 Chl-a 浓度图。

    Parameters
    ----------
    rrs_bands : dict
        Rrs 波段字典，每个值为 2D 数组 (H, W)
    model : Pipeline
        训练好的 sklearn Pipeline
    feature_cols : list
        特征名列表（与模型训练时的顺序一致）
    qa_mask : np.ndarray, optional
        质量掩膜 2D 数组 (H, W)，True=有效像元

    Returns
    -------
    np.ndarray
        Chl-a 浓度 2D 数组 (H, W)，无效区域为 NaN
    """
    h, w = list(rrs_bands.values())[0].shape[:2]
    n = h * w

    # 先从原始 Rrs 波段计算所有派生特征
    derived_features, _ = compute_rrs_features(rrs_bands)

    # 合并原始波段 + 派生特征
    all_features = {**rrs_bands, **derived_features}

    n_features = len(feature_cols)
    X = np.full((n, n_features), np.nan, dtype=np.float32)
    valid = np.ones(n, dtype=bool)

    for i, col in enumerate(feature_cols):
        arr = all_features.get(col)
        if arr is None:
            X[:, i] = 0.0
            continue
        flat = np.asarray(arr, dtype=np.float32).ravel()
        X[:, i] = flat
        # Rrs 波段物理上必须为正；派生特征可以为负（如 NDCI 可以是负值）
        if col.startswith("Rrs_"):
            valid = valid & np.isfinite(flat) & (flat > 0)
        else:
            valid = valid & np.isfinite(flat)

    # QA 掩膜
    if qa_mask is not None and valid.any():
        qa = np.asarray(qa_mask, dtype=np.float32).ravel()
        if qa.shape[0] == n:
            valid = valid & (qa <= 1)

    if not np.any(valid):
        return np.full((h, w), np.nan, dtype=np.float32)

    X_valid = X[valid]
    # 转为 DataFrame 以保留特征名，避免 sklearn 警告
    import pandas as pd
    X_df = pd.DataFrame(X_valid, columns=feature_cols)
    chl_pred = model.predict(X_df).astype(np.float32)
    chl_pred = np.clip(chl_pred, 0.01, 50.0)
    chl_pred = np.where(np.isfinite(chl_pred), chl_pred, np.nan)

    result = np.full(n, np.nan, dtype=np.float32)
    result[valid] = chl_pred
    return result.reshape(h, w)


def save_chla_tiff(
    chl_a: np.ndarray,
    lon: np.ndarray,
    lat: np.ndarray,
    output_path: Path,
    transform: Optional = None,
    crs: str = "EPSG:4326",
) -> Dict:
    """
    将 Chl-a 数组保存为 GeoTIFF（含地理坐标）。

    Parameters
    ----------
    chl_a : np.ndarray
        Chl-a 2D 数组 (H, W)
    lon : np.ndarray
        经度 2D 数组 (H, W)
    lat : np.ndarray
        纬度 2D 数组 (H, W)
    output_path : Path
        输出文件路径
    transform : rasterio.transform, optional
        地理变换（如果已有）
    crs : str
        坐标系，默认 WGS84

    Returns
    -------
    dict
        输出元数据
    """
    if not RASTERIO_AVAILABLE:
        if TIFFILE_AVAILABLE:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            tifffile.imwrite(output_path, chl_a.astype(np.float32))
            return {"path": str(output_path), "warning": "无 rasterio，仅保存原始数组"}
        raise ImportError("tifffile 和 rasterio 均不可用")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    h, w = chl_a.shape

    # 从经纬度角点计算仿射变换
    if transform is None:
        lon_corners = [lon[0, 0], lon[0, -1], lon[-1, -1], lon[-1, 0]]
        lat_corners = [lat[0, 0], lat[0, -1], lat[-1, -1], lat[-1, 0]]
        lon_min = min(lon_corners)
        lon_max = max(lon_corners)
        lat_min = min(lat_corners)
        lat_max = max(lat_corners)
        transform = from_bounds(lon_min, lat_min, lon_max, lat_max, w, h)

    metadata = {
        "driver": "GTiff",
        "height": h,
        "width": w,
        "count": 1,
        "dtype": str(chl_a.dtype),
        "crs": crs,
        "transform": transform,
        "nodata": -9999.0,
    }

    with rasterio.open(output_path, "w", **metadata) as dst:
        chl_f = chl_a.astype(np.float32)
        chl_f = np.where(np.isnan(chl_f), -9999.0, chl_f)
        dst.write(chl_f, 1)

    return {
        "path": str(output_path),
        "shape": (h, w),
        "transform": str(transform),
        "crs": crs,
        "nodata": -9999,
    }


def save_chla_preview_png(
    chl_a: np.ndarray,
    output_path: Path,
    cmap: str = "viridis",
    vmin: float = 0.0,
    vmax: float = 15.0,
) -> str:
    """
    保存 Chl-a 分布图为 PNG 预览图。

    Parameters
    ----------
    chl_a : np.ndarray
        Chl-a 2D 数组
    output_path : Path
        输出路径 (.png)
    cmap : str
        色带名称
    vmin, vmax : float
        色彩映射范围

    Returns
    -------
    str
        保存路径
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
    except ImportError:
        warnings.warn("matplotlib 不可用，跳过预览图生成")
        return ""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    masked = np.ma.masked_invalid(chl_a)

    im = ax.imshow(masked, cmap=cmap, vmin=vmin, vmax=vmax, origin="upper")
    ax.set_title("Chl-a Distribution (mg/m3)", fontsize=14)
    ax.set_xlabel("Column Index", fontsize=11)
    ax.set_ylabel("Row Index", fontsize=11)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Chl-a (mg/m3)", fontsize=12)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return str(output_path)


def generate_chla_statistics(chl_a: np.ndarray) -> Dict:
    """
    生成 Chl-a 分布图的统计信息。

    Parameters
    ----------
    chl_a : np.ndarray
        Chl-a 2D 数组

    Returns
    -------
    dict
        统计结果
    """
    valid = chl_a[~np.isnan(chl_a) & (chl_a > 0)]
    if len(valid) == 0:
        return {"error": "没有有效像元"}

    return {
        "mean": round(float(np.nanmean(chl_a)), 4),
        "median": round(float(np.nanmedian(chl_a)), 4),
        "std": round(float(np.nanstd(chl_a)), 4),
        "min": round(float(np.nanmin(chl_a)), 4),
        "max": round(float(np.nanmax(chl_a)), 4),
        "p25": round(float(np.nanpercentile(chl_a, 25)), 4),
        "p75": round(float(np.nanpercentile(chl_a, 75)), 4),
        "valid_pixels": int(len(valid)),
        "total_pixels": int(chl_a.size),
        "coverage": round(float(len(valid) / chl_a.size * 100), 2),
    }


# ============================================================
# 端到端主函数
# ============================================================

def retrieve_chla(
    modis_data: Dict,
    model: Pipeline,
    feature_cols: List[str],
    qa_max: int = 1,
    output_name: str = "chla_retrieval",
    save_tiff: bool = True,
    save_preview: bool = True,
) -> Dict:
    """
    端到端 Chl-a 反演主函数。

    Parameters
    ----------
    modis_data : dict
        MODIS L2 数据（由 modis_l2_reader.read_all() 返回）
    model : Pipeline
        训练好的模型 Pipeline
    feature_cols : list
        特征名列表
    qa_max : int
        最大 QA 值（质量过滤）
    output_name : str
        输出文件名前缀
    save_tiff : bool
        是否保存 GeoTIFF
    save_preview : bool
        是否保存预览 PNG

    Returns
    -------
    dict
        反演结果，包含统计信息、输出路径等
    """
    rrs_bands = modis_data.get("rrs_bands", {})
    if not rrs_bands:
        raise ValueError("MODIS 数据中未找到 Rrs 波段")

    h, w = list(rrs_bands.values())[0].shape[:2]

    # QA 掩膜
    qa_mask = None
    if modis_data.get("qa") is not None and qa_max is not None:
        qa = modis_data["qa"]
        qa_mask = qa <= qa_max

    # 预测 Chl-a 图
    print(f"[Chl-a 预测] 影像尺寸: {h}x{w}, 有效像元约 {int(h*w*0.7)} 个")
    chl_a = predict_chla_map(rrs_bands, model, feature_cols, qa_mask)

    # 统计
    stats = generate_chla_statistics(chl_a)
    print(f"[Chl-a 统计] 均值={stats['mean']}, 最大={stats['max']}, "
          f"有效像元={stats['valid_pixels']}/{stats['total_pixels']} ({stats['coverage']}%)")

    result = {
        "chl_a_shape": chl_a.shape,
        "statistics": stats,
        "output_files": {},
    }

    # 保存 GeoTIFF
    if save_tiff and modis_data.get("lon") is not None and modis_data.get("lat") is not None:
        tiff_path = MAPS_DIR / f"{output_name}.tif"
        tiff_meta = save_chla_tiff(
            chl_a,
            modis_data["lon"],
            modis_data["lat"],
            tiff_path,
        )
        result["output_files"]["tiff"] = tiff_meta
        print(f"[输出] Chl-a GeoTIFF 已保存: {tiff_path}")

    # 保存预览图
    if save_preview:
        png_path = MAPS_DIR / f"{output_name}_preview.png"
        vmax = min(stats["p75"] * 1.5, stats["max"])
        png_saved = save_chla_preview_png(chl_a, png_path, vmax=vmax)
        if png_saved:
            result["output_files"]["preview"] = png_saved
            print(f"[输出] 预览图已保存: {png_path}")

    result["success"] = True
    return result


def auto_train_from_samples(
    model_name: str = "RF",
    n_samples: int = 1000,
    seed: int = 42,
) -> Tuple[Pipeline, List[str]]:
    """
    自动从合成样本训练模型（用于演示/测试）。

    真实使用时替换为：train_chla_model(df_with_real_insitu_data, ...)

    Parameters
    ----------
    model_name : str
        模型名称
    n_samples : int
        合成样本数量
    seed : int
        随机种子

    Returns
    -------
    tuple
        (模型 Pipeline, 特征名列表)
    """
    from src.preprocess import generate_mock_samples

    print(f"\n[训练] 开始: {model_name} 模型")
    print(f"[训练] 生成 {n_samples} 个合成样本...")

    # Show generation progress (generate in chunks for visual feedback)
    chunk_size = max(n_samples // 20, 1)
    for i in tqdm(range(0, n_samples, chunk_size), desc="  生成样本", leave=False,
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}"):
        pass  # generation is fast; just animate

    df = generate_mock_samples(n_samples=n_samples, seed=seed)

    print(f"[训练] 样本生成完毕，特征数: {df.shape[1]-1}")
    print(f"[训练] 开始训练模型...")

    model, feature_cols = train_chla_model(df, model_name=model_name)

    print(f"[训练] 完成! 特征数: {len(feature_cols)}")
    print()

    return model, feature_cols
