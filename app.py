import re
from urllib.parse import quote

import feedparser
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Radar Bourse 2.0", page_icon="📡", layout="wide")

# =====================================================================
# 1. LES GRANDES TENDANCES MONDIALES
# =====================================================================
TENDANCES = {
    "🤖 IA & semi-conducteurs": {
        "etf": "SMH",
        "actions": ["NVDA", "AVGO", "AMD", "TSM", "ASML", "PLTR", "ARM"],
        "pourquoi": "Les géants du cloud investissent des centaines de milliards dans les data centers. Puces et logiciels d'IA sont au cœur de cette vague.",
        "risques": "Valorisations élevées, dépendance à quelques gros clients, restrictions d'export vers la Chine, risque de bulle.",
    },
    "🛡️ Cybersécurité": {
        "etf": "CIBR",
        "actions": ["CRWD", "PANW", "ZS", "NET", "FTNT"],
        "pourquoi": "Explosion des cyberattaques, tensions géopolitiques et nouvelles obligations réglementaires : la sécurité devient incontournable.",
        "risques": "Concurrence forte, valorisations élevées, une panne majeure peut nuire à la réputation.",
    },
    "⚛️ Nucléaire & uranium": {
        "etf": "URA",
        "actions": ["CCJ", "CEG", "VST", "OKLO", "SMR"],
        "pourquoi": "Les data centers d'IA ont besoin d'une électricité énorme et stable. Le nucléaire revient en grâce (soutien des États, petits réacteurs SMR).",
        "risques": "Projets très longs, dépendance aux autorisations publiques, certaines sociétés n'ont pas encore de revenus.",
    },
    "⚡ Électrification & réseaux": {
        "etf": "GRID",
        "actions": ["ETN", "VRT", "GEV", "SU.PA", "PWR"],
        "pourquoi": "Il faut moderniser les réseaux électriques pour les data centers, les voitures électriques et la relocalisation industrielle.",
        "risques": "Secteur cyclique, sensible aux taux d'intérêt et aux budgets d'investissement.",
    },
    "🌱 Énergies renouvelables": {
        "etf": "ICLN",
        "actions": ["FSLR", "ENPH", "NEE", "ORSTED.CO"],
        "pourquoi": "Transition énergétique, objectifs climat, coûts du solaire en baisse.",
        "risques": "Très dépendant des subventions et des décisions politiques, sensible aux taux.",
    },
    "🎖️ Défense & souveraineté": {
        "etf": "ITA",
        "actions": ["RHM.DE", "HO.PA", "SAF.PA", "LMT", "RTX"],
        "pourquoi": "Réarmement de l'Europe, hausse des budgets militaires de l'OTAN, conflits en cours.",
        "risques": "Un accord de paix ou des coupes budgétaires peuvent faire chuter le secteur, enjeux éthiques.",
    },
    "🧬 Santé & longévité": {
        "etf": "XLV",
        "actions": ["LLY", "NVO", "VRTX", "ISRG"],
        "pourquoi": "Vieillissement de la population, traitements contre l'obésité (GLP-1), chirurgie robotisée.",
        "risques": "Pression politique sur le prix des médicaments, échecs d'essais cliniques.",
    },
    "🦾 Robotique & automatisation": {
        "etf": "BOTZ",
        "actions": ["TSLA", "ROK", "SYM", "TER", "ABBN.SW"],
        "pourquoi": "Manque de main-d'œuvre, relocalisation des usines, robots humanoïdes et IA physique.",
        "risques": "Promesses parfois lointaines, forte volatilité.",
    },
    "🚀 Spatial": {
        "etf": "UFO",
        "actions": ["RKLB", "ASTS", "LUNR"],
        "pourquoi": "Baisse du coût des lancements, constellations de satellites, budgets de défense spatiale.",
        "risques": "Entreprises souvent non rentables, très spéculatives, besoin de lever de l'argent.",
    },
    "💳 Fintech & paiements": {
        "etf": "FINX",
        "actions": ["HOOD", "SOFI", "NU", "ADYEN.AS", "MELI"],
        "pourquoi": "Numérisation de la banque, nouvelles générations d'investisseurs, paiements mobiles dans les pays émergents.",
        "risques": "Régulation, sensibilité aux cycles de crédit et à l'activité des particuliers en bourse.",
    },
}

