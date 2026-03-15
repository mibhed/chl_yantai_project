"""
TIFF影像处理模块 - 用于读取和处理卫星遥感影像

本模块提供TIFF影像的读取、波段提取、特征计算等功能，
支持MODIS、Sentinel-2等常见卫星数据的处理。

主要功能：
    - 读取多波段TIFF影像
    - 提取Rrs（遥感反射率）波段
    - 计算派生特征（比值、差值、组合等）
    - 数据标准化处理
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

try:
    import tifffile
    TIFFILE_AVAILABLE = True
except ImportError:
    TIFFILE_AVAILABLE = False

try:
    import rasterio
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# MODIS标准波段波长（nm）
MODIS_BANDS = {
    "Rrs_412": 413,
    "Rrs_443": 443,
    "Rrs_469": 469,
    "Rrs_488": 488,
    "Rrs_531": 531,
    "Rrs_547": 547,
    "Rrs_555": 555,
    "Rrs_645": 645,
    "Rrs_667": 667,
    "Rrs_678": 678,
}


def check_dependencies() -> bool:
    """检查必要的依赖库是否已安装"""
    if not TIFFILE_AVAILABLE:
        print("警告: tifffile库未安装，请运行: pip install tifffile")
        return False
    return True


def read_tiff(file_path: Union[str, Path]) -> Tuple[np.ndarray, Dict]:
    """
    读取TIFF影像文件和元数据

    Parameters
    ----------
    file_path : str or Path
        TIFF文件路径

    Returns
    -------
    tuple
        (影像数组, 元数据字典)
        影像数组shape: (bands, height, width) 或 (height, width)
        元数据包含: shape, dtype, nodata, crs, transform等

    Examples
    --------
    >>> img, meta = read_tiff("MODIS_2025_01.tif")
    >>> print(img.shape)
    (10, 500, 500)
    """
    if not check_dependencies():
        raise ImportError("tifffile库未安装")

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    img = tifffile.imread(file_path)
    meta = {
        "shape": img.shape,
        "dtype": str(img.dtype),
        "ndim": img.ndim,
    }

    if RASTERIO_AVAILABLE:
        try:
            with rasterio.open(file_path) as src:
                meta.update({
                    "nodata": src.nodata,
                    "crs": str(src.crs) if src.crs else None,
                    "transform": src.transform,
                    "bounds": src.bounds,
                    "res": src.res,
                })
        except Exception:
            pass

    return img, meta


def extract_rrs_bands(img: np.ndarray, band_mapping: Optional[Dict[str, int]] = None) -> Dict[str, np.ndarray]:
    """
    从影像中提取Rrs波段

    Parameters
    ----------
    img : np.ndarray
        影像数组，shape为 (bands, height, width) 或 (height, width, bands)
    band_mapping : dict, optional
        波段映射字典，格式: {"Rrs_443": 0, "Rrs_488": 1, ...}
        如果为None，则尝试自动识别

    Returns
    -------
    dict
        波段名称到数据的映射字典

    Examples
    --------
    >>> img, _ = read_tiff("modis.tif")
    >>> bands = extract_rrs_bands(img, {"Rrs_443": 0, "Rrs_488": 1})
    >>> print(bands.keys())
    dict_keys(['Rrs_443', 'Rrs_488'])
    """
    result = {}

    if band_mapping is None:
        band_mapping = {}

    if img.ndim == 3:
        n_bands = img.shape[0]
        if n_bands == len(MODIS_BANDS) and not band_mapping:
            band_mapping = {name: i for i, name in enumerate(MODIS_BANDS.keys())}
        elif n_bands <= 3 and not band_mapping:
            for i in range(n_bands):
                result[f"band_{i}"] = img[i]
                return result

    for band_name, band_idx in band_mapping.items():
        if band_idx < img.shape[0]:
            result[band_name] = img[band_idx]
        else:
            print(f"警告: 波段索引 {band_idx} 超出范围")

    return result


def calculate_derived_features(rrs_bands: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    根据Rrs波段计算派生特征

    Parameters
    ----------
    rrs_bands : dict
        Rrs波段字典，格式: {"Rrs_443": array, "Rrs_488": array, ...}

    Returns
    -------
    dict
        派生特征字典，包含：
        - 波段比值: ratio_443_555, ratio_488_555, ratio_531_547, ratio_443_488
        - 波段差值: diff_488_555, diff_555_645
        - 波段求和: sum_443_488, sum_555_645
        - 三波段组合: tri_443_488_555, tri_488_555_645

    Examples
    --------
    >>> bands = {"Rrs_443": arr, "Rrs_488": arr, "Rrs_555": arr}
    >>> features = calculate_derived_features(bands)
    >>> print(features.keys())
    dict_keys(['ratio_443_555', 'ratio_488_555', ...])
    """
    features = {}
    eps = 1e-6

    # 波段比值
    if "Rrs_443" in rrs_bands and "Rrs_555" in rrs_bands:
        features["ratio_443_555"] = rrs_bands["Rrs_443"] / (rrs_bands["Rrs_555"] + eps)

    if "Rrs_488" in rrs_bands and "Rrs_555" in rrs_bands:
        features["ratio_488_555"] = rrs_bands["Rrs_488"] / (rrs_bands["Rrs_555"] + eps)

    if "Rrs_531" in rrs_bands and "Rrs_547" in rrs_bands:
        features["ratio_531_547"] = rrs_bands["Rrs_531"] / (rrs_bands["Rrs_547"] + eps)

    if "Rrs_443" in rrs_bands and "Rrs_488" in rrs_bands:
        features["ratio_443_488"] = rrs_bands["Rrs_443"] / (rrs_bands["Rrs_488"] + eps)

    # 波段差值
    if "Rrs_488" in rrs_bands and "Rrs_555" in rrs_bands:
        features["diff_488_555"] = rrs_bands["Rrs_488"] - rrs_bands["Rrs_555"]

    if "Rrs_555" in rrs_bands and "Rrs_645" in rrs_bands:
        features["diff_555_645"] = rrs_bands["Rrs_555"] - rrs_bands["Rrs_645"]

    # 波段求和
    if "Rrs_443" in rrs_bands and "Rrs_488" in rrs_bands:
        features["sum_443_488"] = rrs_bands["Rrs_443"] + rrs_bands["Rrs_488"]

    if "Rrs_555" in rrs_bands and "Rrs_645" in rrs_bands:
        features["sum_555_645"] = rrs_bands["Rrs_555"] + rrs_bands["Rrs_645"]

    # 三波段组合
    if all(k in rrs_bands for k in ["Rrs_443", "Rrs_488", "Rrs_555"]):
        features["tri_443_488_555"] = (
            rrs_bands["Rrs_443"] - rrs_bands["Rrs_488"] + rrs_bands["Rrs_555"]
        )

    if all(k in rrs_bands for k in ["Rrs_488", "Rrs_555", "Rrs_645"]):
        features["tri_488_555_645"] = (
            rrs_bands["Rrs_488"] - rrs_bands["Rrs_555"] + rrs_bands["Rrs_645"]
        )

    return features


