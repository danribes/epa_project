<p align="center">
  <h1 align="center">Spanish Labour Market Analysis (EPA)</h1>
  <p align="center">
    Exploratory Data Analysis (EDA) of the Spanish labour market<br>
    using open data from the <strong>Instituto Nacional de Estadística</strong> (INE)
  </p>
  <p align="center">
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python"></a>
    <a href="https://pandas.pydata.org/"><img src="https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white" alt="Pandas"></a>
    <a href="https://matplotlib.org/"><img src="https://img.shields.io/badge/Matplotlib-3.x-11557C" alt="Matplotlib"></a>
    <a href="https://seaborn.pydata.org/"><img src="https://img.shields.io/badge/Seaborn-0.13-4C72B0" alt="Seaborn"></a>
    <a href="https://servicios.ine.es/wstempus/js"><img src="https://img.shields.io/badge/Data-INE%20API-E4002B" alt="INE API"></a>
  </p>
</p>

---

## Objective

Understand the structure of the Spanish labour market by province, sex, and economic sector, its quarterly evolution, and the territorial and gender inequalities in employment and unemployment. The analysis period is **user-configurable** (default 2020–2025). The project is designed to work with **any period** of EPA data (quarterly from 2002 onwards).

## Quick Start

```bash
git clone https://github.com/danribes/epa_project.git
cd epa_project/
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py --fetch --start 2020 --end 2025
```

> This downloads the 6 EPA tables from the INE public API, runs cleaning, generates features, and produces the 9 charts in `charts/`.

## Dataset

