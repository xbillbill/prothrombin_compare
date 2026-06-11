from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from Bio.PDB import PDBParser
from PIL import Image, ImageDraw, ImageFont

from common import DATA, OUTPUTS, add_generated, add_warning, load_summary, save_summary, write_text


RENDERINGS = OUTPUTS / "renderings"
FIRST_WINDOW = (300, 330)
SECOND_WINDOW = (350, 375)
DELETION_SCAN = (294, 334)


def plus_selection(values: list[int]) -> str:
    return "+".join(str(value) for value in sorted(set(values))) if values else "none"


def aligned_rows() -> pd.DataFrame:
    path = DATA / "alignments" / "human_rabbit_global_alignment.csv"
    if not path.exists():
        raise FileNotFoundError(f"Alignment CSV missing: {path}")
    return pd.read_csv(path)


def rabbit_positions_for_human_window(rows: pd.DataFrame, start: int, end: int) -> list[int]:
    selected = rows[
        rows["human_pos"].between(start, end, inclusive="both")
        & rows["rabbit_pos"].notna()
        & (rows["rabbit_aa"] != "-")
    ]
    return [int(pos) for pos in selected["rabbit_pos"].tolist()]


def deletion_rows(rows: pd.DataFrame) -> pd.DataFrame:
    return rows[
        rows["human_pos"].between(DELETION_SCAN[0], DELETION_SCAN[1], inclusive="both")
        & (rows["human_aa"] != "-")
        & (rows["rabbit_aa"] == "-")
    ]


def deletion_flank_positions(rows: pd.DataFrame, flank: int = 4) -> list[int]:
    gaps = deletion_rows(rows)
    idxs: set[int] = set()
    for idx in gaps.index:
        idxs.update(range(max(0, idx - flank), min(len(rows), idx + flank + 1)))
    selected = rows.loc[sorted(idxs)] if idxs else pd.DataFrame()
    if selected.empty:
        return []
    selected = selected[selected["rabbit_pos"].notna() & (selected["rabbit_aa"] != "-")]
    return [int(pos) for pos in selected["rabbit_pos"].tolist()]


def contiguous_ranges(values: list[int]) -> str:
    if not values:
        return "none"
    values = sorted(set(values))
    ranges = []
    start = prev = values[0]
    for value in values[1:]:
        if value == prev + 1:
            prev = value
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = value
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(ranges)


def renderer_paths() -> dict[str, str | None]:
    return {
        "pymol": shutil.which("pymol"),
        "chimerax": shutil.which("chimerax") or shutil.which("ChimeraX"),
    }


def font(size: int = 16):
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def parse_ca_coords(path: Path | None) -> dict[int, tuple[float, float, float]]:
    if path is None or not path.exists():
        return {}
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(path.stem, path)
    chain = next(structure.get_chains())
    coords: dict[int, tuple[float, float, float]] = {}
    for residue in chain:
        if residue.id[0] == " " and "CA" in residue:
            atom = residue["CA"]
            coords[int(residue.id[1])] = tuple(float(value) for value in atom.coord)
    return coords


def projection_basis(coord_sets: list[dict[int, tuple[float, float, float]]], residues: list[int] | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    points = []
    for coords in coord_sets:
        for pos, xyz in coords.items():
            if residues is None or pos in residues:
                points.append(xyz)
    if len(points) < 3:
        points = [xyz for coords in coord_sets for xyz in coords.values()]
    array = np.array(points, dtype=float)
    center = array.mean(axis=0)
    _, _, vh = np.linalg.svd(array - center, full_matrices=False)
    return center, vh[0], vh[1]


def project_point(xyz: tuple[float, float, float], center: np.ndarray, axis_x: np.ndarray, axis_y: np.ndarray) -> tuple[float, float]:
    vector = np.array(xyz, dtype=float) - center
    return float(np.dot(vector, axis_x)), float(np.dot(vector, axis_y))


def scale_points(points: list[tuple[float, float]], width: int, height: int, margin: int = 90) -> dict[tuple[float, float], tuple[int, int]]:
    if not points:
        return {}
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)
    scale = min((width - 2 * margin) / span_x, (height - 2 * margin) / span_y)
    return {
        point: (
            int(margin + (point[0] - min_x) * scale),
            int(height - margin - (point[1] - min_y) * scale),
        )
        for point in points
    }


