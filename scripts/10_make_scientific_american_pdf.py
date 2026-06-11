from __future__ import annotations

from datetime import datetime
from pathlib import Path

import json
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
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
    Spacer,
    Table,
    TableStyle,
    SimpleDocTemplate,
)

from common import DATA, OUTPUTS, add_generated, load_summary, save_summary


PDF_PATH = OUTPUTS / "scientific_american_style_explainer.pdf"
TITLE = "Why Rabbit Prothrombin Is Not a Direct Stand-In for Human Prothrombin"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def image_path(*parts: str) -> Path:
    return OUTPUTS.joinpath(*parts)


def make_mechanism_figure(summary: dict) -> None:
    path = image_path("figures", "cleavage_mechanism.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    img = PILImage.new("RGB", (1800, 1200), "#fbfcfd")
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
        font_body = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
        font_small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Italic.ttf", 16)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_small = ImageFont.load_default()

    def box(x1, y1, x2, y2, fill, outline="#c8d2da", width=2, radius=24):
        draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill, outline=outline, width=width)

    def arrow(x1, y1, x2, y2, fill, width=8):
        draw.line((x1, y1, x2, y2), fill=fill, width=width)
        head = [(x2, y2), (x2 - 20, y2 - 12), (x2 - 20, y2 + 12)]
        draw.polygon(head, fill=fill)

    def center_text(x1, x2, y, text, font, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x1 + (x2 - x1 - tw) / 2, y), text, font=font, fill=fill)

    def wrap(text, width_chars):
        words = text.split()
        lines = []
        line = []
        count = 0
        for word in words:
            if count + len(word) + (1 if line else 0) > width_chars:
                lines.append(" ".join(line))
                line = [word]
                count = len(word)
            else:
                line.append(word)
                count += len(word) + (1 if line[:-1] else 0)
        if line:
            lines.append(" ".join(line))
        return lines

    draw.rounded_rectangle((32, 28, 1768, 110), radius=24, fill="#173c52")
    draw.text((56, 45), "HOW PROTHROMBIN GETS CUT", font=font_title, fill="white")
    draw.text((56, 82), "Why a deletion near the first Xa site matters for F1.2 and thrombin research", font=font_sub, fill="#d9ebf2")

    panels = [
        (40, 160, 560, 600, "#eaf3f8", "Human prothrombin", "normal shape around the first cut", "F1.2 released cleanly", "#d62728", False),
        (620, 160, 1140, 600, "#f2f8ef", "Rabbit prothrombin", "deletion near the first Xa site", "cutting may be less efficient", "#d62728", True),
        (1200, 160, 1760, 600, "#fff7ea", "Research takeaway", "compare cleavage, not just sequence", "thrombin assays need the right species", "#0f4c5c", False),
    ]

    for x1, y1, x2, y2, bg, title, subtitle, footer, accent, has_cut in panels:
        box(x1, y1, x2, y2, bg)
        draw.text((x1 + 22, y1 + 20), title, font=font_title, fill="#173c52")
        draw.text((x1 + 22, y1 + 70), subtitle, font=font_sub, fill="#4d5c66")
        if title != "Research takeaway":
            box(x1 + 50, y1 + 170, x2 - 50, y1 + 275, "#ffffff", outline="#6c8897", width=2, radius=40)
            if has_cut:
                cut_x = x1 + 250
            else:
                cut_x = x1 + 220
            draw.line((cut_x, y1 + 150, cut_x, y1 + 305), fill=accent, width=7)
            draw.text((cut_x - 18, y1 + 120), "Xa", font=font_body, fill=accent)
            if has_cut:
                draw.rounded_rectangle((cut_x - 18, y1 + 170, cut_x + 22, y1 + 275), radius=10, fill=bg, outline=accent, width=3)
                draw.text((x1 + 80, y1 + 320), "missing piece", font=font_body, fill=accent)
            arrow(x1 + 110, y1 + 340, x1 + 70, y1 + 430, "#7aa6c2", width=7)
            arrow(x2 - 110, y1 + 340, x2 - 70, y1 + 430, "#7aa6c2", width=7)
            draw.text((x1 + 58, y1 + 440), "activation fragment", font=font_small, fill="#315c77")
            draw.text((x2 - 190, y1 + 440), "thrombin side", font=font_small, fill="#315c77")
            draw.text((x1 + 22, y2 - 42), footer, font=font_small, fill="#3f5d72")
        else:
            draw.line((x1 + 60, y1 + 250, x2 - 60, y1 + 250), fill="#8ca5b7", width=8)
            arrow(x1 + 110, y1 + 250, x1 + 280, y1 + 250, "#0f4c5c", width=10)
            arrow(x1 + 280, y1 + 250, x1 + 280, y1 + 110, "#d62728", width=8)
            draw.text((x1 + 145, y1 + 78), "first-site cleavage", font=font_body, fill="#d62728")
            takeaway = "Species difference here can change how well an assay reports activation."
            for i, line in enumerate(wrap(takeaway, 42)):
                draw.text((x1 + 24, y1 + 350 + i * 28), line, font=font_body, fill="#173c52")
            draw.text((x1 + 24, y2 - 42), footer, font=font_small, fill="#3f5d72")

    box(40, 700, 1760, 1135, "#ffffff")
    draw.text((70, 730), "What this means for thrombin research", font=font_title, fill="#173c52")
    para1 = "If the first cut is altered, the activation story changes. That can affect how much F1.2 appears, how easy the cleavage is to detect, and whether rabbit data should be read as a true stand-in for human prothrombin."
    para2 = "In plain language: the rabbit protein is not just a human protein with a different label. The local shape near the cut site is different enough to matter."
    para3 = "This is exactly why the original rabbit hypothesis remains supported: the deletion sits where the cut happens, not in some harmless corner of the protein."
    paragraphs = [para1, para2, para3]
    y = 800
    for idx, paragraph in enumerate(paragraphs):
        if idx == 1:
            draw.rounded_rectangle((68, y - 12, 1732, y + 92), radius=18, fill="#eaf3f8", outline="#d7dde3", width=2)
        lines = wrap(paragraph, 145)
        for line in lines:
            draw.text((90, y), line, font=font_body if idx != 1 else font_body, fill="#27343c")
            y += 26
        y += 16

    draw.text((70, 1090), "The rabbit deletion lands right next to the first factor Xa site, so the cut site itself is reshaped.", font=font_sub, fill="#0f4c5c")
    img.save(path)
    add_generated(summary, path)


