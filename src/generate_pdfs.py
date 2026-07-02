import pandas as pd
from pathlib import Path
from reportlab.lib.pagesizes import landscape, A4, legal, A3
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from src.utils import setup_logger

logger = setup_logger("generate_pdfs")

def generate_pdf_report(df: pd.DataFrame, filepath: Path, title_text: str, is_all_categories: bool = False):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # 9. Dynamic Scaling
    num_cols = len(df.columns)
    if num_cols <= 10:
        pagesize = landscape(A4) # 842 x 595
    elif num_cols <= 18:
        pagesize = landscape(legal) # 1008 x 612
    else:
        # If > 18 columns, use custom width or A3
        custom_width = max(landscape(A3)[0], num_cols * 70)
        pagesize = (custom_width, landscape(A3)[1])
        
    page_width, page_height = pagesize
    margins = 30
    usable_width = page_width - (margins * 2)
    
    doc = SimpleDocTemplate(
        str(filepath), 
        pagesize=pagesize,
        rightMargin=margins, leftMargin=margins, topMargin=margins, bottomMargin=margins
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=1, # Center
        fontName='Helvetica-Bold',
        spaceAfter=20
    )
    elements.append(Paragraph(title_text, title_style))
    
    # 1. & 10. Automatically Calculate Column Widths
    # We will estimate characters to get a proportional width
    col_widths = []
    font_name = 'Helvetica'
    font_size = 9 if num_cols <= 10 else 8
    
    # Text align mapping
    text_cols = ["S.NO", "COLLEGE CODE", "COURSE CODE", "INSTITUTE NAME", "PLACE", "TYPE", "YEAR OF ESTB"]
    
    # Setup paragraph styles
    header_style = ParagraphStyle(
        'HeaderStyle', 
        fontName='Helvetica-Bold', 
        fontSize=font_size, 
        textColor=colors.whitesmoke, 
        alignment=1 # Center
    )
    
    body_left_style = ParagraphStyle(
        'BodyLeftStyle', 
        fontName=font_name, 
        fontSize=font_size, 
        alignment=0 # Left
    )
    
    body_center_style = ParagraphStyle(
        'BodyCenterStyle', 
        fontName=font_name, 
        fontSize=font_size, 
        alignment=1 # Center
    )
    
    data = []
    
    # Header Row
    header_row = []
    for col in df.columns:
        header_row.append(Paragraph(str(col), header_style))
    data.append(header_row)
    
    # 3. Wrap long text using Paragraph
    for _, row in df.iterrows():
        row_data = []
        for col_idx, col_name in enumerate(df.columns):
            val = row[col_name]
            val_str = "" if pd.isna(val) else str(val)
            
            # 6. Align text properly
            if col_name in text_cols:
                p_style = body_left_style
            else:
                p_style = body_center_style
                
            row_data.append(Paragraph(val_str, p_style))
        data.append(row_data)
        
    # Calculate widths based on characters or strict rules
    # 10. BC_B_GIRLS PDF - allocate 40% to INSTITUTE NAME
    if not is_all_categories and "INSTITUTE NAME" in df.columns and num_cols <= 10:
        inst_idx = df.columns.tolist().index("INSTITUTE NAME")
        base_width = (usable_width * 0.6) / (num_cols - 1)
        for i in range(num_cols):
            if i == inst_idx:
                col_widths.append(usable_width * 0.4)
            else:
                col_widths.append(base_width)
    else:
        # Dynamic calculation based on max string length in each column
        max_lens = []
        for col in df.columns:
            # Header len
            m_len = len(str(col))
            # Values max len
            if not df.empty:
                val_len = df[col].astype(str).map(len).max()
                m_len = max(m_len, val_len)
            
            # Cap the max length logic so that text columns (like Institute name) can wrap
            if col == "INSTITUTE NAME":
                m_len = max(m_len, 35) # Give it reasonable weight
            
            max_lens.append(m_len)
            
        total_len = sum(max_lens)
        for ml in max_lens:
            # Allocate proportional width
            cw = (ml / total_len) * usable_width
            # Ensure a minimum width so columns don't completely collapse
            cw = max(cw, 40)
            col_widths.append(cw)
            
        # Re-normalize if sum exceeds usable width (though it shouldn't if we proportioned, but min() could break it)
        total_cw = sum(col_widths)
        if total_cw > usable_width:
            factor = usable_width / total_cw
            col_widths = [w * factor for w in col_widths]
    
    # 4. ReportLab Table handles automatic row height increase when Paragraphs are used
    t = Table(data, repeatRows=1, colWidths=col_widths)
    
    # 7 & 8. Padding, Typography and Colors
    t_style = TableStyle([
        # Header formatting
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        # General padding
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 1), (-1, -1), 'TOP')
    ])
    
    # Alternating row colors
    for i in range(1, len(data)):
        bg_color = colors.whitesmoke if i % 2 == 0 else colors.white
        t_style.add('BACKGROUND', (0, i), (-1, i), bg_color)
            
    t.setStyle(t_style)
    elements.append(t)
    
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(page_width - 30, 15, text)
        canvas.restoreState()
        
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    logger.info(f"Saved PDF to {filepath}")