MOTS_CLES = {
    "🏛️ Taux / banques centrales": ["fed", "bce", "taux", "powell", "lagarde", "inflation"],
    "🚢 Douane / commerce": ["douane", "douanes", "tarif", "tarifs", "tariff", "tariffs", "export", "exportations"],
    "💶 Subventions / plans publics": ["subvention", "subventions", "chips act", "plan", "aide publique", "budget"],
    "⚔️ Géopolitique / défense": ["guerre", "otan", "nato", "ukraine", "chine", "taïwan", "sanction", "sanctions", "défense"],
    "⚖️ Régulation / justice": ["régulation", "antitrust", "amende", "enquête", "sec", "bruxelles", "procès"],
    "📊 Résultats / contrats": ["résultats", "chiffre d'affaires", "bénéfice", "contrat", "commande", "prévisions", "earnings"],
}

BENCH = "^GSPC"  # S&P 500

# =====================================================================
# 2. CHARGEMENT DES DONNÉES
# =====================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def charger_prix(tickers):
    data = yf.download(list(tickers), period="1y", auto_adjust=True,
                       progress=False, threads=True)
    close, volume = data["Close"], data["Volume"]
    if isinstance(close, pd.Series):
        close, volume = close.to_frame(tickers[0]), volume.to_frame(tickers[0])
    return close.ffill(), volume


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def charger_infos(ticker):
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


def etiqueter(texte):
    texte = texte.lower()
    return [cat for cat, mots in MOTS_CLES.items()
            if any(re.search(r"\b" + re.escape(m) + r"\b", texte) for m in mots)]


@st.cache_data(ttl=1800, show_spinner=False)
def actualites(requete, n=8):
    url = f"https://news.google.com/rss/search?q={quote(requete)}&hl=fr&gl=FR&ceid=FR:fr"
    flux = feedparser.parse(url)
    return [
        {"titre": e.title, "lien": e.link,
         "date": e.get("published", "")[:16], "tags": etiqueter(e.title)}
        for e in flux.entries[:n]
    ]

# =====================================================================
# 3. INDICATEURS ET SCORES
# =====================================================================
def indicateurs(close, volume, bench, etf):
    c = close.dropna()
    if len(c) < 130:
        return None
    r = c.pct_change().dropna()

    def perf(s, n):
        s = s.dropna()
        return s.iloc[-1] / s.iloc[-n - 1] - 1 if len(s) > n else np.nan

    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean().iloc[-1]
    perte = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
    rsi = 100 - 100 / (1 + gain / perte) if perte > 0 else 100

    v = volume.dropna()
    base = v.iloc[-120:-20].mean() if len(v) > 120 else np.nan
    vol_ratio = v.iloc[-20:].mean() / base if base and base > 0 else np.nan

    corr = r.iloc[-126:].corr(etf.pct_change().iloc[-126:])

    return {
        "prix": c.iloc[-1],
        "perf_1m": perf(c, 21), "perf_3m": perf(c, 63), "perf_6m": perf(c, 126),
        "perf_1a": c.iloc[-1] / c.iloc[0] - 1,
        "ma50": c.rolling(50).mean().iloc[-1],
        "ma200": c.rolling(min(200, len(c))).mean().iloc[-1],
        "rsi": rsi,
        "volatilite": r.std() * np.sqrt(252),
        "dist_haut": c.iloc[-1] / c.max() - 1,
        "vol_ratio": vol_ratio,
        "force_rel": perf(c, 126) - perf(bench, 126),
        "perf_theme": perf(etf, 126),
        "corr_theme": corr,
    }