def draw_polyline(draw: ImageDraw.ImageDraw, pts: list[tuple[int, int]], color: str, width: int = 5) -> None:
    if len(pts) >= 2:
        draw.line(pts, fill=color, width=width, joint="curve")
    elif len(pts) == 1:
        x, y = pts[0]
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=color)


def draw_residue_markers(
    draw: ImageDraw.ImageDraw,
    scaled: dict[int, tuple[int, int]],
    positions: list[int],
    color: str,
    label_prefix: str | None = None,
) -> None:
    for pos in positions:
        if pos not in scaled:
            continue
        x, y = scaled[pos]
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=color, outline="black", width=2)
        if label_prefix:
            draw.text((x + 12, y - 10), f"{label_prefix}{pos}", fill=color, font=font(13))


def render_projection(
    path: Path,
    title: str,
    human_coords: dict[int, tuple[float, float, float]],
    rabbit_coords: dict[int, tuple[float, float, float]],
    human_focus: list[int],
    rabbit_focus: list[int],
    human_highlights: dict[str, list[int]],
    rabbit_highlights: dict[str, list[int]],
    note: str,
) -> None:
    width, height = 1500, 1100
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    residues_for_basis = human_focus + rabbit_focus if human_focus or rabbit_focus else None
    center, axis_x, axis_y = projection_basis([human_coords, rabbit_coords], residues_for_basis)

    all_projected: list[tuple[float, float]] = []
    human_projected: dict[int, tuple[float, float]] = {}
    rabbit_projected: dict[int, tuple[float, float]] = {}
    human_positions = human_focus if human_focus else sorted(human_coords)
    rabbit_positions = rabbit_focus if rabbit_focus else sorted(rabbit_coords)
    for pos in human_positions:
        if pos in human_coords:
            point = project_point(human_coords[pos], center, axis_x, axis_y)
            human_projected[pos] = point
            all_projected.append(point)
    for pos in rabbit_positions:
        if pos in rabbit_coords:
            point = project_point(rabbit_coords[pos], center, axis_x, axis_y)
            rabbit_projected[pos] = point
            all_projected.append(point)
    point_scale = scale_points(all_projected, width, height)
    human_scaled = {pos: point_scale[point] for pos, point in human_projected.items() if point in point_scale}
    rabbit_scaled = {pos: point_scale[point] for pos, point in rabbit_projected.items() if point in point_scale}

    draw.text((45, 30), title, fill="black", font=font(28))
    draw.text((45, 70), note, fill="black", font=font(15))
    draw.text((45, height - 72), "Pure-Python CA-trace projection; use PyMOL/ChimeraX scripts for ray-traced molecular rendering.", fill="#404040", font=font(14))

    human_trace = [human_scaled[pos] for pos in human_positions if pos in human_scaled]
    rabbit_trace = [rabbit_scaled[pos] for pos in rabbit_positions if pos in rabbit_scaled]
    draw_polyline(draw, human_trace, "#8a8a8a", width=6)
    draw_polyline(draw, rabbit_trace, "#00a6c8", width=6)

    for color, positions in human_highlights.items():
        selected = [human_scaled[pos] for pos in positions if pos in human_scaled]
        draw_polyline(draw, selected, color, width=10)
        draw_residue_markers(draw, human_scaled, positions, color)
    for color, positions in rabbit_highlights.items():
        selected = [rabbit_scaled[pos] for pos in positions if pos in rabbit_scaled]
        draw_polyline(draw, selected, color, width=10)
        draw_residue_markers(draw, rabbit_scaled, positions, color)

    draw_residue_markers(draw, human_scaled, [314, 315], "#d62728", "H")
    draw_residue_markers(draw, human_scaled, [363, 364], "#ff7f0e", "H")

    legend_x = width - 360
    legend = [
        ("human CA trace", "#8a8a8a"),
        ("rabbit CA trace", "#00a6c8"),
        ("first Xa window", "#d62728"),
        ("second Xa window", "#ff7f0e"),
        ("deletion/gap region", "#d100b8"),
    ]
    for i, (label, color) in enumerate(legend):
        y = 45 + i * 30
        draw.line((legend_x, y + 9, legend_x + 45, y + 9), fill=color, width=8)
        draw.text((legend_x + 55, y), label, fill="black", font=font(14))

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def render_pure_python(
    human_pdb: Path,
    rabbit_pdb: Path | None,
    rows: pd.DataFrame,
    manifest: dict,
    summary: dict,
) -> None:
    human_coords = parse_ca_coords(human_pdb)
    rabbit_coords = parse_ca_coords(rabbit_pdb)
    if not human_coords:
        add_warning(summary, "Pure-Python render skipped because human CA coordinates are unavailable.")
        manifest["pure_python_render_status"] = "skipped_missing_human_coordinates"
        return
    if not rabbit_coords:
        note = "Rabbit PDB missing; panels show human AlphaFold structure plus alignment-derived deletion annotations."
        manifest["pure_python_render_status"] = "complete_human_only_rabbit_missing"
    else:
        if manifest.get("rabbit_model_source_type") == "human_backbone_threaded_proxy":
            note = "Rabbit PDB is a human-backbone threaded proxy; this shows residue mapping, not independent structure prediction."
        else:
            note = "Human and rabbit CA traces are projected after using the available aligned rabbit model."
        manifest["pure_python_render_status"] = "complete_human_rabbit_overlay"

    first_positions = list(range(FIRST_WINDOW[0], FIRST_WINDOW[1] + 1))
    second_positions = list(range(SECOND_WINDOW[0], SECOND_WINDOW[1] + 1))
    deletion_positions = manifest["human_deletion_positions"]
    rabbit_first = manifest["rabbit_first_window_positions"]
    rabbit_second = manifest["rabbit_second_window_positions"]
    rabbit_flanks = manifest["rabbit_deletion_flank_positions"]
    panels = [
        (
            RENDERINGS / "01_whole_overlay.png",
            "Whole prothrombin CA-trace overlay",
            sorted(human_coords),
            sorted(rabbit_coords),
            {"#d62728": first_positions, "#ff7f0e": second_positions, "#d100b8": deletion_positions},
            {"#00a6c8": sorted(rabbit_coords), "#d100b8": rabbit_flanks},
        ),
        (
            RENDERINGS / "02_first_xa_closeup.png",
            "First Xa cleavage-site closeup: human precursor 300-330",
            first_positions,
            rabbit_first,
            {"#d62728": first_positions, "#d100b8": deletion_positions},
            {"#00a6c8": rabbit_first, "#d100b8": rabbit_flanks},
        ),
        (
            RENDERINGS / "03_deletion_flanks.png",
            "Rabbit gap context: human 299-303 deletion-equivalent segment",
            list(range(294, 314)),
            rabbit_flanks,
            {"#d100b8": deletion_positions},
            {"#d100b8": rabbit_flanks},
        ),
        (
            RENDERINGS / "04_second_xa_control.png",
            "Second Xa site control: human precursor 350-375",
            second_positions,
            rabbit_second,
            {"#ff7f0e": second_positions},
            {"#00a6c8": rabbit_second},
        ),
        (
            RENDERINGS / "05_first_xa_surface.png",
            "First Xa region pseudo-surface context",
            list(range(290, 340)),
            rabbit_first + rabbit_flanks,
            {"#d62728": first_positions, "#d100b8": deletion_positions},
            {"#00a6c8": rabbit_first, "#d100b8": rabbit_flanks},
        ),
    ]
    for path, title, human_focus, rabbit_focus, human_highlights, rabbit_highlights in panels:
        render_projection(
            path,
            title,
            human_coords,
            rabbit_coords,
            human_focus,
            rabbit_focus,
            human_highlights,
            rabbit_highlights,
            note,
        )
        add_generated(summary, path)


