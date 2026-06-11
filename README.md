# Human vs Rabbit Prothrombin Comparison

This repository compares human and rabbit prothrombin sequence and structure near factor Xa cleavage regions. The workflow is centered on the question of why rabbit prothrombin is not a direct stand-in for human prothrombin activation fragment F1.2 generation.

## Repository Layout

- `scripts/` contains the analysis pipeline.
- `data/` contains downloaded and derived sequence/structure inputs.
- `outputs/` contains generated figures, reports, and the HTML site.
- `requirements.txt` lists the Python dependencies.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Run from the project root:

```bash
python scripts/01_fetch_sequences.py
python scripts/02_align_sequences.py
python scripts/03_fetch_structures.py
python scripts/04_analyze_cleavage_region.py
python scripts/05_make_pymol_script.py
python scripts/06_make_report.py
python scripts/07_render_cleavage_site.py
python scripts/08_make_pnas_style_report.py
python scripts/09_make_pdf_report.py
python scripts/10_make_scientific_american_pdf.py
python scripts/11_make_website.py
```

The main outputs are:

- `outputs/run_summary.json`
- `outputs/report.md`
- `outputs/pnas_style_report.md`
- `outputs/report.pdf`
- `outputs/scientific_american_style_explainer.pdf`
- `outputs/site/index.html`

## Interactive Website

After generating the site, serve the project root locally so the browser can load the PDB files and figures:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/outputs/site/index.html
```

The page uses the AlphaFold PDB files and renderings already in the repository. The 3D viewer is powered by 3Dmol.js; if it does not load, the article, figures, and alignment panels still render.

## PyMOL

If PyMOL is installed:

```bash
pymol outputs/view_human_rabbit_prothrombin.pml
```

This loads the human AlphaFold model, highlights the first and second Xa windows, and saves `outputs/prothrombin_compare.pse`.

## 3D Renderings

For publication-oriented cleavage-site views, run:

```bash
python scripts/07_render_cleavage_site.py
```

This writes:

- `outputs/render_human_rabbit_prothrombin.pml`
- `outputs/render_human_rabbit_prothrombin.cxc`
- `outputs/rendering_manifest.json`
- provisional pure-Python CA-trace PNGs under `outputs/renderings/`

If PyMOL or ChimeraX is installed and the rabbit model exists, the script attempts to render:

- `outputs/renderings/01_whole_overlay.png`
- `outputs/renderings/02_first_xa_closeup.png`
- `outputs/renderings/03_deletion_flanks.png`
- `outputs/renderings/04_second_xa_control.png`
- `outputs/renderings/05_first_xa_surface.png`

If no renderer is installed, run one of the generated scripts manually:

```bash
pymol -cq outputs/render_human_rabbit_prothrombin.pml
chimerax --nogui outputs/render_human_rabbit_prothrombin.cxc
```

When the rabbit PDB is missing, the generated PNGs are human-only structural context panels with alignment-derived deletion annotations. They are useful for planning and communication, but they are not true human/rabbit structural overlays until the rabbit model is added.

## Rabbit Structure Workflow

If you download a rabbit model from the AlphaFold website, save it as `data/structures/rabbit_AF_model.pdb` and rerun the analysis scripts.

If no rabbit AlphaFold DB model is available, script 03 writes:

- `data/structures/rabbit_colabfold_input.fasta`
- `data/structures/RUN_COLABFOLD_INSTRUCTIONS.md`
- `data/structures/rabbit_threaded_from_human_AF_P00734.pdb`

The threaded PDB is a visualization proxy created by threading the rabbit sequence onto the human AlphaFold backbone using the saved alignment. It is useful for showing the deletion/gap and residue mapping in 3D context, but it is not an experimentally solved structure and not an independent structure prediction.

Run ColabFold on `data/structures/rabbit_colabfold_input.fasta`, save the final ranked model as `data/structures/rabbit_colabfold_model.pdb`, then rerun:

```bash
python scripts/04_analyze_cleavage_region.py
python scripts/05_make_pymol_script.py
python scripts/07_render_cleavage_site.py
python scripts/06_make_report.py
```

## Scientific Notes

- Human prothrombin UniProt accession: `P00734`.
- This workflow uses UniProt precursor numbering as the source of truth and labels precursor `314/315` as the first Xa site equivalent to the mature/literature `R271` region, and precursor `363/364` as the second Xa site equivalent to the mature/literature `R320` region.
- AlphaFold and ColabFold models are hypotheses. Kinetics and prothrombinase complex biology require experimental validation.

## License

MIT. See [LICENSE](LICENSE).
