# Human vs Rabbit Prothrombin Comparison

## 1. Question

Can rabbit prothrombin be used to model human prothrombin activation / F1.2 generation?

## 2. Background

PubMed PMID 10030826, "Prothrombin Activation in Rabbits," tested whether rabbit prothrombin activation fragment F1.2 is a useful marker of coagulation activation. The key abstract-level claim encoded for this mini-project is that activated human plasma shows strong F1.2 generation, whereas activated rabbit plasma does not. The reported mechanistic clue is that rabbit prothrombin appears less susceptible to factor Xa cleavage at the first Xa-sensitive site, with a six-amino-acid deletion near that region.

F1.2 assays depend on prothrombin activation chemistry: factor Xa cleavage of prothrombin, in the prothrombinase context, releases activation fragments. A species difference near the first cleavage region can therefore change whether F1.2 generation reports the same biology in rabbit and human samples.

## 3. Sequence Comparison

- Human sequence: UniProt `P00734`.
- Rabbit sequence accession used: `XP_002709128.3`.
- Human UniProt precursor numbering is used as the source of truth.
- First Xa site label: precursor `314/315`, equivalent to the mature/literature `R271` region.
- Second Xa site label: precursor `363/364`, equivalent to the mature/literature `R320` region.
- First-site-proximal deletion detected: `True`.

Alignment excerpt around the first Xa-sensitive region:

```text
human_pos: 294 295 296 297 298 299 300 301 302 303 304 305 306 307 308 309 310 311 312 313 314 315 316 317 318 319 320 321 322 323 324 325 326 327 328 329 330 331 332 333 334
human:     A   V   E   E   E   T   G   D   G   L   D   E   D   S   D   R   A   I   E   G   R   T   A   T   S   E   Y   Q   T   F   F   N   P   R   T   F   G   S   G   E   A 
rabbit:    A   I   E   E   E   -   -   -   -   -   V   L   G   L   E   E   A   I   E   G   R   T   T   E   Q   E   F   Q   T   F   F   N   Q   E   T   F   G   T   G   E   A
```

See `data/alignments/human_rabbit_global_alignment.csv` and `outputs/deletion_summary.csv` for exact mapped positions.

## 4. Structure Comparison

- Human structure source: `AlphaFold DB` `https://alphafold.ebi.ac.uk/files/AF-P00734-F1-model_v6.pdb`.
- Rabbit model source: `AlphaFold website prediction imported locally`.
- Rabbit model path/status: `data/structures/rabbit_AF_model.pdb`.

The rabbit model was imported from the AlphaFold website output and saved as `data/structures/rabbit_AF_model.pdb`. The aligned version is saved as `data/structures/rabbit_aligned_to_human.pdb`.

Structure metrics:

```json
{
  "status": "complete",
  "rabbit_model_type": "alphafold_website_prediction",
  "rabbit_model_source": "AlphaFold website prediction imported locally",
  "superposition_ca_pairs": 616,
  "whole_model_ca_rmsd_angstrom": 8.571601429967375,
  "whole_model_ca_pairs": 616,
  "first_xa_window_300_330_ca_rmsd_angstrom": 8.177920729083395,
  "first_xa_window_ca_pairs": 27,
  "second_xa_window_350_375_ca_rmsd_angstrom": 5.348764487236,
  "second_xa_window_ca_pairs": 26,
  "first_site_gap_human_positions": [
    299,
    300,
    301,
    302,
    303
  ],
  "note": "AlphaFold-derived structures are hypotheses and do not establish cleavage kinetics."
}
```

The structural analysis superimposes rabbit onto human using aligned CA atoms when both models are available. Local RMSD values around human precursor positions 300-330 and 350-375 should be interpreted as geometry-screening metrics, not as proof of cleavage kinetics. Low-confidence, missing, or incorrectly numbered residues are recorded as warnings in `outputs/run_summary.json`.

## 5. 3D Rendering Plan and Outputs

