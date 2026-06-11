from __future__ import annotations

import pandas as pd

from common import DATA, OUTPUTS, add_generated, add_warning, load_summary, save_summary, write_text


def residue_range_for_human_window(rows: pd.DataFrame, start: int, end: int) -> str:
    selected = rows[
        rows["human_pos"].between(start, end, inclusive="both")
        & rows["rabbit_pos"].notna()
        & (rows["rabbit_aa"] != "-")
    ]
    positions = sorted({int(pos) for pos in selected["rabbit_pos"].tolist()})
    if not positions:
        return "none"
    return "+".join(str(pos) for pos in positions)


def deletion_flanks(rows: pd.DataFrame) -> str:
    gaps = rows[
        rows["human_pos"].between(294, 334, inclusive="both")
        & (rows["human_aa"] != "-")
        & (rows["rabbit_aa"] == "-")
    ]
    if gaps.empty:
        return "none"
    idxs = set()
    for idx in gaps.index:
        idxs.update(range(max(0, idx - 3), min(len(rows), idx + 4)))
    selected = rows.loc[sorted(idxs)]
    selected = selected[selected["rabbit_pos"].notna() & (selected["rabbit_aa"] != "-")]
    positions = sorted({int(pos) for pos in selected["rabbit_pos"].tolist()})
    return "+".join(str(pos) for pos in positions) if positions else "none"


def main() -> None:
    summary = load_summary()
    alignment_csv = DATA / "alignments" / "human_rabbit_global_alignment.csv"
    rows = pd.read_csv(alignment_csv) if alignment_csv.exists() else pd.DataFrame()
    if rows.empty:
        add_warning(summary, "PyMOL script generated without rabbit alignment-derived selections.")
        rabbit_first = "none"
        rabbit_deletion = "none"
    else:
        rabbit_first = residue_range_for_human_window(rows, 300, 330)
        rabbit_deletion = deletion_flanks(rows)

    human_pdb = DATA / "structures" / "human_AF_P00734.pdb"
    rabbit_aligned = DATA / "structures" / "rabbit_aligned_to_human.pdb"
    rabbit_model = rabbit_aligned if rabbit_aligned.exists() else DATA / "structures" / "rabbit_colabfold_model.pdb"
    if not rabbit_model.exists():
        rabbit_model = DATA / "structures" / "rabbit_AF_model.pdb"

    pml = OUTPUTS / "view_human_rabbit_prothrombin.pml"
    script = f"""# PyMOL visualization for human vs rabbit prothrombin.
# Run from project root: pymol outputs/view_human_rabbit_prothrombin.pml
reinitialize
load {human_pdb.as_posix()}, human
"""
    if rabbit_model.exists():
        script += f"load {rabbit_model.as_posix()}, rabbit\n"
    else:
        script += "# Rabbit PDB missing. Add data/structures/rabbit_colabfold_model.pdb and rerun script 04/05.\n"
    script += f"""
hide everything
show cartoon, human
color gray70, human
select human_first_Xa_site, human and resi 314+315
select human_second_Xa_site, human and resi 363+364
select human_first_Xa_window, human and resi 300-330
select human_second_Xa_window, human and resi 350-375
select human_thrombin_domain, human and resi 364-622
select human_kringle_regions, human and resi 103-183+203-283
color red, human_first_Xa_window
color orange, human_second_Xa_window
color blue, human_thrombin_domain
color yellow, human_kringle_regions
show sticks, human_first_Xa_site or human_second_Xa_site
show spheres, human_first_Xa_site or human_second_Xa_site
"""
    if rabbit_model.exists():
        script += f"""
show cartoon, rabbit
color cyan, rabbit
select rabbit_first_Xa_region, rabbit and resi {rabbit_first}
select rabbit_deletion_region, rabbit and resi {rabbit_deletion}
color magenta, rabbit_deletion_region
show sticks, rabbit_first_Xa_region or rabbit_deletion_region
"""
    script += """
bg_color white
set cartoon_fancy_helices, 1
set ray_opaque_background, off
orient human_first_Xa_window
zoom human_first_Xa_window, 18
save outputs/prothrombin_compare.pse
"""
    write_text(pml, script, summary)
    save_summary(summary)
    print(f"Wrote {pml}")


if __name__ == "__main__":
    main()
