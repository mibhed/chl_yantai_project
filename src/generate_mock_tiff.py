"""
生成模拟 MODIS L2 影像（GeoTIFF 格式），用于测试 Chl-a 反演流程。

输出文件：
  data/raw/mock_modis_yantai_20240315.tif
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
  - Band 11 : QA (0=best, 1=good, 2=margin, 3=cloud)
  - Band 12 : lon
  - Band 13 : lat

地理范围：烟台近岸海域
  纬度：36.5°N ~ 37.5°N
  经度：120.5°E ~ 121.5°E
  分辨率：~0.001°/px（约 110m）

同时保存同名的 .json 元数据文件。
"""

import numpy as np
from pathlib import Path
from datetime import date

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ROWS, COLS = 400, 400          # 影像尺寸
LAT_MIN, LAT_MAX = 36.5, 37.5  # 纬度范围
LON_MIN, LON_MAX = 120.5, 121.5  # 经度范围
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_PATH.mkdir(parents=True, exist_ok=True)
TIFF_NAME = "mock_modis_yantai_20240315.tif"
JSON_NAME = "mock_modis_yantai_20240315.json"

# MODIS Ocean Color 波段中心波长（μm）
BANDS = ["Rrs_412", "Rrs_443", "Rrs_469", "Rrs_488",
         "Rrs_531", "Rrs_547", "Rrs_555",
         "Rrs_645", "Rrs_667", "Rrs_678"]

# 各波段对 Chl-a 的相对响应系数（蓝波段随 Chl↑ 而↓，绿红随 Chl↑ 而↑）
# OC3-type 经验系数
BAND_WEIGHTS = {
    "Rrs_412": -0.5,
    "Rrs_443": -0.6,
    "Rrs_469": -0.4,
    "Rrs_488": -0.2,
    "Rrs_531":  0.3,
    "Rrs_547":  0.5,
    "Rrs_555":  0.6,
    "Rrs_645":  0.8,
    "Rrs_667":  0.9,
    "Rrs_678":  1.0,
}

# 各波段背景均值（Rrs，sr^-1）
BAND_BASE = {
    "Rrs_412": 0.010,
    "Rrs_443": 0.012,
    "Rrs_469": 0.013,
    "Rrs_488": 0.014,
    "Rrs_531": 0.008,
    "Rrs_547": 0.007,
    "Rrs_555": 0.006,
    "Rrs_645": 0.003,
    "Rrs_667": 0.002,
    "Rrs_678": 0.001,
}


def make_grid(rows, cols, lat_min, lat_max, lon_min, lon_max):
    """生成经纬度网格"""
    lat = np.linspace(lat_max, lat_min, rows)[ :, np.newaxis] + \
          np.zeros(cols)
    lon = np.zeros((rows, cols)) + \
          np.linspace(lon_min, lon_max, cols)[np.newaxis, :]
    return lon.astype(np.float32), lat.astype(np.float32)


