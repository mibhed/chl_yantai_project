"""
Spatial analysis module for chlorophyll-a visualization.

This module generates mock spatial data for chlorophyll-a concentration,
creates visualizations, and produces statistical summaries for different 
regions and time periods.

Functions:
    load_regions: Load region definitions from JSON configuration
    generate_mock_chla_grid: Generate mock Chl-a concentration grid
    save_mock_map: Save spatial distribution map as PNG image
    summarize_grid: Calculate statistics for a grid
    save_single_summary: Save single month summary to CSV
    generate_monthly_series: Generate monthly time series for a region
    generate_multi_region_series: Generate multi-region comparison data
    generate_multi_year_series: Generate multi-year time series for a region
    generate_annual_summary: Generate annual statistical summary

Supported Regions:
    - 烟台近岸整体 (Yantai Nearshore Overall)
    - 芝罘湾 (Zhifu Bay)
    - 四十里湾 (Sishili Bay)
    - 养马岛附近 (Near Yangma Island)
"""

from pathlib import Path
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parents[1]
REGION_PATH = BASE_DIR / "data" / "processed" / "regions.json"
MAP_DIR = BASE_DIR / "outputs" / "maps"
REPORT_DIR = BASE_DIR / "outputs" / "reports"

MAP_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_regions():
    with open(REGION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_mock_chla_grid(region_name: str, year: int, month: int, nx: int = 120, ny: int = 100):
    regions = load_regions()
    region = regions[region_name]

    lon = np.linspace(region["lon_min"], region["lon_max"], nx)
    lat = np.linspace(region["lat_min"], region["lat_max"], ny)
    lon_grid, lat_grid = np.meshgrid(lon, lat)

    lon_center = (region["lon_min"] + region["lon_max"]) / 2
    lat_center = (region["lat_min"] + region["lat_max"]) / 2

    seasonal_factor = 1.0 + 0.25 * np.sin((month - 1) / 12 * 2 * np.pi)
    yearly_factor = 1.0 + 0.03 * (year - 2020)

    region_bias_map = {
        "烟台近岸整体": 0.15,
        "芝罘湾": 0.35,
        "四十里湾": 0.25,
        "养马岛附近": 0.10,
    }
    region_bias = region_bias_map.get(region_name, 0.0)

    hotspot1 = np.exp(-(((lon_grid - lon_center) ** 2) / 0.02 + ((lat_grid - lat_center) ** 2) / 0.01))
    hotspot2 = np.exp(-(((lon_grid - (lon_center + 0.12)) ** 2) / 0.01 + ((lat_grid - (lat_center - 0.08)) ** 2) / 0.02))
    gradient = 0.8 * (lat_grid - region["lat_min"]) / (region["lat_max"] - region["lat_min"])

    rng = np.random.default_rng(seed=year * 100 + month + abs(hash(region_name)) % 1000)
    noise = rng.normal(0, 0.08, size=lon_grid.shape)

    chl = (
        1.5
        + 2.0 * hotspot1
        + 1.2 * hotspot2
        + gradient
        + region_bias
    ) * seasonal_factor * yearly_factor + noise

    chl = np.clip(chl, 0.05, 8.0)
    return lon_grid, lat_grid, chl


def save_mock_map(region_name: str, year: int, month: int, dpi: int = 200):
    lon_grid, lat_grid, chl = generate_mock_chla_grid(region_name, year, month)
    output_path = MAP_DIR / f"mock_chla_map_{region_name}_{year}_{month:02d}.png"

    plt.figure(figsize=(8, 6))
    mesh = plt.pcolormesh(lon_grid, lat_grid, chl, shading="auto")
    plt.colorbar(mesh, label="Chl-a (mg/m³)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title(f"{region_name} {year}-{month:02d} 模拟叶绿素a空间分布")
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()

    return output_path, chl


def summarize_grid(region_name: str, year: int, month: int, chl: np.ndarray):
    return {
        "region": region_name,
        "year": year,
        "month": month,
        "mean_chl_a": round(float(np.mean(chl)), 4),
        "max_chl_a": round(float(np.max(chl)), 4),
        "min_chl_a": round(float(np.min(chl)), 4),
        "std_chl_a": round(float(np.std(chl)), 4),
    }


def save_single_summary(region_name: str, year: int, month: int, summary: dict, model: str = ""):
    """
    Save single month summary to CSV with optional model parameter.
    
    Parameters
    ----------
    region_name : str
        Region name.
    year : int
        Year.
    month : int
        Month.
    summary : dict
        Summary dictionary.
    model : str, optional
        Model name for filename. Default is "".
    
    Returns
    -------
    Path
        Output file path.
    """
    if model:
        output_path = REPORT_DIR / f"summary_{region_name}_{year}_{month:02d}_{model}.csv"
    else:
        output_path = REPORT_DIR / f"summary_{region_name}_{year}_{month:02d}.csv"
    pd.DataFrame([summary]).to_csv(output_path, index=False)
    return output_path


def generate_monthly_series(region_name: str, year: int):
    rows = []
    for month in range(1, 13):
        _, _, chl = generate_mock_chla_grid(region_name, year, month)
        rows.append({
            "region": region_name,
            "year": year,
            "month": month,
            "mean_chl_a": round(float(np.mean(chl)), 4),
            "max_chl_a": round(float(np.max(chl)), 4),
            "min_chl_a": round(float(np.min(chl)), 4),
            "std_chl_a": round(float(np.std(chl)), 4),
        })

    df = pd.DataFrame(rows)
    output_path = REPORT_DIR / f"monthly_series_{region_name}_{year}.csv"
    df.to_csv(output_path, index=False)
    return output_path, df


def generate_multi_region_series(year: int):
    regions = list(load_regions().keys())
    rows = []

    for region_name in regions:
        for month in range(1, 13):
            _, _, chl = generate_mock_chla_grid(region_name, year, month)
            rows.append({
                "region": region_name,
                "year": year,
                "month": month,
                "mean_chl_a": round(float(np.mean(chl)), 4),
                "max_chl_a": round(float(np.max(chl)), 4),
                "min_chl_a": round(float(np.min(chl)), 4),
                "std_chl_a": round(float(np.std(chl)), 4),
            })

    df = pd.DataFrame(rows)
    output_path = REPORT_DIR / f"multi_region_series_{year}.csv"
    df.to_csv(output_path, index=False)
    return output_path, df


def generate_multi_year_series(region_name: str, start_year: int = 2020, end_year: int = 2025):
    rows = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            _, _, chl = generate_mock_chla_grid(region_name, year, month)
            rows.append({
                "region": region_name,
                "year": year,
                "month": month,
                "mean_chl_a": round(float(np.mean(chl)), 4),
                "max_chl_a": round(float(np.max(chl)), 4),
                "min_chl_a": round(float(np.min(chl)), 4),
                "std_chl_a": round(float(np.std(chl)), 4),
            })

    df = pd.DataFrame(rows)
    output_path = REPORT_DIR / f"multi_year_series_{region_name}_{start_year}_{end_year}.csv"
    df.to_csv(output_path, index=False)
    return output_path, df


def generate_annual_summary(region_name: str, year: int, monthly_df: pd.DataFrame, model: str = ""):
    """
    Generate annual statistical summary with optional model parameter.
    
    Parameters
    ----------
    region_name : str
        Region name.
    year : int
        Year.
    monthly_df : pd.DataFrame
        Monthly statistics DataFrame.
    model : str, optional
        Model name for filename. Default is "".
    
    Returns
    -------
    tuple
        (output_path, DataFrame) with annual summary.
    """
    max_row = monthly_df.loc[monthly_df["mean_chl_a"].idxmax()]
    min_row = monthly_df.loc[monthly_df["mean_chl_a"].idxmin()]

    summary = pd.DataFrame([{
        "region": region_name,
        "year": year,
        "annual_mean_chl_a": round(float(monthly_df["mean_chl_a"].mean()), 4),
        "annual_max_monthly_mean": round(float(monthly_df["mean_chl_a"].max()), 4),
        "annual_min_monthly_mean": round(float(monthly_df["mean_chl_a"].min()), 4),
        "peak_month": int(max_row["month"]),
        "lowest_month": int(min_row["month"]),
    }])

    if model:
        output_path = REPORT_DIR / f"annual_summary_{region_name}_{year}_{model}.csv"
    else:
        output_path = REPORT_DIR / f"annual_summary_{region_name}_{year}.csv"
    summary.to_csv(output_path, index=False)
    return output_path, summary


def generate_chla_grid_with_model(pipeline, feature_cols, region_name: str, year: int, month: int, nx: int = 120, ny: int = 100):
    """
    Generate Chl-a concentration grid using trained model predictions.
    
    Parameters
    ----------
    pipeline : sklearn.pipeline.Pipeline
        Trained model pipeline.
    feature_cols : list
        List of feature column names.
    region_name : str
        Region name for spatial context.
    year : int
        Year for seasonal/yearly factors.
    month : int
        Month for seasonal factors.
    nx : int, optional
        Number of grid points in longitude direction. Default is 120.
    ny : int, optional
        Number of grid points in latitude direction. Default is 100.
    
    Returns
    -------
    tuple
        (lon_grid, lat_grid, chl_grid) where chl_grid is model-predicted Chl-a values.
    """
    regions = load_regions()
    region = regions[region_name]

    lon = np.linspace(region["lon_min"], region["lon_max"], nx)
    lat = np.linspace(region["lat_min"], region["lat_max"], ny)
    lon_grid, lat_grid = np.meshgrid(lon, lat)

    lon_center = (region["lon_min"] + region["lon_max"]) / 2
    lat_center = (region["lat_min"] + region["lat_max"]) / 2

    seasonal_factor = 1.0 + 0.25 * np.sin((month - 1) / 12 * 2 * np.pi)
    yearly_factor = 1.0 + 0.03 * (year - 2020)

    region_bias_map = {
        "烟台近岸整体": 0.15,
        "芝罘湾": 0.35,
        "四十里湾": 0.25,
        "养马岛附近": 0.10,
    }
    region_bias = region_bias_map.get(region_name, 0.0)

    hotspot1 = np.exp(-(((lon_grid - lon_center) ** 2) / 0.02 + ((lat_grid - lat_center) ** 2) / 0.01))
    hotspot2 = np.exp(-(((lon_grid - (lon_center + 0.12)) ** 2) / 0.01 + ((lat_grid - (lat_center - 0.08)) ** 2) / 0.02))
    gradient = 0.8 * (lat_grid - region["lat_min"]) / (region["lat_max"] - region["lat_min"])

    rng = np.random.default_rng(seed=year * 100 + month + abs(hash(region_name)) % 1000)
    noise = rng.normal(0, 0.08, size=lon_grid.shape)

    chl_base = (
        1.5
        + 2.0 * hotspot1
        + 1.2 * hotspot2
        + gradient
        + region_bias
    ) * seasonal_factor * yearly_factor

    chl_base_flat = chl_base.flatten()
    
    feature_data = {}
    for i, band in enumerate(["Rrs_412", "Rrs_443", "Rrs_469", "Rrs_488", "Rrs_531", "Rrs_547", "Rrs_555", "Rrs_645", "Rrs_667", "Rrs_678"]):
        base_value = 0.005 + 0.015 * (i / 9.0)
        feature_data[band] = (base_value * chl_base_flat * 0.3 + np.random.default_rng(42).normal(base_value, 0.002, len(chl_base_flat)))
    
    for i, band in enumerate(["Rrs_412", "Rrs_443", "Rrs_469", "Rrs_488", "Rrs_531", "Rrs_547", "Rrs_555", "Rrs_645", "Rrs_667", "Rrs_678"]):
        feature_data[f"ratio_{band.split('_')[1]}_555"] = feature_data[band] / (feature_data["Rrs_555"] + 1e-6)
    
    feature_df = pd.DataFrame(feature_data)
    
    available_cols = [col for col in feature_cols if col in feature_df.columns]
    if len(available_cols) < len(feature_cols):
        for col in feature_cols:
            if col not in feature_df.columns:
                feature_df[col] = 0.0
    
    X = feature_df[feature_cols]
    chl_pred = pipeline.predict(X)
    
    chl_grid = chl_pred.reshape(ny, nx)
    chl_grid = chl_grid + noise
    chl_grid = np.clip(chl_grid, 0.05, 8.0)
    
    return lon_grid, lat_grid, chl_grid


def generate_monthly_series_with_model(pipeline, feature_cols, region_name: str, year: int, model: str = ""):
    """
    Generate monthly time series using model predictions.
    
    Parameters
    ----------
    pipeline : sklearn.pipeline.Pipeline
        Trained model pipeline.
    feature_cols : list
        List of feature column names.
    region_name : str
        Region name.
    year : int
        Year.
    model : str, optional
        Model name for filename. Default is "".
    
    Returns
    -------
    tuple
        (output_path, DataFrame) with monthly statistics.
    """
    rows = []
    for month in range(1, 13):
        _, _, chl = generate_chla_grid_with_model(pipeline, feature_cols, region_name, year, month)
        rows.append({
            "region": region_name,
            "year": year,
            "month": month,
            "mean_chl_a": round(float(np.mean(chl)), 4),
            "max_chl_a": round(float(np.max(chl)), 4),
            "min_chl_a": round(float(np.min(chl)), 4),
            "std_chl_a": round(float(np.std(chl)), 4),
        })

    df = pd.DataFrame(rows)
    if model:
        output_path = REPORT_DIR / f"monthly_series_{region_name}_{year}_{model}.csv"
    else:
        output_path = REPORT_DIR / f"monthly_series_{region_name}_{year}.csv"
    df.to_csv(output_path, index=False)
    return output_path, df


def generate_multi_region_series_with_model(pipeline, feature_cols, year: int, model: str = ""):
    """
    Generate multi-region comparison using model predictions.
    
    Parameters
    ----------
    pipeline : sklearn.pipeline.Pipeline
        Trained model pipeline.
    feature_cols : list
        List of feature column names.
    year : int
        Year.
    model : str, optional
        Model name for filename. Default is "".
    
    Returns
    -------
    tuple
        (output_path, DataFrame) with multi-region statistics.
    """
    regions = list(load_regions().keys())
    rows = []

    for region_name in regions:
        for month in range(1, 13):
            _, _, chl = generate_chla_grid_with_model(pipeline, feature_cols, region_name, year, month)
            rows.append({
                "region": region_name,
                "year": year,
                "month": month,
                "mean_chl_a": round(float(np.mean(chl)), 4),
                "max_chl_a": round(float(np.max(chl)), 4),
                "min_chl_a": round(float(np.min(chl)), 4),
                "std_chl_a": round(float(np.std(chl)), 4),
            })

    df = pd.DataFrame(rows)
    if model:
        output_path = REPORT_DIR / f"multi_region_series_{year}_{model}.csv"
    else:
        output_path = REPORT_DIR / f"multi_region_series_{year}.csv"
    df.to_csv(output_path, index=False)
    return output_path, df


def generate_multi_year_series_with_model(pipeline, feature_cols, region_name: str, start_year: int = 2020, end_year: int = 2025, model: str = ""):
    """
    Generate multi-year time series using model predictions.
    
    Parameters
    ----------
    pipeline : sklearn.pipeline.Pipeline
        Trained model pipeline.
    feature_cols : list
        List of feature column names.
    region_name : str
        Region name.
    start_year : int, optional
        Start year. Default is 2020.
    end_year : int, optional
        End year. Default is 2025.
    model : str, optional
        Model name for filename. Default is "".
    
    Returns
    -------
    tuple
        (output_path, DataFrame) with multi-year statistics.
    """
    rows = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            _, _, chl = generate_chla_grid_with_model(pipeline, feature_cols, region_name, year, month)
            rows.append({
                "region": region_name,
                "year": year,
                "month": month,
                "mean_chl_a": round(float(np.mean(chl)), 4),
                "max_chl_a": round(float(np.max(chl)), 4),
                "min_chl_a": round(float(np.min(chl)), 4),
                "std_chl_a": round(float(np.std(chl)), 4),
            })

    df = pd.DataFrame(rows)
    if model:
        output_path = REPORT_DIR / f"multi_year_series_{region_name}_{start_year}_{end_year}_{model}.csv"
    else:
        output_path = REPORT_DIR / f"multi_year_series_{region_name}_{start_year}_{end_year}.csv"
    df.to_csv(output_path, index=False)
    return output_path, df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", type=str, default="烟台近岸整体")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--month", type=int, default=7)
    args = parser.parse_args()

    map_path, chl = save_mock_map(args.region, args.year, args.month)
    summary = summarize_grid(args.region, args.year, args.month, chl)
    summary_path = save_single_summary(args.region, args.year, args.month, summary)
    monthly_path, monthly_df = generate_monthly_series(args.region, args.year)
    multi_region_path, multi_region_df = generate_multi_region_series(args.year)
    multi_year_path, multi_year_df = generate_multi_year_series(args.region, 2020, 2025)
    annual_summary_path, annual_summary_df = generate_annual_summary(args.region, args.year, monthly_df)

    print(f"Mock map saved to: {map_path}")
    print(f"Single summary saved to: {summary_path}")
    print(f"Monthly series saved to: {monthly_path}")
    print(f"Multi-region series saved to: {multi_region_path}")
    print(f"Multi-year series saved to: {multi_year_path}")
    print(f"Annual summary saved to: {annual_summary_path}")

    print("\nCurrent month summary:")
    print(pd.DataFrame([summary]))
    print("\nAnnual summary:")
    print(annual_summary_df)


if __name__ == "__main__":
    main()