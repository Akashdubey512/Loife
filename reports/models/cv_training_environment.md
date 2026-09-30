# Computer Vision Fruit Freshness Classifier — Training Environment & Feasibility Audit (Phase 11)

**Audit Date:** 2026-10-01  
**Project:** reServe AI Quality Intelligence  
**Dataset:** Fresh and Rotten Fruits Dataset (Mendeley Data, DOI: [10.17632/bdd69gyhv8.1](https://data.mendeley.com/datasets/bdd69gyhv8/1))  
**Authors:** Sultana, Nusrat; Jahan, Musfika; Uddin, Mohammad Shorif (2022)  

---

## 1. Storage & Host Environment Audit

A comprehensive hardware and storage inspection across all local drives was conducted:

| Drive / Resource | Total Capacity | Free Space | State / Purpose | Suitability for Deep Learning |
| :--- | :--- | :--- | :--- | :--- |
| **C: (System OS)** | 229.87 GB | **6.48 GB** | Windows OS, Program Files, AppData | **CRITICALLY LOW HEADROOM** — Do not install heavy ML packages or download large archives here |
| **D: (Data / Workspace)** | 125.71 GB | **110.58 GB** | ReServeAI project repository | **OPTIMAL** — Ample storage for isolated virtualenvs, dataset staging, and checkpoints |
| **E: (Volume)** | 119.15 GB | **119.05 GB** | Unpartitioned / Storage volume | **AVAILABLE** — Secondary cold storage |
| **GPU Hardware** | 6,144 MiB | 3,989 MiB Free | NVIDIA GeForce RTX 3050 Laptop GPU | Active, CUDA 13.0, Driver 581.86 |
| **Docker** | Docker 20.x | N/A | WSL2 Engine (Stopped) | Available for containerized execution |
| **WSL** | WSL2 (Ubuntu) | N/A | Stopped | Available on D: volume mount |
| **Host Python** | Python 3.9.4 | Global | Production web backend (`fastapi`, `lightgbm`, `scikit-learn`) | `torch` and `torchvision` **NOT installed** |

### Safest Provisioning Strategy
In accordance with Phase 11 safety rules:
1. **Never install PyTorch into the host Python 3.9 on `C:`**: PyTorch wheels (~2.5 GB) + pip cache (~2.5 GB) + temporary build files would consume ~5.0 GB of the remaining 6.48 GB on `C:`, risking Windows instability and IDE failure.
2. **Dedicated Isolated Path on `D:`**:
   - Location: `D:\venv_cv_training`
   - Cache flag: `PIP_CACHE_DIR=D:\pip_cache` or `--no-cache-dir`
   - Script: `ml/cv/train_fruit_classifier.py`
   - Dependencies: `ml/cv/requirements-training.txt`

---

## 2. Fruit Dataset Specifications & Download Feasibility

The verified official Mendeley S3 download endpoints were evaluated:

### Archive 1: `Original Image.zip` (Ground Truth)
- **Direct S3 URL:** `https://prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com/5f1cbd0f-b19a-4e2a-a95d-b6a0f8dc47bb`
- **Archive Size:** 2,794,170,228 bytes (2.79 GB)
- **Total Images:** 3,200 images (exactly 200 images per class across 16 classes)
- **Image Resolution:** 4160 × 3120 (RGB JPEG)
- **Classes (16 total):**
  - **Fresh (8 classes, 1,600 images):** `FreshApple`, `FreshBanana`, `FreshGrape`, `FreshGuava`, `FreshJujube`, `FreshOrange`, `FreshPomegranate`, `FreshStrawberry`
  - **Rotten (8 classes, 1,600 images):** `RottenApple`, `RottenBanana`, `RottenGrape`, `RottenGuava`, `RottenJujube`, `RottenOrange`, `RottenPomegranate`, `RottenStrawberry`

### Archive 2: `Augmented Image.zip`
- **Direct S3 URL:** `https://prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com/46dc9748-13da-45aa-89e8-ac2c9c846d02`
- **Archive Size:** 803,272,180 bytes (803.27 MB)
- **Total Images:** 12,335 images
- **Image Resolution:** 1020 × 1020 (RGB JPEG)

### Transfer Throughput & Network Boundary
A live HTTP byte-range test to the EU-West-1 S3 endpoint yielded an average transfer rate of **0.26 MB/s** (260 KB/s).
At 0.26 MB/s:
- Downloading `Original Image.zip` (2.79 GB) requires **~2.85 hours** of continuous streaming.
- Downloading `Augmented Image.zip` (803 MB) requires **~51 minutes**.
- The host network firewall (`FG6H0FTB22905105`) actively drops long-lived persistent TCP connections, presenting a high risk of mid-stream corruption during multi-hour downloads.

---

## 3. Data Leakage Prevention Protocol

The inspection of the augmented archive revealed a critical methodological concern:
1. **Augmented File Prefix Inconsistency:** Images in the augmented archive contain filename prefix mismatches (e.g. `FreshOrange (1).jpg` found inside the `FreshApple` directory).
2. **Derivation Leakage:** Splitting images randomly across train/val/test would place an original image in the training set while placing rotated/scaled variants of the **identical physical fruit** in the test set. This falsely inflates reported generalization metrics (similar to the E-Nose 5-second autocorrelation issue).

### Mandatory Protocol
- **Source-Aware Grouping:** Extract the base sample identifier from filenames (e.g. `FreshApple (12)`).
- **Partitioning:** Allocate 70% of base fruit samples to training, 15% to validation, and 15% to test.
- All augmented transformations of a given fruit specimen must remain strictly within the partition of their parent image.

---

## 4. Model Architecture & Scope Boundaries

| Parameter | Specification |
| :--- | :--- |
| **Model Name** | **Fruit Freshness Classifier** |
| **Model Scope** | **FRUIT IMAGERY ONLY** |
| **Prohibited Claims** | NEVER describe as "Universal Food Freshness AI", "Microbial Pathogen Detector", or "Food Safety Certification Engine". |
| **Backbone** | EfficientNet-B0 (pretrained on ImageNet, fine-tuned top layers) |
| **Loss Function** | Cross-Entropy with label smoothing (0.1) |
| **Optimizer** | AdamW ($\text{lr} = 10^{-4}$, weight decay $10^{-2}$) |
| **Early Stopping** | Patience = 5 epochs monitoring validation Macro-F1 |
| **Production Human Oversight** | Mandatory badge displayed on all UI reports: *"Human inspector sign-off is mandatory before redistribution."* |

---

## 5. Active Production Status

Until the isolated deep learning environment finishes training on dedicated compute:
1. `cv/freshness_classifier.py` operates under **transparent simulation mode** (`SIMULATION_MODE = True`).
2. Inference utilizes **spectral-spatial pixel decomposition** (evaluating enzymatic browning at Hue 8°–38°, necrotic lesions at $V < 0.22$, and mycelium/mold blooms).
3. The API and frontend honestly display `model_status: "simulated"` with zero fabricated CNN weights.
