import pandas as pd
import pdfplumber
from pathlib import Path
from src.utils import setup_logger

logger = setup_logger("pdf_extract")

def extract_tables_pdfplumber(pdf_path: Path) -> pd.DataFrame:
    """Extracts tables from a PDF using pdfplumber."""
    all_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                if table:
                    all_data.extend(table)
                    
    if not all_data:
        return pd.DataFrame()
        
    # Assume the first row containing substantial data is the header
    # But for robustness, we just make it a DataFrame and we'll clean headers later
    # To handle repeating headers across pages, we'll deal with it in data cleaning
    df = pd.DataFrame(all_data)
    
    # Use the first row as the column names
    if not df.empty:
        df.columns = df.iloc[0].astype(str)
        df = df[1:].reset_index(drop=True)
        
    return df

def extract_tables_camelot(pdf_path: Path) -> pd.DataFrame:
    """Extracts tables from a PDF using Camelot (fallback)."""
    try:
        import camelot
    except ImportError:
        logger.error("Camelot is not installed. Please install camelot-py[cv].")
        return pd.DataFrame()
        
    tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="lattice")
    if not tables:
        tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")
        
    if not tables:
        return pd.DataFrame()
        
    df = pd.concat([t.df for t in tables], ignore_index=True)
    
    if not df.empty:
        df.columns = df.iloc[0].astype(str)
        df = df[1:].reset_index(drop=True)
        
    return df

def extract_pdf_data(pdf_path: Path, use_camelot: bool = False) -> pd.DataFrame:
    """Extracts data from PDF, primarily using pdfplumber with camelot fallback."""
    if not pdf_path.exists():
        logger.error(f"File not found: {pdf_path}")
        return pd.DataFrame()
        
    df = extract_tables_pdfplumber(pdf_path)
    
    if (df.empty or len(df.columns) < 3) and use_camelot:
        logger.info(f"pdfplumber extraction yielded poor results for {pdf_path.name}. Falling back to Camelot...")
        df = extract_tables_camelot(pdf_path)
        
    return df