| | Details |
|---|---|
| **Source** | INE public API — [servicios.ine.es/wstempus/js](https://servicios.ine.es/wstempus/js) |
| **Tables** | 65345 (population), 65349 (rates), 65354 (sectors), 65219 (unemployment by age), 65086 (active by nationality), 65112 (employed by nationality) |
| **Size** | ~40,700 rows x 8 cols (raw, 6 years) ➜ ~40,700 x 17 (after cleaning + features) |
| **Key variables** | province, sex, activity type, date (quarterly), value (thousands of people or %) |
| **Additional data** | Raw JSON API responses in `data/raw/` |

> **Methodological note (chart 9):** The INE API does not publish a table with unemployment rates broken down simultaneously by nationality and age group. To obtain them, tables 65086 (active) and 65112 (employed) were downloaded with the same dimensions (nationality x sex x age) and the rate was calculated as: `unemployment_rate = (active - employed) / active * 100`. The result was validated against the official table 65336 with an exact match.

## Research Questions

| # | Question | Chart |
|---|---|---|
| Q1 | Which provinces have the highest and lowest unemployment rates? Has the ranking changed? | 1, 6 |
| Q2 | Is there a gender gap in activity, employment, and unemployment rates? | 2 |
| Q3 | How is employment distributed by economic sector and how does it vary geographically? | 3 |
| Q4 | How has total employment evolved over the period? | 4, 5 |
| Q5 | Is there seasonality in employment/unemployment (quarterly)? | 6 |
| Q6 | How does the unemployment rate vary by age group? Are there differences by sex? | 7 |
| Q7 | How has youth unemployment (16–19 and 20–24) evolved compared to the total? | 8 |
| Q8 | Is there an unemployment gap between Spanish and foreign workers? | 9 |

## Data Issues & Fixes

| Issue | Fix |
|---|---|
| Dirty column names (spaces, uppercase) | `strip().lower().replace(' ', '_')` |
| Value as text with decimal comma (`203,2`) | `.str.replace(",", ".")` + `pd.to_numeric` |
| Dates in 5 different formats (ISO, dd/mm, ms, textual) | Custom parser with fallbacks |
| Serie_nombre with inconsistent casing | Parsing on `.lower()` version with canonical mapping |
| All dimensions packed into a single string | Regex parsing per table to extract province, sex, activity |
| ~3% nulls in value | Kept as NaN (not imputed) |
| 20 duplicate rows | `drop_duplicates()` by composite key |

## Pipeline

```
fetch_data.py ➜ raw CSV ➜ cleaning.py ➜ utils.py ➜ features.py ➜ data/processed/ ➜ viz.py ➜ charts/
```

The full pipeline — including generation of all 9 charts — runs with a single command:

```bash
python main.py --fetch --start 2020 --end 2025
```

## Findings

> **Note:** The findings below correspond to the default period (2020–2025). Running the project with a different period will produce different results.

| # | Finding | Chart |
|---|---|---|
| 1 | **Strong territorial inequality** — Southern provinces (Andalusia, Extremadura, Canary Islands) maintain significantly higher unemployment rates than northern ones (Basque Country, Navarre, Aragon). | 1, 6 |
| 2 | **Persistent but narrowing gender gap** — The female unemployment rate is consistently higher than the male rate, although the gap has been narrowing. | 2 |
| 3 | **Tertiarised economy** — The services sector overwhelmingly dominates employment (>75%), with agriculture, industry, and construction remaining stable. | 3 |
| 4 | **Positive total employment trend** — Total employment has shown an upward trajectory throughout the analysed period. | 5 |
| 5 | **Employment concentration** — Madrid and Barcelona account for a disproportionate share of employment. | 4 |
| 6 | **Extreme youth unemployment** — People under 25 suffer unemployment rates far above the national average (16–19: >30%, 20–24: ~22%, overall: ~10%). | 7 |
| 7 | **Declining youth unemployment trend** — Youth unemployment has fallen significantly, though it still triples (16–19) and doubles (20–24) the overall rate. | 8 |
| 8 | **Nationality gap across all age groups** — Foreign workers have higher unemployment rates than Spanish workers across all age groups. | 9 |

## Project Structure

```
epa_project/
├── fetch_data.py                     # Data download from INE
├── main.py                           # End-to-end pipeline
├── data/
│   ├── raw/                          # Raw JSON + raw/dirty CSV
│   └── processed/                    # Clean CSV (rows x 17)
├── charts/                           # 9 generated PNG charts
├── notebooks/
│   └── eda.ipynb                     # Interactive analysis notebook
├── src/
│   ├── __init__.py
│   ├── io.py                         # Data loading and saving
│   ├── cleaning.py                   # Data cleaning
│   ├── features.py                   # Feature engineering
│   ├── viz.py                        # Reusable charts
│   └── utils.py                      # Validations and utilities
├── epa_project_report.docx           # Full project report
├── README.md
└── requirements.txt
```

## How to Run

### Step 1 — Clone the repository

```bash
git clone https://github.com/danribes/epa_project.git
cd epa_project/
```

### Step 2 — Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Download INE data

```bash
python fetch_data.py --start 2020 --end 2025
```

This step downloads the 6 EPA tables from the INE public API, generating the raw JSON files and the raw and dirty CSVs in `data/raw/`. The `--start` and `--end` parameters define the year range to download.

### Step 5 — Run the cleaning + charts pipeline

```bash
python main.py
```

<details>
<summary>Expected output</summary>

```
Loading data from .../data/raw/epa_mercado_laboral_dirty.csv ...
  Shape raw: (40724, 8)
Cleaning data ...
  Shape clean: (40704, 10)
All validations passed.
Generating features ...
  Shape final: (40704, 17)
Saved to .../data/processed/epa_mercado_laboral_clean.csv

Generating charts ...
  -> 01_tasa_paro_por_provincia.png
  -> 02_brecha_genero_paro.png
  -> 03_empleo_por_sector.png
  -> 04_distribucion_ocupados.png
  -> 05_evolucion_empleo_total.png
  -> 06_heatmap_paro_ccaa.png
  -> 07_paro_por_edad.png
  -> 08_paro_juvenil_evolucion.png
  -> 09_paro_edad_nacionalidad.png
Charts saved in charts/
```
</details>

Alternatively, download + cleaning + charts can be combined in a single command:

```bash
python main.py --fetch --start 2020 --end 2025
```

### Step 6 — Explore the notebook (optional)

```bash
pip install jupyter
jupyter notebook notebooks/eda.ipynb
```

## Reproducing with a Different Period

The project is designed to work with **any period** of EPA data. To change the time range:

> **Important:** The EPA publishes quarterly data **from 2002 onwards**. If a start year before 2002 is specified, the INE API will simply return data from 2002 onwards without raising an error.

### Step by step

1. **Choose the period.** The EPA publishes quarterly data from 2002. Example: 2015–2020.

2. **Download the data.** The `fetch_data.py` script connects to the INE API using the `date=YYYYMMDD:YYYYMMDD` parameter to request the exact range.

   ```bash
   python fetch_data.py --start 2015 --end 2020
   ```

   This downloads the 6 tables and generates:
   - `data/raw/*.json` — raw JSON API responses (one per table)
   - `data/raw/epa_mercado_laboral_raw.csv` — clean combined CSV
   - `data/raw/epa_mercado_laboral_dirty.csv` — CSV with intentional dirt

3. **Run the pipeline.** The cleaning, features, and charts code is completely period-agnostic — it contains no hardcoded dates. All 9 charts are generated automatically in `charts/`.

   ```bash
   python main.py
   ```

4. **Explore the notebook (optional).** The `eda.ipynb` notebook reads from the dirty CSV and adapts automatically to the downloaded period:
   - **Chart titles** all include the temporal range detected in the data (e.g. "2015–2020").
   - **Charts 7–9** (age, youth, nationality) read the raw JSONs and adapt to the period.
   - **Conclusions** are written in a period-agnostic way.
   - No notebook cells need to be modified.

   ```bash
   jupyter notebook notebooks/eda.ipynb
   ```

### Tables downloaded by `fetch_data.py`

| INE Table | Description | Use |
|---|---|---|
| 65345 | Population 16+ by activity, sex and province | Main CSV |
| 65349 | Activity/unemployment/employment rates by province and sex | Main CSV |
| 65354 | Employed by economic sector and province | Main CSV |
| 65219 | Unemployment rates by sex and age group | Charts 7–8 |
| 65086 | Active by nationality, sex and age group | Chart 9 (merge) |
| 65112 | Employed by nationality, sex and age group | Chart 9 (merge) |

### Usage examples

```bash
# Original project period
python fetch_data.py --start 2020 --end 2025

# 2008 financial crisis
python fetch_data.py --start 2008 --end 2014

# Pre-pandemic
python fetch_data.py --start 2015 --end 2020

# Long range (20 years)
python fetch_data.py --start 2005 --end 2025

# Download only, without generating dirty CSV
python fetch_data.py --start 2020 --end 2025 --no-dirty

# Fetch + cleaning in a single command
python main.py --fetch --start 2015 --end 2020
```

### Period-adaptive design

All project code is **period-agnostic**. It contains no hardcoded dates:

| Component | Adaptation mechanism |
|---|---|
| `fetch_data.py` | `--start` / `--end` parameters to define the range |
| `src/cleaning.py` | Date and dimension parsing with no reference to specific years |
| `src/features.py` | Generic temporal feature engineering (quarter, month, year) |
| `src/viz.py` | Generates all 9 charts with titles that include the temporal range detected in the data |
| `main.py` | Orchestrates the full pipeline (fetch + clean + features + charts) in a single command |
| `notebooks/eda.ipynb` | Derives `PERIOD_LABEL` from the data and uses it in all chart titles |

### Important notes

- The INE API is public and free; no API key is required.
- The script includes automatic retries (3 attempts with exponential backoff) and a 1s courtesy delay between requests.
- **EPA data is available quarterly from 2002.** If `--start` is set to a year before 2002, the INE API will return data from 2002 onwards without raising an error.
- The full pipeline (`main.py`) runs cleaning, features, and generation of all 9 charts in `charts/`. All components are period-agnostic: they contain no hardcoded dates.
- The intentional dirt in the dirty CSV is deterministic (seed=42), so running twice with the same period produces exactly the same file.
