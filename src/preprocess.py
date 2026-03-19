"""
Data preprocessing module for chlorophyll-a sample generation and feature engineering.

Functions:
    generate_mock_samples: Generate synthetic Rrs and Chl-a samples with realistic relationships
    generate_training_data_from_modis: Generate training data from MODIS L2 imagery
    compute_features_from_rrs: Compute all features (bands + derived) from Rrs dict
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLES_DIR = BASE_DIR / "data" / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def generate_mock_samples(n_samples: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic Rrs and Chl-a samples with physically realistic relationships.

    The Chl-a generation formula is based on the OC3-type band-ratio approach
    commonly used in ocean color algorithms (Hu et al., 2012):
      log10(Chl-a) = a0 + a1*X + a2*X^2 + a3*X^3 + a4*X^4
      where X = log10(max(Rrs_443, Rrs_488) / Rrs_555)

    Parameters
    ----------
    n_samples : int, optional
        Number of samples to generate. Default is 1000.
    seed : int, optional
        Random seed for reproducibility. Default is 42.

    Returns
    -------
    pd.DataFrame
        DataFrame containing Rrs bands, derived features, and Chl-a values.
        Columns include:
        - Rrs bands: Rrs_412, Rrs_443, Rrs_469, Rrs_488, Rrs_531, Rrs_547,
                    Rrs_555, Rrs_645, Rrs_667, Rrs_678
        - Ratio features: ratio_443_555, ratio_488_555, ratio_531_547, ratio_443_488
        - Difference features: diff_488_555, diff_555_645
        - Sum features: sum_443_488, sum_555_645
        - Triple features: tri_443_488_555, tri_488_555_645
        - Water-quality indices: ndci, ndci_678, ci_green, ci_rededge, brr_green_blue, brr_red_green
        - Target: chl_a (mg/m³)
    """
    rng = np.random.default_rng(seed)

    # Generate Rrs with realistic ranges for coastal waters
    # Low-Chl-a (oligotrophic): Rrs values lower
    # High-Chl-a (eutrophic): Rrs values higher, especially green and red
    n = n_samples
    log_chl = rng.uniform(-1.3, 1.2, n)  # log10(Chl-a) in range 0.05 - 16 mg/m³
    chl_true = 10 ** log_chl

    # Generate Rrs values correlated with Chl-a
    # Blue bands decrease with Chl-a, green/red increase
    blue_scale = np.exp(-0.3 * log_chl)  # higher Chl-a -> lower blue
    green_scale = np.power(chl_true / 3.0, 0.4)  # higher Chl-a -> higher green
    red_scale = np.power(chl_true / 5.0, 0.6)  # stronger response in red band

    data = pd.DataFrame({
        "Rrs_412": rng.uniform(0.001, 0.020, n) * blue_scale + rng.uniform(0.0, 0.003, n),
        "Rrs_443": rng.uniform(0.002, 0.022, n) * blue_scale + rng.uniform(0.0, 0.004, n),
        "Rrs_469": rng.uniform(0.003, 0.025, n) * blue_scale + rng.uniform(0.0, 0.005, n),
        "Rrs_488": rng.uniform(0.003, 0.030, n) * blue_scale * 1.1 + rng.uniform(0.0, 0.006, n),
        "Rrs_531": rng.uniform(0.004, 0.028, n) * green_scale * 0.8 + rng.uniform(0.0, 0.005, n),
        "Rrs_547": rng.uniform(0.005, 0.030, n) * green_scale * 0.9 + rng.uniform(0.0, 0.005, n),
        "Rrs_555": rng.uniform(0.005, 0.032, n) * green_scale * 1.0 + rng.uniform(0.0, 0.006, n),
        "Rrs_645": rng.uniform(0.002, 0.020, n) * red_scale * 1.2 + rng.uniform(0.0, 0.003, n),
        "Rrs_667": rng.uniform(0.001, 0.015, n) * red_scale * 1.5 + rng.uniform(0.0, 0.002, n),
        "Rrs_678": rng.uniform(0.001, 0.012, n) * red_scale * 1.8 + rng.uniform(0.0, 0.002, n),
    })

    # Ensure physically plausible ranges
    for col in data.columns:
        data[col] = data[col].clip(lower=0.0001)

    eps = 1e-6

    # Band ratios
    data["ratio_443_555"] = data["Rrs_443"] / (data["Rrs_555"] + eps)
    data["ratio_488_555"] = data["Rrs_488"] / (data["Rrs_555"] + eps)
    data["ratio_531_547"] = data["Rrs_531"] / (data["Rrs_547"] + eps)
    data["ratio_443_488"] = data["Rrs_443"] / (data["Rrs_488"] + eps)

    # Band differences
    data["diff_488_555"] = data["Rrs_488"] - data["Rrs_555"]
    data["diff_555_645"] = data["Rrs_555"] - data["Rrs_645"]

    # Band sums
    data["sum_443_488"] = data["Rrs_443"] + data["Rrs_488"]
    data["sum_555_645"] = data["Rrs_555"] + data["Rrs_645"]

    # Triple combinations
    data["tri_443_488_555"] = data["Rrs_443"] - data["Rrs_488"] + data["Rrs_555"]
    data["tri_488_555_645"] = data["Rrs_488"] - data["Rrs_555"] + data["Rrs_645"]

    # Water-quality indices
    data["ndci"] = (data["Rrs_645"] - data["Rrs_555"]) / (data["Rrs_645"] + data["Rrs_555"] + eps)
    data["ndci_678"] = (data["Rrs_678"] - data["Rrs_555"]) / (data["Rrs_678"] + data["Rrs_555"] + eps)
    data["ci_green"] = data["Rrs_555"] - data["Rrs_443"]
    data["ci_rededge"] = data["Rrs_678"] - data["Rrs_645"]
    data["brr_green_blue"] = data["Rrs_555"] / (data["Rrs_443"] + data["Rrs_488"] + eps)
    data["brr_red_green"] = data["Rrs_645"] / (data["Rrs_555"] + eps)

    # Clip to physically plausible ranges
    for col in data.columns:
        if col == "chl_a":
            continue
        data[col] = data[col].clip(-10, 100)

    # Add realistic measurement noise to Chl-a
    # Noise scales with Chl-a level (higher Chl-a -> more variability)
    noise_std = 0.15 + 0.05 * log_chl  # 15-25% relative error
    noise = rng.normal(0, noise_std)
    data["chl_a"] = np.clip(chl_true * np.exp(noise), 0.05, 20.0)

    return data


