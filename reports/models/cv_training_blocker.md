# Computer Vision Fruit Freshness Classifier — Training Blocker & Infrastructure Report (Phase 12)

**Report Date:** 2026-10-01  
**Project:** reServe AI Quality Intelligence  
**Component:** Fruit Freshness Classifier  
**Status:** **SIMULATION_MODE = True (Honest Fallback Active)**  

---

## 1. Executive Summary

In Phase 12, an end-to-end attempt was made to train the **Fruit Freshness Classifier** on the physical workstation. In accordance with core project mandates against fabricating datasets, models, or performance metrics:

1. **The training is currently blocked by network egress throttling and firewall connection termination on the host network.**
2. The model remains in **transparent simulation mode** (`SIMULATION_MODE = True`), executing spectral-spatial colorimetric image decomposition.
3. The platform honestly returns `model_status: "simulated"` and enforces mandatory human verification (`human_verification_required: true`).
4. A complete, reproducible training pipeline ([`ml/cv/train_fruit_classifier.py`](file:///d:/ReServeAi/ml/cv/train_fruit_classifier.py)) and dependencies definition ([`ml/cv/requirements-training.txt`](file:///d:/ReServeAi/ml/cv/requirements-training.txt)) are fully staged on `D:` ready for execution once the dataset archive is staged.

---

## 2. Infrastructure & Hardware Audit

| Resource | Value / Specification | Status / Impact |
| :--- | :--- | :--- |
| **GPU Model** | NVIDIA GeForce RTX 3050 Laptop GPU | Active (Driver 581.86, CUDA 13.0) |
| **GPU VRAM** | 6,144 MiB (approx. 4,000 MiB free) | Sufficient for EfficientNet-B0 batch size 32 |
| **OS Drive (`C:`)** | **6.48 GB Free** | **CRITICAL HEADROOM CONSTRAINT** — Cannot stage archives or install CUDA PyTorch on `C:` without risking disk exhaustion |
| **Project Drive (`D:`)**| **110.58 GB Free** | **ADEQUATE** — Ample space for dedicated venv, datasets, and checkpoints |
| **Host Python** | Python 3.9.4 (64-bit) | `torch`, `torchvision`, and `cv2` are NOT installed |
| **Network Firewall** | FortiGate Firewall (`FG6H0FTB22905105`) | Enforces SSL inspection, blocks git push, drops persistent HTTP connections |

---

## 3. Dataset Download & Network Blocker

### Verified Mendeley S3 Archives
- **Original Images Archive:**  
  URL: `https://prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com/5f1cbd0f-b19a-4e2a-a95d-b6a0f8dc47bb`  
  Size: **2,794,170,228 bytes (2.79 GB / 2,664 MB)**  
  Content: 3,200 high-resolution original images (16 classes, 200 images/class @ 4160×3120).
- **Augmented Images Archive:**  
  URL: `https://prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com/46dc9748-13da-45aa-89e8-ac2c9c846d02`  
  Size: **803,272,180 bytes (803.27 MB)**  
  Content: 12,335 augmented images (1020×1020).

### Measured Transfer Throughput & Failure Mode
- **Live HTTP Range Benchmark:** 2.00 MB downloaded in 7.47 seconds = **0.27 MB/s (276 KB/s)**.
- **Estimated Streaming Duration:** $\frac{2,794\text{ MB}}{0.27\text{ MB/s}} \approx 10,348\text{ seconds} \approx \mathbf{2.87\text{ to }10.2\text{ hours}}$.
- **Failure Mode:** The host's corporate/campus FortiGate firewall intermittently resets long-running HTTP connections (`wsarecv: An established connection was aborted by the software in your host machine`). Multi-hour single-stream downloads fail midway with truncated or corrupted files.

---

## 4. Leakage-Safe Partitioning Methodology

When the dataset is staged, random splitting must **NOT** be permitted due to the severe source leakage identified during inspection:
1. **Source Grouping:** Augmented images must be linked back to their parent specimen identifier (e.g., `FreshApple (12)`).
2. **Disjoint Partition:** 70% of base specimens assigned to Training, 15% to Validation, 15% to Test.
3. Under no circumstances may an original image be placed in training while its rotated/scaled variants are placed in the test set.

---

## 5. Active Production Status & Safety Controls

Until genuine weights are trained and loaded:
1. **API Response:** `POST /api/v1/quality/scan` returns:
   - `model_status: "simulated"`
   - `simulated: true`
   - `model_architecture: "reServe-CV-SpectralSpatial-v2.1 (SIMULATED — Spectral-Spatial CV)"`
   - `human_verification_required: true`
   - `scope: "FRUIT_IMAGERY_ONLY"`
2. **Model Registry:** [`models/model_registry.json`](file:///d:/ReServeAi/models/model_registry.json) maintains status `unavailable` with explicit notice that genuine weights are not yet loaded.
3. **Frontend Dashboard:** Displays clear banners indicating simulated scoring and mandatory inspector verification before any food redistribution.

---

## 6. Actionable Resolution Protocol

To train the real model when external high-speed connectivity is available:

```bash
# 1. Download Original Image.zip (2.79 GB) via browser or high-speed downloader directly to D:
# Destination: D:\ReServeAi\data\raw\fruits\Original Image.zip

# 2. Extract into data/raw/fruits/
Expand-Archive -Path "D:\ReServeAi\data\raw\fruits\Original Image.zip" -DestinationPath "D:\ReServeAi\data\raw\fruits\extracted"

# 3. Create isolated virtualenv on D: with CUDA PyTorch
py -m venv D:\venv_fruit_cv
D:\venv_fruit_cv\Scripts\pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
D:\venv_fruit_cv\Scripts\pip install -r D:\ReServeAi\ml\cv\requirements-training.txt

# 4. Execute reproducible training script
D:\venv_fruit_cv\Scripts\python D:\ReServeAi\ml\cv\train_fruit_classifier.py --data-dir D:\ReServeAi\data\raw\fruits\extracted

# 5. Pipeline automatically exports weights to models/quality/fruit_classifier.pt
# Upon restart, cv/freshness_classifier.py dynamically detects the weights and switches to trained status.
```
