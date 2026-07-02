import pandas as pd
import numpy as np
import datetime
import random
from pathlib import Path
from src.utils import setup_logger

logger = setup_logger("verify_data")

def verify_merged_data(web_clean: pd.DataFrame, ranks_clean: pd.DataFrame, merged_df: pd.DataFrame, report_path: Path):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting Data Integrity Verification...")
    
    mismatches = []
    
    # 1. Full Dataset Checks
    # Duplicate COLLEGE CODE + COURSE CODE
    duplicates = merged_df[merged_df.duplicated(subset=["COLLEGE CODE", "COURSE CODE"], keep=False)]
    duplicate_count = len(duplicates)
    
    # Missing merge keys
    missing_keys = merged_df[merged_df["COLLEGE CODE"].isna() | merged_df["COURSE CODE"].isna()]
    missing_keys_count = len(missing_keys)
    
    # Rows with all cutoff values empty
    cutoff_cols = [c for c in merged_df.columns if "BOYS" in c or "GIRLS" in c]
    all_empty_cutoffs = 0
    if cutoff_cols:
        all_empty_cutoffs = len(merged_df[merged_df[cutoff_cols].isna().all(axis=1)])
        
    # Duplicate institute records after merge (same college code, but maybe expected if multiple courses)
    # We will just check strict duplicates
    strict_dupes = len(merged_df[merged_df.duplicated()])
    
    # 2. Random Verification (25 records)
    sample_size = min(25, len(merged_df))
    # For reproducible debugging during execution
    random.seed(42)
    sample_indices = random.sample(range(len(merged_df)), sample_size)
    sample_df = merged_df.iloc[sample_indices]
    
    perfect_matches = 0
    
    for _, row in sample_df.iterrows():
        cc = row["COLLEGE CODE"]
        crc = row["COURSE CODE"]
        
        is_match = True
        reason = []
        
        # Find in web_clean
        web_match = web_clean[(web_clean["COLLEGE CODE"] == cc) & (web_clean["COURSE CODE"] == crc)]
        if len(web_match) == 0:
            is_match = False
            reason.append("Record not found in Web Options clean dataset.")
        elif len(web_match) > 1:
            is_match = False
            reason.append("Multiple matches found in Web Options clean dataset.")
        else:
            w_row = web_match.iloc[0]
            # Compare Web fields
            web_fields = ["INSTITUTE NAME", "PLACE", "TYPE", "YEAR OF ESTB"]
            for f in web_fields:
                if f in row and f in w_row:
                    v_m = row[f]
                    v_w = w_row[f]
                    if pd.isna(v_m) and pd.isna(v_w): continue
                    if str(v_m) != str(v_w):
                        is_match = False
                        reason.append(f"Web field '{f}' mismatch. Expected: {v_w}, Merged: {v_m}")
                        
        # Find in ranks_clean
        # The merge key in ranks_clean is INST CODE and BRANCH CODE
        rank_match = ranks_clean[(ranks_clean["INST CODE"] == cc) & (ranks_clean["BRANCH CODE"] == crc)]
        if len(rank_match) == 0:
            # It's an unmatched record which was kept (left join)
            # This is technically not a mismatch of data corruption, but a missing rank.
            # But we should ensure all cutoffs are empty in merged_df
            for f in cutoff_cols:
                if not pd.isna(row.get(f)):
                    is_match = False
                    reason.append(f"Cutoff '{f}' should be NaN for unmatched record, but is {row.get(f)}")
        elif len(rank_match) > 1:
            is_match = False
            reason.append("Multiple matches found in Last Rank clean dataset.")
        else:
            r_row = rank_match.iloc[0]
            for f in cutoff_cols:
                if f in row and f in r_row:
                    v_m = row[f]
                    v_r = r_row[f]
                    if pd.isna(v_m) and pd.isna(v_r): continue
                    # Both might be numeric but different types, so compare string representations of floats/ints safely
                    if str(v_m) != str(v_r):
                        # Attempt float comparison
                        try:
                            if float(v_m) != float(v_r):
                                is_match = False
                                reason.append(f"Rank field '{f}' mismatch. Expected: {v_r}, Merged: {v_m}")
                        except ValueError:
                            is_match = False
                            reason.append(f"Rank field '{f}' mismatch. Expected: {v_r}, Merged: {v_m}")
                            
        if is_match:
            perfect_matches += 1
        else:
            mismatches.append({
                "college": cc,
                "course": crc,
                "reasons": reason
            })
            
    # 3. Generate Report
    lines = []
    lines.append("========================================")
    lines.append("RANDOM DATA VERIFICATION REPORT")
    lines.append("========================================")
    lines.append(f"Verification Date & Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Merged Rows: {len(merged_df)}")
    lines.append(f"Random Samples Checked: {sample_size}")
    lines.append(f"Perfect Matches: {perfect_matches}")
    lines.append(f"Mismatches Found: {len(mismatches)}")
    lines.append("")
    
    if len(mismatches) == 0 and duplicate_count == 0 and missing_keys_count == 0:
        lines.append("Status:")
        lines.append("[x] VERIFIED SUCCESSFULLY")
    else:
        lines.append("Status:")
        lines.append("[ ] VERIFICATION FAILED / WARNINGS EXIST")
        
    lines.append("========================================")
    lines.append("FULL DATASET CHECKS")
    lines.append(f"Duplicate Merge Keys: {duplicate_count}")
    lines.append(f"Missing Merge Keys  : {missing_keys_count}")
    lines.append(f"All Cutoffs Empty   : {all_empty_cutoffs}")
    lines.append(f"Strict Row Dupes    : {strict_dupes}")
    lines.append("========================================")
    
    if mismatches:
        lines.append("MISMATCH DETAILS:")
        for idx, m in enumerate(mismatches, 1):
            lines.append(f"\nRecord {idx}")
            lines.append(f"College Code : {m['college']}")
            lines.append(f"Course Code  : {m['course']}")
            lines.append("Reason:")
            for r in m['reasons']:
                lines.append(f"- {r}")
                
    report_content = "\n".join(lines)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    logger.info(f"Verification report saved to {report_path}")
    
    if mismatches:
        logger.warning(f"Verification found {len(mismatches)} mismatches! See {report_path}")
    else:
        logger.info("Verification passed successfully.")
        
    return len(mismatches) == 0
