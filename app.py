import copy
import json
import random

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Oak & Ledger",
    layout="wide",
)

KEY = "oak_ledger_complet_v2"

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


def euros(x):
    return (
        format(x, ",.2f")
        .replace(",", " ")
        .replace(".", ",")
        + " €"
    )


def personne(
    nom,
    age,
    revenu,
    statut="Salaire",
    retraite=64,
):
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
        "positions": [],
    },
    "Léa — Construire son patrimoine": {
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
                "Bénéfice réel",
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
        "positions": [
            ("CTO", "Actions monde", 10000.0),
            ("CTO", "Obligations diversifiées", 5000.0),
        ],
    },
    "Sylvie — Préparer sa retraite": {
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
        "positions": [
            ("CTO", "Actions monde", 25000.0),
            ("CTO", "Obligations diversifiées", 35000.0),
        ],
    },
}


def placements(s, enveloppe=None):
    return sum(
        p["valeur"]
        for p in s["positions"]
        if enveloppe is None
        or p["env"] == enveloppe
    )


def patrimoine(s):
    return (
        s["courant"]
        + s["livret"]
        + placements(s)
        + s["maison"]
        - s["dette"]
    )


def depenses_fixes(s):
    return (
        s["charges"]
        + s["loyer"]
        + s["credit"]
    )


def photo(s):
    return {
        "Courant": s["courant"],
        "Livret": s["livret"],
        "CTO": placements(s, "CTO"),
        "Assurance-vie": placements(s, "AV"),
        "Immobilier": s["maison"],
        "Dette": s["dette"],
        "Patrimoine net": patrimoine(s),
    }


def tranches(base, parts):
    bas = 0.0
    total = 0.0
    lignes = []

    for haut, taux in TRANCHES:
        assiette = max(
            0.0,
            min(
                max(0.0, base) / parts,
                haut,
            )
            - bas,
        )

        impot = assiette * taux

        if haut == float("inf"):
            libelle = "Au-delà de {:,.0f}".format(
                bas
            )
        else:
            libelle = "{:,.0f} à {:,.0f}".format(
                bas,
                haut,
            )

        lignes.append(
            {
                "Tranche par part": libelle,
                "Taux (%)": taux * 100,
                "Base par part (€)": assiette,
                "IR par part (€)": impot,
            }
        )

        total += impot
        bas = haut

    return total * parts, lignes


def calcul_ir(base, adultes, enfants):
    base = max(0.0, base)

    supplement = (
        min(enfants, 2) * 0.5
        + max(0, enfants - 2)
    )

    parts = adultes + supplement

    brut, lignes = tranches(
        base,
        parts,
    )

    sans, _ = tranches(
        base,
        adultes,
    )

    plafonne = max(
        brut,
        sans - supplement * 2 * 1807.0,
    )

    seuil = (
        3277.0 if adultes == 2 else 1982.0
    )
    constante = (
        1483.0 if adultes == 2 else 897.0
    )

    if plafonne <= seuil:
        decote = min(
            plafonne,
            max(
                0.0,
                constante - 0.4525 * plafonne,
            ),
        )
    else:
        decote = 0.0

    return {
        "base": base,
        "parts": parts,
        "brut": brut,
        "plafonne": plafonne,
        "decote": decote,
        "net": max(0.0, plafonne - decote),
        "lignes": lignes,
    }


def fiscalite(
    s,
    revenus_fiscaux,
    gain_cto,
    gain_av,
    option,
):
    details = []
    pensions = []

    for p, montant in zip(
        s["personnes"],
        revenus_fiscaux,
    ):
        montant = max(0.0, montant)

        if p["statut"] == "Salaire":
            deduction = min(
                montant,
                max(
                    509.0,
                    min(
                        montant * 0.10,
                        14555.0,
                    ),
                ),
            )

        elif p["statut"] == "Pension":
            deduction = min(
                montant,
                max(
                    454.0,
                    montant * 0.10,
                ),
            )
            pensions.append(len(details))

        else:
            deduction = 0.0

        details.append(
            {
                "Personne": p["nom"],
                "Catégorie": p["statut"],
                "Revenu fiscal (€)": montant,
                "Déduction (€)": deduction,
            }
        )

    somme = sum(
        details[i]["Déduction (€)"]
        for i in pensions
    )

    if somme > 4439.0:
        for i in pensions:
            details[i]["Déduction (€)"] *= (
                4439.0 / somme
            )

    base = max(
        0.0,
        sum(
            ligne["Revenu fiscal (€)"]
            - ligne["Déduction (€)"]
            for ligne in details
        )
        - s["csg_report"],
    )

    adultes = len(s["personnes"])
    enfants = len(s["enfants"])

    ir_seul = calcul_ir(
        base,
        adultes,
        enfants,
    )

    ancien = (
        s["av_ouverture"] is not None
        and s["annee"] - s["av_ouverture"] >= 8
    )

    produit_av = max(0.0, gain_av)

    if ancien:
        plafond = (
            9200.0 if adultes == 2 else 4600.0
        )
        abattement_av = min(
            produit_av,
            plafond,
        )
    else:
        abattement_av = 0.0

    base_av = produit_av - abattement_av
    pv = max(0.0, gain_cto)

    taux_ir_av = (
        0.075 if ancien else 0.128
    )

    ir_forfait = (
        ir_seul["net"]
        + pv * 0.128
        + base_av * taux_ir_av
    )

    ir_bareme = calcul_ir(
        base + pv + base_av,
        adultes,
        enfants,
    )

    if option == "Forfait":
        retenu = ir_forfait
        ir_detail = ir_seul
    else:
        retenu = ir_bareme["net"]
        ir_detail = ir_bareme

    ir_du = (
        0.0 if retenu < 61.0 else retenu
    )

    ps_cto = pv * 0.186
    ps_av = produit_av * 0.172

    return {
        "details": details,
        "base": base,
        "csg_deduite": s["csg_report"],
        "ir_seul": ir_seul,
        "ir_detail": ir_detail,
        "pv": pv,
        "produit_av": produit_av,
        "ancien": ancien,
        "abattement_av": abattement_av,
        "base_av": base_av,
        "forfait": ir_forfait,
        "bareme": ir_bareme["net"],
        "ir_du": ir_du,
        "ps_cto": ps_cto,
        "ps_av": ps_av,
        "total": ir_du + ps_cto + ps_av,
        "option": option,
        "csg_future": (
            pv * 0.068
            if option == "Barème global"
            else 0.0
        ),
    }


