import streamlit as st
import random
from datetime import datetime

st.set_page_config(page_title="Simulateur conseiller bancaire", layout="wide")
st.title("Simulateur de conseil bancaire et patrimonial")
st.write("Aide Léa à gérer son budget, ses investissements et sa fiscalité sur 5 ans.")

if "etat" not in st.session_state:
    st.session_state.etat = {
        "annee": 1,
        "age": 32,
        "salaire": 2600.0,
        "loyer_paye": 0.0,
        "loyers_encaisses": 0.0,
        "credit_immo": 0.0,
        "credit_auto": 0.0,
        "charges": 1500.0,
        "solde": 3250.0,
        "epargne_precaution": 7802.50,
        "patrimoine": 7713.98,
        "risque": 3.5,
        "voiture": False,
        "voiture_obligatoire": False,
        "residence": False,
        "locatif": False,
        "enfant": False,
        "couple": False,
        "prevoyance": None,
        "portefeuille": [],
        "compte_titres": [],
        "pea": [],
        "assurance_vie": [],
        "fiscalite": {"pfu": 0.0, "bareme": 0.0, "plus_values": 0.0},
        "notes": []
    }

s = st.session_state.etat

st.sidebar.header("Situation")
st.sidebar.write(f"Année {s['annee']} | Âge {s['age']}")
st.sidebar.write(f"Salaire : {s['salaire']:.2f} €/mois")
st.sidebar.write(f"Loyer payé : {s['loyer_paye']:.2f} €/mois")
st.sidebar.write(f"Loyers encaissés : {s['loyers_encaisses']:.2f} €/mois")
st.sidebar.write(f"Crédit immo : {s['credit_immo']:.2f} €/mois")
st.sidebar.write(f"Crédit auto : {s['credit_auto']:.2f} €/mois")
st.sidebar.write(f"Charges : {s['charges']:.2f} €/mois")

budget_disponible = (
    s["salaire"]
    + s["loyers_encaisses"]
    - s["loyer_paye"]
    - s["credit_immo"]
    - s["credit_auto"]
    - s["charges"]
)

st.sidebar.write(f"Budget disponible : {budget_disponible:.2f} €/mois")
st.sidebar.write(f"Solde : {s['solde']:.2f} €")
st.sidebar.write(f"Épargne : {s['epargne_precaution']:.2f} €")
st.sidebar.write(f"Patrimoine : {s['patrimoine']:.2f} €")
st.sidebar.write(f"Risque : {s['risque']:.2f}/10")
st.sidebar.write(f"Prévoyance : {s['prevoyance'] or 'Aucune'}")

st.header("Investissement")

types = ["Monétaire", "Fonds euros", "Obligataire", "SCPI", "ETF", "OPCVM"]
type_choisi = st.selectbox("Type", types)

zones = ["France", "Europe", "États-Unis", "Asie", "Émergents", "Monde"]
zone = st.selectbox("Zone", zones)

secteurs = [
    "Diversifié",
    "Technologie",
    "Santé",
    "Énergie",
    "Industrie",
    "Consommation",
    "Finance",
    "Immobilier"
]
secteur = st.selectbox("Secteur", secteurs)

montant = st.number_input("Montant total (€)", min_value=0.0, value=1000.0, step=100.0)

mode = st.radio("Mode", ["Versement unique", "Investissement progressif"])

if mode == "Investissement progressif":
    duree = st.selectbox("Durée (mois)", )[3][6][9][12]
    mensuel = montant / duree
    st.write(f"Versement mensuel : {mensuel:.2f} €")
else:
    mensuel = montant

enveloppe = st.selectbox("Enveloppe", ["compte_titres", "pea", "assurance_vie"])

if st.button("Investir"):
    support = {
        "nom": f"{type_choisi} {zone} {secteur}",
        "type": type_choisi,
        "zone": zone,
        "secteur": secteur,
        "risque": random.randint(1, 8),
        "rend": random.uniform(0.02, 0.09),
        "vol": random.uniform(0.01, 0.22),
        "frais": 0.002
    }

    s["portefeuille"].append({
        "support": support,
        "montant": montant,
        "mensuel": mensuel,
        "enveloppe": enveloppe,
        "annee_achat": s["annee"],
        "date_achat": datetime.now().strftime("%Y-%m-%d")
    })

    s["solde"] -= montant
    s["patrimoine"] += montant
    s["risque"] = round(s["risque"] * 0.8 + support["risque"] * 0.2, 2)

    st.success(
        f"Investissement enregistré : {support['nom']} | {montant:.2f} € | enveloppe {enveloppe}"
    )

