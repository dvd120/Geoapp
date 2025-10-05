# streamlit_mineral_id.py
"""
Aplicație simplă pentru identificare minerală (rule-based).
Rulare: pip install streamlit pandas
Apoi: streamlit run streamlit_mineral_id.py
"""

import streamlit as st
import pandas as pd
from math import fabs

st.set_page_config(page_title="Identificator minerale (demo)", layout="centered")

st.title("Identificator de minerale — demo pragmatic")
st.write("Introdu proprietățile observate; aplicația returnează cele mai probabile minerale și ce teste/sintetizări poți face în continuare.")

# --- Bază de date simplă de minerale (exemplu) ---
# Fiecare mineral are proprietăți aproximative: culori tipice, streak, duritate (min,max),
# luciu, clivaj, densitate aproximativă, magnetism, reacție acid.
MINERALS = {
    "Quartz": {
        "color": ["colorless", "white", "grey", "pink", "purple"],
        "streak": "white",
        "hardness": (7.0, 7.0),
        "luster": ["vitreous", "glassy"],
        "cleavage": ["none"],
        "density": 2.65,
        "magnetic": False,
        "acid": False,
        "notes": "dure, zgârie oțelul; fără clivaj evident"
    },
    "Calcite": {
        "color": ["colorless", "white", "yellow", "grey"],
        "streak": "white",
        "hardness": (3.0, 3.0),
        "luster": ["vitreous"],
        "cleavage": ["perfect rhombohedral"],
        "density": 2.71,
        "magnetic": False,
        "acid": True,
        "notes": "efervescență cu acid (HCl) — test cheie"
    },
    "Feldspar": {
        "color": ["white", "pink", "grey"],
        "streak": "white",
        "hardness": (6.0, 6.5),
        "luster": ["vitreous", "pearly"],
        "cleavage": ["two directions"],
        "density": 2.56,
        "magnetic": False,
        "acid": False,
        "notes": "clivaj bun în două direcții; frecvent în rocile magmatice"
    },
    "Mica (Biotite/Muscovite)": {
        "color": ["black", "brown", "silvery", "greenish"],
        "streak": "white",
        "hardness": (2.5, 3.0),
        "luster": ["pearly", "vitreous"],
        "cleavage": ["perfect basal"],
        "density": 2.8,
        "magnetic": False,
        "acid": False,
        "notes": "foi subțiri, flexibile"
    },
    "Pyrite": {
        "color": ["brassy", "golden"],
        "streak": "greenish-black",
        "hardness": (6.0, 6.5),
        "luster": ["metallic"],
        "cleavage": ["none"],
        "density": 5.0,
        "magnetic": False,
        "acid": False,
        "notes": "aspect de \"aur fals\"; nu-s maleabil"
    },
    "Galena": {
        "color": ["lead-gray"],
        "streak": "lead-gray",
        "hardness": (2.5, 2.75),
        "luster": ["metallic"],
        "cleavage": ["perfect cubic"],
        "density": 7.4,
        "magnetic": False,
        "acid": False,
        "notes": "greu (densitate mare), forme cubice"
    },
    "Hematite": {
        "color": ["steel-gray", "reddish"],
        "streak": "reddish-brown",
        "hardness": (5.5, 6.5),
        "luster": ["metallic", "earthy"],
        "cleavage": ["none"],
        "density": 5.3,
        "magnetic": False,
        "acid": False,
        "notes": "streak roșu-brun foarte caracteristic"
    },
    "Magnetite": {
        "color": ["black"],
        "streak": "black",
        "hardness": (5.5, 6.5),
        "luster": ["metallic"],
        "cleavage": ["none"],
        "density": 5.17,
        "magnetic": True,
        "acid": False,
        "notes": "puternic magnetic"
    },
    "Halite": {
        "color": ["colorless", "white"],
        "streak": "white",
        "hardness": (2.0, 2.5),
        "luster": ["vitreous"],
        "cleavage": ["perfect cubic"],
        "density": 2.17,
        "magnetic": False,
        "acid": False,
        "notes": "gust sărat (do not taste in professional setting) — dar e test clasic"
    },
    "Gypsum": {
        "color": ["colorless", "white", "grey"],
        "streak": "white",
        "hardness": (1.5, 2.0),
        "luster": ["pearly"],
        "cleavage": ["perfect"],
        "density": 2.3,
        "magnetic": False,
        "acid": False,
        "notes": "foarte moale; se zgârie ușor cu unghia"
    }
}