def borne(x):
    return float(np.clip(x, 0, 100))


def score_momentum(i):
    s = 50 + i["perf_6m"] * 60 + i["force_rel"] * 40
    s += 10 if i["prix"] > i["ma200"] else -10
    s += 5 if i["ma50"] > i["ma200"] else -5
    return borne(s)


def score_fondamentaux(f):
    if not f or f.get("revenueGrowth") is None:
        return 50.0
    s = 40
    rg = f.get("revenueGrowth") or 0
    eg = f.get("earningsGrowth")
    gm, pm = f.get("grossMargins"), f.get("profitMargins")
    dte, fpe = f.get("debtToEquity"), f.get("forwardPE")
    s += 25 if rg > 0.3 else 15 if rg > 0.15 else 5 if rg > 0.05 else -15 if rg < 0 else 0
    if eg is not None:
        s += 10 if eg > 0.25 else -10 if eg < 0 else 0
    if gm is not None and gm > 0.5:
        s += 10
    if pm is not None:
        s += 10 if pm > 0.15 else -15 if pm < 0 else 0
    if dte is not None and dte > 200:
        s -= 10
    if fpe is not None:
        s += 5 if 0 < fpe < 30 else -10 if fpe > 80 else 0
    return borne(s)


def score_tendance(i):
    corr = 0 if np.isnan(i["corr_theme"]) else i["corr_theme"]
    pt = 0 if np.isnan(i["perf_theme"]) else i["perf_theme"]
    return borne(50 + corr * 30 + pt * 60)


def score_risque(i, f):
    s = 30 + (i["volatilite"] - 0.3) * 80
    s += 15 if i["rsi"] > 75 else 0
    s += 10 if i["dist_haut"] < -0.30 else 0
    if f:
        pm = f.get("profitMargins")
        if pm is not None and pm < 0:
            s += 15
        fpe = f.get("forwardPE")
        if fpe is not None and fpe > 80:
            s += 10
    return borne(s)


def profil(mom, fond, risque):
    if mom >= 60 and fond >= 60 and risque < 65:
        return "🚀 Croissance solide"
    if mom >= 60 and (fond < 50 or risque >= 65):
        return "🎲 Spéculatif"
    if mom < 50 and fond >= 60:
        return "💎 Solide mais délaissée"
    return "⚖️ À surveiller"

# =====================================================================
# 4. EXPLICATIONS EN FRANÇAIS
# =====================================================================
def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x * 100:+.0f} %"


