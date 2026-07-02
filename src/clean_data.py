import pandas as pd
import numpy as pd_np
import re
from src.utils import setup_logger

logger = setup_logger("clean_data")

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes column names and ensures they are unique."""
    df = df.copy()
    new_cols = []
    seen = {}
    for i, col in enumerate(df.columns):
        c = re.sub(r'\s+', ' ', str(col).strip()).upper() if pd.notna(col) and str(col).strip() != "" else f"UNNAMED"
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols
    return df

def drop_repeated_headers(df: pd.DataFrame, header_keywords: list) -> pd.DataFrame:
    """Removes rows that are actually repeated table headers."""
    df = df.copy()
    # If a row contains the header keyword in a particular column, we drop it.
    mask = pd.Series([False] * len(df))
    for keyword in header_keywords:
        for col in df.columns:
            # We treat any string containing the keyword as a potential header row
            mask = mask | (df[col].astype(str).str.upper().str.contains(keyword, na=False))
    return df[~mask].reset_index(drop=True)

def normalize_text_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Trims whitespace and converts to uppercase for text columns."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(lambda x: re.sub(r'\s+', ' ', str(x).strip()).upper() if pd.notna(x) and x is not None else x)
    return df

def clean_cutoff_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans cutoff columns, converting them to numeric."""
    df = df.copy()
    cutoff_keywords = ['BOYS', 'GIRLS']
    
    rename_mapping = {}
    for col in df.columns:
        if any(keyword in col for keyword in cutoff_keywords):
            # Replace "-" and empty strings with NaN
            df[col] = df[col].replace([r'^\-$', r'^\s*$'], pd_np.nan, regex=True)
            # Try converting to numeric (Int64 allows NaNs in integer columns)
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            
            # Replace space with underscore for the column name
            rename_mapping[col] = col.replace(" ", "_")
            
    if rename_mapping:
        df = df.rename(columns=rename_mapping)
            
    return df

def set_actual_header(df: pd.DataFrame, keywords: list) -> pd.DataFrame:
    """Finds the actual header row and sets it."""
    df = df.copy()
    header_idx = None
    
    # Check current columns first
    cols_str = " ".join([str(c).upper() for c in df.columns])
    if any(k in cols_str for k in keywords):
        return df # Header is already correct

    for idx, row in df.iterrows():
        row_str = " ".join([str(x).upper() for x in row if pd.notna(x)])
        if any(k in row_str for k in keywords):
            header_idx = idx
            break
            
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx + 1:].reset_index(drop=True)
    return df

def clean_web_options(df: pd.DataFrame) -> pd.DataFrame:
    """Main cleaning pipeline for Web Options data."""
    if df.empty:
        return df
        
    df = set_actual_header(df, ["COLLEGE CODE", "COURSE CODE", "INSTITUTE NAME"])
    df = clean_column_names(df)
    
    # Remove repeated headers (e.g. S.NO, COLLEGE CODE)
    df = drop_repeated_headers(df, ["COLLEGE CODE", "COURSE CODE", "INSTITUTE NAME"])
    
    df = normalize_text_cols(df)
    
    # Remove rows where essential columns are entirely missing
    if "COLLEGE CODE" in df.columns and "COURSE CODE" in df.columns:
        df = df.dropna(subset=["COLLEGE CODE", "COURSE CODE"], how="all")
        
    if "COLLEGE CODE" in df.columns and "COURSE CODE" in df.columns:
        df = df.drop_duplicates(subset=["COLLEGE CODE", "COURSE CODE"]).reset_index(drop=True)
    else:
        df = df.drop_duplicates().reset_index(drop=True)
        
    return df

def clean_last_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """Main cleaning pipeline for Last Ranks data."""
    if df.empty:
        return df
        
    df = set_actual_header(df, ["INST CODE", "BRANCH CODE", "INSTITUTE NAME"])
    df = clean_column_names(df)
    
    # Check for missing crucial columns before dropping repeated headers
    # Some columns might be named slightly differently, e.g. "INST CODE"
    df = drop_repeated_headers(df, ["INST CODE", "BRANCH CODE", "INSTITUTE NAME"])
    
    df = normalize_text_cols(df)
    df = clean_cutoff_columns(df)
    
    # Remove rows where essential columns are missing
    if "INST CODE" in df.columns and "BRANCH CODE" in df.columns:
        df = df.dropna(subset=["INST CODE", "BRANCH CODE"], how="all")
        
    if "INST CODE" in df.columns and "BRANCH CODE" in df.columns:
        df = df.drop_duplicates(subset=["INST CODE", "BRANCH CODE"]).reset_index(drop=True)
    else:
        df = df.drop_duplicates().reset_index(drop=True)
        
    return df
