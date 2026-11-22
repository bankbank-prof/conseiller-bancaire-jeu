import copy
import random

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Le conseil patrimonial — Le jeu",
    layout="wide",
)

DUREE = 5
CLE_SESSION = "jeu_patrimonial_profils_v5"

SUPPORTS = {
    "Obligations France": (0.03, 0.04, 3),
    "Obligations émergentes": (0.045, 0.09, 5),
    "Actions monde": (0.06, 0.16, 6),
    "Actions américaines technologie": (0.075, 0.25, 8),
    "Actions européennes santé": (0.05, 0.15, 6),
    "Immobilier papier fictif": (0.04, 0.08, 5),
}

PROFILS = {
    "Camille — Premier emploi": {
        "prenom": "Camille",
        "age": 24,
        "description": "Premier emploi, location et crédit étudiant.",
        "revenu": 2100.0,
        "charges": 850.0,
        "loyer": 650.0,
        "credit": 160.0,
        "dette": 5760.0,
        "mois_credit": 36,
        "courant": 1400.0,
        "livret": 2200.0,
        "positions": {},
        "immobilier": 0.0,
        "parts": 1.0,
        "statut": "Salarié",
        "enfants": 0,
        "objectif": "Préparer un apport immobilier de 15 000 €.",
        "cible": 15000.0,
        "reserve_mois": 3,
        "risque_max": 5,
        "protection_attendue": False,
        "type_objectif": "apport",
    },
    "Léa — Construire son patrimoine": {
        "prenom": "Léa",
        "age": 32,
        "description": "Célibataire, sans enfant, sans loyer ni crédit.",
        "revenu": 2600.0,
        "charges": 1500.0,
        "loyer": 0.0,
        "credit": 0.0,
        "dette": 0.0,
        "mois_credit": 0,
        "courant": 3250.0,
        "livret": 7802.50,
        "positions": {},
        "immobilier": 0.0,
        "parts": 1.0,
        "statut": "Salarié",
        "enfants": 0,
        "objectif": "Accroître son patrimoine net de 30 000 € en cinq ans.",
        "cible": 30000.0,
        "reserve_mois": 3,
        "risque_max": 5,
        "protection_attendue": False,
        "type_objectif": "progression",
    },
    "Sarah et Mehdi — Famille": {
        "prenom": "Sarah et Mehdi",
        "age": 38,
        "age_conjoint": 40,
        "description": "Couple avec deux enfants et résidence principale à crédit.",
        "revenu": 5100.0,
        "charges": 2600.0,
        "loyer": 0.0,
        "credit": 950.0,
        "dette": 171000.0,
        "mois_credit": 180,
        "courant": 4500.0,
        "livret": 10000.0,
        "positions": {"Actions monde": 5000.0},
        "immobilier": 250000.0,
        "parts": 3.0,
        "statut": "Salarié",
        "enfants": 2,
        "objectif": "Conserver une réserve familiale et atteindre 25 000 € sur livret.",
        "cible": 25000.0,
        "reserve_mois": 4,
        "risque_max": 5,
        "protection_attendue": True,
        "type_objectif": "reserve",
    },
    "Thomas — Indépendant": {
        "prenom": "Thomas",
        "age": 46,
        "description": "Revenus variables et besoin de sécurité professionnelle.",
        "revenu": 3400.0,
        "charges": 1700.0,
        "loyer": 750.0,
        "credit": 0.0,
        "dette": 0.0,
        "mois_credit": 0,
        "courant": 5000.0,
        "livret": 9000.0,
        "positions": {
            "Actions monde": 10000.0,
            "Obligations France": 5000.0,
        },
        "immobilier": 0.0,
        "parts": 1.0,
        "statut": "Indépendant",
        "enfants": 0,
        "objectif": "Atteindre une réserve de six mois de dépenses.",
        "cible": 0.0,
        "reserve_mois": 6,
        "risque_max": 5,
        "protection_attendue": True,
        "type_objectif": "securite",
    },
    "Sylvie — Préparer sa retraite": {
        "prenom": "Sylvie",
        "age": 61,
        "description": "Propriétaire sans crédit ; retraite prévue à 63 ans dans ce scénario.",
        "revenu": 3000.0,
        "charges": 1700.0,
        "loyer": 0.0,
        "credit": 0.0,
        "dette": 0.0,
        "mois_credit": 0,
        "courant": 6000.0,
        "livret": 18000.0,
        "positions": {
            "Actions monde": 25000.0,
            "Obligations France": 35000.0,
        },
        "immobilier": 220000.0,
        "parts": 1.0,
        "statut": "Salarié",
        "enfants": 0,
        "objectif": "Préserver le patrimoine et garder 20 000 € sur livret.",
        "cible": 20000.0,
        "reserve_mois": 6,
        "risque_max": 4,
        "protection_attendue": False,
        "type_objectif": "retraite",
    },
}