def explications(nom_theme, i, f):
    pourquoi, vigilance, correl = [], [], []

    pourquoi.append(f"Le cours a progressé de {pct(i['perf_6m'])} en 6 mois "
                    f"(et {pct(i['perf_1a'])} sur 1 an).")
    if i["force_rel"] > 0.1:
        pourquoi.append(f"Elle fait mieux que le marché américain de {pct(i['force_rel'])} sur 6 mois.")
    if i["prix"] > i["ma50"] > i["ma200"]:
        pourquoi.append("La tendance est haussière et installée (cours au-dessus de ses moyennes 50 et 200 jours).")
    if i["vol_ratio"] and not np.isnan(i["vol_ratio"]) and i["vol_ratio"] > 1.3:
        pourquoi.append(f"Les volumes d'échange sont {i['vol_ratio']:.1f}x plus élevés que d'habitude : l'intérêt des investisseurs augmente.")
    if f:
        rg, gm, pm = f.get("revenueGrowth"), f.get("grossMargins"), f.get("profitMargins")
        if rg is not None and rg > 0.15:
            pourquoi.append(f"Le chiffre d'affaires croît de {pct(rg)} : la hausse est soutenue par une vraie activité.")
        if gm is not None and gm > 0.5:
            pourquoi.append(f"Marge brute élevée ({gm * 100:.0f} %), signe d'un produit à forte valeur.")
        if pm is not None and pm > 0.15:
            pourquoi.append(f"L'entreprise est rentable (marge nette {pm * 100:.0f} %).")

    if i["rsi"] > 70:
        vigilance.append(f"RSI à {i['rsi']:.0f} : le titre est en zone de surchauffe, risque de repli à court terme.")
    if i["dist_haut"] < -0.25:
        vigilance.append(f"Le cours est {abs(i['dist_haut']) * 100:.0f} % sous son plus haut annuel.")
    if i["volatilite"] > 0.6:
        vigilance.append(f"Volatilité très élevée ({i['volatilite'] * 100:.0f} % annualisée) : de fortes variations sont normales.")
    if f:
        if (f.get("profitMargins") or 0) < 0:
            vigilance.append("L'entreprise ne gagne pas encore d'argent : la hausse repose sur des promesses.")
        if (f.get("forwardPE") or 0) > 80:
            vigilance.append("Valorisation très élevée par rapport aux bénéfices attendus.")
        if (f.get("debtToEquity") or 0) > 200:
            vigilance.append("Endettement important.")
    vigilance.append(f"Risques de la thématique : {TENDANCES[nom_theme]['risques']}")

    c = i["corr_theme"]
    if not np.isnan(c):
        if c > 0.7:
            correl.append(f"Forte corrélation avec sa thématique ({c:.2f}) : elle monte surtout parce que tout le secteur monte.")
        elif c < 0.4:
            correl.append(f"Faible corrélation avec sa thématique ({c:.2f}) : sa hausse vient surtout de facteurs propres à l'entreprise.")
        else:
            correl.append(f"Corrélation modérée avec sa thématique ({c:.2f}).")
    if not np.isnan(i["perf_theme"]):
        correl.append(f"Le secteur dans son ensemble fait {pct(i['perf_theme'])} sur 6 mois.")
    correl.append(f"Moteur de la thématique : {TENDANCES[nom_theme]['pourquoi']}")

    return pourquoi, vigilance, correl

# =====================================================================
# 5. ANALYSE D'UNE THÉMATIQUE
# =====================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def analyser_theme(nom_theme):
    th = TENDANCES[nom_theme]
    tickers = tuple(th["actions"]) + (th["etf"], BENCH)
    close, volume = charger_prix(tickers)
    if th["etf"] not in close or BENCH not in close:
        return pd.DataFrame(), {}
    lignes, details = [], {}
    for t in th["actions"]:
        if t not in close:
            continue
        i = indicateurs(close[t], volume[t], close[BENCH], close[th["etf"]])
        if i is None:
            continue
        f = charger_infos(t)
        mom, fond = score_momentum(i), score_fondamentaux(f)
        tend, risq = score_tendance(i), score_risque(i, f)
        lignes.append({
            "Ticker": t, "Nom": f.get("shortName", t), "Profil": profil(mom, fond, risq),
            "Momentum": round(mom), "Fondamentaux": round(fond),
            "Tendance": round(tend), "Risque": round(risq),
            "Perf 6m": i["perf_6m"], "Perf 1a": i["perf_1a"],
        })
        details[t] = {"i": i, "f": f, "serie": close[t].dropna()}
    return pd.DataFrame(lignes), details

# =====================================================================
# 6. INTERFACE
# =====================================================================
st.title("📡 Radar Bourse 2.0")
st.caption("Outil d'aide à la décision, pas un conseil en investissement. "
           "Les performances passées ne garantissent pas les performances futures.")

onglets = st.tabs(["🌍 Tendances mondiales", "🔎 Analyse détaillée",
                   "💼 Mon portefeuille", "ℹ️ Aide"])

