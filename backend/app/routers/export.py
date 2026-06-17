import logging

import io
import os
import json
import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any

from app.dependencies.auth import get_current_user
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
logger = logging.getLogger("lumint.routers.export")


router = APIRouter(prefix="/api/export", tags=["export"], dependencies=[Depends(get_current_user)])

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reports"))

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header (Only on pages after page 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "LUMINT SECURITY RESEARCH — ML VALIDATION REPORT")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 747, 558, 747)
            
        # Footer (On all pages)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 40, "Confidential — Lumint Security Research Group")
        self.drawRightString(558, 40, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 52, 558, 52)
        self.restoreState()


def get_clean_header(h: str) -> str:
    h = h.replace("**", "").strip().lower()
    h = h.replace("&delta;", "delta").replace("&delta", "delta").replace("delta;", "delta").replace("δ", "delta").replace("Δ", "delta")
    h = h.replace("features / shields", "features")
    h = h.replace("f1 score", "f1")
    h = h.replace("auc-roc", "auc")
    h = h.replace("recall (fraud)", "recall")
    h = h.replace("strategy / configuration", "strategy")
    h = h.replace("module / shield", "module")
    h = h.replace("feature group", "feature_group")
    h = h.replace("feature count", "feature_count")
    h = h.replace(" ", "_")
    return h


def parse_md_table(lines: List[str]) -> List[Dict[str, Any]]:
    table_lines = [l.strip() for l in lines if l.strip().startswith('|')]
    if len(table_lines) < 3:
        return []
    
    headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
    clean_headers = [get_clean_header(h) for h in headers]
    
    rows = []
    for line in table_lines[2:]:
        if '---' in line:
            continue
        cols = [c.strip() for c in line.split('|')[1:-1]]
        if len(cols) == len(headers):
            clean_cols = [col.replace("**", "").strip() for col in cols]
            row_dict = {}
            for k, v in zip(clean_headers, clean_cols):
                if v == "--" or v == "":
                    row_dict[k] = None
                    continue
                try:
                    if "." in v:
                        row_dict[k] = float(v)
                    elif v.isdigit() or (v.startswith('-') and v[1:].isdigit()):
                        row_dict[k] = int(v)
                    else:
                        row_dict[k] = v
                except ValueError:
                    row_dict[k] = v
            rows.append(row_dict)
    return rows