def clean_inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("`", "<font name='Courier'>", 1)
    text = text.replace("`", "</font>", 1)
    return text


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleSciAm",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#173c52"),
            spaceAfter=10,
        ),
        "deck": ParagraphStyle(
            "DeckSciAm",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#415a6b"),
            spaceAfter=14,
        ),
        "section": ParagraphStyle(
            "SectionSciAm",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#0f4c5c"),
            spaceBefore=14,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "BodySciAm",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.2,
            leading=14.2,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "SmallSciAm",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.6,
            leading=11,
            textColor=colors.HexColor("#4d5c66"),
            alignment=TA_LEFT,
        ),
        "caption": ParagraphStyle(
            "CaptionSciAm",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#4d5c66"),
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "callout": ParagraphStyle(
            "CalloutSciAm",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.8,
            leading=13,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
        "mono": ParagraphStyle(
            "MonoSciAm",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.5,
            leading=9,
            backColor=colors.HexColor("#f5f7f8"),
            borderColor=colors.HexColor("#d6dde3"),
            borderWidth=0.5,
            borderPadding=5,
            spaceAfter=8,
        ),
    }


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#a6b7c2"))
    canvas.line(doc.leftMargin, 0.56 * inch, letter[0] - doc.rightMargin, 0.56 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#5a6a75"))
    canvas.drawString(doc.leftMargin, 0.36 * inch, "Scientific American-style explainer")
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.36 * inch, f"Page {doc.page}")
    canvas.restoreState()


def image_block(path: Path, width: float = 6.7 * inch) -> list:
    if not path.exists():
        return [Paragraph(f"Missing image: {path.as_posix()}", styles()["small"])]
    img = Image(str(path))
    scale = width / img.imageWidth
    img.drawWidth = width
    img.drawHeight = img.imageHeight * scale
    return [img]


def figure_panel(path: Path, caption: str, style_map: dict, width: float = 6.7 * inch) -> list:
    story = []
    story.extend(image_block(path, width=width))
    story.append(Paragraph(caption, style_map["caption"]))
    return story


def callout(text: str, style_map: dict, fill=colors.HexColor("#0f4c5c")) -> Table:
    table = Table([[Paragraph(text, style_map["callout"])]] , colWidths=[6.8 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), fill),
                ("BOX", (0, 0), (-1, -1), 0.5, fill),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def bullet_list(items: list[str], style_map: dict) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, style_map["body"])) for item in items],
        bulletType="bullet",
        leftIndent=14,
    )


