# EAPCET Cutoff Merger

This project merges two Telangana EAPCET PDFs containing complete cutoff information into a single CSV and Excel file.

## Project
The script parses "Web Options" and "Last Ranks" PDFs, extracts all tables using `pdfplumber` (with optional `camelot` fallback), cleans and normalizes the data, and performs a LEFT JOIN.

## Installation
Use Python 3.10+.
```bash
pip install -r requirements.txt
```

## Dependencies
- `pdfplumber`
- `pandas`
- `openpyxl`

*(Optional)* For camelot fallback, install `camelot-py[cv]` and ensure Ghostscript/Java dependencies are satisfied per your OS.

## Input Files

To run the pipeline, you must place the following input PDF files inside the `datasets/` directory (create the directory if it does not exist):

- `TSEAMCET-2026+WEBOPTIONS new.pdf` (The Web Options PDF)
- `TGEAPCET_2025_FINALPHASE_LASTRANKS.pdf` (The Last Ranks PDF)

*Note: The file names must match the above exactly, or you must update the names in `config.py` to match your files.*

## Execution
Run the following command without any user interaction:
```bash
python main.py
```

## Expected Outputs

After executing `main.py`, the `output/` directory will be created and populated with the following structure:

### 1. Merged Datasets (`output/merged/`)
The final combined data containing both the web options and the cutoff ranks.
- `web_options_with_cutoffs.csv`
- `web_options_with_cutoffs.xlsx`

### 2. Category Cutoffs (`output/category_cutoffs/`)
Isolated datasets for specific reservation categories (e.g., BC_B_GIRLS).
- `<CATEGORY_NAME>.csv`
- `<CATEGORY_NAME>.xlsx`

### 3. PDF Reports (`output/pdf/`)
Professionally formatted PDF reports generated from the processed data.
- `ALL_CATEGORIES.pdf`: Complete cutoff dataset report.
- `BC_B_GIRLS.pdf`: Category-specific report.
- `KEY_STATISTICS.pdf`: Key statistical metrics and phase comparison report.

### 4. Intermediate & Diagnostic Files (`output/`)
Files used for tracking unmatched records, verifying data integrity, and reviewing raw/cleaned extraction results.
- `web_options_raw.csv` & `last_ranks_raw.csv`
- `web_options_clean.csv` & `last_ranks_clean.csv`
- `unmatched_records.csv`: Records from Web Options that did not find a match in the Last Ranks data.
- `verification_report.txt`: Summary of matches and data discrepancies.

The console will also output a detailed Validation Summary containing metrics of the merge process.

## Troubleshooting
- **Missing PDFs:** Ensure the PDFs are correctly placed in the `datasets/` directory.
- **Dependency Issues:** Check that you are using a virtual environment and installed the dependencies via `pip install -r requirements.txt`.
- **Extraction Failures:** If `pdfplumber` struggles with the PDFs, you can enable Camelot by setting `USE_CAMELOT = True` in `config.py` (ensure you have installed `camelot-py[cv]`).
