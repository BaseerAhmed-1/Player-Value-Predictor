// ---------------- Config ----------------
const ATTR_CONFIG = {
  age:          { label: "Age",          min: 16, max: 45, default: 25 },
  reactions:    { label: "Reactions",    min: 1,  max: 100, default: 65 },
  composure:    { label: "Composure",    min: 1,  max: 100, default: 65 },
  ball_control: { label: "Ball Control", min: 1,  max: 100, default: 65 },
  dribbling:    { label: "Dribbling",    min: 1,  max: 100, default: 65 },
};
const RADAR_ATTRS = ["reactions", "composure", "ball_control", "dribbling"];
const fmtMoney = (v) => "€" + Math.round(v).toLocaleString();

// ---------------- Tabs ----------------
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

// ---------------- Slider builder ----------------
function buildSliders(containerId, attrs, prefix, onChange) {
  const container = document.getElementById(containerId);
  attrs.forEach(attr => {
    const cfg = ATTR_CONFIG[attr];
    const row = document.createElement("div");
    row.className = "slider-row";
    row.innerHTML = `
      <label>${cfg.label} <span id="${prefix}-${attr}-val">${cfg.default}</span></label>
      <input type="range" id="${prefix}-${attr}" min="${cfg.min}" max="${cfg.max}" value="${cfg.default}">
    `;
    container.appendChild(row);
    const input = row.querySelector("input");
    input.addEventListener("input", () => {
      document.getElementById(`${prefix}-${attr}-val`).textContent = input.value;
      onChange();
    });
  });
}

function readValues(attrs, prefix) {
  const out = {};
  attrs.forEach(attr => out[attr] = Number(document.getElementById(`${prefix}-${attr}`).value));
  return out;
}

// ---------------- Radar chart helper ----------------
function makeRadar(ctx, datasets) {
  return new Chart(ctx, {
    type: "radar",
    data: { labels: RADAR_ATTRS, datasets },
    options: {
      scales: { r: { min: 0, max: 100, ticks: { color: "#7e8fa3", backdropColor: "transparent", stepSize: 25, font: { family: "JetBrains Mono", size: 10 } }, grid: { color: "#223349" }, angleLines: { color: "#223349" }, pointLabels: { color: "#ccc", font: { family: "Oswald", size: 11 } } } },
      plugins: { legend: { labels: { color: "#ccc" } } }
    }
  });
}

// ================= PREDICT TAB =================
const predictAttrs = ["age", "reactions", "composure", "ball_control", "dribbling"];
buildSliders("predict-sliders", predictAttrs, "p", updatePredict);

const predictRadar = makeRadar(document.getElementById("predict-radar"), [
  { label: "Player", data: [65, 65, 65, 65], backgroundColor: "rgba(255,180,0,0.25)", borderColor: "#ffb400" }
]);

async function updatePredict() {
  const vals = readValues(predictAttrs, "p");
  const res = await fetch("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(vals) });
  const data = await res.json();
  document.getElementById("predict-result").textContent = fmtMoney(data.value);
  predictRadar.data.datasets[0].data = RADAR_ATTRS.map(a => vals[a]);
  predictRadar.update();
}
updatePredict();

// ================= COMPARE TAB =================
buildSliders("compareA-sliders", predictAttrs, "a", updateCompare);
buildSliders("compareB-sliders", predictAttrs, "b", updateCompare);

const compareRadar = makeRadar(document.getElementById("compare-radar"), [
  { label: "Player A", data: [60, 60, 60, 60], backgroundColor: "rgba(255,180,0,0.2)", borderColor: "#ffb400" },
  { label: "Player B", data: [75, 75, 75, 75], backgroundColor: "rgba(76,201,240,0.2)", borderColor: "#4cc9f0" }
]);

async function updateCompare() {
  const a = readValues(predictAttrs, "a");
  const b = readValues(predictAttrs, "b");
  const [ra, rb] = await Promise.all([
    fetch("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(a) }).then(r => r.json()),
    fetch("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) }).then(r => r.json()),
  ]);
  document.getElementById("compareA-result").textContent = fmtMoney(ra.value);
  document.getElementById("compareB-result").textContent = fmtMoney(rb.value);
  compareRadar.data.datasets[0].data = RADAR_ATTRS.map(k => a[k]);
  compareRadar.data.datasets[1].data = RADAR_ATTRS.map(k => b[k]);
  compareRadar.update();
}
updateCompare();

// ================= WHAT-IF TAB =================
buildSliders("whatif-sliders", predictAttrs, "w", updateWhatif);
document.getElementById("whatif-attr").addEventListener("change", updateWhatif);

let whatifChart = new Chart(document.getElementById("whatif-chart"), {
  type: "line",
  data: { labels: [], datasets: [{ label: "Predicted Value", data: [], borderColor: "#ffb400", backgroundColor: "rgba(255,180,0,0.15)", fill: true, tension: 0.2 }] },
  options: {
    scales: { x: { ticks: { color: "#888" }, grid: { color: "#222" } }, y: { ticks: { color: "#888" }, grid: { color: "#222" } } },
    plugins: { legend: { labels: { color: "#ccc" } } }
  }
});

async function updateWhatif() {
  const base = readValues(predictAttrs, "w");
  const attr = document.getElementById("whatif-attr").value;
  const res = await fetch("/api/whatif", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ attr, base }) });
  const data = await res.json();
  whatifChart.data.labels = data.map(d => d.x);
  whatifChart.data.datasets[0].data = data.map(d => d.y);
  whatifChart.data.datasets[0].label = `Value vs ${attr}`;
  whatifChart.update();
}
updateWhatif();

// ================= SIMILAR TAB =================
const similarAttrs = ["reactions", "composure", "ball_control", "dribbling"];
buildSliders("similar-sliders", similarAttrs, "s", updateSimilar);

async function updateSimilar() {
  const vals = readValues(similarAttrs, "s");
  const res = await fetch("/api/similar", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(vals) });
  const rows = await res.json();
  const tbody = document.querySelector("#similar-table tbody");
  tbody.innerHTML = "";
  rows.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.player ?? "-"}</td><td>${r.country ?? "-"}</td><td>${fmtMoney(r.value)}</td>`;
    tbody.appendChild(tr);
  });
}
updateSimilar();

// ================= LEADERBOARD TAB =================
async function loadLeaderboard() {
  const res = await fetch("/api/leaderboard");
  const data = await res.json();
  new Chart(document.getElementById("leaderboard-chart"), {
    type: "bar",
    data: {
      labels: data.map(d => d.player),
      datasets: [{ label: "Value", data: data.map(d => d.value), backgroundColor: "#ffb400" }]
    },
    options: {
      indexAxis: "y",
      scales: { x: { ticks: { color: "#888" }, grid: { color: "#222" } }, y: { ticks: { color: "#888" }, grid: { color: "#222" } } },
      plugins: { legend: { display: false } }
    }
  });
}

async function loadAgeTrend() {
  const res = await fetch("/api/age-trend");
  const data = await res.json();
  new Chart(document.getElementById("agetrend-chart"), {
    type: "line",
    data: {
      labels: data.map(d => d.age),
      datasets: [{ label: "Median Value", data: data.map(d => d.value), borderColor: "#ffb400", backgroundColor: "rgba(255,180,0,0.15)", fill: true, tension: 0.2 }]
    },
    options: {
      scales: { x: { ticks: { color: "#888" }, grid: { color: "#222" } }, y: { ticks: { color: "#888" }, grid: { color: "#222" } } },
      plugins: { legend: { labels: { color: "#ccc" } } }
    }
  });
}
loadLeaderboard();
loadAgeTrend();