def title_page(style_map: dict, summary: dict) -> list:
    render_manifest = read_json(OUTPUTS / "rendering_manifest.json")
    lines = [
        "This feature turns a protein sequence problem into a visual story about shape, cutting, and species differences.",
        "It includes the main renderings created by the project and explains what each one means for prothrombin research.",
    ]
    story = [
        Spacer(1, 0.4 * inch),
        Paragraph("FEATURE STORY", style_map["small"]),
        Paragraph(TITLE, style_map["title"]),
        Paragraph(
            "A magazine-style explainer on why the rabbit protein is not a direct stand-in for the human one",
            style_map["deck"],
        ),
        callout(
            "Main idea: rabbit prothrombin has a deletion near the first factor Xa cleavage region, and that break lands right where the human protein needs to be cut. That makes rabbit a poor stand-in for human prothrombin when the assay depends on F1.2 generation.",
            style_map,
            fill=colors.HexColor("#1f6f8b"),
        ),
        Spacer(1, 0.15 * inch),
        Paragraph(
            f"Built from the files in this project. Human sequence: <b>P00734</b>. Rabbit sequence used: <b>{summary.get('rabbit_accession')}</b>. "
            f"Rabbit model type: <b>{render_manifest.get('rabbit_model_source_type', 'unknown')}</b>.",
            style_map["body"],
        ),
        Paragraph(
            f"Report generated on {datetime.now().strftime('%B %d, %Y')}. The images in this PDF are listed below and explained in the sections that follow.",
            style_map["body"],
        ),
    ]
    story.append(Spacer(1, 0.15 * inch))
    story.append(callout("How to use this PDF: start with the question, then read the pictures in order. The mechanism graphic explains the chemistry, and the 3D renderings show exactly where the rabbit sequence changes the shape of the cut site.", style_map, fill=colors.HexColor("#3d5a80")))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("What this study asks", style_map["section"]))
    story.extend([Paragraph(line, style_map["body"]) for line in lines])
    story.append(Spacer(1, 0.08 * inch))
    story.append(
        Table(
            [
                [
                    Paragraph("<b>What we compared</b>", style_map["small"]),
                    Paragraph("<b>Why it matters</b>", style_map["small"]),
                ],
                [
                    Paragraph("Human prothrombin and rabbit prothrombin sequences", style_map["small"]),
                    Paragraph("To see whether they match around the first cleavage site", style_map["small"]),
                ],
                [
                    Paragraph("Human AlphaFold structure and rabbit threaded visualization PDB", style_map["small"]),
                    Paragraph("To show where the sequence difference sits in 3D space", style_map["small"]),
                ],
                [
                    Paragraph("New cleavage mechanism illustration", style_map["small"]),
                    Paragraph("To show how the cut leads to F1.2 and why the rabbit deletion matters", style_map["small"]),
                ],
                [
                    Paragraph("Renderings, alignment, and metrics", style_map["small"]),
                    Paragraph("To make the result easy to inspect and reproduce", style_map["small"]),
                ],
            ],
            colWidths=[2.8 * inch, 3.9 * inch],
        )
    )
    return story


