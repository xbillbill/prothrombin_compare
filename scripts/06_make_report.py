from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from common import DATA, OUTPUTS, add_generated, add_warning, load_summary, save_summary, write_text


FIGURES = OUTPUTS / "figures"


def font(size: int = 14):
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def save_png(image: Image.Image, path: Path, summary: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    add_generated(summary, path)


def make_domain_map(summary: dict) -> None:
    width, height = 1400, 330
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    left, right = 80, 1320
    y = 150

    def x_for(pos: int) -> int:
        return int(left + (pos - 1) / (622 - 1) * (right - left))

    domains = [
        ("Gla", 44, 88, "#8dd3c7"),
        ("Kringle 1", 103, 183, "#ffffb3"),
        ("Kringle 2", 203, 283, "#ffe082"),
        ("Activation peptide / cleavage region", 284, 363, "#bebada"),
        ("Thrombin light chain", 364, 408, "#80b1d3"),
        ("Thrombin heavy chain", 409, 622, "#4f79b8"),
    ]
    draw.text((left, 20), "Human prothrombin P00734 domain map", fill="black", font=font(22))
    draw.line((left, y, right, y), fill="black", width=3)
    for name, start, end, color in domains:
        x1, x2 = x_for(start), x_for(end)
        draw.rectangle((x1, y - 35, x2, y + 35), fill=color, outline="black")
        draw.text((x1 + 4, y - 62), name, fill="black", font=font(12))
    for pos, label, color in [(314, "Xa 314/315\n(mature R271 region)", "red"), (363, "Xa 363/364\n(mature R320 region)", "orange")]:
        x = x_for(pos)
        draw.line((x, y - 75, x, y + 90), fill=color, width=4)
        draw.multiline_text((x - 70, y + 95), label, fill=color, font=font(13), align="center")
    draw.text((left, 285), "Residue position uses UniProt precursor numbering", fill="black", font=font(14))
    path = FIGURES / "domain_map.png"
    save_png(image, path, summary)


def window_strings(rows: pd.DataFrame, start: int, end: int) -> tuple[list[str], list[str], list[int | str], list[str]]:
    selected = rows[rows["human_pos"].between(start, end, inclusive="both")]
    return (
        selected["human_aa"].tolist(),
        selected["rabbit_aa"].tolist(),
        [int(pos) if not pd.isna(pos) else "" for pos in selected["human_pos"].tolist()],
        selected["label"].fillna("").tolist(),
    )


def make_alignment_figure(summary: dict) -> None:
    alignment_csv = DATA / "alignments" / "human_rabbit_global_alignment.csv"
    if not alignment_csv.exists():
        add_warning(summary, "Skipping cleavage_alignment.png because alignment CSV is missing.")
        return
    rows = pd.read_csv(alignment_csv)
    human, rabbit, positions, labels = window_strings(rows, 294, 334)
    cell = 28
    width = 130 + cell * len(human)
    height = 230
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 15), "Alignment window around the first factor Xa-sensitive site", fill="black", font=font(18))
    x0 = 95
    for i, pos in enumerate(positions):
        x = x0 + i * cell
        color = "#ffffff"
        if rabbit[i] == "-":
            color = "#ff66cc"
        if pos == 314:
            color = "#ff4444"
        draw.rectangle((x, 80, x + cell, 112), fill=color, outline="lightgray")
        draw.rectangle((x, 120, x + cell, 152), fill=color if rabbit[i] == "-" else "white", outline="lightgray")
        draw.text((x + 9, 88), human[i], fill="black", font=font(13))
        draw.text((x + 9, 128), rabbit[i], fill="black", font=font(13))
        if pos in (300, 314, 330):
            draw.text((x + 2, 58), str(pos), fill="black", font=font(11))
    draw.text((35, 88), "human", fill="black", font=font(13))
    draw.text((35, 128), "rabbit", fill="black", font=font(13))
    draw.text((20, 178), "Magenta marks rabbit gaps/deletions; red marks human precursor Arg314 first Xa site.", fill="black", font=font(13))
    path = FIGURES / "cleavage_alignment.png"
    save_png(image, path, summary)


