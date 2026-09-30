# Fruit Freshness Classifier — Model Card & Audit Specification

**Document Date:** 2026-10-01  
**Platform:** reServe AI Quality Intelligence  
**Model Name:** Fruit Freshness Classifier  
**Current Production Status:** **`SIMULATION_MODE = True` (Active Colorimetric Spectral-Spatial Decomposition)**  
**Target Architecture:** Transfer Learning via EfficientNet-B0 (PyTorch)  
**Intended Scope:** **FRUIT IMAGERY ONLY** (Apples, Bananas, Oranges, Grapes, Guavas, Jujubes, Pomegranates, Strawberries)  

---

## 1. Model Purpose
The Fruit Freshness Classifier is designed to assess the surface decay, mold infiltration, enzymatic browning, and chromatic vibrancy of whole fresh fruits to assist food redistribution logistics in prioritizing batches near their end-of-shelf-life.

---

## 2. Dataset & Provenance
- **Dataset Name:** Fresh and Rotten Fruits Dataset
- **Hosting Organization:** Mendeley Data
- **DOI:** [10.17632/bdd69gyhv8.1](https://data.mendeley.com/datasets/bdd69gyhv8/1)
- **Authors:** Sultana, Nusrat; Jahan, Musfika; Uddin, Mohammad Shorif (2022)
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Primary Archive:** `Original Image.zip` (2,794,170,228 bytes / ~2.79 GB)
- **Augmented Archive:** `Augmented Image.zip` (803,272,180 bytes / ~803 MB)

---

## 3. Dataset Characteristics & Limitations
- **Image Count:** 3,200 high-resolution original images across 16 balanced classes (exactly 200 images per class).
- **Native Resolution:** 4160 × 3120 pixels (RGB JPEG).
- **Limitations:**
  - Collected in controlled studio backgrounds; lighting and backdrop variations across commercial food banks may affect inference.
  - Contains whole fruits only; does not evaluate sliced, diced, cooked, or processed foods.
  - S3 download throughput from the host environment is 0.27–0.97 MB/s, requiring 2.8+ hours of sustained connection under firewall restrictions.

---

## 4. Class Definitions (16 Classes)
1. `fresh_apple` (Fresh Apple)
2. `rotten_apple` (Rotten Apple)
3. `fresh_banana` (Fresh Banana)
4. `rotten_banana` (Rotten Banana)
5. `fresh_orange` (Fresh Orange)
6. `rotten_orange` (Rotten Orange)
7. `fresh_grape` (Fresh Grape)
8. `rotten_grape` (Rotten Grape)
9. `fresh_guava` (Fresh Guava)
10. `rotten_guava` (Rotten Guava)
11. `fresh_jujube` (Fresh Jujube)
12. `rotten_jujube` (Rotten Jujube)
13. `fresh_pomegranate` (Fresh Pomegranate)
14. `rotten_pomegranate` (Rotten Pomegranate)
15. `fresh_strawberry` (Fresh Strawberry)
16. `rotten_strawberry` (Rotten Strawberry)

---

## 5. Leakage Prevention Methodology
- **Source-Aware Partitioning:** Augmented images share identical root specimen identities (e.g., `FreshApple (12)`). Random image-level splitting introduces severe data leakage.
- **Protocol:** All transformations of a single physical fruit specimen are grouped together and assigned exclusively to either the training (70%), validation (15%), or test (15%) partition.

---

## 6. Training Configuration & Reproducibility
- **Backbone:** EfficientNet-B0 (pretrained on ImageNet-1k)
- **Input Dimension:** 224 × 224 × 3 (RGB)
- **Normalization:** ImageNet standard ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$)
- **Loss Function:** Cross-Entropy Loss with label smoothing (0.1)
- **Optimizer:** AdamW ($\text{lr} = 10^{-4}$, weight decay $10^{-2}$)
- **Batch Size:** 32
- **Early Stopping:** Patience = 5 epochs monitoring validation Macro-F1
- **Random Seed:** Deterministic fixed seed = 42
- **Standalone Pipeline:** [`ml/cv/train_fruit_classifier.py`](file:///d:/ReServeAi/ml/cv/train_fruit_classifier.py)
- **Environment Definition:** [`ml/cv/requirements-training.txt`](file:///d:/ReServeAi/ml/cv/requirements-training.txt)

---

## 7. Hardware & Infrastructure Requirements
- **Target Compute:** NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MiB VRAM), CUDA 13.0
- **Dedicated Volume:** Drive `D:` (~110 GB free)
- **System Drive Policy:** Drive `C:` (6.46 GB free) must NOT be used for dataset staging or large wheel caching.

---

## 8. Current Metrics & Operational Status
- **Current Active Model:** `spectral-spatial-v2.1-SIMULATED`
- **Model Status:** `simulated` (Active Colorimetric Decomposition)
- **Simulated Notice:** *"SIMULATED — Spectral-Spatial Colorimetric CV (No pre-trained CNN weights loaded). Human inspector sign-off is mandatory before redistribution."*
- **Trained Deep Learning Metrics:** Pending out-of-band staging of `Original Image.zip` on `D:\ReServeAi\data\raw\fruits\`.

---

## 9. Critical Scope Limitations & Safety Mandates
- **PROHIBITED CLAIMS:**
  - DO NOT claim universal food freshness.
  - DO NOT claim microbial pathogen detection (e.g., Salmonella, E. coli, Listeria).
  - DO NOT claim food safety certification.
  - DO NOT evaluate prepared, cooked, or restaurant meals.
  - DO NOT evaluate meat or dairy products (meat is handled by the dedicated E-Nose beef model).
- **MANDATORY HUMAN VERIFICATION:** Visual classification is strictly an advisory screening heuristic. Certified human inspector sign-off is legally required under FSSAI protocols before redistributing produce.

---

## 10. Artifact Storage
- **Artifact Path:** `models/quality/fruit_classifier.pt`
- **Dynamic Loader:** [`cv/freshness_classifier.py`](file:///d:/ReServeAi/cv/freshness_classifier.py) automatically validates and activates the model when valid weights are present on disk.