- Rabbit model status: `aligned`.
- Rabbit model source type: `alphafold_website_prediction`.
- Pure-Python rendering status: `complete_human_rabbit_overlay`.
- Auto-render status: `skipped_no_renderer`.
- Human deletion/gap positions highlighted: `[299, 300, 301, 302, 303]`.
- Human deletion/gap sequence highlighted: `TGDGL`.
- Render scripts: `outputs/render_human_rabbit_prothrombin.pml` and `outputs/render_human_rabbit_prothrombin.cxc`.
- Generated renderings:
  - `outputs/renderings/01_whole_overlay.png`
  - `outputs/renderings/02_first_xa_closeup.png`
  - `outputs/renderings/03_deletion_flanks.png`
  - `outputs/renderings/04_second_xa_control.png`
  - `outputs/renderings/05_first_xa_surface.png`


These renderings are intended to make the first-site-proximal alignment gap visible in structural context. Pure-Python PNGs are CA-trace projections for communication and quality control; use the PyMOL/ChimeraX scripts for ray-traced molecular figures when a rabbit model and renderer are available. These images do not convert the static model into kinetic evidence.

## 6. Biological Interpretation

Human prothrombin efficiently generates F1.2 after activation, whereas PMID 10030826 reports that rabbit plasma does not show the same F1.2 response. The sequence comparison specifically tests the reported deletion near the first factor Xa-sensitive region, where altered local substrate geometry could reduce rabbit susceptibility to first-site cleavage. Therefore, rabbit prothrombin may under-report or misrepresent activation when the human question depends on F1.2 generation or first-cleavage-site assays; rabbit may still be useful for other coagulation questions, but not as a direct human substitute for this mechanism.

## 7. Limitations

- AlphaFold and ColabFold models are structural hypotheses, not experimental proof.
- Prothrombinase biology includes factor Xa, factor Va, phospholipid membrane, and Ca2+.
- Gla-domain membrane binding and activation-complex dynamics are difficult to infer from static monomer structures.
- Kinetics and prothrombinase complex biology require experimental validation, such as biochemical cleavage assays and, if useful, docking or molecular dynamics.

## 8. Files Generated

- `data/alignments/human_rabbit_global_alignment.csv`
- `data/alignments/human_rabbit_global_alignment.txt`
- `data/raw/ncbi_search_rabbit.json`
- `data/raw/uniprot_search_rabbit.json`
- `data/sequences/human_P00734.fasta`
- `data/sequences/rabbit_F2.fasta`
- `data/structures/RUN_COLABFOLD_INSTRUCTIONS.md`
- `data/structures/human_AF_P00734.pdb`
- `data/structures/rabbit_AF_model.pdb`
- `data/structures/rabbit_aligned_to_human.pdb`
- `data/structures/rabbit_colabfold_input.fasta`
- `data/structures/rabbit_threaded_from_human_AF_P00734.pdb`
- `outputs/deletion_summary.csv`
- `outputs/deletion_summary.txt`
- `outputs/figures/cleavage_alignment.png`
- `outputs/figures/domain_map.png`
- `outputs/figures/metrics_barplot.png`
- `outputs/pnas_style_report.md`
- `outputs/render_human_rabbit_prothrombin.cxc`
- `outputs/render_human_rabbit_prothrombin.pml`
- `outputs/rendering_manifest.json`
- `outputs/renderings/01_whole_overlay.png`
- `outputs/renderings/02_first_xa_closeup.png`
- `outputs/renderings/03_deletion_flanks.png`
- `outputs/renderings/04_second_xa_control.png`
- `outputs/renderings/05_first_xa_surface.png`
- `outputs/report.md`
- `outputs/report.pdf`
- `outputs/scientific_american_style_explainer.pdf`
- `outputs/structure_metrics.csv`
- `outputs/structure_metrics.json`
- `outputs/view_human_rabbit_prothrombin.pml`