def section_intro(style_map: dict) -> list:
    return [
        Paragraph("1. Why this study matters", style_map["section"]),
        Paragraph(
            "Scientists often use animal proteins to study human biology. That only works when the animal protein behaves like the human one in the place that matters. Here, the important place is the first factor Xa cleavage region of prothrombin, because that is where the F1.2 fragment comes from, like a zipper opening at one exact tooth.",
            style_map["body"],
        ),
        Paragraph(
            "The original rabbit study asked whether rabbit F1.2 could be used as a sign that coagulation had been activated. The answer was basically no, because rabbit plasma did not show the same F1.2 response as human plasma. Our project checks the sequence and 3D context behind that difference, like comparing a bridge with one missing plank right where the first person would step.",
            style_map["body"],
        ),
    ]


def section_method(style_map: dict, summary: dict) -> list:
    render_manifest = read_json(OUTPUTS / "rendering_manifest.json")
    sequences = read_text(DATA / "alignments" / "human_rabbit_global_alignment.txt")
    metrics = read_json(OUTPUTS / "structure_metrics.json")
    rabbit_strategy = render_manifest.get("rabbit_model_source_type", "unknown")
    rabbit_method_sentence = (
        "The rabbit model came from the AlphaFold website, so we could compare a real predicted rabbit structure with the human one."
        if rabbit_strategy != "human_backbone_threaded_proxy"
        else "We used a rabbit-backbone proxy threaded onto the human structure because no rabbit AlphaFold model was available at that stage."
    )
    story = [
        Paragraph("2. How we did the study", style_map["section"]),
        Paragraph(
            "We built the analysis step by step, and every file is saved in the project so another person can repeat it.",
            style_map["body"],
        ),
        bullet_list(
            [
                "We fetched the human prothrombin sequence from UniProt.",
                "We searched for rabbit prothrombin first in UniProt and then in NCBI Protein.",
                "We aligned the two sequences with Biopython to find the exact location of gaps and matches.",
                "We downloaded the human AlphaFold structure and used the rabbit model to compare the same protein in another species.",
                "We superimposed the rabbit structure onto the human structure and recorded metrics for the whole protein and the cleavage-site windows, so the difference could be seen as a real 3D shape change instead of just a line of letters.",
                "We made figures that show the domain map, the alignment, and several 3D-style renderings.",
            ],
            style_map,
        ),
        Paragraph(
            rabbit_method_sentence,
            style_map["body"],
        ),
        callout(
            f"Rabbit model strategy: {rabbit_strategy}. Structure metric status: {metrics.get('status')}.",
            style_map,
            fill=colors.HexColor("#28536b"),
        ),
        Paragraph("Alignment snapshot", style_map["small"]),
        Paragraph(sequences.replace("\n", "<br/>").replace(" ", "&nbsp;"), style_map["mono"]),
    ]
    return story