TRANCHES = [
    (11600.0, 0.00),
    (29579.0, 0.11),
    (84577.0, 0.30),
    (181917.0, 0.41),
    (float("inf"), 0.45),
]


def euros(x):
    return (
        f"{x:,.2f}".replace(",", " ").replace(".", ",")
        + " €"
    )


def placements(s):
    return sum(p["valeur"] for p in s["positions"].values())


def financier(s):
    return s["courant"] + s["livret"] + placements(s)


def patrimoine_net(s):
    return financier(s) + s["immobilier"] - s["dette"]


def depenses_fixes(s):
    return s["charges"] + s["loyer"] + s["credit"]


def risque(s):
    total = placements(s)
    if total <= 0:
        return 0.0
    return sum(
        p["valeur"] * SUPPORTS[n][2]
        for n, p in s["positions"].items()
    ) / total


def commencer(nom):
    p = copy.deepcopy(PROFILS[nom])
    p["profil"] = nom
    p["annee"] = 1
    p["bilans"] = []
    p["positions"] = {
        n: {"valeur": montant, "capital": montant}
        for n, montant in p["positions"].items()
    }
    p["reglages"] = {
        "livret": 0.0,
        "versements": {n: 0.0 for n in SUPPORTS},
        "protection": 0,
        "option": "PFU fictif",
    }
    p["net_initial"] = patrimoine_net(p)
    p["retraite_appliquee"] = False
    return p


def calcul_ir(base, parts):
    quotient = max(0.0, base) / parts
    bas = 0.0
    impot_part = 0.0
    lignes = []

    for haut, taux in TRANCHES:
        taxable = max(0.0, min(quotient, haut) - bas)
        montant = taxable * taux
        lignes.append({
            "Tranche par part": (
                f"Au-delà de {bas:,.0f}"
                if haut == float("inf")
                else f"{bas:,.0f} à {haut:,.0f}"
            ),
            "Taux (%)": taux * 100,
            "Base par part (€)": taxable,
            "Impôt par part (€)": montant,
        })
        impot_part += montant
        bas = haut

    brut = impot_part * parts

    # Modèle volontairement simplifié :
    # pas de décote ni de plafonnement du quotient familial.
    return {
        "base": base,
        "parts": parts,
        "quotient": quotient,
        "brut": brut,
        "net": brut,
        "details": lignes,
    }


def fiscalite(revenus, gain, parts, option):
    abattement = revenus * 0.10
    base = max(0.0, revenus - abattement)
    ir_revenus = calcul_ir(base, parts)
    gain_taxable = max(0.0, gain)
    ir_total_bareme = calcul_ir(base + gain_taxable, parts)
    supplement = max(
        0.0,
        ir_total_bareme["net"] - ir_revenus["net"],
    )
    pfu = gain_taxable * 0.30
    sociaux = gain_taxable * 0.172
    bareme = supplement + sociaux
    retenu = pfu if option == "PFU fictif" else bareme

    return {
        "revenus": revenus,
        "abattement": abattement,
        "base": base,
        "ir_revenus": ir_revenus,
        "gain": gain,
        "gain_taxable": gain_taxable,
        "ir_total_bareme": ir_total_bareme,
        "supplement": supplement,
        "sociaux": sociaux,
        "pfu": pfu,
        "bareme": bareme,
        "option": option,
        "impot_placements": retenu,
        "total": ir_revenus["net"] + retenu,
    }


def verser(s, nom, montant):
    if montant <= 0:
        return
    p = s["positions"].setdefault(
        nom, {"valeur": 0.0, "capital": 0.0}
    )
    p["valeur"] += montant
    p["capital"] += montant


def scenario_annuel(s):
    t = copy.deepcopy(s)
    messages = []

    if (
        t["prenom"] == "Sylvie"
        and t["age"] >= 63
        and not t["retraite_appliquee"]
    ):
        t["revenu"] = 2200.0
        t["statut"] = "Retraité"
        t["retraite_appliquee"] = True
        messages.append(
            "Départ à la retraite prévu dans ce scénario : "
            "revenu mensuel ramené à 2 200 € avant IR."
        )

    if (
        t["prenom"] == "Sarah et Mehdi"
        and t["annee"] == 3
    ):
        t["charges"] += 200.0
        messages.append(
            "Évolution prévue : dépenses familiales "
            "supplémentaires de 200 € par mois."
        )

    return t, messages