def choose_rabbit_pdb() -> tuple[Path | None, str]:
    aligned = DATA / "structures" / "rabbit_aligned_to_human.pdb"
    colabfold = DATA / "structures" / "rabbit_colabfold_model.pdb"
    af = DATA / "structures" / "rabbit_AF_model.pdb"
    threaded = DATA / "structures" / "rabbit_threaded_from_human_AF_P00734.pdb"
    if aligned.exists():
        return aligned, "aligned"
    if colabfold.exists():
        return colabfold, "unaligned_colabfold"
    if af.exists():
        return af, "unaligned_alphafold"
    if threaded.exists():
        return threaded, "threaded_proxy"
    return None, "missing"


def build_pymol_script(
    human_pdb: Path,
    rabbit_pdb: Path | None,
    rabbit_state: str,
    selections: dict[str, str],
) -> str:
    script = f"""# Publication-oriented PyMOL render script for human vs rabbit prothrombin.
# Run from project root:
#   pymol -cq outputs/render_human_rabbit_prothrombin.pml
reinitialize
set ray_opaque_background, off
set antialias, 2
set cartoon_fancy_helices, 1
set sphere_scale, 0.45
bg_color white
load {human_pdb.as_posix()}, human
"""
    if rabbit_pdb:
        script += f"load {rabbit_pdb.as_posix()}, rabbit\n"
        if rabbit_state.startswith("unaligned"):
            script += "# Rabbit model is not pre-aligned. Re-run script 04 after adding the rabbit model for best overlays.\n"
    else:
        script += "# Rabbit PDB missing. Add data/structures/rabbit_colabfold_model.pdb and rerun scripts 04 and 07.\n"
    script += f"""
hide everything
show cartoon, human
color gray70, human
select human_first_Xa_window, human and resi 300-330
select human_first_Xa_site, human and resi 314+315
select human_second_Xa_window, human and resi 350-375
select human_second_Xa_site, human and resi 363+364
select human_deletion_segment, human and resi {selections["human_deletion"]}
select human_thrombin_domain, human and resi 364-622
color red, human_first_Xa_window
color orange, human_second_Xa_window
color magenta, human_deletion_segment
color blue, human_thrombin_domain
show sticks, human_first_Xa_site or human_second_Xa_site or human_deletion_segment
show spheres, human_first_Xa_site or human_second_Xa_site
"""
    if rabbit_pdb:
        script += f"""
show cartoon, rabbit
color cyan, rabbit
select rabbit_first_Xa_region, rabbit and resi {selections["rabbit_first_window"]}
select rabbit_second_Xa_region, rabbit and resi {selections["rabbit_second_window"]}
select rabbit_deletion_flanks, rabbit and resi {selections["rabbit_deletion_flanks"]}
color cyan, rabbit_first_Xa_region
color marine, rabbit_second_Xa_region
color magenta, rabbit_deletion_flanks
show sticks, rabbit_first_Xa_region or rabbit_second_Xa_region or rabbit_deletion_flanks
"""
    else:
        script += """
select rabbit_first_Xa_region, none
select rabbit_second_Xa_region, none
select rabbit_deletion_flanks, none
"""
    script += """
set_view (\
     0.913,   -0.277,    0.299,\
     0.242,    0.958,    0.153,\
    -0.329,   -0.067,    0.942,\
     0.000,    0.000, -260.000,\
   315.000,  310.000,  305.000,\
   190.000,  320.000,  -20.000 )

# 01 whole protein overlay
orient human
zoom human, 12
png outputs/renderings/01_whole_overlay.png, width=1800, height=1400, ray=1

# 02 first factor Xa cleavage region
orient human_first_Xa_window
zoom human_first_Xa_window, 12
png outputs/renderings/02_first_xa_closeup.png, width=1800, height=1400, ray=1

# 03 human deletion segment and rabbit flanking residues
orient human_deletion_segment or rabbit_deletion_flanks
zoom human_deletion_segment or rabbit_deletion_flanks, 10
png outputs/renderings/03_deletion_flanks.png, width=1800, height=1400, ray=1

# 04 second factor Xa site as a control region
orient human_second_Xa_window
zoom human_second_Xa_window, 12
png outputs/renderings/04_second_xa_control.png, width=1800, height=1400, ray=1

# 05 first Xa surface context
show surface, human_first_Xa_window
set transparency, 0.45, human_first_Xa_window
orient human_first_Xa_window
zoom human_first_Xa_window, 14
png outputs/renderings/05_first_xa_surface.png, width=1800, height=1400, ray=1
hide surface

save outputs/prothrombin_compare.pse
"""
    return script


