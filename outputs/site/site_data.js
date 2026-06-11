window.SITE_DATA = {
  "title": "Human vs Rabbit Prothrombin",
  "subtitle": "An interactive feature on why the rabbit protein is not a drop-in stand-in for the human one",
  "human_accession": "P00734",
  "rabbit_accession": "XP_002709128.3",
  "human_structure": "../../data/structures/human_AF_P00734.pdb",
  "rabbit_structure": "../../data/structures/rabbit_aligned_to_human.pdb",
  "mode_titles": {
    "overlay": "Overlay",
    "human": "Human only",
    "rabbit": "Rabbit only",
    "first": "First Xa site",
    "second": "Second Xa site",
    "surface": "Surface focus"
  },
  "metrics": {
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
  },
  "manifest": {
    "auto_render_status": "skipped_no_renderer",
    "expected_renderings": [
      "outputs/renderings/01_whole_overlay.png",
      "outputs/renderings/02_first_xa_closeup.png",
      "outputs/renderings/03_deletion_flanks.png",
      "outputs/renderings/04_second_xa_control.png",
      "outputs/renderings/05_first_xa_surface.png"
    ],
    "generated_renderings": [
      "outputs/renderings/01_whole_overlay.png",
      "outputs/renderings/02_first_xa_closeup.png",
      "outputs/renderings/03_deletion_flanks.png",
      "outputs/renderings/04_second_xa_control.png",
      "outputs/renderings/05_first_xa_surface.png"
    ],
    "human_deletion_positions": [
      299,
      300,
      301,
      302,
      303
    ],
    "human_deletion_sequence": "TGDGL",
    "human_first_xa_site": "314/315",
    "human_second_xa_site": "363/364",
    "human_structure": "data/structures/human_AF_P00734.pdb",
    "notes": [
      "PMID 10030826 reports a six-amino-acid deletion; this manifest records the exact alignment-derived gap for the sequence used.",
      "AlphaFold/ColabFold structures are hypotheses and do not prove cleavage kinetics."
    ],
    "pure_python_render_status": "complete_human_rabbit_overlay",
    "rabbit_deletion_flank_positions": [
      296,
      297,
      298,
      299,
      300,
      301,
      302,
      303
    ],
    "rabbit_first_window_positions": [
      300,
      301,
      302,
      303,
      304,
      305,
      306,
      307,
      308,
      309,
      310,
      311,
      312,
      313,
      314,
      315,
      316,
      317,
      318,
      319,
      320,
      321,
      322,
      323,
      324,
      325,
      326
    ],
    "rabbit_model_source_type": "alphafold_website_prediction",
    "rabbit_model_status": "aligned",
    "rabbit_second_window_positions": [
      346,
      347,
      348,
      349,
      350,
      351,
      352,
      353,
      354,
      355,
      356,
      357,
      358,
      359,
      360,
      361,
      362,
      363,
      364,
      365,
      366,
      367,
      368,
      369,
      370,
      371
    ],
    "rabbit_structure": "data/structures/rabbit_aligned_to_human.pdb",
    "renderers": {
      "chimerax": null,
      "pymol": null
    }
  },
  "gallery": [
    {
      "title": "Cleavage mechanism",
      "path": "../figures/cleavage_mechanism.png",
      "caption": "A magazine-style diagram of how prothrombin gets cut, where F1.2 comes from, and why the rabbit deletion matters."
    },
    {
      "title": "Domain map",
      "path": "../figures/domain_map.png",
      "caption": "The human protein laid out like a blueprint."
    },
    {
      "title": "Sequence alignment",
      "path": "../figures/cleavage_alignment.png",
      "caption": "The rabbit gap is visible as the magenta break near the first Xa site."
    },
    {
      "title": "Whole overlay",
      "path": "../renderings/01_whole_overlay.png",
      "caption": "Human and rabbit compared in one structural frame."
    },
    {
      "title": "First Xa closeup",
      "path": "../renderings/02_first_xa_closeup.png",
      "caption": "The critical region where the first cut happens."
    },
    {
      "title": "Deletion context",
      "path": "../renderings/03_deletion_flanks.png",
      "caption": "The rabbit gap in 3D context, where the shape shifts right next to the cut site."
    },
    {
      "title": "Second Xa control",
      "path": "../renderings/04_second_xa_control.png",
      "caption": "A neighboring site used as a control comparison."
    },
    {
      "title": "First Xa surface view",
      "path": "../renderings/05_first_xa_surface.png",
      "caption": "The cut site sitting on the protein surface."
    }
  ],
  "alignment_first": [
    {
      "human_pos": 294,
      "human_aa": "A",
      "rabbit_aa": "A",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 295,
      "human_aa": "V",
      "rabbit_aa": "I",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 296,
      "human_aa": "E",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 297,
      "human_aa": "E",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 298,
      "human_aa": "E",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 299,
      "human_aa": "T",
      "rabbit_aa": "-",
      "gap": true,
      "first_site": false,
      "deletion": true,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 300,
      "human_aa": "G",
      "rabbit_aa": "-",
      "gap": true,
      "first_site": false,
      "deletion": true,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 301,
      "human_aa": "D",
      "rabbit_aa": "-",
      "gap": true,
      "first_site": false,
      "deletion": true,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 302,
      "human_aa": "G",
      "rabbit_aa": "-",
      "gap": true,
      "first_site": false,
      "deletion": true,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 303,
      "human_aa": "L",
      "rabbit_aa": "-",
      "gap": true,
      "first_site": false,
      "deletion": true,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 304,
      "human_aa": "D",
      "rabbit_aa": "V",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 305,
      "human_aa": "E",
      "rabbit_aa": "L",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 306,
      "human_aa": "D",
      "rabbit_aa": "G",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 307,
      "human_aa": "S",
      "rabbit_aa": "L",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 308,
      "human_aa": "D",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 309,
      "human_aa": "R",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 310,
      "human_aa": "A",
      "rabbit_aa": "A",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 311,
      "human_aa": "I",
      "rabbit_aa": "I",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 312,
      "human_aa": "E",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 313,
      "human_aa": "G",
      "rabbit_aa": "G",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 314,
      "human_aa": "R",
      "rabbit_aa": "R",
      "gap": false,
      "first_site": true,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330;first_Xa_site_equiv_mature_R271_region"
    },
    {
      "human_pos": 315,
      "human_aa": "T",
      "rabbit_aa": "T",
      "gap": false,
      "first_site": true,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330;first_Xa_site_equiv_mature_R271_region"
    },
    {
      "human_pos": 316,
      "human_aa": "A",
      "rabbit_aa": "T",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 317,
      "human_aa": "T",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 318,
      "human_aa": "S",
      "rabbit_aa": "Q",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 319,
      "human_aa": "E",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 320,
      "human_aa": "Y",
      "rabbit_aa": "F",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 321,
      "human_aa": "Q",
      "rabbit_aa": "Q",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 322,
      "human_aa": "T",
      "rabbit_aa": "T",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 323,
      "human_aa": "F",
      "rabbit_aa": "F",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 324,
      "human_aa": "F",
      "rabbit_aa": "F",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 325,
      "human_aa": "N",
      "rabbit_aa": "N",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 326,
      "human_aa": "P",
      "rabbit_aa": "Q",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 327,
      "human_aa": "R",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 328,
      "human_aa": "T",
      "rabbit_aa": "T",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 329,
      "human_aa": "F",
      "rabbit_aa": "F",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 330,
      "human_aa": "G",
      "rabbit_aa": "G",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "first_Xa_window_300_330"
    },
    {
      "human_pos": 331,
      "human_aa": "S",
      "rabbit_aa": "T",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 332,
      "human_aa": "G",
      "rabbit_aa": "G",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 333,
      "human_aa": "E",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 334,
      "human_aa": "A",
      "rabbit_aa": "A",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    }
  ],
  "alignment_second": [
    {
      "human_pos": 346,
      "human_aa": "S",
      "rabbit_aa": "S",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 347,
      "human_aa": "L",
      "rabbit_aa": "L",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 348,
      "human_aa": "E",
      "rabbit_aa": "K",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 349,
      "human_aa": "D",
      "rabbit_aa": "D",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": ""
    },
    {
      "human_pos": 350,
      "human_aa": "K",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 351,
      "human_aa": "T",
      "rabbit_aa": "R",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 352,
      "human_aa": "E",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 353,
      "human_aa": "R",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 354,
      "human_aa": "E",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 355,
      "human_aa": "L",
      "rabbit_aa": "L",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 356,
      "human_aa": "L",
      "rabbit_aa": "L",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 357,
      "human_aa": "E",
      "rabbit_aa": "E",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 358,
      "human_aa": "S",
      "rabbit_aa": "S",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 359,
      "human_aa": "Y",
      "rabbit_aa": "Y",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 360,
      "human_aa": "I",
      "rabbit_aa": "I",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 361,
      "human_aa": "D",
      "rabbit_aa": "H",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 362,
      "human_aa": "G",
      "rabbit_aa": "G",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 363,
      "human_aa": "R",
      "rabbit_aa": "R",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": true,
      "label": "second_Xa_window_350_375;second_Xa_site_equiv_mature_R320_region"
    },
    {
      "human_pos": 364,
      "human_aa": "I",
      "rabbit_aa": "I",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": true,
      "label": "second_Xa_window_350_375;second_Xa_site_equiv_mature_R320_region"
    },
    {
      "human_pos": 365,
      "human_aa": "V",
      "rabbit_aa": "V",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 366,
      "human_aa": "E",
      "rabbit_aa": "G",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 367,
      "human_aa": "G",
      "rabbit_aa": "G",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 368,
      "human_aa": "S",
      "rabbit_aa": "R",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 369,
      "human_aa": "D",
      "rabbit_aa": "D",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 370,
      "human_aa": "A",
      "rabbit_aa": "A",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    },
    {
      "human_pos": 371,
      "human_aa": "E",
      "rabbit_aa": "Q",
      "gap": false,
      "first_site": false,
      "deletion": false,
      "second_site": false,
      "label": "second_Xa_window_350_375"
    }
  ],
  "alignment_excerpt": "Rabbit-alignment gaps near human precursor first Xa site (scan 294-334):\n- human 299-303 (5 aa): TGDGL\n\nAlignment excerpt:\nhuman_pos: 294 295 296 297 298 299 300 301 302 303 304 305 306 307 308 309 310 311 312 313 314 315 316 317 318 319 320 321 322 323 324 325 326 327 328 329 330 331 332 333 334\nhuman:     A   V   E   E   E   T   G   D   G   L   D   E   D   S   D   R   A   I   E   G   R   T   A   T   S   E   Y   Q   T   F   F   N   P   R   T   F   G   S   G   E   A \nrabbit:    A   I   E   E   E   -   -   -   -   -   V   L   G   L   E   E   A   I   E   G   R   T   T   E   Q   E   F   Q   T   F   F   N   Q   E   T   F   G   T   G   E   A \n",
  "first_site_window": "300-330",
  "second_site_window": "350-375",
  "deletion_positions": [
    299,
    300,
    301,
    302,
    303
  ],
  "controls": {
    "whole": "Overlay both structures and show the main deletion zone.",
    "human": "Hide the rabbit structure and inspect the human scaffold.",
    "rabbit": "Hide the human structure and inspect the rabbit prediction.",
    "first": "Zoom tight on the first Xa region and the rabbit gap.",
    "second": "Move to the second Xa region as a control.",
    "surface": "Show a surface skin to make the first cleavage region feel more physical."
  },
  "why_it_matters": [
    "The deletion is not random background noise. It sits in the first cleavage neighborhood, where the assay gets its signal.",
    "That makes rabbit prothrombin a poor direct stand-in for human F1.2 work.",
    "The 3D model turns that sequence difference into something you can actually see and rotate."
  ],
  "cut_theory": [
    {
      "title": "Human: more open around the cut",
      "text": "The human first-site region looks a little more open in the overlay. That gives the enzyme a clearer path to the scissile bond, like a doorway with no clutter in front of it.",
      "mode": "first"
    },
    {
      "title": "Rabbit: the deletion reshapes the loop",
      "text": "The rabbit gap sits right beside the same site, so the nearby loop can settle into a different shape. That can change how the cut site is presented to factor Xa.",
      "mode": "first"
    },
    {
      "title": "Why that can matter",
      "text": "If the enzyme sees a different geometry, it may not dock or cut as efficiently. That is a structural explanation for why rabbit could be harder to cut at the first site.",
      "mode": "surface"
    }
  ]
};
