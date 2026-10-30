"""
Radar Croissance — Screener d'actions à progression rapide / fluctuante
Lancer avec :  streamlit run app.py
⚠️ Outil d'analyse uniquement, pas un conseil en investissement.
"""
import io
import datetime as dt

import numpy as np
import pandas as pd
import requests
import feedparser
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Radar Croissance", layout="wide", page_icon="🚀")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ----------------------------------------------------------------------------
# UNIVERS D'ACTIONS
# ----------------------------------------------------------------------------
CAC40 = {
    "AI.PA": "Air Liquide", "AIR.PA": "Airbus", "ALO.PA": "Alstom", "MT.AS": "ArcelorMittal",
    "CS.PA": "AXA", "BNP.PA": "BNP Paribas", "EN.PA": "Bouygues", "CAP.PA": "Capgemini",
    "CA.PA": "Carrefour", "ACA.PA": "Crédit Agricole", "BN.PA": "Danone",
    "DSY.PA": "Dassault Systèmes", "EDEN.PA": "Edenred", "ENGI.PA": "Engie",
    "EL.PA": "EssilorLuxottica", "ERF.PA": "Eurofins", "RMS.PA": "Hermès", "KER.PA": "Kering",
    "OR.PA": "L'Oréal", "LR.PA": "Legrand", "MC.PA": "LVMH", "ML.PA": "Michelin",
    "ORA.PA": "Orange", "RI.PA": "Pernod Ricard", "PUB.PA": "Publicis", "RNO.PA": "Renault",
    "SAF.PA": "Safran", "SGO.PA": "Saint-Gobain", "SAN.PA": "Sanofi",
    "SU.PA": "Schneider Electric", "GLE.PA": "Société Générale", "STLAP.PA": "Stellantis",
    "STMPA.PA": "STMicroelectronics", "TEP.PA": "Teleperformance", "HO.PA": "Thales",
    "TTE.PA": "TotalEnergies", "URW.PA": "Unibail-Rodamco", "VIE.PA": "Veolia",
    "DG.PA": "Vinci", "VIV.PA": "Vivendi",
}


@st.cache_data(ttl=86400, show_spinner=False)
def get_universe(name: str) -> dict:
    try:
        if name == "S&P 500":
            html = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                                headers=HEADERS, timeout=20).text
            df = pd.read_html(io.StringIO(html))[0]
            return dict(zip(df["Symbol"].str.replace(".", "-", regex=False), df["Security"]))
        if name == "Nasdaq 100":
            html = requests.get("https://en.wikipedia.org/wiki/Nasdaq-100",
                                headers=HEADERS, timeout=20).text
            for t in pd.read_html(io.StringIO(html)):
                if "Ticker" in t.columns:
                    col = "Company" if "Company" in t.columns else t.columns[0]
                    return dict(zip(t["Ticker"], t[col]))
        if name == "CAC 40":
            return CAC40
    except Exception as e:
        st.error(f"Impossible de charger l'univers {name} : {e}")
    return {}


# ----------------------------------------------------------------------------
# DONNÉES DE MARCHÉ
# ----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_prices(tickers: tuple, period: str = "1y") -> pd.DataFrame:
    return yf.download(list(tickers), period=period, interval="1d", group_by="ticker",
                       auto_adjust=True, threads=True, progress=False)


def extract(data: pd.DataFrame, t: str) -> pd.DataFrame | None:
    try:
        df = data[t] if isinstance(data.columns, pd.MultiIndex) else data
        df = df.dropna(subset=["Close"])
        return df if len(df) else None
    except KeyError:
        return None


def classify(r6, r3, amp, vol):
    if r6 >= 100: return "🚀🚀 Hyper-croissance"
    if r6 >= 40:  return "🚀 Fusée"
    if r6 <= -35: return "📉 Chute libre"
    if amp >= 80 and abs(r6) < 30: return "🎢 Montagnes russes"
    if r3 >= 25:  return "⚡ Accélération récente"
    if vol >= 60: return "🌪️ Très volatile"
    return "➖ Neutre"


