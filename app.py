import re
from urllib.parse import quote

import feedparser
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Radar Bourse 3.0", page_icon="📡", layout="wide")

# =====================================================================
# 1. TENDANCES MONDIALES (grandes + petites entreprises)
# =====================================================================
TENDANCES = {
    "🤖 IA & semi-conducteurs": {
        "etf": "SMH",
        "actions": ["NVDA", "AVGO", "AMD", "TSM", "ASML", "PLTR", "ARM", "SOUN", "BBAI", "AI"],
        "pourquoi": "Les géants du cloud investissent des centaines de milliards dans les data centers. Puces et logiciels d'IA sont au coeur de cette vague.",
        "risques": "Valorisations élevées, dépendance à quelques gros clients, restrictions d'export vers la Chine, risque de bulle.",
    },
    "🛡️ Cybersécurité": {
        "etf": "CIBR",
        "actions": ["CRWD", "PANW", "ZS", "NET", "FTNT", "S", "RPD"],
        "pourquoi": "Explosion des cyberattaques, tensions géopolitiques et nouvelles obligations réglementaires : la sécurité devient incontournable.",
        "risques": "Concurrence forte, valorisations élevées, une panne majeure peut nuire à la réputation.",
    },
    "⚡ Énergie propre & électrification": {
        "etf": "ICLN",
        "actions": ["ENPH", "FSLR", "NEE", "PLUG", "RUN", "BE", "STEM", "SHLS"],
        "pourquoi": "Transition énergétique, demande d'électricité tirée par l'IA et les véhicules électriques, soutien public.",
        "risques": "Dépendance aux subventions et aux taux d'intérêt, marges fragiles, changements politiques.",
    },
    "🚀 Défense & spatial": {
        "etf": "ITA",
        "actions": ["LMT", "RTX", "RKLB", "PL", "ASTS", "LUNR", "RDW", "KTOS"],
        "pourquoi": "Hausse des budgets militaires mondiaux, tensions géopolitiques, nouvelle économie spatiale (satellites, lanceurs).",
        "risques": "Dépendance aux budgets publics, retards de programmes, très forte volatilité sur les petites valeurs spatiales.",
    },
    "🧬 Santé & biotech": {
        "etf": "XBI",
        "actions": ["LLY", "NVO", "VRTX", "ISRG", "REGN", "CRSP", "BEAM"],
        "pourquoi": "Vieillissement de la population, traitements de l'obésité, thérapies géniques, IA appliquée à la découverte de médicaments.",
        "risques": "Échecs d'essais cliniques (chute brutale), décisions réglementaires, pression sur les prix des médicaments.",
    },
    "💳 Fintech & paiements": {
        "etf": "ARKF",
        "actions": ["V", "MA", "SQ", "SOFI", "AFRM", "HOOD", "NU", "COIN"],
        "pourquoi": "Digitalisation des paiements, banque en ligne, crypto-actifs et services financiers accessibles.",
        "risques": "Régulation, sensibilité aux taux d'intérêt, risque de crédit, volatilité de la crypto.",
    },
    "☁️ Cloud & logiciels": {
        "etf": "WCLD",
        "actions": ["MSFT", "SNOW", "DDOG", "MDB", "NOW", "TEAM", "GTLB"],
        "pourquoi": "Migration des entreprises vers le cloud et intégration de l'IA dans les logiciels professionnels.",
        "risques": "Concurrence des géants, ralentissement des budgets IT, valorisations tendues.",
    },
    "⚛️ Quantique & technologies émergentes": {
        "etf": "QTUM",
        "actions": ["IONQ", "RGTI", "QBTS", "QUBT", "LUNR"],
        "pourquoi": "Course mondiale à l'informatique quantique, financements publics et privés en forte hausse.",
        "risques": "Technologie encore très jeune, peu de revenus, dilution du capital, risque de perte totale.",
    },
}

ETF_MARCHE = "SPY"

# Univers de scan pour les petites entreprises (liste de départ)
UNIVERS_SMALL = [
    "SOUN", "BBAI", "RGTI", "QBTS", "QUBT", "IONQ", "RKLB", "ASTS", "LUNR", "PL",
    "SOFI", "HOOD", "AFRM", "PLUG", "RUN", "BE", "STEM", "SHLS", "RPD", "S",
    "CRSP", "BEAM", "GTLB", "RDW", "KTOS",
]

DESCRIPTIONS_PROFILS = {
    "🚀 Croissance solide": "Le cours monte ET l'entreprise est saine. Le profil le plus intéressant, mais pas sans risque.",
    "🎲 Spéculatif": "Le cours monte fort mais les fondamentaux sont fragiles. Gros potentiel, gros risque de chute.",
    "💎 Solide mais délaissée": "Bonne entreprise dont le cours n'a pas encore suivi. À surveiller.",
    "⚖️ À surveiller": "Signaux mélangés, pas de conviction claire.",
}