def make_metrics_barplot(summary: dict) -> None:
    metrics_csv = OUTPUTS / "structure_metrics.csv"
    if not metrics_csv.exists():
        add_warning(summary, "Skipping metrics_barplot.png because structure metrics CSV is missing.")
        return
    df = pd.read_csv(metrics_csv)
    df = df[df["value"].notna()]
    if df.empty:
        add_warning(summary, "Skipping metrics_barplot.png because structure metrics are unavailable.")
        return
    labels = {
        "whole_model_ca_rmsd_angstrom": "Whole model",
        "first_xa_window_300_330_ca_rmsd_angstrom": "First Xa window",
        "second_xa_window_350_375_ca_rmsd_angstrom": "Second Xa window",
    }
    df["label"] = df["metric"].map(labels).fillna(df["metric"])
    width, height = 760, 420
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((35, 20), "Human vs rabbit prothrombin structural comparison", fill="black", font=font(18))
    max_value = max(float(value) for value in df["value"].tolist()) or 1.0
    colors = ["#777777", "#d62728", "#ff7f0e"]
    for i, row in enumerate(df.itertuples(index=False)):
        x = 80 + i * 220
        bar_h = int(float(row.value) / max_value * 250)
        draw.rectangle((x, 330 - bar_h, x + 120, 330), fill=colors[i % len(colors)], outline="black")
        draw.text((x, 340), str(row.label), fill="black", font=font(12))
        draw.text((x, 315 - bar_h), f"{float(row.value):.2f}", fill="black", font=font(12))
    draw.line((60, 330, 720, 330), fill="black", width=2)
    draw.text((35, 370), "CA RMSD after superposition (Angstrom)", fill="black", font=font(13))
    path = FIGURES / "metrics_barplot.png"
    save_png(image, path, summary)


def alignment_excerpt() -> str:
    path = OUTPUTS / "deletion_summary.txt"
    if not path.exists():
        return "Alignment excerpt unavailable."
    text = path.read_text()
    if "Alignment excerpt:" in text:
        return text.split("Alignment excerpt:", 1)[1].strip()
    return text.strip()


def load_metrics() -> dict:
    path = OUTPUTS / "structure_metrics.json"
    if not path.exists():
        return {"status": "unavailable", "reason": "structure_metrics.json missing"}
    return json.loads(path.read_text())


def load_rendering_manifest() -> dict:
    path = OUTPUTS / "rendering_manifest.json"
    if not path.exists():
        return {"status": "unavailable", "reason": "rendering_manifest.json missing; run scripts/07_render_cleavage_site.py"}
    return json.loads(path.read_text())


def rendering_section(manifest: dict) -> str:
    if manifest.get("status") == "unavailable":
        return f"- Rendering status: `{manifest['reason']}`.\n"
    expected = manifest.get("expected_renderings", [])
    generated = manifest.get("generated_renderings", [])
    text = (
        f"- Rabbit model status: `{manifest.get('rabbit_model_status')}`.\n"
        f"- Rabbit model source type: `{manifest.get('rabbit_model_source_type', 'unknown')}`.\n"
        f"- Pure-Python rendering status: `{manifest.get('pure_python_render_status', 'not_run')}`.\n"
        f"- Auto-render status: `{manifest.get('auto_render_status')}`.\n"
        f"- Human deletion/gap positions highlighted: `{manifest.get('human_deletion_positions')}`.\n"
        f"- Human deletion/gap sequence highlighted: `{manifest.get('human_deletion_sequence')}`.\n"
        "- Render scripts: `outputs/render_human_rabbit_prothrombin.pml` and `outputs/render_human_rabbit_prothrombin.cxc`.\n"
    )
    if generated:
        text += "- Generated renderings:\n" + "".join(f"  - `{item}`\n" for item in generated)
    else:
        text += "- Generated renderings: none yet; expected PNGs after adding the rabbit model and running a renderer:\n"
        text += "".join(f"  - `{item}`\n" for item in expected)
    return text


def generated_files(summary: dict) -> str:
    files = summary.get("generated_files", [])
    if not files:
        return "- No generated files recorded.\n"
    return "".join(f"- `{item}`\n" for item in sorted(files))


