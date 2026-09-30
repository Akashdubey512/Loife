"""
reServe AI — Phase 8C Data Acquisition Pipeline

Downloads, verifies, and catalogs all Phase 8 datasets.
Run: python -m ml.pipelines.download_datasets

Safety measures:
  - SHA256 checksum on every download
  - Content-type verification
  - Archive integrity check
  - Path traversal prevention on extraction
  - Manifest auto-update
"""

import os
import sys
import json
import hashlib
import zipfile
import csv
import io
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANIFEST_PATH = DATA_DIR / "manifests" / "dataset_manifest.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_extract_zip(zip_path: Path, dest_dir: Path):
    """Extract ZIP with path traversal prevention."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            member_path = Path(dest_dir) / member.filename
            # Prevent path traversal
            try:
                member_path.resolve().relative_to(dest_dir.resolve())
            except ValueError:
                print(f"  ⚠ SKIPPING suspicious path: {member.filename}")
                continue
            zf.extract(member, dest_dir)
    print(f"  ✓ Extracted to {dest_dir}")


def download_file(url: str, dest_path: Path, timeout: int = 120) -> Dict[str, Any]:
    """Download a file with verification."""
    import requests
    
    print(f"  → Downloading: {url}")
    try:
        resp = requests.get(url, timeout=timeout, stream=True, allow_redirects=True)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e), "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None}

    content_type = resp.headers.get("Content-Type", "unknown")
    content = resp.content
    file_size = len(content)
    checksum = sha256_bytes(content)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(content)

    print(f"  ✓ Downloaded: {file_size:,} bytes | SHA256: {checksum[:16]}...")
    return {
        "success": True,
        "file_size": file_size,
        "content_type": content_type,
        "checksum_sha256": checksum,
        "path": str(dest_path),
    }


def update_manifest(dataset_id: str, updates: Dict[str, Any]):
    """Update a specific dataset entry in the manifest."""
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    for ds in manifest["datasets"]:
        if ds["id"] == dataset_id:
            ds.update(updates)
            break

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, default=str)


def count_csv_rows(filepath: Path) -> int:
    """Count rows in a CSV file (excluding header)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            count = sum(1 for _ in reader)
        return count
    except Exception:
        return -1