def preparer(s, premier=False):
    messages = []

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

            messages.append(
                p["nom"]
                + " part à la retraite dans ce scénario : "
                + "revenu ramené à 72 % du revenu antérieur."
            )

    gardes = []

    for age in s["enfants"]:
        if age >= 22:
            s["charges"] = max(
                0.0,
                s["charges"] - 300.0,
            )

            messages.append(
                "Départ fiscal d'un enfant à 22 ans : "
                "charges réduites de 300 €/mois."
            )

        else:
            gardes.append(age)

            if age == 18 and not premier:
                s["charges"] += 200.0

                messages.append(
                    "Études d'un enfant : "
                    "charges supplémentaires de 200 €/mois."
                )

    s["enfants"] = gardes

    retraite = all(
        p["statut"] == "Pension"
        for p in s["personnes"]
    )

    independant = any(
        p["statut"] == "Bénéfice réel"
        for p in s["personnes"]
    )

    age = max(
        p["age"]
        for p in s["personnes"]
    )

    if retraite or independant:
        mois_reserve = 6
    elif s["enfants"]:
        mois_reserve = 4
    else:
        mois_reserve = 3

    if age >= 75:
        s["risque_max"] = 3
    elif retraite or age >= 58:
        s["risque_max"] = 4
    else:
        s["risque_max"] = 5

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
        besoin = "Développer le patrimoine"

    s["besoin"] = besoin

    s["reserve_cible"] = (
        mois_reserve * depenses_fixes(s)
    )

    complement = (
        10000.0
        if not retraite and s["maison"] == 0
        else 5000.0
    )

    s["projet_cible"] = (
        s["reserve_cible"] + complement
    )

    s["preparation"] = messages

    return s


def nouveau(nom):
    s = copy.deepcopy(PROFILS[nom])

    s["positions"] = [
        {
            "env": enveloppe,
            "support": support,
            "valeur": montant,
            "capital": montant,
        }
        for enveloppe, support, montant in s["positions"]
    ]

    s.update(
        {
            "profil": nom,
            "uid": str(random.getrandbits(48)),
            "annee": 1,
            "phase": "decisions",
            "bilans": [],
            "pertes": [],
            "csg_report": 0.0,
            "av_ouverture": None,
            "av_capital": 0.0,
        }
    )

    s["reglages"] = {
        "livret": 0.0,
        "protection": 0,
        "option": "Forfait",
        "versements": {
            enveloppe + " | " + support: 0.0
            for enveloppe in ["CTO", "AV"]
            for support in SUPPORTS
        },
    }

    return preparer(s, True)


def investir(s, env, support, montant):
    if montant <= 0:
        return

    if env == "AV":
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


def vendre(s, cto, av):
    gains = {
        "CTO": 0.0,
        "AV": 0.0,
    }
    produit = 0.0

    for p in s["positions"]:
        fraction = (
            cto if p["env"] == "CTO" else av
        ) / 100

        produit += p["valeur"] * fraction

        gains[p["env"]] += (
            p["valeur"] - p["capital"]
        ) * fraction

        p["valeur"] *= 1 - fraction
        p["capital"] *= 1 - fraction

    s["av_capital"] *= 1 - av / 100
    s["courant"] += produit

    s["positions"] = [
        p for p in s["positions"]
        if p["valeur"] > 0.001
    ]

    s["pertes"] = [
        p for p in s["pertes"]
        if s["annee"] - p["annee"] <= 10
    ]

    taxable = max(0.0, gains["CTO"])
    utilise = 0.0

    if gains["CTO"] < 0:
        s["pertes"].append(
            {
                "annee": s["annee"],
                "montant": -gains["CTO"],
            }
        )

    for perte in s["pertes"]:
        deduction = min(
            taxable,
            perte["montant"],
        )

        taxable -= deduction
        perte["montant"] -= deduction
        utilise += deduction

    s["pertes"] = [
        p for p in s["pertes"]
        if p["montant"] > 0.001
    ]

    return produit, gains, taxable, utilise


