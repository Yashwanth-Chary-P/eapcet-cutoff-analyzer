import pandas as pd
from typing import Tuple
from src.utils import setup_logger

logger = setup_logger("merge_data")

def merge_datasets(web_df: pd.DataFrame, ranks_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Merges Web Options and Last Ranks DataFrames using a LEFT JOIN.
    Returns (merged_df, unmatched_web_options_df).
    """
    if web_df.empty:
        logger.warning("Web Options DataFrame is empty, nothing to merge.")
        return pd.DataFrame(), pd.DataFrame()
        
    if ranks_df.empty:
        logger.warning("Last Ranks DataFrame is empty, returning Web Options as is.")
        return web_df.copy(), web_df.copy()

    # Ensure key columns exist
    if "COLLEGE CODE" not in web_df.columns or "COURSE CODE" not in web_df.columns:
        logger.error("Web Options DataFrame is missing required key columns ('COLLEGE CODE', 'COURSE CODE').")
        return web_df.copy(), web_df.copy()
        
    if "INST CODE" not in ranks_df.columns or "BRANCH CODE" not in ranks_df.columns:
        logger.error("Last Ranks DataFrame is missing required key columns ('INST CODE', 'BRANCH CODE').")
        return web_df.copy(), web_df.copy()

    # We need to perform a LEFT JOIN on:
    # COLLEGE CODE == INST CODE
    # COURSE CODE == BRANCH CODE
    
    # We will rename the keys in ranks_df to match web_df for the merge, 
    # or just use left_on and right_on
    
    merged_df = pd.merge(
        web_df,
        ranks_df,
        left_on=["COLLEGE CODE", "COURSE CODE"],
        right_on=["INST CODE", "BRANCH CODE"],
        how="left",
        indicator=True
    )
    
    unmatched_df = merged_df[merged_df["_merge"] == "left_only"].drop(columns=["_merge"])
    merged_df = merged_df.drop(columns=["_merge"])
    
    # Optional: drop the redundant INST CODE and BRANCH CODE if they are identical to COLLEGE CODE and COURSE CODE
    # But since it's a left join, unmatched rows will have NaN for INST CODE and BRANCH CODE.
    # We can keep them or drop them. Let's drop the redundant keys.
    if "INST CODE" in merged_df.columns:
        merged_df = merged_df.drop(columns=["INST CODE"])
    if "BRANCH CODE" in merged_df.columns:
        merged_df = merged_df.drop(columns=["BRANCH CODE"])
        
    # Also, Institute Name might be duplicated. We can resolve suffix or just drop the one from Last Ranks.
    if "INSTITUTE NAME_y" in merged_df.columns:
        merged_df = merged_df.drop(columns=["INSTITUTE NAME_y"])
    if "INSTITUTE NAME_x" in merged_df.columns:
        merged_df = merged_df.rename(columns={"INSTITUTE NAME_x": "INSTITUTE NAME"})
        
    return merged_df, unmatched_df
