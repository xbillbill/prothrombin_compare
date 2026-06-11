from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pandas as pd

from common import DATA, OUTPUTS, add_generated, load_summary, save_summary, write_text


SITE_ROOT = OUTPUTS / "site"
SITE_DATA_JS = SITE_ROOT / "site_data.js"
SITE_HTML = SITE_ROOT / "index.html"
SITE_CSS = SITE_ROOT / "styles.css"
SITE_JS = SITE_ROOT / "app.js"


def rel_site(path: Path) -> str:
    return str(path.relative_to(SITE_ROOT))


def make_alignment_window(csv_path: Path, start: int, end: int) -> list[dict[str, object]]:
    rows = pd.read_csv(csv_path)
    selected = rows[rows["human_pos"].between(start, end, inclusive="both")].copy()
    items: list[dict[str, object]] = []
    for row in selected.itertuples(index=False):
        pos = int(row.human_pos) if not pd.isna(row.human_pos) else None
        human_aa = str(row.human_aa)
        rabbit_aa = str(row.rabbit_aa)
        items.append(
            {
                "human_pos": pos,
                "human_aa": human_aa,
                "rabbit_aa": rabbit_aa,
                "gap": rabbit_aa == "-",
                "first_site": pos in {314, 315},
                "deletion": pos in {299, 300, 301, 302, 303},
                "second_site": pos in {363, 364},
                "label": str(row.label) if hasattr(row, "label") and not pd.isna(row.label) else "",
            }
        )
    return items


def build_site_data(summary: dict) -> dict:
    metrics = json.loads((OUTPUTS / "structure_metrics.json").read_text())
    manifest = json.loads((OUTPUTS / "rendering_manifest.json").read_text())
    deletion_summary = (OUTPUTS / "deletion_summary.txt").read_text() if (OUTPUTS / "deletion_summary.txt").exists() else ""
    return {
        "title": "Human vs Rabbit Prothrombin",
        "subtitle": "An interactive feature on why the rabbit protein is not a drop-in stand-in for the human one",
        "human_accession": summary.get("human_accession"),
        "rabbit_accession": summary.get("rabbit_accession"),
        "human_structure": "../../data/structures/human_AF_P00734.pdb",
        "rabbit_structure": "../../data/structures/rabbit_aligned_to_human.pdb",
        "mode_titles": {
            "overlay": "Overlay",
            "human": "Human only",
            "rabbit": "Rabbit only",
            "first": "First Xa site",
            "second": "Second Xa site",
            "surface": "Surface focus",
        },
        "metrics": metrics,
        "manifest": manifest,
        "gallery": [
            {
                "title": "Cleavage mechanism",
                "path": "../figures/cleavage_mechanism.png",
                "caption": "A magazine-style diagram of how prothrombin gets cut, where F1.2 comes from, and why the rabbit deletion matters.",
            },
            {
                "title": "Domain map",
                "path": "../figures/domain_map.png",
                "caption": "The human protein laid out like a blueprint.",
            },
            {
                "title": "Sequence alignment",
                "path": "../figures/cleavage_alignment.png",
                "caption": "The rabbit gap is visible as the magenta break near the first Xa site.",
            },
            {
                "title": "Whole overlay",
                "path": "../renderings/01_whole_overlay.png",
                "caption": "Human and rabbit compared in one structural frame.",
            },
            {
                "title": "First Xa closeup",
                "path": "../renderings/02_first_xa_closeup.png",
                "caption": "The critical region where the first cut happens.",
            },
            {
                "title": "Deletion context",
                "path": "../renderings/03_deletion_flanks.png",
                "caption": "The rabbit gap in 3D context, where the shape shifts right next to the cut site.",
            },
            {
                "title": "Second Xa control",
                "path": "../renderings/04_second_xa_control.png",
                "caption": "A neighboring site used as a control comparison.",
            },
            {
                "title": "First Xa surface view",
                "path": "../renderings/05_first_xa_surface.png",
                "caption": "The cut site sitting on the protein surface.",
            },
        ],
        "alignment_first": make_alignment_window(DATA / "alignments" / "human_rabbit_global_alignment.csv", 294, 334),
        "alignment_second": make_alignment_window(DATA / "alignments" / "human_rabbit_global_alignment.csv", 346, 371),
        "alignment_excerpt": deletion_summary,
        "first_site_window": "300-330",
        "second_site_window": "350-375",
        "deletion_positions": [299, 300, 301, 302, 303],
        "controls": {
            "whole": "Overlay both structures and show the main deletion zone.",
            "human": "Hide the rabbit structure and inspect the human scaffold.",
            "rabbit": "Hide the human structure and inspect the rabbit prediction.",
            "first": "Zoom tight on the first Xa region and the rabbit gap.",
            "second": "Move to the second Xa region as a control.",
            "surface": "Show a surface skin to make the first cleavage region feel more physical.",
        },
        "why_it_matters": [
            "The deletion is not random background noise. It sits in the first cleavage neighborhood, where the assay gets its signal.",
            "That makes rabbit prothrombin a poor direct stand-in for human F1.2 work.",
            "The 3D model turns that sequence difference into something you can actually see and rotate.",
        ],
        "cut_theory": [
            {
                "title": "Human: more open around the cut",
                "text": "The human first-site region looks a little more open in the overlay. That gives the enzyme a clearer path to the scissile bond, like a doorway with no clutter in front of it.",
                "mode": "first",
            },
            {
                "title": "Rabbit: the deletion reshapes the loop",
                "text": "The rabbit gap sits right beside the same site, so the nearby loop can settle into a different shape. That can change how the cut site is presented to factor Xa.",
                "mode": "first",
            },
            {
                "title": "Why that can matter",
                "text": "If the enzyme sees a different geometry, it may not dock or cut as efficiently. That is a structural explanation for why rabbit could be harder to cut at the first site.",
                "mode": "surface",
            },
        ],
    }


