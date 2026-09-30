# Capacitated Vehicle Routing Problem (CVRP) Benchmark Report

**Benchmark Date:** 2026-09-30T20:11:36Z  
**Source:** CVRPLIB (PUC-Rio, https://galgos.inf.puc-rio.br/cvrplib/)  
**Feasibility:** 100% FEASIBLE (0 capacity violations across all instances)  
**Baseline Greedy Gap:** +40.24% vs Best Known Solution (BKS)  
**Improved (Clarke-Wright + 2-Opt) Gap:** **+4.07%** vs BKS  
**Mean Distance Reduction:** **25.72%**  

---

## 1. Baseline Performance (Greedy Nearest-Neighbor)

| Instance | Size | Customers | Capacity | Greedy Dist | BKS Dist | Optimality Gap | Greedy Veh | BKS Veh | Runtime (ms) | Feasible |
|---|---|---|---|---|---|---|---|---|---|---|
| **A-n32-k5** | Small | 31 | 100 | 1145.0 | 784 | **+46.05%** | 5 | 5 | 0.29 | [OK] |
| **A-n33-k5** | Small | 32 | 100 | 977.0 | 661 | **+47.81%** | 5 | 5 | 0.3 | [OK] |
| **A-n33-k6** | Small | 32 | 100 | 1042.0 | 742 | **+40.43%** | 6 | 6 | 0.31 | [OK] |
| **A-n55-k9** | Medium | 54 | 100 | 1500.0 | 1073 | **+39.79%** | 9 | 9 | 0.8 | [OK] |
| **A-n60-k9** | Medium | 59 | 100 | 1837.0 | 1354 | **+35.67%** | 9 | 9 | 0.9 | [OK] |
| **A-n63-k9** | Medium | 62 | 100 | 2188.0 | 1616 | **+35.4%** | 9 | 9 | 0.97 | [OK] |
| **A-n80-k10** | Large | 79 | 100 | 2348.0 | 1763 | **+33.18%** | 10 | 10 | 1.58 | [OK] |
| **B-n50-k7** | Medium | 49 | 100 | 1036.0 | 741 | **+39.81%** | 7 | 7 | 0.68 | [OK] |
| **B-n78-k10** | Large | 77 | 100 | 1758.0 | 1221 | **+43.98%** | 10 | 10 | 2.35 | [OK] |
