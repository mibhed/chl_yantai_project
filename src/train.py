"""
Model training module for chlorophyll-a prediction.

This module provides functions for training and evaluating multiple machine learning 
models on remote sensing data to predict chlorophyll-a concentration.

Functions:
    rmse: Calculate Root Mean Square Error
    evaluate_model: Evaluate a model using cross-validation
    save_scatter_plot: Save observed vs predicted scatter plot
    save_error_histogram: Save prediction error histogram
    run_training: Run training for multiple models and generate reports

Supported Models:
    - MLR: Multiple Linear Regression with PCA
    - RF: Random Forest Regressor
    - GP: Gaussian Process Regressor
    - ET: Extra Trees Regressor
    - LGB: LightGBM (if available)
    - XGB: XGBoost (if available)
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from lightgbm import LGBMRegressor
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLES_PATH = BASE_DIR / "data" / "samples" / "mock_rrs_chla_samples.csv"
REPORT_DIR = BASE_DIR / "outputs" / "reports"
FIGURE_DIR = BASE_DIR / "outputs" / "figures"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))


def evaluate_model(name, pipeline, X, y, cv):
    y_pred = cross_val_predict(pipeline, X, y, cv=cv)
    result = {
        "model": name,
        "R2": round(r2_score(y, y_pred), 4),
        "RMSE": round(rmse(y, y_pred), 4),
        "Bias": round(float(np.mean(y_pred - y)), 4),
    }
    return result, y_pred


def save_scatter_plot(y_true, y_pred, model_name, output_path, dpi=200):
    plt.figure(figsize=(7, 6))
    plt.scatter(y_true, y_pred, alpha=0.65)
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], linestyle="--")
    plt.xlabel("Observed Chl-a")
    plt.ylabel("Predicted Chl-a")
    plt.title(f"{model_name} - Observed vs Predicted")
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()


def save_error_histogram(y_true, y_pred, model_name, output_path, dpi=200):
    errors = y_pred - y_true
    plt.figure(figsize=(7, 5))
    plt.hist(errors, bins=25)
    plt.xlabel("Prediction Error")
    plt.ylabel("Frequency")
    plt.title(f"{model_name} - Error Distribution")
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()


def run_training(df, report_dir=None, figure_dir=None, dpi=200):
    """Run multi-model training on a DataFrame with feature columns and 'chl_a' target.
    Optionally pass report_dir/figure_dir; defaults to module REPORT_DIR/FIGURE_DIR."""
    report_dir = report_dir or REPORT_DIR
    figure_dir = figure_dir or FIGURE_DIR
    report_dir = Path(report_dir)
    figure_dir = Path(figure_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    feature_cols = [col for col in df.columns if col != "chl_a"]
    X = df[feature_cols]
    y = df["chl_a"]

    cv = KFold(n_splits=10, shuffle=True, random_state=42)

    models = {
        "MLR": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", LinearRegression())
        ]),
        "RF": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", RandomForestRegressor(
                n_estimators=200,
                random_state=42,
                n_jobs=2
            ))
        ]),
        "GP": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", GaussianProcessRegressor(
                kernel=C(1.0) * RBF(length_scale=1.0),
                alpha=0.1,
                normalize_y=True,
                random_state=42
            ))
        ]),
        "ET": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", ExtraTreesRegressor(
                n_estimators=200,
                random_state=42,
                n_jobs=2
            ))
        ]),
    }

    if HAS_LGB:
        models["LGB"] = Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", LGBMRegressor(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=42,
                n_jobs=2,
                verbosity=-1
            ))
        ])

    if HAS_XGB:
        models["XGB"] = Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", XGBRegressor(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=42,
                n_jobs=2
            ))
        ])

    results = []
    predictions = {}

    for name, model in models.items():
        result, y_pred = evaluate_model(name, model, X, y, cv)
        results.append(result)
        predictions[name] = y_pred

    results_df = pd.DataFrame(results).sort_values(by="R2", ascending=False)
    output_csv = report_dir / "model_comparison.csv"
    results_df.to_csv(output_csv, index=False)

    best_model = results_df.iloc[0]["model"]
    best_pred = predictions[best_model]

    pred_df = pd.DataFrame({
        "observed": y,
        "predicted": best_pred
    })
    pred_df.to_csv(report_dir / "best_model_predictions.csv", index=False)

    save_scatter_plot(
        y_true=y.to_numpy(),
        y_pred=best_pred,
        model_name=best_model,
        output_path=figure_dir / "best_model_scatter.png",
        dpi=dpi
    )

    save_error_histogram(
        y_true=y.to_numpy(),
        y_pred=best_pred,
        model_name=best_model,
        output_path=figure_dir / "best_model_error_hist.png",
        dpi=dpi
    )

    print("Model comparison results:")
    print(results_df)
    print(f"\nSaved comparison table to: {output_csv}")
    print(f"Saved predictions to: {report_dir / 'best_model_predictions.csv'}")
    print(f"Saved scatter plot to: {figure_dir / 'best_model_scatter.png'}")
    print(f"Saved error histogram to: {figure_dir / 'best_model_error_hist.png'}")
    return results_df, pred_df, best_model


def train_single_model(df, model_name="RF", report_dir=None, figure_dir=None, dpi=200):
    """
    Train a single specified model and return the trained model.
    
    Parameters
    ----------
    df : pd.DataFrame
        Training data with features and 'chl_a' target column.
    model_name : str, optional
        Model name to train. Options: "MLR", "RF", "GP", "ET", "LGB", "XGB". Default is "RF".
    report_dir : Path, optional
        Directory to save reports. Defaults to REPORT_DIR.
    figure_dir : Path, optional
        Directory to save figures. Defaults to FIGURE_DIR.
    dpi : int, optional
        DPI for saved figures. Default is 200.
    
    Returns
    -------
    tuple
        (trained_pipeline, feature_cols)
    """
    report_dir = report_dir or REPORT_DIR
    figure_dir = figure_dir or FIGURE_DIR
    report_dir = Path(report_dir)
    figure_dir = Path(figure_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    feature_cols = [col for col in df.columns if col != "chl_a"]
    X = df[feature_cols]
    y = df["chl_a"]

    model_configs = {
        "MLR": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", LinearRegression())
        ]),
        "RF": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", RandomForestRegressor(
                n_estimators=200,
                random_state=42,
                n_jobs=2
            ))
        ]),
        "GP": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", GaussianProcessRegressor(
                kernel=C(1.0) * RBF(length_scale=1.0),
                alpha=0.1,
                normalize_y=True,
                random_state=42
            ))
        ]),
        "ET": Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", ExtraTreesRegressor(
                n_estimators=200,
                random_state=42,
                n_jobs=2
            ))
        ]),
    }

    if HAS_LGB:
        model_configs["LGB"] = Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", LGBMRegressor(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=42,
                n_jobs=2,
                verbosity=-1
            ))
        ])

    if HAS_XGB:
        model_configs["XGB"] = Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=min(16, X.shape[1]))),
            ("model", XGBRegressor(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=42,
                n_jobs=2
            ))
        ])

    if model_name not in model_configs:
        raise ValueError(f"Model {model_name} not available. Available: {list(model_configs.keys())}")

    pipeline = model_configs[model_name]
    pipeline.fit(X, y)
    
    return pipeline, feature_cols


def main():
    df = pd.read_csv(SAMPLES_PATH)
    run_training(df)


if __name__ == "__main__":
    main()