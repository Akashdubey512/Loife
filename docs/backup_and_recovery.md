# ReServeAI — Backup & Disaster Recovery Guide

## 1. Overview
This document specifies the backup and disaster recovery procedures for ReServeAI. The recovery scope encompasses the relational database (PostgreSQL in production, SQLite in development), machine learning model weights, and environment configuration.

---

## 2. Backup Scope & Retention Schedule

| Component | Target Location | Frequency | Retention | Tool / Command |
| :--- | :--- | :--- | :--- | :--- |
| **Production Database** | PostgreSQL (`reserve_ai_db`) | Hourly WAL / Daily Full | 30 Days | `pg_dump -Fc` / WAL archiving |
| **Development Database** | `reserve_ai.db` | On-demand before migration | 7 Days | SQLite Online Backup API |
| **Model Weights** | `models/*/`, `models/model_registry.json` | On model promotion | Indefinite | Git LFS / S3 versioned bucket |
| **Configuration** | `.env`, Nginx configs | On modification | Indefinite | Encrypted Vault / KMS |

---

## 3. Database Backup Procedures

### A. Production PostgreSQL Backup
```bash
# Full compressed database dump
pg_dump -U reserve_user -h localhost -F c -b -v -f "/var/backups/reserveai/db_$(date +%Y%m%d_%H%M%S).dump" reserve_ai_db
```

### B. Development SQLite Backup (Non-Blocking Online Copy)
Do not use raw OS file copies while the database is actively receiving write transactions. Use the SQLite online backup protocol:
```python
import sqlite3

def backup_sqlite(source_path="reserve_ai.db", backup_path="backups/backup.db"):
    src = sqlite3.connect(source_path)
    dst = sqlite3.connect(backup_path)
    src.backup(dst)
    dst.close()
    src.close()
```

---

## 4. Machine Learning Artifact Backup
Trained model artifacts are immutable and tied to specific git commits:
- `models/demand/`
- `models/maintenance/`
- `models/energy/`
- `models/sensor/`
- `models/model_registry.json`

Backup script:
```bash
tar -czvf "model_artifacts_$(date +%Y%m%d).tar.gz" models/
```

---

## 5. Recovery Procedures

### A. Restoring Production PostgreSQL
1. Terminate active application backend connections:
   ```bash
   systemctl stop reserveai-backend
   ```
2. Drop and recreate the database:
   ```sql
   DROP DATABASE reserve_ai_db;
   CREATE DATABASE reserve_ai_db OWNER reserve_user;
   ```
3. Restore from the chosen archive:
   ```bash
   pg_restore -U reserve_user -d reserve_ai_db -v "/var/backups/reserveai/db_20261001_000000.dump"
   ```
4. Restart application backend:
   ```bash
   systemctl start reserveai-backend
   ```

### B. Restoring SQLite
1. Stop backend service.
2. Replace `reserve_ai.db` with the verified backup copy:
   ```bash
   cp backups/reserve_ai_backup.db reserve_ai.db
   ```
3. Verify integrity:
   ```bash
   sqlite3 reserve_ai.db "PRAGMA integrity_check;"
   ```
4. Restart backend.

---

## 6. Verification & Disaster Testing
On 2026-10-01 (Phase 14 validation), the online backup and restore protocol was empirically verified:
- Source: `reserve_ai.db`
- Backup Integrity Check: `ok`
- Restored Database Integrity: `ok`
- Restored Table Count: 23 tables
- User Account Record Parity: 71 verified records preserved with zero corruption.

---

## 7. Recovery Limitations
1. **Fruit CV Model Artifacts:**
   Fruit CV is currently in simulation mode (`spectral-spatial-v2.1-SIMULATED`). No trained weights exist to restore.
2. **Waste ML Production Logs:**
   Because the live production database currently contains 0 real historical waste records, recovering the database will restore 0 waste records. Waste ML relies on rule-based fallback logic.
3. **Point-In-Time Recovery (PITR):**
   Available on PostgreSQL via WAL archiving; not supported on local single-file SQLite without third-party extension tools.