def compute_features_from_rrs(
    rrs_bands: Dict[str, np.ndarray],
    sampling_rate: int = 1
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    从 Rrs 波段字典计算所有特征，兼容 raster_processor.py 的逻辑。

    Parameters
    ----------
    rrs_bands : dict
        Rrs 波段字典，键为 "Rrs_443" 等
    sampling_rate : int
        采样率，每隔 n 个像元取一个

    Returns
    -------
    tuple
        (特征 DataFrame, 有效像元掩膜 1D 数组)
    """
    eps = 1e-6
    h, w = list(rrs_bands.values())[0].shape[:2]

    # 构建有效像元掩膜（所有波段均非零/非NaN）
    mask = np.ones((h, w), dtype=bool)
    for band_name, band_data in rrs_bands.items():
        valid = ~(np.isnan(band_data) | np.isinf(band_data) | (band_data <= 0))
        mask = mask & valid

    # 展平
    rows_idx, cols_idx = np.where(mask)
    if len(rows_idx) == 0:
        return pd.DataFrame(), np.array([], dtype=bool)

    # 采样
    if sampling_rate > 1:
        idx = np.arange(0, len(rows_idx), sampling_rate)
        rows_idx = rows_idx[idx]
        cols_idx = cols_idx[idx]

    n = len(rows_idx)
    data = {"row": rows_idx, "col": cols_idx}

    # 读取 Rrs 波段
    for band_name, band_data in rrs_bands.items():
        data[band_name] = band_data[rows_idx, cols_idx]

    # 计算派生特征
    features = _compute_derived_features(data)
    data.update(features)

    df = pd.DataFrame(data)
    valid_mask_1d = np.ones(n, dtype=bool)

    return df, valid_mask_1d


def _compute_derived_features(data: Dict) -> Dict[str, np.ndarray]:
    """内部函数：从原始波段数据计算派生特征"""
    eps = 1e-6
    features = {}

    def safe(key):
        return data.get(key, None)

    rrs_keys = ["Rrs_412", "Rrs_443", "Rrs_469", "Rrs_488",
                "Rrs_531", "Rrs_547", "Rrs_555", "Rrs_645", "Rrs_667", "Rrs_678"]

    rrs = {k: safe(k) for k in rrs_keys}

    if rrs["Rrs_443"] is not None and rrs["Rrs_555"] is not None:
        features["ratio_443_555"] = rrs["Rrs_443"] / (rrs["Rrs_555"] + eps)
    if rrs["Rrs_488"] is not None and rrs["Rrs_555"] is not None:
        features["ratio_488_555"] = rrs["Rrs_488"] / (rrs["Rrs_555"] + eps)
    if rrs["Rrs_531"] is not None and rrs["Rrs_547"] is not None:
        features["ratio_531_547"] = rrs["Rrs_531"] / (rrs["Rrs_547"] + eps)
    if rrs["Rrs_443"] is not None and rrs["Rrs_488"] is not None:
        features["ratio_443_488"] = rrs["Rrs_443"] / (rrs["Rrs_488"] + eps)

    if rrs["Rrs_488"] is not None and rrs["Rrs_555"] is not None:
        features["diff_488_555"] = rrs["Rrs_488"] - rrs["Rrs_555"]
    if rrs["Rrs_555"] is not None and rrs["Rrs_645"] is not None:
        features["diff_555_645"] = rrs["Rrs_555"] - rrs["Rrs_645"]

    if rrs["Rrs_443"] is not None and rrs["Rrs_488"] is not None:
        features["sum_443_488"] = rrs["Rrs_443"] + rrs["Rrs_488"]
    if rrs["Rrs_555"] is not None and rrs["Rrs_645"] is not None:
        features["sum_555_645"] = rrs["Rrs_555"] + rrs["Rrs_645"]

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

    return features


def generate_training_data_from_modis(
    modis_data: Dict,
    sampling_rate: int = 100,
    qa_max: int = 1,
) -> pd.DataFrame:
    """
    从 MODIS L2 数据生成训练样本。

    该函数从 MODIS L2 影像中提取所有有效像元（按 QA 过滤后），
    计算特征，返回 DataFrame（不含 chl_a，因为这是预测目标）。

    实际使用时，应将返回的 DataFrame 与实测 Chl-a 数据
    按经纬度匹配后，再用于模型训练。

    Parameters
    ----------
    modis_data : dict
        modis_l2_reader.read_all() 返回的数据字典
    sampling_rate : int
        采样率，每隔 n 个有效像元取一个（默认100，避免太大）
    qa_max : int
        最大允许的 QA 值（0=best, 1=good）

    Returns
    -------
    pd.DataFrame
        特征 DataFrame（不含 chl_a 列）
    """
    rrs_bands = modis_data.get("rrs_bands", {})
    if not rrs_bands:
        raise ValueError("MODIS 数据中未找到 Rrs 波段")

    h, w = list(rrs_bands.values())[0].shape[:2]

    # 构建有效像元掩膜
    mask = np.ones((h, w), dtype=bool)
    for band_name, band_data in rrs_bands.items():
        valid = ~(np.isnan(band_data) | np.isinf(band_data) | (band_data <= 0))
        mask = mask & valid

    # QA 过滤
    if modis_data.get("qa") is not None and qa_max is not None:
        qa = modis_data["qa"]
        qa_valid = qa <= qa_max
        mask = mask & qa_valid

    rows_idx, cols_idx = np.where(mask)
    if len(rows_idx) == 0:
        raise ValueError("没有找到有效像元，请检查 QA 设置和区域范围")

    # 采样（避免数据量过大）
    if sampling_rate > 1 and len(rows_idx) > sampling_rate:
        idx = np.arange(0, len(rows_idx), sampling_rate)
        rows_idx = rows_idx[idx]
        cols_idx = cols_idx[idx]

    n = len(rows_idx)
    data = {
        "row": rows_idx,
        "col": cols_idx,
    }

    # 添加经纬度
    if modis_data.get("lon") is not None:
        data["lon"] = modis_data["lon"][rows_idx, cols_idx]
    if modis_data.get("lat") is not None:
        data["lat"] = modis_data["lat"][rows_idx, cols_idx]

    # 读取 Rrs 波段
    for band_name, band_data in rrs_bands.items():
        data[band_name] = band_data[rows_idx, cols_idx]

    # 计算派生特征
    features = _compute_derived_features(data)
    data.update(features)

    # 清理
    df = pd.DataFrame(data)
    df = df.drop(columns=["row", "col"], errors="ignore")
    df = df.dropna()

    return df


if __name__ == "__main__":
    print("生成烟台近岸海域合成训练样本...")
    df = generate_mock_samples(n_samples=1000, seed=42)
    output_path = SAMPLES_DIR / "mock_rrs_chla_samples.csv"
    df.to_csv(output_path, index=False)
    print(f"样本已保存至: {output_path}")
    print(f"样本数量: {len(df)}")
    print(f"Chl-a 范围: {df['chl_a'].min():.3f} ~ {df['chl_a'].max():.3f} mg/m³")
    print(f"Chl-a 均值: {df['chl_a'].mean():.3f} mg/m³")
    print("\n前5行:")
    print(df.head())
    print("\n列名:", list(df.columns))
