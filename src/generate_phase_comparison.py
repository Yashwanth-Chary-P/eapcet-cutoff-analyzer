import pandas as pd
from pathlib import Path
from src.pdf_extract import extract_pdf_data
from src.clean_data import clean_web_options, clean_last_ranks
from src.generate_pdfs import generate_pdf_report
from src.utils import setup_logger
import random
import pdfplumber
import re

logger = setup_logger("generate_phase_comparison")

def main():
    base_dir = Path(__file__).resolve().parent.parent
    dataset_dir = base_dir / "datasets"
    output_dir = base_dir / "output" / "phase_comparison"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    web_options_pdf = dataset_dir / "LAST WEB OPTION.pdf"
    if not web_options_pdf.exists():
        logger.error(f"Dataset not found: {web_options_pdf}")
        return
        
    first_phase_pdf = dataset_dir / "TGEAPCET_2025_LASTRANKS_FirstPhase (1).pdf"
    second_phase_pdf = dataset_dir / "TGEAPCET_2025_LASTRANKS_SecondPhase (1).pdf"
    final_phase_pdf = dataset_dir / "TGEAPCET_2025_FINALPHASE_LASTRANKS.pdf"
    
    # Check if files exist
    for f in [web_options_pdf, first_phase_pdf, second_phase_pdf, final_phase_pdf]:
        if not f.exists():
            logger.error(f"Dataset not found: {f}")
            return
    
    # 1. Extract and clean data
    logger.info("Extracting Web Options (Custom Parser)...")
    
    def extract_custom_web_options(pdf_path):
        rows = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        val = row[0]
                        if not val:
                            continue
                        val = str(val).replace('\n', '  ')
                        match = re.search(r'\b(\d+)\s+(\d+)\s+([A-Z0-9]{3,4})\s+(.*?)\b([A-Z]{3})\b', val)
                        if match:
                            s_no, opt_no, inst_code, inst_name_part, branch_code = match.groups()
                            # Clean inst name part
                            inst_name_clean = inst_name_part.strip()
                            if inst_name_clean.endswith(','):
                                inst_name_clean = inst_name_clean[:-1].strip()
                            
                            rows.append({
                                "S.NO": s_no,
                                "OPTION NO": opt_no,
                                "COLLEGE CODE": inst_code,
                                "COURSE CODE": branch_code,
                                "INSTITUTE NAME": inst_name_clean,
                                "PLACE": ""
                            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.drop_duplicates(subset=["S.NO"]).reset_index(drop=True)
            df["S.NO"] = pd.to_numeric(df["S.NO"])
            df = df.sort_values("S.NO").reset_index(drop=True)
            df["S.NO"] = df["S.NO"].astype(str)
        return df
        
    web_options_df = extract_custom_web_options(web_options_pdf)
    
    logger.info("Extracting First Phase...")
    first_phase_df = extract_pdf_data(first_phase_pdf)
    first_phase_df = clean_last_ranks(first_phase_df)
    
    logger.info("Extracting Second Phase...")
    second_phase_df = extract_pdf_data(second_phase_pdf)
    second_phase_df = clean_last_ranks(second_phase_df)
    
    logger.info("Extracting Final Phase...")
    final_phase_df = extract_pdf_data(final_phase_pdf)
    final_phase_df = clean_last_ranks(final_phase_df)
    
    # 2. Extract only required columns from cutoffs
    # We only care about BC_B_GIRLS
    
    def extract_cutoff(df, phase_name):
        if "BC_B_GIRLS" in df.columns:
            return df[["INST CODE", "BRANCH CODE", "BC_B_GIRLS"]].rename(
                columns={"BC_B_GIRLS": f"BC_B_GIRLS_{phase_name}"}
            ).dropna(subset=[f"BC_B_GIRLS_{phase_name}"])
        else:
            logger.warning(f"BC_B_GIRLS not found in {phase_name} dataset!")
            return pd.DataFrame(columns=["INST CODE", "BRANCH CODE", f"BC_B_GIRLS_{phase_name}"])

    # Enhance INSTITUTE NAME from final phase df if possible
    inst_name_map = final_phase_df.drop_duplicates(subset=["INST CODE"]).set_index("INST CODE")["INSTITUTE NAME"].to_dict()
    
    for idx, row in web_options_df.iterrows():
        code = row["COLLEGE CODE"]
        if code in inst_name_map and pd.notna(inst_name_map[code]) and str(inst_name_map[code]).strip():
            web_options_df.at[idx, "INSTITUTE NAME"] = inst_name_map[code]
            
    first_cutoff = extract_cutoff(first_phase_df, "FIRST_PHASE")
    second_cutoff = extract_cutoff(second_phase_df, "SECOND_PHASE")
    final_cutoff = extract_cutoff(final_phase_df, "FINAL_PHASE")
    
    # 3. Merge datasets
    base_cols = ["S.NO", "OPTION NO", "COLLEGE CODE", "COURSE CODE", "INSTITUTE NAME", "PLACE"]
    
    # Ensure columns exist, if not create empty
    for col in base_cols:
        if col not in web_options_df.columns:
            web_options_df[col] = ""
            
    merged_df = web_options_df[base_cols].copy()
    
    # Merge Phase 1
    merged_df = pd.merge(
        merged_df,
        first_cutoff,
        how="left",
        left_on=["COLLEGE CODE", "COURSE CODE"],
        right_on=["INST CODE", "BRANCH CODE"]
    ).drop(columns=["INST CODE", "BRANCH CODE"], errors="ignore")
    
    # Merge Phase 2
    merged_df = pd.merge(
        merged_df,
        second_cutoff,
        how="left",
        left_on=["COLLEGE CODE", "COURSE CODE"],
        right_on=["INST CODE", "BRANCH CODE"]
    ).drop(columns=["INST CODE", "BRANCH CODE"], errors="ignore")
    
    # Merge Final Phase
    merged_df = pd.merge(
        merged_df,
        final_cutoff,
        how="left",
        left_on=["COLLEGE CODE", "COURSE CODE"],
        right_on=["INST CODE", "BRANCH CODE"]
    ).drop(columns=["INST CODE", "BRANCH CODE"], errors="ignore")
    
    # Format blank values
    for phase in ["FIRST_PHASE", "SECOND_PHASE", "FINAL_PHASE"]:
        col = f"BC_B_GIRLS_{phase}"
        merged_df[col] = merged_df[col].apply(lambda x: "" if pd.isna(x) else str(int(x)) if isinstance(x, (float, int)) else str(x))

    # 4. Generate outputs
    csv_path = output_dir / "BC_B_GIRLS_Comparison.csv"
    excel_path = output_dir / "BC_B_GIRLS_Comparison.xlsx"
    pdf_path = output_dir / "BC_B_GIRLS_Comparison.pdf"
    
    merged_df.to_csv(csv_path, index=False)
    merged_df.to_excel(excel_path, index=False)
    
    title = "Telangana EAPCET 2025\nBC_B_GIRLS Cutoff Comparison\nFirst Phase vs Second Phase vs Final Phase"
    generate_pdf_report(merged_df, pdf_path, title, is_all_categories=False)
    
    # 5. Post Execution Validation
    import datetime
    now = datetime.datetime.now()
    exec_date = now.strftime("%Y-%m-%d")
    exec_time = now.strftime("%H:%M:%S")

    total_web_options = len(web_options_df)
    total_merged = len(merged_df)
    row_count_match = (total_web_options == total_merged)
    
    first_row_match = (str(web_options_df.iloc[0]["S.NO"]) == str(merged_df.iloc[0]["S.NO"])) and \
                      (str(web_options_df.iloc[0]["OPTION NO"]) == str(merged_df.iloc[0]["OPTION NO"])) and \
                      (web_options_df.iloc[0]["COLLEGE CODE"] == merged_df.iloc[0]["COLLEGE CODE"])
                      
    last_row_match = (str(web_options_df.iloc[-1]["S.NO"]) == str(merged_df.iloc[-1]["S.NO"])) and \
                     (str(web_options_df.iloc[-1]["OPTION NO"]) == str(merged_df.iloc[-1]["OPTION NO"])) and \
                     (web_options_df.iloc[-1]["COLLEGE CODE"] == merged_df.iloc[-1]["COLLEGE CODE"])
                     
    ordering_verified = all(
        (str(web_options_df.iloc[i]["OPTION NO"]) == str(merged_df.iloc[i]["OPTION NO"]) and 
         web_options_df.iloc[i]["COLLEGE CODE"] == merged_df.iloc[i]["COLLEGE CODE"] and
         web_options_df.iloc[i]["COURSE CODE"] == merged_df.iloc[i]["COURSE CODE"])
        for i in range(total_web_options)
    )

    if not (row_count_match and first_row_match and last_row_match and ordering_verified):
        logger.error("POST EXECUTION VALIDATION FAILED! Row order/count does not match.")
        print("Validation Failed. Please check logs.")
        return
        
    matched_first = len(merged_df[merged_df["BC_B_GIRLS_FIRST_PHASE"] != ""])
    matched_second = len(merged_df[merged_df["BC_B_GIRLS_SECOND_PHASE"] != ""])
    matched_final = len(merged_df[merged_df["BC_B_GIRLS_FINAL_PHASE"] != ""])
    
    missing_first = total_merged - matched_first
    missing_second = total_merged - matched_second
    missing_final = total_merged - matched_final
    
    # Random verification
    sample_indices = random.sample(range(total_merged), min(25, total_merged))
    perfect_matches = 0
    mismatches = 0
    mismatch_details = []
    
    for idx in sample_indices:
        row = merged_df.iloc[idx]
        college = row["COLLEGE CODE"]
        course = row["COURSE CODE"]
        
        f_match = first_cutoff[(first_cutoff["INST CODE"] == college) & (first_cutoff["BRANCH CODE"] == course)]
        f_val = str(int(f_match["BC_B_GIRLS_FIRST_PHASE"].iloc[0])) if not f_match.empty and not pd.isna(f_match["BC_B_GIRLS_FIRST_PHASE"].iloc[0]) else ""
        
        s_match = second_cutoff[(second_cutoff["INST CODE"] == college) & (second_cutoff["BRANCH CODE"] == course)]
        s_val = str(int(s_match["BC_B_GIRLS_SECOND_PHASE"].iloc[0])) if not s_match.empty and not pd.isna(s_match["BC_B_GIRLS_SECOND_PHASE"].iloc[0]) else ""
        
        fn_match = final_cutoff[(final_cutoff["INST CODE"] == college) & (final_cutoff["BRANCH CODE"] == course)]
        fn_val = str(int(fn_match["BC_B_GIRLS_FINAL_PHASE"].iloc[0])) if not fn_match.empty and not pd.isna(fn_match["BC_B_GIRLS_FINAL_PHASE"].iloc[0]) else ""
        
        is_match = (row["BC_B_GIRLS_FIRST_PHASE"] == f_val and 
                    row["BC_B_GIRLS_SECOND_PHASE"] == s_val and 
                    row["BC_B_GIRLS_FINAL_PHASE"] == fn_val)
                    
        if is_match:
            perfect_matches += 1
        else:
            mismatches += 1
            mismatch_details.append(f"Mismatch at {college} - {course}:")
            mismatch_details.append(f"  Expected: First={f_val}, Second={s_val}, Final={fn_val}")
            mismatch_details.append(f"  Found:    First={row['BC_B_GIRLS_FIRST_PHASE']}, Second={row['BC_B_GIRLS_SECOND_PHASE']}, Final={row['BC_B_GIRLS_FINAL_PHASE']}")
            
    if mismatches > 0:
        logger.error("DATA INTEGRITY VERIFICATION FAILED!")
        for m in mismatch_details:
            print(m)
        return
        
    print("==========================================")
    print("BC_B_GIRLS COMPARISON SUMMARY")
    print("==========================================")
    print("Base Dataset")
    print("LAST WEB OPTION.pdf")
    print("")
    print(f"Total Web Options        : {total_merged}")
    print(f"Matched in First Phase   : {matched_first}")
    print(f"Matched in Second Phase  : {matched_second}")
    print(f"Matched in Final Phase   : {matched_final}")
    print(f"Missing First Phase      : {missing_first}")
    print(f"Missing Second Phase     : {missing_second}")
    print(f"Missing Final Phase      : {missing_final}")
    print(f"Ordering Verified        : {ordering_verified}")
    print(f"First Row Verified       : {first_row_match}")
    print(f"Last Row Verified        : {last_row_match}")
    print("Random Verification")
    print(f"Perfect Matches          : {perfect_matches}")
    print(f"Mismatches               : {mismatches}")
    print("Output Files Generated")
    print("==========================================")

    status_str = "Passed" if mismatches == 0 and ordering_verified else "Failed"

    report_lines = []
    report_lines.append("Execution Date: " + exec_date)
    report_lines.append("Execution Time: " + exec_time)
    report_lines.append(f"Total Rows: {total_merged}")
    report_lines.append(f"Random Samples Checked: {len(sample_indices)}")
    report_lines.append(f"Perfect Matches: {perfect_matches}")
    report_lines.append(f"Mismatches: {mismatches}")
    report_lines.append(f"Ordering Verified: {ordering_verified}")
    report_lines.append(f"First Row Verified: {first_row_match}")
    report_lines.append(f"Last Row Verified: {last_row_match}")
    report_lines.append(f"Status: {status_str}")
    
    verification_path = output_dir / "verification_report.txt"
    with open(verification_path, "w") as f:
        f.write("\n".join(report_lines))

if __name__ == "__main__":
    main()
