"""Convert DOCX to styled HTML for browser review."""
from docx import Document
from docx.shared import Pt
from pathlib import Path
import html as html_lib

path = Path(r"C:\Auto-Claud\Auto-Claude\BD-Automation-Engine\data\deliverables\reports\PTS_BD_EXECUTION_STRATEGY_2026.docx")
out = path.with_suffix(".html")
doc = Document(str(path))

CSS = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', Calibri, sans-serif; color: #333; background: #f8f9fa; padding: 0; }
  .page { max-width: 900px; margin: 0 auto; background: #fff; padding: 50px 60px; box-shadow: 0 2px 20px rgba(0,0,0,0.08); }
  h1 { font-size: 28px; color: #1B2A4A; margin: 30px 0 12px; border-bottom: 2px solid #2E75B6; padding-bottom: 6px; }
  h2 { font-size: 20px; color: #1B2A4A; margin: 24px 0 10px; }
  h3 { font-size: 15px; color: #2E75B6; margin: 18px 0 8px; }
  h4 { font-size: 13px; color: #2E75B6; margin: 14px 0 6px; }
  p { font-size: 14px; line-height: 1.6; margin: 6px 0; }
  ul, ol { margin: 6px 0 6px 28px; font-size: 14px; line-height: 1.6; }
  li { margin: 3px 0; }
  table { width: 100%; border-collapse: collapse; margin: 14px 0 20px; font-size: 13px; }
  th { background: #1B2A4A; color: #fff; padding: 10px 12px; text-align: left; font-weight: 600; }
  td { padding: 8px 12px; border-bottom: 1px solid #e0e0e0; }
  tr:nth-child(even) td { background: #F2F6FA; }
  tr:hover td { background: #E8EEF5; }
  .title-page { text-align: center; padding: 80px 0 60px; border-bottom: 3px solid #1B2A4A; margin-bottom: 40px; }
  .title-page h1 { font-size: 38px; border: none; margin: 0 0 8px; }
  .title-page .subtitle { font-size: 22px; color: #2E75B6; margin: 0 0 30px; }
  .title-page .meta { font-size: 14px; color: #555; margin: 4px 0; }
  .title-page .confidential { color: #CC0000; font-weight: bold; font-size: 14px; margin-top: 30px; }
  pre { background: #f5f5f5; padding: 12px 16px; border-radius: 4px; font-family: Consolas, monospace; font-size: 12px; overflow-x: auto; margin: 10px 0; color: #404040; }
  strong { font-weight: 700; }
  .page-break { border-top: 2px dashed #ccc; margin: 40px 0; }
  .footer { text-align: center; color: #1B2A4A; font-weight: bold; font-size: 16px; margin-top: 40px; }
  .footer-sub { text-align: center; color: #555; font-size: 13px; margin-top: 8px; }
</style>
"""

lines = []
lines.append("<!DOCTYPE html><html><head><meta charset='utf-8'><title>PTS BD Execution Strategy Q1/Q2 2026</title>")
lines.append(CSS)
lines.append("</head><body><div class='page'>")

in_table = False
in_code = False
code_buf = []

for elem in doc.element.body:
    tag = elem.tag.split('}')[-1]

    if tag == 'p':
        # Find matching paragraph
        para = None
        for p in doc.paragraphs:
            if p._element is elem:
                para = p
                break
        if para is None:
            continue

        text = para.text.strip()
        if not text:
            # Check for page break
            xml = para._element.xml
            if 'w:br' in xml and 'page' in xml:
                if in_table:
                    lines.append("</table>")
                    in_table = False
                lines.append("<div class='page-break'></div>")
            continue

        style = para.style.name

        # Close table if open and we're not in a table row
        if in_table:
            lines.append("</table>")
            in_table = False

        # Build rich text with bold
        rich = ""
        for run in para.runs:
            t = html_lib.escape(run.text)
            if not t:
                continue
            is_consolas = run.font.name and "Consolas" in run.font.name
            if is_consolas:
                if not in_code:
                    in_code = True
                    code_buf = []
                code_buf.append(t)
                continue
            if in_code:
                lines.append("<pre>" + "\n".join(code_buf) + "</pre>")
                code_buf = []
                in_code = False
            if run.bold:
                rich += f"<strong>{t}</strong>"
            else:
                rich += t

        if in_code:
            code_buf.append("")
            continue

        if not rich.strip():
            continue

        # Title page elements
        if style == "Heading 2":
            lines.append(f"<h1>{rich}</h1>")
        elif style == "Heading 3":
            lines.append(f"<h2>{rich}</h2>")
        elif style == "Heading 4":
            lines.append(f"<h3>{rich}</h3>")
        elif "List Bullet" in style:
            lines.append(f"<ul><li>{rich}</li></ul>")
        elif "List Number" in style:
            lines.append(f"<ol><li>{rich}</li></ol>")
        else:
            # Check for special title page content
            if "PTS BD EXECUTION STRATEGY" in text and len(text) < 40:
                lines.append(f"<div class='title-page'><h1>{rich}</h1>")
            elif "Q1/Q2 2026" in text:
                lines.append(f"<div class='subtitle'>{rich}</div>")
            elif "CONFIDENTIAL" in text:
                lines.append(f"<div class='confidential'>{rich}</div></div>")
            elif "END OF DOCUMENT" in text:
                lines.append(f"<div class='footer'>{rich}</div>")
            elif "Generated by PTS" in text:
                lines.append(f"<div class='footer-sub'>{rich}</div>")
            elif text.startswith("Prepared:") or text.startswith("Data Sources:") or text.startswith("Records:") or text.startswith("Vector Index:") or text.startswith("Bullhorn Ingestion:"):
                lines.append(f"<div class='meta'>{rich}</div>")
            else:
                lines.append(f"<p>{rich}</p>")

    elif tag == 'tbl':
        if in_code:
            lines.append("<pre>" + "\n".join(code_buf) + "</pre>")
            code_buf = []
            in_code = False

        # Find matching table
        tbl = None
        for t in doc.tables:
            if t._tbl is elem:
                tbl = t
                break
        if tbl is None:
            continue

        lines.append("<table>")
        for r_idx, row in enumerate(tbl.rows):
            lines.append("<tr>")
            for cell in row.cells:
                cell_text = html_lib.escape(cell.text.strip())
                # Preserve bold markers
                for p in cell.paragraphs:
                    rich_cell = ""
                    for run in p.runs:
                        t = html_lib.escape(run.text)
                        if run.font.bold:
                            rich_cell += f"<strong>{t}</strong>"
                        else:
                            rich_cell += t
                    if rich_cell:
                        cell_text = rich_cell
                        break

                if r_idx == 0:
                    lines.append(f"<th>{cell_text}</th>")
                else:
                    lines.append(f"<td>{cell_text}</td>")
            lines.append("</tr>")
        lines.append("</table>")

if in_code and code_buf:
    lines.append("<pre>" + "\n".join(code_buf) + "</pre>")

lines.append("</div></body></html>")

# Merge consecutive ul/ol
html_out = "\n".join(lines)
html_out = html_out.replace("</ul>\n<ul>", "\n")
html_out = html_out.replace("</ol>\n<ol>", "\n")

out.write_text(html_out, encoding="utf-8")
print(f"HTML saved to: {out}")