@router.get("/research-report")
def export_research_report():
    # Load all research data
    doc_path = os.path.join(REPORTS_DIR, "r10_doc_statistical.json")
    phish_path = os.path.join(REPORTS_DIR, "r10_phish_statistical.json")
    upi_path = os.path.join(REPORTS_DIR, "r10_upi_statistical.json")
    ablation_md_path = os.path.join(REPORTS_DIR, "r11_ablation_tables.md")
    
    # Missing checks
    if not (os.path.exists(doc_path) and os.path.exists(phish_path) and os.path.exists(upi_path)):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Research reports are not generated yet."
        )
        
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)
        with open(phish_path, "r", encoding="utf-8") as f:
            phish_data = json.load(f)
        with open(upi_path, "r", encoding="utf-8") as f:
            upi_data = json.load(f)
            
        ablation_sections = {}
        if os.path.exists(ablation_md_path):
            with open(ablation_md_path, "r", encoding="utf-8") as f:
                content = f.read()
            current_key = None
            section_lines = []
            for line in content.split("\n"):
                if line.startswith("## Table A:"):
                    current_key = "module_ablation"
                    section_lines = []
                elif line.startswith("## Table B:"):
                    ablation_sections[current_key] = parse_md_table(section_lines)
                    current_key = "feature_ablation"
                    section_lines = []
                elif line.startswith("## Table C:"):
                    ablation_sections[current_key] = parse_md_table(section_lines)
                    current_key = "smote_ablation"
                    section_lines = []
                elif line.startswith("## Table D:") or line.startswith("## Global Feature"):
                    if current_key:
                        ablation_sections[current_key] = parse_md_table(section_lines)
                    current_key = None
                elif current_key:
                    section_lines.append(line)
            if current_key and current_key not in ablation_sections:
                ablation_sections[current_key] = parse_md_table(section_lines)
    except Exception:
        logger.exception("Failed to read raw report data")
        raise HTTPException(
            status_code=500,
            detail="Failed to read raw report data."
        )
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette Styling
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=20
    )
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f766e'),
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )
    table_cell_bold_style = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0f172a')
    )
    
    story = []
    
    # Document Header
    story.append(Paragraph("Lumint Security Research Platform", title_style))
    date_str = datetime.date.today().strftime("%B %d, %Y")
    story.append(Paragraph(f"<b>Statistical Validation & Ablation Report</b> | Generated: {date_str} | Platform Version: R14.0", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", h1_style))
    summary_text = (
        "This report provides a formal statistical validation and ablation analysis of Lumint's "
        "multi-modal threat detection system. The evaluation spans three security modules: PhishShield (lexical/URL "
        "phishing), DocShield (document error level analysis & metadata structure), and UPIShield (transaction "
        "receipt verification). All model evaluation metrics are reported with 95% confidence intervals "
        "quantified via stratified bootstrap resampling (2000 replicates). Systematic module and feature group "
        "ablation studies prove the scientific contribution of each detector, justifying Lumint's integrated architecture."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))
    
    # Section 1: Model Performance Table
    story.append(Paragraph("1. Model Performance & Statistical Credibility", h1_style))
    story.append(Paragraph(
        "Table 1 outlines performance metrics for all classifiers. 95% Confidence Intervals (CIs) "
        "are displayed in brackets. Bold entries signify the best performing model per module selected for deployment.",
        body_style
    ))
    
    # Build Performance Table
    perf_data = [
        [
            Paragraph("Module", table_header_style),
            Paragraph("Classifier", table_header_style),
            Paragraph("F1 Score [95% CI]", table_header_style),
            Paragraph("AUC-ROC [95% CI]", table_header_style),
            Paragraph("MCC [95% CI]", table_header_style)
        ]
    ]
    
    modules_list = [("PhishShield", phish_data), ("DocShield", doc_data), ("UPIShield", upi_data)]
    for mod_name, m_data in modules_list:
        models = m_data.get("models", {})
        best_model = m_data.get("best_model", "")
        for clf_name, clf_perf in models.items():
            is_best = (clf_name == best_model)
            c_style = table_cell_bold_style if is_best else table_cell_style
            
            # format intervals
            cis = clf_perf.get("confidence_intervals", {})
            f1_ci = cis.get("f1", {})
            auc_ci = cis.get("auc", {})
            mcc_ci = cis.get("mcc", {})
            
            f1_txt = f"{f1_ci.get('point_estimate', 0.0):.3f} [{f1_ci.get('ci_lower', 0.0):.3f}, {f1_ci.get('ci_upper', 0.0):.3f}]"
            auc_txt = f"{auc_ci.get('point_estimate', 0.0):.3f} [{auc_ci.get('ci_lower', 0.0):.3f}, {auc_ci.get('ci_upper', 0.0):.3f}]"
            mcc_txt = f"{mcc_ci.get('point_estimate', 0.0):.3f} [{mcc_ci.get('ci_lower', 0.0):.3f}, {mcc_ci.get('ci_upper', 0.0):.3f}]"
            
            if is_best:
                clf_disp = f"<b>{clf_name} (Deployed)</b>"
            else:
                clf_disp = clf_name
                
            perf_data.append([
                Paragraph(mod_name, c_style),
                Paragraph(clf_disp, c_style),
                Paragraph(f1_txt, c_style),
                Paragraph(auc_txt, c_style),
                Paragraph(mcc_txt, c_style)
            ])
            
    t_perf = Table(perf_data, colWidths=[70, 110, 115, 115, 115])
    t_perf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    story.append(t_perf)
    story.append(Spacer(1, 10))
    
    # Section 2: Module Ablation Study
    story.append(Paragraph("2. Module Ablation & Fusion Security Impact", h1_style))
    story.append(Paragraph(
        "Ablation testing evaluates the degradation in detection metrics when specific detection modules "
        "are systematically disabled. Table 2 details the performance of different model configurations.",
        body_style
    ))
    
    ablation_rows = ablation_sections.get("module_ablation", [])
    if ablation_rows:
        ab_data = [
            [
                Paragraph("Configuration", table_header_style),
                Paragraph("Features / Shields", table_header_style),
                Paragraph("F1 Score", table_header_style),
                Paragraph("AUC-ROC", table_header_style),
                Paragraph("MCC", table_header_style),
                Paragraph("Δ F1", table_header_style)
            ]
        ]
        for row in ablation_rows:
            config = row.get("configuration", "--")
            features = row.get("features", "--")
            f1 = f"{row.get('f1', 0.0):.3f}" if isinstance(row.get('f1'), float) else str(row.get('f1'))
            auc = f"{row.get('auc', 0.0):.3f}" if isinstance(row.get('auc'), float) else str(row.get('auc'))
            mcc = f"{row.get('mcc', 0.0):.3f}" if isinstance(row.get('mcc'), float) else str(row.get('mcc'))
            delta = f"{row.get('delta_f1', 0.0):.3f}" if isinstance(row.get('delta_f1'), float) else str(row.get('delta_f1', "--"))
            
            ab_data.append([
                Paragraph(str(config), table_cell_bold_style if "Full" in str(config) else table_cell_style),
                Paragraph(str(features), table_cell_style),
                Paragraph(f1, table_cell_style),
                Paragraph(auc, table_cell_style),
                Paragraph(mcc, table_cell_style),
                Paragraph(delta, table_cell_style)
            ])
            
        t_ab = Table(ab_data, colWidths=[90, 150, 60, 60, 60, 60])
        t_ab.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_ab)
    else:
        story.append(Paragraph("Ablation study metrics are currently unavailable.", body_style))
        
    story.append(Spacer(1, 10))
    
    # Section 3: Interpretability & SHAP Importance
    story.append(Paragraph("3. Global Feature Importance (SHAP Analysis)", h1_style))
    story.append(Paragraph(
        "SHAP (SHapley Additive exPlanations) values validate feature attribution consistency. "
        "Below are the top 3 global features driving classification decisions for each shield module.",
        body_style
    ))
    
    shap_files = {
        "PhishShield": "r11_phish_shap_global.json",
        "DocShield": "r11_doc_shap_global.json",
        "UPIShield": "r11_upi_shap_global.json"
    }
    
    for mod_name, file_name in shap_files.items():
        sh_path = os.path.join(REPORTS_DIR, file_name)
        if os.path.exists(sh_path):
            try:
                with open(sh_path, "r", encoding="utf-8") as sf:
                    shap_data = json.load(sf)
                top_3 = shap_data.get("top_features", [])[:3]
                
                story.append(Paragraph(f"<b>{mod_name} Features:</b>", h2_style))
                for f_info in top_3:
                    f_name = f_info.get("name", "Unknown")
                    mean_shap = f_info.get("mean_abs_shap", 0.0)
                    direction = f_info.get("direction", "neutral")
                    interpretation = f_info.get("interpretation", "")
                    
                    color_tag = "green" if direction == "positive" else "red"
                    story.append(Paragraph(
                        f"• <b>{f_name}</b> (Mean |SHAP|: {mean_shap:.4f} | "
                        f"<font color='{color_tag}'>{direction.capitalize()}</font>): {interpretation}",
                        body_style
                    ))
            except Exception:
                story.append(Paragraph(f"• Failed to load SHAP data for {mod_name}.", body_style))
        else:
            story.append(Paragraph(f"• SHAP data for {mod_name} is unavailable.", body_style))
            
    story.append(Spacer(1, 10))
    
    # Section 4: Dataset References
    story.append(Paragraph("4. Dataset Integration & References", h1_style))
    story.append(Paragraph(
        "To ensure academic rigor, Lumint is evaluated against verified real-world threat "
        "datasets alongside deterministic synthetic reference baselines.",
        body_style
    ))
    
    dataset_rows = [
        [
            Paragraph("Dataset", table_header_style),
            Paragraph("Source / Repository", table_header_style),
            Paragraph("Samples", table_header_style),
            Paragraph("Digital Object Identifier (DOI)", table_header_style)
        ],
        [
            Paragraph("UCI Phishing Websites", table_cell_bold_style),
            Paragraph("UCI Machine Learning Repository", table_cell_style),
            Paragraph("11,055", table_cell_style),
            Paragraph("10.24432/C51W2X", table_cell_style)
        ],
        [
            Paragraph("DocShield Forensic", table_cell_bold_style),
            Paragraph("Lumint Synthetic Generator", table_cell_style),
            Paragraph("1,500", table_cell_style),
            Paragraph("None (Synthetic reference)", table_cell_style)
        ],
        [
            Paragraph("UPIShield Transactions", table_cell_bold_style),
            Paragraph("Lumint Synthetic Generator", table_cell_style),
            Paragraph("1,500", table_cell_style),
            Paragraph("None (Synthetic reference)", table_cell_style)
        ]
    ]
    t_ds = Table(dataset_rows, colWidths=[120, 160, 70, 170])
    t_ds.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_ds)
    
    # Build Document
    try:
        doc.build(story, canvasmaker=NumberedCanvas)
    except Exception:
        logger.exception("Failed to compile PDF document")
        raise HTTPException(
            status_code=500,
            detail="Failed to compile PDF document."
        )
        
    pdf_out = buffer.getvalue()
    buffer.close()
    
    return StreamingResponse(
        io.BytesIO(pdf_out),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=lumint_research_report.pdf"}
    )