MINERAL_NAMES = list(MINERALS.keys())

# --- Input UI ---
st.sidebar.header("Proprietăți observate (introdu cât poți)")

color = st.sidebar.text_input("Culoare (separate prin virgulă, ex: white, pink)", "")
streak = st.sidebar.selectbox("Streak (culoarea dârei)", ["unknown", "white", "black", "reddish-brown", "lead-gray", "greenish-black"])
hardness = st.sidebar.slider("Duritate Mohs (val)", 1.0, 10.0, 5.0, 0.1)
luster = st.sidebar.multiselect("Luciul (alege toate aplicabile)", ["vitreous", "glassy", "pearly", "metallic", "earthy"])
cleavage = st.sidebar.multiselect("Clivaj/Fractură (alege)", ["none", "perfect", "perfect cubic", "perfect rhombohedral", "perfect basal", "two directions"])
density = st.sidebar.number_input("Densitate aproximativă (g/cm³) — lasă 0 dacă necunoscut", min_value=0.0, step=0.01, value=0.0)
magnetic = st.sidebar.selectbox("Magnetic?", ["unknown", "yes", "no"])
acid = st.sidebar.selectbox("Reacție la acid (HCl)?", ["unknown", "yes", "no"])

st.sidebar.markdown("---")
st.sidebar.write("Exemplu rapid: dacă ai o piesă cu streak roșu-brun și fără magnetism, hematite e o ipoteză bună.")
st.markdown("### Introducere rapidă")
st.write("Apăsă *Identifică* când ești gata. Dacă adaugi puține proprietăți, rezultatele vor fi mai vagi — normal.")

