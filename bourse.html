<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bourse Analyse Long Terme</title>
<style>
  :root {
    --bg: #f4f6fa;
    --card: #ffffff;
    --primary: #2563eb;
    --green: #16a34a;
    --red: #dc2626;
    --orange: #f59e0b;
    --text: #1e293b;
    --muted: #64748b;
    --border: #e2e8f0;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }
  header {
    background: var(--primary);
    color: #fff;
    padding: 20px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
  }
  header h1 { font-size: 1.3rem; }
  header small { opacity: .85; }
  .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
  .tabs { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
  .tab {
    padding: 10px 18px; border: none; border-radius: 8px;
    background: var(--card); color: var(--text); cursor: pointer;
    font-weight: 600; border: 1px solid var(--border);
  }
  .tab.active { background: var(--primary); color: #fff; border-color: var(--primary); }
  .section { display: none; }
  .section.active { display: block; }
  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px; margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
  }
  .card h2 { font-size: 1.1rem; margin-bottom: 12px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
  .stock-card { cursor: pointer; transition: transform .15s; }
  .stock-card:hover { transform: translateY(-2px); }
  .ticker { font-weight: 700; font-size: 1.05rem; }
  .price { font-size: 1.5rem; font-weight: 700; margin: 6px 0; }
  .change.up { color: var(--green); font-weight: 600; }
  .change.down { color: var(--red); font-weight: 600; }
  .badge {
    display: inline-block; padding: 4px 10px; border-radius: 999px;
    font-size: .8rem; font-weight: 600; color: #fff;
  }
  .score-bar { height: 10px; background: var(--border); border-radius: 999px; overflow: hidden; margin-top: 8px; }
  .score-fill { height: 100%; border-radius: 999px; transition: width .4s; }
  .btn {
    background: var(--primary); color: #fff; border: none; padding: 10px 16px;
    border-radius: 8px; cursor: pointer; font-weight: 600;
  }
  .btn:hover { opacity: .9; }
  .btn-outline { background: #fff; color: var(--primary); border: 1px solid var(--primary); }
  input, select {
    padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px;
    font-size: .95rem; width: 100%;
  }
  label { font-size: .85rem; color: var(--muted); display: block; margin-bottom: 4px; }
  .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 14px; }
  .news-item { padding: 12px 0; border-bottom: 1px solid var(--border); }
  .news-item:last-child { border-bottom: none; }
  .news-item a { color: var(--primary); text-decoration: none; font-weight: 600; }
  .news-item small { color: var(--muted); display: block; margin-top: 4px; }
  .alert { padding: 12px 14px; border-radius: 8px; margin-bottom: 10px; font-size: .9rem; }
  .alert.warn { background: #fef3c7; color: #92400e; }
  .alert.ok { background: #dcfce7; color: #166534; }
  .alert.danger { background: #fee2e2; color: #991b1b; }
  .disclaimer { font-size: .8rem; color: var(--muted); margin-top: 20px; text-align: center; }
  table { width: 100%; border-collapse: collapse; font-size: .9rem; }
  th, td { text-align: left; padding: 10px; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 600; }
  .status { font-size: .8rem; opacity: .85; }
  .demo-banner {
    background: #fef3c7; color: #92400e; padding: 8px 14px; border-radius: 8px;
    font-size: .85rem; margin-bottom: 16px; display: none;
  }
  canvas { width: 100%; max-height: 260px; }
  @media (max-width: 600px) {
    .container { padding: 14px; }
    .price { font-size: 1.3rem; }
  }
</style>
</head>
<body>

<header>
  <div>
    <h1>📈 Bourse Analyse Long Terme</h1>
    <small>Qualité, valorisation, risques et simulation</small>
  </div>
  <div class="status" id="lastUpdate">Mise à jour : --</div>
</header>

<div class="container">

  <div class="demo-banner" id="demoBanner">
    ⚠️ Données de démonstration : l'API en direct n'a pas répondu. Les cours affichés sont indicatifs.
  </div>

  <div class="tabs">
    <button class="tab active" data-tab="dashboard">Tableau de bord</button>
    <button class="tab" data-tab="analysis">Analyse</button>
    <button class="tab" data-tab="news">Actualités</button>
    <button class="tab" data-tab="simulator">Simulateur</button>
    <button class="tab" data-tab="portfolio">Portefeuille</button>
  </div>

  <!-- TABLEAU DE BORD -->
  <div class="section active" id="dashboard">
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:12px">
        <h2>Liste de surveillance</h2>
        <div style="display:flex;gap:8px">
          <input id="newTicker" placeholder="Ticker (ex: AMZN)" style="width:200px">
          <button class="btn" onclick="addTicker()">Ajouter</button>
          <button class="btn btn-outline" onclick="refreshAll()">Actualiser</button>
        </div>
      </div>
      <div class="grid" id="stockGrid"></div>
    </div>
  </div>

  <!-- ANALYSE -->
  <div class="section" id="analysis">
    <div class="card">
      <h2 id="analysisTitle">Sélectionnez une entreprise dans le tableau de bord</h2>
      <div id="analysisContent"></div>
    </div>
  </div>

  <!-- ACTUALITÉS -->
  <div class="section" id="news">
    <div class="card">
      <h2>Actualités récentes</h2>
      <div id="newsList"></div>
    </div>
  </div>

  <!-- SIMULATEUR -->
  <div class="section" id="simulator">
    <div class="card">
      <h2>Simulateur de rentabilité</h2>
      <div class="form-row">
        <div><label>Versement mensuel (€)</label><input type="number" id="monthly" value="100"></div>
        <div><label>Rendement annuel attendu (%)</label><input type="number" id="rate" value="7"></div>
        <div><label>Durée (années)</label><input type="number" id="years" value="10"></div>
        <div><label>Capital initial (€)</label><input type="number" id="initial" value="0"></div>
      </div>
      <button class="btn" onclick="runSimulation()">Calculer</button>
      <div id="simResult" style="margin-top:20px"></div>
      <canvas id="simChart"></canvas>
      <p class="disclaimer">Projection théorique : les rendements passés ne garantissent pas les rendements futurs.</p>
    </div>
  </div>

  <!-- PORTEFEUILLE -->
  <div class="section" id="portfolio">
    <div class="card">
      <h2>Mon portefeuille et alertes</h2>
      <div id="portfolioContent"></div>
    </div>
  </div>

  <p class="disclaimer">Outil pédagogique. Ce n'est pas un conseil en investissement. Investir comporte un risque de perte en capital.</p>
</div>

<script>
// ============ DONNÉES ============
const DEFAULT_TICKERS = ["AMZN", "GOOGL", "MSFT", "NVDA", "MC.PA", "ASML"];

// Données de démonstration (utilisées si l'API échoue)
const DEMO = {
  "AMZN":  { name:"Amazon", price:249.67, changePct:1.2, pe:38, pegRatio:1.6, roe:22, debtEq:0.6, growth:12, score:78, sector:"Technologie / Cloud" },
  "GOOGL": { name:"Alphabet", price:172.40, changePct:-0.4, pe:24, pegRatio:1.2, roe:30, debtEq:0.1, growth:14, score:82, sector:"Technologie / IA" },
  "MSFT":  { name:"Microsoft", price:415.10, changePct:0.6, pe:33, pegRatio:2.0, roe:38, debtEq:0.3, growth:15, score:85, sector:"Logiciels / Cloud" },
  "NVDA":  { name:"Nvidia", price:122.80, changePct:2.3, pe:52, pegRatio:1.3, roe:90, debtEq:0.4, growth:60, score:74, sector:"Semi-conducteurs" },
  "MC.PA": { name:"LVMH", price:620.00, changePct:-1.1, pe:22, pegRatio:1.8, roe:25, debtEq:0.4, growth:8, score:76, sector:"Luxe" },
  "ASML":  { name:"ASML", price:720.50, changePct:0.9, pe:35, pegRatio:1.5, roe:50, debtEq:0.2, growth:13, score:80, sector:"Équipements IA" }
};

const DEMO_NEWS = [
  { title:"Amazon : croissance d'AWS de 39 % au T3", src:"Yahoo Finance", url:"https://finance.yahoo.com/quote/AMZN/" },
  { title:"Les valeurs IA restent sous surveillance des investisseurs", src:"Google Actualités", url:"https://news.google.com/search?q=intelligence+artificielle+bourse" },
  { title:"Politique commerciale et semi-conducteurs : les tensions s'intensifient", src:"Google Actualités", url:"https://news.google.com/search?q=semi-conducteurs+politique" }
];

let tickers = JSON.parse(localStorage.getItem("tickers")) || DEFAULT_TICKERS;
let portfolio = JSON.parse(localStorage.getItem("portfolio")) || [];
let liveData = {};
let demoMode = false;
let simChart = null;

// ============ NAVIGATION ============
document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

// ============ DONNÉES EN DIRECT ============
async function fetchQuote(symbol) {
  // Proxy public Yahoo Finance (peut être indisponible)
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?range=1d&interval=1d`;
  const proxy = `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`;
  const res = await fetch(proxy);
  if (!res.ok) throw new Error("HTTP " + res.status);
  const json = await res.json();
  const meta = json.chart.result[0].meta;
  const price = meta.regularMarketPrice;
  const prev = meta.chartPreviousClose;
  return { price, changePct: ((price - prev) / prev) * 100 };
}

async function refreshAll() {
  demoMode = false;
  let failures = 0;
  for (const t of tickers) {
    try {
      const q = await fetchQuote(t);
      liveData[t] = { ...(DEMO[t] || {}), ...q };
    } catch (e) {
      failures++;
      liveData[t] = DEMO[t] || { price: 0, changePct: 0, score: 50 };
    }
  }
  if (failures === tickers.length) demoMode = true;
  document.getElementById("demoBanner").style.display = demoMode ? "block" : "none";
  document.getElementById("lastUpdate").textContent =
    "Mise à jour : " + new Date().toLocaleTimeString("fr-FR");
  renderDashboard();
  renderPortfolio();
}

// ============ TABLEAU DE BORD ============
function scoreColor(s) {
  if (s >= 75) return "var(--green)";
  if (s >= 55) return "var(--orange)";
  return "var(--red)";
}

function renderDashboard() {
  const grid = document.getElementById("stockGrid");
  grid.innerHTML = "";
  tickers.forEach(t => {
    const d = liveData[t] || DEMO[t] || { price: 0, changePct: 0, score: 50, name: t };
    const up = d.changePct >= 0;
    const score = d.score ?? 50;
    const card = document.createElement("div");
    card.className = "card stock-card";
    card.onclick = () => showAnalysis(t);
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="ticker">${t}</span>
        <span class="badge" style="background:${scoreColor(score)}">Score ${score}</span>
      </div>
      <div style="color:var(--muted);font-size:.9rem">${d.name || t}</div>
      <div class="price">${d.price ? d.price.toFixed(2) : "--"}</div>
      <div class="change ${up ? "up" : "down"}">${up ? "▲" : "▼"} ${d.changePct.toFixed(2)} %</div>
      <div class="score-bar"><div class="score-fill" style="width:${score}%;background:${scoreColor(score)}"></div></div>
    `;
    grid.appendChild(card);
  });
}

function addTicker() {
  const input = document.getElementById("newTicker");
  const t = input.value.trim().toUpperCase();
  if (!t || tickers.includes(t)) return;
  tickers.push(t);
  localStorage.setItem("tickers", JSON.stringify(tickers));
  input.value = "";
  refreshAll();
}

// ============ ANALYSE ============
function showAnalysis(t) {
  document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  document.querySelector('[data-tab="analysis"]').classList.add("active");
  document.getElementById("analysis").classList.add("active");

  const d = liveData[t] || DEMO[t] || {};
  document.getElementById("analysisTitle").textContent = `${d.name || t} (${t})`;

  const checks = [
    { label:"Rentabilité (ROE)", ok: d.roe >= 15, value: (d.roe ?? "--") + " %" },
    { label:"Endettement faible", ok: d.debtEq <= 0.8, value: d.debtEq ?? "--" },
    { label:"Croissance", ok: d.growth >= 8, value: (d.growth ?? "--") + " %" },
    { label:"Valorisation raisonnable (PEG < 1,5)", ok: d.pegRatio <= 1.5, value: d.pegRatio ?? "--" }
  ];

  const rows = checks.map(c => `
    <tr>
      <td>${c.label}</td>
      <td>${c.value}</td>
      <td><span class="badge" style="background:${c.ok ? "var(--green)" : "var(--red)"}">${c.ok ? "OK" : "Vigilance"}</span></td>
    </tr>`).join("");

  const score = d.score ?? 50;
  document.getElementById("analysisContent").innerHTML = `
    <p style="margin-bottom:12px"><strong>Secteur :</strong> ${d.sector || "--"}</p>
    <p style="margin-bottom:12px"><strong>Score de qualité :</strong>
      <span class="badge" style="background:${scoreColor(score)}">${score} / 100</span></p>
    <div class="score-bar" style="margin-bottom:20px"><div class="score-fill" style="width:${score}%;background:${scoreColor(score)}"></div></div>
    <table>
      <tr><th>Critère</th><th>Valeur</th><th>Statut</th></tr>
      ${rows}
    </table>
    <div style="margin-top:16px" class="alert ok">
      Lecture : un score élevé et des critères validés suggèrent une entreprise solide. Ce n'est pas une garantie de performance.
    </div>
    <div class="alert warn">
      Risques à surveiller : valorisation (P/E ${d.pe ?? "--"}), dépendance au secteur, actualité réglementaire.
    </div>
  `;
}

// ============ ACTUALITÉS ============
async function loadNews() {
  // Flux Google News RSS via proxy
  const list = document.getElementById("newsList");
  list.innerHTML = "<p>Chargement…</p>";
  try {
    const rss = "https://news.google.com/rss/search?q=bourse+actions&hl=fr&gl=FR&ceid=FR:fr";
    const res = await fetch(`https://api.allorigins.win/raw?url=${encodeURIComponent(rss)}`);
    const xml = new DOMParser().parseFromString(await res.text(), "text/xml");
    const items = [...xml.querySelectorAll("item")].slice(0, 10);
    if (!items.length) throw new Error("vide");
    list.innerHTML = items.map(i => `
      <div class="news-item">
        <a href="${i.querySelector("link").textContent}" target="_blank">${i.querySelector("title").textContent}</a>
        <small>${new Date(i.querySelector("pubDate").textContent).toLocaleString("fr-FR")}</small>
      </div>`).join("");
  } catch (e) {
    list.innerHTML = DEMO_NEWS.map(n => `
      <div class="news-item">
        <a href="${n.url}" target="_blank">${n.title}</a>
        <small>${n.src} (exemple)</small>
      </div>`).join("");
  }
}

// ============ SIMULATEUR ============
function runSimulation() {
  const m = +document.getElementById("monthly").value;
  const r = (+document.getElementById("rate").value) / 100 / 12;
  const y = +document.getElementById("years").value;
  const init = +document.getElementById("initial").value;

  let value = init;
  const labels = [], values = [], invested = [];
  let totalInvested = init;

  for (let year = 1; year <= y; year++) {
    for (let mo = 0; mo < 12; mo++) {
      value = value * (1 + r) + m;
      totalInvested += m;
    }
    labels.push("An " + year);
    values.push(Math.round(value));
    invested.push(Math.round(totalInvested));
  }

  document.getElementById("simResult").innerHTML = `
    <div class="grid">
      <div class="card"><small>Total investi</small><div class="price">${Math.round(totalInvested).toLocaleString("fr-FR")} €</div></div>
      <div class="card"><small>Valeur estimée</small><div class="price" style="color:var(--green)">${Math.round(value).toLocaleString("fr-FR")} €</div></div>
      <div class="card"><small>Gain estimé</small><div class="price">${Math.round(value - totalInvested).toLocaleString("fr-FR")} €</div></div>
    </div>`;

  if (simChart) simChart.destroy();
  simChart = new Chart(document.getElementById("simChart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        { label:"Valeur estimée", data: values, borderColor:"#2563eb", backgroundColor:"rgba(37,99,235,.1)", fill:true, tension:.3 },
        { label:"Montant investi", data: invested, borderColor:"#64748b", borderDash:[5,5], tension:.3 }
      ]
    },
    options: { responsive:true, plugins:{ legend:{ position:"bottom" } } }
  });
}

// ============ PORTEFEUILLE ============
function renderPortfolio() {
  const el = document.getElementById("portfolioContent");
  const alerts = [];

  tickers.forEach(t => {
    const d = liveData[t] || DEMO[t] || {};
    if (d.pegRatio > 2) alerts.push({ type:"danger", msg:`${t} : valorisation élevée (PEG ${d.pegRatio}).` });
    if (d.debtEq > 1) alerts.push({ type:"warn", msg:`${t} : endettement à surveiller (${d.debtEq}).` });
    if (d.changePct <= -3) alerts.push({ type:"warn", msg:`${t} : baisse marquée aujourd'hui (${d.changePct.toFixed(1)} %).` });
  });

  if (!alerts.length) alerts.push({ type:"ok", msg:"Aucune alerte pour le moment." });

  el.innerHTML = `
    <p style="margin-bottom:14px;color:var(--muted)">Alertes basées sur valorisation, endettement et variations du jour.</p>
    ${alerts.map(a => `<div class="alert ${a.type}">${a.msg}</div>`).join("")}
    <p style="margin-top:16px;color:var(--muted);font-size:.85rem">
      Règle de diversification : aucune position ne devrait dépasser 10 % du portefeuille.
    </p>`;
}

// ============ CHARGEMENT ============
document.querySelector('[data-tab="news"]').addEventListener("click", loadNews);
refreshAll();
setInterval(refreshAll, 5 * 60 * 1000); // actualisation automatique toutes les 5 min
</script>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</body>
</html>
