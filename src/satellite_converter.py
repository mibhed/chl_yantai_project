"""
卫星影像格式验证与转换模块

本模块提供多种卫星影像的格式验证、自动识别和转换功能，
支持MODIS、Landsat、Sentinel-2等常见卫星数据。

主要功能：
    - 自动识别卫星类型
    - 验证TIFF格式是否符合系统要求
    - 自动转换不同卫星数据到标准格式
    - 波段映射和重采样
    - 数据质量检查
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Literal
import re

try:
    import tifffile
    TIFFILE_AVAILABLE = True
except ImportError:
    TIFFILE_AVAILABLE = False

try:
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

# 卫星类型定义
SatelliteType = Literal["MODIS", "Landsat", "Sentinel2", "Unknown"]

# MODIS标准波段配置
MODIS_CONFIG = {
    "name": "MODIS",
    "bands": {
        "Rrs_412": {"wavelength": 413, "description": "蓝光波段1"},
        "Rrs_443": {"wavelength": 443, "description": "蓝光波段2"},
        "Rrs_469": {"wavelength": 469, "description": "蓝光波段3"},
        "Rrs_488": {"wavelength": 488, "description": "青光波段"},
        "Rrs_531": {"wavelength": 531, "description": "绿光波段1"},
        "Rrs_547": {"wavelength": 547, "description": "绿光波段2"},
        "Rrs_555": {"wavelength": 555, "description": "绿光波段3"},
        "Rrs_645": {"wavelength": 645, "description": "红光波段1"},
        "Rrs_667": {"wavelength": 667, "description": "红光波段2"},
        "Rrs_678": {"wavelength": 678, "description": "红光波段3"},
    },
    "expected_bands": 10,
    "common_names": ["MODIS", "MOD", "Aqua", "Terra"]
}

# Landsat波段配置
LANDSAT_CONFIG = {
    "name": "Landsat",
    "bands": {
        "B1": {"wavelength": 443, "description": "沿海/气溶胶"},
        "B2": {"wavelength": 482, "description": "蓝光"},
        "B3": {"wavelength": 562, "description": "绿光"},
        "B4": {"wavelength": 655, "description": "红光"},
        "B5": {"wavelength": 865, "description": "近红外"},
        "B6": {"wavelength": 1610, "description": "短波红外1"},
        "B7": {"wavelength": 2200, "description": "短波红外2"},
        "B8": {"wavelength": 590, "description": "全色"},
        "B9": {"wavelength": 1373, "description": "卷云"},
        "B10": {"wavelength": 10800, "description": "热红外1"},
        "B11": {"wavelength": 12000, "description": "热红外2"},
    },
    "expected_bands": 11,
    "common_names": ["Landsat", "LC08", "LE07", "LT05", "Landsat8", "Landsat7"]
}

# Sentinel-2波段配置
SENTINEL2_CONFIG = {
    "name": "Sentinel-2",
    "bands": {
        "B1": {"wavelength": 443, "description": "沿海"},
        "B2": {"wavelength": 490, "description": "蓝光"},
        "B3": {"wavelength": 560, "description": "绿光"},
        "B4": {"wavelength": 665, "description": "红光"},
        "B5": {"wavelength": 705, "description": "红边1"},
        "B6": {"wavelength": 740, "description": "红边2"},
        "B7": {"wavelength": 783, "description": "红边3"},
        "B8": {"wavelength": 842, "description": "近红外"},
        "B8A": {"wavelength": 865, "description": "近红外窄"},
        "B9": {"wavelength": 945, "description": "水汽"},
        "B10": {"wavelength": 1375, "description": "卷云"},
        "B11": {"wavelength": 1610, "description": "短波红外1"},
        "B12": {"wavelength": 2190, "description": "短波红外2"},
    },
    "expected_bands": 13,
    "common_names": ["Sentinel", "S2", "S2A", "S2B", "MSI"]
}

# 波段映射配置：将不同卫星的波段映射到标准Rrs波段
BAND_MAPPING = {
    "MODIS": {
        "Rrs_412": "Rrs_412",
        "Rrs_443": "Rrs_443",
        "Rrs_469": "Rrs_469",
        "Rrs_488": "Rrs_488",
        "Rrs_531": "Rrs_531",
        "Rrs_547": "Rrs_547",
        "Rrs_555": "Rrs_555",
        "Rrs_645": "Rrs_645",
        "Rrs_667": "Rrs_667",
        "Rrs_678": "Rrs_678",
    },
    "Landsat": {
        "Rrs_412": "B1",
        "Rrs_443": "B2",
        "Rrs_488": "B2",
        "Rrs_531": "B3",
        "Rrs_547": "B3",
        "Rrs_555": "B3",
        "Rrs_645": "B4",
        "Rrs_667": "B4",
        "Rrs_678": "B4",
    },
    "Sentinel2": {
        "Rrs_412": "B1",
        "Rrs_443": "B2",
        "Rrs_488": "B2",
        "Rrs_531": "B3",
        "Rrs_547": "B3",
        "Rrs_555": "B3",
        "Rrs_645": "B4",
        "Rrs_667": "B4",
        "Rrs_678": "B4",
    }
}


class SatelliteImageValidator:
    """卫星影像验证器"""
    
    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.satellite_type: SatelliteType = "Unknown"
        self.metadata = {}
        self.validation_result = {
            "valid": False,
            "satellite_type": "Unknown",
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
    def validate(self) -> Dict:
        """
        验证TIFF影像格式
        
        Returns
        -------
        dict
            验证结果，包含卫星类型、错误、警告和建议
        """
        if not self.file_path.exists():
            self.validation_result["errors"].append("文件不存在")
            return self.validation_result
        
        if not TIFFILE_AVAILABLE:
            self.validation_result["errors"].append("tifffile库未安装")
            return self.validation_result
        
        try:
            with tifffile.TiffFile(self.file_path) as tif:
                self.metadata = self._extract_metadata(tif)
                self.satellite_type = self._identify_satellite()
                self._check_format_compatibility()
                self._generate_suggestions()
                
                self.validation_result["valid"] = len(self.validation_result["errors"]) == 0
                self.validation_result["satellite_type"] = self.satellite_type
                
        except Exception as e:
            self.validation_result["errors"].append(f"文件读取失败: {str(e)}")
        
        return self.validation_result
    
    def _extract_metadata(self, tif) -> Dict:
        """提取TIFF元数据"""
        metadata = {
            "file_size_mb": self.file_path.stat().st_size / 1024 / 1024,
            "n_pages": len(tif.pages),
            "shape": tif.pages[0].shape,
            "dtype": str(tif.pages[0].dtype),
            "description": tif.pages[0].description if hasattr(tif.pages[0], 'description') else ""
        }
        
        if RASTERIO_AVAILABLE:
            try:
                with rasterio.open(self.file_path) as src:
                    metadata["crs"] = str(src.crs) if src.crs else None
                    metadata["transform"] = src.transform
                    metadata["bounds"] = src.bounds
                    metadata["res"] = src.res
                    metadata["count"] = src.count
            except Exception:
                pass
        
        return metadata
    
    def _identify_satellite(self) -> SatelliteType:
        """识别卫星类型"""
        filename = self.file_path.name.upper()
        description = self.metadata.get("description", "").upper()
        
        # MODIS识别
        modis_keywords = ["MODIS", "MOD", "AQUA", "TERRA", "MYD", "MOD"]
        if any(keyword in filename or keyword in description for keyword in modis_keywords):
            return "MODIS"
        
        # Landsat识别
        landsat_keywords = ["LANDSAT", "LC08", "LE07", "LT05", "Landsat8", "Landsat7"]
        if any(keyword in filename or keyword in description for keyword in landsat_keywords):
            return "Landsat"
        
        # Sentinel-2识别
        sentinel_keywords = ["SENTINEL", "S2", "S2A", "S2B", "MSI", "T30"]
        if any(keyword in filename or keyword in description for keyword in sentinel_keywords):
            return "Sentinel2"
        
        # 基于波段数量推断
        n_bands = self.metadata.get("count", len(self.metadata.get("shape", [])))
        if n_bands == 10:
            self.validation_result["warnings"].append("根据波段数量推测为MODIS，请确认")
            return "MODIS"
        elif n_bands in [11, 12]:
            self.validation_result["warnings"].append("根据波段数量推测为Landsat，请确认")
            return "Landsat"
        elif n_bands >= 13:
            self.validation_result["warnings"].append("根据波段数量推测为Sentinel-2，请确认")
            return "Sentinel2"
        
        return "Unknown"
    
    def _check_format_compatibility(self):
        """检查格式兼容性"""
        # 检查数据类型
        dtype = self.metadata.get("dtype", "")
        if "uint" in dtype or "int" in dtype:
            self.validation_result["warnings"].append("影像为整数类型，可能需要转换为浮点型")
        
        # 检查波段数量
        n_bands = self.metadata.get("count", len(self.metadata.get("shape", [])))
        if self.satellite_type == "MODIS" and n_bands != 10:
            self.validation_result["errors"].append(f"MODIS影像应有10个波段，当前有{n_bands}个")
        elif self.satellite_type == "Landsat" and n_bands < 7:
            self.validation_result["errors"].append(f"Landsat影像至少需要7个波段，当前有{n_bands}个")
        elif self.satellite_type == "Sentinel2" and n_bands < 10:
            self.validation_result["errors"].append(f"Sentinel-2影像至少需要10个波段，当前有{n_bands}个")
        
        # 检查坐标系
        if not self.metadata.get("crs"):
            self.validation_result["warnings"].append("影像缺少坐标系信息")
    
    def _generate_suggestions(self):
        """生成转换建议"""
        if self.satellite_type == "Unknown":
            self.validation_result["suggestions"].append("无法自动识别卫星类型，请手动指定")
            self.validation_result["suggestions"].append("支持MODIS、Landsat、Sentinel-2")
        else:
            self.validation_result["suggestions"].append(f"识别为{self.satellite_type}影像")
            self.validation_result["suggestions"].append("可以使用自动转换功能处理此影像")
            self.validation_result["suggestions"].append("转换后可用于模型训练和预测")


def convert_satellite_to_standard(
    file_path: Union[str, Path],
    satellite_type: Optional[SatelliteType] = None,
    output_path: Optional[Union[str, Path]] = None,
    target_resolution: Optional[float] = None,
    resampling_method: str = "nearest"
) -> Tuple[np.ndarray, Dict]:
    """
    将卫星影像转换为标准格式
    
    Parameters
    ----------
    file_path : str or Path
        输入TIFF文件路径
    satellite_type : str, optional
        卫星类型，如果为None则自动识别
    output_path : str or Path, optional
        输出文件路径，如果为None则不保存
    target_resolution : float, optional
        目标分辨率（米），如果为None则保持原分辨率
    resampling_method : str, optional
        重采样方法: "nearest", "bilinear", "cubic"
    
    Returns
    -------
    tuple
        (转换后的影像数组, 元数据字典)
    """
    if not TIFFILE_AVAILABLE:
        raise ImportError("tifffile库未安装")
    
    file_path = Path(file_path)
    
    # 验证和识别卫星类型
    validator = SatelliteImageValidator(file_path)
    validation_result = validator.validate()
    
    if not validation_result["valid"]:
        raise ValueError(f"影像验证失败: {validation_result['errors']}")
    
    if satellite_type is None:
        satellite_type = validator.satellite_type
    
    if satellite_type == "Unknown":
        raise ValueError("无法识别卫星类型，请手动指定")
    
    # 读取影像
    with tifffile.TiffFile(file_path) as tif:
        img = tif.asarray()
        if img.ndim == 2:
            img = img[np.newaxis, :]
    
    # 获取波段映射
    mapping = BAND_MAPPING.get(satellite_type, {})
    
    # 根据卫星类型选择配置
    if satellite_type == "MODIS":
        config = MODIS_CONFIG
    elif satellite_type == "Landsat":
        config = LANDSAT_CONFIG
    elif satellite_type == "Sentinel2":
        config = SENTINEL2_CONFIG
    else:
        config = None
    
    # 转换为标准Rrs波段
    standard_img = _convert_to_standard_bands(img, satellite_type, mapping)
    
    # 重采样（如果需要）
    if target_resolution is not None and RASTERIO_AVAILABLE:
        standard_img = _resample_image(standard_img, file_path, target_resolution, resampling_method)
    
    # 构建元数据
    metadata = {
        "satellite_type": satellite_type,
        "shape": standard_img.shape,
        "dtype": str(standard_img.dtype),
        "band_mapping": mapping,
        "original_metadata": validator.metadata
    }
    
    # 保存结果（如果指定了输出路径）
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tifffile.imwrite(output_path, standard_img)
        metadata["output_path"] = str(output_path)
    
    return standard_img, metadata


def _convert_to_standard_bands(
    img: np.ndarray,
    satellite_type: SatelliteType,
    mapping: Dict[str, str]
) -> np.ndarray:
    """
    将影像转换为标准Rrs波段
    
    Parameters
    ----------
    img : np.ndarray
        输入影像数组
    satellite_type : str
        卫星类型
    mapping : dict
        波段映射
    
    Returns
    -------
    np.ndarray
        标准化的影像数组
    """
    # MODIS影像已经是标准格式
    if satellite_type == "MODIS":
        return img.astype(np.float32)
    
    # Landsat和Sentinel-2需要转换
    standard_bands = []
    
    # 获取需要的标准波段
    target_bands = ["Rrs_412", "Rrs_443", "Rrs_488", "Rrs_531", "Rrs_547", 
                     "Rrs_555", "Rrs_645", "Rrs_667", "Rrs_678"]
    
    for target_band in target_bands:
        if target_band in mapping:
            source_band = mapping[target_band]
            # 提取源波段
            if isinstance(source_band, str):
                # 根据波段名称查找
                if satellite_type == "Landsat":
                    band_idx = int(source_band.replace("B", "")) - 1
                elif satellite_type == "Sentinel2":
                    if source_band == "B8A":
                        band_idx = 7
                    else:
                        band_idx = int(source_band.replace("B", "")) - 1
                else:
                    band_idx = 0
            else:
                band_idx = source_band
            
            if band_idx < img.shape[0]:
                band_data = img[band_idx].astype(np.float32)
                
                # Landsat和Sentinel-2的DN值转换为反射率
                if satellite_type in ["Landsat", "Sentinel2"]:
                    band_data = band_data / 10000.0  # 简化的转换公式
                
                standard_bands.append(band_data)
            else:
                # 如果找不到对应波段，用最近波段的值填充
                if len(standard_bands) > 0:
                    standard_bands.append(standard_bands[-1])
                else:
                    standard_bands.append(np.zeros_like(img[0], dtype=np.float32))
        else:
            # 如果没有映射，用零填充
            standard_bands.append(np.zeros_like(img[0], dtype=np.float32))
    
    return np.array(standard_bands)


def _resample_image(
    img: np.ndarray,
    file_path: Path,
    target_resolution: float,
    resampling_method: str
) -> np.ndarray:
    """
    重采样影像到目标分辨率
    
    Parameters
    ----------
    img : np.ndarray
        输入影像
    file_path : Path
        原始文件路径
    target_resolution : float
        目标分辨率
    resampling_method : str
        重采样方法
    
    Returns
    -------
    np.ndarray
        重采样后的影像
    """
    try:
        with rasterio.open(file_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, src.crs,
                src.width, src.height,
                *src.bounds,
                dst_width=int((src.bounds.right - src.bounds.left) / target_resolution),
                dst_height=int((src.bounds.top - src.bounds.bottom) / target_resolution)
            )
            
            # 选择重采样方法
            resampling_map = {
                "nearest": Resampling.nearest,
                "bilinear": Resampling.bilinear,
                "cubic": Resampling.cubic
            }
            resample = resampling_map.get(resampling_method, Resampling.nearest)
            
            # 创建输出数组
            resampled = np.zeros((img.shape[0], height, width), dtype=img.dtype)
            
            # 对每个波段进行重采样
            for i in range(img.shape[0]):
                dest = np.zeros((height, width), dtype=img.dtype)
                reproject(
                    source=img[i],
                    destination=dest,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=src.crs,
                    resampling=resample
                )
                resampled[i] = dest
            
            return resampled
    except Exception as e:
        print(f"重采样失败: {e}，返回原始影像")
        return img


def batch_convert_directory(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    satellite_type: Optional[SatelliteType] = None,
    pattern: str = "*.tif"
) -> List[Dict]:
    """
    批量转换目录中的TIFF文件
    
    Parameters
    ----------
    input_dir : str or Path
        输入目录
    output_dir : str or Path
        输出目录
    satellite_type : str, optional
        卫星类型，如果为None则自动识别
    pattern : str
        文件匹配模式
    
    Returns
    -------
    list
        转换结果列表
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    tif_files = list(input_dir.glob(pattern))
    
    for tif_file in tif_files:
        try:
            print(f"正在处理: {tif_file.name}")
            
            output_path = output_dir / f"converted_{tif_file.name}"
            img, metadata = convert_satellite_to_standard(
                tif_file,
                satellite_type=satellite_type,
                output_path=output_path
            )
            
            results.append({
                "file": str(tif_file),
                "status": "success",
                "output": str(output_path),
                "metadata": metadata
            })
            
        except Exception as e:
            results.append({
                "file": str(tif_file),
                "status": "failed",
                "error": str(e)
            })
    
    return results


