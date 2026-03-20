"""
GeoTIFF 格式 MODIS L2 数据读取模块。

将标准 GeoTIFF 格式的 MODIS L2 数据转换为 chla_predictor 模块可用的格式。

支持的波段：
    - Band 1  : Rrs_412
    - Band 2  : Rrs_443
    - Band 3  : Rrs_469
    - Band 4  : Rrs_488
    - Band 5  : Rrs_531
    - Band 6  : Rrs_547
    - Band 7  : Rrs_555
    - Band 8  : Rrs_645
    - Band 9  : Rrs_667
    - Band 10 : Rrs_678
    - Band 11 : QA (质量标志)
    - Band 12 : Lon (经度)
    - Band 13 : Lat (纬度)
"""

from pathlib import Path
from typing import Dict, Optional
import numpy as np

try:
    import rasterio
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

# 标准波段映射
BAND_MAPPING = {
    1: "Rrs_412",
    2: "Rrs_443",
    3: "Rrs_469",
    4: "Rrs_488",
    5: "Rrs_531",
    6: "Rrs_547",
    7: "Rrs_555",
    8: "Rrs_645",
    9: "Rrs_667",
    10: "Rrs_678",
    11: "qa",
    12: "lon",
    13: "lat",
}


def read_geotiff_as_modis_data(
    file_path: Path,
    qa_max: float = 1.0,
) -> Dict:
    """
    读取 GeoTIFF 格式的 MODIS L2 数据，返回标准化格式。

    Parameters
    ----------
    file_path : Path
        GeoTIFF 文件路径
    qa_max : float
        最大允许的 QA 值（小于等于此值的像元被视为有效）

    Returns
    -------
    dict
        包含以下键：
        - rrs_bands: dict[str, np.ndarray]  Rrs 波段数据 (H, W)
        - lon: np.ndarray  经度网格 (H, W)
        - lat: np.ndarray  纬度网格 (H, W)
        - qa: np.ndarray or None  质量标志 (H, W)
        - shape: tuple  影像尺寸 (H, W)
        - bands_found: list  成功读取的波段列表
        - warnings: list  警告信息

    Raises
    ------
    ImportError
        如果 rasterio 不可用
    FileNotFoundError
        如果文件不存在
    ValueError
        如果文件格式不符合预期
    """
    if not RASTERIO_AVAILABLE:
        raise ImportError("rasterio 库不可用，请运行: pip install rasterio")

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    result = {
        "file_path": str(file_path),
        "file_format": "geotiff",
        "rrs_bands": {},
        "lon": None,
        "lat": None,
        "qa": None,
        "metadata": {},
        "shape": None,
        "bands_found": [],
        "warnings": [],
    }

    with rasterio.open(file_path) as src:
        n_bands = src.count
        result["shape"] = (src.height, src.width)

        # 读取经纬度（通常在最后几个波段）
        for band_idx in [n_bands - 1, n_bands - 2]:
            if band_idx < 1:
                continue
            band_name = BAND_MAPPING.get(band_idx + 1, f"band_{band_idx + 1}")
            data = src.read(band_idx + 1)
            data = np.array(data, dtype=np.float32)

            if band_name == "lon":
                result["lon"] = data
            elif band_name == "lat":
                result["lat"] = data

        # 如果没找到经纬度，尝试从元数据构建
        if result["lon"] is None or result["lat"] is None:
            try:
                bounds = src.bounds
                transform = src.transform
                h, w = src.height, src.width

                # 从仿射变换计算经纬度
                lon_min, lat_max = rasterio.transform.xy(transform, 0, 0)
                lon_max, lat_min = rasterio.transform.xy(transform, h - 1, w - 1)

                col_coords = np.linspace(lon_min, lon_max, w)
                row_coords = np.linspace(lat_max, lat_min, h)

                lon_grid, lat_grid = np.meshgrid(col_coords, row_coords)
                result["lon"] = lon_grid.astype(np.float32)
                result["lat"] = lat_grid.astype(np.float32)
                result["warnings"].append("经纬度由GeoTIFF变换参数计算得出")
            except Exception as e:
                result["warnings"].append(f"无法获取经纬度: {e}")

        # 读取 Rrs 波段
        for i in range(1, min(n_bands + 1, 11)):
            band_name = BAND_MAPPING.get(i)
            if band_name is None:
                continue

            data = src.read(i)
            data = np.array(data, dtype=np.float32)

            # 处理 nodata 值
            if src.nodata is not None:
                data = np.where(data == src.nodata, np.nan, data)

            # 处理常见的无效值
            data = np.where(data < 0, np.nan, data)
            data = np.where(data > 10, np.nan, data)  # Rrs 不应大于 10

            result["rrs_bands"][band_name] = data
            result["bands_found"].append(band_name)

        # 读取 QA 波段
        if n_bands >= 11:
            qa_band_idx = 10  # Band 11
            qa_data = src.read(qa_band_idx)
            qa_data = np.array(qa_data, dtype=np.float32)
            if src.nodata is not None:
                qa_data = np.where(qa_data == src.nodata, np.nan, qa_data)
            result["qa"] = qa_data

    result["n_bands_found"] = len(result["bands_found"])

    # 质量过滤
    if result["qa"] is not None and qa_max is not None:
        from src.modis_l2_reader import filter_by_qa
        result = filter_by_qa(result, qa_max)

    return result