def simuler(s, vl, versements, protection, option, vente_pct):
    t, messages = scenario_annuel(s)
    debut = patrimoine_net(t)

    actifs_debut = {
        "Compte courant": t["courant"],
        "Livret": t["livret"],
        "Placements": placements(t),
        "Immobilier": t["immobilier"],
        "Dette restante": t["dette"],
        "Patrimoine net": debut,
    }

    fraction = vente_pct / 100
    produit = placements(t) * fraction
    gain_realise = sum(
        (p["valeur"] - p["capital"]) * fraction
        for p in t["positions"].values()
    )

    for p in t["positions"].values():
        p["valeur"] *= 1 - fraction
        p["capital"] *= 1 - fraction

    t["positions"] = {
        n: p for n, p in t["positions"].items()
        if p["valeur"] > 0.001
    }
    t["courant"] += produit

    choix = ["Aucun événement majeur", "Dépense imprévue"]
    poids = [65, 15]

    if t["statut"] == "Indépendant":
        choix += ["Baisse d'activité", "Bonne activité"]
        poids += [12, 8]
    elif t["statut"] == "Salarié":
        choix += ["Augmentation", "Arrêt de travail"]
        poids += [10, 10]
    else:
        choix += ["Dépense de santé"]
        poids += [20]

    evenement = random.choices(choix, weights=poids, k=1)[0]
    mois_evt = random.randint(1, 12)
    revenus = [t["revenu"]] * 12
    depenses_exceptionnelles = [0.0] * 12
    indemnites = [0.0] * 12

    if evenement == "Dépense imprévue":
        depenses_exceptionnelles[mois_evt - 1] = float(
            random.randint(500, 2500)
        )

    elif evenement == "Dépense de santé":
        depenses_exceptionnelles[mois_evt - 1] = float(
            random.randint(1000, 4000)
        )

    elif evenement == "Augmentation":
        hausse = float(random.randint(50, 150))
        for i in range(mois_evt - 1, 12):
            revenus[i] += hausse
        t["revenu"] += hausse
        messages.append(
            f"Augmentation de {euros(hausse)} par mois "
            f"à partir du mois {mois_evt}."
        )

    elif evenement == "Bonne activité":
        for i in range(mois_evt - 1, min(12, mois_evt + 2)):
            revenus[i] *= 1.25

    elif evenement == "Baisse d'activité":
        for i in range(mois_evt - 1, min(12, mois_evt + 2)):
            revenus[i] *= 0.65

    elif evenement == "Arrêt de travail":
        couverture = {0: 0.0, 20: 0.50, 40: 0.80}[protection]
        for i in range(mois_evt - 1, min(12, mois_evt + 1)):
            perte = revenus[i] * 0.50
            revenus[i] -= perte
            indemnites[i] = perte * couverture

    f = fiscalite(
        sum(revenus),
        gain_realise,
        t["parts"],
        option,
    )

    # Paiement lissé de l'impôt annuel connu de la simulation.
    ir_mensuel = f["ir_revenus"]["net"] / 12

    performances = {
        n: max(-0.70, min(0.70, random.gauss(v[0], v[1])))
        for n, v in SUPPORTS.items()
    }

    lignes = []
    gain_marche = 0.0
    interets = 0.0
    capital_rembourse = 0.0
    programme = vl + sum(versements.values())

    for mois in range(1, 13):
        i = mois - 1
        ouverture = t["courant"]

        remboursement_credit = (
            min(t["credit"], t["dette"])
            if t["mois_credit"] > 0 else 0.0
        )
        t["dette"] -= remboursement_credit
        capital_rembourse += remboursement_credit

        if t["mois_credit"] > 0:
            t["mois_credit"] -= 1

        if t["mois_credit"] == 0 or t["dette"] <= 0.001:
            t["credit"] = 0.0
            t["dette"] = max(0.0, t["dette"])

        impot_placements = f["impot_placements"] if mois == 1 else 0.0

        t["courant"] += (
            revenus[i]
            + indemnites[i]
            - t["charges"]
            - t["loyer"]
            - remboursement_credit
            - protection
            - ir_mensuel
            - impot_placements
            - depenses_exceptionnelles[i]
        )

        execute = t["courant"] >= programme
        reel_livret = vl if execute else 0.0
        reel_placements = sum(versements.values()) if execute else 0.0

        if execute:
            t["courant"] -= programme
            t["livret"] += vl
            for nom, montant in versements.items():
                verser(t, nom, montant)

        secours = min(t["livret"], max(0.0, -t["courant"]))
        t["livret"] -= secours
        t["courant"] += secours

        il = t["livret"] * (1.02 ** (1 / 12) - 1)
        t["livret"] += il
        interets += il

        gp = 0.0
        for nom, p in t["positions"].items():
            variation = p["valeur"] * (
                (1 + performances[nom]) ** (1 / 12) - 1
            )
            p["valeur"] += variation
            gp += variation

        gain_marche += gp

        lignes.append({
            "Mois": mois,
            "Courant ouverture": ouverture,
            "Revenus avant IR": revenus[i],
            "Indemnité fictive": indemnites[i],
            "Charges": t["charges"],
            "Loyer": t["loyer"],
            "Crédit payé": remboursement_credit,
            "Protection": protection,
            "IR revenus": ir_mensuel,
            "Impôt placements": impot_placements,
            "Dépense exceptionnelle": depenses_exceptionnelles[i],
            "Virement livret": reel_livret,
            "Investissements": reel_placements,
            "Retrait de secours": secours,
            "Courant clôture": t["courant"],
            "Intérêts livret": il,
            "Gains placements": gp,
            "Livret": t["livret"],
            "Placements": placements(t),
            "Dette restante": t["dette"],
            "Patrimoine net": patrimoine_net(t),
            "Virements suspendus": not execute,
        })

    df = pd.DataFrame(lignes)
    reserve_cible = t["reserve_mois"] * depenses_fixes(t)
    risque_final = risque(t)

    actifs = [
        p["valeur"] for p in t["positions"].values()
        if p["valeur"] > 0.01
    ]
    diversification = (
        len(actifs) >= 2 and max(actifs) / sum(actifs) <= 0.75
    )

    progression_attendue = (
        t["cible"] * t["annee"] / DUREE
    )

    if t["type_objectif"] == "apport":
        objectif_ok = t["livret"] >= progression_attendue
    elif t["type_objectif"] == "progression":
        objectif_ok = (
            patrimoine_net(t) - t["net_initial"]
            >= progression_attendue
        )
    elif t["type_objectif"] == "reserve":
        objectif_ok = (
            t["livret"] >= t["cible"]
            and protection > 0
        )
    elif t["type_objectif"] == "securite":
        objectif_ok = (
            t["livret"] >= reserve_cible
            and protection > 0
        )
    else:
        objectif_ok = (
            t["livret"] >= t["cible"]
            and patrimoine_net(t) >= t["net_initial"] * 0.95
        )

    strategie_ok = (
        protection > 0
        if t["protection_attendue"]
        else (
            diversification
            if t["type_objectif"] == "progression"
            else t["livret"] >= reserve_cible
        )
    )

    criteres = {
        "Réserve adaptée au client": (
            4 if t["livret"] >= reserve_cible else 0
        ),
        "Absence de découvert mensuel": (
            4 if df["Courant clôture"].min() >= 0 else 0
        ),
        "Risque compatible avec le client": (
            4 if risque_final <= t["risque_max"] else 0
        ),
        "Avancement de l'objectif personnel": (
            4 if objectif_ok else 0
        ),
        "Stratégie adaptée : protection ou diversification": (
            4 if strategie_ok else 0
        ),
    }

    flux_financiers = (
        sum(revenus)
        + sum(indemnites)
        - t["charges"] * 12
        - t["loyer"] * 12
        - capital_rembourse
        - protection * 12
        - f["total"]
        - sum(depenses_exceptionnelles)
    )

    fin = patrimoine_net(t)
    rapprochement = (
        debut
        + flux_financiers
        + capital_rembourse
        + interets
        + gain_marche
    )

    actifs_fin = {
        "Compte courant": t["courant"],
        "Livret": t["livret"],
        "Placements": placements(t),
        "Immobilier": t["immobilier"],
        "Dette restante": t["dette"],
        "Patrimoine net": fin,
    }

    t["bilans"].append({
        "annee": t["annee"],
        "age_debut": t["age"],
        "age_fin": t["age"] + 1,
        "messages": messages,
        "evenement": evenement,
        "mois_evenement": mois_evt,
        "mensuel": lignes,
        "fiscalite": f,
        "debut": debut,
        "fin": fin,
        "actifs_debut": actifs_debut,
        "actifs_fin": actifs_fin,
        "produit_ventes": produit,
        "interets": interets,
        "gains": gain_marche,
        "flux_financiers": flux_financiers,
        "capital_rembourse": capital_rembourse,
        "ecart": fin - rapprochement,
        "reserve_cible": reserve_cible,
        "risque": risque_final,
        "criteres": criteres,
        "note": sum(criteres.values()),
        "performances": [
            {
                "Support": n,
                "Performance simulée sur 12 mois (%)": v * 100,
                "Risque /10": SUPPORTS[n][2],
            }
            for n, v in performances.items()
        ],
    })

    t["reglages"] = {
        "livret": vl,
        "versements": dict(versements),
        "protection": protection,
        "option": option,
    }
    t["age"] += 1
    if "age_conjoint" in t:
        t["age_conjoint"] += 1
    t["annee"] += 1
    return t


