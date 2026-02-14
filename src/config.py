from pathlib import Path
import os

# Detect Kaggle or Local
if os.path.exists("/kaggle"):
    PROJECT_ROOT = Path("/kaggle/working/skripsi-clir-code")
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
QUERIES_DIR = DATA_DIR / "queries"
INDICES_DIR = DATA_DIR / "indices"
RESULTS_DIR = PROJECT_ROOT / "results"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Optional
MODEL_DIR = PROJECT_ROOT / "models"

# Auto create folders if needed
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
