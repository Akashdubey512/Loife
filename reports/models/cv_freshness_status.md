# Computer Vision Fruit Freshness Classifier — Status & Feasibility Audit

**Audit Date:** 2026-10-01  
**Auditor:** reServe AI Engineering & ML Vision Team  
**Dataset:** Fresh and Rotten Fruits Dataset (Mendeley Data, DOI: [10.17632/bdd69gyhv8.1](https://data.mendeley.com/datasets/bdd69gyhv8/1))  
**Authors:** Sultana, Nusrat; Jahan, Musfika; Uddin, Mohammad Shorif (2022)  
**Current Production Status:** **`SIMULATION_MODE = True` (Active Colorimetric Spectral-Spatial Decomposition)**

---

## 1. Executive Summary

In Phase 10B, the team verified and inspected the official Mendeley Data S3 repositories for the Fresh and Rotten Fruits dataset. 

While the direct download endpoints are active and accessible, **deep learning model training (PyTorch/torchvision) is blocked by environment and storage constraints on the host system**:
1. Neither `torch` nor `torchvision` is installed in the system Python environment (Python 3.9.4).
2. The primary operating system drive (`C:`) has only **6.99 GB of free space**. Installing PyTorch, torchvision, CUDA/CPU dependencies, and pip wheel caches requires ~4–6 GB, presenting a high risk of host drive exhaustion.
3. The raw uncompressed original archive is **2.79 GB** (3,200 high-resolution 4160×3120 images), requiring ~84 minutes of sustained streaming at current network throughput (0.55 MB/s).

In accordance with Phase 10B core mandates:
- **No false claims of trained CNN weights are made.**
- `SIMULATION_MODE = True` remains active in `cv/freshness_classifier.py`.
- The API honestly returns `simulated: true`, `model_version: "spectral-spatial-v2.1-SIMULATED"`, and `human_verification_required: true`.

---

## 2. Dataset Architecture & Verification

Using remote ZIP central directory parsing, both official Mendeley archives were inspected:

### Archive 1: `Original Image.zip` (Ground Truth)
- **Direct S3 URL:** `https://prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com/5f1cbd0f-b19a-4e2a-a95d-b6a0f8dc47bb`
- **Archive Size:** 2,794,170,228 bytes (2.79 GB)
- **Total Images:** **3,200 images** (perfectly balanced: exactly 200 images per class)
- **Image Resolution:** 4160 × 3120 (RGB JPEG)
- **Classes (16 total):**
  - **Fresh (8 classes, 1,600 images):** `FreshApple`, `FreshBanana`, `FreshGrape`, `FreshGuava`, `FreshJujube`, `FreshOrange`, `FreshPomegranate`, `FreshStrawberry`
  - **Rotten (8 classes, 1,600 images):** `RottenApple`, `RottenBanana`, `RottenGrape`, `RottenGuava`, `RottenJujube`, `RottenOrange`, `RottenPomegranate`, `RottenStrawberry`

### Archive 2: `Augmented Image.zip`
- **Direct S3 URL:** `https://prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com/46dc9748-13da-45aa-89e8-ac2c9c846d02`
- **Archive Size:** 803,272,180 bytes (803.27 MB)
- **Total Images:** 12,335 images
- **Image Resolution:** 1020 × 1020 (RGB JPEG)
- **Audit Flag (Augmentation Contamination):** Inspection revealed filename prefix mismatches (e.g. `FreshOrange (1).jpg` placed inside the `FreshApple` folder). Splitting augmented images randomly across train/test would introduce severe source leakage.

---

## 3. Active Production Pipeline (`cv/freshness_classifier.py`)

Until an isolated GPU environment with PyTorch is provisioned:
1. **Spectral-Spatial Pixel Decomposition:**
   - Evaluates RGB and HSV channels directly from uploaded image bytes.
   - Analyzes enzymatic browning (polyphenol oxidase melanin reactions: Hue 8°–38°).
   - Detects necrotic lesions (cellular breakdown, Value < 0.22).
   - Quantifies fungal mycelium / mold blooms (cyan/green mildew and pale spore dust).
   - Calculates chromatic vibrancy ratio for carotenoid/chlorophyll retention.
2. **Honesty & Transparency:**
   - Clearly flags `simulated: true` on all scans.
   - Displays clear banner: *"SIMULATED — Spectral-Spatial Colorimetric CV (No pre-trained CNN weights loaded). Human inspector sign-off is mandatory before redistribution."*
   - Explicit domain restriction: **FRUIT FRESHNESS ONLY** (not valid for prepared meals, cooked food, meat, or universal food safety).

---

## 4. Path to Real CNN Training

When an environment with suitable GPU resources and disk headroom is allocated:
1. Provision isolated container/environment with PyTorch 2.x and torchvision.
2. Download `Original Image.zip` (3,200 clean images) to dedicated volume.
3. Perform a **patient-aware/source-aware split** (e.g., 70% train, 15% val, 15% test).
4. Fine-tune an **EfficientNet-B0** or **MobileNetV3** backbone using transfer learning.
5. Export ONNX / PyTorch weights to `models/quality/fruit_classifier.pt`.
6. Update `SIMULATION_MODE = False` only upon verified artifact loading.