if CLE_SESSION not in st.session_state:
    st.session_state[CLE_SESSION] = None

st.title("Conseiller bancaire et patrimonial")
st.write(
    "Choisis un client, construis sa stratégie et accompagne-le "
    "pendant cinq années."
)

with st.expander("Règles et limites pédagogiques"):
    st.write(
        "Tous les personnages et contrats sont fictifs. "
        "Les revenus sont disponibles après cotisations sociales, "
        "mais avant impôt sur le revenu. Ce ne sont pas des salaires bruts."
    )
    st.write(
        "Le revenu disponible avant IR est supposé égal au revenu "
        "fiscal avant abattement. Cette égalité est une simplification."
    )
    st.write(
        "Fiscalité pédagogique commune : abattement forfaitaire "
        "de 10 % sur tous les revenus professionnels ou de retraite, "
        "sans minimum ni plafond. Pour Thomas, il s'agit d'une "
        "convention de jeu, pas du calcul fiscal réel d'un indépendant."
    )
    st.write(
        "Le barème de référence est figé : seuils de 11 600 €, "
        "29 579 €, 84 577 € et 181 917 €, avec taux de "
        "0 %, 11 %, 30 %, 41 % et 45 %. "
        "Pas de décote, de plafonnement du quotient familial, "
        "de frais réels, de crédits ni de réductions d'impôt. "
        "L'impôt affiché n'est donc pas l'impôt réel du foyer."
    )
    st.write(
        "Les revenus annuels réellement simulés servent au calcul. "
        "L'impôt sur ces revenus est réparti également sur les douze "
        "mois : le calendrier réel du prélèvement à la source "
        "et de sa régularisation n'est pas reproduit."
    )
    st.write(
        "Placements fictifs : PFU de 30 % ou supplément d'impôt "
        "au barème avec 17,2 % de prélèvements simulés sur les gains "
        "réalisés positifs. Pas de report des pertes. "
        "Aucun régime réel PEA, assurance-vie ou SCPI n'est modélisé."
    )
    st.write(
        "Livret fictif : rendement annuel de 2 %, sans impôt. "
        "Les autres rendements sont aléatoires, capitalisés, "
        "sans frais, revenus distribués ni contrainte de revente."
    )
    st.write(
        "Crédits simplifiés à taux zéro : chaque paiement réduit "
        "la dette du même montant. L'immobilier reste à valeur "
        "constante. Il n'est pas possible de l'acheter ou de le vendre."
    )
    st.write(
        "Protection fictive : 20 € ou 40 € par mois pour couvrir "
        "50 % ou 80 % de la perte simulée lors d'un arrêt de travail. "
        "Pas d'indemnisation de la baisse d'activité ou des dépenses "
        "de santé. Les indemnités sont non imposables par convention."
    )
    st.write(
        "La retraite de Sylvie à 63 ans est un événement fixé "
        "pour le scénario, pas une affirmation sur ses droits réels. "
        "Les frais familiaux du couple augmentent en année 3."
    )
    st.write(
        "La note est une grille pédagogique, pas une mesure "
        "professionnelle de la qualité d'un conseil. "
        "La session n'est pas une sauvegarde permanente."
    )

