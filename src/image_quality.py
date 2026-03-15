"""
影像数据质量检查模块

本模块专门用于检查卫星遥感影像的质量，
包括影像完整性、波段有效性、异常值检测等功能。

主要功能：
    - 影像元数据检查
    - 波段数据有效性验证
    - 异常值检测与标记
    - 生成质量报告
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import io

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


class ImageQualityResult:
    """影像质量检查结果容器"""
    
    def __init__(self):
        self.passed = True
        self.warnings = []
        self.errors = []
        self.stats = {}
        self.details = {}
    
    def add_warning(self, message: str, category: str = "general"):
        self.warnings.append({"category": category, "message": message})
    
    def add_error(self, message: str, category: str = "general"):
        self.errors.append({"category": category, "message": message})
        self.passed = False
    
    def add_stat(self, key: str, value):
        self.stats[key] = value
    
    def add_detail(self, key: str, value):
        self.details[key] = value
    
    def get_summary(self) -> Dict:
        return {
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors,
            "stats": self.stats,
            "details": self.details
        }


def check_tiff_metadata(file_path: Union[str, Path]) -> ImageQualityResult:
    """
    检查TIFF影像元数据
    
    Parameters
    ----------
    file_path : str or Path
        TIFF文件路径
        
    Returns
    -------
    ImageQualityResult
        质量检查结果
    """
    result = ImageQualityResult()
    
    if not TIFFILE_AVAILABLE:
        result.add_error("tifffile库未安装")
        return result
    
    file_path = Path(file_path)
    if not file_path.exists():
        result.add_error(f"文件不存在: {file_path}")
        return result
    
    try:
        with tifffile.TiffFile(file_path) as tif:
            result.add_stat("file_size_mb", file_path.stat().st_size / 1024 / 1024)
            result.add_stat("n_pages", len(tif.pages))
            
            page = tif.pages[0]
            result.add_stat("image_width", page.shape[-1] if page.shape else 0)
            result.add_stat("image_height", page.shape[-2] if len(page.shape) > 1 else 0)
            result.add_stat("dtype", str(page.dtype))
            
            if page.compression:
                result.add_stat("compression", str(page.compression))
            
            total_pixels = page.shape[-1] * page.shape[-2] if page.shape else 0
            if total_pixels > 10000 * 10000:
                result.add_warning(f"影像尺寸较大: {page.shape[-1]}x{page.shape[-2]}", "size")
            elif total_pixels < 10 * 10:
                result.add_warning(f"影像尺寸过小: {page.shape[-1]}x{page.shape[-2]}", "size")
                
    except Exception as e:
        result.add_error(f"读取影像元数据失败: {str(e)}")
    
    return result


def check_band_data(img: np.ndarray, nodata_value: Optional[float] = None) -> ImageQualityResult:
    """
    检查波段数据有效性
    
    Parameters
    ----------
    img : np.ndarray
        影像数组
    nodata_value : float, optional
        无效数据值
        
    Returns
    -------
    ImageQualityResult
        质量检查结果
    """
    result = ImageQualityResult()
    
    if img.ndim == 2:
        result.add_stat("n_bands", 1)
        result.add_detail("single_band", True)
    else:
        result.add_stat("n_bands", img.shape[0])
        result.add_stat("height", img.shape[-2])
        result.add_stat("width", img.shape[-1])
        result.add_detail("single_band", False)
    
    if img.dtype == np.uint16:
        result.add_stat("data_type", "uint16")
    elif img.dtype == np.uint8:
        result.add_stat("data_type", "uint8")
    elif img.dtype == np.float32:
        result.add_stat("data_type", "float32")
    elif img.dtype == np.float64:
        result.add_stat("data_type", "float64")
    else:
        result.add_stat("data_type", str(img.dtype))
    
    valid_pixels = np.sum(np.isfinite(img))
    total_pixels = img.size
    valid_ratio = valid_pixels / total_pixels
    result.add_stat("valid_ratio", valid_ratio)
    
    if valid_ratio < 0.5:
        result.add_error("有效像元比例过低", "data_coverage")
    elif valid_ratio < 0.8:
        result.add_warning("有效像元比例较低", "data_coverage")
    
    if nodata_value is not None:
        nodata_ratio = np.sum(img == nodata_value) / total_pixels
        result.add_stat("nodata_ratio", nodata_ratio)
        if nodata_ratio > 0.9:
            result.add_warning("无效数据比例过高", "nodata")
    
    return result


def detect_anomalies(img: np.ndarray, method: str = "iqr", threshold: float = 3.0) -> ImageQualityResult:
    """
    检测影像异常值
    
    Parameters
    ----------
    img : np.ndarray
        影像数组
    method : str, optional
        检测方法: "iqr", "zscore", "percentile"
    threshold : float, optional
        异常阈值
        
    Returns
    -------
    ImageQualityResult
        质量检查结果
    """
    result = ImageQualityResult()
    
    img_flat = img.flatten()
    img_flat = img_flat[np.isfinite(img_flat)]
    
    if len(img_flat) == 0:
        result.add_error("影像中没有有效数据", "anomaly")
        return result
    
    result.add_stat("min_value", float(np.min(img_flat)))
    result.add_stat("max_value", float(np.max(img_flat)))
    result.add_stat("mean_value", float(np.mean(img_flat)))
    result.add_stat("std_value", float(np.std(img_flat)))
    
    if method == "iqr":
        q1 = np.percentile(img_flat, 25)
        q3 = np.percentile(img_flat, 75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        anomalies = (img_flat < lower_bound) | (img_flat > upper_bound)
        result.add_stat("iqr", float(iqr))
        result.add_stat("lower_bound", float(lower_bound))
        result.add_stat("upper_bound", float(upper_bound))
        
    elif method == "zscore":
        mean = np.mean(img_flat)
        std = np.std(img_flat)
        z_scores = np.abs((img_flat - mean) / std)
        anomalies = z_scores > threshold
        
        result.add_stat("mean", float(mean))
        result.add_stat("std", float(std))
        
    elif method == "percentile":
        lower_bound = np.percentile(img_flat, 0.5)
        upper_bound = np.percentile(img_flat, 99.5)
        anomalies = (img_flat < lower_bound) | (img_flat > upper_bound)
        
        result.add_stat("lower_percentile", float(lower_bound))
        result.add_stat("upper_percentile", float(upper_bound))
    
    anomaly_ratio = np.sum(anomalies) / len(img_flat)
    result.add_stat("anomaly_ratio", float(anomaly_ratio))
    result.add_stat("anomaly_count", int(np.sum(anomalies)))
    
    if anomaly_ratio > 0.1:
        result.add_warning(f"异常值比例较高: {anomaly_ratio*100:.2f}%", "anomaly")
    elif anomaly_ratio > 0.05:
        result.add_warning(f"存在少量异常值: {anomaly_ratio*100:.2f}%", "anomaly")
    
    return result


def check_band_ranges(img: np.ndarray, band_ranges: Optional[Dict[str, Tuple[float, float]]] = None) -> ImageQualityResult:
    """
    检查波段值是否在合理范围内
    
    Parameters
    ----------
    img : np.ndarray
        影像数组
    band_ranges : dict, optional
        波段范围字典
        
    Returns
    -------
    ImageQualityResult
        质量检查结果
    """
    result = ImageQualityResult()
    
    if band_ranges is None:
        band_ranges = {}
    
    if img.ndim == 2:
        img = img[np.newaxis, :]
    
    n_bands = img.shape[0]
    result.add_stat("n_bands_checked", n_bands)
    
    for i in range(n_bands):
        band_data = img[i].flatten()
        band_data = band_data[np.isfinite(band_data)]
        
        if len(band_data) == 0:
            result.add_warning(f"波段 {i} 没有有效数据", "band_range")
            continue
        
        band_min = float(np.min(band_data))
        band_max = float(np.max(band_data))
        band_mean = float(np.mean(band_data))
        
        result.add_stat(f"band_{i}_min", band_min)
        result.add_stat(f"band_{i}_max", band_max)
        result.add_stat(f"band_{i}_mean", band_mean)
        
        if i in band_ranges:
            expected_min, expected_max = band_ranges[i]
            if band_min < expected_min:
                result.add_warning(f"波段 {i} 最小值低于预期", "band_range")
            if band_max > expected_max:
                result.add_warning(f"波段 {i} 最大值高于预期", "band_range")
    
    return result


def check_crs_metadata(file_path: Union[str, Path]) -> ImageQualityResult:
    """
    检查影像坐标系统信息
    
    Parameters
    ----------
    file_path : str or Path
        TIFF文件路径
        
    Returns
    -------
    ImageQualityResult
        质量检查结果
    """
    result = ImageQualityResult()
    
    if not RASTERIO_AVAILABLE:
        result.add_warning("rasterio库未安装，无法检查坐标系", "crs")
        result.add_stat("crs_available", False)
        return result
    
    try:
        import rasterio
        from rasterio.crs import CRS
        
        with rasterio.open(file_path) as src:
            crs = src.crs
            
            if crs is not None:
                result.add_stat("crs_available", True)
                result.add_stat("crs_wkt", crs.to_wkt())
                result.add_stat("crs_epsg", crs.to_epsg())
                result.add_stat("crs_proj4", crs.to_proj4())
                
                crs_type = "Geographic" if crs.is_geographic else "Projected"
                result.add_stat("crs_type", crs_type)
                
                if crs.is_geographic:
                    result.add_detail("coordinate_system", "经纬度坐标 (WGS84)")
                else:
                    result.add_detail("coordinate_system", f"投影坐标: {crs.name}")
                
                bounds = src.bounds
                result.add_stat("bounds_left", bounds.left)
                result.add_stat("bounds_right", bounds.right)
                result.add_stat("bounds_top", bounds.top)
                result.add_stat("bounds_bottom", bounds.bottom)
                
                res = src.res
                result.add_stat("resolution_x", res[0])
                result.add_stat("resolution_y", res[1])
                
            else:
                result.add_warning("影像未包含坐标系统信息", "crs")
                result.add_stat("crs_available", False)
                
    except Exception as e:
        result.add_warning(f"无法读取坐标系统信息: {str(e)}", "crs")
        result.add_stat("crs_available", False)
    
    return result


def check_tiff_quality(file_path: Union[str, Path], 
                       nodata_value: Optional[float] = None,
                       check_anomalies: bool = True) -> Dict:
    """
    完整的TIFF影像质量检查
    
    Parameters
    ----------
    file_path : str or Path
        TIFF文件路径
    nodata_value : float, optional
        无效数据值
    check_anomalies : bool, optional
        是否检查异常值
        
    Returns
    -------
    Dict
        完整的质量检查报告
    """
    print(f"正在检查影像: {file_path}")
    
    metadata_result = check_tiff_metadata(file_path)
    print("✓ 元数据检查完成")
    
    if not TIFFILE_AVAILABLE:
        return {"error": "tifffile库未安装"}
    
    img = tifffile.imread(file_path)
    
    band_result = check_band_data(img, nodata_value)
    print("✓ 波段数据检查完成")
    
    anomaly_result = detect_anomalies(img) if check_anomalies else ImageQualityResult()
    if check_anomalies:
        print("✓ 异常值检测完成")
    
    range_result = check_band_ranges(img)
    print("✓ 波段范围检查完成")
    
    crs_result = check_crs_metadata(file_path)
    print("✓ 坐标系检查完成")
    
    overall_passed = (
        metadata_result.passed and 
        band_result.passed and 
        anomaly_result.passed and 
        range_result.passed
    )
    
    all_warnings = (
        metadata_result.warnings + 
        band_result.warnings + 
        anomaly_result.warnings + 
        range_result.warnings +
        crs_result.warnings
    )
    
    all_errors = (
        metadata_result.errors + 
        band_result.errors + 
        anomaly_result.errors + 
        range_result.errors +
        crs_result.errors
    )
    
    return {
        "file_path": str(file_path),
        "overall_passed": overall_passed,
        "metadata": metadata_result.get_summary(),
        "band_data": band_result.get_summary(),
        "anomalies": anomaly_result.get_summary() if check_anomalies else None,
        "band_ranges": range_result.get_summary(),
        "crs": crs_result.get_summary(),
        "warnings": all_warnings,
        "errors": all_errors
    }


def print_quality_report(report: Dict) -> None:
    """
    打印影像质量报告
    """
    print("=" * 60)
    print("影像质量检查报告")
    print("=" * 60)
    
    status = "✓ 通过" if report["overall_passed"] else "✗ 未通过"
    print(f"\n总体状态: {status}")
    print(f"文件: {report.get('file_path', 'N/A')}")
    
    if report.get("errors"):
        print("\n错误:")
        for err in report["errors"]:
            print(f"  - [{err['category']}] {err['message']}")
    
    if report.get("warnings"):
        print("\n警告:")
        for warn in report["warnings"]:
            print(f"  - [{warn['category']}] {warn['message']}")
    
    print("\n详细信息:")
    meta = report.get("metadata", {}).get("stats", {})
    if meta:
        print(f"  影像尺寸: {meta.get('image_width', 'N/A')} x {meta.get('image_height', 'N/A')}")
        print(f"  数据类型: {meta.get('data_type', 'N/A')}")
        print(f"  文件大小: {meta.get('file_size_mb', 'N/A'):.2f} MB")
    
    band = report.get("band_data", {}).get("stats", {})
    if band:
        print(f"  波段数量: {band.get('n_bands', 'N/A')}")
        print(f"  有效像元比例: {band.get('valid_ratio', 'N/A'):.2%}")
    
    if report.get("anomalies"):
        anomaly = report["anomalies"].get("stats", {})
        if anomaly:
            print(f"  异常值比例: {anomaly.get('anomaly_ratio', 'N/A'):.2%}")
            print(f"  异常值数量: {anomaly.get('anomaly_count', 'N/A')}")
    
    crs = report.get("crs", {}).get("stats", {})
    if crs:
        print(f"\n坐标系统信息:")
        print(f"  坐标系可用: {crs.get('crs_available', 'N/A')}")
        if crs.get('crs_available'):
            print(f"  坐标系类型: {crs.get('crs_type', 'N/A')}")
            print(f"  坐标系统: {crs.get('coordinate_system', 'N/A')}")
            if crs.get('crs_epsg'):
                print(f"  EPSG代码: {crs.get('crs_epsg', 'N/A')}")
            print(f"  分辨率: {crs.get('resolution_x', 'N/A')} x {crs.get('resolution_y', 'N/A')}")
            print(f"  范围: ({crs.get('bounds_left', 'N/A'):.4f}, {crs.get('bounds_bottom', 'N/A'):.4f}) - ({crs.get('bounds_right', 'N/A'):.4f}, {crs.get('bounds_top', 'N/A'):.4f})")
    else:
        print(f"\n坐标系统信息: 不可用")
    
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python image_quality.py <tiff_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    report = check_tiff_quality(file_path)
    print_quality_report(report)