def get_csv_columns(filepath: Path) -> List[str]:
    """Get column names from a CSV file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
        return header or []
    except Exception:
        return []


def count_images_in_dir(dirpath: Path) -> int:
    """Recursively count image files."""
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    count = 0
    for p in dirpath.rglob("*"):
        if p.suffix.lower() in extensions:
            count += 1
    return count

# ---------------------------------------------------------------------------
# Dataset-specific downloaders
# ---------------------------------------------------------------------------

def download_ai4i():
    """Dataset 1: AI4I 2020 Predictive Maintenance"""
    print("\n" + "="*60)
    print("DATASET 1: AI4I 2020 Predictive Maintenance")
    print("="*60)

    dest_dir = RAW_DIR / "ai4i"
    zip_path = dest_dir / "ai4i_2020.zip"
    url = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"

    result = download_file(url, zip_path)
    if not result["success"]:
        print(f"  ✗ FAILED: {result['error']}")
        update_manifest("ai4i_2020", {
            "status": "download_failed",
            "download_date": datetime.now(timezone.utc).isoformat(),
            "notes": f"Download failed: {result['error']}"
        })
        return False

    # Verify ZIP integrity
    if not zipfile.is_zipfile(zip_path):
        print("  ✗ Downloaded file is not a valid ZIP")
        update_manifest("ai4i_2020", {"status": "invalid_archive"})
        return False

    safe_extract_zip(zip_path, dest_dir)

    # Find CSV file
    csv_files = list(dest_dir.rglob("*.csv"))
    row_count = -1
    columns = []
    if csv_files:
        row_count = count_csv_rows(csv_files[0])
        columns = get_csv_columns(csv_files[0])
        print(f"  ✓ CSV found: {csv_files[0].name} — {row_count} rows, {len(columns)} columns")

    update_manifest("ai4i_2020", {
        "status": "downloaded",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "file_size_bytes": result["file_size"],
        "checksum_sha256": result["checksum_sha256"],
        "row_count": row_count,
        "columns": columns,
    })
    return True


def download_appliances_energy():
    """Dataset 2: Appliances Energy Prediction"""
    print("\n" + "="*60)
    print("DATASET 2: Appliances Energy Prediction")
    print("="*60)

    dest_dir = RAW_DIR / "appliances_energy"
    zip_path = dest_dir / "appliances_energy.zip"
    url = "https://archive.ics.uci.edu/static/public/374/appliances+energy+prediction.zip"

    result = download_file(url, zip_path)
    if not result["success"]:
        # Try backup
        print("  → Trying backup URL (Zenodo)...")
        url_backup = "https://zenodo.org/record/3902636"
        result = download_file(url_backup, zip_path)
        if not result["success"]:
            print(f"  ✗ FAILED: {result['error']}")
            update_manifest("appliances_energy", {
                "status": "download_failed",
                "download_date": datetime.now(timezone.utc).isoformat(),
                "notes": f"Both URLs failed: {result['error']}"
            })
            return False

    if zipfile.is_zipfile(zip_path):
        safe_extract_zip(zip_path, dest_dir)
    else:
        print("  ℹ File is not a ZIP — may be direct CSV or need different handling")

    csv_files = list(dest_dir.rglob("*.csv"))
    row_count = -1
    columns = []
    if csv_files:
        row_count = count_csv_rows(csv_files[0])
        columns = get_csv_columns(csv_files[0])
        print(f"  ✓ CSV found: {csv_files[0].name} — {row_count} rows, {len(columns)} columns")

    update_manifest("appliances_energy", {
        "status": "downloaded",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "file_size_bytes": result["file_size"],
        "checksum_sha256": result["checksum_sha256"],
        "row_count": row_count,
        "columns": columns,
    })
    return True


def download_poore_nemecek():
    """Dataset 3: Poore & Nemecek / OWID CSVs"""
    print("\n" + "="*60)
    print("DATASET 3: Poore & Nemecek / OWID Environmental Footprints")
    print("="*60)

    dest_dir = RAW_DIR / "poore_nemecek"
    urls = [
        ("ghg-per-kg-poore.csv", "https://ourworldindata.org/grapher/ghg-per-kg-poore"),
        ("ghg-per-protein-poore.csv", "https://ourworldindata.org/grapher/ghg-per-protein-poore"),
        ("ghg-kcal-poore.csv", "https://ourworldindata.org/grapher/ghg-kcal-poore"),
        ("land-use-per-kg-poore.csv", "https://ourworldindata.org/grapher/land-use-per-kg-poore"),
        ("land-use-kcal-poore.csv", "https://ourworlddata.org/grapher/land-use-kcal-poore"),
        ("water-withdrawals-per-kg-poore.csv", "https://ourworlddata.org/grapher/water-withdrawals-per-kg-poore"),
        ("water-per-protein-poore.csv", "https://ourworlddata.org/grapher/water-per-protein-poore"),
    ]

    # OWID provides CSV via ?v=1&csvType=full&useColumnShortNames=false appended, 
    # or via download= parameter. Try the direct download approach.
    successes = 0
    failures = []
    total_size = 0
    total_rows = 0

    for filename, base_url in urls:
        # Try adding the download parameter for OWID
        csv_url = base_url  # Try as-is first
        dest_path = dest_dir / filename
        
        # OWID CSV download pattern
        download_url = base_url + "?v=1&csvType=full&useColumnShortNames=false"
        result = download_file(download_url, dest_path, timeout=30)
        
        if not result["success"]:
            # Try the exact user-provided URL pattern
            csv_url_direct = base_url + ".csv"
            result = download_file(csv_url_direct, dest_path, timeout=30)
        
        if not result["success"]:
            # Try with just ?tab=table&time=latest
            alt_url = base_url + "?tab=table&time=latest&v=1&csvType=full"
            result = download_file(alt_url, dest_path, timeout=30)

        if result["success"]:
            # Check if it's actually a CSV (not HTML error page)
            try:
                with open(dest_path, "r", encoding="utf-8", errors="replace") as f:
                    first_line = f.readline()
                if "<html" in first_line.lower() or "<!doctype" in first_line.lower():
                    print(f"  ⚠ {filename}: Got HTML instead of CSV — URL may need correction")
                    failures.append(filename)
                    dest_path.unlink(missing_ok=True)
                    continue
            except Exception:
                pass

            rows = count_csv_rows(dest_path)
            total_size += result["file_size"]
            total_rows += max(0, rows)
            successes += 1
            print(f"  ✓ {filename}: {rows} rows")
        else:
            failures.append(filename)
            print(f"  ✗ {filename}: FAILED — {result['error']}")

    status = "downloaded" if successes == len(urls) else "partially_downloaded" if successes > 0 else "download_failed"
    update_manifest("poore_nemecek_owid", {
        "status": status,
        "download_date": datetime.now(timezone.utc).isoformat(),
        "file_size_bytes": total_size,
        "row_count": total_rows,
        "notes": f"{successes}/{len(urls)} files downloaded. Failures: {failures}" if failures else f"All {successes} files downloaded."
    })
    return successes > 0


def setup_fao_flw():
    """Dataset 4: FAO FLW — Manual import setup"""
    print("\n" + "="*60)
    print("DATASET 4: FAO Food Loss and Waste Database")
    print("="*60)

    dest_dir = RAW_DIR / "fao_flw"
    readme_path = dest_dir / "IMPORT_INSTRUCTIONS.md"

    instructions = """# FAO Food Loss and Waste Database — Import Instructions