s = st.session_state[CLE_SESSION]

if s is None:
    st.header("Choisir le client")

    noms = list(PROFILS)

    if "profil_selectionne_v5" not in st.session_state:
        st.session_state.profil_selectionne_v5 = noms[0]

    if st.button("Tirer un profil au hasard"):
        st.session_state.profil_selectionne_v5 = random.choice(noms)

    nom = st.selectbox(
        "Profil de départ",
        noms,
        key="profil_selectionne_v5",
    )

    p = PROFILS[nom]
    temporaire = commencer(nom)

    st.subheader(nom)
    st.write(p["description"])
    st.write(f"Âge : {p['age']} ans")
    if "age_conjoint" in p:
        st.write(f"Âge du conjoint : {p['age_conjoint']} ans")
    st.write(f"Statut : {p['statut']}")
    st.write(f"Enfants : {p['enfants']}")
    st.write(f"Parts fiscales du scénario : {p['parts']}")
    st.write(f"Revenus mensuels avant IR : {euros(p['revenu'])}")
    st.write(f"Charges hors loyer et crédit : {euros(p['charges'])}")
    st.write(f"Loyer mensuel : {euros(p['loyer'])}")
    st.write(f"Mensualité de crédit : {euros(p['credit'])}")
    st.write(f"Dette restante : {euros(p['dette'])}")
    st.write(f"Livret : {euros(p['livret'])}")
    st.write(f"Placements : {euros(placements(temporaire))}")
    st.write(f"Patrimoine net : {euros(patrimoine_net(temporaire))}")
    st.write(f"Objectif : {p['objectif']}")
    st.write(f"Risque maximal souhaité : {p['risque_max']}/10")

    if st.button("Commencer la partie", type="primary"):
        st.session_state[CLE_SESSION] = commencer(nom)
        st.rerun()

    st.stop()

