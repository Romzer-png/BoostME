import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="BoostMe | KPIs",
    page_icon="📊",
    layout="wide",
)

# -----------------------------
# Style (inspired by the PBIX)
# -----------------------------
ORANGE = "#FF7F0F"
TEXT = "#252423"
BG = "#FFFFFF"

st.markdown(
    f"""
    <style>
      /* Global */
      .stApp {{
        background: {BG};
        color: {TEXT};
        font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
      }}
      /* Reduce top padding a bit */
      .block-container {{
        padding-top: 0.8rem;
        padding-bottom: 2rem;
      }}
      /* A thin orange bar like Power BI */
      .boostme-topbar {{
        height: 12px;
        background: {ORANGE};
        border-radius: 10px;
        margin-bottom: 12px;
      }}
      /* Section bar "Analyse des tendances" */
      .boostme-sectionbar {{
        background: {ORANGE};
        border-radius: 12px;
        padding: 10px 14px;
        margin: 14px 0 10px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }}
      .boostme-sectionbar h2 {{
        margin: 0;
        color: #FFFFFF;
        font-size: 1.25rem;
        font-weight: 700;
      }}
      /* KPI cards */
      .kpi-card {{
        border: 2px solid {ORANGE};
        border-radius: 15px;
        padding: 14px 16px;
        background: #FFFFFF;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
      }}
      .kpi-title {{
        font-size: 0.9rem;
        font-weight: 700;
        color: {TEXT};
        line-height: 1.15rem;
      }}
      .kpi-value {{
        font-size: 2.05rem;
        font-weight: 800;
        color: {TEXT};
        line-height: 2.3rem;
      }}
      .kpi-sub {{
        font-size: 0.8rem;
        color: #6b6b6b;
      }}
      /* Make selectboxes look a bit tighter */
      div[data-baseweb="select"] > div {{
        border-radius: 10px !important;
      }}
      /* Hide Streamlit default footer */
      footer {{visibility: hidden;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Helpers
# -----------------------------
REQUIRED_COLUMNS = [
    "category_id",
    "views",
    "Taux d'engagement (%)",
    "Engagement total",
    "channel",
    "published_at",
]

def _fr_int(n: float | int) -> str:
    """French-ish thousands separator with spaces."""
    if pd.isna(n):
        return "—"
    try:
        n_int = int(round(float(n)))
        return f"{n_int:,}".replace(",", " ")
    except Exception:
        return "—"

def _fr_float(n: float, decimals: int = 2) -> str:
    if pd.isna(n):
        return "—"
    try:
        fmt = f"{{:,.{decimals}f}}".format(float(n))
        # 12,345.67 -> 12 345,67
        fmt = fmt.replace(",", "X").replace(".", ",").replace("X", " ")
        return fmt
    except Exception:
        return "—"

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    The PBIX uses some column names with spaces/accents.
    Here we accept a few common variants and standardize them.
    """
    rename_map = {
        "taux_engagement": "Taux d'engagement (%)",
        "taux d'engagement (%)": "Taux d'engagement (%)",
        "engagement_total": "Engagement total",
        "engagement total": "Engagement total",
        "publishedAt": "published_at",
        "published_at": "published_at",
        "date_publication": "published_at",
        "categorie_id": "category_id",
        "categoryId": "category_id",
        "vues": "views",
        "views": "views",
        "chaine": "channel",
        "channel": "channel",
        "jour de la semaine": "Jour de la semaine",
        "Jour de la semaine": "Jour de la semaine",
        "heure": "Heure",
        "Heure": "Heure",
        "category_name": "cats.name",
        "categorie": "cats.name",
        "cats.name": "cats.name",
    }

    # Case-insensitive rename
    lower_to_actual = {c.lower(): c for c in df.columns}
    final_rename = {}
    for k, v in rename_map.items():
        if k in lower_to_actual:
            final_rename[lower_to_actual[k]] = v
    df = df.rename(columns=final_rename)

    return df

@st.cache_data(show_spinner=False)
def load_data(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame()

    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif name.endswith(".parquet"):
        df = pd.read_parquet(uploaded_file)
    else:
        raise ValueError("Format non supporté (CSV/Parquet uniquement).")

    df = normalize_columns(df)

    # Parse published_at to datetime (if present)
    if "published_at" in df.columns:
        df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True).dt.tz_convert(None)

    # Derive Year / Weekday / Hour if missing (PBIX slicers)
    if "published_at" in df.columns:
        if "Année" not in df.columns:
            df["Année"] = df["published_at"].dt.year
        if "Jour de la semaine" not in df.columns:
            # French weekday names
            fr_weekdays = {
                0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi",
                4: "Vendredi", 5: "Samedi", 6: "Dimanche"
            }
            df["Jour de la semaine"] = df["published_at"].dt.weekday.map(fr_weekdays)
        if "Heure" not in df.columns:
            df["Heure"] = df["published_at"].dt.hour

    # Coerce numeric columns
    for col in ["views", "Taux d'engagement (%)", "Engagement total"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def kpi_card(title: str, value: str, subtitle: str | None = None):
    sub_html = f'<div class="kpi-sub">{subtitle}</div>' if subtitle else '<div class="kpi-sub">&nbsp;</div>'
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-title">{title}</div>
          <div class="kpi-value">{value}</div>
          {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Sidebar (data import)
# -----------------------------
st.sidebar.header("Données")
uploaded = st.sidebar.file_uploader("Importer le dataset vidéos (CSV/Parquet)", type=["csv", "parquet"])

df = load_data(uploaded)

# -----------------------------
# Header area (logo + title like PBIX)
# -----------------------------
st.markdown('<div class="boostme-topbar"></div>', unsafe_allow_html=True)

h1, h2 = st.columns([1, 3])
with h1:
    # Optional logo from PBIX export
    try:
        st.image("assets/LOGO_BoostMe.png", use_container_width=True)
    except Exception:
        st.write("")
with h2:
    st.markdown(
        f"<div style='padding-top:18px; font-weight:800; font-size:1.05rem; color:{ORANGE};'>"
        "Niveau de performance actuel du contenu tendance sur Youtube"
        "</div>",
        unsafe_allow_html=True,
    )

if df.empty:
    st.info(
        "Importe ton dataset (CSV/Parquet) pour afficher les KPIs.\n\n"
        "Colonnes attendues (au minimum) :\n"
        "- category_id\n- views\n- Taux d'engagement (%)\n- Engagement total\n- channel\n- published_at\n\n"
        "Optionnel : cats.name (nom de catégorie), Jour de la semaine, Heure"
    )
    st.stop()

# -----------------------------
# Filters (inspired by PBIX slicers)
# -----------------------------
st.markdown(
    """
    <div class="boostme-sectionbar">
      <h2>Analyse des tendances</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])

# Year slicer (published_at year)
years = sorted([y for y in df.get("Année", pd.Series(dtype=int)).dropna().unique()])
with c1:
    year_sel = st.multiselect("Année", years, default=years[-1:] if years else years)

# Category name slicer
cats = sorted(df.get("cats.name", pd.Series(dtype=str)).dropna().unique())
with c2:
    cat_sel = st.multiselect("Catégorie", cats, default=[])

# Channel slicer
channels = sorted(df.get("channel", pd.Series(dtype=str)).dropna().unique())
with c3:
    ch_sel = st.multiselect("Chaîne", channels, default=[])

# Weekday slicer
weekdays = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
avail_weekdays = [d for d in weekdays if d in set(df.get("Jour de la semaine", pd.Series(dtype=str)).dropna().unique())]
with c4:
    day_sel = st.multiselect("Jour", avail_weekdays, default=[])

# Hour slicer
hours = sorted([int(h) for h in df.get("Heure", pd.Series(dtype=float)).dropna().unique() if pd.notna(h)])
with c5:
    hour_sel = st.multiselect("Heure", hours, default=[])

fdf = df.copy()

if year_sel and "Année" in fdf.columns:
    fdf = fdf[fdf["Année"].isin(year_sel)]
if cat_sel and "cats.name" in fdf.columns:
    fdf = fdf[fdf["cats.name"].isin(cat_sel)]
if ch_sel and "channel" in fdf.columns:
    fdf = fdf[fdf["channel"].isin(ch_sel)]
if day_sel and "Jour de la semaine" in fdf.columns:
    fdf = fdf[fdf["Jour de la semaine"].isin(day_sel)]
if hour_sel and "Heure" in fdf.columns:
    fdf = fdf[fdf["Heure"].isin(hour_sel)]

# -----------------------------
# KPIs (exactly the 4 cards in the PBIX)
# -----------------------------
k1, k2, k3, k4 = st.columns(4)

with k1:
    # Power BI: CountNonNull(videos.category_id)
    value = _fr_int(fdf["category_id"].notna().sum())
    kpi_card("Nombre total de vidéos analysées", value)

with k2:
    # Power BI: Avg(videos.views)
    value = _fr_int(fdf["views"].mean())
    kpi_card("Moyenne du nombre de vues par vidéo", value)

with k3:
    # Power BI: Avg(videos.Taux d'engagement (%))
    value = _fr_float(fdf["Taux d'engagement (%)"].mean(), decimals=2) + " %"
    kpi_card("Taux d'engagement moyen", value)

with k4:
    # Power BI: Sum(videos.Engagement total)
    value = _fr_int(fdf["Engagement total"].sum())
    kpi_card("Nombre total d'intéractions", value)

st.markdown("<br/>", unsafe_allow_html=True)

# -----------------------------
# (Optional) quick debug table
# -----------------------------
with st.expander("Voir un aperçu des données filtrées"):
    st.dataframe(fdf.head(200), use_container_width=True)
