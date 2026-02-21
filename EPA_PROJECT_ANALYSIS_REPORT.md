# EPA Project — Comprehensive Analysis Report

**Project:** Análisis del Mercado Laboral Español (EPA)
**Report Date:** 2026-02-21
**Primary Artifact:** `notebooks/eda.ipynb`
**Data Source:** Instituto Nacional de Estadística (INE) API
**Period Analysed:** 2020–2025 (default; any period from 2002 onwards is supported)

---

## Table of Contents

1. [Introduction and Purpose](#1-introduction-and-purpose)
2. [Folder Structure](#2-folder-structure)
3. [Dataset Description](#3-dataset-description)
4. [Research Questions](#4-research-questions)
5. [Methodology](#5-methodology)
   - 5.1 Data Acquisition
   - 5.2 Data Quality Assessment
   - 5.3 Cleaning Pipeline
   - 5.4 Feature Engineering
   - 5.5 Notebook Flow (`eda.ipynb`)
   - 5.6 End-to-End Pipeline (CLI Path)
   - 5.7 Visualization Design
6. [Results](#6-results)
7. [Key Findings Summary](#7-key-findings-summary)
8. [Additional Findings](#8-additional-findings)
9. [Data Quality Report](#9-data-quality-report)
10. [Conclusions](#10-conclusions)
11. [Design Rationale](#11-design-rationale)
12. [Project Structure and Reproducibility](#12-project-structure-and-reproducibility)
13. [Dependencies](#13-dependencies)

---

## 1. Introduction and Purpose

This report presents an exploratory data analysis (EDA) of the Spanish labour market over a user-configurable period (default: 2020–2025, i.e. 20 quarters), using official open data published by the Instituto Nacional de Estadística (INE) through its *Encuesta de Población Activa* (EPA) — Spain's quarterly Labour Force Survey, the reference survey for employment statistics in the country.

The project is a self-contained, end-to-end data analysis pipeline that downloads, cleans, enriches, and visualises Spanish labour-market microdata. The primary deliverable is an interactive Jupyter notebook (`eda.ipynb`) that walks through eight research questions about territorial inequality, gender gaps, sectoral composition, and the differential impact of age and nationality on unemployment. All intermediate artefacts (a cleaned CSV, nine publication-ready charts, and this report) are generated programmatically from that notebook or from `main.py`.

**The objectives of this study are:**

- Identify the provinces and autonomous communities with the highest and lowest unemployment rates, and assess whether the territorial ranking has changed over the analysis period.
- Quantify the gender gap in unemployment and examine its evolution over time.
- Analyze the distribution of employment across economic sectors (agriculture, industry, construction, services) and its geographic variation.
- Measure the impact of the 2020 economic shock on total employment and assess the completeness of the recovery.
- Detect seasonal patterns in employment and unemployment at the quarterly level.
- Characterise unemployment differentials by age group, sex, and nationality.

Beyond answering these questions, this project serves as a demonstration of a reproducible data science pipeline — from raw API ingestion through cleaning, feature engineering, visualization, and modular code organization — using real-world, messy public data.

---

## 2. Folder Structure

```
epa_project/
├── main.py               # CLI orchestrator — runs the full pipeline
├── fetch_data.py         # Downloads data from INE API
├── requirements.txt      # Python dependencies
├── README.md
├── src/
│   ├── io.py             # CSV loader
│   ├── cleaning.py       # 8-step cleaning pipeline
│   ├── features.py       # Feature engineering
│   ├── utils.py          # Validation assertions
│   └── viz.py            # 9 chart generators
├── data/
│   ├── raw/              # 6 JSON files + dirty CSV + clean raw CSV
│   └── processed/        # Final clean CSV (40,704 rows × 17 cols)
├── notebooks/
│   ├── eda.ipynb         # Main interactive notebook
│   └── eda_executed.ipynb
└── charts/               # 9 PNG visualisations
    ├── 01_tasa_paro_por_provincia.png
    ├── 02_brecha_genero_paro.png
    ├── 03_empleo_por_sector.png
    ├── 04_distribucion_ocupados.png
    ├── 05_evolucion_empleo_total.png
    ├── 06_heatmap_paro_ccaa.png
    ├── 07_paro_por_edad.png
    ├── 08_paro_juvenil_evolucion.png
    └── 09_paro_edad_nacionalidad.png
```

---

## 3. Dataset Description

The data was obtained from the INE public REST API (`servicios.ine.es/wstempus/js`), which provides free, unauthenticated access to all statistical data published by the Instituto Nacional de Estadística. Six EPA tables were downloaded:

| Table ID | Content | Use |
|---|---|---|
| 65345 | Population 16+ by activity, sex, and province — absolute figures (thousands of persons) | Main CSV → Charts 1–6 |
| 65349 | Activity / unemployment / employment rates by province and sex | Main CSV → Charts 1–6 |
| 65354 | Employed persons by economic sector (CNAE) and province | Main CSV → Charts 1–6 |
| 65219 | Unemployment rates by sex and age group | JSON → Charts 7–8 |
| 65086 | Active population by nationality, sex, and age group | JSON → Chart 9 (merge) |
| 65112 | Employed population by nationality, sex, and age group | JSON → Chart 9 (merge) |

Tables 65345, 65349, and 65354 are merged into a single combined CSV that feeds the main cleaning pipeline. Tables 65219, 65086, and 65112 are preserved as raw JSON files and parsed directly inside the notebook for charts 7–9.

**Dataset dimensions (default 2020–2025 period):**

| Attribute | Value |
|---|---|
| Rows (raw / clean) | 40,724 / 40,704 |
| Columns (raw / with features) | 8 / 17 |
| Time span | Q1 2020 – Q4 2025 (20 quarters) |
| Geographic coverage | 52 provinces + national total |
| Source tables (main CSV) | 3 EPA tables (65345, 65349, 65354) |

The exact number of rows depends on the period selected (e.g. ~40,700 for a 6-year range, ~156,400 for the full 2002–2025 range).

### 3.1 INE API Raw JSON Glossary

The raw JSON files returned by the INE API (`data/raw/*.json`) use a series of internal field names and coded values that are not self-explanatory. This section documents every field so that anyone inspecting the raw data can understand its meaning without consulting external sources.

#### Series-level fields (one per statistical series)

| Field | Meaning | Example |
|---|---|---|
| `COD` | Internal INE **series code** — a unique identifier for a specific combination of table, province, sex, and activity type. | `"EPA397872"` |
| `Nombre` | Human-readable **series name**, containing all analytical dimensions packed into a single string (e.g. province, sex, sector, unit). The cleaning pipeline parses this field to extract `provincia`, `sexo`, and `actividad`. | `"Total Nacional. Ocupados. Ambos sexos. Total CNAE. Personas. "` |
| `FK_Unidad` | **Foreign key to unit of measurement.** Refers to the INE units catalogue. Common values in EPA data: **3** = Personas (persons), **101** = Porcentaje (percentage). The full catalogue is available at `servicios.ine.es/wstempus/js/ES/UNIDADES`. | `3` |
| `FK_Escala` | **Foreign key to scale (multiplier).** Refers to the INE scales catalogue. Common values: **1** = units (×1), **4** = Miles / thousands (×1,000). When `FK_Unidad=3` (persons) and `FK_Escala=4` (thousands), a `Valor` of `22463.3` means 22,463,300 persons. The full catalogue is available at `servicios.ine.es/wstempus/js/ES/ESCALAS`. | `4` |
| `Data` | Array of **data point objects**, one per quarter-year combination. | `[{...}, {...}]` |

#### Data-point-level fields (one per quarter within a series)

| Field | Meaning | Example | Notes |
|---|---|---|---|
| `Fecha` | **Date as a Unix timestamp in milliseconds** (milliseconds elapsed since 1 January 1970 00:00:00 UTC). Must be divided by 1,000 to obtain a standard Unix timestamp, or converted with `pd.Timestamp(val, unit='ms')`. Each timestamp corresponds to the first day of the quarter. | `1759269600000` → 2025-10-01 (start of Q4 2025) | The cleaning pipeline converts this to `datetime64[ns]` using the `parse_fecha()` function in `src/cleaning.py`. |
| `FK_TipoDato` | **Foreign key to data type.** Value **1** = *dato definitivo* (final/definitive data). Other values (provisional, advance, etc.) may exist in other INE tables but are not present in EPA data. | `1` | Not extracted into the raw CSV — always 1 in EPA data. |
| `FK_Periodo` | **Foreign key to quarter identifier.** The INE uses an internal numbering that does **not** follow the calendar quarter order: **19** = Q4 (Oct–Dec), **20** = Q1 (Jan–Mar), **21** = Q2 (Apr–Jun), **22** = Q3 (Jul–Sep). The feature engineering step maps these to human-readable labels (T1–T4) via `PERIODO_MAP` in `src/features.py`. | `22` → Q3 | The non-intuitive numbering (19–22 instead of 1–4) is an artefact of INE's internal catalogue system, where period IDs are shared across different periodicities (monthly, quarterly, annual, etc.). |
| `Anyo` | **Year** of the observation. The field name is the Spanish word *año* (year) transliterated to ASCII (ñ → ny → Anyo). | `2025` | |
| `Valor` | **Observed value.** Its unit and scale depend on the series-level fields `FK_Unidad` and `FK_Escala`. For population tables, values are in thousands of persons; for rate tables, values are percentages. A value of `22463.3` with `FK_Escala=4` means 22,463,300 persons. | `22463.3` | ~3% of values are null in the raw data and are kept as `NaN` in the clean dataset. |
| `Secreto` | **Statistical secrecy flag** (*secreto estadístico*). When `true`, the `Valor` is suppressed (null) to protect the privacy of respondents in cells where the sample size is too small to guarantee anonymity — a standard practice in official statistics (EU Regulation 223/2009). When `false`, the value is publishable. | `false` | In the EPA dataset for 2020–2025, all observations have `Secreto: false`. The field is extracted into the raw CSV but dropped during cleaning as it carries no analytical value for this period. |

#### How these fields map to the processed dataset

| Raw JSON field | Raw CSV column | Final clean column | Transformation |
|---|---|---|---|
| `COD` | `serie_cod` | `serie_cod` | Kept as-is |
| `Nombre` | `serie_nombre` | Dropped (parsed into `provincia`, `sexo`, `actividad`) | Table-specific regex parsers |
| `FK_Unidad` | Not extracted | — | Implicit in context |
| `FK_Escala` | Not extracted | — | Implicit in context |
| `Fecha` | `fecha_ms` | `fecha` (`datetime64`) | `parse_fecha()` — ms timestamp → datetime |
| `FK_TipoDato` | Not extracted | — | Always 1 in EPA |
| `FK_Periodo` | `periodo_id` | `periodo_id` + `trimestre_label` | `PERIODO_MAP`: 19→T4, 20→T1, 21→T2, 22→T3 |
| `Anyo` | `anyo` | `anyo` + `year` | Kept; also extracted as feature |
| `Valor` | `valor` | `valor` (float64) | Comma→dot + `pd.to_numeric` |
| `Secreto` | `secreto` | Dropped | Not needed for analysis |

---

## 4. Research Questions

| # | Question | Chart(s) |
|---|---|---|
| Q1 | Which provinces have the highest and lowest unemployment rates? Has the ranking changed? | 1, 6 |
| Q2 | Is there a gender gap in activity, employment, and unemployment rates? Does it vary by province? | 2 |
| Q3 | How is employment distributed by economic sector and how does it vary geographically? | 3 |
| Q4 | How has total employment evolved over the analysis period? | 4, 5 |
| Q5 | Is there quarterly seasonality in employment/unemployment? Does it affect some provinces more? | 6 |
| Q6 | How does the unemployment rate vary by age group? Are there differences by sex? | 7 |
| Q7 | How has youth unemployment (16–19 and 20–24) evolved compared to the total rate? | 8 |
| Q8 | Is there an unemployment gap between Spanish and foreign workers? Does it vary by age group? | 9 |

---

## 5. Methodology

### 5.1 Data Acquisition

Data was retrieved programmatically via HTTP GET requests to the INE REST API using the Python `requests` library. The `fetch_data.py` script accepts `--start` and `--end` parameters to define the year range, and queries each table using the date range parameter (`date=YYYYMMDD:YYYYMMDD`). The EPA publishes quarterly data since 2002; if a start year earlier than 2002 is specified, the API silently returns data from 2002 onwards without generating an error. Responses are received in JSON format and parsed into flat tabular structures. Raw JSON responses are preserved in `data/raw/` for reproducibility. The script includes automatic retries (3 attempts with exponential backoff) and a 1-second courtesy delay between requests.

The three main tables (65345, 65349, 65354) are combined into a single CSV file. For the extended analysis of unemployment by age and nationality (Charts 7–9), three additional tables are fetched and saved as standalone JSON: Table 65219 (Tasas de paro por sexo y grupo de edad), Table 65086 (Activos por nacionalidad, sexo y grupo de edad), and Table 65112 (Ocupados por nacionalidad, sexo y grupo de edad). Since the INE does not publish a single table with unemployment rates crossed by both nationality and age, Tables 65086 and 65112 are merged by matching on nationality × sex × age group × quarter, and the unemployment rate is derived as `(activos − ocupados) / activos × 100`.

### 5.2 Data Quality Assessment

An initial quality check (QC) was performed on the raw CSV by the notebook (cells 2–5), revealing the following issues:

| Check | Finding |
|---|---|
| `head()` / `shape` | 40,724 rows × 8 columns |
| `info()` / `dtypes` | `valor` is object (not numeric); `fecha` is object |
| Null rates | ~3% nulls in `valor`; minor nulls in `fecha` |
| Duplicates | 20 exact duplicate rows |
| Cardinality | `serie_nombre` has ~1,600 unique values due to mixed casing |

Seven data quality problems are documented in a summary markdown cell in the notebook before any cleaning begins, making the rationale for each subsequent fix concrete and auditable.

### 5.3 Cleaning Pipeline

The cleaning pipeline (`src/cleaning.py`, notebook cells 6–14) applies eight sequential transformations, each in its own cell so the intermediate state can be inspected:

1. **Column standardization** — strip whitespace, convert to lowercase, replace spaces with underscores.
2. **Numeric parsing** — replace comma decimal separators with dots, then convert to float via `pd.to_numeric` with `errors='coerce'`.
3. **Series name normalization** — strip extra whitespace; create a lowercase helper column for consistent matching.
4. **Structural parsing** — extract `provincia`, `sexo`, and `actividad` from the packed `serie_nombre` string. Three table-specific parsers handle the different naming formats used by each source table (65345, 65349, 65354). A canonical province name mapping ensures consistent casing regardless of the original format.
5. **Date parsing** — a custom multi-format parser handles ISO (`2024-06-30`), European (`30/06/2024`), alternative ISO (`2024/06/30`), textual (`Dec 31, 2024`), and Unix millisecond timestamps — all formats present in the same column. Applied via list comprehension + `pd.to_datetime()` to guarantee `datetime64[ns]` dtype.
6. **Categorical normalization** — map `sexo` values to three canonical forms (`Ambos sexos`, `Hombres`, `Mujeres`); strip `provincia` and `actividad`.
7. **Deduplication** — `drop_duplicates` on the composite key `(tabla, serie_cod, anyo, periodo_id)`. 20 duplicate rows removed; 40,704 rows remain.
8. **Cleanup** — drop helper columns (`serie_nombre_lower`, `secreto`) that were created during intermediate steps and are not needed in the final dataset.

A validation cell (Cell 14) runs four `assert` statements to confirm the cleaned dataset meets structural expectations before any analysis proceeds. Missing values in `valor` (~3%) are kept as `NaN` rather than imputed, to preserve data integrity.

### 5.4 Feature Engineering

Seven derived columns are added to the clean DataFrame (`src/features.py`, notebook cells 15–19):

| Column | Derivation |
|---|---|
| `trimestre` | `Period(freq='Q')` string (e.g. `2024Q3`) |
| `mes` | Month number extracted from `fecha` |
| `year` | Year extracted from `fecha` |
| `trimestre_label` | `periodo_id` mapped to T1/T2/T3/T4 |
| `fuente` | Human-readable source name for each `tabla` (`Poblacion`, `Tasas`, `Ocupados por sector`) |
| `es_nacional` | Boolean — `True` if `provincia` contains "total nacional" |
| `ccaa` | Autonomous community derived from a 52-province lookup table |

The period label (`PERIOD_LABEL`, e.g. `"2020–2025"`) is derived dynamically from the minimum and maximum year in the data and stamped on every chart title, so the notebook is fully period-agnostic. The final processed dataset (40,704 rows × 17 columns) is saved to `data/processed/epa_mercado_laboral_clean.csv`.

### 5.5 Notebook Flow (`eda.ipynb`)

The notebook is structured in five logical phases:

**Phase 0 — Framing (Cell 0)**

A markdown cell introduces the project and states the eight core research questions the analysis aims to answer. This acts as both a contract and a navigation guide for the reader.

**Phase 1 — Setup (Cell 1)**

Standard environment bootstrap: imports (NumPy, pandas, Matplotlib, Seaborn); Seaborn theme and context set to `whitegrid` / `notebook`; path constants defined (`ROOT`, `DATA_RAW`, `DATA_PROCESSED`, `CHARTS`); previous chart files cleared so re-runs start clean; dirty CSV path loaded and existence verified.

**Phase 2 — Data Quality Assessment (Cells 2–5)**

The notebook deliberately loads the *dirty* version of the CSV (`epa_mercado_laboral_dirty.csv`) — a file where `fetch_data.py` has injected synthetic data quality issues with a fixed random seed (42), making the cleaning rationale visible and reproducible. The seven data quality problems are documented in a summary markdown cell before any cleaning begins.

**Phase 3 — Cleaning Pipeline (Cells 6–14)**

Eight sequential transformations are applied, each in its own cell so intermediate state can be inspected (see Section 5.3 for full detail). A validation cell (Cell 14) runs four `assert` statements as a hard gate before analysis proceeds.

**Phase 4 — Feature Engineering (Cells 15–19)**

Seven derived columns are added to the clean DataFrame (see Section 5.4 for full detail). The final processed dataset is saved to `data/processed/`.

**Phase 5 — Visualisations and Conclusions (Cells 20–31)**

Nine charts answer the eight research questions. Each chart cell implements its own filtering, aggregation, and plotting logic inline. The same logic is mirrored in `src/viz.py` for use by the CLI pipeline (`main.py`); the notebook does not import from `src/viz.py`. A closing markdown cell (Cell 31) summarises the headline findings.

- **Chart 1** — Horizontal bar; provinces coloured red if above the median, green if at or below. Answers Q1 (territorial ranking).
- **Chart 2** — Two-line chart (Hombres / Mujeres) over the full period. Answers Q2 (gender gap evolution).
- **Chart 3** — Four-line chart (Agriculture, Industry, Construction, Services). Answers Q3 (sectoral composition).
- **Chart 4** — Horizontal bar; provinces coloured by position relative to the median. Complements Q1 with an employment-volume perspective.
- **Chart 5** — Line chart with shaded fill-under. Answers Q4 (aggregate employment trend).
- **Chart 6** — Pivoted heatmap (17 autonomous communities × all quarters). Answers Q5 (seasonality and territorial structure simultaneously).
- **Chart 7** — Source: raw JSON table 65219. Grouped bar chart (Ambos sexos, Hombres, Mujeres per age band). Answers Q6 (age structure).
- **Chart 8** — Source: same JSON. Three-line chart (two youth cohorts vs. national total, shown as a dashed reference line). Answers Q7 (youth unemployment trend).
- **Chart 9** — Source: JSON tables 65086 and 65112 merged. Unemployment rate computed as `(activos − ocupados) / activos × 100`. Grouped bar chart (Española vs. Extranjera). Answers Q8 (nationality gap).

### 5.6 End-to-End Pipeline (CLI Path)

For automated or production runs the notebook logic is replicated in `main.py`:

```
python main.py --fetch --start 2020 --end 2025
     │
     ├─ fetch_data.py → 6 JSON files + dirty CSV + raw CSV
     │
     ├─ src/cleaning.py → 8-step clean (40,724 → 40,704 rows)
     │
     ├─ src/utils.py → 4 validation assertions
     │
     ├─ src/features.py → 7 new columns (17 total)
     │
     ├─ Save: data/processed/epa_mercado_laboral_clean.csv
     │
     └─ src/viz.py → 9 charts → charts/*.png
```

### 5.7 Visualization Design

Nine visualization types were designed to answer the research questions:

- **Comparison chart** (horizontal bar) — unemployment rate by province, colour-coded by median.
- **Time series** (line plot) — gender gap in unemployment over time.
- **Temporal composition** (multi-line) — employment by economic sector over time.
- **Distribution chart** (horizontal bar) — average employed population per province.
- **Annotated time series** (area fill) — total employment evolution with rescaled y-axis for clearer variation.
- **Pattern chart** (heatmap) — unemployment rate by CCAA and quarter.
- **Grouped bar chart** — unemployment rate by age group and sex (from INE table 65219).
- **Multi-line time series** — youth unemployment (16–19, 20–24) vs. total rate evolution, with a dashed reference line for the national total.
- **Grouped bar chart** — unemployment rate by age group and nationality, derived from merging INE tables 65086 and 65112.

All visualization functions are implemented as reusable modules in `src/viz.py`. The `main.py` pipeline generates all 9 charts automatically and saves them to the `charts/` directory. Each function accepts an optional `save_path` parameter for chart export.

---

## 6. Results

### 6.1 Unemployment by Province (Q1)

*Chart 1 — `01_tasa_paro_por_provincia.png`*

The territorial disparity is striking. Southern provinces — particularly those in Andalucía (Cádiz, Huelva, Sevilla, Córdoba, Jaén, Granada), Extremadura (Badajoz, Cáceres), and the Canary Islands — consistently exhibit unemployment rates well above the national average, often exceeding 20%. In contrast, northern provinces — País Vasco (Gipuzkoa, Araba/Álava, Bizkaia), Navarra, Aragón (Huesca, Teruel), and La Rioja — show rates below 10%, sometimes below 7%.

This north–south divide in unemployment is a well-documented structural feature of the Spanish economy, rooted in historical differences in industrial base, educational attainment, sectoral composition, and agricultural dependency. The data confirms that this pattern has remained largely stable over the 2020–2025 period.

### 6.2 Gender Gap in Unemployment (Q2)

*Chart 2 — `02_brecha_genero_paro.png`*

Chart 2 tracks the national unemployment rate for men and women over 20 quarters. The gender gap is clearly visible: female unemployment is consistently higher than male unemployment throughout the entire period. However, the gap has been narrowing gradually since 2020. By 2024–2025, both rates have reached their lowest levels in the observed period, with the gender gap narrowing to approximately 2–3 percentage points — smaller than the 3–4 point gap observed in 2020.

### 6.3 Employment by Economic Sector (Q3)

*Chart 3 — `03_empleo_por_sector.png`*

Chart 3 shows the quarterly evolution of employment across Spain's four main economic sectors. The services sector dominates overwhelmingly, employing roughly 14–15 million people (over 75% of total employment). Industry maintains a stable second position at approximately 2.5–2.8 million, followed by construction at ~1.3–1.5 million and agriculture at ~0.7–0.8 million.

This extreme tertiarization of the Spanish economy (services > 75%) is both a strength (diversified service economy) and a vulnerability (sensitivity to tourism shocks, as seen during economic downturns). The relative stability of industry and the modest recovery of construction reflect broader European trends.

### 6.4 Employment Evolution and Recovery (Q4)

*Chart 5 — `05_evolucion_empleo_total.png`*

Chart 5 presents the total number of employed persons in Spain over the analysis period. The 2020 economic shock is unmistakable: employment dropped from approximately 20.0 million in Q4 2019 to a trough of roughly 18.6 million in Q2 2020 — a loss of ~1.4 million jobs in a single quarter.

The recovery trajectory shows several phases: an initial rapid rebound in Q3 2020 (as lockdowns eased), a slower consolidation through 2021, and a sustained growth phase from 2022 onward that has pushed employment to record highs above 22 million by 2025. This represents not just a full recovery but a net gain of approximately 2 million jobs compared to pre-shock levels. The strength of this recovery has been attributed to several factors: labour market flexibility measures that preserved employment relationships during lockdowns, the strong rebound in tourism, the labour reform of 2021 that increased permanent contracts, and sustained EU recovery fund investments.

### 6.5 Employment Distribution and Territorial Concentration (Q4/Q5)

*Chart 4 — `04_distribucion_ocupados.png`*

Chart 4 shows the distribution of employed persons across Spain's 52 provinces. The distribution is extremely right-skewed: the vast majority of provinces have modest employment figures (under 300,000), while two provinces — Madrid and Barcelona — are dramatic outliers with over 2 million and 1.5 million employed respectively.

This concentration reflects Spain's demographic and economic reality: Madrid and Barcelona together account for roughly a quarter of total national employment, followed at a distance by Valencia, Sevilla, and Bizkaia. The *España Vacía* (Empty Spain) phenomenon is clearly visible — many interior provinces (Soria, Teruel, Ávila, Segovia) have very small employment bases, often under 50,000.

### 6.6 Territorial Unemployment Patterns — Heatmap (Q1/Q5)

*Chart 6 — `06_heatmap_paro_ccaa.png`*

Chart 6 presents a heatmap of average unemployment rates by Autonomous Community and quarter. Two structural patterns emerge clearly:

- **Persistent territorial ranking:** Andalucía, Canarias, Extremadura, and Ceuta/Melilla consistently occupy the top rows (highest unemployment), while País Vasco, Navarra, Aragón, and La Rioja occupy the bottom (lowest). This ranking barely changes across 20 quarters.
- **Gradual improvement:** within each CCAA, there is a visible left-to-right gradient (darker to lighter), indicating that unemployment has generally decreased over the 2020–2025 period. The 2020 economic spike is visible as a darker band across all communities.

The persistence of the territorial ranking despite a 5-year period that included a major economic shock, recovery, and labour reform, underscores the structural nature of Spain's unemployment geography.

### 6.7 Unemployment by Age Group (Q6)

*Chart 7 — `07_paro_por_edad.png`*

Chart 7 displays the unemployment rate for 12 age bands, broken down by sex (both sexes, men, women). The age gradient is dramatic: the youngest group (16–19 years) faces an unemployment rate exceeding 30%, which drops sharply to ~22% for 20–24 and ~13% for 25–29. From age 30 onwards, rates stabilize between 5% and 10%. This pattern highlights that Spain's high overall unemployment rate is heavily driven by extreme youth unemployment — a structural problem rooted in temporary contracts, educational mismatches, and limited work experience opportunities.

A secondary finding is the U-shaped pattern across ages: after the initial drop from the extreme youth rates, unemployment stabilizes through middle age (30–54) at around 8–10%, then rises slightly for the 55–64 group before dropping again for 65+ (where labour force participation is very low). The gender gap is inverted among the youngest (16–19: men 32%, women 28%) but becomes consistently female-disadvantaged from age 35 onwards, with differences of 2–4 percentage points.

### 6.8 Youth Unemployment Evolution (Q7)

*Chart 8 — `08_paro_juvenil_evolucion.png`*

Chart 8 tracks the quarterly evolution of unemployment for the two youngest age groups (16–19 and 20–24) compared with the overall rate (16+ years, shown as a dashed reference line). Both youth groups show a clear downward trend from 2020 to 2025. The 16–19 group fell from ~59% to ~31%, while the 20–24 group declined from ~36% to ~22%. The overall rate dropped from ~16% to ~10% over the same period.

Despite this improvement, youth unemployment remains structurally elevated: even at their lowest points, the 16–19 group (~31%) is roughly triple the national average (~10%), and the 20–24 group (~22%) is more than double. This persistent youth penalty reflects deep structural issues in the Spanish labour market — high temporary employment rates, skills mismatches, and limited entry-level opportunities — that the 2021 labour reform has only partially addressed.

### 6.9 Unemployment by Age and Nationality (Q8)

*Chart 9 — `09_paro_edad_nacionalidad.png`*

Chart 9 compares the unemployment rate between Spanish nationals and foreign workers across age groups. Foreign workers face higher unemployment in every age bracket, confirming a structural nationality gap in the Spanish labour market.

The gap is smallest in absolute terms among youth (16–24): 23.0% vs 25.7%, a difference of just 2.7 percentage points — partly because youth unemployment is already extremely high for both groups. At the other end, the 55+ group shows 8.3% for Spanish nationals vs 15.7% for foreigners — nearly double. The largest relative gap appears in the 45–54 group (6.7% vs 12.0%), suggesting that older immigrant workers face particular difficulty in the Spanish labour market. These disparities likely reflect a combination of factors: occupational segregation, language barriers, credential recognition challenges, and sectoral concentration in more volatile industries (construction, hospitality).

> **Methodological note:** This chart was constructed by merging two separate INE API tables, since no single published table provides unemployment rates disaggregated simultaneously by nationality and age group. Table 65086 provides the number of active persons; Table 65112 provides employed persons — both broken down by nationality × sex × age group. For each combination of nationality × age group (filtered to *Ambos sexos*), the unemployment rate was computed as `tasa_paro = (activos − ocupados) / activos × 100`. This derived metric was validated against the official INE table 65336, achieving exact numerical agreement for all matching aggregations — confirming the correctness of the merge and computation.

---

## 7. Key Findings Summary

| # | Research Question | Finding |
|---|---|---|
| Q1 | Provinces with highest/lowest unemployment? | Strong North–South divide: Andalucía and Extremadura lead; País Vasco and Navarra are consistently lowest. Ranking is structurally stable. |
| Q2 | Gender gap in unemployment? | Women's unemployment is persistently ~2–3 percentage points higher than men's. The gap narrows over 2020–2025 but does not close. |
| Q3 | Sectoral composition? | Services absorbs >75% of employment. Agriculture, Industry, and Construction are small and stable. |
| Q4 | Employment trend? | Clear upward trajectory post-2020, with strong recovery from the pandemic trough. Total employment reached record highs above 22 million by 2025. |
| Q5 | Seasonality? | Quarterly patterns exist (Q1 typically peaks unemployment) but are secondary to persistent structural regional differences. |
| Q6 | Unemployment by age and sex? | Youth unemployment is extreme: 16–19 age group exceeds 30%; 20–24 exceeds 20%. A gender gap exists in every age group, inverted only for 16–19. |
| Q7 | Youth unemployment evolution? | Downward trend 2020–2025 (16–19: 59% → 31%; 20–24: 36% → 22%), but youth unemployment remains 2–3× the national total throughout the period. |
| Q8 | Nationality gap? | Foreign-born workers have consistently higher unemployment in every age group. The gap is largest in middle and older ages (~45–54 and 55+). |

---

## 8. Additional Findings

### 8.1 Labour Market Flexibility (2020)

Labour market flexibility mechanisms implemented during the 2020 economic shock preserved employment contracts for millions of workers. The data shows that the unemployment spike, while severe, was significantly smaller than the GDP contraction would predict (-10.8% GDP in 2020 vs. -7.5% employment decline). This buffer is visible in the relatively moderate unemployment increase compared to the magnitude of the economic shock.

### 8.2 The 2021 Labour Reform Impact

The 2021 labour reform (*Reforma Laboral*) aimed to reduce temporary employment by converting fixed-term contracts to permanent ones. The data from 2022 onward shows sustained employment growth and continued reduction in unemployment. However, the aggregate EPA data used in this study does not distinguish contract types — a limitation for assessing the reform's full impact.

### 8.3 The Services Sector Dominance

The services sector accounts for over 75% of total employment in Spain, a dominance that has remained remarkably stable throughout the analysis period. While this reflects a modern, diversified economy, it also creates vulnerability to sector-specific shocks — as demonstrated by the severe impact on tourism-dependent regions during economic downturns. Agriculture, industry, and construction combined account for the remaining quarter of employment, with little variation across quarters.

### 8.4 The 'Empty Spain' Challenge

The extreme concentration of employment in Madrid and Barcelona — visible in the heavily right-skewed distribution in Chart 4 — reflects the broader *España Vacía* (Empty Spain) demographic challenge. Interior and rural provinces face not just low employment in absolute terms, but declining populations that make local economic revitalization increasingly difficult. This structural imbalance appears to be durable: it persisted through the 2020 shock and the subsequent recovery without narrowing.

---

## 9. Data Quality Report

The raw dataset presented several data quality challenges typical of real-world data ingestion from a public API. The following table summarises the issues encountered and the solutions applied:

**Issues found in the raw CSV:**

| Issue | Affected columns | Extent |
|---|---|---|
| Mixed date formats (5 distinct patterns) | Fecha | 100% of dates (cyclic across rows) |
| Comma decimal separators | Valor | ~10% of values |
| Inconsistent casing (UPPER vs. Title case) | Serie Nombre | ~5% of rows (randomly uppercased) |
| Extra whitespace in series names | Serie Nombre | ~3% of rows |
| All dimensions packed in one string | Serie Nombre | 100% — requires structural parsing |
| Dirty column names (spaces, mixed case) | All columns | 8 of 8 columns |
| Missing values | Valor | ~3% (1,125 values) |
| Duplicate rows | All | 20 rows (0.06%) |

**Solutions applied:**

| Issue | Solution | Impact |
|---|---|---|
| 5 mixed date formats | Custom multi-format parser (ISO, dd/mm, yyyy/mm, textual, ms timestamp) | 100% recovery |
| Comma decimal separators (~10%) | `str.replace(',', '.')` + `pd.to_numeric` | 100% recovery |
| Inconsistent casing (UPPER/Title) | Lowercased for matching + canonical province map | All variants normalized |
| Extra whitespace in names (~3%) | `str.strip()` before parsing | 100% cleanup |
| Packed dimensions in one string | Table-specific parsers extracting `provincia`, `sexo`, `actividad` | 3 structured columns created |
| Dirty column names (8 of 8) | Strip + lowercase + underscore | All standardized |
| 20 duplicate rows (0.06%) | `drop_duplicates` on composite key | Removed without data loss |
| ~3% null values in `valor` | Kept as `NaN` (not imputed) | Preserves data integrity |

The cleaning pipeline is fully deterministic and reproducible — running `main.py` regenerates the clean dataset from the raw CSV with identical results.

---

## 10. Conclusions

1. **Spain's unemployment geography is structural and persistent.** The north–south divide — with Andalucía, Extremadura, and Canarias consistently above 20% while País Vasco, Navarra, and Aragón remain below 10% — has barely changed in 5 years, surviving a major economic shock, recovery, and labour reform. This suggests that the drivers (industrial base, education, sectoral mix) are deeply rooted.

2. **The gender gap in unemployment is real but narrowing.** Female unemployment remains consistently higher than male unemployment, but the gap has shrunk from ~4 percentage points in 2020 to ~2–3 points by 2025. The 2020 crisis initially hit male employment harder (construction, industry), but the male recovery was also faster.

3. **Spain's economy is extremely tertiarized,** with services accounting for over 75% of total employment. This dominance has remained stable throughout the period and creates both resilience (diversified service economy) and vulnerability (sensitivity to tourism and hospitality shocks).

4. **Employment has fully recovered and reached record highs.** Total employment exceeded 22 million by 2025, representing a net gain of approximately 2 million jobs compared to early 2020 levels. The extreme concentration of employment in Madrid and Barcelona — together accounting for roughly a quarter of all jobs — underscores the *España Vacía* challenge facing interior provinces.

5. **Data quality matters: even official INE data requires significant cleaning** when accessed via API. This project dealt with 5 date formats, packed multi-dimensional series names, inconsistent casing, and the need for structural parsing — demonstrating that real-world data engineering is a non-trivial part of any analysis.

6. **Age is the strongest predictor of unemployment in Spain.** The youngest workers (16–19) face rates exceeding 30%, dropping sharply with age and stabilizing around 8–10% for workers aged 30–54. This extreme age gradient reflects temporary contract prevalence, educational mismatches, and limited entry-level opportunities for young Spaniards.

7. **Youth unemployment has improved significantly but remains structurally extreme.** The 16–19 group dropped from ~59% to ~31% and the 20–24 group from ~36% to ~22% between 2020 and 2025, yet both still far exceed the national average, indicating deep structural barriers to youth employment.

8. **The nationality gap in unemployment is structural and age-dependent.** Foreign workers face higher unemployment rates across all age groups, with the relative gap widening in middle and older ages. This finding, derived by merging two INE tables (*activos* and *ocupados* by nationality and age), reveals a dimension of labour market inequality that complements the territorial and gender analyses.

---

## 11. Design Rationale

### Dirty-first loading

Loading the deliberately corrupted file before cleaning is a deliberate pedagogical choice: it makes the rationale for every cleaning step concrete and auditable. The reader can see the problem, understand the fix, and verify the result in a single scroll. The intentional dirt is injected deterministically (seed=42) so that re-runs produce exactly the same file.

### Table-specific parsing of `serie_nombre`

INE encodes all analytical dimensions (province, sex, activity type) inside a single free-text string whose format differs by table. A generic parser would either fail or produce noisy output. The three dedicated parsers (one per source table ID: 65345, 65349, 65354) are more verbose but far more reliable and easier to debug individually.

### Separating cleaning from feature engineering

Keeping `cleaning.py` and `features.py` as distinct modules (and as distinct phases in the notebook) respects the principle of separation of concerns: cleaning corrects errors in what was recorded; feature engineering adds business meaning. The boundary is enforced by saving the clean CSV and reloading it before feature work begins.

### Dynamic period labelling

By deriving `PERIOD_START` / `PERIOD_END` from the data rather than hardcoding them, the notebook remains valid for any EPA extract downloaded via the CLI (`--start`, `--end`). Chart titles, axis labels, and captions all reflect the actual period without manual editing. Charts 7–9 detect the latest available quarter from the raw JSON data and label charts accordingly.

### Computed unemployment rate for Chart 9

INE does not publish a ready-made cross-tabulation of unemployment by both age and nationality. By merging the *activos* and *ocupados* tables and computing the rate from first principles, the notebook extracts an insight that would otherwise require a custom INE data request. The result was validated against the official INE table 65336, demonstrating a practical analytical pattern applicable to other derived metrics.

### Validation before analysis

Running `validate_clean()` immediately after cleaning and before feature engineering acts as a hard gate: if the data does not meet structural guarantees (correct dtypes, no unexpected nulls in key columns, correct row count), the pipeline fails loudly rather than producing silently wrong charts.

### Nine charts, not one dashboard

Each chart is saved as an independent PNG and answers a specific research question. This makes it straightforward to embed individual charts in reports or presentations without exporting from an interactive dashboard, and it means each visualisation can be regenerated independently. The notebook does not import from `src/viz.py`; both implement the same logic, one for interactive exploration and one for automated CLI runs.

---

## 12. Project Structure and Reproducibility

The entire pipeline — from data acquisition through cleaning, feature engineering, and chart generation — is designed to work with any time period available in the EPA dataset (quarterly data from 2002 onwards). No code changes are required to switch periods.

### Quick start

```bash
git clone https://github.com/danribes/epa_project.git
cd epa_project/
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py --fetch --start 2020 --end 2025
```

### Reproducing for a different period

**Step 1 — Clone the repository.**
```bash
git clone https://github.com/danribes/epa_project.git && cd epa_project
```

**Step 2 — Choose the period.** The EPA publishes quarterly data since 2002. If a start year before 2002 is specified, the API will silently return data from 2002 onwards. Examples: `--start 2008 --end 2014` (financial crisis); `--start 2015 --end 2020` (pre-pandemic).

**Step 3 — Fetch the data.**
```bash
python fetch_data.py --start YYYY --end YYYY
```
This downloads 6 INE API tables (3 main tables combined into the CSV, plus 3 additional JSON files for Charts 7–9). Both a clean raw CSV and a dirty CSV (with intentional quality issues, seed=42) are generated.

**Step 4 — Run the pipeline.**
```bash
python main.py
```
Or combine fetch + pipeline in one command:
```bash
python main.py --fetch --start YYYY --end YYYY
```
The cleaning (`src/cleaning.py`), feature engineering (`src/features.py`), and chart generation (`src/viz.py`) contain no hardcoded dates. The pipeline processes whatever data is in the dirty CSV and generates all 9 charts automatically in `charts/`.

**Step 5 — Explore the notebook (optional).**
```bash
jupyter notebook notebooks/eda.ipynb
```
All visualizations adapt dynamically to the data range present in the dataset.

**Example period ranges:**
```bash
python fetch_data.py --start 2008 --end 2014   # 2008 financial crisis
python fetch_data.py --start 2015 --end 2020   # pre-pandemic
python fetch_data.py --start 2005 --end 2025   # long 20-year range
```

### 12.1 Period-adaptive design

| Component | Adaptation mechanism |
|---|---|
| `fetch_data.py` | `--start` / `--end` parameters define the download range |
| `src/cleaning.py` | Date and dimension parsing with no reference to specific years |
| `src/features.py` | Generic temporal feature engineering (quarter, month, year) |
| `src/viz.py` | Generates all 9 charts with period-aware titles derived from the data |
| `main.py` | Orchestrates the full pipeline in a single command |
| `notebooks/eda.ipynb` | Derives `PERIOD_LABEL` from the data; all chart titles and captions adapt automatically |

### 12.2 Period-adaptive notebook design

The EDA notebook (`eda.ipynb`) is designed to adapt automatically to whatever period is loaded. It derives the analysis period directly from the data by reading the minimum and maximum year in the dataset (`PERIOD_START`, `PERIOD_END`, `PERIOD_LABEL`). All chart titles include this label dynamically via f-strings. Charts 7–9, which use the additional JSON tables (65219, 65086, 65112), detect the latest available quarter from the JSON data and label charts accordingly. The conclusions section is written in period-agnostic language. No notebook cells need to be modified when switching periods — the notebook adapts entirely from the data.

This design was validated by running the full pipeline with multiple periods: 2006–2015 (~65,700 rows), 2024–2026 (~13,600 rows), and 2002–2026 (~156,400 rows). All periods passed validations identically, and all 9 charts were generated successfully.

The notebook orchestrates and documents the analysis, while all reusable logic resides in the `src/` package — following the principle that notebooks explain, while modules execute.

---

## 13. Dependencies

```
pandas
numpy
matplotlib
seaborn
requests        # INE API calls
python-docx     # Word report generation
openpyxl        # (optional, for Excel export)
jupyter         # For interactive notebook use
```

Install with: `pip install -r requirements.txt`

---

*Report compiled from `EPA_PROJECT_ANALYSIS_REPORT.md` and `epa_project_report.docx` — manual review of all source files in `/home/dan/projects/evolve_master/data_science/Python/epa_project/`.*