# ---------------------------------------------------------------- ONGLET 1
with onglets[0]:
    st.subheader("Quelles thématiques portent le marché ?")
    with st.spinner("Calcul des tendances..."):
        resume = []
        for nom, th in TENDANCES.items():
            try:
                cl, _ = charger_prix((th["etf"], BENCH))
                if th["etf"] not in cl or len(cl[th["etf"]].dropna()) < 130:
                    continue
                s = cl[th["etf"]].dropna()
                b = cl[BENCH].dropna()
                resume.append({
                    "Tendance": nom,
                    "Perf 6 mois": s.iloc[-1] / s.iloc[-127] - 1,
                    "Perf 1 an": s.iloc[-1] / s.iloc[0] - 1,
                    "vs S&P 500 (6m)": (s.iloc[-1] / s.iloc[-127] - 1) - (b.iloc[-1] / b.iloc[-127] - 1),
                })
            except Exception:
                continue
    if resume:
        df_res = pd.DataFrame(resume).sort_values("Perf 6 mois", ascending=False)
        fig = px.bar(df_res, x="Perf 6 mois", y="Tendance", orientation="h",
                     color="Perf 6 mois", color_continuous_scale="RdYlGn")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=420)
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_res.style.format({"Perf 6 mois": "{:+.1%}", "Perf 1 an": "{:+.1%}",
                                          "vs S&P 500 (6m)": "{:+.1%}"}),
                     use_container_width=True, hide_index=True)
    else:
        st.warning("Impossible de charger les données pour le moment. Réessayez dans un instant.")

    st.markdown("### Détail d'une thématique")
    choix = st.selectbox("Choisissez une thématique", list(TENDANCES.keys()))
    st.info(f"**Pourquoi elle est portée par le monde actuel :** {TENDANCES[choix]['pourquoi']}")
    st.warning(f"**Risques :** {TENDANCES[choix]['risques']}")

    df_t, _ = analyser_theme(choix)
    if not df_t.empty:
        st.dataframe(
            df_t.sort_values("Momentum", ascending=False).style.format(
                {"Perf 6m": "{:+.0%}", "Perf 1a": "{:+.0%}"}),
            use_container_width=True, hide_index=True)
        st.caption("Momentum = le cours monte-t-il ? • Fondamentaux = l'entreprise gagne-t-elle vraiment de l'argent ? "
                   "• Tendance = le secteur la porte-t-il ? • Risque = plus c'est haut, plus c'est dangereux.")

