"""
Data quality validation module.

This module provides comprehensive data quality checks for chlorophyll-a 
remote sensing datasets, including validation of data types, value ranges,
missing values, and statistical properties.

Functions:
    validate_rrs_bands: Validate remote sensing reflectance band values
    validate_chla_values: Validate chlorophyll-a concentration values
    validate_derived_features: Validate derived feature calculations
    validate_dataframe_schema: Validate DataFrame has expected schema
    generate_quality_report: Generate comprehensive data quality report
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional


REQUIRED_RRS_BANDS = [
    "Rrs_412", "Rrs_443", "Rrs_469", "Rrs_488",
    "Rrs_531", "Rrs_547", "Rrs_555", "Rrs_645",
    "Rrs_667", "Rrs_678"
]

DERIVED_FEATURE_PATTERNS = [
    "ratio_", "diff_", "sum_", "tri_"
]

RRS_BAND_RANGES = {
    "Rrs_412": (0.0, 0.05),
    "Rrs_443": (0.0, 0.06),
    "Rrs_469": (0.0, 0.08),
    "Rrs_488": (0.0, 0.10),
    "Rrs_531": (0.0, 0.08),
    "Rrs_547": (0.0, 0.07),
    "Rrs_555": (0.0, 0.07),
    "Rrs_645": (0.0, 0.04),
    "Rrs_667": (0.0, 0.03),
    "Rrs_678": (0.0, 0.03),
}


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self):
        self.passed = True
        self.warnings = []
        self.errors = []
        self.stats = {}
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.passed = False
    
    def add_stat(self, key: str, value: Any):
        self.stats[key] = value
    
    def summary(self) -> Dict:
        return {
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors,
            "stats": self.stats
        }


def validate_rrs_bands(df: pd.DataFrame) -> ValidationResult:
    """
    Validate remote sensing reflectance band values.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing Rrs band columns.
    
    Returns
    -------
    ValidationResult
        Validation result with any warnings or errors.
    """
    result = ValidationResult()
    
    for band in REQUIRED_RRS_BANDS:
        if band not in df.columns:
            result.add_error(f"Missing required band: {band}")
            continue
        
        col = df[band]
        
        if col.isnull().any():
            result.add_error(f"Band {band} contains null values")
        
        if (col < 0).any():
            result.add_error(f"Band {band} contains negative values")
        
        min_val, max_val = RRS_BAND_RANGES.get(band, (0, 0.1))
        if (col > max_val * 2).any():
            result.add_warning(f"Band {band} has unusually high values (>{max_val*2})")
        
        result.add_stat(f"{band}_mean", float(col.mean()))
        result.add_stat(f"{band}_std", float(col.std()))
    
    return result


def validate_chla_values(df: pd.DataFrame, 
                         min_val: float = 0.01, 
                         max_val: float = 100.0) -> ValidationResult:
    """
    Validate chlorophyll-a concentration values.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing 'chl_a' column.
    min_val : float, optional
        Minimum valid Chl-a value. Default is 0.01.
    max_val : float, optional
        Maximum valid Chl-a value. Default is 100.0.
    
    Returns
    -------
    ValidationResult
        Validation result with any warnings or errors.
    """
    result = ValidationResult()
    
    if "chl_a" not in df.columns:
        result.add_error("Missing required column: chl_a")
        return result
    
    chla = df["chl_a"]
    
    if chla.isnull().any():
        null_count = chla.isnull().sum()
        result.add_error(f"Chl-a contains {null_count} null values")
    
    if (chla <= 0).any():
        non_positive = (chla <= 0).sum()
        result.add_error(f"Chl-a contains {non_positive} non-positive values")
    
    if (chla > max_val).any():
        too_high = (chla > max_val).sum()
        result.add_warning(f"Chl-a contains {too_high} values exceeding {max_val}")
    
    if (chla < min_val).min() < min_val / 10:
        result.add_warning(f"Chl-a has values extremely close to zero")
    
    result.add_stat("chl_a_mean", float(chla.mean()))
    result.add_stat("chl_a_median", float(chla.median()))
    result.add_stat("chl_a_std", float(chla.std()))
    result.add_stat("chl_a_min", float(chla.min()))
    result.add_stat("chl_a_max", float(chla.max()))
    result.add_stat("chl_a_p25", float(chla.quantile(0.25)))
    result.add_stat("chl_a_p75", float(chla.quantile(0.75)))
    
    return result


def validate_derived_features(df: pd.DataFrame) -> ValidationResult:
    """
    Validate derived feature calculations.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing derived feature columns.
    
    Returns
    -------
    ValidationResult
        Validation result with any warnings or errors.
    """
    result = ValidationResult()
    
    derived_cols = [col for col in df.columns 
                   if any(col.startswith(pattern) for pattern in DERIVED_FEATURE_PATTERNS)]
    
    result.add_stat("derived_feature_count", len(derived_cols))
    
    for col in derived_cols:
        if df[col].isnull().any():
            result.add_warning(f"Derived feature {col} contains null values")
        
        if not np.isfinite(df[col]).all():
            result.add_error(f"Derived feature {col} contains infinite or NaN values")
        
        if (df[col] > 1e6).any() or (df[col] < -1e6).any():
            result.add_warning(f"Derived feature {col} has extreme values")
    
    return result


def validate_dataframe_schema(df: pd.DataFrame) -> ValidationResult:
    """
    Validate DataFrame has expected schema structure.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate.
    
    Returns
    -------
    ValidationResult
        Validation result with any warnings or errors.
    """
    result = ValidationResult()
    
    result.add_stat("n_rows", len(df))
    result.add_stat("n_columns", len(df.columns))
    result.add_stat("column_names", list(df.columns))
    
    missing_bands = [b for b in REQUIRED_RRS_BANDS if b not in df.columns]
    if missing_bands:
        result.add_warning(f"Missing optional RRS bands: {missing_bands}")
    
    if "chl_a" not in df.columns:
        result.add_error("Missing required column: chl_a")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric = [col for col in df.columns if col not in numeric_cols]
    if non_numeric:
        result.add_warning(f"Non-numeric columns: {non_numeric}")
    
    return result


def generate_quality_report(df: pd.DataFrame) -> Dict:
    """
    Generate comprehensive data quality report.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate.
    
    Returns
    -------
    Dict
        Comprehensive quality report with all validation results.
    
    Examples
    --------
    >>> df = pd.read_csv("samples.csv")
    >>> report = generate_quality_report(df)
    >>> print(report["schema"]["passed"])
    True
    """
    schema_result = validate_dataframe_schema(df)
    rrs_result = validate_rrs_bands(df)
    chla_result = validate_chla_values(df)
    derived_result = validate_derived_features(df)
    
    overall_passed = (
        schema_result.passed and 
        rrs_result.passed and 
        chla_result.passed and 
        derived_result.passed
    )
    
    return {
        "overall_passed": overall_passed,
        "schema": schema_result.summary(),
        "rrs_bands": rrs_result.summary(),
        "chla": chla_result.summary(),
        "derived_features": derived_result.summary()
    }


def print_quality_report(report: Dict) -> None:
    """
    Print formatted data quality report.
    
    Parameters
    ----------
    report : Dict
        Quality report from generate_quality_report.
    """
    print("=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)
    
    status = "✓ PASSED" if report["overall_passed"] else "✗ FAILED"
    print(f"\nOverall Status: {status}\n")
    
    for section in ["schema", "rrs_bands", "chla", "derived_features"]:
        section_data = report[section]
        print(f"--- {section.upper().replace('_', ' ')} ---")
        print(f"  Passed: {section_data['passed']}")
        
        if section_data.get("errors"):
            print(f"  Errors:")
            for err in section_data["errors"]:
                print(f"    - {err}")
        
        if section_data.get("warnings"):
            print(f"  Warnings:")
            for warn in section_data["warnings"]:
                print(f"    - {warn}")
        
        if section_data.get("stats"):
            print(f"  Stats: {len(section_data['stats'])} items")
        print()


if __name__ == "__main__":
    from src.preprocess import generate_mock_samples
    
    df = generate_mock_samples(n_samples=200, seed=42)
    report = generate_quality_report(df)
    print_quality_report(report)