# =====================================================================
# 2. DONNÉES
# =====================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def charger_prix(tickers, periode="1y"):
    if not tickers:
        return pd.DataFrame()
    try:
        data = yf.download(list(tickers), period=periode, auto_adjust=True,
                           progress=False, group_by="column", threads=True)
        if data.empty:
            return pd.DataFrame()
        close = data["Close"] if "Close" in data else data
        if isinstance(close, pd.Series):
            close = close.to_frame(name=list(tickers)[0])
        return close.dropna(how="all")
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=86400, show_spinner=False)
def charger_infos(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


@st.cache_data(ttl=1800, show_spinner=False)
def charger_actus(ticker):
    try:
        url = f"https://news.google.com/rss/search?q={quote(ticker + ' stock')}&hl=fr&gl=FR&ceid=FR:fr"
        flux = feedparser.parse(url)
        return [{"titre": e.get("title", ""), "lien": e.get("link", ""),
                 "date": e.get("published", "")} for e in flux.entries[:6]]
    except Exception:
        return []

# =====================================================================
# 3. CALCULS DE PERFORMANCE ET DE RISQUE
# =====================================================================
def perf(serie, jours):
    s = serie.dropna()
    if len(s) < 2:
        return np.nan
    n = min(jours, len(s) - 1)
    return (s.iloc[-1] / s.iloc[-1 - n] - 1) * 100


def volatilite_annuelle(serie):
    r = serie.dropna().pct_change().dropna()
    if len(r) < 20:
        return np.nan
    return r.std() * np.sqrt(252) * 100


def drawdown_max(serie):
    s = serie.dropna()
    if len(s) < 2:
        return np.nan
    sommet = s.cummax()
    return ((s / sommet - 1).min()) * 100


def hausse_parabolique(serie):
    s = serie.dropna()
    if len(s) < 60:
        return False
    return perf(s, 60) > 80


def classer_capitalisation(cap):
    if cap is None or pd.isna(cap) or cap == 0:
        return "Inconnue"
    if cap < 300e6:
        return "Micro-cap"
    if cap < 2e9:
        return "Petite cap"
    if cap < 10e9:
        return "Moyenne cap"
    return "Grande cap"

# =====================================================================
# 4. SCORES
# =====================================================================
def score_momentum(p1m, p3m, p6m, p12m, p6m_marche):
    pts = 0.0
    for p in (p3m, p6m):
        if pd.notna(p):
            pts += min(max(p, -20), 80) / 80 * 35
    if pd.notna(p6m) and pd.notna(p6m_marche):
        rel = p6m - p6m_marche
        pts += min(max(rel, -20), 60) / 60 * 20
    if pd.notna(p1m) and p1m > 0:
        pts += 5
    if pd.notna(p12m) and p12m > 0:
        pts += 5
    return round(min(max(pts, 0), 100), 1)


def score_fondamentaux(info):
    pts, poids = 0.0, 0.0

    def ajoute(valeur, bas, haut, poids_c):
        nonlocal pts, poids
        if valeur is None or pd.isna(valeur):
            return
        pts += min(max((valeur - bas) / (haut - bas), 0), 1) * poids_c
        poids += poids_c

    ajoute(info.get("revenueGrowth"), 0.0, 0.40, 30)
    ajoute(info.get("earningsGrowth"), 0.0, 0.50, 15)
    ajoute(info.get("grossMargins"), 0.20, 0.70, 15)
    ajoute(info.get("operatingMargins"), 0.0, 0.30, 15)
    ajoute(info.get("returnOnEquity"), 0.0, 0.30, 10)
    dette = info.get("debtToEquity")
    if dette is not None and not pd.isna(dette):
        pts += (1 - min(max(dette, 0), 300) / 300) * 15
        poids += 15
    if poids == 0:
        return np.nan
    return round(pts / poids * 100, 1)


def score_risque(vol, drawdown, cap_classe, parabolique, fond):
    pts = 0.0
    if pd.notna(vol):
        pts += min(vol, 100) / 100 * 40
    else:
        pts += 20
    if pd.notna(drawdown):
        pts += min(abs(drawdown), 60) / 60 * 25
    else:
        pts += 12
    pts += {"Grande cap": 0, "Moyenne cap": 5, "Petite cap": 12,
            "Micro-cap": 20, "Inconnue": 10}.get(cap_classe, 10)
    if parabolique:
        pts += 10
    if pd.notna(fond) and fond < 35:
        pts += 5
    return round(min(pts, 100), 1)


def profil(mom, fond, risque):
    if pd.isna(fond):
        return "🎲 Spéculatif" if mom >= 55 else "⚖️ À surveiller"
    if mom >= 55 and fond >= 55 and risque < 70:
        return "🚀 Croissance solide"
    if mom >= 55 and fond < 40:
        return "🎲 Spéculatif"
    if mom < 45 and fond >= 60:
        return "💎 Solide mais délaissée"
    return "⚖️ À surveiller"


def badges(cap_classe, volume_moyen, parabolique, vol):
    b = []
    if cap_classe in ("Micro-cap", "Petite cap"):
        b.append(f"⚠️ {cap_classe}")
    if volume_moyen is not None and volume_moyen < 300_000:
        b.append("💧 Faible liquidité")
    if parabolique:
        b.append("📈 Hausse parabolique")
    if pd.notna(vol) and vol > 70:
        b.append("🌪️ Très volatile")
    return b

# =====================================================================
# 5. ANALYSE COMPLÈTE D'UN TICKER
# =====================================================================
def analyser_ticker(ticker, serie, serie_marche, tendance=None):
    info = charger_infos(ticker)
    p1m, p3m, p6m = perf(serie, 21), perf(serie, 63), perf(serie, 126)
    p12m = perf(serie, 252)
    p6m_marche = perf(serie_marche, 126) if serie_marche is not None else np.nan
    vol = volatilite_annuelle(serie)
    dd = drawdown_max(serie)
    cap = info.get("marketCap")
    cap_classe = classer_capitalisation(cap)
    parab = hausse_parabolique(serie)
    mom = score_momentum(p1m, p3m, p6m, p12m, p6m_marche)
    fond = score_fondamentaux(info)
    risque = score_risque(vol, dd, cap_classe, parab, fond)
    prof = profil(mom, fond, risque)
    return {
        "Ticker": ticker,
        "Nom": info.get("shortName", ticker),
        "Secteur": info.get("sector", "n/a"),
        "Tendance": tendance or "Recherche libre",
        "Capitalisation": cap_classe,
        "Cap ($)": cap,
        "Perf 1m %": round(p1m, 1) if pd.notna(p1m) else np.nan,
        "Perf 3m %": round(p3m, 1) if pd.notna(p3m) else np.nan,
        "Perf 6m %": round(p6m, 1) if pd.notna(p6m) else np.nan,
        "Perf 12m %": round(p12m, 1) if pd.notna(p12m) else np.nan,
        "Volatilité %": round(vol, 1) if pd.notna(vol) else np.nan,
        "Drawdown max %": round(dd, 1) if pd.notna(dd) else np.nan,
        "Momentum": mom,
        "Fondamentaux": fond,
        "Risque": risque,
        "Profil": prof,
        "Badges": " ".join(badges(cap_classe, info.get("averageVolume"), parab, vol)),
        "Croiss. CA %": round(info["revenueGrowth"] * 100, 1) if info.get("revenueGrowth") is not None else np.nan,
        "Marge op. %": round(info["operatingMargins"] * 100, 1) if info.get("operatingMargins") is not None else np.nan,
        "Dette/Fonds propres": info.get("debtToEquity", np.nan),
        "PER prévisionnel": info.get("forwardPE", np.nan),
        "Description": info.get("longBusinessSummary", ""),
    }

# =====================================================================
# 6. PLAN D'INVESTISSEMENT (taille, durée, scénarios, stop-loss)
# =====================================================================
def plan_investissement(ligne, serie, capital):
    risque = ligne["Risque"]
    vol = ligne["Volatilité %"]
    dd = ligne["Drawdown max %"]

    if risque < 35:
        pct_max, label = 8, "Risque modéré"
    elif risque < 50:
        pct_max, label = 5, "Risque moyen"
    elif risque < 65:
        pct_max, label = 3, "Risque élevé"
    elif risque < 80:
        pct_max, label = 2, "Risque très élevé"
    else:
        pct_max, label = 1, "Risque extrême"

    if ligne["Profil"] == "🚀 Croissance solide":
        horizon = "Moyen à long terme (1 à 3 ans)"
        raison = "Les fondamentaux soutiennent la hausse : mieux vaut laisser le temps jouer."
    elif ligne["Profil"] == "🎲 Spéculatif":
        horizon = "Court terme (3 à 6 mois), avec suivi serré"
        raison = "La hausse repose surtout sur l'élan du marché : il faut surveiller et être prêt à sortir."
    elif ligne["Profil"] == "💎 Solide mais délaissée":
        horizon = "Long terme (2 à 5 ans)"
        raison = "Entreprise saine dont le cours peut rattraper son retard, mais cela peut prendre du temps."
    else:
        horizon = "Observation d'abord, pas d'urgence"
        raison = "Pas de signal clair : attendre une meilleure configuration."

    vol_eff = vol if pd.notna(vol) else 50
    stop_pct = min(max(vol_eff * 0.4, 8), 35)

    montant_max = capital * pct_max / 100
    perte_stop = montant_max * stop_pct / 100

    # Scénarios sur 12 mois, fondés sur la volatilité historique
    sigma = vol_eff / 100
    scenarios = {
        "Pessimiste (défavorable)": -1.0 * sigma,
        "Central (neutre)": 0.0,
        "Optimiste (favorable)": 1.0 * sigma,
    }
    return {
        "pct_max": pct_max, "label_risque": label, "horizon": horizon,
        "raison_horizon": raison, "stop_pct": round(stop_pct, 1),
        "montant_max": round(montant_max, 2), "perte_stop": round(perte_stop, 2),
        "scenarios": scenarios, "sigma": sigma,
        "pire_cas": dd,
    }


def explication(ligne, tendance_info):
    t = []
    mom, fond, risque = ligne["Momentum"], ligne["Fondamentaux"], ligne["Risque"]
    if mom >= 65:
        t.append(f"📈 **Élan fort** : {ligne['Perf 6m %']} % sur 6 mois, le marché récompense clairement ce titre.")
    elif mom >= 45:
        t.append(f"📊 **Élan correct** : {ligne['Perf 6m %']} % sur 6 mois, sans excès.")
    else:
        t.append(f"📉 **Élan faible** : {ligne['Perf 6m %']} % sur 6 mois, le marché n'est pas convaincu.")
    if pd.notna(fond):
        if fond >= 65:
            t.append("🏗️ **Fondamentaux solides** : croissance, marges et endettement sont globalement sains.")
        elif fond >= 40:
            t.append("🏗️ **Fondamentaux moyens** : certains indicateurs sont bons, d'autres fragiles.")
        else:
            t.append("🏗️ **Fondamentaux faibles** : l'entreprise est peu rentable ou très endettée. La hausse est surtout de la spéculation.")
    else:
        t.append("🏗️ **Fondamentaux indisponibles** : données financières insuffisantes, prudence.")
    if tendance_info:
        t.append(f"🌍 **Contexte** : {tendance_info['pourquoi']}")
    if risque >= 65:
        t.append("🔥 **Risque élevé** : forte volatilité et/ou petite taille. Une perte importante est possible.")
    if "Hausse parabolique" in ligne["Badges"]:
        t.append("⚠️ **Hausse parabolique** : le titre a explosé en peu de temps. Historiquement, ces hausses se retournent souvent brutalement.")
    if tendance_info:
        t.append(f"⚠️ **Risques de la tendance** : {tendance_info['risques']}")
    return t
# =====================================================================
# 7. ÉTAT DE LA SESSION (watchlist, portefeuille fictif)
# =====================================================================
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "papier" not in st.session_state:
    st.session_state.papier = []


def tendance_de(ticker):
    for nom, t in TENDANCES.items():
        if ticker in t["actions"]:
            return nom
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def analyser_liste(tickers_tuple, tendances_tuple):
    tickers = list(tickers_tuple)
    prix = charger_prix(tuple(tickers + [ETF_MARCHE]), "1y")
    if prix.empty:
        return pd.DataFrame(), prix
    marche = prix[ETF_MARCHE] if ETF_MARCHE in prix else None
    lignes = []
    for tk, tend in zip(tickers, tendances_tuple):
        if tk in prix.columns and prix[tk].dropna().shape[0] > 30:
            lignes.append(analyser_ticker(tk, prix[tk], marche, tend))
    return pd.DataFrame(lignes), prix


# =====================================================================
# 8. BARRE LATÉRALE (filtres)
# =====================================================================
st.title("📡 Radar Bourse 3.0")
st.caption("Détection des entreprises en forte progression, analyse expliquée et plan d'investissement. Outil pédagogique : ce n'est pas un conseil en investissement.")

with st.sidebar:
    st.header("🎛️ Paramètres")
    capital = st.number_input("💶 Votre capital total (€)", min_value=100, value=5000, step=100)
    st.subheader("Filtres")
    tendances_choisies = st.multiselect("Tendances", list(TENDANCES.keys()),
                                        default=list(TENDANCES.keys()))
    inclure_small = st.checkbox("Inclure le scanner de petites entreprises", value=True)
    caps_ok = st.multiselect("Tailles d'entreprise",
                             ["Grande cap", "Moyenne cap", "Petite cap", "Micro-cap", "Inconnue"],
                             default=["Grande cap", "Moyenne cap", "Petite cap", "Micro-cap", "Inconnue"])
    mom_min = st.slider("Momentum minimum", 0, 100, 0)
    risque_max = st.slider("Risque maximum", 0, 100, 100)
    profils_ok = st.multiselect("Profils", list(DESCRIPTIONS_PROFILS.keys()),
                                default=list(DESCRIPTIONS_PROFILS.keys()))

# Construction de l'univers
tickers, tends = [], []
for nom in tendances_choisies:
    for tk in TENDANCES[nom]["actions"]:
        if tk not in tickers:
            tickers.append(tk)
            tends.append(nom)
if inclure_small:
    for tk in UNIVERS_SMALL:
        if tk not in tickers:
            tickers.append(tk)
            tends.append(tendance_de(tk) or "Scanner petites caps")

with st.spinner("Analyse du marché en cours (30 à 60 secondes la première fois)..."):
    df, prix = analyser_liste(tuple(tickers), tuple(tends))

if df.empty:
    st.error("Impossible de charger les données pour le moment. Réessayez dans quelques minutes.")
    st.stop()

df_f = df[
    df["Capitalisation"].isin(caps_ok)
    & (df["Momentum"] >= mom_min)
    & (df["Risque"] <= risque_max)
    & df["Profil"].isin(profils_ok)
].copy()

# =====================================================================
# 9. ONGLETS
# =====================================================================
onglets = st.tabs([
    "🏆 Classement", "🔍 Recherche libre", "📋 Fiche & plan", "⚖️ Comparateur",
    "🌍 Tendances", "⭐ Watchlist", "🧪 Backtest", "📓 Mode papier",
    "💼 Mon portefeuille", "❓ Aide",
])

# ---------- Onglet 1 : Classement ----------
with onglets[0]:
    st.subheader("🏆 Classement des entreprises")
    st.write(f"**{len(df_f)}** entreprises correspondent à vos filtres (sur {len(df)} analysées).")
    if df_f.empty:
        st.info("Aucune entreprise ne correspond. Assouplissez les filtres à gauche.")
    else:
        tri = st.selectbox("Trier par", ["Momentum", "Fondamentaux", "Perf 6m %", "Perf 3m %", "Risque"])
        df_aff = df_f.sort_values(tri, ascending=(tri == "Risque"))
        cols = ["Ticker", "Nom", "Tendance", "Capitalisation", "Perf 3m %", "Perf 6m %",
                "Perf 12m %", "Momentum", "Fondamentaux", "Risque", "Profil", "Badges"]
        st.dataframe(df_aff[cols], use_container_width=True, hide_index=True, height=450)

        fig = px.scatter(
            df_aff, x="Risque", y="Perf 6m %", size="Momentum", color="Profil",
            hover_name="Nom", text="Ticker",
            title="Rendement sur 6 mois selon le risque (haut-gauche = idéal)",
        )
        fig.update_traces(textposition="top center")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Plus un point est en haut à gauche, meilleur est le rapport rendement/risque. Les grosses bulles ont un fort momentum.")

# ---------- Onglet 2 : Recherche libre ----------
with onglets[1]:
    st.subheader("🔍 Analyser n'importe quelle entreprise")
    st.write("Entrez un ou plusieurs tickers séparés par des virgules. Pour l'Europe, ajoutez le suffixe : `.PA` (Paris), `.DE` (Allemagne), `.AS` (Amsterdam).")
    saisie = st.text_input("Tickers", placeholder="Ex : RKLB, SOUN, MC.PA, ASML.AS")
    if saisie:
        liste = [x.strip().upper() for x in saisie.split(",") if x.strip()]
        res, _ = analyser_liste(tuple(liste), tuple([tendance_de(x) or "Recherche libre" for x in liste]))
        if res.empty:
            st.warning("Aucune donnée trouvée. Vérifiez l'orthographe du ticker.")
        else:
            st.dataframe(res[["Ticker", "Nom", "Capitalisation", "Perf 6m %", "Perf 12m %",
                              "Momentum", "Fondamentaux", "Risque", "Profil", "Badges"]],
                         use_container_width=True, hide_index=True)
            st.info("Pour le plan d'investissement détaillé, allez dans l'onglet « Fiche & plan » : ces tickers y seront disponibles après analyse.")
            st.session_state["recherche"] = res

# ---------- Onglet 3 : Fiche & plan ----------
with onglets[2]:
    st.subheader("📋 Fiche détaillée et plan d'investissement")
    base = pd.concat([df, st.session_state.get("recherche", pd.DataFrame())]).drop_duplicates("Ticker")
    choix = st.selectbox("Choisissez une entreprise", base["Ticker"] + " - " + base["Nom"].astype(str))
    tk = choix.split(" - ")[0]
    ligne = base[base["Ticker"] == tk].iloc[0]
    serie = charger_prix((tk,), "1y")[tk].dropna()
    marche = charger_prix((ETF_MARCHE,), "1y")[ETF_MARCHE].dropna()

    st.markdown(f"### {ligne['Nom']} ({tk}) {ligne['Profil']}")
    if ligne["Badges"]:
        st.warning(ligne["Badges"])
    st.caption(DESCRIPTIONS_PROFILS.get(ligne["Profil"], ""))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Momentum", f"{ligne['Momentum']}/100")
    c2.metric("Fondamentaux", f"{ligne['Fondamentaux']}/100" if pd.notna(ligne["Fondamentaux"]) else "n/a")
    c3.metric("Risque", f"{ligne['Risque']}/100")
    c4.metric("Perf 6 mois", f"{ligne['Perf 6m %']} %")

    # Graphique prix vs marché
    n = min(len(serie), len(marche))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=serie.index, y=serie / serie.iloc[0] * 100, name=tk))
    fig.add_trace(go.Scatter(x=marche.index, y=marche / marche.iloc[0] * 100,
                             name="Marché (S&P 500)", line=dict(dash="dot")))
    fig.update_layout(title="Évolution comparée (base 100 il y a 1 an)", height=380)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🧠 Pourquoi ce résultat ?")
    tinfo = TENDANCES.get(ligne["Tendance"])
    for phrase in explication(ligne, tinfo):
        st.markdown(f"- {phrase}")

    # Plan d'investissement
    st.markdown("#### 💰 Plan d'investissement (repère pédagogique)")
    plan = plan_investissement(ligne, serie, capital)
    p1, p2, p3 = st.columns(3)
    p1.metric("Niveau de risque", plan["label_risque"])
    p2.metric("Part max suggérée", f"{plan['pct_max']} % du capital")
    p3.metric("Montant max", f"{plan['montant_max']} €")
    st.markdown(f"**⏱️ Horizon :** {plan['horizon']}  \n_{plan['raison_horizon']}_")
    st.markdown(f"**🛑 Stop-loss indicatif :** environ **-{plan['stop_pct']} %** depuis votre prix d'achat. "
                f"Sur {plan['montant_max']} €, cela limiterait la perte à environ **{plan['perte_stop']} €**.")
    if pd.notna(plan["pire_cas"]):
        pire = plan["montant_max"] * (1 + plan["pire_cas"] / 100)
        st.markdown(f"**📉 Pire moment de l'année écoulée :** {plan['pire_cas']} %. "
                    f"Sur {plan['montant_max']} €, votre position serait tombée à environ **{round(pire, 2)} €**.")

    st.markdown("**🔮 Scénarios à 12 mois (basés sur la volatilité passée, pas une prévision) :**")
    lignes_sc = []
    for nom, mult in plan["scenarios"].items():
        gain = plan["montant_max"] * mult
        lignes_sc.append({"Scénario": nom, "Variation": f"{mult * 100:+.0f} %",
                          "Sur le montant max": f"{gain:+.0f} €"})
    st.table(pd.DataFrame(lignes_sc))
    st.caption("Ces scénarios illustrent l'amplitude possible des mouvements. Ils ne sont pas des prévisions et le passé ne garantit pas l'avenir.")

    # Simulateur "et si"
    st.markdown("#### 🎮 Simulateur « Et si j'avais investi ? »")
    mise = st.slider("Montant investi (€)", 100, 10000, 1000, 100)
    mois = st.select_slider("Il y a combien de mois ?", options=[1, 3, 6, 9, 12], value=6)
    jours = {1: 21, 3: 63, 6: 126, 9: 189, 12: 251}[mois]
    jours = min(jours, len(serie) - 1)
    valeur = mise * serie.iloc[-1] / serie.iloc[-1 - jours]
    st.success(f"Vos {mise} € seraient aujourd'hui à environ **{valeur:.0f} €** ({valeur - mise:+.0f} €).")

    # Actualités
    st.markdown("#### 📰 Actualités récentes")
    for a in charger_actus(tk):
        st.markdown(f"- [{a['titre']}]({a['lien']})")

    # Actions
    b1, b2 = st.columns(2)
    if b1.button("⭐ Ajouter à la watchlist"):
        if tk not in st.session_state.watchlist:
            st.session_state.watchlist.append(tk)
        st.success("Ajouté.")
    if b2.button("📓 Acheter en mode papier (montant max)"):
        st.session_state.papier.append({"ticker": tk, "prix": float(serie.iloc[-1]),
                                        "montant": plan["montant_max"]})
        st.success("Position fictive ouverte.")

    # Analyste IA optionnel
    if "ANTHROPIC_API_KEY" in st.secrets:
        if st.button("🤖 Demander un avis à l'analyste IA"):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                actus = "\n".join(a["titre"] for a in charger_actus(tk))
                prompt = (f"Analyse {ligne['Nom']} ({tk}). Momentum {ligne['Momentum']}, "
                          f"fondamentaux {ligne['Fondamentaux']}, risque {ligne['Risque']}, "
                          f"perf 6m {ligne['Perf 6m %']}%. Actualités :\n{actus}\n"
                          "Donne en français une analyse équilibrée (points forts, risques, "
                          "contexte mondial) en 150 mots, sans conseil d'achat.")
                rep = client.messages.create(model="claude-sonnet-4-5", max_tokens=500,
                                             messages=[{"role": "user", "content": prompt}])
                st.info(rep.content[0].text)
            except Exception as e:
                st.error(f"Analyste IA indisponible : {e}")