def make_chl_pattern(rows, cols):
    """
    生成空间 Chl-a 分布图（mg/m³）。
    模拟近岸高浓度、河口羽状锋、离岸递减的自然格局。
    """
    rng = np.random.default_rng(2026)

    # 基础梯度：离岸距离（沿列方向，col 越大越靠近外海）
    offshore = np.linspace(0, 1, cols)[np.newaxis, :] ** 0.7
    chl = (12.0 - 9.0 * offshore).astype(np.float32)  # (rows=1, cols)
    # 广播到完整尺寸
    chl = np.broadcast_to(chl, (rows, cols)).copy()

    # 河口羽状锋（中部偏左，约 col=120 处）
    plume_width = 80
    plume_center = 120
    plume = np.exp(-((np.arange(cols) - plume_center) / plume_width) ** 2) * 4.0
    chl = chl + plume[np.newaxis, :]  # (rows, cols)

    # 局部斑块/高值区（随机）
    rng_local = np.random.default_rng(99)
    for _ in range(5):
        pr = rng_local.integers(rows // 4, rows * 3 // 4)
        pc = rng_local.integers(cols // 4, cols * 3 // 4)
        amp = rng_local.uniform(2, 5)
        rad = rng_local.uniform(20, 50)
        y = np.arange(rows)[:, None] - pr     # (rows, 1)
        x = np.arange(cols)[None, :] - pc     # (1, cols)
        mask = (y ** 2 + x ** 2) < rad ** 2  # (rows, cols)
        chl[mask] += amp

    # 噪声（< 10% 相对误差）
    noise = rng.normal(0, 0.3, (rows, cols))
    chl = chl + noise * (chl * 0.08)
    return np.clip(chl, 0.5, 25.0).astype(np.float32)


def rrs_from_chl(chl, band):
    """从 Chl-a 估算 Rrs（经验近似）"""
    w = BAND_WEIGHTS[band]
    base = BAND_BASE[band]
    # 对数响应 + 随机扰动
    log_ratio = w * np.log10(chl + 0.1)
    rrs = base * 10 ** (log_ratio * 0.5)
    # 加一点空间相关噪声
    rng = np.random.default_rng(hash(band) & 0xffffffff)
    rrs = rrs * (1 + rng.normal(0, 0.05, rrs.shape))
    return np.clip(rrs, 0.0001, 0.05).astype(np.float32)


def make_qa(rows, cols, chl):
    """生成 QA 波段：沿岸高值斑块=cloud（3），其余=good（0~1）"""
    rng = np.random.default_rng(7)
    qa = np.ones((rows, cols), dtype=np.float32)  # 默认 good

    # 云/无效斑块（占 8~15%）
    rng_qa = np.random.default_rng(7)
    for _ in range(12):
        cr = rng_qa.integers(0, rows)
        cc = rng_qa.integers(0, cols)
        rad = rng_qa.integers(8, 35)
        y = np.arange(rows)[:, None] - cr
        x = np.arange(cols)[None, :] - cc
        mask = (y ** 2 + x ** 2) < rad ** 2
        qa[mask] = 3.0

    # 近岸边缘（列<5）设为 best（0）
    qa[:, :5] = 0.0
    return qa


def write_geotiff(path, arrays, transform, crs="EPSG:4326"):
    """写入多波段 GeoTIFF"""
    import rasterio
    from rasterio.transform import from_bounds

    h, w = arrays[0].shape
    metadata = {
        "driver": "GTiff",
        "height": h,
        "width": w,
        "count": len(arrays),
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": -9999.0,
        "compress": "deflate",
    }

    with rasterio.open(path, "w", **metadata) as dst:
        for i, arr in enumerate(arrays, 1):
            data = arr.copy().astype(np.float32)
            bad = ~np.isfinite(data)
            data[bad] = -9999.0
            dst.write(data, i)

    print(f"  GeoTIFF 已写入: {path}  ({w}×{h}×{len(arrays)} bands)")


def main():
    print("=" * 60)
    print("生成模拟 MODIS L2 影像（烟台近岸，2024-03-15）")
    print("=" * 60)

    rows, cols = ROWS, COLS
    lon, lat = make_grid(rows, cols, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX)

    # Chl-a 空间分布
    print("  生成 Chl-a 空间分布...")
    chl = make_chl_pattern(rows, cols)

    # Rrs 波段
    print("  生成 Rrs 波段...")
    rrs_arrays = {}
    for band in BANDS:
        rrs_arrays[band] = rrs_from_chl(chl, band)

    # QA
    print("  生成 QA 波段...")
    qa = make_qa(rows, cols, chl)

    # 组装所有波段
    all_arrays = [rrs_arrays[b] for b in BANDS] + [qa, lon, lat]

    # 地理变换
    import rasterio.transform as rt
    transform = rt.from_bounds(LON_MIN, LAT_MIN, LON_MAX, LAT_MAX, cols, rows)

    # 写入 GeoTIFF
    tiff_path = OUT_PATH / TIFF_NAME
    write_geotiff(tiff_path, all_arrays, transform)

    # 统计摘要
    valid = chl[chl > 0]
    print(f"\n  Chl-a 统计: 均值={valid.mean():.2f}  最大={valid.max():.2f}  mg/m³")
    print(f"  云/无效覆盖率: {(qa >= 3).sum() / qa.size * 100:.1f}%")

    # 写入 JSON 元数据
    import json
    meta = {
        "satellite": "MODIS",
        "sensor": "SeaWiFS/MODIS",
        "product": "mock_L2",
        "date": "2024-03-15",
        "bounds": {
            "lat_min": LAT_MIN, "lat_max": LAT_MAX,
            "lon_min": LON_MIN, "lon_max": LON_MAX,
        },
        "shape": [rows, cols],
        "bands": {
            **{b: i + 1 for i, b in enumerate(BANDS)},
            "qa": len(BANDS) + 1,
            "lon": len(BANDS) + 2,
            "lat": len(BANDS) + 3,
        },
        "note": "模拟数据，用于测试 Chl-a 反演流程",
    }
    json_path = OUT_PATH / JSON_NAME
    json_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"  元数据已写入: {json_path}")

    print("\n  可用 rasterio 读取测试:")
    print(f"  >>> import rasterio")
    print(f"  >>> with rasterio.open('{tiff_path}') as src:")
    print(f"  ...     rrs_555 = src.read(7)   # Band 7 = Rrs_555")
    print(f"  ...     lon = src.read({len(BANDS)+2})   # Band {len(BANDS)+2} = lon")
    print(f"  ...     lat = src.read({len(BANDS)+3})   # Band {len(BANDS)+3} = lat")
    print()
    print("✅ 完成！")


if __name__ == "__main__":
    main()