@st.cache_data(ttl=3600, show_spinner=False)
def compute_metrics(_data: pd.DataFrame, names: dict, key: str) -> pd.DataFrame:
    rows = []
    for t, name in names.items():
        df = extract(_data, t)
        if df is None or len(df) < 130:
            continue
        c, v = df["Close"], df["Volume"]
        last = c.iloc[-1]
        ret = lambda n: (last / c.iloc[-n - 1] - 1) * 100 if len(c) > n else np.nan
        lr = np.log(c).diff().dropna()
        c6 = c.iloc[-126:]
        r6, r3 = ret(126), ret(63)
        amp = (c6.max() / c6.min() - 1) * 100
        vol = lr.std() * np.sqrt(252) * 100
        rows.append({
            "Ticker": t, "Entreprise": name, "Prix": round(last, 2),
            "Perf 1 mois %": ret(21), "Perf 3 mois %": r3, "Perf 6 mois %": r6,
            "Perf 1 an %": (last / c.iloc[0] - 1) * 100,
            "Volatilité 1 an %": vol,
            "Volatilité 3 mois %": lr.iloc[-63:].std() * np.sqrt(252) * 100,
            "Amplitude 6 mois %": amp,
            "Drawdown max %": ((c / c.cummax()) - 1).min() * 100,
            "Distance plus haut %": (last / c.max() - 1) * 100,
            "Volume x": v.iloc[-20:].mean() / max(v.iloc[-126:].mean(), 1),
            "Profil": classify(r6, r3, amp, vol),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # Score d'explosivité (0-100), basé sur les rangs
    rk = lambda col: out[col].rank(pct=True)
    out["Score 🔥"] = (100 * (0.35 * rk("Perf 6 mois %") + 0.20 * rk("Perf 3 mois %")
                             + 0.15 * rk("Perf 1 an %") + 0.20 * rk("Volatilité 3 mois %")
                             + 0.10 * rk("Volume x"))).round(1)
    return out.sort_values("Score 🔥", ascending=False).reset_index(drop=True)


# ----------------------------------------------------------------------------
# INDICATEURS TECHNIQUES
# ----------------------------------------------------------------------------
def rsi(series: pd.Series, n: int = 14) -> pd.Series:
    d = series.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


# ----------------------------------------------------------------------------
# ACTUALITÉS
# ----------------------------------------------------------------------------
POS = ["beat", "surge", "soar", "record", "upgrade", "growth", "rally", "jump", "strong",
       "hausse", "bond", "record", "croissance", "relève", "dépasse", "envol", "contrat"]
NEG = ["miss", "plunge", "fall", "drop", "downgrade", "lawsuit", "probe", "cut", "weak",
       "baisse", "chute", "plonge", "enquête", "sanction", "abaisse", "perte", "recul"]
POLITICS = {
    "🏛️ Politique monétaire": ["fed", "powell", "bce", "ecb", "lagarde", "taux", "rate", "inflation"],
    "🛃 Commerce / Tarifs": ["tariff", "douane", "trade war", "export", "import", "sanction"],
    "⚖️ Régulation": ["sec", "antitrust", "regulat", "régulat", "ftc", "commission européenne", "amende", "fine"],
    "🗳️ Élections / Gouvernement": ["election", "élection", "trump", "congress", "congrès",
                                     "gouvernement", "white house", "maison blanche", "budget"],
    "🌍 Géopolitique": ["china", "chine", "russia", "russie", "ukraine", "israel", "iran", "taiwan", "war", "guerre"],
}


def sentiment(text: str) -> str:
    t = text.lower()
    s = sum(w in t for w in POS) - sum(w in t for w in NEG)
    return "🟢 Positif" if s > 0 else "🔴 Négatif" if s < 0 else "⚪ Neutre"


def tags(text: str) -> str:
    t = text.lower()
    return ", ".join(k for k, words in POLITICS.items() if any(w in t for w in words))


@st.cache_data(ttl=1800, show_spinner=False)
def ticker_news(t: str) -> pd.DataFrame:
    rows = []
    try:
        for n in yf.Ticker(t).news or []:
            c = n.get("content", n)  # gère ancien et nouveau format yfinance
            title = c.get("title", "")
            date = c.get("pubDate") or c.get("providerPublishTime")
            date = pd.to_datetime(date, unit="s" if isinstance(date, (int, float)) else None, utc=True)
            url = (c.get("canonicalUrl") or {}).get("url") if isinstance(c.get("canonicalUrl"), dict) else c.get("link")
            src = (c.get("provider") or {}).get("displayName", "") if isinstance(c.get("provider"), dict) else c.get("publisher", "")
            rows.append({"Date": date, "Titre": title, "Source": src, "Lien": url})
    except Exception:
        pass
    return pd.DataFrame(rows)


@st.cache_data(ttl=1800, show_spinner=False)
def google_news(query: str, lang: str = "fr", n: int = 25) -> pd.DataFrame:
    gl, ceid = ("FR", "FR:fr") if lang == "fr" else ("US", "US:en")
    url = (f"https://news.google.com/rss/search?q={requests.utils.quote(query)}"
           f"&hl={lang}&gl={gl}&ceid={ceid}")
    feed = feedparser.parse(url)
    rows = [{"Date": pd.to_datetime(e.get("published"), utc=True, errors="coerce"),
             "Titre": e.title, "Source": e.get("source", {}).get("title", ""), "Lien": e.link}
            for e in feed.entries[:n]]
    return pd.DataFrame(rows)


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df["Sentiment"] = df["Titre"].apply(sentiment)
    df["Thème politique"] = df["Titre"].apply(tags)
    return df.sort_values("Date", ascending=False)


# ----------------------------------------------------------------------------
# INTERFACE
# ----------------------------------------------------------------------------
st.title("🚀 Radar Croissance — Entreprises à dynamique explosive")
st.caption(f"Données Yahoo Finance & Google News • Mise à jour : {dt.datetime.now():%d/%m/%Y %H:%M} "
           "• ⚠️ Ceci n'est pas un conseil en investissement.")

with st.sidebar:
    st.header("⚙️ Paramètres")
    univ = st.selectbox("Univers", ["Nasdaq 100", "S&P 500", "CAC 40", "Liste personnalisée"])
    if univ == "Liste personnalisée":
        raw = st.text_area("Tickers (séparés par des virgules)",
                           "PLTR, NVDA, HOOD, APP, RKLB, SMCI, COIN, MSTR, SOFI, RDDT, IONQ, ASTS")
        names = {t.strip().upper(): t.strip().upper() for t in raw.split(",") if t.strip()}
    else:
        names = get_universe(univ)
    st.write(f"**{len(names)}** entreprises dans l'univers")

    st.subheader("Filtres")
    min6 = st.slider("Perf. 6 mois minimum (%)", -100, 300, -100, 5)
    minvol = st.slider("Volatilité minimum (%)", 0, 150, 0, 5)
    profils = st.multiselect("Profils", ["🚀🚀 Hyper-croissance", "🚀 Fusée", "⚡ Accélération récente",
                                         "🎢 Montagnes russes", "🌪️ Très volatile", "📉 Chute libre", "➖ Neutre"])
    if st.button("🔄 Rafraîchir les données"):
        st.cache_data.clear()

if not names:
    st.stop()

with st.spinner(f"Téléchargement de {len(names)} historiques boursiers…"):
    data = get_prices(tuple(names.keys()))
    metrics = compute_metrics(data, names, key=univ + str(len(names)))

if metrics.empty:
    st.warning("Aucune donnée exploitable.")
    st.stop()

f = metrics[(metrics["Perf 6 mois %"] >= min6) & (metrics["Volatilité 1 an %"] >= minvol)]
if profils:
    f = f[f["Profil"].isin(profils)]

tab1, tab2, tab3, tab4 = st.tabs(["🏆 Classement", "📊 Analyse détaillée",
                                  "🌍 Actualité & politique", "🗺️ Carte du marché"])

# ---------------- TAB 1 : CLASSEMENT ----------------
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    best = metrics.iloc[metrics["Perf 6 mois %"].idxmax()]
    worst = metrics.iloc[metrics["Perf 6 mois %"].idxmin()]
    c1.metric("🥇 Meilleure perf 6 mois", best["Ticker"], f"{best['Perf 6 mois %']:.1f}%")
    c2.metric("💀 Pire perf 6 mois", worst["Ticker"], f"{worst['Perf 6 mois %']:.1f}%")
    c3.metric("🚀 Nombre de « fusées »", int(metrics["Profil"].str.contains("🚀").sum()))
    c4.metric("Perf 6 mois médiane", f"{metrics['Perf 6 mois %'].median():.1f}%")

    pct_cols = [c for c in f.columns if "%" in c]
    st.dataframe(
        f.style.format({**{c: "{:+.1f}" for c in pct_cols}, "Volume x": "{:.2f}x", "Prix": "{:.2f}"})
         .background_gradient(subset=["Perf 6 mois %", "Perf 3 mois %", "Perf 1 an %"], cmap="RdYlGn")
         .background_gradient(subset=["Score 🔥"], cmap="Oranges"),
        use_container_width=True, height=600)
    st.download_button("⬇️ Exporter en CSV", f.to_csv(index=False).encode(), "radar_croissance.csv")

    st.subheader("Top 20 — Performance 6 mois")
    top = f.nlargest(20, "Perf 6 mois %")
    st.plotly_chart(px.bar(top, x="Ticker", y="Perf 6 mois %", color="Volatilité 3 mois %",
                           hover_name="Entreprise", color_continuous_scale="Turbo"),
                    use_container_width=True)

# ---------------- TAB 2 : ANALYSE DÉTAILLÉE ----------------
with tab2:
    opts = f["Ticker"].tolist() or metrics["Ticker"].tolist()
    sel = st.selectbox("Choisir une entreprise", opts,
                       format_func=lambda t: f"{t} — {names.get(t, t)}")
    period = st.radio("Période", ["6mo", "1y", "2y"], index=1, horizontal=True)
    df = extract(get_prices((sel,), period), sel)
    row = metrics[metrics["Ticker"] == sel].iloc[0]

    k = st.columns(6)
    for col, lab in zip(k, ["Perf 1 mois %", "Perf 3 mois %", "Perf 6 mois %", "Perf 1 an %",
                            "Volatilité 1 an %", "Drawdown max %"]):
        col.metric(lab.replace(" %", ""), f"{row[lab]:+.1f}%")
    st.info(f"**Profil : {row['Profil']}** • Score d'explosivité : **{row['Score 🔥']}/100** "
            f"• Volume récent : **{row['Volume x']:.2f}x** la moyenne 6 mois")

    if df is not None:
        c = df["Close"]
        sma20, sma50, sma200 = c.rolling(20).mean(), c.rolling(50).mean(), c.rolling(200).mean()
        std = c.rolling(20).std()
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2],
                            vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"],
                                     close=c, name="Cours"), 1, 1)
        for s, n, col in [(sma50, "MM50", "orange"), (sma200, "MM200", "purple")]:
            fig.add_trace(go.Scatter(x=df.index, y=s, name=n, line=dict(color=col, width=1.5)), 1, 1)
        fig.add_trace(go.Scatter(x=df.index, y=sma20 + 2 * std, line=dict(color="gray", width=0.5),
                                 name="Bollinger +", showlegend=False), 1, 1)
        fig.add_trace(go.Scatter(x=df.index, y=sma20 - 2 * std, line=dict(color="gray", width=0.5),
                                 fill="tonexty", fillcolor="rgba(128,128,128,0.1)", name="Bollinger"), 1, 1)
        colors = np.where(c.diff() >= 0, "green", "red")
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, name="Volume"), 2, 1)
        r = rsi(c)
        fig.add_trace(go.Scatter(x=df.index, y=r, name="RSI", line=dict(color="royalblue")), 3, 1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)

        # Actualités placées sur le graphique
        news = enrich(ticker_news(sel))
        if not news.empty:
            news_in = news[news["Date"].notna()]
            for _, n in news_in.iterrows():
                d = n["Date"].tz_convert(None).normalize()
                if df.index[0] <= d <= df.index[-1]:
                    fig.add_vline(x=d, line_dash="dot", line_color="gold", opacity=0.6, row=1, col=1)
        fig.update_layout(height=800, xaxis_rangeslider_visible=False, template="plotly_dark",
                          title=f"{sel} — {names.get(sel, sel)}")
        st.plotly_chart(fig, use_container_width=True)

        # Lecture automatique
        st.subheader("🧠 Lecture technique automatique")
        notes = []
        last = c.iloc[-1]
        if not np.isnan(sma200.iloc[-1]):
            notes.append("✅ Cours **au-dessus** de la MM200 (tendance de fond haussière)"
                         if last > sma200.iloc[-1] else "⚠️ Cours **sous** la MM200 (tendance de fond baissière)")
        if sma50.iloc[-1] > (sma200.iloc[-1] if not np.isnan(sma200.iloc[-1]) else np.inf):
            notes.append("✅ MM50 > MM200 (configuration « golden cross »)")
        notes.append(f"RSI = **{r.iloc[-1]:.0f}** → " + ("🔥 suracheté (risque de correction)" if r.iloc[-1] > 70
                     else "🧊 survendu (rebond possible)" if r.iloc[-1] < 30 else "zone neutre"))
        notes.append(f"Distance au plus haut 1 an : **{row['Distance plus haut %']:.1f}%**")
        for n in notes:
            st.markdown("- " + n)

        st.subheader("📰 Actualités de l'entreprise")
        extra = enrich(google_news(f"{names.get(sel, sel)} action bourse", "fr", 15))
        allnews = pd.concat([news, extra], ignore_index=True) if not news.empty else extra
        if not allnews.empty:
            st.dataframe(allnews, use_container_width=True,
                         column_config={"Lien": st.column_config.LinkColumn("Lien")})