# ---------- Onglet 4 : Comparateur ----------
with onglets[3]:
    st.subheader("⚖️ Comparer des entreprises")
    sel = st.multiselect("Choisissez 2 à 4 entreprises", list(df["Ticker"]), max_selections=4)
    if len(sel) >= 2:
        fig = go.Figure()
        for s in sel:
            sr = prix[s].dropna()
            fig.add_trace(go.Scatter(x=sr.index, y=sr / sr.iloc[0] * 100, name=s))
        fig.update_layout(title="Performance comparée (base 100)", height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[df["Ticker"].isin(sel)][["Ticker", "Nom", "Perf 6m %", "Momentum",
                                                  "Fondamentaux", "Risque", "Volatilité %", "Profil"]],
                     use_container_width=True, hide_index=True)
    else:
        st.info("Sélectionnez au moins 2 entreprises.")

# ---------- Onglet 5 : Tendances ----------
with onglets[4]:
    st.subheader("🌍 Les grandes tendances")
    for nom, t in TENDANCES.items():
        sous = df[df["Tendance"] == nom]
        with st.expander(f"{nom} ({len(sous)} entreprises)"):
            st.markdown(f"**Pourquoi ça porte :** {t['pourquoi']}")
            st.markdown(f"**Risques :** {t['risques']}")
            if not sous.empty:
                st.dataframe(sous.sort_values("Momentum", ascending=False)[
                    ["Ticker", "Nom", "Perf 6m %", "Momentum", "Fondamentaux", "Risque", "Profil"]],
                    use_container_width=True, hide_index=True)

