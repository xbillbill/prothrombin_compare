# Contributing

Thanks for helping improve this project.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Working on changes

- Keep the scripts runnable from the project root.
- Do not commit local virtual environments, cache directories, or other machine-specific files.
- Prefer small, reproducible changes that preserve the existing analysis workflow.

## Running the workflow

The project is organized as a sequence of scripts:

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

If you change one stage, rerun the downstream scripts that depend on it.

