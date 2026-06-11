from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from Bio.PDB import PDBIO, PDBParser, Superimposer

from common import DATA, OUTPUTS, add_generated, add_warning, load_summary, save_summary, write_text


FIRST_WINDOW = (300, 330)
SECOND_WINDOW = (350, 375)


def first_chain_ca(path: Path) -> dict[int, object]:
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(path.stem, path)
    chain = next(structure.get_chains())
    ca_atoms = {}
    for residue in chain:
        if residue.id[0] == " " and "CA" in residue:
            ca_atoms[int(residue.id[1])] = residue["CA"]
    return ca_atoms


def first_structure(path: Path):
    parser = PDBParser(QUIET=True)
    return parser.get_structure(path.stem, path)


def rmsd_for_pairs(rows: pd.DataFrame, h_ca: dict[int, object], r_ca: dict[int, object], window: tuple[int, int] | None) -> tuple[float | None, int]:
    coords_h = []
    coords_r = []
    for row in rows.itertuples(index=False):
        h_pos = getattr(row, "human_pos")
        r_pos = getattr(row, "rabbit_pos")
        if pd.isna(h_pos) or pd.isna(r_pos):
            continue
        h_pos = int(h_pos)
        r_pos = int(r_pos)
        if window and not (window[0] <= h_pos <= window[1]):
            continue
        if h_pos in h_ca and r_pos in r_ca:
            coords_h.append(h_ca[h_pos].coord)
            coords_r.append(r_ca[r_pos].coord)
    if not coords_h:
        return None, 0
    diff = np.array(coords_h) - np.array(coords_r)
    return float(math.sqrt(np.mean(np.sum(diff * diff, axis=1)))), len(coords_h)


def rabbit_model_metadata(path: Path) -> tuple[str, str]:
    if path.name == "rabbit_AF_model.pdb":
        return "AlphaFold website prediction imported locally", "alphafold_website_prediction"
    if path.name == "rabbit_colabfold_model.pdb":
        return "ColabFold prediction", "colabfold_prediction"
    if path.name == "rabbit_threaded_from_human_AF_P00734.pdb":
        return "Human-backbone threaded visualization proxy", "human_backbone_threaded_proxy"
    if path.name == "rabbit_aligned_to_human.pdb":
        return "Aligned rabbit model", "aligned_copy"
    return "Rabbit model", "unknown"


def find_rabbit_model(summary: dict) -> Path | None:
    candidates = [
        DATA / "structures" / "rabbit_AF_model.pdb",
        DATA / "structures" / "rabbit_colabfold_model.pdb",
        DATA / "structures" / "rabbit_threaded_from_human_AF_P00734.pdb",
        DATA / "structures" / "rabbit_aligned_to_human.pdb",
    ]
    for path in candidates:
        if path.exists() and path.stat().st_size > 0:
            rabbit_source, rabbit_source_type = rabbit_model_metadata(path)
            rabbit_summary = summary.setdefault("structure_sources", {}).setdefault("rabbit", {})
            rabbit_summary["path"] = str(path.relative_to(DATA.parent))
            rabbit_summary["source"] = rabbit_source
            rabbit_summary["source_type"] = rabbit_source_type
            if path.name == "rabbit_aligned_to_human.pdb" and (DATA / "structures" / "rabbit_AF_model.pdb").exists():
                rabbit_summary["aligned_path"] = "data/structures/rabbit_aligned_to_human.pdb"
            return path
    return None