if st.button("Identifică"):
    # normalize inputs
    input_colors = [c.strip().lower() for c in color.split(",") if c.strip()] if color else []
    input_streak = streak if streak != "unknown" else None
    input_luster = [x for x in luster]
    input_cleavage = [x for x in cleavage]
    input_density = density if density > 0 else None
    input_magnetic = None if magnetic == "unknown" else (True if magnetic == "yes" else False)
    input_acid = None if acid == "unknown" else (True if acid == "yes" else False)

    def score_mineral(mineral_props):
        # score components: color, streak, hardness, luster, cleavage, density, magnetic, acid
        score = 0.0
        weight_total = 0.0

        # color (fuzzy): +1 if any match
        weight = 1.5
        weight_total += weight
        if input_colors:
            match = any(c in [mc.lower() for mc in mineral_props["color"]] for c in input_colors)
            if match:
                score += weight
            else:
                # partial credit if some similarity: we won't fuzzy-match names here
                score += 0.0

        # streak exact-ish
        weight = 2.0
        weight_total += weight
        if input_streak:
            if input_streak == mineral_props["streak"]:
                score += weight
            else:
                score += 0.0

        # hardness: gaussian-ish difference -> normalized to 0..2 points
        weight = 2.5
        weight_total += weight
        h_min, h_max = mineral_props["hardness"]
        h_center = (h_min + h_max) / 2.0
        diff = fabs(hardness - h_center)
        # if within 0.25 -> full, within 1 -> half, else linear decay
        if diff <= 0.25:
            score += weight
        elif diff <= 1.0:
            score += weight * 0.5
        elif diff <= 2.0:
            score += weight * 0.2

        # luster
        weight = 1.5
        weight_total += weight
        if input_luster:
            if any(l in mineral_props["luster"] for l in input_luster):
                score += weight

        # cleavage
        weight = 1.5
        weight_total += weight
        if input_cleavage:
            if any(c in mineral_props["cleavage"] for c in input_cleavage):
                score += weight

        # density (if known) -> reward proximity
        weight = 1.5
        weight_total += weight
        if input_density:
            d_diff = fabs(input_density - mineral_props["density"])
            if d_diff <= 0.1:
                score += weight
            elif d_diff <= 0.5:
                score += weight * 0.5

        # magnetic
        weight = 1.0
        weight_total += weight
        if input_magnetic is not None:
            if input_magnetic == mineral_props["magnetic"]:
                score += weight

        # acid
        weight = 1.0
        weight_total += weight
        if input_acid is not None:
            if input_acid == mineral_props["acid"]:
                score += weight

        # Normalize to percent
        percent = (score / weight_total) * 100 if weight_total else 0
        return percent

    results = []
    for name in MINERAL_NAMES:
        s = score_mineral(MINERALS[name])
        results.append((name, round(s, 1), MINERALS[name]["notes"], MINERALS[name]))

    results.sort(key=lambda x: x[1], reverse=True)
    df = pd.DataFrame([{"Mineral": r[0], "Score (%)": r[1], "Notes": r[2]} for r in results])
    st.subheader("Rezultate (ordonează după scor)")
    st.dataframe(df.style.hide_index())

    st.markdown("### Detalii și explicații")
    top = results[0]
    st.write(f"Cel mai probabil: **{top[0]}** (scor {top[1]}%). Motivație: {top[2]}")
    st.markdown("#### Cum interpretează aplicația scorurile")
    st.write("Scorul e o combinație ponderată a concordanței între proprietățile introduse și proprietățile tipice ale mineralului.\n\n"
             "- Dacă multe proprietăți coincid -> scor mare.\n- Dacă ai doar culoarea, scorurile vor fi mai apropiate între minerale cu culori similare.")
    st.markdown("#### Teste practice sugerate (ordinea e pragmatică):")
    st.write("""
    1. **Testul acidului (HCl)** — pune 1–2 picături de HCl diluat pe mineral: dacă effervescență → *Calcite*.
    2. **Testul magnetismului** — magnet puternic: dacă atrage → *Magnetite*.
    3. **Streak** — freci pe o placă de porțelan neglazurat; culoarea dârei e adesea concludentă (ex. hematite are streak roșu-brun).
    4. **Duritate Mohs** — unește cuțitul, sticlă, cuie, minerale cunoscute; vezi dacă scrie sau e zgâriat.
    5. **Observă clivajul** — foi subțiri (mica), clivaj cubic (galena, halite), etc.
    6. **Densitate brută** — dacă e vizibil foarte greu → galena sau minerale metalice.
    """)

    st.markdown("#### Răspunsuri slabe? Ce poți face")
    st.write("- Încarcă o mostră mai curată (fără oxidare/alterare).")
    st.write("- Adaugă rezultatele testelor (HCl, magnet, streak, duritate).")
    st.write("- Vrei integrare ML pe imagini? Pot adăuga un pipeline: încărcare imagini -> fine-tune pe model (trebuie dataset).")

    # show top 3 with property comparison
    st.markdown("### Top 3 comparat rapid (proprietăți cheie)")
    top3 = results[:3]
    comp = []
    for name, s, notes, props in top3:
        comp.append({
            "Mineral": name,
            "Score (%)": s,
            "Streak": props["streak"],
            "Hardness": f"{props['hardness'][0]} - {props['hardness'][1]}",
            "Luster": ", ".join(props["luster"]),
            "Cleavage": ", ".join(props["cleavage"]),
            "Density": props["density"],
            "Magnetic": props["magnetic"],
            "Acid": props["acid"]
        })
    st.table(pd.DataFrame(comp).set_index("Mineral"))

else:
    st.write("Completează cel puțin o proprietate în bara laterală și apasă *Identifică*.")