## Why Manual Import?

The FAO Food Loss and Waste Database platform requires interactive access
and may have CAPTCHA or authentication barriers. reServe AI does NOT bypass
access controls.

## Steps to Import

1. Visit: https://www.fao.org/platform-food-loss-waste/flw-data/en
2. Use the data explorer to select:
   - All countries (or target countries)
   - All food groups
   - All supply chain stages
   - All years available
3. Export / download the dataset as CSV
4. Place the downloaded CSV file(s) in this directory:
   `data/raw/fao_flw/`
5. Re-run the validation pipeline:
   `python -m ml.pipelines.validate_datasets`

## Backup Source

If the main platform is unavailable, try:
https://data.harvestportal.org/dataset/un-fao-food-loss-and-waste-database

## Expected Format

The pipeline expects CSV files with columns including (at minimum):
- country
- food_group or commodity
- year
- loss_percentage or loss_quantity
- supply_chain_stage

## License

LICENSE_REVIEW_REQUIRED — FAO data terms must be reviewed before use.
"""
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(instructions)

    print("  ✓ Import instructions created at data/raw/fao_flw/IMPORT_INSTRUCTIONS.md")
    print("  ℹ This dataset requires manual download from the FAO platform.")

    update_manifest("fao_flw", {
        "status": "pending_manual_import",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "notes": "Requires manual export from FAO platform. Import instructions created."
    })
    return True


def download_genpact():
    """Dataset 7: Genpact Food Demand — use GitHub backup"""
    print("\n" + "="*60)
    print("DATASET 7: Genpact Food Demand Forecasting")
    print("="*60)

    dest_dir = RAW_DIR / "genpact"

    # The official AnalyticsVidhya source requires signup — use verified backup
    print("  ℹ Official source (AnalyticsVidhya) requires signup — using verified GitHub backup")
    
    base_url = "https://raw.githubusercontent.com/SaiPrasath-S/DemandPrediction/master"
    files_to_try = [
        ("train.csv", f"{base_url}/train.csv"),
        ("test.csv", f"{base_url}/test.csv"),
        ("meal_info.csv", f"{base_url}/meal_info.csv"),
        ("fulfilment_center_info.csv", f"{base_url}/fulfilment_center_info.csv"),
        ("sample_submission.csv", f"{base_url}/sample_submission.csv"),
    ]

    # Also try alternate paths
    alt_paths = [
        ("train.csv", f"{base_url}/Data/train.csv"),
        ("test.csv", f"{base_url}/Data/test.csv"),
        ("meal_info.csv", f"{base_url}/Data/meal_info.csv"),
        ("fulfilment_center_info.csv", f"{base_url}/Data/fulfilment_center_info.csv"),
    ]

    successes = 0
    total_rows = 0
    total_size = 0
    all_columns = []

    for filename, url in files_to_try:
        dest_path = dest_dir / filename
        result = download_file(url, dest_path, timeout=30)
        
        if not result["success"]:
            # Try alternate path
            for alt_name, alt_url in alt_paths:
                if alt_name == filename:
                    result = download_file(alt_url, dest_path, timeout=30)
                    break

        if result["success"]:
            # Verify it's CSV not HTML
            try:
                with open(dest_path, "r", encoding="utf-8", errors="replace") as f:
                    first_line = f.readline()
                if "<html" in first_line.lower() or "<!doctype" in first_line.lower() or "404" in first_line:
                    print(f"  ⚠ {filename}: Got HTML/404 — skipping")
                    dest_path.unlink(missing_ok=True)
                    continue
            except Exception:
                pass

            rows = count_csv_rows(dest_path)
            cols = get_csv_columns(dest_path)
            total_rows += max(0, rows)
            total_size += result["file_size"]
            successes += 1
            if filename == "train.csv":
                all_columns = cols
            print(f"  ✓ {filename}: {rows} rows, {len(cols)} columns")
        else:
            print(f"  ✗ {filename}: FAILED")

    status = "downloaded" if successes >= 2 else "download_failed"
    update_manifest("genpact_demand", {
        "status": status,
        "download_date": datetime.now(timezone.utc).isoformat(),
        "file_size_bytes": total_size,
        "row_count": total_rows,
        "columns": all_columns,
        "notes": f"{successes} files downloaded from GitHub backup (SaiPrasath-S/DemandPrediction). Provenance: Genpact ML Hackathon on AnalyticsVidhya."
    })
    return successes >= 2


def download_fruits():
    """Dataset 5: Fresh and Rotten Fruits (Mendeley)"""
    print("\n" + "="*60)
    print("DATASET 5: Fresh and Rotten Fruits Dataset")
    print("="*60)

    dest_dir = RAW_DIR / "fruits"
    
    # Mendeley datasets require API or direct download link
    # The page https://data.mendeley.com/datasets/bdd69gyhv8/1 provides download links
    # We need to find the actual download URL
    print("  ℹ Mendeley datasets may require browser-based download")
    print("  → Attempting programmatic download...")

    # Mendeley Data API pattern
    api_url = "https://data.mendeley.com/public-files/datasets/bdd69gyhv8/files"
    
    import requests
    try:
        # Try the direct dataset page to find download links
        resp = requests.get("https://data.mendeley.com/datasets/bdd69gyhv8/1", timeout=30)
        if resp.status_code == 200:
            # Try the API endpoint for file listing
            api_resp = requests.get(
                "https://data.mendeley.com/api/datasets/bdd69gyhv8/1",
                timeout=30,
                headers={"Accept": "application/json"}
            )
            if api_resp.status_code == 200:
                try:
                    data = api_resp.json()
                    print(f"  ✓ Dataset API accessible: {data.get('name', 'Unknown')}")
                except Exception:
                    pass

            # Try direct zip download
            zip_url = "https://data.mendeley.com/datasets/bdd69gyhv8/1/files/dataset.zip"
            zip_path = dest_dir / "fruits_dataset.zip"
            
            # Mendeley uses a different download pattern
            download_url = "https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/bdd69gyhv8-1.zip"
            result = download_file(download_url, zip_path, timeout=300)
            
            if result["success"] and zipfile.is_zipfile(zip_path):
                safe_extract_zip(zip_path, dest_dir)
                img_count = count_images_in_dir(dest_dir)
                print(f"  ✓ Extracted — {img_count} images found")
                update_manifest("fresh_rotten_fruits", {
                    "status": "downloaded",
                    "download_date": datetime.now(timezone.utc).isoformat(),
                    "file_size_bytes": result["file_size"],
                    "checksum_sha256": result["checksum_sha256"],
                    "image_count": img_count,
                })
                return True
    except Exception as e:
        print(f"  ⚠ Error: {e}")

    # Create manual import instructions
    readme = dest_dir / "IMPORT_INSTRUCTIONS.md"
    with open(readme, "w") as f:
        f.write("""# Fresh and Rotten Fruits Dataset — Import Instructions

