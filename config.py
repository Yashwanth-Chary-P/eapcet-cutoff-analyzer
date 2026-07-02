from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets"
OUTPUT_DIR = BASE_DIR / "output"

# Input Files
WEB_OPTIONS_PDF = DATASET_DIR / "TSEAMCET-2026+WEBOPTIONS new.pdf"
LAST_RANKS_PDF = DATASET_DIR / "TGEAPCET_2025_FINALPHASE_LASTRANKS.pdf"

# Output Directories
MERGED_DIR = OUTPUT_DIR / "merged"
CATEGORY_DIR = OUTPUT_DIR / "category_cutoffs"
PDF_DIR = OUTPUT_DIR / "pdf"

# Output Files
WEB_OPTIONS_RAW_CSV = OUTPUT_DIR / "web_options_raw.csv"
LAST_RANKS_RAW_CSV = OUTPUT_DIR / "last_ranks_raw.csv"
WEB_OPTIONS_CLEAN_CSV = OUTPUT_DIR / "web_options_clean.csv"
LAST_RANKS_CLEAN_CSV = OUTPUT_DIR / "last_ranks_clean.csv"
UNMATCHED_CSV = OUTPUT_DIR / "unmatched_records.csv"
VERIFICATION_REPORT = OUTPUT_DIR / "verification_report.txt"

FINAL_CSV = MERGED_DIR / "web_options_with_cutoffs.csv"
FINAL_EXCEL = MERGED_DIR / "web_options_with_cutoffs.xlsx"

# Configuration
USE_CAMELOT = False
SAVE_INTERMEDIATE = True
