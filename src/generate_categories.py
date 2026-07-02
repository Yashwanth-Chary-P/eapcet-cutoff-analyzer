import pandas as pd
from pathlib import Path
from src.utils import setup_logger

logger = setup_logger("generate_categories")

def generate_category_dataset(merged_df: pd.DataFrame, category: str, output_dir: Path) -> pd.DataFrame:
    """Generates the specific dataset for a given category."""
    if merged_df.empty:
        return pd.DataFrame()
        
    base_cols = [
        "S.NO",
        "COLLEGE CODE",
        "COURSE CODE",
        "INSTITUTE NAME",
        "PLACE",
        "TYPE",
        "YEAR OF ESTB"
    ]
    
    # Check if category exists
    if category not in merged_df.columns:
        logger.warning(f"Category '{category}' not found in merged dataset!")
        # We will create an empty column if not found to satisfy output requirements,
        # but realistically it should be there.
        merged_df[category] = pd.NA
        
    cols_to_keep = [c for c in base_cols if c in merged_df.columns] + [category]
    
    cat_df = merged_df[cols_to_keep].copy()
    
    # Save CSV and Excel
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / f"{category}.csv"
    excel_path = output_dir / f"{category}.xlsx"
    
    cat_df.to_csv(csv_path, index=False)
    cat_df.to_excel(excel_path, index=False)
    
    logger.info(f"Saved {category} datasets to {output_dir}")
    return cat_df