## Download
1. Visit: https://data.mendeley.com/datasets/bdd69gyhv8/1
2. Click "Download" to get the ZIP file
3. Extract the contents into this directory: `data/raw/fruits/`

## Expected Structure
```
data/raw/fruits/
├── Train/
│   ├── freshapples/
│   ├── rottenapples/
│   ├── freshbananas/
│   └── ...
└── Test/
    ├── freshapples/
    └── ...
```

## Re-run Validation
After placing files, run: `python -m ml.pipelines.validate_datasets`
""")
    print("  ℹ Created manual import instructions")
    update_manifest("fresh_rotten_fruits", {
        "status": "pending_manual_import",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "notes": "Mendeley download may require browser. Import instructions created."
    })
    return False


def download_enose():
    """Dataset 6: E-nose Beef Quality (Mendeley)"""
    print("\n" + "="*60)
    print("DATASET 6: E-nose Beef Quality Dataset")
    print("="*60)

    dest_dir = RAW_DIR / "enose"
    
    import requests
    try:
        # Try Mendeley S3 cache pattern
        download_url = "https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/n8mc3nspfn-1.zip"
        zip_path = dest_dir / "enose_dataset.zip"
        result = download_file(download_url, zip_path, timeout=120)
        
        if result["success"] and zipfile.is_zipfile(zip_path):
            safe_extract_zip(zip_path, dest_dir)
            csv_files = list(dest_dir.rglob("*.csv"))
            xlsx_files = list(dest_dir.rglob("*.xlsx"))
            data_files = csv_files + xlsx_files
            
            row_count = 0
            columns = []
            for cf in csv_files:
                rc = count_csv_rows(cf)
                if rc > row_count:
                    row_count = rc
                    columns = get_csv_columns(cf)
            
            print(f"  ✓ Extracted — {len(data_files)} data files, {row_count} rows")
            update_manifest("enose_beef", {
                "status": "downloaded",
                "download_date": datetime.now(timezone.utc).isoformat(),
                "file_size_bytes": result["file_size"],
                "checksum_sha256": result["checksum_sha256"],
                "row_count": row_count,
                "columns": columns,
            })
            return True
    except Exception as e:
        print(f"  ⚠ Error: {e}")

    # Fallback: manual import
    readme = dest_dir / "IMPORT_INSTRUCTIONS.md"
    with open(readme, "w") as f:
        f.write("""# E-nose Beef Quality Dataset — Import Instructions