def validate_geotiff_format(file_path: Path) -> Dict:
    """
    验证 GeoTIFF 文件是否符合 MODIS L2 标准格式。

    Parameters
    ----------
    file_path : Path
        GeoTIFF 文件路径

    Returns
    -------
    dict
        验证结果，包含：
        - valid: bool  是否有效
        - n_bands: int  波段数
        - has_rrs: bool  是否包含 Rrs 波段
        - has_geo: bool  是否包含地理坐标
        - warnings: list  警告信息
        - suggestions: list  建议信息
    """
    if not RASTERIO_AVAILABLE:
        return {
            "valid": False,
            "error": "rasterio 不可用",
        }

    file_path = Path(file_path)
    if not file_path.exists():
        return {
            "valid": False,
            "error": f"文件不存在: {file_path}",
        }

    warnings = []
    suggestions = []

    try:
        with rasterio.open(file_path) as src:
            n_bands = src.count
            has_geo = src.crs is not None and src.transform is not None
            has_rrs = n_bands >= 10

            if not has_geo:
                warnings.append("文件缺少地理坐标信息（CRS/Transform）")
                suggestions.append("建议使用包含地理坐标的 GeoTIFF 文件")

            if n_bands < 10:
                warnings.append(f"波段数不足（{n_bands} < 10），可能缺少部分 Rrs 波段")
                suggestions.append(f"标准 MODIS L2 应包含至少 10 个 Rrs 波段")

            # 检查 nodata 设置
            if src.nodata is None:
                warnings.append("文件未设置 nodata 值")
                suggestions.append("建议设置 nodata 值以便正确识别无效像元")

            return {
                "valid": has_rrs and n_bands >= 10,
                "satellite_type": "MODIS L2 (GeoTIFF)" if has_rrs else "Unknown",
                "n_bands": n_bands,
                "has_rrs": has_rrs,
                "has_geo": has_geo,
                "crs": str(src.crs) if src.crs else None,
                "bounds": src.bounds if has_geo else None,
                "nodata": src.nodata,
                "warnings": warnings,
                "suggestions": suggestions,
                "errors": [],
            }

    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "warnings": [],
            "suggestions": ["请确保文件是有效的 GeoTIFF 格式"],
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python geotiff_modis_reader.py <GeoTIFF文件路径>")
        sys.exit(1)

    tiff_path = Path(sys.argv[1])
    print(f"验证文件: {tiff_path}")
    print("=" * 60)

    # 验证格式
    validation = validate_geotiff_format(tiff_path)
    print(f"验证结果: {'✓ 通过' if validation.get('valid') else '✗ 失败'}")
    print(f"卫星类型: {validation.get('satellite_type', 'Unknown')}")
    print(f"波段数量: {validation.get('n_bands', 0)}")
    print(f"地理坐标: {'✓ 有' if validation.get('has_geo') else '✗ 无'}")

    if validation.get("warnings"):
        print("\n警告:")
        for w in validation["warnings"]:
            print(f"  - {w}")

    if validation.get("suggestions"):
        print("\n建议:")
        for s in validation["suggestions"]:
            print(f"  - {s}")

    # 读取数据
    print("\n" + "=" * 60)
    print("读取数据...")
    data = read_geotiff_as_modis_data(tiff_path)
    print(f"Rrs 波段: {data['bands_found']}")
    print(f"影像尺寸: {data['shape']}")
    print(f"经度范围: {float(data['lon'].min()):.4f}° ~ {float(data['lon'].max()):.4f}°")
    print(f"纬度范围: {float(data['lat'].min()):.4f}° ~ {float(data['lat'].max()):.4f}°")

    if data.get("qa") is not None:
        qa_valid = np.sum(data["qa"] <= 1)
        qa_total = data["qa"].size
        print(f"有效像元: {qa_valid}/{qa_total} ({100*qa_valid/qa_total:.1f}%)")