def simuler(
    s,
    reg,
    cto,
    av,
    retrait,
):
    t = copy.deepcopy(s)

    debut = patrimoine(t)
    image_debut = photo(t)

    produit, gains, taxable, utilise = vendre(
        t,
        cto,
        av,
    )

    t["courant"] += retrait
    t["livret"] -= retrait

    revenus = [
        [
            p["revenu"]
            for p in t["personnes"]
        ]
        for _ in range(12)
    ]

    fiscaux = [
        [
            p["fiscal"]
            for p in t["personnes"]
        ]
        for _ in range(12)
    ]

    depenses = [0.0] * 12
    indemnites = [0.0] * 12

    journal = list(t["preparation"])

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

    eligibles = [
        "Dépense imprévue",
        "Santé",
        "Baisse des marchés",
        "Hausse des marchés",
    ]

    if actifs:
        eligibles.append(
            "Arrêt de travail"
        )

    if salaries:
        eligibles += [
            "Augmentation",
            "Prime",
            "Chômage temporaire",
        ]

    if independants:
        eligibles += [
            "Baisse d'activité",
            "Bonne activité",
        ]

    if t["maison"] > 0:
        eligibles.append(
            "Travaux du logement"
        )

    if t["voiture"]:
        eligibles.append(
            "Réparation automobile"
        )

    if (
        len(t["personnes"]) == 2
        and min(
            p["age"]
            for p in t["personnes"]
        ) < 43
    ):
        eligibles.append(
            "Naissance"
        )

    nombre = random.choices(
        [0, 1, 2, 3],
        weights=[35, 40, 20, 5],
        k=1,
    )[0]

    selection = random.sample(
        eligibles,
        min(
            nombre,
            len(eligibles),
        ),
    )

    evenements = sorted(
        [
            (
                random.randint(0, 11),
                evenement,
            )
            for evenement in selection
        ]
    )

    rendements = {}

    for support, parametres in SUPPORTS.items():
        rendement_annuel = max(
            -0.70,
            min(
                0.70,
                random.gauss(
                    parametres[0],
                    parametres[1],
                ),
            ),
        )

        rendement_mensuel = (
            (1 + rendement_annuel) ** (1 / 12)
            - 1
        )

        rendements[support] = [
            rendement_mensuel
        ] * 12

    for mois, evenement in evenements:
        texte = "Mois {} — {}".format(
            mois + 1,
            evenement,
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
                random.randint(
                    500,
                    maximum,
                )
            )

            depenses[mois] += montant

            texte += (
                " : "
                + euros(montant)
                + "."
            )

        elif evenement in [
            "Baisse des marchés",
            "Hausse des marchés",
        ]:
            choc = (
                -0.15
                if evenement == "Baisse des marchés"
                else 0.12
            )

            for support, parametres in SUPPORTS.items():
                ancien_taux = (
                    rendements[support][mois]
                )

                nouveau_taux = (
                    (1 + ancien_taux)
                    * (
                        1
                        + choc * parametres[2] / 8
                    )
                    - 1
                )

                rendements[support][mois] = (
                    nouveau_taux
                )

        elif evenement == "Naissance":
            t["enfants"].append(0)

            depenses[mois] += 1000.0

            for m in range(mois, 12):
                depenses[m] += 250.0

            t["charges"] += 250.0

            texte += (
                " : 1 000 € puis 250 €/mois "
                "de dépenses supplémentaires."
            )

        else:
            if evenement in [
                "Baisse d'activité",
                "Bonne activité",
            ]:
                groupe = independants

            elif evenement in [
                "Augmentation",
                "Prime",
                "Chômage temporaire",
            ]:
                groupe = salaries

            else:
                groupe = actifs

            index = random.choice(groupe)
            p = t["personnes"][index]

            texte += (
                " — " + p["nom"]
            )

            if evenement == "Augmentation":
                montant = float(
                    random.randint(
                        50,
                        150,
                    )
                )

                ratio = (
                    p["fiscal"] / p["revenu"]
                    if p["revenu"]
                    else 1.0
                )

                for m in range(mois, 12):
                    revenus[m][index] += (
                        montant
                    )

                    fiscaux[m][index] += (
                        montant * ratio
                    )

                p["revenu"] += montant
                p["fiscal"] += montant * ratio

                texte += (
                    " : +"
                    + euros(montant)
                    + "/mois."
                )

            elif evenement == "Prime":
                montant = float(
                    random.randint(
                        500,
                        2000,
                    )
                )

                revenus[mois][index] += (
                    montant
                )

                fiscaux[mois][index] += (
                    montant
                )

                texte += (
                    " : "
                    + euros(montant)
                    + ", imposable."
                )

            else:
                if evenement == "Baisse d'activité":
                    facteur = 0.65

                elif evenement == "Bonne activité":
                    facteur = 1.25

                else:
                    facteur = 0.55

                duree = (
                    2
                    if evenement == "Arrêt de travail"
                    else 3
                )

                for m in range(
                    mois,
                    min(
                        12,
                        mois + duree,
                    ),
                ):
                    perte = (
                        revenus[m][index]
                        * (1 - facteur)
                    )

                    revenus[m][index] *= (
                        facteur
                    )

                    fiscaux[m][index] *= (
                        facteur
                    )

                    if evenement == "Arrêt de travail":
                        couverture = {
                            0: 0.0,
                            20: 0.50,
                            40: 0.80,
                        }[
                            reg["protection"]
                        ]

                        indemnites[m] += (
                            max(0.0, perte)
                            * couverture
                        )

                texte += (
                    " : variation temporaire "
                    "des revenus, limitée à cette année."
                )

        journal.append(texte)

    if not evenements:
        journal.append(
            "Aucun événement aléatoire majeur cette année."
        )

    annuels = [
        sum(
            fiscaux[mois][index]
            for mois in range(12)
        )
        for index in range(
            len(t["personnes"])
        )
    ]

    f = fiscalite(
        t,
        annuels,
        taxable,
        gains["AV"],
        reg["option"],
    )

    f.update(
        {
            "produit": produit,
            "gain_cto_brut": gains["CTO"],
            "pertes_utilisees": utilise,
            "pertes_restantes": sum(
                p["montant"]
                for p in t["pertes"]
            ),
        }
    )

    t["csg_report"] = (
        f["csg_future"]
    )

    lignes = []
    interets = 0.0
    gains_marche = 0.0
    rembourse = 0.0

    programme = (
        reg["livret"]
        + sum(
            reg["versements"].values()
        )
    )

    for mois in range(12):
        credit = min(
            t["credit"],
            t["dette"],
        )

        t["dette"] -= credit
        rembourse += credit

        if t["dette"] < 0.001:
            t["dette"] = 0.0
            t["credit"] = 0.0

        taxe = (
            f["total"] / 12
        )

        t["courant"] += (
            sum(revenus[mois])
            + indemnites[mois]
            - s["charges"]
            - s["loyer"]
            - credit
            - reg["protection"]
            - depenses[mois]
            - taxe
        )

        av_mensuel = sum(
            montant
            for cle, montant in reg["versements"].items()
            if cle.startswith(
                "AV | "
            )
        )

        execute = (
            t["courant"] >= programme
            and (
                t["av_capital"]
                + av_mensuel
                <= 150000.0 + 0.001
            )
        )

        verse_livret = (
            reg["livret"]
            if execute
            else 0.0
        )

        verse_placements = (
            sum(
                reg["versements"].values()
            )
            if execute
            else 0.0
        )

        if execute:
            t["courant"] -= programme

            t["livret"] += (
                verse_livret
            )

            for cle, montant in reg["versements"].items():
                enveloppe, support = (
                    cle.split(" | ")
                )

                investir(
                    t,
                    enveloppe,
                    support,
                    montant,
                )

        secours = min(
            t["livret"],
            max(
                0.0,
                -t["courant"],
            ),
        )

        t["livret"] -= secours
        t["courant"] += secours

        interet_mois = (
            t["livret"]
            * (
                1.02 ** (1 / 12)
                - 1
            )
        )

        t["livret"] += (
            interet_mois
        )

        interets += (
            interet_mois
        )

        gain_mois = 0.0

        for p in t["positions"]:
            variation = (
                p["valeur"]
                * rendements[
                    p["support"]
                ][mois]
            )

            p["valeur"] += variation
            gain_mois += variation

        gains_marche += (
            gain_mois
        )

        lignes.append(
            {
                "Mois": mois + 1,
                "Revenus avant IR": sum(
                    revenus[mois]
                ),
                "Revenus fiscaux": sum(
                    fiscaux[mois]
                ),
                "Indemnités": indemnites[mois],
                "Charges": s["charges"],
                "Loyer": s["loyer"],
                "Crédit": credit,
                "Protection": reg["protection"],
                "Impôt provisionné": taxe,
                "Aléas": depenses[mois],
                "Virement livret": verse_livret,
                "Investissements": verse_placements,
                "Secours livret": secours,
                "Courant": t["courant"],
                "Livret": t["livret"],
                "Placements": placements(t),
                "Dette": t["dette"],
                "Patrimoine net": patrimoine(t),
                "Intérêts": interet_mois,
                "Gains placements": gain_mois,
                "Virements suspendus": not execute,
            }
        )

    df = pd.DataFrame(lignes)

    if placements(t) > 0:
        risque = sum(
            p["valeur"]
            * SUPPORTS[
                p["support"]
            ][2]
            for p in t["positions"]
        ) / placements(t)
    else:
        risque = 0.0

    objectifs = []

    cibles = [
        (
            "Réserve de sécurité",
            s["reserve_cible"],
        ),
        (
            s["besoin"],
            s["projet_cible"],
        ),
    ]

    for nom, cible in cibles:
        ratio = (
            t["livret"] / cible
            if cible > 0
            else 1.0
        )

        if ratio >= 1:
            statut = "Atteint"
        elif ratio >= 0.5:
            statut = "Partiellement atteint"
        else:
            statut = "Non atteint"

        objectifs.append(
            {
                "Objectif": nom,
                "Cible fixée (€)": cible,
                "Résultat (€)": t["livret"],
                "Statut": statut,
            }
        )

    criteres = {
        "Réserve de sécurité": (
            4
            if t["livret"] >= s["reserve_cible"]
            else 0
        ),
        "Objectif du projet": (
            4
            if t["livret"] >= s["projet_cible"]
            else 0
        ),
        "Pas de découvert mensuel": (
            4
            if df["Courant"].min() >= 0
            else 0
        ),
        "Risque compatible": (
            4
            if risque <= s["risque_max"]
            else 0
        ),
        "Patrimoine préservé": (
            4
            if patrimoine(t) >= debut
            else 0
        ),
    }

    flux = (
        df["Revenus avant IR"].sum()
        + sum(indemnites)
        - s["charges"] * 12
        - s["loyer"] * 12
        - rembourse
        - reg["protection"] * 12
        - sum(depenses)
        - f["total"]
    )

    performances = {}

    for support, serie in rendements.items():
        facteur = 1.0

        for taux in serie:
            facteur *= (
                1 + taux
            )

        performances[support] = (
            facteur - 1
        ) * 100

    ecart = (
        patrimoine(t)
        - (
            debut
            + flux
            + rembourse
            + interets
            + gains_marche
        )
    )

    bilan = {
        "annee": s["annee"],
        "ages": [
            p["age"]
            for p in s["personnes"]
        ],
        "noms": [
            p["nom"]
            for p in s["personnes"]
        ],
        "journal": journal,
        "mensuel": lignes,
        "fiscal": f,
        "debut": debut,
        "fin": patrimoine(t),
        "photo_debut": image_debut,
        "photo_fin": photo(t),
        "interets": interets,
        "gains": gains_marche,
        "rembourse": rembourse,
        "flux": float(flux),
        "ecart": float(ecart),
        "objectifs": objectifs,
        "criteres": criteres,
        "note": sum(
            criteres.values()
        ),
        "risque": risque,
        "performances": performances,
    }

    t["bilans"].append(bilan)
    t["reglages"] = reg
    t["phase"] = "debrief"

    return t