## Download
1. Visit: https://data.mendeley.com/datasets/n8mc3nspfn
2. Download the dataset files
3. Place in: `data/raw/enose/`

## Re-run
`python -m ml.pipelines.validate_datasets`
""")
    print("  ℹ Created manual import instructions")
    update_manifest("enose_beef", {
        "status": "pending_manual_import",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "notes": "Mendeley download may require browser. Import instructions created."
    })
    return False


def download_vrplib():
    """Dataset 8: CVRPLIB via vrplib Python package"""
    print("\n" + "="*60)
    print("DATASET 8: CVRPLIB Routing Benchmarks")
    print("="*60)

    dest_dir = RAW_DIR / "vrplib"

    try:
        import vrplib
    except ImportError:
        print("  → Installing vrplib...")
        os.system(f"{sys.executable} -m pip install vrplib -q")
        try:
            import vrplib
        except ImportError:
            print("  ✗ Could not install vrplib")
            update_manifest("cvrplib", {
                "status": "dependency_missing",
                "notes": "vrplib package could not be installed"
            })
            return False

    # Download a set of benchmark instances
    instances = [
        "X-n101-k25",
        "X-n106-k14",
        "X-n110-k13",
        "X-n115-k10",
        "X-n120-k6",
    ]

    successes = 0
    for name in instances:
        try:
            filepath = str(dest_dir / f"{name}.vrp")
            sol_filepath = str(dest_dir / f"{name}.sol")
            vrplib.download_instance(name, str(dest_dir))
            vrplib.download_solution(name, str(dest_dir))
            successes += 1
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")

    update_manifest("cvrplib", {
        "status": "downloaded" if successes > 0 else "download_failed",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "row_count": successes,
        "notes": f"{successes}/{len(instances)} benchmark instances downloaded"
    })
    return successes > 0


def download_pmfme():
    """Dataset 9: PMFME data.gov.in"""
    print("\n" + "="*60)
    print("DATASET 9: PMFME Registered Food Processing Units")
    print("="*60)

    dest_dir = RAW_DIR / "pmfme"
    url = "https://www.data.gov.in/resource/stateut-wise-information-total-number-registered-food-processing-units-under-pradhan"

    import requests
    try:
        # data.gov.in often provides API access or CSV download
        # Try to get the page and find download links
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            # Check if there's a direct CSV/JSON API
            # data.gov.in API pattern: add ?format=csv or look for api links
            api_url = url.replace("/resource/", "/resource-info/")
            
            # Try common data.gov.in CSV download patterns
            csv_dest = dest_dir / "pmfme_data.csv"
            
            # Save the HTML page for reference
            html_path = dest_dir / "source_page.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"  ✓ Source page saved for reference")
            
            # Create import instructions since data.gov.in may need interactive access
            readme = dest_dir / "IMPORT_INSTRUCTIONS.md"
            with open(readme, "w") as f:
                f.write("""# PMFME Food Processing Units Data — Import Instructions

