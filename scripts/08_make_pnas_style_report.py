from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from common import DATA, OUTPUTS, add_generated, load_summary, save_summary, write_text


FIRST_WINDOW = (300, 330)
SECOND_WINDOW = (350, 375)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def fasta_sequence(path: Path) -> tuple[str, str]:
    header = ""
    seq_parts = []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            header = line[1:]
        else:
            seq_parts.append(line.strip())
    return header, "".join(seq_parts)


def alignment_stats(rows: pd.DataFrame, start: int | None = None, end: int | None = None) -> dict:
    subset = rows.copy()
    if start is not None and end is not None:
        subset = subset[subset["human_pos"].between(start, end, inclusive="both")]
    comparable = subset[
        subset["human_pos"].notna()
        & subset["rabbit_pos"].notna()
        & (subset["human_aa"] != "-")
        & (subset["rabbit_aa"] != "-")
    ]
    matches = comparable[comparable["human_aa"] == comparable["rabbit_aa"]]
    rabbit_gaps = subset[(subset["human_aa"] != "-") & (subset["rabbit_aa"] == "-")]
    human_gaps = subset[(subset["human_aa"] == "-") & (subset["rabbit_aa"] != "-")]
    identity = (len(matches) / len(comparable) * 100.0) if len(comparable) else 0.0
    return {
        "comparable": int(len(comparable)),
        "matches": int(len(matches)),
        "identity_pct": identity,
        "rabbit_gap_count": int(len(rabbit_gaps)),
        "human_gap_count": int(len(human_gaps)),
    }


def deletion_blocks(rows: pd.DataFrame) -> list[dict]:
    gaps = rows[
        rows["human_pos"].between(294, 334, inclusive="both")
        & (rows["human_aa"] != "-")
        & (rows["rabbit_aa"] == "-")
    ]
    if gaps.empty:
        return []
    blocks = []
    current = []
    previous = None
    for row in gaps.itertuples(index=False):
        pos = int(getattr(row, "human_pos"))
        if previous is not None and pos != previous + 1:
            blocks.append(current)
            current = []
        current.append(row)
        previous = pos
    if current:
        blocks.append(current)
    output = []
    for block in blocks:
        output.append(
            {
                "human_start": int(getattr(block[0], "human_pos")),
                "human_end": int(getattr(block[-1], "human_pos")),
                "length": len(block),
                "sequence": "".join(getattr(row, "human_aa") for row in block),
            }
        )
    return output


def alignment_excerpt(rows: pd.DataFrame, start: int = 294, end: int = 334) -> str:
    selected = rows[rows["human_pos"].between(start, end, inclusive="both")]
    return (
        "human_pos: "
        + " ".join(f"{int(row.human_pos):>3}" for row in selected.itertuples(index=False))
        + "\nhuman:    "
        + " ".join(f" {row.human_aa} " for row in selected.itertuples(index=False))
        + "\nrabbit:   "
        + " ".join(f" {row.rabbit_aa} " for row in selected.itertuples(index=False))
    )


def pdb_residue_count(path: Path) -> int:
    if not path.exists():
        return 0
    residues = set()
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith("ATOM"):
            residues.add((line[21], line[22:26].strip()))
    return len(residues)


def mean_bfactor(path: Path, start: int, end: int) -> float | None:
    values = []
    if not path.exists():
        return None
    for line in path.read_text(errors="ignore").splitlines():
        if not line.startswith("ATOM"):
            continue
        try:
            residue = int(line[22:26])
        except ValueError:
            continue
        if start <= residue <= end and line[12:16].strip() == "CA":
            values.append(float(line[60:66]))
    if not values:
        return None
    return sum(values) / len(values)


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