# ---------- Onglet 6 : Watchlist ----------
with onglets[5]:
    st.subheader("⭐ Ma watchlist")
    st.caption("La watchlist est conservée tant que la page reste ouverte.")
    if not st.session_state.watchlist:
        st.info("Vide. Ajoutez des entreprises depuis l'onglet « Fiche & plan ».")
    else:
        w = df[df["Ticker"].isin(st.session_state.watchlist)]
        st.dataframe(w[["Ticker", "Nom", "Perf 1m %", "Perf 6m %", "Momentum", "Risque", "Profil"]],
                     use_container_width=True, hide_index=True)
        if st.button("🗑️ Vider la watchlist"):
            st.session_state.watchlist = []
            st.rerun()

# ---------- Onglet 7 : Backtest ----------
with onglets[6]:
    st.subheader("🧪 Backtest simplifié")
    st.write("Test : si on avait acheté, il y a 6 mois, les entreprises qui avaient alors le meilleur élan "
             "(mesuré sur les 6 mois précédents), auraient-elles battu le marché ?")
    pr = charger_prix(tuple(df["Ticker"].tolist() + [ETF_MARCHE]), "2y")
    if pr.shape[0] > 280:
        coupe = pr.shape[0] - 126
        avant = pr.iloc[:coupe]
        apres = pr.iloc[coupe - 1:]
        mom_avant = {}
        for c in avant.columns:
            s = avant[c].dropna()
            if len(s) > 130 and c != ETF_MARCHE:
                mom_avant[c] = perf(s, 126)
        classement = pd.Series(mom_avant).sort_values(ascending=False)
        n_top = max(5, len(classement) // 5)
        top = classement.head(n_top).index
        reste = classement.tail(len(classement) - n_top).index

        def rend(cols):
            vals = [(apres[c].dropna().iloc[-1] / apres[c].dropna().iloc[0] - 1) * 100
                    for c in cols if apres[c].dropna().shape[0] > 10]
            return np.mean(vals) if vals else np.nan

        r_top, r_reste = rend(top), rend(reste)
        r_marche = (apres[ETF_MARCHE].iloc[-1] / apres[ETF_MARCHE].iloc[0] - 1) * 100
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Top {n_top} élan (il y a 6 mois)", f"{r_top:+.1f} %")
        m2.metric("Les autres", f"{r_reste:+.1f} %")
        m3.metric("Marché (S&P 500)", f"{r_marche:+.1f} %")
        if r_top > r_marche:
            st.success("Sur cette période, les titres à fort élan ont battu le marché. Cela ne garantit rien pour l'avenir.")
        else:
            st.warning("Sur cette période, les titres à fort élan n'ont PAS battu le marché. Preuve que le momentum seul ne suffit pas.")
        st.caption("Backtest très simplifié : une seule période, pas de frais, biais possible (liste actuelle d'entreprises). À prendre comme un indice, pas une preuve.")
    else:
        st.info("Pas assez d'historique pour le backtest.")

# ---------- Onglet 8 : Mode papier ----------
with onglets[7]:
    st.subheader("📓 Portefeuille fictif (mode papier)")
    st.write("Testez vos idées avec de l'argent virtuel avant de risquer du vrai argent.")
    if not st.session_state.papier:
        st.info("Aucune position. Ouvrez-en depuis l'onglet « Fiche & plan ».")
    else:
        rows, total_in, total_now = [], 0, 0
        pp = charger_prix(tuple({p["ticker"] for p in st.session_state.papier}), "5d")
        for p in st.session_state.papier:
            if p["ticker"] in pp.columns:
                actuel = float(pp[p["ticker"]].dropna().iloc[-1])
                val = p["montant"] * actuel / p["prix"]
                rows.append({"Ticker": p["ticker"], "Mis (€)": p["montant"],
                             "Valeur (€)": round(val, 2),
                             "Variation %": round((val / p["montant"] - 1) * 100, 1)})
                total_in += p["montant"]
                total_now += val
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if total_in:
            st.metric("Total", f"{total_now:.0f} €", f"{(total_now / total_in - 1) * 100:+.1f} %")
        if st.button("🗑️ Réinitialiser le mode papier"):
            st.session_state.papier = []
            st.rerun()

# ---------- Onglet 9 : Portefeuille réel (CSV) + corrélations ----------
with onglets[8]:
    st.subheader("💼 Mon portefeuille réel")
    st.write("Importez un fichier CSV avec les colonnes : `ticker, quantite, prix_achat`.")
    fichier = st.file_uploader("Fichier CSV", type="csv")
    if fichier:
        pf = pd.read_csv(fichier)
        pf.columns = [c.strip().lower() for c in pf.columns]
        if {"ticker", "quantite", "prix_achat"}.issubset(pf.columns):
            tks = tuple(pf["ticker"].str.upper().tolist())
            pxs = charger_prix(tks, "1y")
            lignes, total = [], 0
            for _, r in pf.iterrows():
                t = str(r["ticker"]).upper()
                if t in pxs.columns:
                    actuel = float(pxs[t].dropna().iloc[-1])
                    val = actuel * r["quantite"]
                    total += val
                    lignes.append({"Ticker": t, "Quantité": r["quantite"],
                                   "Prix achat": r["prix_achat"], "Prix actuel": round(actuel, 2),
                                   "Valeur": round(val, 2),
                                   "Gain %": round((actuel / r["prix_achat"] - 1) * 100, 1)})
            dfp = pd.DataFrame(lignes)
            dfp["Poids %"] = (dfp["Valeur"] / total * 100).round(1)
            st.dataframe(dfp, use_container_width=True, hide_index=True)
            st.metric("Valeur totale", f"{total:,.0f}")
            fig = px.pie(dfp, names="Ticker", values="Valeur", title="Répartition")
            st.plotly_chart(fig, use_container_width=True)
            if (dfp["Poids %"] > 25).any():
                st.warning("⚠️ Une position dépasse 25 % du portefeuille : forte concentration.")
            if len(tks) >= 3:
                corr = pxs.pct_change().dropna().corr()
                fig2 = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                                 zmin=-1, zmax=1, title="Corrélations (proche de 1 = bougent ensemble)")
                st.plotly_chart(fig2, use_container_width=True)
                st.caption("Des valeurs proches de 1 signifient que vos actions réagissent de la même façon : peu de diversification.")
        else:
            st.error("Le CSV doit contenir : ticker, quantite, prix_achat.")