def extract_pixels_as_dataframe(
    img: np.ndarray,
    band_mapping: Optional[Dict[str, int]] = None,
    nodata_value: Optional[float] = None,
    sampling_rate: int = 1
) -> pd.DataFrame:
    """
    从影像中提取像元数据，转换为DataFrame格式

    该函数将影像中的有效像元提取为表格数据，
    便于后续的机器学习模型训练和验证。

    Parameters
    ----------
    img : np.ndarray
        影像数组
    band_mapping : dict, optional
        波段映射
    nodata_value : float, optional
        无效数据值，自动从元数据中读取
    sampling_rate : int, optional
        采样率，用于减少数据量。例如sampling_rate=10表示每10个像元取1个

    Returns
    -------
    pd.DataFrame
        包含所有波段和派生特征的DataFrame

    Examples
    --------
    >>> img, _ = read_tiff("modis.tif")
    >>> df = extract_pixels_as_dataframe(img, sampling_rate=10)
    >>> print(df.shape)
    (2500, 22)
    """
    rrs_bands = extract_rrs_bands(img, band_mapping)

    if not rrs_bands:
        raise ValueError("未能提取任何波段数据")

    height, width = img.shape[-2], img.shape[-1]
    rows, cols = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
    rows = rows.flatten()
    cols = cols.flatten()

    data = {"row": rows, "col": cols}

    for band_name, band_data in rrs_bands.flatten():
        data[band_name] = band_data.flatten()

    features = calculate_derived_features(rrs_bands)
    for feat_name, feat_data in features.items():
        data[feat_name] = feat_data.flatten()

    df = pd.DataFrame(data)

    if nodata_value is not None:
        mask = ~df.isin([nodata_value, np.nan, np.inf, -np.inf]).any(axis=1)
        df = df[mask]

    df = df.dropna()

    if sampling_rate > 1:
        df = df.iloc[::sampling_rate]

    return df.reset_index(drop=True)


