"""
Unit tests for chl_yantai_project core modules.

This test suite covers:
- preprocess.py: Sample generation
- train.py: Model training and evaluation
- analysis.py: Spatial analysis and visualization
- config.py: Configuration management
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.preprocess import generate_mock_samples
from src.config import (
    BASE_DIR, DATA_DIR, RAW_DIR, PROCESSED_DIR, SAMPLES_DIR,
    SRC_DIR, APP_DIR, OUTPUT_DIR, FIGURES_DIR, MAPS_DIR, REPORTS_DIR
)


class TestPreprocess:
    """Tests for data preprocessing module."""

    def test_generate_mock_samples_default(self):
        """Test default sample generation."""
        df = generate_mock_samples()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 500
        assert "chl_a" in df.columns

    def test_generate_mock_samples_custom_size(self):
        """Test sample generation with custom size."""
        df = generate_mock_samples(n_samples=100, seed=123)
        assert len(df) == 100
        assert isinstance(df, pd.DataFrame)

    def test_generate_mock_samples_has_required_columns(self):
        """Test that generated data has required Rrs columns."""
        df = generate_mock_samples()
        expected_cols = [
            "Rrs_412", "Rrs_443", "Rrs_469", "Rrs_488", "Rrs_531",
            "Rrs_547", "Rrs_555", "Rrs_645", "Rrs_667", "Rrs_678"
        ]
        for col in expected_cols:
            assert col in df.columns

    def test_generate_mock_samples_has_derived_features(self):
        """Test that derived features are created."""
        df = generate_mock_samples()
        derived_cols = [
            "ratio_443_555", "ratio_488_555", "ratio_531_547",
            "ratio_443_488", "diff_488_555", "diff_555_645"
        ]
        for col in derived_cols:
            assert col in df.columns

    def test_chla_range_valid(self):
        """Test that Chl-a values are within valid range."""
        df = generate_mock_samples()
        assert df["chl_a"].min() >= 0.05
        assert df["chl_a"].max() <= 8.0
        assert df["chl_a"].notna().all()

    def test_no_null_values(self):
        """Test that generated data has no null values."""
        df = generate_mock_samples()
        assert df.isnull().sum().sum() == 0


class TestConfig:
    """Tests for configuration module."""

    def test_base_dir_exists(self):
        """Test that BASE_DIR is correctly set."""
        assert BASE_DIR.exists()
        assert BASE_DIR.name == "chl_yantai_project"

    def test_data_dirs_exist(self):
        """Test that data directories are defined."""
        assert DATA_DIR.exists()
        assert isinstance(DATA_DIR, Path)

    def test_output_dirs_exist(self):
        """Test that output directories are defined and created."""
        assert OUTPUT_DIR.exists()
        assert FIGURES_DIR.exists()
        assert MAPS_DIR.exists()
        assert REPORTS_DIR.exists()

    def test_dir_structure(self):
        """Test that expected directory structure exists."""
        assert (BASE_DIR / "src").exists()
        assert (BASE_DIR / "app").exists()
        assert (BASE_DIR / "data").exists()


class TestTrain:
    """Tests for model training module."""

    def test_train_module_imports(self):
        """Test that train module can be imported."""
        from src import train
        assert hasattr(train, "run_training")
        assert hasattr(train, "rmse")

    def test_rmse_function(self):
        """Test RMSE calculation."""
        from src.train import rmse
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.0, 2.9, 4.2, 4.8])
        result = rmse(y_true, y_pred)
        assert isinstance(result, (float, np.floating))
        assert result >= 0

    def test_run_training_with_sample_data(self):
        """Test training run with sample data."""
        from src.train import run_training
        df = generate_mock_samples(n_samples=100, seed=42)
        results_df, pred_df, best_model = run_training(df, report_dir=REPORTS_DIR, figure_dir=FIGURES_DIR)
        assert isinstance(results_df, pd.DataFrame)
        assert isinstance(pred_df, pd.DataFrame)
        assert best_model in ["MLR", "RF", "GP", "ET", "LGB", "XGB"]
        assert "R2" in results_df.columns
        assert "RMSE" in results_df.columns

    def test_model_comparison_output(self):
        """Test that model comparison CSV is generated."""
        from src.train import run_training
        df = generate_mock_samples(n_samples=50, seed=99)
        run_training(df, report_dir=REPORTS_DIR, figure_dir=FIGURES_DIR)
        comparison_path = REPORTS_DIR / "model_comparison.csv"
        assert comparison_path.exists()
        df_compare = pd.read_csv(comparison_path)
        assert len(df_compare) > 0


class TestAnalysis:
    """Tests for analysis module."""

    def test_analysis_module_imports(self):
        """Test that analysis module can be imported."""
        from src import analysis
        assert hasattr(analysis, "generate_mock_chla_grid")
        assert hasattr(analysis, "save_mock_map")
        assert hasattr(analysis, "summarize_grid")

    def test_regions_json_exists(self):
        """Test that regions configuration exists."""
        regions_path = PROCESSED_DIR / "regions.json"
        assert regions_path.exists()

    def test_generate_mock_chla_grid(self):
        """Test mock Chl-a grid generation."""
        from src.analysis import generate_mock_chla_grid
        lon, lat, chl = generate_mock_chla_grid("烟台近岸整体", 2025, 6)
        assert lon.shape == lat.shape
        assert lon.shape == chl.shape
        assert chl.min() >= 0
        assert chl.max() <= 10

    def test_generate_mock_chla_grid_different_regions(self):
        """Test grid generation for different regions."""
        from src.analysis import generate_mock_chla_grid
        regions = ["烟台近岸整体", "芝罘湾", "四十里湾", "养马岛附近"]
        for region in regions:
            lon, lat, chl = generate_mock_chla_grid(region, 2025, 1)
            assert lon.shape == chl.shape

    def test_summarize_grid(self):
        """Test grid summarization."""
        from src.analysis import generate_mock_chla_grid, summarize_grid
        lon, lat, chl = generate_mock_chla_grid("芝罘湾", 2024, 3)
        summary = summarize_grid("芝罘湾", 2024, 3, chl)
        assert "mean_chl_a" in summary
        assert "max_chl_a" in summary
        assert "min_chl_a" in summary
        assert "std_chl_a" in summary
        assert summary["region"] == "芝罘湾"
        assert summary["year"] == 2024
        assert summary["month"] == 3


class TestDataQuality:
    """Tests for data quality validation."""

    def test_sample_data_quality(self):
        """Test quality of generated sample data."""
        df = generate_mock_samples(n_samples=200, seed=42)
        
        assert df.shape[0] > 0
        assert df.shape[1] > 10
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        assert len(numeric_cols) == df.shape[1]
        
        for col in numeric_cols:
            assert df[col].isna().sum() == 0, f"Column {col} has null values"
            assert np.isfinite(df[col]).all(), f"Column {col} has infinite values"

    def test_rrs_bands_positive(self):
        """Test that Rrs band values are positive."""
        df = generate_mock_samples(n_samples=100, seed=42)
        rrs_cols = [col for col in df.columns if col.startswith("Rrs_")]
        for col in rrs_cols:
            assert (df[col] > 0).all(), f"Column {col} has non-positive values"

    def test_ratio_features_valid(self):
        """Test that ratio features are valid."""
        df = generate_mock_samples(n_samples=100, seed=42)
        ratio_cols = [col for col in df.columns if col.startswith("ratio_")]
        for col in ratio_cols:
            assert np.isfinite(df[col]).all(), f"Ratio column {col} has invalid values"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
