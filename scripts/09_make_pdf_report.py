from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from common import OUTPUTS, add_generated, load_summary, save_summary


REPORT_MD = OUTPUTS / "report.md"
REPORT_PDF = OUTPUTS / "report.pdf"


def clean_inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = text.replace("&", "&amp;")
    text = text.replace("<font name='Courier'>", "§FONT§")
    text = text.replace("</font>", "§/FONT§")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("§FONT§", "<font name='Courier'>").replace("§/FONT§", "</font>")
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCustom",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "h2": ParagraphStyle(
            "Heading2Custom",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#1f3b57"),
            spaceBefore=12,
            spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            alignment=TA_LEFT,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "SmallCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#444444"),
        ),
        "bullet": ParagraphStyle(
            "BulletCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            leftIndent=12,
        ),
        "code": ParagraphStyle(
            "CodeCustom",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.3,
            leading=9,
            backColor=colors.HexColor("#f4f6f8"),
            borderColor=colors.HexColor("#d7dde3"),
            borderWidth=0.5,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=8,
        ),
    }


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "Human vs Rabbit Prothrombin Comparison")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def parse_markdown(markdown: str, style_map: dict) -> list:
    story = []
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("# "):
            story.append(Paragraph(clean_inline(stripped[2:]), style_map["title"]))
            i += 1
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(clean_inline(stripped[3:]), style_map["h2"]))
            i += 1
            continue
        if stripped.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            story.append(Preformatted("\n".join(code_lines), style_map["code"], maxLineLength=120))
            continue
        if stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(ListItem(Paragraph(clean_inline(lines[i].strip()[2:]), style_map["bullet"])))
                i += 1
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=16, bulletFontSize=7))
            story.append(Spacer(1, 4))
            continue
        paragraph = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith(("#", "```", "- ")):
                break
            paragraph.append(nxt)
            i += 1
        story.append(Paragraph(clean_inline(" ".join(paragraph)), style_map["body"]))
    return story


def add_figures(story: list, style_map: dict) -> None:
    figures = [
        ("Domain map", OUTPUTS / "figures" / "domain_map.png"),
        ("Cleavage-region alignment", OUTPUTS / "figures" / "cleavage_alignment.png"),
        ("Whole CA-trace overlay", OUTPUTS / "renderings" / "01_whole_overlay.png"),
        ("First Xa closeup", OUTPUTS / "renderings" / "02_first_xa_closeup.png"),
        ("Deletion-flank context", OUTPUTS / "renderings" / "03_deletion_flanks.png"),
        ("Second Xa control", OUTPUTS / "renderings" / "04_second_xa_control.png"),
    ]
    story.append(PageBreak())
    story.append(Paragraph("Figures", style_map["h2"]))
    for label, path in figures:
        if not path.exists():
            continue
        story.append(Paragraph(f"<b>{clean_inline(label)}</b>", style_map["body"]))
        img = Image(str(path))
        max_width = 6.7 * inch
        max_height = 4.8 * inch
        scale = min(max_width / img.imageWidth, max_height / img.imageHeight)
        img.drawWidth = img.imageWidth * scale
        img.drawHeight = img.imageHeight * scale
        story.append(img)
        story.append(Spacer(1, 10))


def add_summary_table(story: list, style_map: dict) -> None:
    table_data = [
        ["Output", "Path"],
        ["Markdown report", "outputs/report.md"],
        ["PDF report", "outputs/report.pdf"],
        ["PNAS-style report", "outputs/pnas_style_report.md"],
        ["Rabbit AlphaFold PDB", "data/structures/rabbit_AF_model.pdb"],
        ["Render manifest", "outputs/rendering_manifest.json"],
    ]
    table = Table(table_data, colWidths=[2.0 * inch, 4.6 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b57")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d0d8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
            ]
        )
    )
    story.append(Paragraph("Output Summary", style_map["h2"]))
    story.append(table)
    story.append(Spacer(1, 12))


def main() -> None:
    if not REPORT_MD.exists():
        raise FileNotFoundError(f"Missing markdown report: {REPORT_MD}")
    summary = load_summary()
    style_map = styles()
    doc = SimpleDocTemplate(
        str(REPORT_PDF),
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="Human vs Rabbit Prothrombin Comparison",
        author="Codex bioinformatics workflow",
    )
    story = []
    add_summary_table(story, style_map)
    story.extend(parse_markdown(REPORT_MD.read_text(), style_map))
    add_figures(story, style_map)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    add_generated(summary, REPORT_PDF)
    save_summary(summary)
    print(f"Wrote {REPORT_PDF}")


if __name__ == "__main__":
    main()