def normalize_rrs_data(df: pd.DataFrame, method: str = "minmax") -> Tuple[pd.DataFrame, Dict]:
    """
    对Rrs数据进行标准化处理

    Parameters
    ----------
    df : pd.DataFrame
        输入数据
    method : str, optional
        标准化方法: "minmax", "zscore", 或 "robust"

    Returns
    -------
    tuple
        (标准化后的数据, 标准化参数字典)

    Examples
    --------
    >>> df = pd.DataFrame({"Rrs_443": [0.01, 0.02], "Rrs_555": [0.015, 0.025]})
    >>> df_norm, params = normalize_rrs_data(df, method="minmax")
    """
    from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler

    rrs_cols = [col for col in df.columns if col.startswith("Rrs_")]
    feature_cols = [col for col in df.columns if col not in ["row", "col", "chl_a"]]

    params = {"method": method}

    if method == "minmax":
        scaler = MinMaxScaler()
        params["feature_range"] = (0, 1)
    elif method == "zscore":
        scaler = StandardScaler()
        params["with_mean"] = True
        params["with_std"] = True
    elif method == "robust":
        scaler = RobustScaler()
    else:
        raise ValueError(f"不支持的标准化方法: {method}")

    df_norm = df.copy()

    if feature_cols:
        df_norm[feature_cols] = scaler.fit_transform(df[feature_cols])
        params["scalers"] = scaler

    return df_norm, params


def process_tiff_to_samples(
    file_path: Union[str, Path],
    band_mapping: Optional[Dict[str, int]] = None,
    nodata_value: Optional[float] = None,
    sampling_rate: int = 100,
    calculate_features: bool = True,
    normalize: bool = False
) -> pd.DataFrame:
    """
    完整的TIFF影像处理流程

    将TIFF影像转换为机器学习可用的样本数据，
    包含波段提取、特征计算、数据标准化等步骤。

    Parameters
    ----------
    file_path : str or Path
        TIFF文件路径
    band_mapping : dict, optional
        波段映射
    nodata_value : float, optional
        无效数据值
    sampling_rate : int, optional
        采样率，用于减少数据量
    calculate_features : bool, optional
        是否计算派生特征
    normalize : bool, optional
        是否进行数据标准化

    Returns
    -------
    pd.DataFrame
        处理后的样本数据

    Examples
    --------
    >>> df = process_tiff_to_samples("modis.tif", sampling_rate=50)
    >>> print(df.shape)
    (100, 22)
    """
    print(f"正在读取影像: {file_path}")
    img, meta = read_tiff(file_path)
    print(f"影像shape: {meta['shape']}, dtype: {meta['dtype']}")

    if img.ndim == 2:
        img = img[np.newaxis, :]

    print("正在提取波段数据...")
    rrs_bands = extract_rrs_bands(img, band_mapping)
    print(f"提取到 {len(rrs_bands)} 个波段: {list(rrs_bands.keys())}")

    data = {}
    for band_name, band_data in rrs_bands.items():
        flat_data = band_data.flatten()
        if nodata_value is not None:
            flat_data = flat_data[flat_data != nodata_value]
            flat_data = flat_data[~np.isnan(flat_data)]
            flat_data = flat_data[~np.isinf(flat_data)]
        data[band_name] = flat_data

    if calculate_features:
        print("正在计算派生特征...")
        features = calculate_derived_features(rrs_bands)
        for feat_name, feat_data in features.items():
            flat_data = feat_data.flatten()
            if nodata_value is not None:
                flat_data = flat_data[flat_data != nodata_value]
                flat_data = flat_data[~np.isnan(flat_data)]
                flat_data = flat_data[~np.isinf(flat_data)]
            data[feat_name] = flat_data

    min_len = min(len(v) for v in data.values())
    for key in data:
        data[key] = data[key][:min_len]

    df = pd.DataFrame(data)
    print(f"原始像元数量: {len(df)}")

    if sampling_rate > 1:
        df = df.iloc[::sampling_rate].reset_index(drop=True)
        print(f"采样后像元数量: {len(df)}")

    if normalize:
        print("正在标准化数据...")
        df, _ = normalize_rrs_data(df)

    print("处理完成!")
    return df


def save_processed_samples(df: pd.DataFrame, output_name: str) -> Path:
    """
    保存处理后的样本数据

    Parameters
    ----------
    df : pd.DataFrame
        样本数据
    output_name : str
        输出文件名（不含扩展名）

    Returns
    -------
    Path
        保存的文件路径
    """
    output_path = PROCESSED_DIR / f"{output_name}.csv"
    df.to_csv(output_path, index=False)
    print(f"数据已保存至: {output_path}")
    return output_path


if __name__ == "__main__":
    print("TIFF影像处理模块测试")
    print("=" * 50)

    if not check_dependencies():
        print("请安装必要的依赖库: pip install tifffile rasterio")
    else:
        print("依赖库检查通过")
        print(f"处理后数据保存目录: {PROCESSED_DIR}")
        print("\n使用方法:")
        print("1. process_tiff_to_samples('path/to/image.tif') - 完整处理流程")
        print("2. read_tiff('path/to/image.tif') - 仅读取影像")
        print("3. extract_rrs_bands(img, band_mapping) - 提取波段")
        print("4. calculate_derived_features(rrs_bands) - 计算派生特征")