st.header("Événement aléatoire")

if st.button("Tirer l'événement"):
    r = random.random()

    if r < 0.55:
        ev = "aucun"
    elif r < 0.60:
        ev = "panne_voiture"
    elif r < 0.63:
        ev = "travaux"
    elif r < 0.67:
        ev = "famille"
    elif r < 0.71:
        ev = "revenus"
    elif r < 0.75:
        ev = "immobilier"
    elif r < 0.79:
        ev = "sante"
    elif r < 0.82:
        ev = "succession"
    elif r < 0.85:
        ev = "impots"
    else:
        ev = "marches"

    st.info(f"Événement tiré : {ev}")

    if ev == "panne_voiture":
        m = random.uniform(500, 2500)
        s["solde"] -= m
        st.write(f"Dépense : {m:.2f} €")

    elif ev == "travaux":
        m = random.uniform(2000, 10000)
        s["solde"] -= m
        st.write(f"Dépense : {m:.2f} €")

    elif ev == "famille":
        m = random.uniform(200, 800)
        s["charges"] += m
        st.write(f"Charges mensuelles +{m:.2f} €")

    elif ev == "revenus":
        m = random.uniform(50, 300)
        s["salaire"] += m
        st.write(f"Salaire +{m:.2f} €/mois")

    elif ev == "immobilier":
        m = random.uniform(500, 3000)
        s["solde"] -= m
        st.write(f"Dépense : {m:.2f} €")

    elif ev == "sante":
        m = random.uniform(300, 2000)
        s["solde"] -= m
        st.write(f"Dépense : {m:.2f} €")

    elif ev == "succession":
        m = random.uniform(3000, 30000)
        s["solde"] += m
        st.write(f"Revenu exceptionnel : +{m:.2f} €")

    elif ev == "impots":
        m = random.uniform(300, 3000)
        s["solde"] -= m
        st.write(f"Dépense : {m:.2f} €")

    elif ev == "marches":
        perf = random.uniform(-0.15, 0.15)
        for p in s["portefeuille"]:
            p["montant"] *= (1 + perf)
        s["patrimoine"] *= (1 + perf * 0.5)
        st.write(f"Variation des marchés : {perf*100:.1f}%")

    else:
        st.write("Aucun événement majeur.")

st.header("Fiscalité")

st.write("Compte-titres : PFU 31,4% ou barème progressif avec abattement et prélèvements sociaux.")
st.write("PEA : abattement après 5 ans.")
st.write("Assurance-vie : fiscalité 30% actuellement.")

pv = sum(
    l["montant"] for l in s["portefeuille"]
    if l["enveloppe"] == "compte_titres"
) * 0.1

st.write(f"Plus-value latente estimée : {pv:.2f} €")

choix = st.radio(
    "Choix fiscal",
    ["PFU 31,4%", "Barème progressif", "PEA", "Assurance-vie"]
)

if st.button("Appliquer la fiscalité"):
    if choix == "PFU 31,4%":
        impot = pv * 0.314
        s["fiscalite"]["pfu"] += impot
        st.success(f"PFU appliqué : {impot:.2f} €")

    elif choix == "Barème progressif":
        duree = 5
        abattement = pv * 0.5 if duree < 8 else pv * 0.65
        pv_net = pv - abattement
        ir = pv_net * 0.128
        ps = pv * 0.172
        bareme = ir + ps
        s["fiscalite"]["bareme"] += bareme
        st.success(f"Barème appliqué : {bareme:.2f} €")

    elif choix == "PEA":
        st.info("PEA : abattement après 5 ans.")

    else:
        impot = pv * 0.30
        s["fiscalite"]["pfu"] += impot
        st.success(f"Assurance-vie : {impot:.2f} €")

st.header("Fin d'année")

if st.button("Passer à l'année suivante"):
    note = 10

    if s["epargne_precaution"] > 10000:
        note += 3
    if s["risque"] < 5:
        note += 2
    if s["prevoyance"]:
        note += 3
    if s["solde"] > 0:
        note += 2

    note = min(note, 20)
    s["notes"].append(note)
    s["annee"] += 1

    st.success(f"Note de l'année : {note}/20")

st.header("Portefeuille")

for p in s["portefeuille"]:
    st.write(
        f"{p['support']['nom']} | {p['montant']:.2f} € | "
        f"enveloppe {p['enveloppe']} | risque {p['support']['risque']}"
    )