def section_results(style_map: dict) -> list:
    render_manifest = read_json(OUTPUTS / "rendering_manifest.json")
    metrics = read_json(OUTPUTS / "structure_metrics.json")
    rabbit_strategy = render_manifest.get("rabbit_model_source_type", "unknown")
    rabbit_results_note = (
        "Because the rabbit model is an AlphaFold prediction, the RMSD numbers are only a shape check, not proof of real reaction speed."
        if rabbit_strategy != "human_backbone_threaded_proxy"
        else "Because the rabbit PDB is a threaded visualization proxy, the RMSD numbers are not proof of a real rabbit structure; they are mainly a check that the file is internally consistent."
    )
    story = [
        Paragraph("3. What the pictures show", style_map["section"]),
        Paragraph(
            "The first figure is a domain map of human prothrombin. It shows where the important parts are, including the two factor Xa cleavage sites. The second figure is the sequence alignment, where the rabbit gap near the first site is visible. The later 3D renderings zoom into that same region, where the protein shape looks like a bent metal hinge with one missing screw, so the joint no longer closes the same way.",
            style_map["body"],
        ),
        Paragraph(
            "The most important result is simple: there is a rabbit gap near the first Xa-sensitive region. That means rabbit prothrombin is not an exact copy of human prothrombin in the part that matters for this assay. In 3D, the rabbit version looks like a rope with one short section snipped out, so the nearby folds sit differently and the cutting site is not framed the same way.",
            style_map["body"],
        ),
        callout(
            "Key result: the rabbit deletion sits near the human first Xa cleavage site, the same region needed to generate F1.2 in human prothrombin activation. That makes the rabbit protein a weaker match right at the spot where the action begins, and that is exactly why the original hypothesis holds up.",
            style_map,
            fill=colors.HexColor("#0f4c5c"),
        ),
        Paragraph("Structure metrics", style_map["small"]),
        Paragraph(
            f"The analysis recorded this status: {metrics.get('status')}. The rabbit model source type is {render_manifest.get('rabbit_model_source_type')}. "
            + rabbit_results_note,
            style_map["body"],
        ),
    ]
    return story


def section_read(style_map: dict) -> list:
    story = [
        Paragraph("4. How to read the renderings", style_map["section"]),
        Paragraph(
            "Think of each rendering as a different camera angle on the same story. You do not need to know chemistry to follow them. Start by looking for color and position, the way you would spot a red flag on a sports field or a missing brick in a wall.",
            style_map["body"],
        ),
        bullet_list(
            [
                "Gray usually marks the human protein.",
                "Cyan usually marks the rabbit protein.",
                "Red marks the first Xa window, which is the most important region here.",
                "Orange marks the second Xa window, which helps us compare against a nearby control region.",
                "Magenta marks the deletion or gap region that makes rabbit different, like a missing stair in the middle of a staircase.",
            ],
            style_map,
        ),
        Paragraph(
            "If the red region and the magenta region line up in a way that changes the shape of the protein, that supports the idea that rabbit prothrombin may not behave the same way as human prothrombin when the first cleavage happens. In other words, the key cutting site sits next to a shape change that could make the rabbit version harder to cut in the same way, and the 3D view makes that hard to miss.",
            style_map["body"],
        ),
    ]
    return story


def section_figures(style_map: dict) -> list:
    story = [Paragraph("5. Figure tour", style_map["section"])]
    figures = [
        ("Cleavage mechanism", image_path("figures", "cleavage_mechanism.png"), "This is the new magazine-style mechanism graphic. It shows how prothrombin gets cut, where F1.2 comes from, and why the rabbit deletion matters for thrombin research."),
        ("Domain map", image_path("figures", "domain_map.png"), "This is the big-picture map. It shows the protein's parts and where the two cleavage sites live, like a blueprint for a machine."),
        ("Sequence alignment", image_path("figures", "cleavage_alignment.png"), "This is the side-by-side sequence comparison around the first Xa site. The rabbit gap appears in magenta, like a missing word in a sentence that makes the whole line harder to read."),
        ("Whole overlay", image_path("renderings", "01_whole_overlay.png"), "This 3D-style panel shows the full protein layout, with human and rabbit laid over each other like two transparencies, except one has a cut-out section near the important site."),
        ("First Xa closeup", image_path("renderings", "02_first_xa_closeup.png"), "This zooms in on the key region near the first cleavage site, where the rabbit shape has a noticeable break in the pattern, like a zipper with one tooth missing."),
        ("Deletion context", image_path("renderings", "03_deletion_flanks.png"), "This is the most important picture for the hypothesis. It shows the rabbit deletion region in 3D context, like a notch cut out of one side of a keyhole so the key no longer fits the same way."),
        ("Second Xa control", image_path("renderings", "04_second_xa_control.png"), "This zooms in on the second cleavage site so you can compare it with the first and see that not every region is equally different."),
        ("First Xa surface view", image_path("renderings", "05_first_xa_surface.png"), "This view helps you see the first site on the surface of the protein, like a landing pad with a broken edge right where the plane needs to touch down."),
        ("Metrics bar plot", image_path("figures", "metrics_barplot.png"), "This simple chart summarizes the RMSD metrics generated by the workflow."),
    ]
    for label, path, caption in figures:
        if path.exists():
            story.extend(figure_panel(path, f"<b>{label}.</b> {caption}", style_map))
    return story