# ---------- Onglet 10 : Aide ----------
with onglets[9]:
    st.subheader("❓ Aide")
    st.markdown("""
**Momentum** : le cours monte-t-il plus vite que le marché ?

**Fondamentaux** : croissance, marges, rentabilité, endettement.

**Risque** : plus le chiffre est haut, plus l'investissement est dangereux.

**Les profils**
- 🚀 Croissance solide : le cours monte ET l'entreprise est saine.
- 🎲 Spéculatif : le cours monte mais les fondamentaux sont fragiles.
- 💎 Solide mais délaissée : bonne entreprise dont le cours est en retard.
- ⚖️ À surveiller : signaux mélangés.

**Petites entreprises** : elles peuvent monter très vite mais aussi perdre
la quasi-totalité de leur valeur. Gardez des montants faibles.

**Importer un CSV** : colonnes ticker, quantite, prix_achat.
Pour l'Europe, ajoutez le suffixe de la bourse (.PA, .DE, .AS).

**Plan d'investissement** : les montants, durées et stop-loss affichés sont
des repères pédagogiques calculés à partir de la volatilité passée.
Ils ne constituent pas un conseil personnalisé.

**Analyste IA (optionnel)** : ajoutez ANTHROPIC_API_KEY dans les Secrets
de Streamlit pour l'activer.
""")
    st.warning("⚠️ Outil pédagogique : ne constitue pas un conseil en investissement. Le passé ne garantit pas l'avenir. N'investissez que de l'argent que vous pouvez vous permettre de perdre.")