def write_site_files(site_data: dict, summary: dict) -> None:
    SITE_ROOT.mkdir(parents=True, exist_ok=True)
    write_text(SITE_DATA_JS, "window.SITE_DATA = " + json.dumps(site_data, indent=2) + ";\n", summary)

    html = textwrap.dedent(
        """
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>Human vs Rabbit Prothrombin</title>
          <link rel="stylesheet" href="./styles.css" />
          <script src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.0.4/3Dmol-min.js"></script>
          <script defer src="./site_data.js"></script>
          <script defer src="./app.js"></script>
        </head>
        <body>
          <div class="bg-orb bg-orb-a"></div>
          <div class="bg-orb bg-orb-b"></div>
          <header class="masthead">
            <div class="kicker">Interactive feature</div>
            <h1>Human vs Rabbit Prothrombin</h1>
            <p class="deck">A visual story about a tiny deletion, a big cleavage site, and why rabbit prothrombin is not a drop-in model for the human assay.</p>
            <div class="masthead-meta">
              <div><span>Human</span><strong>P00734</strong></div>
              <div><span>Rabbit</span><strong id="rabbit-accession">loading...</strong></div>
              <div><span>First Xa site</span><strong>314/315</strong></div>
              <div><span>Gap</span><strong>299-303</strong></div>
            </div>
          </header>

          <nav class="topnav">
            <a href="#viewer">3D viewer</a>
            <a href="#mechanism">Mechanism</a>
            <a href="#alignment">Alignment</a>
            <a href="#gallery">Figures</a>
            <a href="#conclusion">Conclusion</a>
          </nav>

          <main class="layout">
            <aside class="sidebar">
              <section class="card facts">
                <h2>What to notice</h2>
                <ul id="fact-list"></ul>
              </section>
              <section class="card quote">
                <p>“The rabbit gap sits where the first cut happens. That is why the species difference matters.”</p>
              </section>
              <section class="card stats">
                <h2>Key metrics</h2>
                <dl id="metrics-dl"></dl>
              </section>
            </aside>

            <section class="content">
              <section class="hero-grid">
                <article class="card intro">
                  <h2>The short version</h2>
                  <p>Rabbit prothrombin looks close on paper, but the first Xa neighborhood is where the story breaks. The sequence gap is small, yet it lands in the part of the protein that matters most for F1.2 generation and thrombin research.</p>
                  <p>The site below lets you rotate the AlphaFold rabbit model, switch views, and jump between the first and second cleavage regions.</p>
                </article>
                <article class="card pulse">
                  <h2>Why the paper mattered</h2>
                  <p>The old rabbit experiment asked a simple question: can rabbit F1.2 stand in for human F1.2? The answer was no, and the 3D model here shows a plausible reason why.</p>
                </article>
              </section>

              <section id="viewer" class="section">
                <div class="section-head">
                  <div>
                    <h2>Rotate the protein</h2>
                    <p>Drag the model, zoom in, and switch modes to compare the human and rabbit structures around the cleavage site.</p>
                  </div>
                  <div class="chip-row">
                    <span class="chip">Interactive 3D</span>
                    <span class="chip">AlphaFold-derived</span>
                    <span class="chip">First-site focus</span>
                  </div>
                </div>
                <div class="viewer-shell">
                  <div id="viewer-status" class="viewer-status">Loading interactive molecular view...</div>
                  <div id="molecule-viewer" class="viewer-canvas"></div>
                </div>
                <div class="control-row" id="mode-buttons"></div>
              </section>

              <section id="mechanism" class="section grid-two">
                <article class="card panel">
                  <h2>How the cut works</h2>
                  <p>Factor Xa trims prothrombin at two places. The first cut is the key one for F1.2. In the rabbit model, the deletion sits right in that neighborhood, so the local architecture is changed where the action starts.</p>
                  <div class="mechanism-steps" id="mechanism-steps"></div>
                </article>
                <article class="card panel">
                  <h2>Why it matters for thrombin research</h2>
                  <p>The mechanism graphic and the 3D model tell the same story: if the first cut site shifts shape, the assay output can shift too. That means rabbit data can be useful as a clue, but it should not be read as a direct human substitute.</p>
                  <img src="../figures/cleavage_mechanism.png" alt="Cleavage mechanism graphic" class="full-image" />
                </article>
              </section>

              <section id="cut-theory" class="section card">
                <div class="section-head">
                  <div>
                    <h2>What could make human easier to cut?</h2>
                    <p>The cards below translate the 3D overlay into plain language. Click one to focus the viewer on the first cleavage region.</p>
                  </div>
                </div>
                <div id="cut-theory-grid" class="theory-grid"></div>
              </section>

              <section id="alignment" class="section card">
                <div class="section-head">
                  <div>
                    <h2>Sequence alignment around the first cut</h2>
                    <p>The gap is highlighted in magenta. Click a residue to focus the 3D viewer on that spot.</p>
                  </div>
                  <button class="ghost-button" id="focus-gap">Focus gap</button>
                </div>
                <div id="alignment-band" class="alignment-band"></div>
              </section>

              <section class="section grid-two">
                <article class="card">
                  <h2>What the 3D view should make obvious</h2>
                  <ul class="bullet-list" id="why-list"></ul>
                </article>
                <article class="card">
                  <h2>Evidence trail</h2>
                  <p>The figures and metrics below are the same ones used in the written report, but the site lets you move between them like a story rather than a static paper.</p>
                  <div class="image-strip">
                    <img src="../renderings/02_first_xa_closeup.png" alt="First Xa closeup" />
                    <img src="../renderings/03_deletion_flanks.png" alt="Deletion flanks" />
                  </div>
                </article>
              </section>

              <section id="gallery" class="section">
                <div class="section-head">
                  <div>
                    <h2>Figures you can open</h2>
                    <p>Click any panel to enlarge it. The gallery includes the new mechanism illustration and the existing 3D renderings.</p>
                  </div>
                </div>
                <div id="gallery-grid" class="gallery-grid"></div>
              </section>

              <section id="conclusion" class="section card conclusion">
                <h2>Bottom line</h2>
                <p>Rabbit prothrombin is not a direct stand-in for human prothrombin in F1.2 or first-cleavage-site work. The AlphaFold rabbit model makes that difference visible at the exact place the protein gets cut, which is why the original hypothesis holds up.</p>
                <p>Static structure does not prove kinetics, but it can show you where the chemistry is likely to change. Here, the shape difference sits right on top of the biological question.</p>
              </section>
            </section>
          </main>

          <div id="lightbox" class="lightbox" aria-hidden="true">
            <button class="lightbox-close" id="lightbox-close">Close</button>
            <img id="lightbox-image" alt="Expanded figure" />
            <p id="lightbox-caption"></p>
          </div>
        </body>
        </html>
        """
    ).strip()
    write_text(SITE_HTML, html, summary)

    css = textwrap.dedent(
        """
        :root {
          --bg: #f3f0e8;
          --paper: rgba(255,255,255,0.86);
          --ink: #14212b;
          --muted: #546372;
          --accent: #0f4c5c;
          --accent-2: #d62728;
          --border: rgba(20,33,43,0.12);
          --shadow: 0 24px 80px rgba(17, 28, 36, 0.12);
        }

        * { box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body {
          margin: 0;
          color: var(--ink);
          font-family: Inter, "Segoe UI", Helvetica, Arial, sans-serif;
          background:
            radial-gradient(circle at top left, rgba(13,76,92,0.10), transparent 28%),
            radial-gradient(circle at top right, rgba(214,39,40,0.08), transparent 26%),
            linear-gradient(180deg, #fbfaf6 0%, #f2efe7 30%, #ece6da 100%);
        }

        .bg-orb {
          position: fixed;
          width: 30vw;
          aspect-ratio: 1;
          border-radius: 50%;
          filter: blur(60px);
          opacity: 0.35;
          pointer-events: none;
          z-index: 0;
        }
        .bg-orb-a { top: -8vw; left: -10vw; background: #8dd3c7; }
        .bg-orb-b { top: 18vw; right: -12vw; background: #f7c873; }

        .masthead, .topnav, .layout { position: relative; z-index: 1; }
        .masthead {
          max-width: 1480px;
          margin: 0 auto;
          padding: 72px 28px 28px;
        }
        .kicker {
          font-size: .82rem;
          letter-spacing: .24em;
          text-transform: uppercase;
          color: var(--accent);
          font-weight: 800;
          margin-bottom: 12px;
        }
        h1, h2 {
          font-family: Georgia, "Times New Roman", serif;
          letter-spacing: -0.02em;
        }
        .masthead h1 {
          font-size: clamp(3rem, 7vw, 6.3rem);
          line-height: .92;
          margin: 0;
          max-width: 11ch;
        }
        .deck {
          max-width: 66ch;
          font-size: clamp(1.1rem, 1.6vw, 1.3rem);
          line-height: 1.65;
          color: var(--muted);
          margin-top: 18px;
        }
        .masthead-meta {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 16px;
          margin-top: 28px;
        }
        .masthead-meta > div {
          padding: 16px 18px;
          background: var(--paper);
          border: 1px solid var(--border);
          border-radius: 18px;
          box-shadow: var(--shadow);
          backdrop-filter: blur(10px);
        }
        .masthead-meta span { display: block; font-size: .78rem; color: var(--muted); text-transform: uppercase; letter-spacing: .14em; }
        .masthead-meta strong { display: block; margin-top: 5px; font-size: 1.1rem; }

        .topnav {
          max-width: 1480px;
          margin: 0 auto;
          display: flex;
          gap: 14px;
          padding: 0 28px 18px;
          position: sticky;
          top: 0;
          z-index: 20;
          backdrop-filter: blur(18px);
        }
        .topnav a {
          text-decoration: none;
          color: var(--ink);
          background: rgba(255,255,255,0.72);
          border: 1px solid var(--border);
          padding: 10px 16px;
          border-radius: 999px;
          transition: transform .2s ease, background .2s ease;
        }
        .topnav a:hover { transform: translateY(-2px); background: #fff; }

        .layout {
          max-width: 1480px;
          margin: 0 auto;
          padding: 0 28px 56px;
          display: grid;
          grid-template-columns: 340px minmax(0, 1fr);
          gap: 28px;
          align-items: start;
        }
        .sidebar {
          position: sticky;
          top: 84px;
          display: grid;
          gap: 18px;
        }
        .content { display: grid; gap: 28px; }
        .hero-grid, .grid-two {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 18px;
        }
        .section { scroll-margin-top: 88px; }
        .card, .viewer-shell {
          background: var(--paper);
          border: 1px solid var(--border);
          border-radius: 24px;
          box-shadow: var(--shadow);
          backdrop-filter: blur(16px);
        }
        .card { padding: 22px; }
        .card h2, .section h2 { margin: 0 0 8px; font-size: clamp(1.6rem, 2.8vw, 2.2rem); }
        .card p, .section p { color: var(--muted); line-height: 1.7; }
        .section-head {
          display: flex;
          gap: 18px;
          justify-content: space-between;
          align-items: end;
          margin-bottom: 14px;
        }
        .chip-row { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
        .chip {
          padding: 7px 12px;
          border-radius: 999px;
          background: rgba(15,76,92,0.08);
          color: var(--accent);
          font-size: .82rem;
          font-weight: 700;
          letter-spacing: .02em;
        }

        .viewer-shell {
          overflow: hidden;
          padding: 0;
          position: relative;
        }
        .viewer-status {
          position: absolute;
          top: 14px;
          left: 14px;
          z-index: 5;
          background: rgba(255,255,255,0.84);
          border-radius: 999px;
          padding: 8px 12px;
          font-size: .86rem;
          box-shadow: 0 12px 30px rgba(0,0,0,0.08);
        }
        .viewer-canvas {
          width: 100%;
          height: 720px;
        }
        .control-row {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          margin-top: 12px;
        }
        .mode-btn, .ghost-button, .lightbox-close {
          border: 1px solid rgba(20,33,43,.16);
          background: #fff;
          color: var(--ink);
          border-radius: 999px;
          padding: 10px 15px;
          font: inherit;
          cursor: pointer;
          transition: transform .2s ease, box-shadow .2s ease, background .2s ease;
        }
        .mode-btn:hover, .ghost-button:hover, .lightbox-close:hover { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(0,0,0,0.08); }
        .mode-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }

        .mechanism-steps {
          display: grid;
          gap: 10px;
          margin-top: 16px;
        }
        .step {
          padding: 14px 16px;
          border: 1px solid var(--border);
          border-radius: 16px;
          background: rgba(255,255,255,0.78);
          cursor: pointer;
          transition: transform .2s ease, border-color .2s ease;
        }
        .step.active { border-color: var(--accent); transform: translateX(4px); }
        .step strong { display: block; margin-bottom: 4px; }
        .step span { color: var(--muted); font-size: .95rem; }
        .full-image {
          width: 100%;
          display: block;
          margin-top: 16px;
          border-radius: 18px;
          border: 1px solid var(--border);
        }
        .theory-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 14px;
          margin-top: 18px;
        }
        .theory-card {
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 18px;
          background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(247,247,241,.96));
          cursor: pointer;
          transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
        }
        .theory-card:hover { transform: translateY(-2px); box-shadow: 0 16px 34px rgba(0,0,0,.08); }
        .theory-card.active { border-color: var(--accent-2); }
        .theory-card h3 { margin: 0 0 8px; font-size: 1.05rem; }
        .theory-card p { margin: 0; color: var(--muted); line-height: 1.65; }
        .alignment-band {
          display: grid;
          gap: 12px;
          margin-top: 18px;
        }
        .alignment-row {
          display: grid;
          grid-template-columns: 70px 1fr 1fr 1fr;
          gap: 8px;
          align-items: center;
          padding: 10px;
          border-radius: 14px;
          border: 1px solid rgba(20,33,43,.08);
          background: rgba(255,255,255,.74);
          cursor: pointer;
          transition: transform .2s ease, box-shadow .2s ease;
        }
        .alignment-row:hover { transform: translateY(-1px); box-shadow: 0 12px 24px rgba(0,0,0,.06); }
        .alignment-row.active { border-color: var(--accent-2); }
        .pos { font-weight: 800; color: var(--accent); }
        .aa {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 34px;
          height: 34px;
          border-radius: 10px;
          background: rgba(15,76,92,.07);
          font-family: "Courier New", monospace;
        }
        .aa.gap { background: rgba(214,39,40,.12); color: var(--accent-2); font-weight: 800; }
        .aa.focus { outline: 2px solid var(--accent-2); }
        .legend { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; color: var(--muted); font-size: .9rem; }
        .legend span { display: inline-flex; align-items: center; gap: 6px; }
        .dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
        .dot.h { background: #8a8a8a; }
        .dot.r { background: #00a6c8; }
        .dot.g { background: #d100b8; }
        .bullet-list { padding-left: 18px; line-height: 1.7; }
        .image-strip { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }
        .image-strip img, .gallery-card img {
          width: 100%;
          display: block;
          border-radius: 16px;
          border: 1px solid var(--border);
        }
        .gallery-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 16px;
        }
        .gallery-card {
          border: 1px solid var(--border);
          border-radius: 20px;
          background: rgba(255,255,255,0.82);
          padding: 14px;
          cursor: zoom-in;
          transition: transform .2s ease;
        }
        .gallery-card:hover { transform: translateY(-2px); }
        .gallery-card h3 { margin: 0 0 6px; font-size: 1.08rem; }
        .gallery-card p { margin: 8px 0 0; font-size: .95rem; }
        .quote {
          font-family: Georgia, "Times New Roman", serif;
          font-size: 1.15rem;
          font-style: italic;
          line-height: 1.6;
        }
        .stats dl {
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 8px 16px;
          margin: 0;
        }
        .stats dt { color: var(--muted); }
        .stats dd { margin: 0; font-weight: 800; }
        .conclusion p:last-child { margin-bottom: 0; }
        .lightbox {
          position: fixed;
          inset: 0;
          background: rgba(7, 12, 16, 0.86);
          display: none;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          gap: 14px;
          z-index: 50;
          padding: 24px;
        }
        .lightbox.open { display: flex; }
        .lightbox img {
          max-width: min(1200px, 94vw);
          max-height: 78vh;
          border-radius: 20px;
          box-shadow: 0 30px 80px rgba(0,0,0,0.42);
        }
        .lightbox p {
          color: #fff;
          margin: 0;
          max-width: 84ch;
          text-align: center;
        }
        .lightbox-close {
          position: absolute;
          top: 24px;
          right: 24px;
          background: rgba(255,255,255,.95);
        }
        .card, .viewer-shell, .gallery-card, .alignment-row {
          will-change: transform;
        }
        @media (max-width: 1160px) {
          .layout { grid-template-columns: 1fr; }
          .sidebar { position: static; }
        }
        @media (max-width: 860px) {
          .masthead-meta, .hero-grid, .grid-two, .gallery-grid, .image-strip, .theory-grid { grid-template-columns: 1fr; }
          .viewer-canvas { height: 540px; }
          .alignment-row { grid-template-columns: 58px 1fr; }
          .alignment-row .rabbit, .alignment-row .human2 { grid-column: 2; }
          .topnav { overflow-x: auto; }
        }
        """
    ).strip()
    write_text(SITE_CSS, css, summary)

    js = textwrap.dedent(
        """
        const data = window.SITE_DATA;

        const state = {
          viewer: null,
          mode: "overlay",
          models: [],
          controls: {}
        };

        const modes = [
          { id: "overlay", label: "Overlay", focus: "all" },
          { id: "human", label: "Human only", focus: "human" },
          { id: "rabbit", label: "Rabbit only", focus: "rabbit" },
          { id: "first", label: "First Xa site", focus: "first" },
          { id: "second", label: "Second Xa site", focus: "second" },
          { id: "surface", label: "Surface focus", focus: "surface" },
        ];

        const alignmentFocusMap = {
          "299": "first",
          "300": "first",
          "301": "first",
          "302": "first",
          "303": "first",
          "314": "first",
          "315": "first",
          "363": "second",
          "364": "second"
        };

        function q(id) { return document.getElementById(id); }

        function setStatus(text) {
          q("viewer-status").textContent = text;
        }

        function esc(text) {
          return String(text)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;");
        }

        function renderMetrics() {
          const pairs = [
            ["Whole-model RMSD", `${data.metrics.whole_model_ca_rmsd_angstrom.toFixed(2)} Å`],
            ["First Xa window", `${data.metrics.first_xa_window_300_330_ca_rmsd_angstrom.toFixed(2)} Å`],
            ["Second Xa window", `${data.metrics.second_xa_window_350_375_ca_rmsd_angstrom.toFixed(2)} Å`],
            ["Gap length", `${data.manifest.human_deletion_positions.length} residues`],
          ];
          q("metrics-dl").innerHTML = pairs.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("");
        }

        function renderFacts() {
          const facts = [
            `Rabbit accession: ${data.rabbit_accession}`,
            `Rabbit model type: ${data.manifest.rabbit_model_source_type}`,
            `First Xa site: human precursor 314/315`,
            `Rabbit gap: human 299-303`,
            `Model status: ${data.metrics.status}`,
          ];
          q("fact-list").innerHTML = facts.map(item => `<li>${esc(item)}</li>`).join("");
          q("rabbit-accession").textContent = data.rabbit_accession;
          q("why-list").innerHTML = data.why_it_matters.map(item => `<li>${esc(item)}</li>`).join("");
        }

        function modeButton(label, id) {
          const btn = document.createElement("button");
          btn.className = "mode-btn";
          btn.textContent = label;
          btn.dataset.mode = id;
          btn.addEventListener("click", () => setMode(id));
          return btn;
        }

        function renderModeButtons() {
          const row = q("mode-buttons");
          row.innerHTML = "";
          modes.forEach(mode => row.appendChild(modeButton(mode.label, mode.id)));
        }

        function setActiveButtons(mode) {
          document.querySelectorAll(".mode-btn").forEach(btn => {
            btn.classList.toggle("active", btn.dataset.mode === mode);
          });
        }

        function residueRange(sel) {
          if (typeof sel === "number") return `${sel}`;
          return sel;
        }

        function clearViewer() {
          if (!state.viewer) return;
          state.viewer.removeAllSurfaces?.();
          state.viewer.removeAllLabels?.();
          state.viewer.setStyle({}, {});
        }

        function labelRange(model, text, color, resi) {
          try {
            const atoms = state.viewer.getModel(model).selectedAtoms({chain: "A", resi: residueRange(resi)});
            if (atoms.length) {
              const atom = atoms[Math.floor(atoms.length / 2)];
              state.viewer.addLabel(text, {
                position: {x: atom.x, y: atom.y, z: atom.z},
                backgroundColor: color,
                fontColor: "white",
                inFront: true,
                padding: 3,
                borderRadius: 4
              });
            }
          } catch (e) {}
        }

        function styleCommon() {
          state.viewer.addStyle({model: 0}, {cartoon: {color: "#7f7f7f", opacity: 0.92}});
          state.viewer.addStyle({model: 1}, {cartoon: {color: "#00a6c8", opacity: 0.72}});
        }

        function styleFocus(range) {
          if (range === "all") {
            state.viewer.zoomTo();
            styleCommon();
            return;
          }
          if (range === "human") {
            state.viewer.addStyle({model: 0}, {cartoon: {color: "#7f7f7f", opacity: 0.96}});
            state.viewer.addStyle({model: 1}, {cartoon: {color: "#00a6c8", opacity: 0.08}});
            state.viewer.zoomTo({model: 0});
            return;
          }
          if (range === "rabbit") {
            state.viewer.addStyle({model: 0}, {cartoon: {color: "#7f7f7f", opacity: 0.08}});
            state.viewer.addStyle({model: 1}, {cartoon: {color: "#00a6c8", opacity: 0.96}});
            state.viewer.zoomTo({model: 1});
            return;
          }
          if (range === "first") {
            styleCommon();
            state.viewer.addStyle({model: 0, chain: "A", resi: "294-334"}, {stick: {colorscheme: "redCarbon"}});
            state.viewer.addStyle({model: 1, chain: "A", resi: "294-334"}, {stick: {colorscheme: "cyanCarbon"}});
            state.viewer.zoomTo({model: 0, chain: "A", resi: "294-334"});
            labelRange(0, "First Xa site", "#d62728", "314-315");
            labelRange(1, "Rabbit gap zone", "#d100b8", "299-303");
            return;
          }
          if (range === "second") {
            styleCommon();
            state.viewer.addStyle({model: 0, chain: "A", resi: "346-371"}, {stick: {colorscheme: "orangeCarbon"}});
            state.viewer.addStyle({model: 1, chain: "A", resi: "346-371"}, {stick: {colorscheme: "cyanCarbon"}});
            state.viewer.zoomTo({model: 0, chain: "A", resi: "346-371"});
            labelRange(0, "Second Xa site", "#f28e2b", "363-364");
            return;
          }
          if (range === "surface") {
            state.viewer.addStyle({model: 0}, {cartoon: {color: "#7f7f7f"}});
            state.viewer.addStyle({model: 1}, {cartoon: {color: "#00a6c8"}});
            state.viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity: 0.35, color: "#f1efe8"}, {model: 0, chain: "A", resi: "300-330"});
            state.viewer.zoomTo({model: 0, chain: "A", resi: "300-330"});
            return;
          }
        }

        function setMode(mode) {
          if (!state.viewer) return;
          state.mode = mode;
          clearViewer();
          state.viewer.show({model: 0});
          state.viewer.show({model: 1});
          styleFocus(modes.find(m => m.id === mode).focus);
          setActiveButtons(mode);
          state.viewer.render();
          setStatus(`Mode: ${data.mode_titles[mode]}. Drag to rotate and scroll to zoom.`);
          highlightAlignment(mode);
          highlightCutTheory(mode);
        }

        function renderAlignment(containerId, rows) {
          const container = q(containerId);
          container.innerHTML = "";
          const legend = document.createElement("div");
          legend.className = "legend";
          legend.innerHTML = `
            <span><i class="dot h"></i> human</span>
            <span><i class="dot r"></i> rabbit</span>
            <span><i class="dot g"></i> deletion gap</span>
          `;
          container.appendChild(legend);

          rows.forEach(row => {
            const el = document.createElement("div");
            el.className = "alignment-row";
            if (row.gap) el.classList.add("gap");
            if (row.first_site || row.deletion || row.second_site) el.classList.add("active");
            el.dataset.pos = row.human_pos;
            el.dataset.mode = alignmentFocusMap[String(row.human_pos)] || "";
            el.innerHTML = `
              <div class="pos">${row.human_pos ?? ""}</div>
              <div class="human"><span class="aa">${esc(row.human_aa)}</span> human</div>
              <div class="rabbit"><span class="aa ${row.gap ? "gap" : ""}">${esc(row.rabbit_aa)}</span> rabbit</div>
              <div class="human2">${row.first_site ? "first Xa site" : row.second_site ? "second Xa site" : row.gap ? "gap" : row.label || ""}</div>
            `;
            el.addEventListener("click", () => {
              const mode = el.dataset.mode || "first";
              setMode(mode);
              el.scrollIntoView({behavior: "smooth", block: "nearest", inline: "center"});
            });
            container.appendChild(el);
          });
        }

        function highlightAlignment(mode) {
          document.querySelectorAll(".alignment-row").forEach(row => {
            row.classList.toggle("focus", row.dataset.mode === mode);
          });
        }

        function renderMechanismSteps() {
          const steps = [
            {
              title: "1. Factor Xa arrives",
              text: "The enzyme finds the right region on prothrombin and starts the cleavage process.",
              mode: "human"
            },
            {
              title: "2. First cut opens F1.2",
              text: "This is the key step. If the first site is changed, the signal the assay sees can change too.",
              mode: "first"
            },
            {
              title: "3. Thrombin-side product remains",
              text: "After the cut, the remaining part of prothrombin continues toward thrombin formation.",
              mode: "second"
            }
          ];
          const host = q("mechanism-steps");
          host.innerHTML = "";
          steps.forEach((step, idx) => {
            const card = document.createElement("button");
            card.className = "step";
            card.innerHTML = `<strong>${esc(step.title)}</strong><span>${esc(step.text)}</span>`;
            card.addEventListener("click", () => setMode(step.mode));
            if (idx === 1) card.classList.add("active");
            host.appendChild(card);
          });
        }

        function renderCutTheory() {
          const host = q("cut-theory-grid");
          if (!host) return;
          host.innerHTML = "";
          data.cut_theory.forEach((item, idx) => {
            const card = document.createElement("article");
            card.className = "theory-card";
            card.dataset.mode = item.mode;
            card.innerHTML = `
              <h3>${esc(item.title)}</h3>
              <p>${esc(item.text)}</p>
            `;
            card.addEventListener("click", () => setMode(item.mode));
            if (idx === 0) card.classList.add("active");
            host.appendChild(card);
          });
        }

        function highlightCutTheory(mode) {
          document.querySelectorAll(".theory-card").forEach(card => {
            card.classList.toggle("active", card.dataset.mode === mode);
          });
        }

        function bindLightbox() {
          const lb = q("lightbox");
          const img = q("lightbox-image");
          const cap = q("lightbox-caption");
          q("lightbox-close").addEventListener("click", () => lb.classList.remove("open"));
          lb.addEventListener("click", e => {
            if (e.target === lb) lb.classList.remove("open");
          });
          document.querySelectorAll(".gallery-card").forEach(card => {
            card.addEventListener("click", () => {
              img.src = card.dataset.path;
              cap.textContent = card.dataset.caption;
              lb.classList.add("open");
            });
          });
        }

        function renderGallery() {
          const host = q("gallery-grid");
          host.innerHTML = "";
          data.gallery.forEach(item => {
            const card = document.createElement("article");
            card.className = "gallery-card";
            card.dataset.path = item.path;
            card.dataset.caption = item.caption;
            card.innerHTML = `
              <h3>${esc(item.title)}</h3>
              <img src="${item.path}" alt="${esc(item.title)}" />
              <p>${esc(item.caption)}</p>
            `;
            host.appendChild(card);
          });
        }

        function focusGap() {
          setMode("first");
          const rows = document.querySelectorAll(".alignment-row");
          const target = [...rows].find(row => row.dataset.pos === "299");
          if (target) target.scrollIntoView({behavior: "smooth", block: "center"});
        }

        async function initViewer() {
          const host = q("molecule-viewer");
          if (!window.$3Dmol) {
            host.innerHTML = `
              <div class="card" style="margin:24px; background:rgba(255,255,255,0.92);">
                <h2>Interactive 3D viewer unavailable</h2>
                <p>The page still works as a reading experience, but the WebGL viewer could not load. Open this page from a local server with internet access so the 3D library can load.</p>
              </div>
            `;
            setStatus("3D viewer unavailable; use the figure gallery and alignment below.");
            return;
          }

          const [humanText, rabbitText] = await Promise.all([
            fetch(data.human_structure).then(r => r.text()),
            fetch(data.rabbit_structure).then(r => r.text()),
          ]);

          state.viewer = $3Dmol.createViewer(host, {backgroundColor: "#ffffff"});
          state.viewer.addModel(humanText, "pdb");
          state.viewer.addModel(rabbitText, "pdb");
          setMode("overlay");
          state.viewer.zoomTo();
          state.viewer.render();
          setStatus("Mode: Overlay. Drag the protein and explore the first cleavage site.");
        }

        function initScrollProgress() {
          const bar = document.createElement("div");
          bar.style.position = "fixed";
          bar.style.top = "0";
          bar.style.left = "0";
          bar.style.height = "4px";
          bar.style.width = "100%";
          bar.style.zIndex = "99";
          bar.style.background = "linear-gradient(90deg, var(--accent), #f7c873)";
          bar.style.transformOrigin = "0 0";
          bar.style.transform = "scaleX(0)";
          document.body.appendChild(bar);
          window.addEventListener("scroll", () => {
            const max = document.documentElement.scrollHeight - window.innerHeight;
            const pct = max > 0 ? window.scrollY / max : 0;
            bar.style.transform = `scaleX(${Math.min(1, Math.max(0, pct))})`;
          });
        }

        document.addEventListener("DOMContentLoaded", async () => {
          renderMetrics();
          renderFacts();
          renderModeButtons();
          renderCutTheory();
          renderMechanismSteps();
          renderGallery();
          renderAlignment("alignment-band", data.alignment_first);
          initScrollProgress();
          q("focus-gap").addEventListener("click", focusGap);
          bindLightbox();
          await initViewer();
        });
        """
    ).strip()
    write_text(SITE_JS, js, summary)


def main() -> None:
    summary = load_summary()
    site_data = build_site_data(summary)
    write_site_files(site_data, summary)
    add_generated(summary, SITE_DATA_JS)
    add_generated(summary, SITE_HTML)
    add_generated(summary, SITE_CSS)
    add_generated(summary, SITE_JS)
    save_summary(summary)
    print(f"Wrote {SITE_HTML}")


if __name__ == "__main__":
    main()