with st.sidebar:
    st.header(s["prenom"])
    st.write(f"Âge : {s['age']} ans")
    if "age_conjoint" in s:
        st.write(f"Conjoint : {s['age_conjoint']} ans")
    st.write(f"Statut actuel : {s['statut']}")
    st.write(f"Année : {min(s['annee'], DUREE)} / {DUREE}")
    st.write(f"Revenus avant IR : {euros(s['revenu'])}/mois")
    st.write(f"Loyer : {euros(s['loyer'])}/mois")
    st.write(f"Crédit : {euros(s['credit'])}/mois")
    st.write(f"Dette : {euros(s['dette'])}")
    st.write(s["objectif"])

    if st.button("Changer de client / Nouvelle partie"):
        st.session_state[CLE_SESSION] = None
        st.rerun()

cols = st.columns(5)
valeurs = [
    ("Compte courant", s["courant"]),
    ("Livret", s["livret"]),
    ("Placements", placements(s)),
    ("Dette", s["dette"]),
    ("Patrimoine net", patrimoine_net(s)),
]
for col, (libelle, montant) in zip(cols, valeurs):
    col.metric(libelle, euros(montant))

if s["annee"] <= DUREE:
    prevision, messages = scenario_annuel(s)
    reg = s["reglages"]
    cle = str(s["annee"])

    st.header(
        f"Année {s['annee']} — {s['prenom']} — {s['age']} ans"
    )

    for message in messages:
        st.info(message)

    st.subheader("1. Protection")
    protection = st.selectbox(
        "Cotisation mensuelle de protection (€)",
        [0, 20, 40],
        index=[0, 20, 40].index(reg["protection"]),
        key="protection_" + cle,
    )

    st.caption(
        "0 € : aucune couverture ; 20 € : indemnisation de 50 % ; "
        "40 € : indemnisation de 80 % de la perte simulée "
        "en cas d'arrêt de travail. Contrat fictif."
    )
    if prevision["statut"] == "Retraité":
        st.info(
            "Le scénario de retraite ne tire pas d'arrêt de travail : "
            "ce contrat ne protège donc pas contre les événements "
            "proposés à ce client."
        )
    elif prevision["statut"] == "Indépendant":
        st.info(
            "Ce contrat ne couvre pas la baisse d'activité. "
            "La réserve de trésorerie est essentielle dans ce scénario."
        )

    st.subheader("2. Versements mensuels")

    vl = st.number_input(
        "Livret — montant par mois (€)",
        min_value=0.0,
        value=float(reg["livret"]),
        step=10.0,
        key="livret_" + cle,
    )

    versements = {}
    for nom_support in SUPPORTS:
        versements[nom_support] = st.number_input(
            nom_support + " — montant par mois (€)",
            min_value=0.0,
            value=float(reg["versements"][nom_support]),
            step=10.0,
            key=cle + "_" + nom_support,
        )

    f_prevu = fiscalite(
        prevision["revenu"] * 12,
        0.0,
        prevision["parts"],
        "PFU fictif",
    )
    ir_prevu = f_prevu["ir_revenus"]["net"] / 12

    capacite = (
        prevision["revenu"]
        - depenses_fixes(prevision)
        - protection
        - ir_prevu
    )
    programme = vl + sum(versements.values())

    c1, c2, c3 = st.columns(3)
    c1.metric("IR mensuel estimé", euros(ir_prevu))
    c2.metric("Capacité d'épargne prévue", euros(capacite))
    c3.metric("Versements prévus", euros(programme))

    st.write(
        "Reste mensuel prévisionnel après versements : "
        + euros(capacite - programme)
    )

    st.caption(
        "Les virements sont réalisés mois par mois après les revenus "
        "et les dépenses. Un événement peut modifier la trésorerie. "
        "Si le programme complet est impossible, les virements "
        "du mois sont suspendus."
    )

    st.subheader("3. Ventes et fiscalité")
    vente_pct = st.slider(
        "Part de chaque placement existant à vendre en début d'année (%)",
        0, 100, 0, 10,
        key="vente_" + cle,
    )

    options = ["PFU fictif", "Barème fictif"]
    option = st.radio(
        "Option fiscale des gains réalisés",
        options,
        index=options.index(reg["option"]),
        key="option_" + cle,
    )

    if st.button(
        "Valider et simuler les douze mois",
        type="primary",
    ):
        if programme > max(0.0, capacite):
            st.error(
                "Les versements dépassent la capacité mensuelle "
                "prévisionnelle après impôt et protection."
            )
        else:
            st.session_state[CLE_SESSION] = simuler(
                s, vl, versements, protection, option, vente_pct
            )
            st.rerun()

st.header("Portefeuille actuel")

