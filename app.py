import copy
import json
import random

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Oak & Ledger — Conseil patrimonial",
    layout="wide",
)

KEY = "oak_ledger_v1"

SUPPORTS = {
    "Obligations diversifiées": (0.03, 0.05, 3),
    "Obligations émergentes": (0.045, 0.10, 5),
    "Actions monde": (0.06, 0.17, 6),
    "Actions technologie": (0.075, 0.26, 8),
    "Actions santé": (0.05, 0.16, 6),
}

TRANCHES = [
    (11600.0, 0.00),
    (29579.0, 0.11),
    (84577.0, 0.30),
    (181917.0, 0.41),
    (float("inf"), 0.45),
]

CSS = """
<style>
.stApp {
    background: #f4f0e6;
    color: #24372d;
}
h1, h2, h3 {
    font-family: Georgia, 'Times New Roman', serif !important;
    color: #203e30 !important;
}
[data-testid="stSidebar"] {
    background: #e4e5d8;
    border-right: 3px solid #aa8b55;
}
.stButton > button {
    background: #244533;
    color: #fff9e9;
    border: 1px solid #ad925e;
    border-radius: 4px;
}
.stButton > button:hover {
    background: #623c42;
    color: white;
    border-color: #ad925e;
}
[data-testid="stMetric"] {
    background: #fffcf3;
    padding: 14px;
    border-top: 3px solid #a68a53;
    border-radius: 4px;
}
.banner {
    padding: 24px;
    border: 1px solid #ac915b;
    color: #fff9e8;
    background-color: #213e30;
    background-image:
        repeating-linear-gradient(
            90deg,
            transparent 0px,
            transparent 37px,
            #a88a4d33 38px,
            #a88a4d33 40px
        ),
        repeating-linear-gradient(
            0deg,
            transparent 0px,
            transparent 37px,
            #6c394344 38px,
            #6c394344 41px
        );
    margin-bottom: 22px;
}
.banner-title {
    font: 32px Georgia, serif;
    letter-spacing: 2px;
}
.banner-sub {
    font: 14px Georgia, serif;
    margin-top: 8px;
    color: #eee2c8;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


def euro(x):
    return (
        f"{x:,.2f}".replace(",", " ").replace(".", ",")
        + " €"
    )


def personne(nom, age, revenu, statut="Salaire", retraite=64):
    return {
        "nom": nom,
        "age": age,
        "revenu": revenu,
        "fiscal": revenu,
        "statut": statut,
        "retraite": retraite,
    }


PROFILS = {
    "Camille — Premier emploi": {
        "personnes": [
            personne("Camille", 24, 2100.0),
        ],
        "enfants": [],
        "charges": 850.0,
        "loyer": 650.0,
        "credit": 160.0,
        "dette": 5760.0,
        "courant": 1400.0,
        "livret": 2200.0,
        "maison": 0.0,
        "voiture": False,
        "reserve": 3,
        "risque": 5,
        "objectif": (
            "Préparer un apport et finir le crédit étudiant."
        ),
        "positions": [],
    },
    "Léa — Construction patrimoniale": {
        "personnes": [
            personne("Léa", 32, 2600.0),
        ],
        "enfants": [],
        "charges": 1500.0,
        "loyer": 0.0,
        "credit": 0.0,
        "dette": 0.0,
        "courant": 3250.0,
        "livret": 7802.50,
        "maison": 0.0,
        "voiture": False,
        "reserve": 3,
        "risque": 5,
        "objectif": (
            "Conserver une réserve et diversifier le patrimoine."
        ),
        "positions": [],
    },
    "Sarah et Mehdi — Famille": {
        "personnes": [
            personne("Sarah", 38, 2600.0),
            personne("Mehdi", 40, 2500.0),
        ],
        "enfants": [8, 11],
        "charges": 2600.0,
        "loyer": 0.0,
        "credit": 950.0,
        "dette": 171000.0,
        "courant": 4500.0,
        "livret": 10000.0,
        "maison": 250000.0,
        "voiture": True,
        "reserve": 4,
        "risque": 5,
        "objectif": (
            "Protéger la famille et préparer les dépenses des enfants."
        ),
        "positions": [
            ("CTO", "Actions monde", 5000.0),
        ],
    },
    "Thomas — Indépendant au réel": {
        "personnes": [
            personne(
                "Thomas",
                46,
                3400.0,
                statut="Bénéfice réel",
            ),
        ],
        "enfants": [],
        "charges": 1700.0,
        "loyer": 750.0,
        "credit": 0.0,
        "dette": 0.0,
        "courant": 5000.0,
        "livret": 9000.0,
        "maison": 0.0,
        "voiture": True,
        "reserve": 6,
        "risque": 5,
        "objectif": (
            "Sécuriser les revenus irréguliers et préparer la retraite."
        ),
        "positions": [
            ("CTO", "Actions monde", 10000.0),
            ("CTO", "Obligations diversifiées", 5000.0),
        ],
    },
    "Sylvie — Transition retraite": {
        "personnes": [
            personne(
                "Sylvie",
                61,
                3000.0,
                retraite=63,
            ),
        ],
        "enfants": [],
        "charges": 1700.0,
        "loyer": 0.0,
        "credit": 0.0,
        "dette": 0.0,
        "courant": 6000.0,
        "livret": 18000.0,
        "maison": 220000.0,
        "voiture": True,
        "reserve": 6,
        "risque": 4,
        "objectif": (
            "Anticiper la retraite et maîtriser les retraits."
        ),
        "positions": [
            ("CTO", "Actions monde", 25000.0),
            ("CTO", "Obligations diversifiées", 35000.0),
        ],
    },
}


def places(s, env=None):
    return sum(
        p["valeur"]
        for p in s["positions"]
        if env is None or p["env"] == env
    )


def net(s):
    return (
        s["courant"]
        + s["livret"]
        + places(s)
        + s["maison"]
        - s["dette"]
    )


def fixes(s):
    return s["charges"] + s["loyer"] + s["credit"]


def brut_tranches(base, parts):
    bas = 0.0
    montant = 0.0
    lignes = []
    quotient = max(0.0, base) / parts

    for haut, taux in TRANCHES:
        assiette = max(
            0.0,
            min(quotient, haut) - bas,
        )
        impot_tranche = assiette * taux
        montant += impot_tranche

        libelle = (
            f"Au-delà de {bas:,.0f}"
            if haut == float("inf")
            else f"{bas:,.0f} à {haut:,.0f}"
        )

        lignes.append(
            {
                "Tranche par part": libelle,
                "Taux (%)": taux * 100,
                "Base par part (€)": assiette,
                "IR par part (€)": impot_tranche,
            }
        )
        bas = haut

    return montant * parts, lignes


def ir(base, adultes, enfants):
    base = max(0.0, base)

    supplement = (
        min(enfants, 2) * 0.5
        + max(0, enfants - 2)
    )
    parts = adultes + supplement

    brut, lignes = brut_tranches(base, parts)
    sans_enfants, _ = brut_tranches(base, adultes)

    plafonne = max(
        brut,
        sans_enfants - supplement * 2 * 1807.0,
    )

    seuil = 3277.0 if adultes == 2 else 1982.0
    constante = 1483.0 if adultes == 2 else 897.0

    if plafonne <= seuil:
        decote = min(
            plafonne,
            max(0.0, constante - 0.4525 * plafonne),
        )
    else:
        decote = 0.0

    return {
        "base": base,
        "parts": parts,
        "quotient": base / parts,
        "brut": brut,
        "plafonne": plafonne,
        "decote": decote,
        "net": max(0.0, plafonne - decote),
        "lignes": lignes,
    }


def base_professionnelle(s, annuels):
    lignes = []
    pension_deductions = []

    for p, revenu in zip(s["personnes"], annuels):
        revenu = max(0.0, revenu)

        if p["statut"] == "Salaire":
            deduction = min(
                revenu,
                max(
                    509.0,
                    min(revenu * 0.10, 14555.0),
                ),
            )

        elif p["statut"] == "Pension":
            deduction = min(
                revenu,
                max(454.0, revenu * 0.10),
            )
            pension_deductions.append(len(lignes))

        else:
            deduction = 0.0

        lignes.append(
            {
                "Personne": p["nom"],
                "Catégorie": p["statut"],
                "Revenu fiscal (€)": revenu,
                "Déduction (€)": deduction,
            }
        )

    total_pensions_deduit = sum(
        lignes[i]["Déduction (€)"]
        for i in pension_deductions
    )

    if total_pensions_deduit > 4439.0:
        for i in pension_deductions:
            lignes[i]["Déduction (€)"] *= (
                4439.0 / total_pensions_deduit
            )

    base = sum(
        x["Revenu fiscal (€)"] - x["Déduction (€)"]
        for x in lignes
    )

    return base, lignes


def fiscalite(s, annuels, gain_cto, gain_av, option):
    base, lignes = base_professionnelle(s, annuels)

    deduction_csg = s["csg_report"]
    base = max(0.0, base - deduction_csg)

    ages65 = sum(
        p["age"] + 1 >= 65
        for p in s["personnes"]
    )

    if base < 17670.0:
        abattement_unitaire = 2822.0
    elif base <= 28430.0:
        abattement_unitaire = 1411.0
    else:
        abattement_unitaire = 0.0

    age_abatt = ages65 * abattement_unitaire
    base = max(0.0, base - age_abatt)

    adultes = len(s["personnes"])
    enfants = len(s["enfants"])

    seul = ir(base, adultes, enfants)
    av_gain = max(0.0, gain_av)

    ancien = (
        s["av_ouverture"] is not None
        and s["annee"] - s["av_ouverture"] >= 8
    )

    if ancien:
        plafond_abattement = (
            9200.0 if adultes == 2 else 4600.0
        )
        abatt_av = min(av_gain, plafond_abattement)
    else:
        abatt_av = 0.0

    av_base = av_gain - abatt_av
    pv = max(0.0, gain_cto)

    taux_ir_av = 0.075 if ancien else 0.128

    forfait = (
        seul["net"]
        + pv * 0.128
        + av_base * taux_ir_av
    )

    bareme_ir = ir(
        base + pv + av_base,
        adultes,
        enfants,
    )

    ps_cto = pv * 0.186
    ps_av = av_gain * 0.172

    if option == "Forfait":
        retenu = forfait
        detail = seul
    else:
        retenu = bareme_ir["net"]
        detail = bareme_ir

    ir_du = 0.0 if retenu < 61.0 else retenu

    return {
        "base": base,
        "lignes_revenus": lignes,
        "csg_deduite": deduction_csg,
        "abatt_age": age_abatt,
        "seul": seul,
        "detail": detail,
        "pv": pv,
        "av_gain": av_gain,
        "av_base": av_base,
        "av_abatt": abatt_av,
        "av_ancien": ancien,
        "forfait": forfait,
        "bareme": bareme_ir["net"],
        "ps_cto": ps_cto,
        "ps_av": ps_av,
        "ir_du": ir_du,
        "total": ir_du + ps_cto + ps_av,
        "option": option,
        "csg_future": (
            pv * 0.068
            if option == "Barème global"
            else 0.0
        ),
    }


def preparer(s, premier=False):
    notes = []

    if not premier:
        s["charges"] *= 1.015
        s["loyer"] *= 1.015

    for p in s["personnes"]:
        if (
            p["statut"] != "Pension"
            and p["age"] >= p["retraite"]
        ):
            p["revenu"] *= 0.72
            p["fiscal"] *= 0.72
            p["statut"] = "Pension"

            notes.append(
                p["nom"]
                + " : retraite prévue par le scénario ; "
                "revenu ramené à 72 % du revenu antérieur."
            )

    gardes = []

    for age in s["enfants"]:
        if age >= 22:
            s["charges"] = max(
                0.0,
                s["charges"] - 300.0,
            )
            notes.append(
                "Un enfant devient fiscalement indépendant "
                "à 22 ans dans le scénario ; "
                "charges réduites de 300 €/mois."
            )
        else:
            gardes.append(age)

            if age == 18 and not premier:
                s["charges"] += 200.0
                notes.append(
                    "Études d'un enfant : charges "
                    "supplémentaires de 200 €/mois."
                )

    s["enfants"] = gardes

    age = max(
        p["age"] for p in s["personnes"]
    )
    retraite = all(
        p["statut"] == "Pension"
        for p in s["personnes"]
    )
    independant = any(
        p["statut"] == "Bénéfice réel"
        for p in s["personnes"]
    )

    if retraite or independant:
        reserve = 6
    elif s["enfants"]:
        reserve = 4
    else:
        reserve = 3

    s["reserve"] = reserve

    if age >= 75:
        s["risque"] = 3
    elif retraite or age >= 58:
        s["risque"] = 4
    else:
        s["risque"] = 5

    if retraite:
        besoin = (
            "Sécuriser les retraits et les dépenses de santé"
        )
    elif s["enfants"]:
        besoin = (
            "Préparer les études et protéger la famille"
        )
    elif age >= 50:
        besoin = "Préparer la retraite"
    elif s["maison"] == 0:
        besoin = "Constituer un apport"
    else:
        besoin = "Développer un patrimoine diversifié"

    s["objectif_actuel"] = besoin
    s["cible_reserve"] = reserve * fixes(s)

    complement_projet = (
        10000.0
        if not retraite and s["maison"] == 0
        else 5000.0
    )

    s["cible_projet"] = (
        s["cible_reserve"] + complement_projet
    )
    s["net_debut"] = net(s)
    s["notes_preparation"] = notes

    return s


def creer(nom):
    s = copy.deepcopy(PROFILS[nom])

    s.update(
        {
            "profil": nom,
            "annee": 1,
            "phase": "decisions",
            "bilans": [],
            "pertes": [],
            "csg_report": 0.0,
            "av_ouverture": None,
            "av_capital": 0.0,
            "notes_preparation": [],
        }
    )

    s["id"] = str(random.getrandbits(48))

    s["positions"] = [
        {
            "env": enveloppe,
            "support": support,
            "valeur": montant,
            "capital": montant,
        }
        for enveloppe, support, montant in s["positions"]
    ]

    s["reglages"] = {
        "livret": 0.0,
        "protection": 0,
        "option": "Forfait",
        "versements": {
            enveloppe + " | " + support: 0.0
            for enveloppe in ["CTO", "Assurance-vie"]
            for support in SUPPORTS
        },
    }

    return preparer(s, premier=True)


def acheter(s, env, support, montant):
    if montant <= 0:
        return

    if env == "Assurance-vie":
        if s["av_ouverture"] is None:
            s["av_ouverture"] = s["annee"]

        s["av_capital"] += montant

    for p in s["positions"]:
        if (
            p["env"] == env
            and p["support"] == support
        ):
            p["valeur"] += montant
            p["capital"] += montant
            return

    s["positions"].append(
        {
            "env": env,
            "support": support,
            "valeur": montant,
            "capital": montant,
        }
    )


def ceder(s, pct_cto, pct_av):
    gains = {
        "CTO": 0.0,
        "Assurance-vie": 0.0,
    }
    produits = 0.0

    for p in s["positions"]:
        fraction = (
            pct_cto
            if p["env"] == "CTO"
            else pct_av
        ) / 100

        produits += p["valeur"] * fraction
        gains[p["env"]] += (
            p["valeur"] - p["capital"]
        ) * fraction

        p["valeur"] *= 1 - fraction
        p["capital"] *= 1 - fraction

    s["av_capital"] *= 1 - pct_av / 100
    s["courant"] += produits

    s["positions"] = [
        p for p in s["positions"]
        if p["valeur"] > 0.001
    ]

    s["pertes"] = [
        x for x in s["pertes"]
        if s["annee"] - x["annee"] <= 10
    ]

    gain = gains["CTO"]
    utilise = 0.0

    if gain < 0:
        s["pertes"].append(
            {
                "annee": s["annee"],
                "montant": -gain,
            }
        )

    if gain > 0:
        for perte in s["pertes"]:
            deduction = min(
                gain,
                perte["montant"],
            )
            gain -= deduction
            perte["montant"] -= deduction
            utilise += deduction

    s["pertes"] = [
        x for x in s["pertes"]
        if x["montant"] > 0.001
    ]

    return produits, gains, max(0.0, gain), utilise


def photo(s):
    return {
        "Compte courant": s["courant"],
        "Livret": s["livret"],
        "Compte-titres": places(s, "CTO"),
        "Assurance-vie": places(s, "Assurance-vie"),
        "Immobilier": s["maison"],
        "Dette": s["dette"],
        "Patrimoine net": net(s),
    }


def simuler(s, reg, pct_cto, pct_av, retrait):
    t = copy.deepcopy(s)

    debut = net(t)
    photo_debut = photo(t)

    debut_age = [
        p["age"] for p in t["personnes"]
    ]

    produits, gains, pv, pertes_utilisees = ceder(
        t,
        pct_cto,
        pct_av,
    )

    t["courant"] += retrait
    t["livret"] -= retrait

    revenus = [
        [p["revenu"] for p in t["personnes"]]
        for _ in range(12)
    ]

    fiscaux = [
        [p["fiscal"] for p in t["personnes"]]
        for _ in range(12)
    ]

    depenses = [0.0] * 12
    indemnites = [0.0] * 12
    journal = list(t["notes_preparation"])
    cout = reg["protection"]

    eligibles = [
        "Dépense imprévue",
        "Santé",
        "Marchés en baisse",
        "Marchés en hausse",
    ]

    actifs = [
        i
        for i, p in enumerate(t["personnes"])
        if p["statut"] != "Pension"
    ]

    salaries = [
        i
        for i, p in enumerate(t["personnes"])
        if p["statut"] == "Salaire"
    ]

    independants = [
        i
        for i, p in enumerate(t["personnes"])
        if p["statut"] == "Bénéfice réel"
    ]

    if actifs:
        eligibles.append("Arrêt de travail")

    if salaries:
        eligibles += [
            "Augmentation",
            "Prime professionnelle",
            "Chômage temporaire",
        ]

    if independants:
        eligibles += [
            "Baisse d'activité",
            "Bonne activité",
        ]

    if t["maison"] > 0:
        eligibles.append("Travaux du logement")

    if t["voiture"]:
        eligibles.append("Réparation automobile")

    if (
        len(t["personnes"]) == 2
        and min(
            p["age"] for p in t["personnes"]
        ) < 43
    ):
        eligibles.append("Naissance")

    nombre = random.choices(
        [0, 1, 2, 3],
        weights=[35, 40, 20, 5],
        k=1,
    )[0]

    evenements = random.sample(
        eligibles,
        min(nombre, len(eligibles)),
    )

    choc_marche = 0.0

    for evenement in evenements:
        mois = random.randint(1, 12)
        index_mois = mois - 1

        message = (
            f"Mois {mois} — {evenement}"
        )

        if evenement in [
            "Dépense imprévue",
            "Santé",
            "Travaux du logement",
            "Réparation automobile",
        ]:
            maximum = (
                7000
                if evenement == "Travaux du logement"
                else 3000
            )
            montant = float(
                random.randint(500, maximum)
            )
            depenses[index_mois] += montant
            message += f" : {euro(montant)}."

        elif evenement in [
            "Marchés en baisse",
            "Marchés en hausse",
        ]:
            choc_marche += (
                -0.15
                if evenement == "Marchés en baisse"
                else 0.12
            )
            message += (
                " : choc commun aux supports, "
                "modulé selon leur risque."
            )

        elif evenement == "Naissance":
            t["enfants"].append(0)
            depenses[index_mois] += 1000.0

            for m in range(index_mois, 12):
                depenses[m] += 250.0

            t["charges"] += 250.0

            message += (
                " : 1 000 € d'équipement et "
                "250 €/mois de charges nouvelles."
            )

        else:
            if evenement in [
                "Baisse d'activité",
                "Bonne activité",
            ]:
                groupe = independants

            elif evenement in [
                "Augmentation",
                "Prime professionnelle",
                "Chômage temporaire",
            ]:
                groupe = salaries

            else:
                groupe = actifs

            index_personne = random.choice(groupe)
            p = t["personnes"][index_personne]
            message += " — " + p["nom"]

            if evenement == "Augmentation":
                montant = float(
                    random.randint(50, 150)
                )
                ratio = (
                    p["fiscal"] / p["revenu"]
                    if p["revenu"]
                    else 1.0
                )

                for m in range(index_mois, 12):
                    revenus[m][index_personne] += montant
                    fiscaux[m][index_personne] += montant * ratio

                p["revenu"] += montant
                p["fiscal"] += montant * ratio

                message += (
                    f" : +{euro(montant)}/mois."
                )

            elif evenement == "Prime professionnelle":
                montant = float(
                    random.randint(500, 2000)
                )

                revenus[index_mois][index_personne] += montant
                fiscaux[index_mois][index_personne] += montant

                message += (
                    f" : {euro(montant)}, imposable."
                )

            else:
                if evenement == "Baisse d'activité":
                    facteur = 0.65
                elif evenement == "Bonne activité":
                    facteur = 1.25
                else:
                    facteur = 0.55

                duree = (
                    3
                    if evenement in [
                        "Baisse d'activité",
                        "Bonne activité",
                        "Chômage temporaire",
                    ]
                    else 2
                )

                for m in range(
                    index_mois,
                    min(12, index_mois + duree),
                ):
                    perte = (
                        revenus[m][index_personne]
                        * (1 - facteur)
                    )

                    revenus[m][index_personne] *= facteur
                    fiscaux[m][index_personne] *= facteur

                    if evenement == "Arrêt de travail":
                        couverture = {
                            0: 0.0,
                            20: 0.50,
                            40: 0.80,
                        }[cout]

                        indemnites[m] += (
                            max(0.0, perte) * couverture
                        )

                message += (
                    " : variation temporaire des revenus ; "
                    "détail dans le tableau mensuel."
                )

        journal.append(message)

    if not evenements:
        journal.append(
            "Aucun événement aléatoire majeur cette année."
        )

    charges_base = s["charges"]

    annuels = [
        sum(
            fiscaux[m][i]
            for m in range(12)
        )
        for i in range(len(t["personnes"]))
    ]

    f = fiscalite(
        t,
        annuels,
        pv,
        gains["Assurance-vie"],
        reg["option"],
    )

    t["csg_report"] = f["csg_future"]

    f.update(
        {
            "gain_cto_brut": gains["CTO"],
            "pertes_utilisees": pertes_utilisees,
            "pertes_restantes": sum(
                x["montant"]
                for x in t["pertes"]
            ),
            "produit_ventes": produits,
        }
    )

    performances = {
        nom: max(
            -0.75,
            min(
                0.75,
                random.gauss(
                    parametres[0],
                    parametres[1],
                )
                + choc_marche * parametres[2] / 8,
            ),
        )
        for nom, parametres in SUPPORTS.items()
    }

    lignes = []

    programme = (
        reg["livret"]
        + sum(reg["versements"].values())
    )

    interets = 0.0
    gain_marche = 0.0
    rembourse = 0.0

    for index_mois in range(12):
        credit = min(
            t["credit"],
            t["dette"],
        )

        t["dette"] -= credit
        rembourse += credit

        if t["dette"] < 0.001:
            t["dette"] = 0.0
            t["credit"] = 0.0

        taxe = f["total"] / 12

        t["courant"] += (
            sum(revenus[index_mois])
            + indemnites[index_mois]
            - charges_base
            - t["loyer"]
            - credit
            - cout
            - depenses[index_mois]
            - taxe
        )

        execute = (
            t["courant"] >= programme
        )

        versement_av = sum(
            montant
            for cle, montant in reg["versements"].items()
            if cle.startswith("Assurance-vie | ")
        )

        limite_av = (
            t["av_capital"] + versement_av
            <= 150000.0 + 0.001
        )

        execute = execute and limite_av

        verse_livret = (
            reg["livret"] if execute else 0.0
        )
        verse_placements = (
            sum(reg["versements"].values())
            if execute
            else 0.0
        )

        if execute:
            t["courant"] -= programme
            t["livret"] += verse_livret

            for cle, montant in reg["versements"].items():
                enveloppe, support = cle.split(" | ")

                acheter(
                    t,
                    enveloppe,
                    support,
                    montant,
                )

        secours = min(
            t["livret"],
            max(0.0, -t["courant"]),
        )

        t["livret"] -= secours
        t["courant"] += secours

        interet_mois = (
            t["livret"]
            * (1.02 ** (1 / 12) - 1)
        )

        t["livret"] += interet_mois
        interets += interet_mois

        gain_mois = 0.0

        for position in t["positions"]:
            variation = (
                position["valeur"]
                * (
                    (
                        1 + performances[position["support"]]
                    ) ** (1 / 12)
                    - 1
                )
            )

            position["valeur"] += variation
            gain_mois += variation

        gain_marche += gain_mois

        lignes.append(
            {
                "Mois": index_mois + 1,
                "Revenus avant IR": sum(revenus[index_mois]),
                "Revenus fiscaux": sum(fiscaux[index_mois]),
                "Indemnités fictives": indemnites[index_mois],
                "Charges": charges_base,
                "Loyer": t["loyer"],
                "Crédit": credit,
                "Protection": cout,
                "Impôts provisionnés": taxe,
                "Aléas payés": depenses[index_mois],
                "Virement livret": verse_livret,
                "Investissements": verse_placements,
                "Secours livret": secours,
                "Courant": t["courant"],
                "Livret": t["livret"],
                "Placements": places(t),
                "Dette": t["dette"],
                "Patrimoine net": net(t),
                "Intérêts livret": interet_mois,
                "Gains placements": gain_mois,
                "Virements suspendus": not execute,
            }
        )

    df = pd.DataFrame(lignes)

    if places(t) > 0:
        risque = sum(
            p["valeur"]
            * SUPPORTS[p["support"]][2]
            for p in t["positions"]
        ) / places(t)
    else:
        risque = 0.0

    objectifs = [
        {
            "Objectif fixé": (
                "Réserve sur livret : "
                + euro(s["cible_reserve"])
            ),
            "Cible (€)": s["cible_reserve"],
            "Résultat (€)": t["livret"],
            "Atteint": (
                t["livret"] >= s["cible_reserve"]
            ),
        },
        {
            "Objectif fixé": (
                "Projet : " + s["objectif_actuel"]
            ),
            "Cible (€)": s["cible_projet"],
            "Résultat (€)": t["livret"],
            "Atteint": (
                t["livret"] >= s["cible_projet"]
            ),
        },
    ]

    criteres = {
        "Réserve fixée en début d'année": (
            4 if objectifs[0]["Atteint"] else 0
        ),
        "Projet fixé en début d'année": (
            4 if objectifs[1]["Atteint"] else 0
        ),
        "Aucun découvert en fin de mois": (
            4 if df["Courant"].min() >= 0 else 0
        ),
        "Risque compatible": (
            4 if risque <= s["risque"] else 0
        ),
        "Patrimoine préservé": (
            4 if net(t) >= debut else 0
        ),
    }

    flux = (
        sum(sum(x) for x in revenus)
        + sum(indemnites)
        - charges_base * 12
        - t["loyer"] * 12
        - rembourse
        - cout * 12
        - sum(depenses)
        - f["total"]
    )

    ecart = net(t) - (
        debut
        + flux
        + rembourse
        + interets
        + gain_marche
    )

    t["bilans"].append(
        {
            "annee": s["annee"],
            "ages": debut_age,
            "personnes": [
                p["nom"] for p in t["personnes"]
            ],
            "journal": journal,
            "mensuel": lignes,
            "fiscal": f,
            "debut": debut,
            "fin": net(t),
            "photo_debut": photo_debut,
            "photo_fin": photo(t),
            "interets": interets,
            "gains": gain_marche,
            "rembourse": rembourse,
            "flux": flux,
            "ecart": ecart,
            "objectifs": objectifs,
            "criteres": criteres,
            "note": sum(criteres.values()),
            "risque": risque,
            "perf": performances,
        }
    )

    t["reglages"] = reg
    t["phase"] = "debrief"

    return t


def afficher_bilan(b):
    df = pd.DataFrame(b["mensuel"])
    f = b["fiscal"]

    st.subheader("1. Évolution de l'année")

    for message in b["journal"]:
        st.write("• " + message)

    st.subheader("2. Atteinte des objectifs fixés")

    st.dataframe(
        pd.DataFrame(b["objectifs"]).round(2),
        hide_index=True,
    )

    st.write(
        "Les cibles ci-dessus ont été figées avant la simulation ; "
        "elles ne sont pas recalculées pour améliorer la note."
    )

    st.subheader("3. Budget exécuté")

    postes = [
        "Revenus avant IR",
        "Indemnités fictives",
        "Charges",
        "Loyer",
        "Crédit",
        "Protection",
        "Impôts provisionnés",
        "Aléas payés",
        "Virement livret",
        "Investissements",
        "Secours livret",
    ]

    st.dataframe(
        pd.DataFrame(
            {
                "Poste": postes,
                "Total annuel (€)": [
                    df[nom].sum()
                    for nom in postes
                ],
            }
        ).round(2),
        hide_index=True,
    )

    st.caption(
        "Les virements entre comptes sont des transferts internes. "
        "Le remboursement du capital réduit simultanément "
        "la trésorerie et la dette."
    )

    st.subheader(
        "4. Déroulé fiscal — paramètres figés de référence 2026"
    )

    st.dataframe(
        pd.DataFrame(
            f["lignes_revenus"]
        ).round(2),
        hide_index=True,
    )

    st.write(
        "CSG déductible reportée : "
        f"{euro(f['csg_deduite'])}. "
        "Abattement d'âge dans le périmètre du modèle : "
        f"{euro(f['abatt_age'])}. "
        "Base professionnelle/pensions nette : "
        f"{euro(f['base'])}."
    )

    st.write(
        f"Ventes brutes : {euro(f['produit_ventes'])}. "
        f"Gain net CTO réalisé : {euro(f['gain_cto_brut'])}. "
        "Pertes antérieures imputées : "
        f"{euro(f['pertes_utilisees'])}. "
        f"Plus-value CTO taxable : {euro(f['pv'])}. "
        "Pertes encore reportables : "
        f"{euro(f['pertes_restantes'])}."
    )

    st.write(
        "Produits d'assurance-vie rachetés : "
        f"{euro(f['av_gain'])}. "
        "Contrat d'au moins huit ans
