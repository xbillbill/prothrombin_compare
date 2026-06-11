# Rabbit prothrombin ColabFold instructions

Rabbit AlphaFold DB model was not available or could not be downloaded.

1. Run ColabFold on `data/structures/rabbit_colabfold_input.fasta`.
2. Save the final ranked model as `data/structures/rabbit_colabfold_model.pdb`.
3. Re-run:

```bash
python scripts/04_analyze_cleavage_region.py
python scripts/05_make_pymol_script.py
python scripts/06_make_report.py
```

Use the model as a structural hypothesis only; activation kinetics require biochemical validation.
