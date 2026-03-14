"""
Data preprocessing module for chlorophyll-a sample generation.

This module generates mock remote sensing reflectance (Rrs) data 
with derived features for machine learning model training.

Functions:
    generate_mock_samples: Generate synthetic Rrs and Chl-a samples
"""

from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLES_DIR = BASE_DIR / "data" / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def generate_mock_samples(n_samples: int = 500, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic remote sensing reflectance samples with Chl-a values.
    
    Parameters
    ----------
    n_samples : int, optional
        Number of samples to generate. Default is 500.
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
        - Target: chl_a (chlorophyll-a concentration in mg/m³)
    
    Examples
    --------
    >>> df = generate_mock_samples(n_samples=100, seed=123)
    >>> print(df.shape)
    (100, 22)
    """
    rng = np.random.default_rng(seed)

    data = pd.DataFrame({
        "Rrs_412": rng.uniform(0.001, 0.020, n_samples),
        "Rrs_443": rng.uniform(0.001, 0.025, n_samples),
        "Rrs_469": rng.uniform(0.001, 0.030, n_samples),
        "Rrs_488": rng.uniform(0.001, 0.035, n_samples),
        "Rrs_531": rng.uniform(0.001, 0.030, n_samples),
        "Rrs_547": rng.uniform(0.001, 0.028, n_samples),
        "Rrs_555": rng.uniform(0.001, 0.027, n_samples),
        "Rrs_645": rng.uniform(0.0005, 0.015, n_samples),
        "Rrs_667": rng.uniform(0.0005, 0.012, n_samples),
        "Rrs_678": rng.uniform(0.0005, 0.010, n_samples),
    })

    data["ratio_443_555"] = data["Rrs_443"] / (data["Rrs_555"] + 1e-6)
    data["ratio_488_555"] = data["Rrs_488"] / (data["Rrs_555"] + 1e-6)
    data["ratio_531_547"] = data["Rrs_531"] / (data["Rrs_547"] + 1e-6)
    data["ratio_443_488"] = data["Rrs_443"] / (data["Rrs_488"] + 1e-6)
    data["diff_488_555"] = data["Rrs_488"] - data["Rrs_555"]
    data["diff_555_645"] = data["Rrs_555"] - data["Rrs_645"]
    data["sum_443_488"] = data["Rrs_443"] + data["Rrs_488"]
    data["sum_555_645"] = data["Rrs_555"] + data["Rrs_645"]
    data["tri_443_488_555"] = data["Rrs_443"] - data["Rrs_488"] + data["Rrs_555"]
    data["tri_488_555_645"] = data["Rrs_488"] - data["Rrs_555"] + data["Rrs_645"]

    signal = (
        25 * data["Rrs_443"]
        + 30 * data["Rrs_488"]
        - 18 * data["Rrs_555"]
        + 10 * data["ratio_488_555"]
        + 6 * data["diff_488_555"]
    )

    noise = rng.normal(0, 0.35, n_samples)
    data["chl_a"] = np.clip(signal + noise + 2.0, 0.05, 8.0)

    return data

if __name__ == "__main__":
    df = generate_mock_samples()
    output_path = SAMPLES_DIR / "mock_rrs_chla_samples.csv"
    df.to_csv(output_path, index=False)
    print(f"Mock samples saved to: {output_path}")
    print(df.head())