# BoostMe Streamlit (KPIs)

Cette mini-app Streamlit reproduit les **4 KPI cards** du fichier Power BI (PBIX) BoostMe, avec un style proche :
- barre orange en haut
- cartes KPI avec bordure orange et coins arrondis
- titres identiques à ceux du PBIX
- filtres inspirés des slicers (Année, Catégorie, Chaîne, Jour, Heure)

## Lancer l'app

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Données attendues

Importe un CSV ou Parquet contenant au minimum :

- `category_id`
- `views`
- `Taux d'engagement (%)`
- `Engagement total`
- `channel`
- `published_at` (date/heure)

Optionnel (si dispo) :
- `cats.name` (nom de catégorie)
- `Jour de la semaine`
- `Heure`

> Si tes colonnes ont des variantes (ex: `taux_engagement`, `engagement_total`), l'app tente de les normaliser automatiquement.
