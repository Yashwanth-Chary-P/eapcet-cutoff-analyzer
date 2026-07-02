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

## Folder Structure
- `datasets/`: Place your `TSEAMCET_2026_WEBOPTIONS.pdf` and `TGEAPCET_2025_FINALPHASE_LASTRANKS.pdf` here.
- `output/`: Generated CSV and Excel outputs will be placed here.
- `src/`: Contains extraction (`pdf_extract.py`), cleaning (`clean_data.py`), and merging (`merge_data.py`) modules.
- `config.py`: Centralized configuration.
- `main.py`: Entrypoint.

## Execution
Run the following command without any user interaction:
```bash
python main.py
```

## Expected Outputs
The `output/` directory will contain:
- `web_options_raw.csv`
- `last_ranks_raw.csv`
- `web_options_clean.csv`
- `last_ranks_clean.csv`
- `web_options_with_cutoffs.csv`
- `web_options_with_cutoffs.xlsx`
- `unmatched_records.csv`

The console will also output a detailed Validation Summary containing metrics of the merge process.

## Troubleshooting
- **Missing PDFs:** Ensure the PDFs are correctly placed in the `datasets/` directory.
- **Dependency Issues:** Check that you are using a virtual environment and installed the dependencies via `pip install -r requirements.txt`.
- **Extraction Failures:** If `pdfplumber` struggles with the PDFs, you can enable Camelot by setting `USE_CAMELOT = True` in `config.py` (ensure you have installed `camelot-py[cv]`).