if s["positions"]:
    st.dataframe(
        pd.DataFrame([
            {
                "Support": n,
                "Capital restant investi (€)": p["capital"],
                "Valeur (€)": p["valeur"],
                "Gain latent (€)": p["valeur"] - p["capital"],
                "Risque /10": SUPPORTS[n][2],
            }
            for n, p in s["positions"].items()
        ]).round(2),
        hide_index=True,
        use_container_width=True,
    )
else:
    st.write("Aucun placement pour le moment.")

st.header("Synthèses annuelles")

if not s["bilans"]:
    st.write("La synthèse apparaîtra après la première année.")

else:
    recap = pd.DataFrame([
        {
            "Année": b["annee"],
            "Âge fin": b["age_fin"],
            "Patrimoine net (€)": b["fin"],
            "Intérêts livret (€)": b["interets"],
            "Gains placements (€)": b["gains"],
            "IR revenus (€)": b["fiscalite"]["ir_revenus"]["net"],
            "Impôt placements (€)": b["fiscalite"]["impot_placements"],
            "Note /20": b["note"],
        }
        for b in s["bilans"]
    ])

    st.dataframe(
        recap.round(2),
        hide_index=True,
        use_container_width=True,
    )

    evolution = [{
        "Année": 0,
        "Patrimoine net": s["bilans"][0]["debut"],
    }] + [
        {"Année": b["annee"], "Patrimoine net": b["fin"]}
        for b in s["bilans"]
    ]
    st.line_chart(pd.DataFrame(evolution).set_index("Année"))

    st.download_button(
        "Exporter la synthèse annuelle CSV",
        recap.to_csv(
            index=False, sep=";", decimal=","
        ).encode("utf-8-sig"),
        file_name="synthese_annuelle.csv",
        mime="text/csv",
    )

    for b in reversed(s["bilans"]):
        titre = (
            f"Année {b['annee']} — "
            f"{b['age_debut']} à {b['age_fin']} ans — "
            f"{b['note']}/20"
        )

        with st.expander(
            titre,
            expanded=b["annee"] == s["bilans"][-1]["annee"],
        ):
            df = pd.DataFrame(b["mensuel"])
            f = b["fiscalite"]

            st.subheader("Situation et événements")
            for message in b["messages"]:
                st.write(message)
            st.write(f"Événement : {b['evenement']}.")
            if b["evenement"] != "Aucun événement majeur":
                st.write(f"Début de l'événement : mois {b['mois_evenement']}.")

            st.subheader("Budget annuel")

            budget = pd.DataFrame([
                ["Revenus avant IR", df["Revenus avant IR"].sum()],
                ["Indemnités fictives", df["Indemnité fictive"].sum()],
                ["Charges", df["Charges"].sum()],
                ["Loyers", df["Loyer"].sum()],
                ["Crédit remboursé", df["Crédit payé"].sum()],
                ["Protection", df["Protection"].sum()],
                ["IR sur les revenus", f["ir_revenus"]["net"]],
                ["Impôt des placements", f["impot_placements"]],
                ["Dépenses exceptionnelles", df["Dépense exceptionnelle"].sum()],
                ["Flux financiers nets", b["flux_financiers"]],
                ["Versements livret", df["Virement livret"].sum()],
                ["Versements placements", df["Investissements"].sum()],
                ["Retraits de secours", df["Retrait de secours"].sum()],
            ], columns=["Poste", "Montant (€)"])

            st.dataframe(
                budget.round(2),
                hide_index=True,
                use_container_width=True,
            )

            st.caption(
                "Les versements entre comptes sont des transferts internes. "
                "Ils ne réduisent pas le patrimoine total. "
                "Le crédit réduit le compte courant mais aussi la dette."
            )

            st.subheader("Calcul de l'impôt pédagogique")

            st.write(
                f"1. Revenus annuels avant IR : {euros(f['revenus'])}."
            )
            st.write(
                f"2. Abattement conventionnel de 10 % : "
                f"{euros(f['abattement'])}."
            )
            st.write(
                f"3. Base imposable du modèle : {euros(f['base'])}."
            )
            st.write(
                f"4. Nombre de parts : {f['ir_revenus']['parts']}."
            )
            st.write(
                f"5. Revenu par part : "
                f"{euros(f['ir_revenus']['quotient'])}."
            )

            st.dataframe(
                pd.DataFrame(
                    f["ir_revenus"]["details"]
                ).round(2),
                hide_index=True,
                use_container_width=True,
            )

            st.write(
                "6. Total de l'impôt par part × nombre de parts : "
                f"{euros(f['ir_revenus']['net'])}."
            )
            st.write(
                "7. Prélèvement mensuel lissé du modèle : "
                f"{euros(f['ir_revenus']['net'] / 12)}."
            )
            st.caption(
                "Pas de décote ni de plafonnement du quotient familial : "
                "ce montant ne constitue pas une estimation fiscale complète."
            )

            st.subheader("Fiscalité fictive des placements")
            st.write(
                f"Produit des ventes : {euros(b['produit_ventes'])}."
            )
            st.write(
                f"Gain net réalisé : {euros(f['gain'])}."
            )
            st.write(
                f"Base taxable positive : {euros(f['gain_taxable'])}."
            )
            st.write(
                f"PFU fictif : base × 30 % = {euros(f['pfu'])}."
            )
            st.write(
                "Barème fictif : IR après ajout des gains "
                f"{euros(f['ir_total_bareme']['net'])} "
                "− IR sur les revenus seuls "
                f"{euros(f['ir_revenus']['net'])} "
                f"= supplément de {euros(f['supplement'])}."
            )
            st.write(
                "Prélèvements simulés : base × 17,2 % = "
                f"{euros(f['sociaux'])}."
            )
            st.write(
                f"Total au barème fictif : {euros(f['bareme'])}."
            )
            st.write(
                f"Choix retenu : {f['option']} — "
                f"{euros(f['impot_placements'])}."
            )
            st.write(
                f"Total fiscal annuel du modèle : {euros(f['total'])}."
            )
            st.caption(
                "Sans vente, pas de gain réalisé taxé dans le modèle. "
                "Les régimes réels des enveloppes fiscales ne sont pas calculés."
            )

            st.subheader("Synthèse patrimoniale")
            patrimoine_table = pd.DataFrame([
                {
                    "Poste": nom,
                    "Début (€)": b["actifs_debut"][nom],
                    "Fin (€)": b["actifs_fin"][nom],
                    "Variation (€)": (
                        b["actifs_fin"][nom] - b["actifs_debut"][nom]
                    ),
                }
                for nom in b["actifs_debut"]
            ])

            st.dataframe(
                patrimoine_table.round(2),
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                "Patrimoine net = compte courant + livret + placements "
                "+ immobilier − dette restante."
            )

            st.line_chart(
                df.set_index("Mois")[
                    ["Courant clôture", "Livret", "Placements", "Patrimoine net"]
                ]
            )

            st.subheader("Rendement et formation du patrimoine")
            st.write(f"Intérêts du livret : {euros(b['interets'])}.")
            st.write(f"Gains ou pertes des placements : {euros(b['gains'])}.")

            st.dataframe(
                pd.DataFrame(b["performances"]).round(2),
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                "Ces performances sont celles des supports sur douze mois. "
                "Les versements progressifs ne restent pas tous investis "
                "pendant une année complète."
            )

            st.bar_chart(
                pd.DataFrame({
                    "Origine": [
                        "Flux financiers nets",
                        "Réduction de dette",
                        "Intérêts livret",
                        "Gains placements",
                    ],
                    "Montant (€)": [
                        b["flux_financiers"],
                        b["capital_rembourse"],
                        b["interets"],
                        b["gains"],
                    ],
                }).set_index("Origine")
            )

            st.write(
                f"Patrimoine initial {euros(b['debut'])} "
                f"+ flux financiers nets {euros(b['flux_financiers'])} "
                f"+ réduction de dette {euros(b['capital_rembourse'])} "
                f"+ intérêts {euros(b['interets'])} "
                f"+ gains/pertes {euros(b['gains'])} "
                f"= patrimoine final {euros(b['fin'])}."
            )
            st.write(
                f"Écart de rapprochement comptable : {euros(b['ecart'])}."
            )
            st.caption(
                "L'augmentation du patrimoine inclut l'épargne issue "
                "des revenus : ce n'est pas un taux de rendement."
            )

            st.subheader("Détail mensuel")
            st.dataframe(
                df.round(2),
                hide_index=True,
                use_container_width=True,
            )
            st.write(
                "Mois avec virements suspendus : "
                f"{int(df['Virements suspendus'].sum())}."
            )

            st.subheader("Évaluation adaptée au client")
            st.write(
                f"Réserve cible : {euros(b['reserve_cible'])}."
            )
            st.write(
                f"Risque moyen des placements : {b['risque']:.1f}/10."
            )
            for critere, points in b["criteres"].items():
                st.write(f"{critere} : {points}/4")
            st.write(f"Note annuelle : {b['note']}/20.")

            st.download_button(
                "Exporter le détail mensuel CSV",
                df.to_csv(
                    index=False, sep=";", decimal=","
                ).encode("utf-8-sig"),
                file_name=f"annee_{b['annee']}.csv",
                mime="text/csv",
                key=f"export_{b['annee']}",
            )

if s["annee"] > DUREE:
    moyenne = sum(b["note"] for b in s["bilans"]) / DUREE
    st.success(
        f"Partie terminée — {s['prenom']} — "
        f"moyenne : {moyenne:.1f}/20."
    )
