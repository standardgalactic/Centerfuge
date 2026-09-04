"use strict";

const state = { data: null, query: "", status: "all", framework: "all" };
const $ = (selector, root = document) => root.querySelector(selector);
const escapeText = value => value == null ? "—" : typeof value === "string" ? value : JSON.stringify(value);

function addDefinition(list, key, value) {
  const row = document.createElement("div");
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = key.replaceAll("_", " ");
  description.textContent = escapeText(value);
  row.append(term, description);
  list.append(row);
}

function renderSummary(data) {
  const values = [
    [data.totals.scenes, "Experiments"],
    [data.totals.pass, "Passing"],
    [data.totals.fail + data.totals.error, "Attention"],
    [`${data.totals.checks_passed}/${data.totals.checks}`, "Checks passed"],
    [data.totals.missing_images, "Missing renders"],
  ];
  const summary = $("#summary");
  summary.replaceChildren(...values.map(([value, label]) => {
    const node = document.createElement("div");
    node.className = "metric";
    node.innerHTML = `<span class="metric-value"></span><span class="metric-label"></span>`;
    $(".metric-value", node).textContent = value;
    $(".metric-label", node).textContent = label;
    return node;
  }));
  const overall = data.totals.scenes > 0 && data.totals.fail === 0 && data.totals.error === 0 ? "pass" : "fail";
  const badge = $("#suiteState");
  badge.className = `suite-state ${overall}`;
  badge.textContent = data.totals.scenes ? `Suite ${overall}` : "No data";
}

function checkNode(check) {
  const node = document.createElement("div");
  node.className = `check ${check.passed ? "pass" : "fail"}`;
  const icon = document.createElement("span");
  icon.className = "check-icon";
  icon.textContent = check.passed ? "✓" : "×";
  const name = document.createElement("span");
  name.className = "check-name";
  name.textContent = check.name;
  const expected = document.createElement("span");
  expected.className = "datum";
  expected.innerHTML = "<b>Expected</b>";
  expected.append(document.createTextNode(escapeText(check.expected)));
  const observed = document.createElement("span");
  observed.className = "datum";
  observed.innerHTML = "<b>Observed</b>";
  observed.append(document.createTextNode(escapeText(check.observed)));
  node.append(icon, name, expected, observed);
  return node;
}

function renderCard(scene) {
  const card = $("#experimentTemplate").content.firstElementChild.cloneNode(true);
  card.dataset.status = scene.status;
  card.dataset.search = [scene.scene_id, scene.framework, scene.primitive, scene.generator,
    ...scene.checks.map(item => item.name)].join(" ").toLowerCase();
  $(".scene-name", card).textContent = scene.scene_id.replaceAll("_", " ");
  $(".scene-meta", card).textContent = `${scene.framework} / ${scene.primitive}`;
  const passed = scene.checks.filter(item => item.passed).length;
  $(".check-ratio", card).textContent = `${passed}/${scene.checks.length} checks`;
  const heading = $(".card-heading", card);
  const body = $(".card-body", card);
  heading.addEventListener("click", () => {
    const open = heading.getAttribute("aria-expanded") === "true";
    heading.setAttribute("aria-expanded", String(!open));
    body.hidden = open;
  });

  const renderColumn = $(".render-column", card);
  if (scene.images.length) {
    scene.images.forEach(image => {
      const figure = document.createElement("figure");
      figure.className = "render-figure";
      const img = document.createElement("img");
      img.src = image.src;
      img.alt = `${scene.scene_id} render: ${image.label}`;
      img.loading = "lazy";
      const caption = document.createElement("figcaption");
      caption.textContent = image.label;
      figure.append(img, caption);
      renderColumn.append(figure);
    });
  } else {
    const empty = document.createElement("div");
    empty.className = "no-render";
    empty.textContent = scene.missing_images.length ? "Referenced render is missing" : "No image output declared";
    renderColumn.append(empty);
  }

  const warning = $(".integrity-warning", card);
  const warnings = [];
  if (!scene.status_consistent) warnings.push(`Reported status ${scene.status} disagrees with computed status ${scene.computed_status}.`);
  if (scene.missing_images.length) warnings.push(`Missing: ${scene.missing_images.join(", ")}`);
  if (scene.load_error) warnings.push(`Sidecar error: ${scene.load_error}`);
  if (warnings.length) { warning.hidden = false; warning.textContent = warnings.join(" "); }
  const checks = $(".checks", card);
  checks.replaceChildren(...scene.checks.map(checkNode));
  if (!scene.checks.length) checks.textContent = "No checks were recorded.";
  Object.entries(scene.parameters).forEach(([key, value]) => addDefinition($(".parameters", card), key, value));
  Object.entries(scene.evidence).forEach(([key, value]) => addDefinition($(".evidence", card), key, value));
  const metadata = { generator: scene.generator, sidecar: scene.source_sidecar, status: scene.status, ...scene.render };
  Object.entries(metadata).forEach(([key, value]) => addDefinition($(".metadata", card), key, value));
  return card;
}

function applyFilters() {
  const cards = [...document.querySelectorAll(".experiment-card")];
  let visible = 0;
  cards.forEach(card => {
    const searchMatch = !state.query || card.dataset.search.includes(state.query);
    const statusMatch = state.status === "all" || card.dataset.status === state.status;
    const scene = state.data.scenes.find(item => item.scene_id.replaceAll("_", " ") === $(".scene-name", card).textContent);
    const frameworkMatch = state.framework === "all" || scene.framework === state.framework;
    card.hidden = !(searchMatch && statusMatch && frameworkMatch);
    if (!card.hidden) visible += 1;
  });
  $("#resultCount").textContent = `${visible} experiment${visible === 1 ? "" : "s"}`;
}

async function init() {
  try {
    const response = await fetch("data.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`data.json returned ${response.status}`);
    state.data = await response.json();
    renderSummary(state.data);
    const framework = $("#frameworkFilter");
    state.data.frameworks.forEach(value => {
      const option = document.createElement("option"); option.value = option.textContent = value; framework.append(option);
    });
    $("#experiments").replaceChildren(...state.data.scenes.map(renderCard));
    $("#emptyState").hidden = state.data.scenes.length > 0;
    $("#generatedAt").textContent = `Built ${new Date(state.data.generated_at).toLocaleString()}`;
    applyFilters();
  } catch (error) {
    $("#suiteState").className = "suite-state error";
    $("#suiteState").textContent = "Ledger unavailable";
    $("#emptyState").hidden = false;
    $("#emptyState h2").textContent = "Dashboard data could not be loaded.";
    $("#emptyState p:last-child").textContent = `${error.message} Serve the dist directory over HTTP after running build_dashboard.py.`;
  }
}

$("#search").addEventListener("input", event => { state.query = event.target.value.trim().toLowerCase(); applyFilters(); });
$("#statusFilter").addEventListener("change", event => { state.status = event.target.value; applyFilters(); });
$("#frameworkFilter").addEventListener("change", event => { state.framework = event.target.value; applyFilters(); });
$("#expandAll").addEventListener("click", () => {
  document.querySelectorAll(".experiment-card:not([hidden]) .card-heading").forEach(button => {
    button.setAttribute("aria-expanded", "true");
    $(".card-body", button.parentElement).hidden = false;
  });
});
init();