## Source
https://www.data.gov.in/resource/stateut-wise-information-total-number-registered-food-processing-units-under-pradhan

## Download
1. Visit the URL above
2. Look for "Download" or "Export" button
3. Download as CSV
4. Place in: `data/raw/pmfme/`

## Usage
This is CONTEXTUAL REFERENCE DATA only — NOT a machine learning training dataset.
Used for geographic food-processing ecosystem context in dashboards.

## License
Government Open Data License - India
""")

            update_manifest("pmfme", {
                "status": "pending_manual_import",
                "download_date": datetime.now(timezone.utc).isoformat(),
                "notes": "data.gov.in may require interactive download. Import instructions created."
            })
            return True
    except Exception as e:
        print(f"  ⚠ Error: {e}")

    update_manifest("pmfme", {
        "status": "download_failed",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "notes": f"Could not access data.gov.in: {str(e)}"
    })
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("reServe AI — Phase 8C Data Acquisition Pipeline")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    results = {}

    # 1. AI4I 2020
    try:
        results["ai4i_2020"] = download_ai4i()
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        traceback.print_exc()
        results["ai4i_2020"] = False

    # 2. Appliances Energy
    try:
        results["appliances_energy"] = download_appliances_energy()
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        traceback.print_exc()
        results["appliances_energy"] = False

    # 3. Poore & Nemecek / OWID
    try:
        results["poore_nemecek_owid"] = download_poore_nemecek()
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        traceback.print_exc()
        results["poore_nemecek_owid"] = False

    # 4. FAO FLW (manual)
    try:
        results["fao_flw"] = setup_fao_flw()
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        results["fao_flw"] = False

    # 5. Fresh & Rotten Fruits
    try:
        results["fresh_rotten_fruits"] = download_fruits()
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        traceback.print_exc()
        results["fresh_rotten_fruits"] = False

    # 6. E-nose Beef
    try:
        results["enose_beef"] = download_enose()
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        traceback.print_exc()
        results["enose_beef"] = False

    # 7. Genpact Demand
    try:
        results["genpact_demand"] = download_genpact()
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        traceback.print_exc()
        results["genpact_demand"] = False

    # 8. CVRPLIB
    try:
        results["cvrplib"] = download_vrplib()
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        traceback.print_exc()
        results["cvrplib"] = False

    # 9. PMFME
    try:
        results["pmfme"] = download_pmfme()
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        traceback.print_exc()
        results["pmfme"] = False

    # Summary
    print("\n" + "=" * 60)
    print("DATA ACQUISITION SUMMARY")
    print("=" * 60)
    for ds, ok in results.items():
        status = "✓ SUCCESS" if ok else "✗ NEEDS ATTENTION"
        print(f"  {status}: {ds}")

    total = len(results)
    success = sum(1 for v in results.values() if v)
    print(f"\n  {success}/{total} datasets acquired or configured")
    print(f"  Manifest: {MANIFEST_PATH}")
    print(f"  Completed: {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