def build_chimerax_script(
    human_pdb: Path,
    rabbit_pdb: Path | None,
    selections: dict[str, str],
) -> str:
    script = f"""# ChimeraX render script for human vs rabbit prothrombin.
# Run from project root:
#   chimerax --nogui outputs/render_human_rabbit_prothrombin.cxc
open {human_pdb.as_posix()}
rename #1 human
"""
    if rabbit_pdb:
        script += f"open {rabbit_pdb.as_posix()}\nrename #2 rabbit\n"
    else:
        script += "# Rabbit PDB missing. Add data/structures/rabbit_colabfold_model.pdb and rerun scripts 04 and 07.\n"
    script += f"""
hide atoms
cartoon #1
color #1 gray
color #1:300-330 red
color #1:350-375 orange
color #1:{selections["human_deletion_cxc"]} magenta
style #1:314,315,363,364 sphere
"""
    if rabbit_pdb:
        script += f"""
cartoon #2
color #2 cyan
color #2:{selections["rabbit_deletion_flanks_cxc"]} magenta
style #2:{selections["rabbit_first_window_cxc"]},{selections["rabbit_deletion_flanks_cxc"]} stick
"""
    script += """
view
save outputs/renderings/01_whole_overlay.png width 1800 height 1400 supersample 3
view #1:300-330
save outputs/renderings/02_first_xa_closeup.png width 1800 height 1400 supersample 3
view #1:299-303
save outputs/renderings/03_deletion_flanks.png width 1800 height 1400 supersample 3
view #1:350-375
save outputs/renderings/04_second_xa_control.png width 1800 height 1400 supersample 3
surface #1:300-330
transparency #1:300-330 45
view #1:300-330
save outputs/renderings/05_first_xa_surface.png width 1800 height 1400 supersample 3
exit
"""
    return script


