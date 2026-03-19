"""
模型管理模块 - 模型保存、加载、交叉验证和版本控制

本模块提供完整的模型生命周期管理功能：
    - 模型保存和加载
    - 交叉验证
    - 模型评估和选择
    - 模型版本控制
"""

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from tqdm import tqdm

from sklearn.model_selection import KFold, cross_val_score, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.pipeline import Pipeline


BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE_DIR / "outputs" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


class ModelManager:
    """模型管理器类"""
    
    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.models_info_file = self.model_dir / "models_info.json"
        self.models_info = self._load_models_info()
    
    def _load_models_info(self) -> Dict:
        """加载模型信息"""
        if self.models_info_file.exists():
            with open(self.models_info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_models_info(self):
        """保存模型信息"""
        with open(self.models_info_file, 'w', encoding='utf-8') as f:
            json.dump(self.models_info, f, ensure_ascii=False, indent=2)
    
    def save_model(
        self,
        pipeline: Pipeline,
        model_name: str,
        feature_cols: List[str],
        metrics: Dict[str, float],
        version: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Path:
        """
        保存训练好的模型
        
        Parameters
        ----------
        pipeline : Pipeline
            训练好的sklearn pipeline
        model_name : str
            模型名称
        feature_cols : List[str]
            特征列名
        metrics : Dict[str, float]
            模型评估指标
        version : str, optional
            版本号，默认使用时间戳
        metadata : Dict, optional
            额外元数据
            
        Returns
        -------
        Path
            保存的模型文件路径
        """
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_filename = f"{model_name}_{version}.pkl"
        model_path = self.model_dir / model_filename
        
        model_data = {
            "pipeline": pipeline,
            "model_name": model_name,
            "version": version,
            "feature_cols": feature_cols,
            "metrics": metrics,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        model_key = f"{model_name}_{version}"
        self.models_info[model_key] = {
            "model_name": model_name,
            "version": version,
            "filename": model_filename,
            "metrics": metrics,
            "feature_cols": feature_cols,
            "created_at": datetime.now().isoformat()
        }
        self._save_models_info()
        
        return model_path
    
    def load_model(self, model_name: str, version: Optional[str] = None) -> Tuple[Pipeline, Dict]:
        """
        加载保存的模型
        
        Parameters
        ----------
        model_name : str
            模型名称
        version : str, optional
            版本号，如果为None则加载最新版本
            
        Returns
        -------
        tuple
            (pipeline, model_data)
        """
        if version is None:
            version = self.get_latest_version(model_name)
            if version is None:
                raise ValueError(f"模型 {model_name} 不存在")
        
        model_filename = f"{model_name}_{version}.pkl"
        model_path = self.model_dir / model_filename
        
        if not model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        return model_data["pipeline"], model_data
    
    def get_latest_version(self, model_name: str) -> Optional[str]:
        """获取模型的最新版本号"""
        versions = []
        for key, info in self.models_info.items():
            if info["model_name"] == model_name:
                versions.append(info["version"])
        
        if not versions:
            return None
        return sorted(versions, reverse=True)[0]
    
    def list_models(self) -> pd.DataFrame:
        """列出所有保存的模型"""
        if not self.models_info:
            return pd.DataFrame()
        
        data = []
        for key, info in self.models_info.items():
            data.append({
                "模型名称": info["model_name"],
                "版本": info["version"],
                "R2": info["metrics"].get("R2", "N/A"),
                "RMSE": info["metrics"].get("RMSE", "N/A"),
                "MAE": info["metrics"].get("MAE", "N/A"),
                "创建时间": info["created_at"]
            })
        
        return pd.DataFrame(data)
    
    def delete_model(self, model_name: str, version: Optional[str] = None) -> bool:
        """
        删除模型
        
        Parameters
        ----------
        model_name : str
            模型名称
        version : str, optional
            版本号，如果为None则删除所有版本
            
        Returns
        -------
        bool
            是否成功删除
        """
        if version is None:
            keys_to_delete = [k for k, v in self.models_info.items() 
                            if v["model_name"] == model_name]
            for key in keys_to_delete:
                model_path = self.model_dir / self.models_info[key]["filename"]
                if model_path.exists():
                    model_path.unlink()
                del self.models_info[key]
        else:
            key = f"{model_name}_{version}"
            if key in self.models_info:
                model_path = self.model_dir / self.models_info[key]["filename"]
                if model_path.exists():
                    model_path.unlink()
                del self.models_info[key]
            else:
                return False
        
        self._save_models_info()
        return True


def cross_validate_model(
    pipeline: Pipeline,
    X: np.ndarray,
    y: np.ndarray,
    cv: int = 5,
    metrics: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    交叉验证模型
    
    Parameters
    ----------
    pipeline : Pipeline
        sklearn pipeline
    X : np.ndarray
        特征数据
    y : np.ndarray
        目标变量
    cv : int, optional
        折数，默认5折
    metrics : List[str], optional
        评估指标列表
        
    Returns
    -------
    Dict
        交叉验证结果
    """
    if metrics is None:
        metrics = ["r2", "neg_mean_squared_error", "neg_mean_absolute_error"]
    
    kfold = KFold(n_splits=cv, shuffle=True, random_state=42)

    results = {}
    for metric in tqdm(metrics, desc="  Metrics", leave=False,
                       bar_format="{l_bar}{bar}| {postfix}"):
        scores = cross_val_score(pipeline, X, y, cv=kfold, scoring=metric)

        if metric == "r2":
            results["R2_mean"] = scores.mean()
            results["R2_std"] = scores.std()
        elif metric == "neg_mean_squared_error":
            results["RMSE_mean"] = (-scores).mean()
            results["RMSE_std"] = (-scores).std()
        elif metric == "neg_mean_absolute_error":
            results["MAE_mean"] = (-scores).mean()
            results["MAE_std"] = (-scores).std()

    print(f"    R2={results.get('R2_mean',0):.4f}±{results.get('R2_std',0):.4f}  "
          f"RMSE={results.get('RMSE_mean',0):.4f}±{results.get('RMSE_std',0):.4f}")

    y_pred = cross_val_predict(pipeline, X, y, cv=kfold)
    results["R2"] = r2_score(y, y_pred)
    results["RMSE"] = np.sqrt(mean_squared_error(y, y_pred))
    results["MAE"] = mean_absolute_error(y, y_pred)
    results["Bias"] = np.mean(y_pred - y)

    return results


def compare_models(
    pipelines: Dict[str, Pipeline],
    X: np.ndarray,
    y: np.ndarray,
    cv: int = 5
) -> pd.DataFrame:
    """
    比较多个模型的性能
    
    Parameters
    ----------
    pipelines : Dict[str, Pipeline]
        模型名称到pipeline的映射
    X : np.ndarray
        特征数据
    y : np.ndarray
        目标变量
        
    Returns
    -------
    pd.DataFrame
        模型比较结果
    """
    results = []

    for name, pipeline in tqdm(pipelines.items(), desc="  Comparing models", leave=False,
                               bar_format="{l_bar}{bar}| {postfix}"):
        try:
            cv_results = cross_validate_model(pipeline, X, y, cv=cv)
            results.append({
                "模型": name,
                "R2": cv_results.get("R2", 0),
                "R2_std": cv_results.get("R2_std", 0),
                "RMSE": cv_results.get("RMSE", 0),
                "RMSE_std": cv_results.get("RMSE_std", 0),
                "MAE": cv_results.get("MAE", 0),
                "MAE_std": cv_results.get("MAE_std", 0),
                "Bias": cv_results.get("Bias", 0)
            })
        except Exception as e:
            results.append({
                "模型": name,
                "R2": None,
                "R2_std": None,
                "RMSE": None,
                "RMSE_std": None,
                "MAE": None,
                "MAE_std": None,
                "Bias": None,
                "Error": str(e)
            })
    
    df = pd.DataFrame(results)
    if "Error" not in df.columns or df["Error"].isna().all():
        df = df.drop(columns=["Error"], errors="ignore")
    
    return df.sort_values("R2", ascending=False).reset_index(drop=True)


def get_best_model(comparison_df: pd.DataFrame, metric: str = "R2") -> str:
    """
    从比较结果中获取最佳模型
    
    Parameters
    ----------
    comparison_df : pd.DataFrame
        模型比较结果
    metric : str, optional
        评估指标，默认R2
        
    Returns
    -------
    str
        最佳模型名称
    """
    if comparison_df.empty:
        return None
    
    return comparison_df.loc[comparison_df[metric].idxmax(), "模型"]


if __name__ == "__main__":
    print("模型管理模块测试")
    print("=" * 50)
    
    manager = ModelManager()
    print(f"模型保存目录: {MODEL_DIR}")
    print(f"已有模型数量: {len(manager.models_info)}")
    
    print("\n列出所有模型:")
    models_df = manager.list_models()
    if not models_df.empty:
        print(models_df)
    else:
        print("暂无保存的模型")