def print_validation_report(validation_result: Dict):
    """打印验证报告"""
    print("=" * 60)
    print("卫星影像验证报告")
    print("=" * 60)
    
    status = "✓ 通过" if validation_result["valid"] else "✗ 未通过"
    print(f"\n验证状态: {status}")
    print(f"卫星类型: {validation_result['satellite_type']}")
    
    if validation_result.get("errors"):
        print("\n错误:")
        for error in validation_result["errors"]:
            print(f"  ✗ {error}")
    
    if validation_result.get("warnings"):
        print("\n警告:")
        for warning in validation_result["warnings"]:
            print(f"  ⚠ {warning}")
    
    if validation_result.get("suggestions"):
        print("\n建议:")
        for suggestion in validation_result["suggestions"]:
            print(f"  → {suggestion}")
    
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python satellite_converter.py <tiff_file>              # 验证文件")
        print("  python satellite_converter.py <tiff_file> --convert    # 转换文件")
        print("  python satellite_converter.py <input_dir> <output_dir> --batch  # 批量转换")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if "--batch" in sys.argv and len(sys.argv) >= 3:
        output_dir = sys.argv[2]
        results = batch_convert_directory(file_path, output_dir)
        print(f"\n批量转换完成，共处理{len(results)}个文件")
        for result in results:
            print(f"  {result['file']}: {result['status']}")
    
    elif "--convert" in sys.argv:
        try:
            img, metadata = convert_satellite_to_standard(file_path)
            print(f"转换成功!")
            print(f"输出shape: {img.shape}")
            print(f"卫星类型: {metadata['satellite_type']}")
        except Exception as e:
            print(f"转换失败: {e}")
    
    else:
        validator = SatelliteImageValidator(file_path)
        result = validator.validate()
        print_validation_report(result)