def try_auto_render(pml: Path, cxc: Path, manifest: dict, summary: dict) -> None:
    if manifest["rabbit_model_status"] == "missing":
        manifest["auto_render_status"] = "skipped_missing_rabbit_model"
        add_warning(summary, "Skipping automated 3D rendering because rabbit_colabfold_model.pdb is missing.")
        return
    renderers = manifest["renderers"]
    if renderers.get("pymol"):
        result = subprocess.run([renderers["pymol"], "-cq", str(pml)], cwd=OUTPUTS.parent, check=False, text=True, capture_output=True)
        manifest["auto_render_status"] = "pymol_complete" if result.returncode == 0 else "pymol_failed"
        manifest["auto_render_stdout"] = result.stdout[-4000:]
        manifest["auto_render_stderr"] = result.stderr[-4000:]
    elif renderers.get("chimerax"):
        result = subprocess.run([renderers["chimerax"], "--nogui", str(cxc)], cwd=OUTPUTS.parent, check=False, text=True, capture_output=True)
        manifest["auto_render_status"] = "chimerax_complete" if result.returncode == 0 else "chimerax_failed"
        manifest["auto_render_stdout"] = result.stdout[-4000:]
        manifest["auto_render_stderr"] = result.stderr[-4000:]
    else:
        manifest["auto_render_status"] = "skipped_no_renderer"
        add_warning(summary, "No PyMOL or ChimeraX executable found; render scripts were generated but PNGs were not rendered.")


