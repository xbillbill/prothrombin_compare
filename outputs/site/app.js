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