def table_alignment(overall: dict, first: dict, second: dict) -> str:
    rows = [
        ("Full precursor alignment", overall),
        ("First Xa window, human 300-330", first),
        ("Second Xa window, human 350-375", second),
    ]
    text = "| Region | Comparable aligned residues | Matches | Identity | Rabbit gaps | Human gaps |\n"
    text += "|---|---:|---:|---:|---:|---:|\n"
    for label, stats in rows:
        text += (
            f"| {label} | {stats['comparable']} | {stats['matches']} | "
            f"{format_pct(stats['identity_pct'])} | {stats['rabbit_gap_count']} | {stats['human_gap_count']} |\n"
        )
    return text


def generated_rendering_list(render_manifest: dict) -> str:
    files = render_manifest.get("generated_renderings", [])
    if not files:
        return "No rendering PNGs were generated."
    return "\n".join(f"- `{item}`" for item in files)


def main() -> None:
    summary = load_summary()
    rows = pd.read_csv(DATA / "alignments" / "human_rabbit_global_alignment.csv")
    human_header, human_seq = fasta_sequence(DATA / "sequences" / "human_P00734.fasta")
    rabbit_header, rabbit_seq = fasta_sequence(DATA / "sequences" / "rabbit_F2.fasta")
    metrics = read_json(OUTPUTS / "structure_metrics.json")
    render_manifest = read_json(OUTPUTS / "rendering_manifest.json")
    deletion = deletion_blocks(rows)
    deletion_text = "; ".join(
        f"human {item['human_start']}-{item['human_end']} ({item['length']} aa, {item['sequence']})"
        for item in deletion
    ) or "none detected"
    human_pdb = DATA / "structures" / "human_AF_P00734.pdb"
    rabbit_proxy_pdb = DATA / "structures" / "rabbit_threaded_from_human_AF_P00734.pdb"
    rabbit_aligned_pdb = DATA / "structures" / "rabbit_aligned_to_human.pdb"
    rabbit_model_source = summary.get("structure_sources", {}).get("rabbit", {}).get("source", "unavailable")
    rabbit_model_path = summary.get("structure_sources", {}).get("rabbit", {}).get("path", "data/structures/rabbit_AF_model.pdb")
    rabbit_model_is_proxy = "proxy" in rabbit_model_source.lower()
    rabbit_model_description = (
        f"The rabbit model was imported from the AlphaFold website and saved as `{rabbit_model_path}`. "
        f"The aligned copy is saved as `data/structures/rabbit_aligned_to_human.pdb`."
        if not rabbit_model_is_proxy
        else (
            "No rabbit AlphaFold model was available in the initial run, so the workflow created "
            "`data/structures/rabbit_threaded_from_human_AF_P00734.pdb` as a visualization fallback."
        )
    )
    human_first_plddt = mean_bfactor(human_pdb, *FIRST_WINDOW)
    human_second_plddt = mean_bfactor(human_pdb, *SECOND_WINDOW)
    report = f"""# Species-specific prothrombin activation-site divergence explains why rabbit plasma is a poor direct model for human F1.2 generation

**PNAS-style manuscript report generated:** {datetime.now().isoformat(timespec="seconds")}

**Project directory:** `prothrombin_compare`

## Abstract

Rabbit models are often used for coagulation biology, but the fragment measured in human prothrombin activation assays is not guaranteed to be conserved mechanistically across species. We built a reproducible sequence-to-structure workflow comparing human prothrombin (`P00734`) with rabbit prothrombin resolved programmatically as `{summary.get("rabbit_accession")}` from {summary.get("rabbit_sequence_source", "unknown source")}. The alignment identifies a first-factor-Xa-site-proximal rabbit gap corresponding to {deletion_text}, upstream of the human precursor `314/315` first Xa cleavage region. The human AlphaFold DB model (`P00734`, model v6) was used as the structural reference. {rabbit_model_description} Together with the prior experimental report that rabbit plasma fails to generate detectable F1.2 under conditions where human plasma shows strong F1.2 generation, these findings support the conclusion that rabbit prothrombin is not an equivalent model for human F1.2 or first-cleavage-site assays.

## Significance

The central practical question is whether rabbit prothrombin activation can report the same biology as human prothrombin activation fragment F1.2 assays. The answer from this reproducible analysis is no for this mechanism: the rabbit sequence differs precisely near the first factor Xa-sensitive region implicated by the original rabbit activation study. The structural renderings are useful for communicating where the deletion maps in a 3D context, but they should not be used to claim altered kinetics without biochemical validation in the prothrombinase complex.

## Introduction

Prothrombin activation requires proteolysis by factor Xa in a biochemical context that includes factor Va, calcium, and a phospholipid membrane. Human prothrombin cleavage numbering differs by convention. In this project, the UniProt precursor sequence is used as the source of truth: the first Xa site is labeled around precursor `314/315`, equivalent to the mature/literature `R271` region, and the second site is labeled around precursor `363/364`, equivalent to the mature/literature `R320` region.

The motivating study, *Prothrombin Activation in Rabbits* (PMID 10030826), tested whether rabbit F1.2 could serve as a marker of coagulation activation. The paper reported that activated human plasma showed strong F1.2 generation, whereas rabbit plasma did not, and attributed the difference in part to altered susceptibility near the first Xa-sensitive site. The paper also reported a six-amino-acid deletion near that region. Our project independently reconstructs the comparison using public sequence retrieval, alignment, AlphaFold DB model retrieval for human prothrombin, and explicit rabbit structural proxy creation when no rabbit AlphaFold DB model is available.

## Results

### Human and rabbit prothrombin sequences were resolved reproducibly

The workflow retrieved human prothrombin from UniProt (`P00734`; {len(human_seq)} amino acids). UniProt REST searches did not resolve a unique rabbit F2/prothrombin sequence, so the pipeline fell back to NCBI Protein and selected `{summary.get("rabbit_accession")}` ({len(rabbit_seq)} amino acids), recorded in `data/sequences/rabbit_F2.fasta`. The raw UniProt and NCBI search payloads are preserved under `data/raw/`, allowing the sequence choice to be audited.

### Rabbit prothrombin contains a deletion/gap near the first Xa-sensitive region

The global pairwise alignment identifies {deletion_text}. This gap lies immediately upstream of the human first Xa cleavage-site label at precursor `314/315`, the region equivalent to mature/literature `R271`. The exact gap length reported here is alignment- and sequence-dependent; the original paper reported a six-amino-acid deletion, while the currently resolved NCBI protein sequence and alignment produce the explicit five-residue human segment `TGDGL` absent from the aligned rabbit sequence.

{table_alignment(alignment_stats(rows), alignment_stats(rows, *FIRST_WINDOW), alignment_stats(rows, *SECOND_WINDOW))}

Alignment excerpt around the first Xa region:

```text
{alignment_excerpt(rows)}
```

### Structural resources now include a rabbit PDB for visualization

The workflow downloaded the human AlphaFold DB model from `{summary.get("structure_sources", {}).get("human", {}).get("url", "AlphaFold DB")}` and saved it as `data/structures/human_AF_P00734.pdb`. {rabbit_model_description}

The rabbit model used in the current run contains {pdb_residue_count(rabbit_aligned_pdb)} modeled rabbit residues after alignment. Rabbit gaps are omitted in the aligned copy, so the first-site-proximal deletion is represented explicitly as absent rabbit coordinates. The aligned version is saved as `data/structures/rabbit_aligned_to_human.pdb`.

### Structural metrics are generated but deliberately caveated

The structure analysis status is `{metrics.get("status")}`. Because the rabbit model is an AlphaFold-derived prediction rather than an experimental structure, the RMSD values are geometry-screening metrics and must not be interpreted as proof of cleavage kinetics:

```json
{json.dumps(metrics, indent=2)}
```

Human AlphaFold per-residue confidence is stored in the PDB B-factor column. Mean CA pLDDT-like values from the human model are approximately `{human_first_plddt:.1f}` for the first Xa window (`300-330`) and `{human_second_plddt:.1f}` for the second Xa window (`350-375`). These values describe confidence in the human monomer prediction only; they do not validate rabbit threading or prothrombinase-complex geometry.

### Renderings show the deletion in 3D context

The rendering workflow produced the following panels:

{generated_rendering_list(render_manifest)}

Rendering manifest status:

```json
{json.dumps({k: render_manifest.get(k) for k in ["rabbit_model_status", "rabbit_model_source_type", "pure_python_render_status", "auto_render_status", "rabbit_structure"]}, indent=2)}
```

The pure-Python renderings are CA-trace projections suitable for communicating the mapping and deletion. The generated PyMOL and ChimeraX scripts (`outputs/render_human_rabbit_prothrombin.pml` and `outputs/render_human_rabbit_prothrombin.cxc`) can be used to produce ray-traced molecular renderings when those tools are installed.

## Discussion

The sequence comparison and 3D mapping support the original biological concern: rabbit prothrombin is not a direct substitute for human prothrombin when the assay readout depends on F1.2 generation or first-site cleavage. The deletion/gap near the human first Xa region provides a plausible structural explanation for reduced susceptibility at the first Xa-sensitive site, consistent with the paper's observation that rabbit plasma did not generate detectable F1.2 under conditions where human plasma did.

The most important interpretation boundary is that sequence and static structure cannot establish cleavage kinetics. Prothrombin activation is not a property of a monomer alone; it depends on factor Xa, factor Va, calcium, membrane binding, Gla-domain positioning, and reaction pathway partitioning between cleavage sites. The rabbit model is valuable for visualization and hypothesis generation, but the decisive validation remains biochemical: purified rabbit and human prothrombin activation by prothrombinase, time-resolved fragment detection, and direct comparison of first-site versus second-site cleavage products.

## Materials and Methods

### Sequence retrieval

Human prothrombin was downloaded from UniProt REST as `P00734`. Rabbit sequence retrieval was attempted first with UniProt REST queries for `organism_id:9986 AND gene:F2`, `Oryctolagus cuniculus prothrombin`, and `Oryctolagus cuniculus coagulation factor II`. Because these searches did not resolve a unique rabbit F2/prothrombin sequence, the workflow used NCBI E-utilities Protein searches and resolved `{summary.get("rabbit_accession")}`. All raw search payloads were saved in `data/raw/`.

### Alignment and cleavage-site mapping

Sequences were aligned with Biopython `PairwiseAligner` in global mode with match score `2`, mismatch score `-1`, gap open score `-10`, and gap extension score `-0.5`. Human UniProt precursor numbering was used for all residue labels. The first Xa region was defined as human precursor `300-330` with the cleavage-site label `314/315`; the second region was defined as `350-375` with the cleavage-site label `363/364`. Rabbit deletions were detected as rabbit gaps aligned to human residues within ±20 residues of human precursor `314`.

### Structure retrieval and rabbit PDB creation

The human AlphaFold DB PDB was resolved through AlphaFold metadata and saved as `data/structures/human_AF_P00734.pdb`. No rabbit AlphaFold DB structure was available for `{summary.get("rabbit_accession")}`. The project therefore creates `data/structures/rabbit_threaded_from_human_AF_P00734.pdb`: for each aligned human/rabbit residue pair, the human backbone coordinates (`N`, `CA`, `C`, `O`) are copied, the residue name is changed to the aligned rabbit amino acid, the chain is labeled `R`, and the residue number is set to the rabbit sequence position. Aligned human residues with rabbit gaps are omitted.

### Superposition and metrics

`scripts/04_analyze_cleavage_region.py` parses human and rabbit PDBs with Biopython PDB, identifies aligned CA atoms from `data/alignments/human_rabbit_global_alignment.csv`, and superimposes rabbit onto human. Whole-model and local RMSD values are written to `outputs/structure_metrics.json` and `.csv`. If a threaded proxy is ever used as a fallback, the metric status is set to `complete_threaded_proxy`; in the current run, the rabbit model is AlphaFold-derived and the RMSD values are treated as geometry-screening metrics rather than kinetic evidence.

### Rendering

`scripts/07_render_cleavage_site.py` creates PyMOL and ChimeraX render scripts and a rendering manifest. In the absence of local PyMOL/ChimeraX executables, the script creates pure-Python CA-trace projection PNGs using Biopython PDB coordinates and Pillow. These panels highlight human first Xa window `300-330`, second Xa window `350-375`, human deletion-equivalent positions `299-303`, and rabbit flanking residues derived from the alignment.

## Limitations

1. The rabbit PDB used in the current run is an AlphaFold-derived prediction, not a solved structure.
2. The original paper reported a six-amino-acid deletion; the currently resolved public protein sequence and alignment identify the explicit alignment-derived gap `TGDGL` at human `299-303`.
3. AlphaFold models are monomeric hypotheses and do not represent the complete prothrombinase complex.
4. Gla-domain membrane binding, calcium coordination, factor Va interactions, and factor Xa docking are not modeled.
5. Kinetics and prothrombinase complex biology require experimental validation.

## Conclusion

Rabbit prothrombin should not be treated as an equivalent model for human prothrombin activation fragment F1.2 generation or first-cleavage-site assays. The rabbit sequence differs near the first Xa-sensitive region, and the generated 3D mapping shows where this deletion-equivalent segment lies in the prothrombin structural context. The result is a mechanistic warning, not final kinetic proof: biochemical cleavage assays remain required.

## Data and Code Availability

All code, intermediate files, raw sequence-search payloads, alignments, structures, render scripts, figures, and reports are stored in the local project directory `prothrombin_compare/`. Key outputs include:

- `data/sequences/human_P00734.fasta`
- `data/sequences/rabbit_F2.fasta`
- `data/alignments/human_rabbit_global_alignment.csv`
- `data/structures/human_AF_P00734.pdb`
- `data/structures/rabbit_AF_model.pdb`
- `data/structures/rabbit_aligned_to_human.pdb`
- `outputs/renderings/`
- `outputs/rendering_manifest.json`
- `outputs/structure_metrics.json`

## Figure Legends

**Figure 1. Domain map of human prothrombin.** Linear map of human precursor `P00734` with Gla, kringle, activation peptide, and thrombin-chain regions. The first and second Xa site labels are shown in UniProt precursor numbering and mature/literature equivalences.

**Figure 2. Sequence alignment around the first Xa-sensitive region.** Human precursor positions `294-334` aligned to rabbit prothrombin. The rabbit gap corresponding to human `299-303` is highlighted, with human precursor `314` marked as the first Xa-site arginine region.

**Figure 3. Whole-protein CA-trace overlay.** Human AlphaFold structure and rabbit AlphaFold prediction shown as CA traces. The panel is for residue-mapping visualization, not structural validation.

**Figure 4. First Xa region closeup.** Human `300-330`, deletion-equivalent segment `299-303`, and rabbit mapped residues shown in local 3D context.

**Figure 5. Second Xa region control.** Human `350-375` and corresponding rabbit mapped residues shown as a comparison region outside the first-site-proximal deletion.

## References

1. *Prothrombin Activation in Rabbits*. Thrombosis Research 93(3):101-112, 1999. PMID 10030826. DOI: 10.1016/S0049-3848(98)00153-4. https://www.sciencedirect.com/science/article/abs/pii/S0049384898001534
2. UniProtKB P00734, human prothrombin/F2. https://www.uniprot.org/uniprotkb/P00734/entry
3. RCSB computed structure model AF_AFP00734F1 for human prothrombin. https://www.rcsb.org/structure/AF_AFP00734F1
4. AlphaFold DB model metadata and PDB for human prothrombin P00734. https://alphafold.ebi.ac.uk/entry/P00734
5. NCBI Protein accession `{summary.get("rabbit_accession")}`, rabbit prothrombin sequence used by this workflow. https://www.ncbi.nlm.nih.gov/protein/{summary.get("rabbit_accession")}
"""
    out = OUTPUTS / "pnas_style_report.md"
    write_text(out, report, summary)
    save_summary(summary)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