# ---------------------------------------------------------------- ONGLET 2
with onglets[1]:
    st.subheader("Analyse détaillée d'une entreprise")
    c1, c2 = st.columns(2)
    theme_sel = c1.selectbox("Thématique", list(TENDANCES.keys()), key="th_det")
    ticker_sel = c2.selectbox("Entreprise", TENDANCES[theme_sel]["actions"])

    df_t, details = analyser_theme(theme_sel)
    if ticker_sel in details:
        d = details[ticker_sel]
        i, f, serie = d["i"], d["f"], d["serie"]
        ligne = df_t[df_t["Ticker"] == ticker_sel].iloc[0]

        st.markdown(f"## {ligne['Nom']} ({ticker_sel}) — {ligne['Profil']}")
        m = st.columns(4)
        m[0].metric("Momentum", f"{ligne['Momentum']}/100")
        m[1].metric("Fondamentaux", f"{ligne['Fondamentaux']}/100")
        m[2].metric("Tendance", f"{ligne['Tendance']}/100")
        m[3].metric("Risque", f"{ligne['Risque']}/100")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=serie.index, y=serie, name="Cours"))
        fig.add_trace(go.Scatter(x=serie.index, y=serie.rolling(50).mean(), name="Moyenne 50j"))
        fig.add_trace(go.Scatter(x=serie.index, y=serie.rolling(200).mean(), name="Moyenne 200j"))
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)

        pq, vg, co = explications(theme_sel, i, f)
        a, b, cc = st.columns(3)
        with a:
            st.markdown("#### ✅ Pourquoi ça marche")
            for x in pq:
                st.write("• " + x)
        with b:
            st.markdown("#### ⚠️ Points de vigilance")
            for x in vg:
                st.write("• " + x)
        with cc:
            st.markdown("#### 🔗 Corrélations")
            for x in co:
                st.write("• " + x)

        st.markdown("#### 📰 Actualité récente")
        for n in actualites(f"{ligne['Nom']} bourse"):
            tags = " ".join(n["tags"])
            st.markdown(f"- [{n['titre']}]({n['lien']})  \n  <small>{n['date']} {tags}</small>",
                        unsafe_allow_html=True)

        # --- Analyste IA optionnel (clé à mettre dans les Secrets Streamlit)
        if "ANTHROPIC_API_KEY" in st.secrets:
            if st.button("🤖 Générer une thèse d'investissement par IA"):
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                    prompt = (
                        f"Entreprise : {ligne['Nom']} ({ticker_sel}). Thématique : {theme_sel}.\n"
                        f"Données : perf 6m {pct(i['perf_6m'])}, perf 1 an {pct(i['perf_1a'])}, "
                        f"RSI {i['rsi']:.0f}, volatilité {i['volatilite']:.0%}, "
                        f"croissance CA {f.get('revenueGrowth')}, marge nette {f.get('profitMargins')}.\n"
                        f"Actualités : {[n['titre'] for n in actualites(ligne['Nom'] + ' bourse', 5)]}\n"
                        "Rédige en français une thèse d'investissement courte : pourquoi l'entreprise "
                        "progresse, lien avec les tendances mondiales, risques, et ce qu'il faudrait "
                        "surveiller. Reste factuel, sans promettre de gains."
                    )
                    rep = client.messages.create(
                        model="claude-sonnet-4-5", max_tokens=900,
                        messages=[{"role": "user", "content": prompt}])
                    st.markdown(rep.content[0].text)
                except Exception as e:
                    st.error(f"Erreur IA : {e}")
    else:
        st.warning("Données indisponibles pour cette entreprise.")