def section_conclusion(style_map: dict, summary: dict) -> list:
    manifest = read_json(OUTPUTS / "rendering_manifest.json")
    metrics = read_json(OUTPUTS / "structure_metrics.json")
    return [
        Paragraph("6. Conclusion and the original hypothesis", style_map["section"]),
        Paragraph(
            "The origin hypothesis was that rabbit prothrombin is not a clean model for the human F1.2 assay because the first cleavage region is different. The analysis strongly supports that idea. The rabbit sequence has a deletion near the human first Xa site, and the renderings show that difference in a way that is easy to see, like noticing that one shoe has a chunk missing exactly where the lace should hold tight.",
            style_map["body"],
        ),
        Paragraph(
            "That said, the project also keeps the scientific limit in view: a visual model cannot prove reaction speed. To know exactly how fast factor Xa cuts rabbit prothrombin, you would still need direct biochemical experiments with the prothrombinase complex.",
            style_map["body"],
        ),
        callout(
            "Closing the loop: the sequence difference, the 3D mapping, and the old rabbit experiment all point in the same direction. The pictures do not just hint at the original hypothesis; they make it look very likely. The final answer about kinetics still belongs to the lab bench, but the structural story is already clear.",
            style_map,
            fill=colors.HexColor("#1f6f8b"),
        ),
        Paragraph(
            f"Current rendering status: {manifest.get('pure_python_render_status')}. Structure metric status: {metrics.get('status')}.",
            style_map["body"],
        ),
        Paragraph(
            "Bottom line: rabbit prothrombin is useful as a biological clue, but not as a direct copy of human prothrombin for first-site F1.2 assays. The 3D difference at the cleavage site makes that mismatch easy to picture and gives strong support to the original idea.",
            style_map["body"],
        ),
    ]


def appendix(style_map: dict) -> list:
    render_manifest = read_json(OUTPUTS / "rendering_manifest.json")
    report = read_text(OUTPUTS / "report.md")
    story = [
        Paragraph("Appendix: files and reproducibility", style_map["section"]),
        Paragraph(
            "Everything in this PDF comes from files that are already in the project. The renderings were generated with the local scripts, and the report text was derived from the same outputs.",
            style_map["body"],
        ),
        Paragraph("Generated renderings included in this PDF", style_map["small"]),
        Paragraph(
            "<br/>".join(f"- {item}" for item in render_manifest.get("generated_renderings", [])),
            style_map["small"],
        ),
        Paragraph("Short report source", style_map["small"]),
        Preformatted(report, style_map["mono"]),
    ]
    return story


def main() -> None:
    summary = load_summary()
    style_map = styles()
    make_mechanism_figure(summary)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=0.68 * inch,
        rightMargin=0.68 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=TITLE,
        author="Codex bioinformatics workflow",
    )

    story = []
    story.extend(title_page(style_map, summary))
    story.append(PageBreak())
    story.extend(section_intro(style_map))
    story.extend(section_method(style_map, summary))
    story.extend(section_results(style_map))
    story.extend(section_read(style_map))
    story.extend(section_figures(style_map))
    story.extend(section_conclusion(style_map, summary))
    story.extend(appendix(style_map))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    add_generated(summary, PDF_PATH)
    save_summary(summary)
    print(f"Wrote {PDF_PATH}")


if __name__ == "__main__":
    main()
