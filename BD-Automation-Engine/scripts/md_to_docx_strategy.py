"""Convert PTS BD Execution Strategy markdown to formatted DOCX."""
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

BASE = Path(r"C:\Auto-Claud\Auto-Claude\BD-Automation-Engine")
MD_PATH = BASE / "data" / "deliverables" / "reports" / "PTS_BD_EXECUTION_STRATEGY_2026.md"
DOCX_PATH = BASE / "data" / "deliverables" / "reports" / "PTS_BD_EXECUTION_STRATEGY_2026.docx"

# Colors
NAVY = RGBColor(0x1B, 0x2A, 0x4A)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
ACCENT_BLUE = RGBColor(0x2E, 0x75, 0xB6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG = "D6E4F0"
HEADER_BG = "1B2A4A"
ALT_ROW = "F2F6FA"


def set_cell_shading(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def style_document(doc):
    """Set up document styles."""
    # Page margins
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)

    # Normal style
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(10.5)
    font.color.rgb = DARK_GRAY
    style.paragraph_format.space_after = Pt(4)
    style.paragraph_format.line_spacing = 1.15

    # Heading 1
    h1 = doc.styles["Heading 1"]
    h1.font.name = "Calibri"
    h1.font.size = Pt(22)
    h1.font.color.rgb = NAVY
    h1.font.bold = True
    h1.paragraph_format.space_before = Pt(24)
    h1.paragraph_format.space_after = Pt(8)

    # Heading 2
    h2 = doc.styles["Heading 2"]
    h2.font.name = "Calibri"
    h2.font.size = Pt(16)
    h2.font.color.rgb = NAVY
    h2.font.bold = True
    h2.paragraph_format.space_before = Pt(18)
    h2.paragraph_format.space_after = Pt(6)

    # Heading 3
    h3 = doc.styles["Heading 3"]
    h3.font.name = "Calibri"
    h3.font.size = Pt(13)
    h3.font.color.rgb = ACCENT_BLUE
    h3.font.bold = True
    h3.paragraph_format.space_before = Pt(14)
    h3.paragraph_format.space_after = Pt(4)

    # Heading 4
    h4 = doc.styles["Heading 4"]
    h4.font.name = "Calibri"
    h4.font.size = Pt(11)
    h4.font.color.rgb = ACCENT_BLUE
    h4.font.bold = True
    h4.paragraph_format.space_before = Pt(10)
    h4.paragraph_format.space_after = Pt(3)


def add_styled_table(doc, headers, rows):
    """Add a formatted table with header row and alternating shading."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    # Header row
    hdr_row = table.rows[0]
    for i, header in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(header.strip())
        run.font.name = "Calibri"
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = WHITE
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        set_cell_shading(cell, HEADER_BG)

    # Data rows
    for r_idx, row_data in enumerate(rows):
        row = table.rows[r_idx + 1]
        for c_idx, cell_text in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            # Bold text wrapped in ** **
            parts = re.split(r'(\*\*[^*]+\*\*)', cell_text.strip())
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = p.add_run(part[2:-2])
                    run.font.bold = True
                else:
                    run = p.add_run(part)
                run.font.name = "Calibri"
                run.font.size = Pt(9)
                run.font.color.rgb = DARK_GRAY
            if r_idx % 2 == 1:
                set_cell_shading(cell, ALT_ROW)

    # Set column widths roughly
    try:
        tbl = table._tbl
        tblPr = tbl.tblPr if tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
        tbl.append(tblPr) if tbl.tblPr is None else None
    except Exception:
        pass

    return table


def add_formatted_run(paragraph, text):
    """Add text with inline bold/italic formatting."""
    # Split on bold markers
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.font.bold = True
        else:
            run = paragraph.add_run(part)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = DARK_GRAY


def add_code_block(doc, lines):
    """Add a code/preformatted block."""
    for line in lines:
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.name = "Consolas"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        # Light background via shading
        pPr = p._p.get_or_add_pPr()
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F5F5F5" w:val="clear"/>')
        pPr.append(shading)


def parse_table_block(lines):
    """Parse markdown table lines into headers and rows."""
    # Filter separator lines
    data_lines = [l for l in lines if not re.match(r'^\s*\|[-:\s|]+\|\s*$', l)]
    if len(data_lines) < 1:
        return None, None

    def split_row(line):
        cells = line.strip().strip("|").split("|")
        return [c.strip() for c in cells]

    headers = split_row(data_lines[0])
    rows = [split_row(l) for l in data_lines[1:]]
    return headers, rows


def convert():
    md_text = MD_PATH.read_text(encoding="utf-8")
    lines = md_text.split("\n")

    doc = Document()
    style_document(doc)

    # --- Title Page ---
    doc.add_paragraph("")  # spacer
    doc.add_paragraph("")
    doc.add_paragraph("")

    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_p.add_run("PTS BD EXECUTION STRATEGY")
    run.font.name = "Calibri"
    run.font.size = Pt(32)
    run.font.color.rgb = NAVY
    run.font.bold = True

    subtitle_p = doc.add_paragraph()
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle_p.add_run("Q1/Q2 2026")
    run.font.name = "Calibri"
    run.font.size = Pt(20)
    run.font.color.rgb = ACCENT_BLUE

    doc.add_paragraph("")

    # Metadata box
    meta_lines = [
        "Prepared: February 20, 2026",
        "Data Sources: 8-Engine BD Intelligence Pipeline",
        "Records: 50,710 call notes | 7,339 contacts | 401 programs | 1,297 contracts",
        "Vector Index: 8,447 records across 5 collections",
        "Bullhorn Ingestion: 2026-02-20 | Pipeline: 2026-01-23",
    ]
    for line in meta_lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line)
        run.font.name = "Calibri"
        run.font.size = Pt(11)
        run.font.color.rgb = DARK_GRAY
        p.paragraph_format.space_after = Pt(2)

    doc.add_paragraph("")
    doc.add_paragraph("")

    class_p = doc.add_paragraph()
    class_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = class_p.add_run("CONFIDENTIAL — PTS INTERNAL USE ONLY")
    run.font.name = "Calibri"
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
    run.font.bold = True

    # Page break after title
    doc.add_page_break()

    # --- Parse body ---
    i = 0
    # Skip the markdown title and metadata lines (first few lines)
    while i < len(lines) and (lines[i].startswith("#") and lines[i].count("#") == 1):
        i += 1

    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []

    while i < len(lines):
        line = lines[i]

        # Code block toggle
        if line.strip().startswith("```"):
            if in_code_block:
                add_code_block(doc, code_lines)
                code_lines = []
                in_code_block = False
            else:
                # Flush any pending table
                if in_table and table_lines:
                    headers, rows = parse_table_block(table_lines)
                    if headers and rows:
                        add_styled_table(doc, headers, rows)
                    table_lines = []
                    in_table = False
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Table detection
        if line.strip().startswith("|") and "|" in line.strip()[1:]:
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line)
            i += 1
            continue
        else:
            if in_table and table_lines:
                headers, rows = parse_table_block(table_lines)
                if headers and rows:
                    add_styled_table(doc, headers, rows)
                    doc.add_paragraph("")  # spacer
                table_lines = []
                in_table = False

        stripped = line.strip()

        # Horizontal rule / separator
        if stripped.startswith("---") and len(stripped.replace("-", "")) == 0:
            i += 1
            continue

        # Headings
        if stripped.startswith("####"):
            text = stripped.lstrip("#").strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            doc.add_heading(text, level=4)
            i += 1
            continue
        if stripped.startswith("###"):
            text = stripped.lstrip("#").strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            doc.add_heading(text, level=3)
            i += 1
            continue
        if stripped.startswith("##"):
            text = stripped.lstrip("#").strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            doc.add_heading(text, level=2)
            i += 1
            continue
        if stripped.startswith("#"):
            text = stripped.lstrip("#").strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            # Skip the main title (already on title page)
            if "Execution Strategy" in text and "Q1" in text:
                i += 1
                continue
            doc.add_heading(text, level=1)
            i += 1
            continue

        # Bullet points
        if stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:]
            p = doc.add_paragraph(style="List Bullet")
            add_formatted_run(p, text)
            i += 1
            continue

        # Numbered lists
        m = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if m:
            text = m.group(2)
            p = doc.add_paragraph(style="List Number")
            add_formatted_run(p, text)
            i += 1
            continue

        # Empty line
        if not stripped:
            i += 1
            continue

        # Regular paragraph
        # Skip lines that are just metadata from the MD header
        if stripped.startswith("**Prepared:**") or stripped.startswith("**Data Sources:**") or stripped.startswith("**Data Freshness:**"):
            i += 1
            continue

        p = doc.add_paragraph()
        add_formatted_run(p, stripped)
        i += 1

    # Flush remaining table
    if in_table and table_lines:
        headers, rows = parse_table_block(table_lines)
        if headers and rows:
            add_styled_table(doc, headers, rows)

    # --- Footer ---
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("— END OF DOCUMENT —")
    run.font.name = "Calibri"
    run.font.size = Pt(14)
    run.font.color.rgb = NAVY
    run.font.bold = True

    doc.add_paragraph("")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Generated by PTS BD Intelligence Pipeline | 8-Engine Architecture\nAll data queryable via Engine 8 Knowledge System")
    run.font.name = "Calibri"
    run.font.size = Pt(10)
    run.font.color.rgb = DARK_GRAY

    # Save
    doc.save(str(DOCX_PATH))
    print(f"DOCX saved to: {DOCX_PATH}")
    print(f"Pages estimated: ~25-30 (553 lines of content)")


if __name__ == "__main__":
    convert()
