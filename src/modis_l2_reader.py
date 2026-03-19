"""
MODIS L2 HDF5/NetCDF 读取模块

支持读取 NASA LAADS 提供的 MODIS L2 级产品，提取：
- 遥感反射率 (Rrs) 波段
- 经纬度网格
- 质量标志 (QA flags)
- 其他辅助数据

MODIS L2 产品来源: https://ladsweb.modaps.eosdis.nasa.gov/
主要产品: MODISA_L2, MYD21_L2 (SST/Chl-a 综合)
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import warnings

try:
    import netCDF4
    NETCDF4_AVAILABLE = True
except ImportError:
    NETCDF4_AVAILABLE = False

try:
    import h5py
    H5PY_AVAILABLE = True
except ImportError:
    H5PY_AVAILABLE = False


# MODIS Rrs 波段定义 (nm)
MODIS_RRS_BANDS = {
    "Rrs_412": {"wavelength": 412, "SDS": "Rrs_412", "description": "蓝光波段1"},
    "Rrs_443": {"wavelength": 443, "SDS": "Rrs_443", "description": "蓝光波段2"},
    "Rrs_469": {"wavelength": 469, "SDS": "Rrs_469", "description": "蓝光波段3"},
    "Rrs_488": {"wavelength": 488, "SDS": "Rrs_488", "description": "青光波段"},
    "Rrs_531": {"wavelength": 531, "SDS": "Rrs_531", "description": "绿光波段1"},
    "Rrs_547": {"wavelength": 547, "SDS": "Rrs_547", "description": "绿光波段2"},
    "Rrs_555": {"wavelength": 555, "SDS": "Rrs_555", "description": "绿光波段3"},
    "Rrs_645": {"wavelength": 645, "SDS": "Rrs_645", "description": "红光波段1"},
    "Rrs_667": {"wavelength": 667, "SDS": "Rrs_667", "description": "红光波段2"},
    "Rrs_678": {"wavelength": 678, "SDS": "Rrs_678", "description": "红光波段3"},
}

# NASA MODIS L2 常用 SDS 名称变体（兼容不同产品版本）
SDS_NAME_VARIANTS = {
    "Rrs_412": ["Rrs_412", "Rrs_412_sw", "remote_reflectance_412"],
    "Rrs_443": ["Rrs_443", "Rrs_443_sw", "remote_reflectance_443"],
    "Rrs_469": ["Rrs_469", "Rrs_469_sw"],
    "Rrs_488": ["Rrs_488", "Rrs_488_sw", "remote_reflectance_488"],
    "Rrs_531": ["Rrs_531", "Rrs_531_sw", "remote_reflectance_531"],
    "Rrs_547": ["Rrs_547", "Rrs_547_sw", "remote_reflectance_547"],
    "Rrs_555": ["Rrs_555", "Rrs_555_sw"],
    "Rrs_645": ["Rrs_645", "Rrs_645_sw"],
    "Rrs_667": ["Rrs_667", "Rrs_667_sw"],
    "Rrs_678": ["Rrs_678", "Rrs_678_sw", "remote_reflectance_678"],
}

# QA flag 值含义 (简化版，通用)
# 0 = best, 1 = good, 2 = marginal, 3+ = bad/fill
QA_FLAGS = {
    0: "best",
    1: "good",
    2: "marginal",
    3: "bad",
}


class MODISL2Reader:
    """
    MODIS L2 产品读取器

    支持 NetCDF4 (.nc) 和 HDF5 (.hdf/.h5) 格式。
    自动识别 Rrs 波段、经纬度、质量标志。

    Parameters
    ----------
    file_path : str or Path
        MODIS L2 文件路径 (.nc 或 .hdf)
    """

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.metadata = {}
        self._dataset = None
        self._file_format = None  # "netcdf4" or "hdf5"

    def _open(self):
        """打开文件并检测格式"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")

        if self._dataset is not None:
            return

        suffix = self.file_path.suffix.lower()

        # 优先尝试 NetCDF4（兼容 .nc 和 .hdf）
        if NETCDF4_AVAILABLE:
            try:
                self._dataset = netCDF4.Dataset(str(self.file_path), "r")
                self._file_format = "netcdf4"
                return
            except Exception:
                pass

        # 回退到 h5py
        if H5PY_AVAILABLE:
            try:
                self._dataset = h5py.File(str(self.file_path), "r")
                self._file_format = "hdf5"
                return
            except Exception:
                pass

        raise ImportError(
            "无法读取文件，请安装 netCDF4 或 h5py: pip install netCDF4 h5py"
        )

    def close(self):
        """关闭文件"""
        if self._dataset is not None:
            self._dataset.close()
            self._dataset = None

    def __enter__(self):
        self._open()
        return self

    def __exit__(self, *args):
        self.close()

    def _get_sds(self, name: str) -> Optional[str]:
        """尝试多种 SDS 名称变体找到正确的波段名称"""
        variants = SDS_NAME_VARIANTS.get(name, [name])

        if self._file_format == "netcdf4":
            for var_name in variants:
                if var_name in self._dataset.variables:
                    return var_name

        elif self._file_format == "hdf5":
            def find_key(group, target):
                found = []
                def _search(g, prefix=""):
                    for k in g.keys():
                        full_key = f"{prefix}/{k}" if prefix else k
                        if target.lower() in k.lower():
                            found.append(full_key)
                        if isinstance(g[k], h5py.Group):
                            _search(g[k], full_key)
                _search(g)
                return found

            results = find_key(self._dataset, name)
            if results:
                return results[0]

        return None

    def _read_variable(self, var_name: str) -> Optional[np.ndarray]:
        """读取变量，处理维度和缺省值"""
        actual_name = self._get_sds(var_name)
        if actual_name is None:
            return None

        try:
            if self._file_format == "netcdf4":
                var = self._dataset.variables[actual_name]
                data = var[:].data
                # 处理缺省值
                if hasattr(var, "_FillValue"):
                    data = np.where(data == var._FillValue, np.nan, data)
                elif hasattr(var, "missing_value"):
                    data = np.where(data == var.missing_value, np.nan, data)
            else:
                var = self._dataset[actual_name]
                data = var[:]
                if isinstance(data, h5py.Dataset):
                    fill_value = var.attrs.get("FillValue", None)
                    if fill_value is not None:
                        data = np.where(data == fill_value, np.nan, data)

            return np.array(data, dtype=np.float32)
        except Exception:
            return None

    def _read_lon_lat(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """读取经纬度"""
        lon = None
        lat = None

        # 尝试不同名称
        for lon_name in ["lon", "longitude", "Longitude"]:
            if self._file_format == "netcdf4":
                if lon_name in self._dataset.variables:
                    var = self._dataset.variables[lon_name]
                    lon = var[:].data
                    if hasattr(var, "_FillValue"):
                        lon = np.where(lon == var._FillValue, np.nan, lon)
            else:
                def find_in_h5(obj, name):
                    if name.lower() in obj.name.lower():
                        return obj.name
                    return None
                for obj in self._dataset.values():
                    if isinstance(obj, h5py.Dataset):
                        if lon_name.lower() in obj.name.lower():
                            lon = obj[:]
                            break
            if lon is not None:
                break

        for lat_name in ["lat", "latitude", "Latitude"]:
            if self._file_format == "netcdf4":
                if lat_name in self._dataset.variables:
                    var = self._dataset.variables[lat_name]
                    lat = var[:].data
                    if hasattr(var, "_FillValue"):
                        lat = np.where(lat == var._FillValue, np.nan, lat)
            else:
                for obj in self._dataset.values():
                    if isinstance(obj, h5py.Dataset):
                        if lat_name.lower() in obj.name.lower():
                            lat = obj[:]
                            break
            if lat is not None:
                break

        return lon, lat

    def _read_qa(self) -> Optional[np.ndarray]:
        """读取质量标志"""
        for qa_name in ["l2_flags", "qual_flag", "quality", "QA", "flags"]:
            if self._file_format == "netcdf4":
                if qa_name in self._dataset.variables:
                    return self._dataset.variables[qa_name][:].data
            else:
                for obj in self._dataset.values():
                    if isinstance(obj, h5py.Dataset):
                        if qa_name.lower() in obj.name.lower():
                            return obj[:]
        return None

    def read_all(self) -> Dict:
        """
        读取 MODIS L2 文件的全部关键数据

        Returns
        -------
        dict
            包含以下键：
            - rrs_bands: dict[str, np.ndarray]  各波段遥感反射率 (sr^-1)
            - lon: np.ndarray  经度网格
            - lat: np.ndarray  纬度网格
            - qa: np.ndarray or None  质量标志
            - metadata: dict  文件元数据
            - file_format: str  文件格式
        """
        self._open()

        result = {
            "file_path": str(self.file_path),
            "file_format": self._file_format,
            "rrs_bands": {},
            "lon": None,
            "lat": None,
            "qa": None,
            "metadata": {},
            "shape": None,
            "bands_found": [],
            "warnings": [],
        }

        # 读取经纬度
        lon, lat = self._read_lon_lat()
        if lon is not None:
            result["lon"] = np.array(lon, dtype=np.float32)
            result["lat"] = np.array(lat, dtype=np.float32)
            if result["shape"] is None:
                result["shape"] = lon.shape
        else:
            result["warnings"].append("未找到经纬度数据")

        # 读取 QA 标志
        qa = self._read_qa()
        if qa is not None:
            result["qa"] = qa

        # 读取 Rrs 波段
        for band_key, band_info in MODIS_RRS_BANDS.items():
            sds_name = band_info["SDS"]
            data = self._read_variable(sds_name)

            if data is not None:
                result["rrs_bands"][band_key] = np.array(data, dtype=np.float32)
                result["bands_found"].append(band_key)
                if result["shape"] is None:
                    result["shape"] = data.shape
            else:
                # 尝试从 _read_variable 的通用搜索
                for variant in SDS_NAME_VARIANTS.get(band_key, [band_key]):
                    data = self._read_variable(variant)
                    if data is not None:
                        result["rrs_bands"][band_key] = np.array(data, dtype=np.float32)
                        result["bands_found"].append(band_key)
                        if result["shape"] is None:
                            result["shape"] = data.shape
                        break

        # 提取元数据
        if self._file_format == "netcdf4":
            result["metadata"] = {
                "dimensions": dict(self._dataset.dimensions),
                "variables": list(self._dataset.variables.keys()),
            }
        else:
            def get_h5_info(obj, prefix=""):
                items = {}
                for k, v in obj.items():
                    full_key = f"{prefix}/{k}" if prefix else k
                    if isinstance(v, h5py.Dataset):
                        items[full_key] = dict(v.attrs)
                return items
            result["metadata"] = get_h5_info(self._dataset)

        result["n_bands_found"] = len(result["bands_found"])
        result["warnings"].append(
            f"找到 {result['n_bands_found']}/10 个 Rrs 波段"
            if result["n_bands_found"] < 10
            else "所有 10 个 Rrs 波段已读取"
        )

        return result

    def get_band_stats(self) -> Dict[str, Dict]:
        """获取各波段的统计信息"""
        data = self.read_all()
        stats = {}
        for band, arr in data["rrs_bands"].items():
            valid = arr[~np.isnan(arr)]
            if len(valid) > 0:
                stats[band] = {
                    "min": float(np.nanmin(arr)),
                    "max": float(np.nanmax(arr)),
                    "mean": float(np.nanmean(arr)),
                    "std": float(np.nanstd(arr)),
                    "valid_pixels": int(np.sum(~np.isnan(arr))),
                    "total_pixels": int(arr.size),
                    "coverage": float(np.sum(~np.isnan(arr)) / arr.size),
                }
        return stats


def read_modis_l2(
    file_path: Union[str, Path],
    lon_range: Optional[Tuple[float, float]] = None,
    lat_range: Optional[Tuple[float, float]] = None,
    qa_max: int = 1,
) -> Dict:
    """
    读取 MODIS L2 文件并可选按区域和质量过滤

    Parameters
    ----------
    file_path : str or Path
        MODIS L2 文件路径
    lon_range : tuple, optional
        经度范围 (lon_min, lon_max)
    lat_range : tuple, optional
        纬度范围 (lat_min, lat_max)
    qa_max : int, optional
        最大 QA 值（0=best, 1=good, 2=marginal, 3+=bad）
        默认 1 表示保留 quality ≤ 1 的像元

    Returns
    -------
    dict
        包含过滤后的 Rrs 数据、经纬度、质量标志等

    Examples
    --------
    >>> data = read_modis_l2("MODISA_L2_2024_001.nc",
    ...                       lon_range=(120.0, 123.0),
    ...                       lat_range=(36.0, 38.0),
    ...                       qa_max=1)
    >>> print(data["rrs_bands"].keys())
    dict_keys(['Rrs_412', 'Rrs_443', ..., 'Rrs_678'])
    """
    with MODISL2Reader(file_path) as reader:
        result = reader.read_all()

    if result["rrs_bands"] == {}:
        warnings.warn(f"警告: 文件 {file_path} 中未找到 Rrs 波段数据")

    # 按区域裁剪
    if lon_range is not None and lat_range is not None:
        result = clip_to_region(result, lon_range, lat_range)

    # 按质量过滤
    if qa_max is not None and result.get("qa") is not None:
        result = filter_by_qa(result, qa_max)

    return result


def clip_to_region(
    data: Dict,
    lon_range: Tuple[float, float],
    lat_range: Tuple[float, float],
) -> Dict:
    """
    按经纬度范围裁剪数据

    Parameters
    ----------
    data : dict
        MODISL2Reader.read_all() 返回的数据字典
    lon_range : tuple
        (lon_min, lon_max)
    lat_range : tuple
        (lat_min, lat_max)

    Returns
    -------
    dict
        裁剪后的数据
    """
    lon = data.get("lon")
    lat = data.get("lat")

    if lon is None or lat is None:
        data["warnings"].append("无法裁剪：缺少经纬度数据")
        return data

    lon_min, lon_max = lon_range
    lat_min, lat_max = lat_range

    # 构建掩膜 (lat, lon) 维度
    mask = (
        (lon >= lon_min) & (lon <= lon_max) &
        (lat >= lat_min) & (lat <= lat_max)
    )

    # 如果经纬度是 2D 网格
    if mask.ndim == 2:
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        row_min, row_max = np.where(rows)[0][[0, -1]]
        col_min, col_max = np.where(cols)[0][[0, -1]]

        data["lon"] = data["lon"][row_min:row_max+1, col_min:col_max+1]
        data["lat"] = data["lat"][row_min:row_max+1, col_min:col_max+1]
        data["mask"] = mask[row_min:row_max+1, col_min:col_max+1]

        for band in data["rrs_bands"]:
            data["rrs_bands"][band] = data["rrs_bands"][band][
                row_min:row_max+1, col_min:col_max+1
            ]

        if data.get("qa") is not None:
            data["qa"] = data["qa"][row_min:row_max+1, col_min:col_max+1]

    data["shape"] = data["lon"].shape
    data["warnings"].append(
        f"已裁剪至区域 [{lon_min:.2f}, {lon_max:.2f}] x [{lat_min:.2f}, {lat_max:.2f}]"
    )

    return data


def filter_by_qa(data: Dict, qa_max: int = 1) -> Dict:
    """
    按质量标志过滤数据

    Parameters
    ----------
    data : dict
        MODISL2Reader.read_all() 返回的数据字典
    qa_max : int
        最大允许的 QA 值

    Returns
    -------
    dict
        带有 'qa_mask' 键的过滤后数据
    """
    qa = data.get("qa")
    if qa is None:
        data["warnings"].append("无法过滤：缺少 QA 数据")
        return data

    qa_mask = qa <= qa_max
    data["qa_mask"] = qa_mask

    total = qa.size
    valid = np.sum(qa_mask)
    data["warnings"].append(
        f"QA 过滤: 保留 {valid}/{total} 有效像元 ({100*valid/total:.1f}%)"
    )

    return data


def get_yantai_region() -> Dict:
    """
    返回烟台近岸海域的默认区域范围

    Returns
    -------
    dict
        区域定义字典
    """
    return {
        "name": "烟台近岸整体",
        "lon_min": 120.9,
        "lon_max": 122.8,
        "lat_min": 36.1,
        "lat_max": 37.8,
        "description": "烟台近岸海域（参考区域，可根据影像实际覆盖调整）",
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python modis_l2_reader.py <MODIS_L2_file.nc_or.hdf>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"读取文件: {file_path}")

    try:
        with MODISL2Reader(file_path) as reader:
            data = reader.read_all()

        print(f"\n文件格式: {data['file_format']}")
        print(f"影像尺寸: {data['shape']}")
        print(f"找到波段: {data['bands_found']}")
        print(f"\n波段统计:")
        stats = reader.get_band_stats()
        for band, s in stats.items():
            print(f"  {band}: mean={s['mean']:.6f}, min={s['min']:.6f}, max={s['max']:.6f}, coverage={s['coverage']:.1%}")

        if data.get("lon") is not None:
            print(f"\n经度范围: {data['lon'].min():.4f} ~ {data['lon'].max():.4f}")
            print(f"纬度范围: {data['lat'].min():.4f} ~ {data['lat'].max():.4f}")

    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"读取错误: {e}")
        import traceback
        traceback.print_exc()
