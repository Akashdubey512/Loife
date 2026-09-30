"""
reServe AI - E-Nose Beef Quality Classification Training Pipeline

Dataset: Mendeley E-nose Beef Quality Dataset (doi:10.17632/n8mc3nspfn.1)
Authors: Surjith S, Alex Raj SM (2025)
Features: 8 MOS sensors (MQ-2, MQ-3, MQ-4, MQ-5, MQ-135, MQ-136, MQ-137, MQ-138), Temperature, Humidity
Target: Quality Class (1=Excellent, 2=Good, 3=Acceptable, 4=Spoiled)

IMPORTANT NOTICE:
This model is trained strictly for beef quality classification from MOS gas sensors.
It must NOT be presented as a universal food quality model.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "enose"
MODELS_DIR = PROJECT_ROOT / "models" / "enose"
REGISTRY_PATH = PROJECT_ROOT / "models" / "model_registry.json"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "dataset_manifest.json"
DOWNLOAD_STATUS_PATH = PROJECT_ROOT / "data" / "metadata" / "download_status.json"

CLASS_NAMES = {
    1: "EXCELLENT",
    2: "GOOD",
    3: "ACCEPTABLE",
    4: "SPOILED",
}

CLASS_VERDICTS = {
    1: "SAFE_FOR_REDISTRIBUTION",
    2: "SAFE_FOR_REDISTRIBUTION",
    3: "PROCESS_IMMEDIATELY",
    4: "HAZARD_DISCARD",
}


def find_enose_csv() -> Optional[Path]:
    """Find the e-nose dataset CSV."""
    candidates = list(RAW_DIR.rglob("*.csv"))
    if not candidates:
        return None
    # Prioritize top-level or 'Beef quality 4 classes.csv'
    for c in candidates:
        if "beef quality" in c.name.lower():
            return c
    return candidates[0]


def train_enose_model() -> Dict[str, Any]:
    print("=" * 60)
    print("TRAINING: E-Nose Beef Quality Classifier")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    csv_path = find_enose_csv()
    if not csv_path or not csv_path.exists():
        raise FileNotFoundError(f"E-nose dataset CSV not found in {RAW_DIR}")

    print(f"  Source CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    # Normalize column names: strip whitespace and lowercase comparison
    col_map = {c: c.strip() for c in df.columns}
    df = df.rename(columns=col_map)
    print(f"  Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"  Columns: {list(df.columns)}")

    # Target
    target_col = "class"
    if target_col not in df.columns:
        # Check for alternative naming
        for c in df.columns:
            if "class" in c.lower() or "label" in c.lower():
                target_col = c
                break
    print(f"  Target column: {target_col}")

    # Feature columns: 8 MOS sensors + Temp + Humidity
    possible_features = [
        "Temperature", "Humidity",
        "Mq-2", "Mq-3", "Mq-4", "Mq-5",
        "Mq-135", "Mq-136", "Mq-137", "Mq-138"
    ]
    feature_cols = [c for c in possible_features if c in df.columns]
    if len(feature_cols) < 5:
        # Fallback to numeric columns excluding target and identifiers
        feature_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if c not in (target_col, "sl no", "minutes", "tvc")
        ]

    print(f"  Features ({len(feature_cols)}): {feature_cols}")

    X = df[feature_cols].copy().fillna(0)
    y_raw = df[target_col].astype(int)

    # Class distribution
    dist = y_raw.value_counts().to_dict()
    print(f"  Class distribution: {dist}")

    # Map target: LightGBM requires 0..K-1
    unique_classes = sorted(y_raw.unique())
    class_to_idx = {c: i for i, c in enumerate(unique_classes)}
    idx_to_class = {i: c for c, i in class_to_idx.items()}
    y = y_raw.map(class_to_idx)

    # Train / Val / Test split (70 / 15 / 15) stratified
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.1765, random_state=42, stratify=y_train_val
    )
    print(f"  Splits: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")

    # Compute baseline: majority class
    majority_class = y_train.mode()[0]
    y_pred_baseline = np.full(len(y_test), majority_class)
    baseline_acc = float(accuracy_score(y_test, y_pred_baseline))
    baseline_f1 = float(f1_score(y_test, y_pred_baseline, average="macro"))
    print(f"  Baseline (Majority Class {idx_to_class[majority_class]}): Accuracy={baseline_acc:.4f}, Macro-F1={baseline_f1:.4f}")

    results = {}

    # 1. Random Forest
    print("\n  [1/2] Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    results["RandomForest"] = {
        "model": rf,
        "accuracy": float(accuracy_score(y_test, y_pred_rf)),
        "macro_f1": float(f1_score(y_test, y_pred_rf, average="macro")),
        "macro_precision": float(precision_score(y_test, y_pred_rf, average="macro")),
        "macro_recall": float(recall_score(y_test, y_pred_rf, average="macro")),
    }
    print(f"  RandomForest: Accuracy={results['RandomForest']['accuracy']:.4f}, Macro-F1={results['RandomForest']['macro_f1']:.4f}")

    # 2. LightGBM
    try:
        import lightgbm as lgb
        print("\n  [2/2] Training LightGBM...")
        lgb_model = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=10,
            learning_rate=0.08,
            num_leaves=31,
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )
        lgb_model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(25, verbose=False)],
        )
        y_pred_lgb = lgb_model.predict(X_test)
        results["LightGBM"] = {
            "model": lgb_model,
            "accuracy": float(accuracy_score(y_test, y_pred_lgb)),
            "macro_f1": float(f1_score(y_test, y_pred_lgb, average="macro")),
            "macro_precision": float(precision_score(y_test, y_pred_lgb, average="macro")),
            "macro_recall": float(recall_score(y_test, y_pred_lgb, average="macro")),
        }
        print(f"  LightGBM: Accuracy={results['LightGBM']['accuracy']:.4f}, Macro-F1={results['LightGBM']['macro_f1']:.4f}")
    except Exception as e:
        print(f"  [WARN] LightGBM training failed: {e}")

    # Select best model by Macro F1
    best_name = max(results, key=lambda k: results[k]["macro_f1"])
    best_data = results[best_name]
    best_model = best_data["model"]
    print(f"\n  BEST MODEL: {best_name} (Macro-F1={best_data['macro_f1']:.4f}, Acc={best_data['accuracy']:.4f})")

    # Detailed test classification report
    best_preds = best_model.predict(X_test)
    target_names = [CLASS_NAMES.get(idx_to_class[i], f"Class_{i}") for i in range(len(unique_classes))]
    report_dict = classification_report(y_test, best_preds, target_names=target_names, output_dict=True)
    cm = confusion_matrix(y_test, best_preds).tolist()

    # Save model artifact
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = MODELS_DIR / "enose_model.joblib"
    saved_payload = {
        "model": best_model,
        "algorithm": best_name,
        "feature_columns": feature_cols,
        "target_column": target_col,
        "class_to_idx": class_to_idx,
        "idx_to_class": idx_to_class,
        "class_names": CLASS_NAMES,
        "class_verdicts": CLASS_VERDICTS,
    }
    joblib.dump(saved_payload, artifact_path)
    print(f"  Saved model artifact: {artifact_path} ({os.path.getsize(artifact_path):,} bytes)")

    # Compute dataset hash
    with open(csv_path, "rb") as f:
        dataset_hash = hashlib.sha256(f.read()).hexdigest()

    metadata = {
        "model_name": "enose_beef_quality",
        "model_version": f"trained-{best_name.lower()}-v1.0",
        "status": "trained",
        "dataset": "enose_beef",
        "dataset_source": "E-nose Beef Quality (Mendeley, DOI:10.17632/n8mc3nspfn.1)",
        "dataset_sha256": dataset_hash,
        "dataset_rows": len(df),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": best_name,
        "features": feature_cols,
        "target": target_col,
        "classes": {str(k): v for k, v in CLASS_NAMES.items()},
        "metrics": {
            "baseline_accuracy": round(baseline_acc, 4),
            "baseline_macro_f1": round(baseline_f1, 4),
            "test_accuracy": round(best_data["accuracy"], 4),
            "test_macro_f1": round(best_data["macro_f1"], 4),
            "test_macro_precision": round(best_data["macro_precision"], 4),
            "test_macro_recall": round(best_data["macro_recall"], 4),
            "per_class": {
                name: {
                    "precision": round(report_dict[name]["precision"], 4),
                    "recall": round(report_dict[name]["recall"], 4),
                    "f1": round(report_dict[name]["f1-score"], 4),
                    "support": int(report_dict[name]["support"]),
                }
                for name in target_names if name in report_dict
            },
            "confusion_matrix": cm,
        },
        "artifact": "models/enose/enose_model.joblib",
        "limitations": [
            "Trained strictly on Mendeley E-nose Beef Quality Dataset (doi:10.17632/n8mc3nspfn.1)",
            "Scope is BEEF QUALITY ONLY — not calibrated for poultry, pork, seafood, dairy, or fresh produce",
            "Requires DHT11 (temp, humidity) and 8 MOS gas sensors (MQ2-MQ138) for inference",
            "Human sensory inspection remains mandatory before food redistribution",
        ],
    }

    meta_path = MODELS_DIR / "enose_model_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  Saved metadata: {meta_path}")

    # Update model_registry.json
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r") as f:
            registry = json.load(f)
        updated = False
        for entry in registry:
            if entry.get("model_name") == "enose_beef_quality":
                entry["status"] = "trained"
                entry["model_version"] = metadata["model_version"]
                entry["algorithm"] = best_name
                entry["artifact"] = "models/enose/enose_model.joblib"
                entry["trained_at"] = metadata["trained_at"]
                entry["metrics"] = {
                    "accuracy": metadata["metrics"]["test_accuracy"],
                    "macro_f1": metadata["metrics"]["test_macro_f1"],
                    "macro_precision": metadata["metrics"]["test_macro_precision"],
                    "macro_recall": metadata["metrics"]["test_macro_recall"],
                }
                entry["limitations"] = metadata["limitations"]
                updated = True
                break
        if not updated:
            registry.append(metadata)
        with open(REGISTRY_PATH, "w") as f:
            json.dump(registry, f, indent=2)
        print("  Updated model_registry.json")

    # Update dataset_manifest.json
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)
        for d in manifest.get("datasets", []):
            if d.get("id") == "enose_beef":
                d["status"] = "downloaded"
                d["row_count"] = len(df)
                d["file_size_bytes"] = os.path.getsize(csv_path)
                d["checksum_sha256"] = dataset_hash
                d["columns"] = list(df.columns)
                d["download_date"] = datetime.now(timezone.utc).isoformat()
                d["notes"] = f"{len(df)} records from Mendeley (doi:10.17632/n8mc3nspfn.1). Trained {best_name} classifier."
                break
        with open(MANIFEST_PATH, "w") as f:
            json.dump(manifest, f, indent=2)
        print("  Updated dataset_manifest.json")

    # Update download_status.json
    if DOWNLOAD_STATUS_PATH.exists():
        with open(DOWNLOAD_STATUS_PATH, "r") as f:
            status_data = json.load(f)
        if "datasets" in status_data and "enose_beef" in status_data["datasets"]:
            status_data["datasets"]["enose_beef"]["access_status"] = "DOWNLOADED"
            status_data["datasets"]["enose_beef"]["downloaded_at"] = datetime.now(timezone.utc).isoformat()
            status_data["datasets"]["enose_beef"]["verified_rows"] = len(df)
        with open(DOWNLOAD_STATUS_PATH, "w") as f:
            json.dump(status_data, f, indent=2)
        print("  Updated download_status.json")

    return metadata


if __name__ == "__main__":
    train_enose_model()
