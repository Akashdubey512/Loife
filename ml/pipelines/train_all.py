"""
reServe AI - Phase 8E: Model Training Pipelines

Trains real models on acquired datasets:
  A. Demand Forecasting (Genpact schema) - LightGBM, XGBoost, RandomForest
  B. Predictive Maintenance (AI4I 2020) - RandomForest, XGBoost, LightGBM
  C. Energy Forecasting (Appliances Energy) - LightGBM, RandomForest

Run: python -m ml.pipelines.train_all
"""

import os
import sys
import json
import hashlib
import warnings
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
)
from sklearn.preprocessing import LabelEncoder

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports" / "models"
MANIFEST_PATH = DATA_DIR / "manifests" / "dataset_manifest.json"

# Model registry
MODEL_REGISTRY = []


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def save_model_registry():
    registry_path = MODELS_DIR / "model_registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, "w") as f:
        json.dump(MODEL_REGISTRY, f, indent=2, default=str)
    print(f"\n  Model registry saved: {registry_path}")


def register_model(entry: Dict[str, Any]):
    MODEL_REGISTRY.append(entry)


# ============================================================
# A. DEMAND FORECASTING
# ============================================================
def train_demand_model():
    print("\n" + "=" * 60)
    print("TRAINING: Demand Forecasting Model")
    print("=" * 60)

    train_path = RAW_DIR / "genpact" / "train.csv"
    if not train_path.exists():
        print("  [SKIP] No training data available")
        return None

    df = pd.read_csv(train_path)
    print(f"  Dataset: {len(df)} rows, {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)}")

    target_col = "num_orders"
    if target_col not in df.columns:
        print(f"  [FAIL] Target column '{target_col}' not found")
        return None

    # Feature engineering
    feature_cols = []
    for col in ["center_id", "meal_id", "checkout_price", "base_price",
                "emailer_for_promotion", "homepage_featured", "week"]:
        if col in df.columns:
            feature_cols.append(col)

    if "checkout_price" in df.columns and "base_price" in df.columns:
        df["discount_pct"] = (df["base_price"] - df["checkout_price"]) / df["base_price"].clip(lower=1)
        feature_cols.append("discount_pct")

    if "week" in df.columns:
        df["week_sin"] = np.sin(2 * np.pi * df["week"] / 52)
        df["week_cos"] = np.cos(2 * np.pi * df["week"] / 52)
        feature_cols.extend(["week_sin", "week_cos"])

    print(f"  Features: {feature_cols}")

    X = df[feature_cols].fillna(0)
    y = df[target_col]

    print(f"  Target stats: mean={y.mean():.1f}, std={y.std():.1f}, min={y.min()}, max={y.max()}")

    # TIME-AWARE split (week-based, NOT random)
    if "week" in df.columns:
        weeks = sorted(df["week"].unique())
        n_weeks = len(weeks)
        train_weeks = weeks[:int(n_weeks * 0.7)]
        val_weeks = weeks[int(n_weeks * 0.7):int(n_weeks * 0.85)]
        test_weeks = weeks[int(n_weeks * 0.85):]

        train_mask = df["week"].isin(train_weeks)
        val_mask = df["week"].isin(val_weeks)
        test_mask = df["week"].isin(test_weeks)

        X_train, y_train = X[train_mask], y[train_mask]
        X_val, y_val = X[val_mask], y[val_mask]
        X_test, y_test = X[test_mask], y[test_mask]
        print(f"  Time-aware split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")
    else:
        X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
        print(f"  Random split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")

    # Dataset hash for reproducibility
    dataset_hash = hashlib.sha256(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()[:16]

    # ---- Baseline: Naive mean ----
    naive_pred = np.full(len(y_test), y_train.mean())
    baseline_mae = mean_absolute_error(y_test, naive_pred)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, naive_pred))
    print(f"\n  Baseline (naive mean): MAE={baseline_mae:.2f}, RMSE={baseline_rmse:.2f}")

    results = {}

    # ---- Model 1: Random Forest ----
    print("\n  Training Random Forest...")
    rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_pred)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
    rf_r2 = r2_score(y_test, rf_pred)
    results["RandomForest"] = {"mae": rf_mae, "rmse": rf_rmse, "r2": rf_r2}
    print(f"  RandomForest: MAE={rf_mae:.2f}, RMSE={rf_rmse:.2f}, R2={rf_r2:.4f}")

    # ---- Model 2: LightGBM ----
    try:
        import lightgbm as lgb
        print("\n  Training LightGBM...")
        lgb_model = lgb.LGBMRegressor(
            n_estimators=200, max_depth=10, learning_rate=0.1,
            num_leaves=31, random_state=42, n_jobs=-1, verbose=-1
        )
        lgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
                      callbacks=[lgb.early_stopping(20, verbose=False)])
        lgb_pred = lgb_model.predict(X_test)
        lgb_mae = mean_absolute_error(y_test, lgb_pred)
        lgb_rmse = np.sqrt(mean_squared_error(y_test, lgb_pred))
        lgb_r2 = r2_score(y_test, lgb_pred)
        results["LightGBM"] = {"mae": lgb_mae, "rmse": lgb_rmse, "r2": lgb_r2}
        print(f"  LightGBM: MAE={lgb_mae:.2f}, RMSE={lgb_rmse:.2f}, R2={lgb_r2:.4f}")
    except Exception as e:
        print(f"  [WARN] LightGBM failed: {e}")

    # ---- Model 3: XGBoost ----
    try:
        import xgboost as xgb
        print("\n  Training XGBoost...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=200, max_depth=8, learning_rate=0.1,
            random_state=42, n_jobs=-1, verbosity=0
        )
        xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        xgb_pred = xgb_model.predict(X_test)
        xgb_mae = mean_absolute_error(y_test, xgb_pred)
        xgb_rmse = np.sqrt(mean_squared_error(y_test, xgb_pred))
        xgb_r2 = r2_score(y_test, xgb_pred)
        results["XGBoost"] = {"mae": xgb_mae, "rmse": xgb_rmse, "r2": xgb_r2}
        print(f"  XGBoost: MAE={xgb_mae:.2f}, RMSE={xgb_rmse:.2f}, R2={xgb_r2:.4f}")
    except Exception as e:
        print(f"  [WARN] XGBoost failed: {e}")

    # ---- Select best model ----
    best_name = min(results, key=lambda k: results[k]["mae"])
    best_metrics = results[best_name]
    print(f"\n  BEST MODEL: {best_name} (MAE={best_metrics['mae']:.2f})")

    # Save best model
    model_dir = MODELS_DIR / "demand"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "demand_model.joblib"

    best_model = {"RandomForest": rf, "LightGBM": lgb_model if "LightGBM" in results else None,
                  "XGBoost": xgb_model if "XGBoost" in results else None}[best_name]

    joblib.dump({
        "model": best_model,
        "feature_columns": feature_cols,
        "algorithm": best_name,
        "target_column": target_col,
    }, model_path)
    print(f"  Saved: {model_path}")

    # Save metadata
    meta_path = model_dir / "demand_model_metadata.json"
    metadata = {
        "model_name": "demand_forecasting",
        "model_version": f"trained-{best_name.lower()}-v1.0",
        "dataset": "genpact_demand",
        "dataset_hash": dataset_hash,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": best_name,
        "features": feature_cols,
        "metrics": {
            "baseline_mae": round(baseline_mae, 2),
            "baseline_rmse": round(baseline_rmse, 2),
            **{f"{name}_mae": round(m["mae"], 2) for name, m in results.items()},
            **{f"{name}_rmse": round(m["rmse"], 2) for name, m in results.items()},
            **{f"{name}_r2": round(m["r2"], 4) for name, m in results.items()},
            "best_test_mae": round(best_metrics["mae"], 2),
            "best_test_rmse": round(best_metrics["rmse"], 2),
            "best_test_r2": round(best_metrics["r2"], 4),
        },
        "artifact_path": str(model_path),
        "status": "candidate",
        "limitations": [
            "Trained on synthetic Genpact-schema data (development mode)" if "synthetic" in str(RAW_DIR / "genpact") else "Trained on Genpact hackathon data",
            "Does not account for weather, special events, or menu changes",
            "Requires retraining on institution-specific consumption data for production use",
        ]
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    register_model(metadata)
    return metadata


# ============================================================
# B. PREDICTIVE MAINTENANCE (AI4I 2020)
# ============================================================
def train_maintenance_model():
    print("\n" + "=" * 60)
    print("TRAINING: Predictive Maintenance Model (AI4I 2020)")
    print("=" * 60)

    # Find CSV
    csv_files = list((RAW_DIR / "ai4i").rglob("*.csv"))
    if not csv_files:
        print("  [SKIP] No AI4I data found")
        return None

    df = pd.read_csv(csv_files[0])
    print(f"  Dataset: {len(df)} rows, {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)}")

    # Identify target and features
    # AI4I 2020 columns: UDI, Product ID, Type, Air temperature [K], Process temperature [K],
    # Rotational speed [rpm], Torque [Nm], Tool wear [min], Machine failure, TWF, HDF, PWF, OSF, RNF
    target_col = "Machine failure"
    if target_col not in df.columns:
        # Try alternate names
        for alt in ["machine_failure", "Target", "target", "failure"]:
            if alt in df.columns:
                target_col = alt
                break
        else:
            print(f"  Available columns: {list(df.columns)}")
            # Use the 7th column (0-indexed: 6) as target if standard AI4I layout
            if len(df.columns) >= 9:
                target_col = df.columns[8]  # Machine failure is typically column index 8
                print(f"  Using column '{target_col}' as target")

    # Feature columns - numeric sensor readings
    feature_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if any(term in col_lower for term in ["air temp", "process temp", "rotational", "torque", "tool wear"]):
            feature_cols.append(col)

    if not feature_cols:
        # Fallback: use columns 2-6 (typical AI4I layout)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in numeric_cols if c != target_col and c not in ["UDI"]][:5]

    # Type encoding if present
    type_col = None
    for col in df.columns:
        if col.lower() in ["type", "product id"]:
            if df[col].dtype == object:
                type_col = col
                break
    
    if type_col and type_col not in feature_cols:
        le = LabelEncoder()
        df[f"{type_col}_encoded"] = le.fit_transform(df[type_col].astype(str))
        feature_cols.append(f"{type_col}_encoded")

    print(f"  Target: {target_col}")
    print(f"  Features: {feature_cols}")

    X = df[feature_cols].fillna(0).values
    y = df[target_col].values

    # Check class balance
    unique, counts = np.unique(y, return_counts=True)
    print(f"  Class distribution: {dict(zip(unique, counts))}")
    failure_rate = counts.min() / counts.sum() if len(counts) > 1 else 0
    print(f"  Failure rate: {failure_rate:.2%}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.15, random_state=42, stratify=y_train)
    print(f"  Split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")

    dataset_hash = hashlib.sha256(df.values.tobytes()).hexdigest()[:16]

    results = {}

    # ---- Model 1: Random Forest ----
    print("\n  Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1,
                                 class_weight="balanced")
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_proba = rf.predict_proba(X_test)[:, 1] if len(unique) == 2 else None
    rf_metrics = {
        "accuracy": accuracy_score(y_test, rf_pred),
        "precision": precision_score(y_test, rf_pred, zero_division=0),
        "recall": recall_score(y_test, rf_pred, zero_division=0),
        "f1": f1_score(y_test, rf_pred, zero_division=0),
    }
    if rf_proba is not None:
        rf_metrics["roc_auc"] = roc_auc_score(y_test, rf_proba)
    results["RandomForest"] = rf_metrics
    print(f"  RandomForest: Acc={rf_metrics['accuracy']:.4f}, F1={rf_metrics['f1']:.4f}, AUC={rf_metrics.get('roc_auc', 'N/A')}")

    # ---- Model 2: XGBoost ----
    try:
        import xgboost as xgb
        print("\n  Training XGBoost...")
        scale_pos_weight = counts[0] / counts[1] if len(counts) > 1 and counts[1] > 0 else 1
        xgb_model = xgb.XGBClassifier(
            n_estimators=150, max_depth=8, learning_rate=0.1,
            scale_pos_weight=scale_pos_weight, random_state=42,
            n_jobs=-1, verbosity=0, use_label_encoder=False, eval_metric="logloss"
        )
        xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        xgb_pred = xgb_model.predict(X_test)
        xgb_proba = xgb_model.predict_proba(X_test)[:, 1] if len(unique) == 2 else None
        xgb_metrics = {
            "accuracy": accuracy_score(y_test, xgb_pred),
            "precision": precision_score(y_test, xgb_pred, zero_division=0),
            "recall": recall_score(y_test, xgb_pred, zero_division=0),
            "f1": f1_score(y_test, xgb_pred, zero_division=0),
        }
        if xgb_proba is not None:
            xgb_metrics["roc_auc"] = roc_auc_score(y_test, xgb_proba)
        results["XGBoost"] = xgb_metrics
        print(f"  XGBoost: Acc={xgb_metrics['accuracy']:.4f}, F1={xgb_metrics['f1']:.4f}, AUC={xgb_metrics.get('roc_auc', 'N/A')}")
    except Exception as e:
        print(f"  [WARN] XGBoost failed: {e}")

    # ---- Model 3: LightGBM ----
    try:
        import lightgbm as lgb
        print("\n  Training LightGBM...")
        lgb_model = lgb.LGBMClassifier(
            n_estimators=150, max_depth=8, learning_rate=0.1,
            is_unbalance=True, random_state=42, n_jobs=-1, verbose=-1
        )
        lgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
                      callbacks=[lgb.early_stopping(20, verbose=False)])
        lgb_pred = lgb_model.predict(X_test)
        lgb_proba = lgb_model.predict_proba(X_test)[:, 1] if len(unique) == 2 else None
        lgb_metrics = {
            "accuracy": accuracy_score(y_test, lgb_pred),
            "precision": precision_score(y_test, lgb_pred, zero_division=0),
            "recall": recall_score(y_test, lgb_pred, zero_division=0),
            "f1": f1_score(y_test, lgb_pred, zero_division=0),
        }
        if lgb_proba is not None:
            lgb_metrics["roc_auc"] = roc_auc_score(y_test, lgb_proba)
        results["LightGBM"] = lgb_metrics
        print(f"  LightGBM: Acc={lgb_metrics['accuracy']:.4f}, F1={lgb_metrics['f1']:.4f}, AUC={lgb_metrics.get('roc_auc', 'N/A')}")
    except Exception as e:
        print(f"  [WARN] LightGBM failed: {e}")

    # Select best by F1 (important for imbalanced data)
    best_name = max(results, key=lambda k: results[k]["f1"])
    best_metrics = results[best_name]
    print(f"\n  BEST MODEL: {best_name} (F1={best_metrics['f1']:.4f})")

    # Save
    model_dir = MODELS_DIR / "maintenance"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "maintenance_model.joblib"

    best_model = {"RandomForest": rf, "XGBoost": xgb_model if "XGBoost" in results else None,
                  "LightGBM": lgb_model if "LightGBM" in results else None}[best_name]

    joblib.dump({
        "model": best_model,
        "feature_columns": feature_cols,
        "algorithm": best_name,
    }, model_path)
    print(f"  Saved: {model_path}")

    metadata = {
        "model_name": "predictive_maintenance",
        "model_version": f"trained-{best_name.lower()}-v1.0",
        "dataset": "ai4i_2020",
        "dataset_hash": dataset_hash,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": best_name,
        "features": feature_cols,
        "metrics": {name: {k: round(v, 4) for k, v in m.items()} for name, m in results.items()},
        "best_metrics": {k: round(v, 4) for k, v in best_metrics.items()},
        "artifact_path": str(model_path),
        "status": "candidate",
        "limitations": [
            "Trained on UCI AI4I 2020 synthetic industrial data",
            "Not specific to food service kitchen equipment",
            "Applicable for cold-chain equipment anomaly detection research",
        ]
    }
    meta_path = model_dir / "maintenance_model_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    register_model(metadata)
    return metadata


# ============================================================
# C. ENERGY FORECASTING (Appliances Energy)
# ============================================================
def train_energy_model():
    print("\n" + "=" * 60)
    print("TRAINING: Energy Consumption Model (Appliances Energy)")
    print("=" * 60)

    csv_files = list((RAW_DIR / "appliances_energy").rglob("*.csv"))
    if not csv_files:
        print("  [SKIP] No energy data found")
        return None

    df = pd.read_csv(csv_files[0])
    print(f"  Dataset: {len(df)} rows, {len(df.columns)} columns")

    # Target: Appliances energy consumption (Wh)
    target_col = "Appliances"
    if target_col not in df.columns:
        target_col = df.columns[1]  # Usually second column
        print(f"  Using '{target_col}' as target")

    # Parse date for time-aware split
    date_col = None
    for col in df.columns:
        if "date" in col.lower():
            date_col = col
            break

    # Numeric features (exclude date and target)
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if c != target_col and c != "rv1" and c != "rv2"]  # rv1, rv2 are random variables

    print(f"  Target: {target_col}")
    print(f"  Features: {len(feature_cols)} columns")

    X = df[feature_cols].fillna(0)
    y = df[target_col]
    print(f"  Target stats: mean={y.mean():.1f}, std={y.std():.1f}")

    # Time-aware split using row order (data is chronological)
    n = len(df)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)

    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]
    print(f"  Time-aware split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")

    dataset_hash = hashlib.sha256(df.values.tobytes()).hexdigest()[:16]

    # Baseline
    naive_pred = np.full(len(y_test), y_train.mean())
    baseline_mae = mean_absolute_error(y_test, naive_pred)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, naive_pred))
    print(f"\n  Baseline (naive mean): MAE={baseline_mae:.2f}, RMSE={baseline_rmse:.2f}")

    results = {}

    # ---- Random Forest ----
    print("\n  Training Random Forest...")
    rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    results["RandomForest"] = {
        "mae": mean_absolute_error(y_test, rf_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, rf_pred)),
        "r2": r2_score(y_test, rf_pred),
    }
    print(f"  RandomForest: MAE={results['RandomForest']['mae']:.2f}, R2={results['RandomForest']['r2']:.4f}")

    # ---- LightGBM ----
    try:
        import lightgbm as lgb
        print("\n  Training LightGBM...")
        lgb_model = lgb.LGBMRegressor(
            n_estimators=200, max_depth=10, learning_rate=0.1,
            num_leaves=31, random_state=42, n_jobs=-1, verbose=-1
        )
        lgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
                      callbacks=[lgb.early_stopping(20, verbose=False)])
        lgb_pred = lgb_model.predict(X_test)
        results["LightGBM"] = {
            "mae": mean_absolute_error(y_test, lgb_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, lgb_pred)),
            "r2": r2_score(y_test, lgb_pred),
        }
        print(f"  LightGBM: MAE={results['LightGBM']['mae']:.2f}, R2={results['LightGBM']['r2']:.4f}")
    except Exception as e:
        print(f"  [WARN] LightGBM failed: {e}")

    # Select best
    best_name = min(results, key=lambda k: results[k]["mae"])
    best_metrics = results[best_name]
    print(f"\n  BEST MODEL: {best_name} (MAE={best_metrics['mae']:.2f})")

    # Save
    model_dir = MODELS_DIR / "energy"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "energy_model.joblib"

    best_model = {"RandomForest": rf, "LightGBM": lgb_model if "LightGBM" in results else None}[best_name]
    joblib.dump({
        "model": best_model,
        "feature_columns": feature_cols,
        "algorithm": best_name,
        "target_column": target_col,
    }, model_path)
    print(f"  Saved: {model_path}")

    metadata = {
        "model_name": "energy_forecasting",
        "model_version": f"trained-{best_name.lower()}-v1.0",
        "dataset": "appliances_energy",
        "dataset_hash": dataset_hash,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": best_name,
        "features": feature_cols,
        "metrics": {
            "baseline_mae": round(baseline_mae, 2),
            "baseline_rmse": round(baseline_rmse, 2),
            **{f"{name}_{k}": round(v, 4) for name, m in results.items() for k, v in m.items()},
            "best_test_mae": round(best_metrics["mae"], 2),
            "best_test_rmse": round(best_metrics["rmse"], 2),
            "best_test_r2": round(best_metrics["r2"], 4),
        },
        "artifact_path": str(model_path),
        "status": "candidate",
        "limitations": [
            "Trained on Belgian residential appliance data",
            "Not directly calibrated for institutional kitchen energy profiles",
            "Serves as proof-of-concept for facility energy analytics",
        ]
    }
    meta_path = model_dir / "energy_model_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    register_model(metadata)
    return metadata


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("reServe AI - Phase 8E: Model Training Pipeline")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    results = {}

    try:
        results["demand"] = train_demand_model()
    except Exception as e:
        print(f"  [FAIL] Demand training: {e}")
        traceback.print_exc()
        results["demand"] = None

    try:
        results["maintenance"] = train_maintenance_model()
    except Exception as e:
        print(f"  [FAIL] Maintenance training: {e}")
        traceback.print_exc()
        results["maintenance"] = None

    try:
        results["energy"] = train_energy_model()
    except Exception as e:
        print(f"  [FAIL] Energy training: {e}")
        traceback.print_exc()
        results["energy"] = None

    # Save registry
    save_model_registry()

    # Summary
    print("\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)
    for name, meta in results.items():
        if meta:
            best = meta.get("algorithm", "?")
            version = meta.get("model_version", "?")
            print(f"  [OK] {name}: {best} -> {version}")
        else:
            print(f"  [FAIL] {name}: not trained")

    print(f"\nCompleted: {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