def afficher_bilan(b, uid):
    df = pd.DataFrame(
        b["mensuel"]
    )
    f = b["fiscal"]

    st.subheader(
        "1. Évolution de la situation"
    )

    for texte in b["journal"]:
        st.write(
            "• " + texte
        )

    st.subheader(
        "2. Objectifs fixés et résultats"
    )

    st.dataframe(
        pd.DataFrame(
            b["objectifs"]
        ).round(2),
        hide_index=True,
    )

    st.caption(
        "Les objectifs ont été figés en début de tour. "
        "Le projet est une cible d'épargne, "
        "pas un achat automatique. "
        "Sa cible inclut la réserve de sécurité."
    )

    st.subheader(
        "3. Budget annuel exécuté"
    )

    noms = [
        "Revenus avant IR",
        "Indemnités",
        "Charges",
        "Loyer",
        "Crédit",
        "Protection",
        "Impôt provisionné",
        "Aléas",
        "Virement livret",
        "Investissements",
        "Secours livret",
    ]

    tableau_budget = pd.DataFrame(
        {
            "Poste": noms,
            "Total annuel (€)": [
                df[nom].sum()
                for nom in noms
            ],
        }
    )

    st.dataframe(
        tableau_budget.round(2),
        hide_index=True,
    )

    st.caption(
        "Un virement entre comptes n'est pas "
        "une dépense patrimoniale. "
        "Un remboursement de capital réduit aussi la dette."
    )

    st.subheader(
        "4. Déroulé fiscal détaillé"
    )

    st.dataframe(
        pd.DataFrame(
            f["details"]
        ).round(2),
        hide_index=True,
    )

    st.write(
        "CSG déductible reportée : "
        + euros(f["csg_deduite"])
        + ". Base professionnelle et pensions après déductions : "
        + euros(f["base"])
        + "."
    )

    st.write(
        "Ventes : "
        + euros(f["produit"])
        + ". Gain CTO réalisé : "
        + euros(f["gain_cto_brut"])
        + ". Pertes imputées : "
        + euros(f["pertes_utilisees"])
        + ". Gain CTO taxable : "
        + euros(f["pv"])
        + ". Pertes encore reportables : "
        + euros(f["pertes_restantes"])
        + "."
    )

    st.write(
        "Produits assurance-vie rachetés : "
        + euros(f["produit_av"])
        + "."
    )

    anciennete_texte = (
        "oui"
        if f["ancien"]
        else "non"
    )

    st.write(
        "Contrat de huit ans ou plus : "
        + anciennete_texte
        + "."
    )

    st.write(
        "Abattement assurance-vie : "
        + euros(f["abattement_av"])
        + ". Base AV pour IR : "
        + euros(f["base_av"])
        + "."
    )

    st.write(
        "Comparaison IR total : forfait "
        + euros(f["forfait"])
        + " ; barème global "
        + euros(f["bareme"])
        + ". Choix : "
        + f["option"]
        + "."
    )

    detail = f["ir_detail"]

    st.write(
        "Base soumise au barème : "
        + euros(detail["base"])
        + " ; parts : "
        + str(detail["parts"])
        + "."
    )

    st.dataframe(
        pd.DataFrame(
            detail["lignes"]
        ).round(2),
        hide_index=True,
    )

    st.write(
        "IR au quotient : "
        + euros(detail["brut"])
        + " ; après plafonnement familial : "
        + euros(detail["plafonne"])
        + " ; décote : "
        + euros(detail["decote"])
        + "."
    )

    st.write(
        "IR total retenu, forfaits éventuels compris : "
        + euros(f["ir_du"])
        + ". PS CTO à 18,6 % : "
        + euros(f["ps_cto"])
        + ". PS AV à 17,2 % : "
        + euros(f["ps_av"])
        + "."
    )

    st.write(
        "Total fiscal annuel : "
        + euros(f["total"])
        + " ; provision mensuelle : "
        + euros(f["total"] / 12)
        + "."
    )

    st.caption(
        "Le total annuel est provisionné en douze parts égales. "
        "Ce n'est pas le calendrier réel du prélèvement "
        "à la source ou des régularisations. "
        "Voir les limites fiscales en haut de page."
    )

    st.subheader(
        "5. Synthèse patrimoniale"
    )

    tableau_patrimoine = pd.DataFrame(
        [
            {
                "Poste": nom,
                "Début (€)": montant,
                "Fin (€)": (
                    b["photo_fin"][nom]
                ),
                "Variation (€)": (
                    b["photo_fin"][nom]
                    - montant
                ),
            }
            for nom, montant in b["photo_debut"].items()
        ]
    )

    st.dataframe(
        tableau_patrimoine.round(2),
        hide_index=True,
    )

    st.line_chart(
        df.set_index("Mois")[
            [
                "Courant",
                "Livret",
                "Placements",
                "Patrimoine net",
            ]
        ]
    )

    st.subheader(
        "6. Rendements et formation du patrimoine"
    )

    tableau_rendements = pd.DataFrame(
        [
            {
                "Support": nom,
                "Performance du support sur 12 mois (%)": (
                    performance
                ),
            }
            for nom, performance in b["performances"].items()
        ]
    )

    st.dataframe(
        tableau_rendements.round(2),
        hide_index=True,
    )

    st.caption(
        "La performance d'un support ne mesure pas "
        "celle des versements progressifs, "
        "ni celle du patrimoine total."
    )

    st.bar_chart(
        pd.DataFrame(
            {
                "Origine": [
                    "Flux financiers nets",
                    "Capital remboursé",
                    "Intérêts livret",
                    "Gains placements",
                ],
                "Montant (€)": [
                    b["flux"],
                    b["rembourse"],
                    b["interets"],
                    b["gains"],
                ],
            }
        ).set_index("Origine")
    )

    st.write(
        "Patrimoine initial "
        + euros(b["debut"])
        + " + flux financiers nets "
        + euros(b["flux"])
        + " + réduction de dette "
        + euros(b["rembourse"])
        + " + intérêts "
        + euros(b["interets"])
        + " + gains/pertes "
        + euros(b["gains"])
        + " = patrimoine final "
        + euros(b["fin"])
        + "."
    )

    st.write(
        "Écart de rapprochement comptable : "
        + euros(b["ecart"])
        + "."
    )

    st.subheader(
        "7. Débrief du conseil"
    )

    for nom, points in b["criteres"].items():
        st.write(
            nom
            + " : "
            + str(points)
            + "/4"
        )

    st.write(
        "Note : "
        + str(b["note"])
        + "/20. Risque moyen : "
        + format(
            b["risque"],
            ".1f",
        )
        + "/10."
    )

    with st.expander(
        "Détail des douze mois"
    ):
        st.dataframe(
            df.round(2),
            hide_index=True,
        )

        st.write(
            "Mois avec virements suspendus : "
            + str(
                int(
                    df["Virements suspendus"].sum()
                )
            )
        )

    st.download_button(
        "Exporter le détail mensuel CSV",
        df.to_csv(
            index=False,
            sep=";",
            decimal=",",
        ).encode("utf-8-sig"),
        file_name=(
            "annee_"
            + str(b["annee"])
            + ".csv"
        ),
        mime="text/csv",
        key=(
            uid
            + "_csv_"
            + str(b["annee"])
        ),
    )


