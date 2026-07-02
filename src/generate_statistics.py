import pandas as pd
import datetime
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from src.utils import setup_logger
import config

logger = setup_logger("generate_statistics")

def generate_key_statistics_pdf(
    web_df: pd.DataFrame, 
    ranks_df: pd.DataFrame, 
    merged_df: pd.DataFrame, 
    unmatched_df: pd.DataFrame, 
    execution_time: float, 
    filepath: Path
):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(
        str(filepath), 
        pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=1, # Center
        spaceAfter=20
    )
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # 1. Cover Title
    elements.append(Paragraph("Telangana EAPCET Cutoff Processing - Key Statistics Report", title_style))
    elements.append(Spacer(1, 10))
    
    # 2. Dataset Summary
    web_rows = len(web_df)
    rank_rows = len(ranks_df)
    merged_rows = len(merged_df)
    unmatched_rows = len(unmatched_df)
    matched_rows = merged_rows - unmatched_rows
    
    match_pct = (matched_rows / merged_rows * 100) if merged_rows > 0 else 0
    unmatch_pct = (unmatched_rows / merged_rows * 100) if merged_rows > 0 else 0
    
    elements.append(Paragraph("Dataset Summary", heading_style))
    data_summary = [
        ["Metric", "Value"],
        ["Total Web Options Rows", str(web_rows)],
        ["Total Last Rank Rows", str(rank_rows)],
        ["Total Merged Rows", str(merged_rows)],
        ["Total Matched Rows", str(matched_rows)],
        ["Total Unmatched Rows", str(unmatched_rows)],
        ["Match Percentage", f"{match_pct:.2f}%"],
        ["Unmatched Percentage", f"{unmatch_pct:.2f}%"]
    ]
    t1 = Table(data_summary, colWidths=[200, 100])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 15))
    
    # 3. BC_B_GIRLS Summary
    elements.append(Paragraph("BC_B_GIRLS Summary", heading_style))
    bc_total = merged_rows
    if "BC_B_GIRLS" in merged_df.columns:
        bc_missing = merged_df["BC_B_GIRLS"].isna().sum()
    else:
        bc_missing = bc_total
        
    bc_available = bc_total - bc_missing
    av_pct = (bc_available / bc_total * 100) if bc_total > 0 else 0
    ms_pct = (bc_missing / bc_total * 100) if bc_total > 0 else 0
    
    data_bc = [
        ["Metric", "Value"],
        ["Total Colleges/Courses", str(bc_total)],
        ["Total Available BC_B_GIRLS Cutoffs", str(bc_available)],
        ["Total Missing BC_B_GIRLS Cutoffs", str(bc_missing)],
        ["Percentage of Available Cutoffs", f"{av_pct:.2f}%"],
        ["Percentage of Missing Cutoffs", f"{ms_pct:.2f}%"]
    ]
    t2 = Table(data_bc, colWidths=[250, 100])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 15))
    
    # 4. College Statistics
    elements.append(Paragraph("College Statistics", heading_style))
    unique_colleges = merged_df["COLLEGE CODE"].nunique() if "COLLEGE CODE" in merged_df.columns else 0
    unique_branches = merged_df["COURSE CODE"].nunique() if "COURSE CODE" in merged_df.columns else 0
    
    elements.append(Paragraph(f"<b>Total Unique Colleges:</b> {unique_colleges}", normal_style))
    elements.append(Paragraph(f"<b>Total Unique Branches:</b> {unique_branches}", normal_style))
    elements.append(Spacer(1, 10))
    
    if "COLLEGE CODE" in merged_df.columns and "COURSE CODE" in merged_df.columns:
        top_colleges = merged_df.groupby("COLLEGE CODE").size().sort_values(ascending=False).head(10)
        top_branches = merged_df.groupby("COURSE CODE").size().sort_values(ascending=False).head(10)
        
        elements.append(Paragraph("<b>Top 10 Colleges with the Highest Number of Branches:</b>", normal_style))
        tc_data = [["College Code", "Count"]] + [[idx, str(val)] for idx, val in top_colleges.items()]
        t3 = Table(tc_data, colWidths=[150, 100])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t3)
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph("<b>Top 10 Branches Appearing Most Frequently:</b>", normal_style))
        tb_data = [["Course Code", "Count"]] + [[idx, str(val)] for idx, val in top_branches.items()]
        t4 = Table(tb_data, colWidths=[150, 100])
        t4.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t4)
        elements.append(Spacer(1, 15))
    
    # 5. Missing Data Analysis
    elements.append(Paragraph("Missing Data Analysis", heading_style))
    reason = ("These records from the Web Options list were not found in the Last Rank dataset. "
              "Possible reasons include: the college not being present in the Last Rank PDF, "
              "a branch being introduced after the Last Rank dataset was generated, a code mismatch "
              "(e.g., typos in one of the PDFs), or an extraction issue where tables were malformed.")
    elements.append(Paragraph(reason, normal_style))
    elements.append(Spacer(1, 10))
    
    if not unmatched_df.empty:
        umd = [["COLLEGE CODE", "COURSE CODE", "INSTITUTE NAME", "PLACE"]]
        for _, row in unmatched_df.iterrows():
            cc = str(row.get("COLLEGE CODE", ""))
            crc = str(row.get("COURSE CODE", ""))
            iname = str(row.get("INSTITUTE NAME", ""))[:35] + "..." if len(str(row.get("INSTITUTE NAME", ""))) > 35 else str(row.get("INSTITUTE NAME", ""))
            pl = str(row.get("PLACE", ""))
            umd.append([cc, crc, iname, pl])
            
        t5 = Table(umd, colWidths=[80, 80, 200, 100], repeatRows=1)
        t5.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t5)
    else:
        elements.append(Paragraph("No unmatched records found.", normal_style))
    
    elements.append(Spacer(1, 15))
    
    # 6. Execution Summary
    elements.append(Paragraph("Execution Summary", heading_style))
    exec_data = [
        ["Metric", "Value"],
        ["Execution Date & Time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Total Execution Time", f"{execution_time:.2f} seconds"],
        ["Python Version", sys.version.split()[0]],
        ["Extraction Library Used", "Camelot" if config.USE_CAMELOT else "pdfplumber"],
        ["Number of PDFs Processed", "2"],
        ["Number of Output Files Generated", "9 (Includes Intermediate & Final outputs)"]
    ]
    t6 = Table(exec_data, colWidths=[200, 250])
    t6.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t6)
    
    def add_page_footer(canvas, doc):
        page_num = canvas.getPageNumber()
        footer_text = f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Page {page_num}"
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawString(40, 20, footer_text)
        canvas.restoreState()
        
    doc.build(elements, onFirstPage=add_page_footer, onLaterPages=add_page_footer)
    logger.info(f"Saved PDF to {filepath}")