def make_report(summary: dict) -> None:
    metrics = load_metrics()
    render_manifest = load_rendering_manifest()
    rabbit_accession = summary.get("rabbit_accession") or "unresolved"
    deletion_status = summary.get("deletion_detected")
    rabbit_structure = summary.get("structure_sources", {}).get("rabbit", {})
    human_structure = summary.get("structure_sources", {}).get("human", {})
    rabbit_model_source = rabbit_structure.get("source", "unavailable")
    rabbit_model_path = rabbit_structure.get("path", "unavailable")
    rabbit_aligned_path = rabbit_structure.get("aligned_path", "data/structures/rabbit_aligned_to_human.pdb")
    rabbit_model_is_proxy = "proxy" in rabbit_model_source.lower()
    rabbit_model_method = (
        f"The rabbit model was imported from the AlphaFold website output and saved as `{rabbit_model_path}`. "
        f"The aligned version is saved as `{rabbit_aligned_path}`."
        if not rabbit_model_is_proxy
        else (
            "No rabbit AlphaFold model was available at the time of the initial run, so the workflow created "
            "`data/structures/rabbit_threaded_from_human_AF_P00734.pdb` as a visualization fallback. "
            "That fallback is useful for residue mapping, but it is not an independent rabbit structure prediction."
        )
    )
    report = f"""# Human vs Rabbit Prothrombin Comparison

## 1. Question

Can rabbit prothrombin be used to model human prothrombin activation / F1.2 generation?

## 2. Background

PubMed PMID 10030826, "Prothrombin Activation in Rabbits," tested whether rabbit prothrombin activation fragment F1.2 is a useful marker of coagulation activation. The key abstract-level claim encoded for this mini-project is that activated human plasma shows strong F1.2 generation, whereas activated rabbit plasma does not. The reported mechanistic clue is that rabbit prothrombin appears less susceptible to factor Xa cleavage at the first Xa-sensitive site, with a six-amino-acid deletion near that region.

F1.2 assays depend on prothrombin activation chemistry: factor Xa cleavage of prothrombin, in the prothrombinase context, releases activation fragments. A species difference near the first cleavage region can therefore change whether F1.2 generation reports the same biology in rabbit and human samples.

## 3. Sequence Comparison

- Human sequence: UniProt `P00734`.
- Rabbit sequence accession used: `{rabbit_accession}`.
- Human UniProt precursor numbering is used as the source of truth.
- First Xa site label: precursor `314/315`, equivalent to the mature/literature `R271` region.
- Second Xa site label: precursor `363/364`, equivalent to the mature/literature `R320` region.
- First-site-proximal deletion detected: `{deletion_status}`.

Alignment excerpt around the first Xa-sensitive region:

```text
{alignment_excerpt()}
```

See `data/alignments/human_rabbit_global_alignment.csv` and `outputs/deletion_summary.csv` for exact mapped positions.

## 4. Structure Comparison

- Human structure source: `{human_structure.get("source", "unavailable")}` `{human_structure.get("url", "")}`.
- Rabbit model source: `{rabbit_structure.get("source", "unavailable")}`.
- Rabbit model path/status: `{rabbit_structure.get("path", "unavailable")}`.

{rabbit_model_method}

Structure metrics:

```json
{json.dumps(metrics, indent=2)}
```

The structural analysis superimposes rabbit onto human using aligned CA atoms when both models are available. Local RMSD values around human precursor positions 300-330 and 350-375 should be interpreted as geometry-screening metrics, not as proof of cleavage kinetics. Low-confidence, missing, or incorrectly numbered residues are recorded as warnings in `outputs/run_summary.json`.

## 5. 3D Rendering Plan and Outputs

{rendering_section(render_manifest)}

These renderings are intended to make the first-site-proximal alignment gap visible in structural context. Pure-Python PNGs are CA-trace projections for communication and quality control; use the PyMOL/ChimeraX scripts for ray-traced molecular figures when a rabbit model and renderer are available. These images do not convert the static model into kinetic evidence.

## 6. Biological Interpretation

Human prothrombin efficiently generates F1.2 after activation, whereas PMID 10030826 reports that rabbit plasma does not show the same F1.2 response. The sequence comparison specifically tests the reported deletion near the first factor Xa-sensitive region, where altered local substrate geometry could reduce rabbit susceptibility to first-site cleavage. Therefore, rabbit prothrombin may under-report or misrepresent activation when the human question depends on F1.2 generation or first-cleavage-site assays; rabbit may still be useful for other coagulation questions, but not as a direct human substitute for this mechanism.

## 7. Limitations

- AlphaFold and ColabFold models are structural hypotheses, not experimental proof.
- Prothrombinase biology includes factor Xa, factor Va, phospholipid membrane, and Ca2+.
- Gla-domain membrane binding and activation-complex dynamics are difficult to infer from static monomer structures.
- Kinetics and prothrombinase complex biology require experimental validation, such as biochemical cleavage assays and, if useful, docking or molecular dynamics.

## 8. Files Generated

{generated_files(summary)}
"""
    write_text(OUTPUTS / "report.md", report, summary)


def main() -> None:
    summary = load_summary()
    make_domain_map(summary)
    make_alignment_figure(summary)
    make_metrics_barplot(summary)
    make_report(summary)
    save_summary(summary)
    print(f"Wrote {OUTPUTS / 'report.md'}")


if __name__ == "__main__":
    main()