# ---------------- TAB 3 : ACTUALITÉ & POLITIQUE ----------------
with tab3:
    st.subheader("🌍 Décisions politiques et macroéconomiques qui font bouger les marchés")
    topics = {
        "🏛️ Fed / taux US": ("Federal Reserve interest rates decision", "en"),
        "🇪🇺 BCE": ("BCE taux décision Lagarde", "fr"),
        "🛃 Droits de douane": ("tariffs stock market", "en"),
        "⚖️ Régulation / SEC / antitrust": ("SEC antitrust regulation stocks", "en"),
        "🗳️ Politique US": ("White House policy stock market", "en"),
        "🇫🇷 Politique France": ("gouvernement budget bourse CAC 40", "fr"),
        "🌍 Géopolitique": ("geopolitics markets oil China", "en"),
        "🤖 IA & semi-conducteurs": ("AI chips export restrictions", "en"),
    }
    chosen = st.multiselect("Thèmes", list(topics), default=list(topics)[:4])
    custom = st.text_input("…ou recherche libre (ex. « Nvidia Chine export »)")
    frames = []
    for t in chosen:
        q, lang = topics[t]
        d = google_news(q, lang, 15)
        if not d.empty:
            d["Catégorie"] = t
            frames.append(d)
    if custom:
        d = google_news(custom, "fr", 20)
        d["Catégorie"] = "🔎 " + custom
        frames.append(d)
    if frames:
        allm = enrich(pd.concat(frames, ignore_index=True))
        s = allm["Sentiment"].value_counts()
        c1, c2, c3 = st.columns(3)
        c1.metric("🟢 Positives", s.get("🟢 Positif", 0))
        c2.metric("🔴 Négatives", s.get("🔴 Négatif", 0))
        c3.metric("⚪ Neutres", s.get("⚪ Neutre", 0))
        st.plotly_chart(px.histogram(allm, x="Catégorie", color="Sentiment",
                                     color_discrete_map={"🟢 Positif": "green", "🔴 Négatif": "red",
                                                         "⚪ Neutre": "gray"}, barmode="stack"),
                        use_container_width=True)
        st.dataframe(allm[["Date", "Catégorie", "Titre", "Source", "Sentiment", "Thème politique", "Lien"]],
                     use_container_width=True, height=500,
                     column_config={"Lien": st.column_config.LinkColumn("Lien")})

    st.subheader("📈 Réaction des indices de référence")
    idx = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^FCHI": "CAC 40", "^VIX": "VIX (peur)", "GC=F": "Or",
           "CL=F": "Pétrole", "EURUSD=X": "EUR/USD"}
    idata = get_prices(tuple(idx), "6mo")
    norm = pd.DataFrame({n: extract(idata, t)["Close"] for t, n in idx.items() if extract(idata, t) is not None})
    norm = norm.ffill().dropna()
    st.plotly_chart(px.line(norm / norm.iloc[0] * 100, title="Base 100 sur 6 mois"),
                    use_container_width=True)

# ---------------- TAB 4 : CARTE DU MARCHÉ ----------------
with tab4:
    st.subheader("Rendement 6 mois vs volatilité : repérer les « fusées » et les « montagnes russes »")
    fig = px.scatter(f, x="Volatilité 1 an %", y="Perf 6 mois %", size=f["Volume x"].clip(0.1, 5),
                     color="Profil", hover_name="Entreprise", text="Ticker", height=650)
    fig.update_traces(textposition="top center")
    fig.add_hline(y=0, line_dash="dot")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Treemap des performances 6 mois")
    tm = f.copy()
    tm["taille"] = tm["Volatilité 1 an %"].clip(lower=1)
    st.plotly_chart(px.treemap(tm, path=["Profil", "Ticker"], values="taille",
                               color="Perf 6 mois %", color_continuous_scale="RdYlGn",
                               color_continuous_midpoint=0, height=650),
                    use_container_width=True)