def main() -> None:
    summary = load_summary()
    RENDERINGS.mkdir(parents=True, exist_ok=True)
    rows = aligned_rows()
    human_pdb = DATA / "structures" / "human_AF_P00734.pdb"
    rabbit_pdb, rabbit_state = choose_rabbit_pdb()
    gaps = deletion_rows(rows)
    human_deletion_positions = [int(pos) for pos in gaps["human_pos"].dropna().tolist()]
    selections = {
        "human_deletion": plus_selection(human_deletion_positions),
        "human_deletion_cxc": contiguous_ranges(human_deletion_positions),
        "rabbit_first_window": plus_selection(rabbit_positions_for_human_window(rows, *FIRST_WINDOW)),
        "rabbit_first_window_cxc": contiguous_ranges(rabbit_positions_for_human_window(rows, *FIRST_WINDOW)),
        "rabbit_second_window": plus_selection(rabbit_positions_for_human_window(rows, *SECOND_WINDOW)),
        "rabbit_second_window_cxc": contiguous_ranges(rabbit_positions_for_human_window(rows, *SECOND_WINDOW)),
        "rabbit_deletion_flanks": plus_selection(deletion_flank_positions(rows)),
        "rabbit_deletion_flanks_cxc": contiguous_ranges(deletion_flank_positions(rows)),
    }
    if selections["human_deletion"] == "none":
        add_warning(summary, "Rendering script generated without a detected human deletion segment near the first Xa site.")
    if not human_pdb.exists():
        add_warning(summary, "Human PDB missing; render scripts will not run until data/structures/human_AF_P00734.pdb exists.")

    pml = OUTPUTS / "render_human_rabbit_prothrombin.pml"
    cxc = OUTPUTS / "render_human_rabbit_prothrombin.cxc"
    write_text(pml, build_pymol_script(human_pdb, rabbit_pdb, rabbit_state, selections), summary)
    write_text(cxc, build_chimerax_script(human_pdb, rabbit_pdb, selections), summary)

    expected_pngs = [
        "outputs/renderings/01_whole_overlay.png",
        "outputs/renderings/02_first_xa_closeup.png",
        "outputs/renderings/03_deletion_flanks.png",
        "outputs/renderings/04_second_xa_control.png",
        "outputs/renderings/05_first_xa_surface.png",
    ]
    manifest = {
        "human_structure": "data/structures/human_AF_P00734.pdb",
        "rabbit_structure": str(rabbit_pdb.relative_to(OUTPUTS.parent)) if rabbit_pdb else None,
        "rabbit_model_status": rabbit_state,
        "rabbit_model_source_type": (
            "alphafold_website_prediction"
            if (DATA / "structures" / "rabbit_AF_model.pdb").exists()
            else "colabfold_prediction"
            if (DATA / "structures" / "rabbit_colabfold_model.pdb").exists()
            else "human_backbone_threaded_proxy"
            if (DATA / "structures" / "rabbit_threaded_from_human_AF_P00734.pdb").exists()
            else "missing"
        ),
        "renderers": renderer_paths(),
        "human_first_xa_site": "314/315",
        "human_second_xa_site": "363/364",
        "human_deletion_positions": human_deletion_positions,
        "human_deletion_sequence": "".join(gaps["human_aa"].tolist()) if not gaps.empty else "",
        "rabbit_first_window_positions": rabbit_positions_for_human_window(rows, *FIRST_WINDOW),
        "rabbit_second_window_positions": rabbit_positions_for_human_window(rows, *SECOND_WINDOW),
        "rabbit_deletion_flank_positions": deletion_flank_positions(rows),
        "expected_renderings": expected_pngs,
        "generated_renderings": [],
        "notes": [
            "PMID 10030826 reports a six-amino-acid deletion; this manifest records the exact alignment-derived gap for the sequence used.",
            "AlphaFold/ColabFold structures are hypotheses and do not prove cleavage kinetics.",
        ],
    }
    render_pure_python(human_pdb, rabbit_pdb, rows, manifest, summary)
    try_auto_render(pml, cxc, manifest, summary)
    existing_pngs = [path for path in expected_pngs if (OUTPUTS.parent / path).exists()]
    manifest["generated_renderings"] = existing_pngs
    for path in existing_pngs:
        add_generated(summary, OUTPUTS.parent / path)
    manifest_path = OUTPUTS / "rendering_manifest.json"
    write_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n", summary)
    save_summary(summary)
    print(f"Wrote {pml}")
    print(f"Wrote {cxc}")
    print(f"Wrote {manifest_path}")
    print(f"Auto-render status: {manifest['auto_render_status']}")


if __name__ == "__main__":
    main()