# ---------------------------------------------------------------- ONGLET 3
with onglets[2]:
    st.subheader("💼 Mon portefeuille")
    st.caption("Vos données restent dans votre session et ne sont pas enregistrées sur le site.")

    mode = st.radio("Comment ajouter vos positions ?",
                    ["✍️ Saisie manuelle", "📁 Importer un fichier CSV"], horizontal=True)

    if mode.startswith("📁"):
        st.write("Le fichier doit avoir 3 colonnes : `ticker`, `quantite`, `prix_achat`.")
        fichier = st.file_uploader("Fichier CSV", type="csv")
        if fichier is not None:
            try:
                df_p = pd.read_csv(fichier)
                df_p.columns = [c.strip().lower() for c in df_p.columns]
                st.session_state["portefeuille"] = df_p[["ticker", "quantite", "prix_achat"]]
            except Exception:
                st.error("Fichier invalide. Vérifiez les noms de colonnes.")
    else:
        base = st.session_state.get("portefeuille", pd.DataFrame(
            {"ticker": ["NVDA"], "quantite": [1.0], "prix_achat": [100.0]}))
        st.session_state["portefeuille"] = st.data_editor(
            base, num_rows="dynamic", use_container_width=True)

    pf = st.session_state.get("portefeuille")
    if pf is not None and not pf.dropna().empty:
        pf = pf.dropna()
        tickers = tuple(str(t).upper().strip() for t in pf["ticker"])
        try:
            cl, _ = charger_prix(tickers)
            dernier = cl.iloc[-1]
            pf = pf.assign(ticker=list(tickers))
            pf["Prix actuel"] = pf["ticker"].map(dernier)
            pf["Valeur"] = pf["quantite"] * pf["Prix actuel"]
            pf["Gain/Perte"] = pf["Valeur"] - pf["quantite"] * pf["prix_achat"]
            pf["Perf %"] = pf["Prix actuel"] / pf["prix_achat"] - 1

            total = pf["Valeur"].sum()
            gain = pf["Gain/Perte"].sum()
            k = st.columns(2)
            k[0].metric("Valeur totale", f"{total:,.0f}")
            k[1].metric("Gain / perte total", f"{gain:+,.0f}")
            st.dataframe(pf.style.format({"Prix actuel": "{:.2f}", "Valeur": "{:,.0f}",
                                          "Gain/Perte": "{:+,.0f}", "Perf %": "{:+.1%}"}),
                         use_container_width=True, hide_index=True)

            # répartition par tendance
            inverse = {t: nom for nom, th in TENDANCES.items() for t in th["actions"]}
            pf["Tendance"] = pf["ticker"].map(inverse).fillna("Autre")
            rep = pf.groupby("Tendance")["Valeur"].sum().reset_index()
            st.plotly_chart(px.pie(rep, names="Tendance", values="Valeur",
                                   title="Répartition par tendance"),
                            use_container_width=True)

            # alertes
            st.markdown("#### 🚨 Alertes")
            ok = True
            for _, r_ in rep.iterrows():
                if total > 0 and r_["Valeur"] / total > 0.5:
                    st.warning(f"Plus de 50 % de votre portefeuille est concentré sur « {r_['Tendance']} ». "
                               "Pensez à diversifier.")
                    ok = False
            for _, r_ in pf.iterrows():
                if total > 0 and r_["Valeur"] / total > 0.25:
                    st.warning(f"{r_['ticker']} pèse plus de 25 % de votre portefeuille.")
                    ok = False
            if ok:
                st.success("Pas de concentration excessive détectée.")

            # idées à étudier
            st.markdown("#### 💡 Idées à étudier (hors portefeuille)")
            possedes = set(tickers)
            idees = []
            for nom in TENDANCES:
                dft, _ = analyser_theme(nom)
                if dft.empty:
                    continue
                dft = dft[(~dft["Ticker"].isin(possedes)) &
                          (dft["Profil"] == "🚀 Croissance solide")]
                for _, r_ in dft.iterrows():
                    idees.append({"Tendance": nom, **r_.to_dict()})
            if idees:
                df_i = pd.DataFrame(idees).sort_values("Momentum", ascending=False).head(8)
                st.dataframe(df_i[["Ticker", "Nom", "Tendance", "Profil", "Momentum",
                                   "Fondamentaux", "Risque", "Perf 6m"]].style.format(
                    {"Perf 6m": "{:+.0%}"}), use_container_width=True, hide_index=True)
                st.caption("Ce sont des pistes à étudier, pas des recommandations d'achat.")
            else:
                st.info("Aucune idée « Croissance solide » en dehors de votre portefeuille pour l'instant.")
        except Exception as e:
            st.error(f"Impossible de calculer le portefeuille : {e}")

# ---------------------------------------------------------------- ONGLET 4
with onglets[3]:
        st.markdown("""
### Comment lire les scores
- **Momentum** : le cours monte-t-il plus vite que le marché ?
- **Fondamentaux** : croissance, marges, rentabilité, endettement.
- **Tendance** : le secteur entier est-il porteur ?
- **Risque** : plus le chiffre est haut, plus l'investissement est dangereux.

### Les profils
- 🚀 **Croissance solide** : le cours monte ET l'entreprise est saine.
- 🎲 **Spéculatif** : le cours monte mais les fondamentaux sont fragiles.
- 💎 **Solide mais délaissée** : bonne entreprise, cours en retard.
- ⚖️ **À surveiller** : signaux mélangés.

### Importer un CSV
Colonnes : ticker, quantite, prix_achat. Pour les actions européennes, ajoutez le suffixe de la bourse (.PA Paris, .DE Allemagne, .AS Amsterdam).

⚠️ Outil pédagogique : ne constitue pas un conseil en investissement.
""")
