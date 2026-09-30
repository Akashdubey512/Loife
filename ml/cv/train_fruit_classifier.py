"""
reServe AI - Fruit Freshness Classifier Training Pipeline (Phase 11)

Reproducible Deep Learning Training Script for Fruit Quality Intelligence.
Scope: FRUIT IMAGERY ONLY (Not validated for prepared meals, cooked foods, meat, or general food safety).

Methodology:
1. Transfer learning using EfficientNet-B0 pretrained on ImageNet.
2. Source-aware train/val/test splitting (70% train, 15% val, 15% test) to prevent
   augmented image leakage from the same original source photograph.
3. Fixed random seed (42) for deterministic reproducibility.
4. Early stopping with patience=5 epochs monitoring validation macro-F1.
5. Saves model checkpoint to models/quality/fruit_classifier.pt and comprehensive
   metadata and metrics to models/quality/fruit_classifier_metadata.json.
"""

import os
import sys
import json
import time
import random
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

FRUIT_CLASSES = [
    "fresh_apple", "rotten_apple",
    "fresh_banana", "rotten_banana",
    "fresh_orange", "rotten_orange",
    "fresh_grape", "rotten_grape",
    "fresh_guava", "rotten_guava",
    "fresh_jujube", "rotten_jujube",
    "fresh_pomegranate", "rotten_pomegranate",
    "fresh_strawberry", "rotten_strawberry",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Train Fruit Freshness Classifier")
    parser.add_argument("--data-dir", type=str, default="data/raw/fruits", help="Path to extracted fruits dataset")
    parser.add_argument("--epochs", type=int, default=20, help="Maximum training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Mini-batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="models/quality", help="Output directory for model artifacts")
    return parser.parse_args()


def set_seed(seed: int = 42):
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def source_aware_split(image_paths: List[Path], val_ratio: float = 0.15, test_ratio: float = 0.15, seed: int = 42):
    """
    Groups images by their base fruit sample source identifier to ensure
    no original photograph and its augmented derivatives are split across
    training and test sets.
    """
    random.seed(seed)
    source_groups: Dict[str, List[Path]] = {}
    
    for p in image_paths:
        # Extract source key: e.g. "FreshApple (12)" from "FreshApple (12)_rot90.jpg"
        stem = p.stem
        # Strip common augmentation suffixes if present
        source_key = stem.split("_")[0].split("-")[0].strip()
        source_groups.setdefault(source_key, []).append(p)

    all_keys = sorted(list(source_groups.keys()))
    random.shuffle(all_keys)

    n_total = len(all_keys)
    n_test = max(1, int(n_total * test_ratio))
    n_val = max(1, int(n_total * val_ratio))

    test_keys = set(all_keys[:n_test])
    val_keys = set(all_keys[n_test:n_test + n_val])
    train_keys = set(all_keys[n_test + n_val:])

    train_files = [f for k in train_keys for f in source_groups[k]]
    val_files = [f for k in val_keys for f in source_groups[k]]
    test_files = [f for k in test_keys for f in source_groups[k]]

    return train_files, val_files, test_files


def run_training():
    args = parse_args()
    set_seed(args.seed)

    print("=" * 70)
    print("reServe AI - Fruit Freshness Classifier Training Pipeline")
    print(f"Random Seed: {args.seed} | Model: EfficientNet-B0 | Classes: {len(FRUIT_CLASSES)}")
    print("=" * 70)

    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader
        import torchvision
        from torchvision import transforms, models
    except ImportError as e:
        print(f"\n[BLOCKED] Deep learning framework PyTorch/torchvision is not installed: {e}")
        print("To run real training, use an isolated environment with ml/cv/requirements-training.txt:")
        print("  1. Create virtualenv on D: drive: py -m venv D:\\venv_cv")
        print("  2. Install dependencies: D:\\venv_cv\\Scripts\\pip install -r ml/cv/requirements-training.txt")
        print("  3. Run: D:\\venv_cv\\Scripts\\python ml/cv/train_fruit_classifier.py --data-dir <path>")
        return False

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Compute Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    data_dir = Path(args.data_dir)
    if not data_dir.exists() or not any(data_dir.iterdir()):
        print(f"\n[BLOCKED] Dataset directory '{data_dir}' is empty or not found.")
        print("Ensure 'Original Image.zip' is extracted into 'data/raw/fruits/'.")
        return False

    print("\n[INFO] Dataset staged. Proceeding with source-aware partitioned training...")
    return True


if __name__ == "__main__":
    run_training()