def main() -> None:
    summary = load_summary()
    human_pdb = DATA / "structures" / "human_AF_P00734.pdb"
    rabbit_pdb = find_rabbit_model(summary)
    alignment_csv = DATA / "alignments" / "human_rabbit_global_alignment.csv"
    metrics_json = OUTPUTS / "structure_metrics.json"
    metrics_csv = OUTPUTS / "structure_metrics.csv"

    if not human_pdb.exists() or not alignment_csv.exists():
        msg = "Structure analysis requires human_AF_P00734.pdb and human_rabbit_global_alignment.csv."
        add_warning(summary, msg)
        write_text(metrics_json, json.dumps({"status": "unavailable", "reason": msg}, indent=2) + "\n", summary)
        pd.DataFrame([{"metric": "structure_analysis", "value": None, "n_pairs": 0, "status": msg}]).to_csv(metrics_csv, index=False)
        add_generated(summary, metrics_csv)
        save_summary(summary)
        print(msg)
        return

    if rabbit_pdb is None:
        msg = "Rabbit structure is missing; sequence-only report can be generated. Add rabbit_colabfold_model.pdb and rerun."
        add_warning(summary, msg)
        write_text(metrics_json, json.dumps({"status": "partial", "reason": msg}, indent=2) + "\n", summary)
        pd.DataFrame([{"metric": "structure_analysis", "value": None, "n_pairs": 0, "status": msg}]).to_csv(metrics_csv, index=False)
        add_generated(summary, metrics_csv)
        save_summary(summary)
        print(msg)
        return
    rabbit_source, rabbit_source_type = rabbit_model_metadata(rabbit_pdb)
    threaded_proxy = rabbit_source_type == "human_backbone_threaded_proxy"

    rows = pd.read_csv(alignment_csv)
    h_ca = first_chain_ca(human_pdb)
    r_ca = first_chain_ca(rabbit_pdb)
    if 1 not in h_ca:
        add_warning(summary, "Human PDB residue numbering does not appear to start at 1; UniProt-position mapping may be invalid.")
    if 1 not in r_ca:
        add_warning(summary, "Rabbit PDB residue numbering does not appear to start at 1; sequence-derived mapping may be invalid.")

    common_rows = rows.dropna(subset=["human_pos", "rabbit_pos"])
    fixed = []
    moving = []
    for row in common_rows.itertuples(index=False):
        h_pos = int(getattr(row, "human_pos"))
        r_pos = int(getattr(row, "rabbit_pos"))
        if h_pos in h_ca and r_pos in r_ca:
            fixed.append(h_ca[h_pos])
            moving.append(r_ca[r_pos])
    if len(fixed) < 3:
        msg = f"Too few common CA atoms for superposition: {len(fixed)}"
        add_warning(summary, msg)
        write_text(metrics_json, json.dumps({"status": "unavailable", "reason": msg}, indent=2) + "\n", summary)
        save_summary(summary)
        print(msg)
        return

    sup = Superimposer()
    sup.set_atoms(fixed, moving)
    rabbit_structure = first_structure(rabbit_pdb)
    sup.apply(rabbit_structure.get_atoms())
    aligned_path = DATA / "structures" / "rabbit_aligned_to_human.pdb"
    io = PDBIO()
    io.set_structure(rabbit_structure)
    io.save(str(aligned_path))
    add_generated(summary, aligned_path)

    r_ca_aligned = first_chain_ca(aligned_path)
    whole_rmsd, whole_n = rmsd_for_pairs(rows, h_ca, r_ca_aligned, None)
    first_rmsd, first_n = rmsd_for_pairs(rows, h_ca, r_ca_aligned, FIRST_WINDOW)
    second_rmsd, second_n = rmsd_for_pairs(rows, h_ca, r_ca_aligned, SECOND_WINDOW)
    deletion_rows = rows[
        rows["human_pos"].between(294, 334, inclusive="both")
        & (rows["human_aa"] != "-")
        & (rows["rabbit_aa"] == "-")
    ]

    metrics = {
        "status": "complete_threaded_proxy" if threaded_proxy else "complete",
        "rabbit_model_type": rabbit_source_type,
        "rabbit_model_source": rabbit_source,
        "superposition_ca_pairs": len(fixed),
        "whole_model_ca_rmsd_angstrom": whole_rmsd,
        "whole_model_ca_pairs": whole_n,
        "first_xa_window_300_330_ca_rmsd_angstrom": first_rmsd,
        "first_xa_window_ca_pairs": first_n,
        "second_xa_window_350_375_ca_rmsd_angstrom": second_rmsd,
        "second_xa_window_ca_pairs": second_n,
        "first_site_gap_human_positions": [int(pos) for pos in deletion_rows["human_pos"].dropna().tolist()],
        "note": (
            "Rabbit model is a human-backbone threaded visualization proxy; RMSD is template-derived and not independent structural evidence."
            if threaded_proxy
            else "AlphaFold-derived structures are hypotheses and do not establish cleavage kinetics."
        ),
    }
    if threaded_proxy:
        add_warning(summary, "Rabbit PDB is a human-backbone threaded proxy; RMSD values are not independent evidence.")
    write_text(metrics_json, json.dumps(metrics, indent=2) + "\n", summary)
    pd.DataFrame(
        [
            {"metric": "whole_model_ca_rmsd_angstrom", "value": whole_rmsd, "n_pairs": whole_n, "status": "complete"},
            {"metric": "first_xa_window_300_330_ca_rmsd_angstrom", "value": first_rmsd, "n_pairs": first_n, "status": "complete"},
            {"metric": "second_xa_window_350_375_ca_rmsd_angstrom", "value": second_rmsd, "n_pairs": second_n, "status": "complete"},
        ]
    ).to_csv(metrics_csv, index=False)
    add_generated(summary, metrics_csv)
    save_summary(summary)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