st.markdown(
    """
    <style>
    .stApp {
        background: #f4f0e6;
        color: #24372d;
    }
    h1, h2, h3 {
        font-family: Georgia, serif !important;
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
    }
    [data-testid="stMetric"] {
        background: #fffcf3;
        padding: 12px;
        border-top: 3px solid #a68a53;
    }
    .banner {
        padding: 24px;
        color: #fff9e8;
        background-color: #213e30;
        border: 1px solid #ac915b;
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
        margin-bottom: 20px;
    }
    </style>

    <div class="banner">
        <div style="font:32px Georgia,serif;letter-spacing:2px">
            OAK &amp; LEDGER
        </div>
        <div>
            Le cabinet patrimonial — Simulation pédagogique
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.expander(
    "Règles et limites fiscales — à lire"
):
    st.write(
        "Simulation française simplifiée, paramètres figés : "
        "barème 2026 des revenus 2025 et prélèvements financiers 2026. "
        "Ce mélange de millésimes est une convention d'exercice, "
        "pas une déclaration fiscale réelle. "
        "Aucune prévision des lois futures."
    )

    st.write(
        "Revenus disponibles après cotisations mais avant IR, "
        "distincts du net fiscal. Vous pouvez modifier les deux champs. "
        "Salaires : déduction de 10 %, minimum 509 €, "
        "maximum 14 555 € par personne. "
        "Pensions : minimum 454 € par bénéficiaire, "
        "plafond familial 4 439 €. "
        "Thomas : bénéfice au réel déjà net des charges "
        "professionnelles et cotisations, sans abattement salarial."
    )

    st.write(
        "Couples mariés ou pacsés, imposition commune ; "
        "enfants à charge exclusive, sans parent isolé. "
        "Calcul par tranches, plafond familial ordinaire "
        "de 1 807 € par demi-part et décote inclus. "
        "Ne sont pas gérés : abattement pour âge ou invalidité, "
        "crédits/réductions, frais réels, hauts revenus, "
        "IFI et cas internationaux. "
        "Les résultats restent approximatifs, "
        "notamment après 65 ans."
    )

    st.write(
        "CTO : supports capitalisants, aucun revenu distribué. "
        "PFU = 12,8 % + 18,6 % = 31,4 %. "
        "Option globale au barème. "
        "Pertes reportées dix tours. "
        "CSG déductible de 6,8 % sur gains CTO au barème, "
        "reportée au tour suivant. "
        "Pas de titres anciens bénéficiant d'abattements de durée."
    )

    st.write(
        "Assurance-vie : contrat unique en unités de compte "
        "ouvert dans le jeu, primes récentes, aucun autre contrat. "
        "Capital de primes non remboursé limité à 150 000 € "
        "par restriction pédagogique, pas par plafond légal. "
        "Avant huit ans : IR 12,8 %. "
        "Après huit ans : IR 7,5 % après abattement "
        "de 4 600 € ou 9 200 €. "
        "PS de 17,2 % sur les produits rachetés avant abattement. "
        "Option barème possible. "
        "Pas de fonds euros, de CSG déductible AV, "
        "de contrats anciens ou de succession."
    )

    st.write(
        "Impôt annuel calculé sur les revenus simulés "
        "puis provisionné en douze parts égales : "
        "ce n'est pas le calendrier réel des acomptes "
        "ou du prélèvement à la source. "
        "La naissance modifie le quotient pour le tour entier ; "
        "les autres évolutions familiales s'appliquent "
        "au début du tour."
    )

    st.write(
        "Livret fictif : 2 %, sans fiscalité ni plafond. "
        "Crédits à taux zéro : paiement égal au capital remboursé. "
        "Immobilier à valeur constante, sans achat/vente. "
        "Protection fictive à 20 ou 40 €/mois : "
        "couvre 50 % ou 80 % de la perte simulée "
        "d'arrêt de travail seulement ; "
        "indemnités non imposables par convention. "
        "Aucun autre aléa n'est couvert."
    )

    st.write(
        "Retraite à l'âge fixé par le scénario, "
        "revenu ramené à 72 %, sans calcul des droits réels. "
        "Charges et loyers augmentés de 1,5 % par tour. "
        "Enfants indépendants à 22 ans par convention. "
        "Objectifs d'épargne revus à chaque début d'année "
        "puis figés pour la note. "
        "Aucun projet immobilier n'est exécuté automatiquement."
    )

    st.write(
        "Partie sans limite de tours, avec clôture pédagogique "
        "du dossier à 90 ans puis choix d'un nouveau client. "
        "Pas de décès ni de transmission simulés. "
        "Sauvegardez le JSON : la session du navigateur "
        "n'est pas une sauvegarde permanente."
    )

    st.markdown(
        "Sources de référence : "
        "[IR]"
        "(https://www.service-public.gouv.fr/particuliers/vosdroits/F34328), "
        "[revenus mobiliers]"
        "(https://www.impots.gouv.fr/particulier/les-revenus-mobiliers), "
        "[assurance-vie]"
        "(https://www.impots.gouv.fr/particulier/questions/"
        "jai-effectue-des-retraits-sur-mon-contrat-dassurance-vie-"
        "quelles-sont-les)."
    )


if KEY not in st.session_state:
    st.session_state[KEY] = {
        "client": None,
        "archives": [],
    }

app = st.session_state[KEY]
s = app["client"]


with st.sidebar:
    st.header(
        "Le cabinet"
    )

    st.write(
        "Dossiers archivés : "
        + str(
            len(
                app["archives"]
            )
        )
    )

    fichier = st.file_uploader(
        "Restaurer une sauvegarde JSON",
        type="json",
    )

    if fichier is not None:
        if st.button(
            "Charger la sauvegarde"
        ):
            try:
                charge = json.load(
                    fichier
                )

                if (
                    charge.get("format") != KEY
                    or not isinstance(
                        charge.get("partie"),
                        dict,
                    )
                ):
                    raise ValueError(
                        "Sauvegarde incompatible."
                    )

                if (
                    "client" not in charge["partie"]
                    or "archives" not in charge["partie"]
                ):
                    raise ValueError(
                        "Sauvegarde incomplète."
                    )

                st.session_state[KEY] = (
                    charge["partie"]
                )

                st.rerun()

            except (
                ValueError,
                KeyError,
                TypeError,
            ) as erreur:
                st.error(
                    str(erreur)
                )

    sauvegarde = {
        "format": KEY,
        "partie": app,
    }

    st.download_button(
        "Sauvegarder la partie",
        json.dumps(
            sauvegarde,
            ensure_ascii=False,
        ).encode("utf-8"),
        file_name="sauvegarde_cabinet.json",
        mime="application/json",
    )

    if s is not None:
        st.write(
            s["profil"]
        )

        for p in s["personnes"]:
            st.write(
                p["nom"]
                + " : "
                + str(p["age"])
                + " ans — "
                + p["statut"]
            )

        texte_enfants = (
            ", ".join(
                str(age) + " ans"
                for age in s["enfants"]
            )
            or "aucun"
        )

        st.write(
            "Enfants à charge : "
            + texte_enfants
        )

        if st.button(
            "Archiver et choisir un autre client"
        ):
            app["archives"].append(
                copy.deepcopy(s)
            )

            app["client"] = None

            st.rerun()


if s is None:
    st.header(
        "Choisir un nouveau client"
    )

    noms = list(PROFILS)

    if "selection_oak_v2" not in st.session_state:
        st.session_state.selection_oak_v2 = (
            noms[0]
        )

    if st.button(
        "Tirer un profil au hasard"
    ):
        st.session_state.selection_oak_v2 = (
            random.choice(noms)
        )

    nom = st.selectbox(
        "Profil",
        noms,
        key="selection_oak_v2",
    )

    candidat = nouveau(nom)

    for p in candidat["personnes"]:
        st.write(
            p["nom"]
            + " — "
            + str(p["age"])
            + " ans — "
            + euros(p["revenu"])
            + "/mois avant IR."
        )

    st.write(
        "Charges : "
        + euros(candidat["charges"])
        + " ; loyer : "
        + euros(candidat["loyer"])
        + " ; crédit : "
        + euros(candidat["credit"])
        + " par mois."
    )

    st.write(
        "Livret : "
        + euros(candidat["livret"])
        + " ; placements : "
        + euros(
            placements(candidat)
        )
        + " ; dette : "
        + euros(candidat["dette"])
        + "."
    )

    st.write(
        "Besoin : "
        + candidat["besoin"]
        + ". Patrimoine net : "
        + euros(
            patrimoine(candidat)
        )
        + "."
    )

    if st.button(
        "Ouvrir ce dossier",
        type="primary",
    ):
        app["client"] = candidat

        st.rerun()

    st.stop()


st.header(
    s["profil"]
    + " — Année "
    + str(s["annee"])
)

indicateurs = [
    (
        "Compte courant",
        s["courant"],
    ),
    (
        "Livret",
        s["livret"],
    ),
    (
        "Placements",
        placements(s),
    ),
    (
        "Patrimoine net",
        patrimoine(s),
    ),
]

for colonne, (nom, montant) in zip(
    st.columns(4),
    indicateurs,
):
    colonne.metric(
        nom,
        euros(montant),
    )


if s["phase"] == "decisions":
    st.subheader(
        "Situation et besoins de début d'année"
    )

    for texte in s["preparation"]:
        st.info(texte)

    st.write(
        s["besoin"]
    )

    st.write(
        "Réserve cible : "
        + euros(s["reserve_cible"])
        + ". Épargne de projet sur livret, réserve incluse : "
        + euros(s["projet_cible"])
        + ". Risque maximal : "
        + str(s["risque_max"])
        + "/10."
    )

    st.subheader(
        "1. Revenus avant impôt"
    )

    revenus = []
    fiscaux = []

    for index, p in enumerate(
        s["personnes"]
    ):
        colonne_a, colonne_b = (
            st.columns(2)
        )

        cle_personne = (
            s["uid"]
            + "_"
            + str(s["annee"])
            + "_"
            + str(index)
        )

        revenus.append(
            colonne_a.number_input(
                p["nom"]
                + " : disponible mensuel avant IR (€)",
                min_value=0.0,
                value=float(
                    p["revenu"]
                ),
                step=50.0,
                key=(
                    cle_personne
                    + "_revenu"
                ),
            )
        )

        fiscaux.append(
            colonne_b.number_input(
                p["nom"]
                + " : revenu fiscal mensuel avant déduction (€)",
                min_value=0.0,
                value=float(
                    p["fiscal"]
                ),
                step=50.0,
                key=(
                    cle_personne
                    + "_fiscal"
                ),
            )
        )

    st.caption(
        "Ce ne sont pas des salaires bruts. "
        "Pour Thomas, les charges professionnelles "
        "et cotisations sont déjà déduites du bénéfice réel."
    )

    reg = copy.deepcopy(
        s["reglages"]
    )

    cle = (
        s["uid"]
        + "_"
        + str(s["annee"])
    )

    st.subheader(
        "2. Protection et versements mensuels"
    )

    reg["protection"] = st.selectbox(
        "Protection fictive — cotisation mensuelle (€)",
        [0, 20, 40],
        index=[0, 20, 40].index(
            reg["protection"]
        ),
        key=(
            cle
            + "_protection"
        ),
    )

    st.caption(
        "20 € couvre 50 % et 40 € couvre 80 % "
        "de la perte simulée d'arrêt de travail. "
        "Aucun effet sur les dépenses de santé, "
        "travaux ou baisse d'activité."
    )

    reg["livret"] = st.number_input(
        "Livret — versement par mois (€)",
        min_value=0.0,
        value=float(
            reg["livret"]
        ),
        step=10.0,
        key=(
            cle
            + "_livret"
        ),
    )

    for enveloppe in [
        "CTO",
        "AV",
    ]:
        nom_enveloppe = (
            "Assurance-vie"
            if enveloppe == "AV"
            else "Compte-titres"
        )

        with st.expander(
            "Versements mensuels — "
            + nom_enveloppe
        ):
            for support in SUPPORTS:
                cle_versement = (
                    enveloppe
                    + " | "
                    + support
                )

                reg["versements"][cle_versement] = (
                    st.number_input(
                        support
                        + " (€/mois)",
                        min_value=0.0,
                        value=float(
                            reg["versements"][
                                cle_versement
                            ]
                        ),
                        step=10.0,
                        key=(
                            cle
                            + "_"
                            + cle_versement
                        ),
                    )
                )

    st.subheader(
        "3. Retraits et choix fiscal"
    )

    retrait = st.number_input(
        "Transfert immédiat du livret vers le courant (€)",
        min_value=0.0,
        max_value=float(
            s["livret"]
        ),
        value=0.0,
        step=100.0,
        key=(
            cle
            + "_retrait"
        ),
    )

    cto = st.slider(
        "Part de chaque ligne CTO à vendre (%)",
        0,
        100,
        0,
        10,
        key=(
            cle
            + "_cto"
        ),
    )

    av = st.slider(
        "Part du contrat assurance-vie à racheter (%)",
        0,
        100,
        0,
        10,
        key=(
            cle
            + "_av"
        ),
    )

    reg["option"] = st.radio(
        "Option globale sur les revenus financiers concernés",
        [
            "Forfait",
            "Barème global",
        ],
        index=(
            0
            if reg["option"] == "Forfait"
            else 1
        ),
        key=(
            cle
            + "_option"
        ),
    )

    prevision = copy.deepcopy(s)

    for index, p in enumerate(
        prevision["personnes"]
    ):
        p["revenu"] = (
            revenus[index]
        )

        p["fiscal"] = (
            fiscaux[index]
        )

    estimation = fiscalite(
        prevision,
        [
            montant * 12
            for montant in fiscaux
        ],
        0.0,
        0.0,
        reg["option"],
    )

    capacite = (
        sum(revenus)
        - depenses_fixes(s)
        - reg["protection"]
        - estimation["total"] / 12
    )

    programme = (
        reg["livret"]
        + sum(
            reg["versements"].values()
        )
    )

    st.write(
        "Capacité mensuelle après IR et protection, "
        "hors ventes et événements : "
        + euros(capacite)
        + ". Virements programmés : "
        + euros(programme)
        + ". Reste : "
        + euros(
            capacite - programme
        )
        + "."
    )

    st.info(
        "Les virements sont exécutés chaque mois "
        "après les revenus et dépenses, "
        "jamais douze fois d'un coup. "
        "S'il manque de trésorerie, "
        "le programme du mois est suspendu. "
        "Un retrait de secours sur le livret est tenté "
        "si le courant est négatif. "
        "Les montants programmés seront repris "
        "l'année suivante."
    )

    st.divider()

    if st.button(
        "Valider les décisions et simuler l'année",
        type="primary",
    ):
        av_prevu = (
            s["av_capital"]
            * (
                1 - av / 100
            )
            + 12 * sum(
                montant
                for cle_versement, montant
                in reg["versements"].items()
                if cle_versement.startswith(
                    "AV | "
                )
            )
        )

        if av_prevu > 150000.0 + 0.001:
            st.error(
                "Le plafond pédagogique de primes AV "
                "de 150 000 € serait dépassé. "
                "Réduisez les versements."
            )

        else:
            app["client"] = simuler(
                prevision,
                reg,
                cto,
                av,
                retrait,
            )

            st.rerun()


else:
    bilan = (
        s["bilans"][-1]
    )

    st.header(
        "Débrief de l'année "
        + str(
            bilan["annee"]
        )
    )

    texte_ages = ", ".join(
        nom
        + " "
        + str(age)
        + " → "
        + str(age + 1)
        + " ans"
        for nom, age in zip(
            bilan["noms"],
            bilan["ages"],
        )
    )

    st.write(
        "Âges : "
        + texte_ages
    )

    afficher_bilan(
        bilan,
        s["uid"],
    )

    with st.expander(
        "Historique du dossier"
    ):
        historique = pd.DataFrame(
            [
                {
                    "Année": b["annee"],
                    "Patrimoine net": b["fin"],
                    "Impôt annuel": (
                        b["fiscal"]["total"]
                    ),
                    "Note /20": b["note"],
                }
                for b in s["bilans"]
            ]
        )

        st.dataframe(
            historique.round(2),
            hide_index=True,
        )

        evolution = [
            {
                "Année": 0,
                "Patrimoine net": (
                    s["bilans"][0]["debut"]
                ),
            }
        ] + [
            {
                "Année": b["annee"],
                "Patrimoine net": b["fin"],
            }
            for b in s["bilans"]
        ]

        st.line_chart(
            pd.DataFrame(
                evolution
            ).set_index("Année")
        )

        if len(s["bilans"]) > 1:
            annee_consultee = st.selectbox(
                "Consulter un ancien bilan",
                [
                    b["annee"]
                    for b in s["bilans"][:-1]
                ],
            )

            ancien_bilan = next(
                b
                for b in s["bilans"]
                if b["annee"] == annee_consultee
            )

            afficher_bilan(
                ancien_bilan,
                s["uid"],
            )

    st.divider()

    st.subheader(
        "Fin du débrief"
    )

    st.caption(
        "L'année suivante ne démarre qu'après votre clic. "
        "Recharger la page ne relance pas "
        "les événements de cette année."
    )

    if st.button(
        "Passer à l'année suivante",
        type="primary",
    ):
        for p in s["personnes"]:
            p["age"] += 1

        s["enfants"] = [
            age + 1
            for age in s["enfants"]
        ]

        age_maximum = max(
            p["age"]
            for p in s["personnes"]
        )

        if age_maximum >= 90:
            app["archives"].append(
                copy.deepcopy(s)
            )

            app["client"] = None

        else:
            s["annee"] += 1
            s["phase"] = "decisions"

            app["client"] = preparer(s)

        st.rerun()
