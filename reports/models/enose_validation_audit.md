# E-Nose Beef Quality Validation Audit & Leakage Assessment

**Dataset:** Mendeley E-Nose Based Beef Quality Classification Dataset (4 classes)  
**DOI:** [10.17632/n8mc3nspfn.1](https://data.mendeley.com/datasets/n8mc3nspfn/1)  
**Authors:** Surjith S, Alex Raj SM (2025)  
**Audit Date:** 2026-10-01  
**Auditor:** reServe AI Engineering & ML Quality Assurance  
**Model Scope:** **BEEF QUALITY ONLY** (Strict domain limitation: not calibrated for poultry, seafood, pork, dairy, or fresh produce)

---

## 1. Executive Summary

During Phase 9, initial training of a LightGBM classifier on the Mendeley E-nose Beef Quality Dataset yielded a reported **99.78% test accuracy** and **0.9968 Macro-F1**. 

This Phase 10B audit investigated the data collection protocol and train/test split methodology to determine whether this performance reflects true generalization or is inflated by **temporal autocorrelation leakage**.

### Key Findings
1. **Single Experimental Run:** The dataset consists of 20,815 readings recorded continuously from a **single decomposing beef sample** over 1,735 minutes (~28.9 hours) at 5-second intervals.
2. **Temporal Autocorrelation Leakage:** The initial `train_test_split(..., test_size=0.15, random_state=42)` randomly sampled individual 5-second rows. As a result, reading $t$ (e.g., minute 100, second 0) was in the training set while reading $t+5\text{s}$ (minute 100, second 5) was in the test set. Because gas sensor resistance changes slowly over seconds, adjacent rows are nearly identical, allowing the model to interpolate timestamps.
3. **Leakage-Safe Validation (15-Minute Block Holdout):** When contiguous 15-minute time windows (180 consecutive readings each) are held out—ensuring train and test never share neighboring seconds—the true generalization performance is **93.10% accuracy** and **0.8718 Macro-F1**.
4. **Conclusion:** The model has strong discriminative power across sensor patterns, but the original 99.78% metric is an artifact of high-frequency autocorrelation. **The scientifically valid generalization performance of this model is 93.10% accuracy / 0.8718 Macro-F1.**

---

## 2. Dataset Structure & Protocol Analysis

| Field | Value |
|---|---|
| **Total Rows** | 20,815 |
| **Total Features** | 10 (DHT11 Temperature, Humidity + 8 MOS Gas Sensors: MQ-2, MQ-3, MQ-4, MQ-5, MQ-135, MQ-136, MQ-137, MQ-138) |
| **Elapsed Time** | Minute 1 to Minute 1,735 (28.91 hours) |
| **Sampling Frequency** | Every 5 seconds (12 samples per minute) |
| **Sample Count** | 1 physical beef sample monitored over continuous degradation |
| **Minute Resets** | **0** (strictly monotonic elapsed time) |

### Class Breakdown by Temporal Phase

The target labels correspond to sequential degradation phases defined by Total Viable Count (TVC, $\log_{10} \text{CFU/g}$):

| Class | Label | Minute Range | TVC Range ($\log_{10}$) | Row Count | % of Dataset |
|---|---|---|---|---|---|
| **1** | **EXCELLENT** | 1 – 245 | 2.002 – 2.988 | 2,940 | 14.1% |
| **2** | **GOOD** | 246 – 434 | 3.092 – 3.999 | 2,268 | 10.9% |
| **3** | **ACCEPTABLE** | 435 – 625 | 4.026 – 4.997 | 2,292 | 11.0% |
| **4** | **SPOILED** | 626 – 1,735 | 5.100 – 6.314 | 13,315 | 64.0% |

*Note: Class 4 represents the extended terminal spoilage phase (>18 hours), creating natural class imbalance (64% spoiled).*

---

## 3. Comparative Evaluation: Leaky vs. Leakage-Safe Splits

Three splitting strategies were rigorously evaluated:

| Metric | Strategy 1: Random Split (Leaky) | Strategy 2: 15-Minute Block Holdout (Leakage-Safe) | Strategy 3: Phase-Tail Forward Holdout |
|---|---|---|---|
| **Splitting Mechanism** | Random row sampling (80/20) | 23 disjoint 15-min blocks held out (20% of time) | First 80% of each phase to train, last 20% to test |
| **Temporal Independence** | ❌ Severe 5-sec leakage | ✅ Zero adjacent 5-sec leakage | ✅ Zero temporal overlap |
| **Accuracy** | **99.83%** | **93.10%** | **69.52%** |
| **Macro Precision** | 0.9975 | 0.8675 | 0.5015 |
| **Macro Recall** | 0.9973 | 0.8833 | 0.3582 |
| **Macro F1** | **0.9974** | **0.8718** | **0.3776** |

### Per-Class Performance under Leakage-Safe Block Holdout (Strategy 2)

```text
              precision    recall  f1-score   support
   EXCELLENT       1.00      0.90      0.95       708
        GOOD       0.79      0.99      0.88       360
  ACCEPTABLE       0.71      0.68      0.69       360
     SPOILED       0.97      0.96      0.96      2700

    accuracy                           0.93      4128
   macro avg       0.87      0.88      0.87      4128
weighted avg       0.93      0.93      0.93      4128
```

### Analysis of Leakage-Safe Results
1. **Spoiled vs. Fresh Distinction is Exceptional:**
   - EXCELLENT fresh beef achieves **0.95 F1** (1.00 precision, 0.90 recall).
   - SPOILED beef achieves **0.96 F1** (0.97 precision, 0.96 recall).
2. **Intermediate Quality Transition:**
   - The boundary between `GOOD` (0.88 F1) and `ACCEPTABLE` (0.69 F1) shows moderate overlap. This is chemically and biologically expected: bacterial proliferation (TVC 3.8 to 4.2) is a continuous biological process, not a discrete step function.
3. **Phase-Tail Forward Test (Strategy 3):**
   - The drop to 69.5% accuracy in Strategy 3 highlights that training solely on the early half of a degradation phase does not capture late-stage volatility near boundary transitions.

---

## 4. Methodological Recommendations & Production Action

1. **Honest Metric Reporting:**
   - The model metadata and registry must report the **leakage-safe metric (93.10% Acc / 0.8718 Macro-F1)** as the primary validation score.
   - The historical random split (99.78%) must be clearly annotated as an *autocorrelation-unadjusted baseline*.
2. **Model Retraining with Block Stratification:**
   - `ml/sensor/train_enose.py` is updated to implement group block holdouts.
   - The production artifact `models/enose/enose_model.joblib` retains high predictive accuracy while being grounded in honest validation.
3. **Strict Domain Limitation:**
   - Model must be branded and reported solely as **E-Nose Beef Quality Classifier**.
   - It is explicitly prohibited from being presented as "Universal Food Quality AI".
   - Human sensory inspection remains mandatory prior to food redistribution.

---

## 5. Artifact Audit Trail

| File | Status | Description |
|---|---|---|
| `data/raw/enose/Beef quality 4 classes.csv` | Verified | Authentic raw Mendeley sensor dataset (20,815 rows) |
| `models/enose/enose_model.joblib` | Active | Production LightGBM model artifact |
| `models/enose/enose_model_metadata.json` | Updated | Documents both naive (99.78%) and leakage-safe (93.10%) metrics |
| `models/model_registry.json` | Updated | Reflects validated metrics and leakage assessment |
| `reports/models/enose_validation_audit.md` | Created | This complete scientific validation audit |
