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

Understand the structure of the Spanish labour market by province, sex, and economic sector, its quarterly evolution, and the territorial and gender inequalities in employment and unemployment. The analysis period is **user-configurable** (default 2002–2025, i.e. the full available EPA range — 96 quarters). The project is designed to work with **any period** of EPA data (quarterly from 2002 onwards).

The 2002–2025 period captures the full arc of the modern Spanish labour market: the construction-fuelled expansion (2002–2007), the devastating Great Recession and housing bubble collapse (2008–2013), the slow structural recovery (2014–2019), the COVID-19 pandemic shock (2020), and the subsequent record-breaking employment rebound (2021–2025).

---

## Table of Contents

1. [Objective](#objective)
2. [Quick Start](#quick-start)
3. [Dataset](#dataset)
4. [Research Questions](#research-questions)
5. [Methodology](#methodology)
6. [Results](#results)
7. [Key Findings Summary](#key-findings-summary)
8. [Additional Findings](#additional-findings)
9. [Data Quality Report](#data-quality-report)
10. [Conclusions](#conclusions)
11. [Design Rationale](#design-rationale)
12. [Project Structure](#project-structure)
13. [How to Run](#how-to-run)
14. [Reproducing with a Different Period](#reproducing-with-a-different-period)
15. [Dependencies](#dependencies)

---

## Quick Start

```bash
git clone https://github.com/danribes/epa_project.git
cd epa_project/
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py --fetch --start 2002 --end 2025
```

> This downloads the 6 EPA tables from the INE public API, runs cleaning, generates features, and produces the 9 charts in `charts/`.

---

## Dataset

| | Details |
|---|---|
| **Source** | INE public API — [servicios.ine.es/wstempus/js](https://servicios.ine.es/wstempus/js) |
| **Tables** | 65345 (population), 65349 (rates), 65354 (sectors), 65219 (unemployment by age), 65086 (active by nationality), 65112 (employed by nationality) |
| **Size (2002–2025)** | ~156,500 rows x 8 cols (raw) → 156,456 x 17 (after cleaning + features) |
| **Time span** | Q4 2001 – Q3 2025 (96 quarters) |
| **Geographic coverage** | 52 provinces + national total (20 Autonomous Communities) |
| **Key variables** | province, sex, activity type, date (quarterly), value (thousands of people or %) |
| **Additional data** | Raw JSON API responses in `data/raw/` |

| Table ID | Content | Use |
|---|---|---|
| 65345 | Population 16+ by activity, sex, and province — absolute figures (thousands of persons) | Main CSV → Charts 1–6 |
| 65349 | Activity / unemployment / employment rates by province and sex | Main CSV → Charts 1–6 |
| 65354 | Employed persons by economic sector (CNAE) and province | Main CSV → Charts 1–6 |
| 65219 | Unemployment rates by sex and age group | JSON → Charts 7–8 |
| 65086 | Active population by nationality, sex, and age group | JSON → Chart 9 (merge) |
| 65112 | Employed population by nationality, sex, and age group | JSON → Chart 9 (merge) |

Tables 65345, 65349, and 65354 are merged into a single combined CSV that feeds the main cleaning pipeline. Tables 65219, 65086, and 65112 are preserved as raw JSON files and parsed directly inside the notebook for charts 7–9.

> **Methodological note (chart 9):** The INE API does not publish a table with unemployment rates broken down simultaneously by nationality and age group. To obtain them, tables 65086 (active) and 65112 (employed) were downloaded with the same dimensions (nationality x sex x age) and the rate was calculated as: `unemployment_rate = (active - employed) / active * 100`. The result was validated against the official table 65336 with an exact match.

### Raw JSON field glossary

The raw JSON files in `data/raw/` use INE's internal field names and coded values. This table documents every field:

| Field | Meaning | Values / Example |
|---|---|---|
| `COD` | Internal series code | `"EPA397872"` |
| `Nombre` | Series name (all dimensions packed in one string) | `"Total Nacional. Ocupados. Ambos sexos. Total CNAE. Personas. "` |
| `FK_Unidad` | Unit of measurement — **3** = Personas, **101** = Porcentaje | `3` |
| `FK_Escala` | Scale/multiplier — **4** = Miles (×1,000) | `4` → a `Valor` of 22463.3 means 22,463,300 persons |
| `Fecha` | **Unix timestamp in milliseconds** | `1759269600000` → 2025-10-01 |
| `FK_TipoDato` | Data type — **1** = definitive data | Always `1` in EPA |
| `FK_Periodo` | Quarter ID (non-sequential): **19**=Q4, **20**=Q1, **21**=Q2, **22**=Q3 | `22` → Q3 |
| `Anyo` | Year (Spanish *año* in ASCII) | `2025` |
| `Valor` | Observed value (unit and scale depend on `FK_Unidad` / `FK_Escala`) | `22463.3` |
| `Secreto` | Statistical secrecy flag — `true` = value suppressed for respondent privacy | `false` (all values publishable in 2002–2025) |

> **Note:** `FK_Periodo` uses an internal INE numbering (19–22) shared across periodicities (monthly, quarterly, annual), which is why quarter IDs do not start at 1. The pipeline maps them to T1–T4 via `PERIODO_MAP` in `src/features.py`. `FK_Unidad` and `FK_Escala` are not extracted into the CSV — the unit context is implicit in the analysis. Full catalogues available at `servicios.ine.es/wstempus/js/ES/UNIDADES` and `.../ESCALAS`.

### How raw JSON fields map to the processed dataset

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

## Research Questions

| # | Question | Chart |
|---|---|---|
| Q1 | Which provinces have the highest and lowest unemployment rates? Has the ranking changed over 24 years? | 1, 6 |
| Q2 | Is there a gender gap in activity, employment, and unemployment rates? | 2 |
| Q3 | How is employment distributed by economic sector and how does it vary geographically? | 3 |
| Q4 | How has total employment evolved over the period? | 4, 5 |
| Q5 | Is there seasonality in employment/unemployment (quarterly)? | 6 |
| Q6 | How does the unemployment rate vary by age group? Are there differences by sex? | 7 |
| Q7 | How has youth unemployment (16–19 and 20–24) evolved compared to the total? | 8 |
| Q8 | Is there an unemployment gap between Spanish and foreign workers? | 9 |

---

## Methodology

### Data Acquisition

Data was retrieved programmatically via HTTP GET requests to the INE REST API using the Python `requests` library. The `fetch_data.py` script accepts `--start` and `--end` parameters to define the year range. The EPA publishes quarterly data since 2002; if a start year earlier than 2002 is specified, the API silently returns data from 2002 onwards. The script includes automatic retries (3 attempts with exponential backoff) and a 1-second courtesy delay between requests.

### Data Quality Assessment

An initial quality check on the raw CSV revealed: `valor` stored as text (not numeric), `fecha` stored as text, ~3% null values, duplicate rows, mixed casing in series names, and 5 different date formats in the same column. Seven data quality problems are documented in the notebook before cleaning begins.

### Cleaning Pipeline

The cleaning pipeline (`src/cleaning.py`) applies eight sequential transformations:

| Step | Transformation |
|---|---|
| 1 | Column standardization — strip, lowercase, underscores |
| 2 | Numeric parsing — comma→dot + `pd.to_numeric` |
| 3 | Series name normalization — strip whitespace, lowercase helper |
| 4 | Structural parsing — extract `provincia`, `sexo`, `actividad` from packed string |
| 5 | Date parsing — custom multi-format parser (ISO, European, textual, ms timestamp) |
| 6 | Categorical normalization — canonical `sexo` and `provincia` values |
| 7 | Deduplication — `drop_duplicates` on composite key |
| 8 | Cleanup — drop helper columns |

### Feature Engineering

Seven derived columns are added (`src/features.py`): `trimestre`, `mes`, `year`, `trimestre_label`, `fuente`, `es_nacional`, `ccaa`. The period label is derived dynamically from the data so the notebook is fully period-agnostic.

### Pipeline

```
fetch_data.py → raw CSV → cleaning.py → utils.py → features.py → data/processed/ → viz.py → charts/
```

### Visualization Design

Nine visualization types answer the eight research questions:

- **Chart 1** — Horizontal bar: unemployment rate by province, colour-coded by median.
- **Chart 2** — Two-line chart: gender gap in unemployment over time.
- **Chart 3** — Four-line chart: employment by economic sector over time.
- **Chart 4** — Horizontal bar: average employed population per province.
- **Chart 5** — Area fill line chart: total employment evolution.
- **Chart 6** — Heatmap: unemployment rate by CCAA and quarter.
- **Chart 7** — Grouped bar: unemployment rate by age group and sex.
- **Chart 8** — Multi-line: youth unemployment (16–19, 20–24) vs. total rate.
- **Chart 9** — Grouped bar: unemployment rate by age group and nationality.

---

## Results

The 2002–2025 analysis window covers 96 quarters and three complete macroeconomic cycles: the pre-crisis expansion (2002–2007), the Great Recession (2008–2013), and the recovery-pandemic-rebound period (2014–2025).

### Unemployment by Province (Q1)

*Chart 1 — `01_tasa_paro_por_provincia.png`*

The territorial disparity in unemployment is the most persistent structural feature of the Spanish labour market. Across the full 24-year period, the north–south divide is striking and remarkably stable. Southern provinces — particularly those in Andalucía (Cádiz, Huelva, Sevilla, Córdoba, Jaén, Granada), Extremadura (Badajoz, Cáceres), and the Canary Islands — consistently exhibit unemployment rates well above the national average. In contrast, northern provinces — País Vasco (Gipuzkoa, Araba/Álava, Bizkaia), Navarra, Aragón (Huesca, Teruel), and La Rioja — show significantly lower rates.

The scale of this divide fluctuated with the business cycle but the ranking barely changed: in 2007 (the pre-crisis low, national rate 8.5%), southern provinces still led the unemployment table; in 2013 (the crisis peak, national rate 25.8%), the same provinces held the top positions but with rates exceeding 35%; and by 2025 (national rate ~10%), the ranking remained essentially the same. This extraordinary persistence over a period that included a housing bubble, a financial crisis, a labour reform, a pandemic, and a historic recovery confirms that the drivers are deeply structural.

### Gender Gap in Unemployment (Q2)

*Chart 2 — `02_brecha_genero_paro.png`*

The gender gap is a persistent feature of the Spanish labour market, but its magnitude and direction have evolved significantly over the 24-year period.

During the pre-crisis period (2002–2007), female unemployment was consistently 4–6 percentage points higher than male unemployment. The 2008 financial crisis initially narrowed the gap dramatically because male-dominated sectors (construction, industry) were hit hardest — male unemployment surged from ~7% to ~25%, while female unemployment rose from ~12% to ~27%. For the first time, the gap shrank to near zero and briefly inverted.

During the recovery phase (2014–2019), the gender gap re-established itself at around 3–4 percentage points. The 2020 pandemic briefly narrowed the gap again. By 2024–2025, both rates reached their lowest levels in the observed period (~9% male, ~12% female), with the gender gap narrowing to approximately 2–3 percentage points — the smallest sustained gap in the entire 24-year series.

### Employment by Economic Sector (Q3)

*Chart 3 — `03_empleo_por_sector.png`*

The most dramatic story in the sectoral data is the rise and catastrophic fall of the construction sector, set against the relentless growth of services.

| Sector | 2007 (peak) | 2013 (trough) | 2025 (latest) | Change 2007→2013 | Change 2013→2025 |
|---|---|---|---|---|---|
| **Services** | 13,718k | 13,025k | 17,026k | −5.1% | +30.7% |
| **Industry** | 3,353k | 2,336k | 3,036k | −30.3% | +30.0% |
| **Construction** | 2,680k | 999k | 1,547k | **−62.7%** | +54.9% |
| **Agriculture** | 870k | 760k | 764k | −12.6% | +0.5% |

Construction collapsed from 2.7 million workers (2007) to just 1.0 million (2013) — a loss of 1.7 million jobs. By 2025, it has recovered to 1.5 million but remains 43% below its 2007 peak. Services now account for over 76% of total employment, up from ~66% in 2007.

### Employment Evolution and Recovery (Q4)

*Chart 5 — `05_evolucion_empleo_total.png`*

The employment trajectory reveals the full economic cycle:

| Period | Employment | Key event |
|---|---|---|
| 2002 | 16,943k | Starting point |
| 2007 | 20,668k | Pre-crisis peak (+3.7M jobs in 5 years) |
| 2013 | 17,119k | Crisis trough (−3.6M jobs destroyed) |
| 2019 | 19,832k | Pre-pandemic (still below 2007 peak) |
| 2020 | 19,092k | COVID shock |
| 2025 | 22,373k | **All-time record** (+5.4M vs 2002; +1.7M vs 2007) |

The unemployment rate swung from 7.93% (Q1 2007, all-time low) to 26.06% (Q1 2013, peak) to 9.93% (Q3 2025 — breaking below 10% for the first time since the pre-2008 era).

### Employment Distribution and Territorial Concentration (Q4/Q5)

*Chart 4 — `04_distribucion_ocupados.png`*

The distribution is extremely right-skewed: Madrid and Barcelona together account for roughly a quarter of total national employment. The *España Vacía* (Empty Spain) phenomenon is clearly visible — many interior provinces (Soria, Teruel, Ávila, Segovia) have employment bases under 50,000. This territorial concentration has not changed over the 24-year period.

### Territorial Unemployment Patterns — Heatmap (Q1/Q5)

*Chart 6 — `06_heatmap_paro_ccaa.png`*

The heatmap across 96 quarters reveals three structural patterns:

- **Persistent territorial ranking:** Andalucía, Canarias, Extremadura at the top; País Vasco, Navarra, Aragón at the bottom. Barely changes across 24 years and three economic cycles.
- **Dramatic cyclical amplitude:** The 2008–2013 crisis appears as a striking dark band across all communities. The 2020 COVID shock is visible but much less pronounced.
- **Unequal cyclical impact:** Construction-dependent communities experienced the sharpest crisis increases.

### Unemployment by Age Group (Q6)

*Chart 7 — `07_paro_por_edad.png`*

The age gradient is dramatic and consistent across the full 24-year observation window:

| Age group | Period average | 2013 (crisis peak) | 2025 (latest) |
|---|---|---|---|
| 16–19 | ~42% | **74.1%** | 37.0% |
| 20–24 | ~28% | 51.8% | 22.5% |
| 25–29 | ~18% | 33.3% | 13.7% |
| 30–54 | ~12% | ~22% | ~9% |
| 55–64 | ~11% | ~20% | ~10% |
| **Total (16+)** | ~14% | 26.1% | 10.5% |

Youth unemployment (16–19) peaked at 74% in 2013 — three out of four active young people in this age group could not find work. A gender gap exists in every age group, inverted only for 16–19 (male rate slightly higher).

### Youth Unemployment Evolution (Q7)

*Chart 8 — `08_paro_juvenil_evolucion.png`*

The 24-year arc is dramatic:

- **Pre-crisis (2002–2007):** 16–19 group ~29–30%; 20–24 group ~15–20%; overall ~8–12%
- **Great Recession (2008–2013):** 16–19 surged to ~74%; 20–24 to ~52%; overall to ~26%
- **Recovery (2014–2019):** 16–19: ~74% → ~45%; 20–24: ~52% → ~30%; overall: ~26% → ~14%
- **Pandemic and rebound (2020–2025):** After a brief COVID spike, continued downward trend to 16–19 ~37%; 20–24 ~22%; overall ~10%

Despite this improvement, youth unemployment remains structurally elevated: the 16–19 group (~37%) is roughly 3.5× the national average (~10%), and the 20–24 group (~22%) more than doubles it.

### Unemployment by Age and Nationality (Q8)

*Chart 9 — `09_paro_edad_nacionalidad.png`*

Foreign workers face higher unemployment in every age bracket. The gap is smallest among youth (16–24: ~23% vs ~26%) and largest in the 45–54 group (~7% vs ~12%) and 55+ group (~8% vs ~16%, nearly double). The 2008 crisis disproportionately impacted immigrant workers concentrated in the collapsed construction sector. The gap has gradually narrowed since but remains structurally present in 2025.

---

## Key Findings Summary

| # | Finding | Chart |
|---|---|---|
| 1 | **Structural territorial inequality** — Strong North–South divide persists across 24 years and three economic cycles. Andalucía, Extremadura, and Canarias consistently lead; País Vasco and Navarra are consistently lowest. The ranking barely changes. | 1, 6 |
| 2 | **Persistent but narrowing gender gap** — Female unemployment consistently higher. The gap narrowed during the 2008 crisis (male sectors hit harder), re-established during recovery, and reached its smallest sustained level (~2–3 pp) by 2025. | 2 |
| 3 | **Construction boom and bust** — Construction employment collapsed by 62.7% (2007–2013), the most dramatic sectoral story. Only partially recovered to 1.5M by 2025 (43% below peak). Services rose from ~66% to >76% of total employment. | 3 |
| 4 | **Full economic cycle** — Employment: 16.9M (2002) → 20.7M (2007) → 17.1M (2013) → 22.4M (2025 record). Spain lost 3.6M jobs in the Great Recession, surpassed the 2007 peak in 2023, and reached unprecedented levels by 2025. | 4, 5 |
| 5 | **Employment concentration** — Madrid and Barcelona account for ~25% of national employment. The *España Vacía* challenge persists across all 96 quarters. | 4 |
| 6 | **Extreme youth unemployment** — 16–19 group averaged ~42% over 24 years, peaking at 74% in 2013. Even at 2025 levels (~37%), it is 3.5× the national average. The age gradient is the strongest predictor of unemployment in Spain. | 7 |
| 7 | **Dramatic youth improvement from crisis peaks** — 16–19: 74% → 37%; 20–24: 52% → 22% (2013→2025). Still 2–3.5× the overall rate. | 8 |
| 8 | **Nationality gap across all age groups** — Foreign workers have higher unemployment rates. The gap widened during the 2008 crisis and has gradually narrowed since, but remains structural in 2025. | 9 |

---

## Additional Findings

### The Construction Bubble and Its Labour Market Legacy

The construction sector grew from ~1.8 million workers (2002) to a peak of 2.7 million (2007), then collapsed by 62.7% to just 1.0 million (2013). By 2025, construction employs approximately 1.5 million — still 43% below its 2007 peak. Its share of total employment shrank from ~13% (2007) to ~7% (2025). The permanent downsizing has had lasting effects on provinces most dependent on the sector and on demographics most affected (young men, immigrant workers).

### The 2008–2013 Great Recession: Scale and Duration

Unemployment tripled from 7.93% (Q1 2007) to 26.06% (Q1 2013). The crisis destroyed 3.6 million jobs over five years, with unemployment exceeding 20% for 16 consecutive quarters (Q1 2010 through Q4 2013). The sheer duration distinguishes Spain's experience from other European countries, reflecting the combined impact of the global financial crisis and Spain's domestic housing bubble burst.

### Labour Market Flexibility (2020)

The response to the 2020 COVID-19 shock was markedly different from 2008. ERTEs preserved employment contracts for millions of workers. The 2020 unemployment spike was comparatively mild (~16% vs ~26% in 2013) despite a GDP contraction of −10.8%. The recovery was dramatically faster: pre-pandemic levels regained by late 2021, compared to the decade-long recovery from 2008.

### The 2021 Labour Reform Impact

The 2021 *Reforma Laboral* aimed to reduce temporary employment. Data from 2022 onward shows sustained growth and continued unemployment reduction. Employment reached record highs (22.4 million) while unemployment fell below 10% for the first time since 2007 — suggesting a favourable structural shift, though aggregate EPA data does not distinguish contract types.

### Services Sector Dominance

Services have grown from ~66% of total employment (2007) to over 76% (2025), absorbing the workforce displaced from construction while adding new employment. This reflects a modern economy but creates vulnerability to sector-specific shocks, as the 2020 pandemic demonstrated — though the 2020 shock proved far more temporary than the 2008 construction collapse.

### The 'Empty Spain' Challenge

The extreme concentration of employment in Madrid and Barcelona reflects the broader *España Vacía* demographic challenge. Interior and rural provinces face declining populations that make local economic revitalization increasingly difficult. This structural imbalance has been a constant feature across all 96 quarters.

### Immigration and the Labour Market

The 2002–2025 period coincides with Spain's transformation into a country of net immigration. The foreign-born population grew rapidly between 2002 and 2008, with immigrants concentrating in construction, agriculture, and hospitality. The 2008 crisis disproportionately impacted these workers (foreign unemployment rates exceeded 35% in 2013). The 2014–2025 recovery has seen renewed immigration and some narrowing of the nationality gap, but foreign workers remain more vulnerable to cyclical downturns.

---

## Data Quality Report

**Issues found and solutions applied:**

| Issue | Fix | Impact |
|---|---|---|
| 5 mixed date formats (ISO, dd/mm, yyyy/mm, textual, ms) | Custom multi-format parser with fallbacks | 100% recovery |
| Comma decimal separators (~10%) | `.str.replace(",", ".")` + `pd.to_numeric` | 100% recovery |
| Inconsistent casing (UPPER/Title) | Lowercased for matching + canonical province map | All variants normalized |
| Extra whitespace in names (~3%) | `str.strip()` before parsing | 100% cleanup |
| All dimensions packed in one string (100%) | Table-specific regex parsers extracting province, sex, activity | 3 structured columns created |
| Dirty column names (8 of 8) | Strip + lowercase + underscore | All standardized |
| Duplicate rows | `drop_duplicates` on composite key | Removed without data loss |
| ~3% null values in value | Kept as NaN (not imputed) | Preserves data integrity |

The cleaning pipeline is fully deterministic and reproducible.

---

## Conclusions

1. **Spain's unemployment geography is structural and persistent.** The north–south divide has barely changed in 24 years, surviving a housing bubble, financial crisis, pandemic, and record recovery. This is the strongest finding in the entire analysis.

2. **The full economic cycle reveals extraordinary volatility.** Unemployment swung from 7.93% (Q1 2007) to 26.06% (Q1 2013) to 9.93% (Q3 2025) — a range of 18 percentage points. Total employment oscillated from 20.7M to 17.1M to a record 22.4M.

3. **The construction boom and bust is the most dramatic sectoral story.** Construction employment collapsed by 62.7% (2007–2013) and has only partially recovered. The permanent downsizing reshaped Spain's employment landscape.

4. **The gender gap is real but narrowing.** By 2025, the gap stands at ~2–3 pp — the smallest sustained level in 24 years.

5. **Spain is extremely and increasingly tertiarized,** with services growing from ~66% to >76% of employment.

6. **Employment reached all-time highs.** Total employment exceeded 22M by 2025, surpassing the 2007 peak by ~1.7M. Unemployment broke below 10% in Q3 2025 for the first time since the pre-2008 era.

7. **Age is the strongest predictor of unemployment.** Youth (16–19) averaged ~42% unemployment over 24 years, peaking at 74% in 2013.

8. **Youth unemployment improved dramatically from crisis peaks but remains structurally extreme** — still 2–3.5× the national average in 2025.

9. **The nationality gap is structural and age-dependent.** Foreign workers face higher unemployment across all age groups.

10. **Data quality matters** — even official INE data requires significant cleaning when accessed via API. This project dealt with 5 date formats, packed series names, inconsistent casing, and structural parsing.

---

## Design Rationale

- **Dirty-first loading** — Loading the deliberately corrupted file before cleaning makes the rationale for every step concrete and auditable. Intentional dirt is injected deterministically (seed=42).
- **Table-specific parsing** — Three dedicated parsers (one per source table) are more verbose but far more reliable than a generic approach.
- **Separating cleaning from feature engineering** — `cleaning.py` corrects errors; `features.py` adds business meaning. The boundary is enforced by saving the clean CSV between phases.
- **Dynamic period labelling** — `PERIOD_START` / `PERIOD_END` are derived from the data, not hardcoded. Charts adapt to any period without manual editing.
- **Computed unemployment rate** (Chart 9) — Merging *activos* and *ocupados* tables by nationality/age extracts an insight unavailable in any single INE table. Validated against official table 65336.
- **Centralized configuration** — All path constants live in `src/config.py`, making the project easy to relocate or restructure.
- **Validation before analysis** — `validate_clean()` acts as a hard gate before feature engineering.
- **Test suite** — 12 pytest tests covering all `src/` modules (config, io, cleaning, features, utils) ensure pipeline correctness.
- **Nine charts, not one dashboard** — Each chart is an independent PNG answering a specific research question. Both the notebook and `src/viz.py` implement the same logic independently.

---

## Project Structure

```
epa_project/
├── fetch_data.py                     # Data download from INE
├── main.py                           # End-to-end pipeline
├── conftest.py                       # Pytest root configuration
├── pyrightconfig.json                # IDE import resolution config
├── data/
│   ├── raw/                          # Raw JSON + raw/dirty CSV
│   └── processed/                    # Clean CSV (156,456 rows × 17 cols)
├── charts/                           # 9 generated PNG charts
├── notebooks/
│   └── eda.ipynb                     # Interactive analysis notebook
├── src/
│   ├── __init__.py
│   ├── config.py                     # Centralized path constants
│   ├── io.py                         # Data loading and saving
│   ├── cleaning.py                   # Data cleaning
│   ├── features.py                   # Feature engineering
│   ├── viz.py                        # Reusable charts
│   └── utils.py                      # Validations and utilities
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py              # 12 pytest tests (config, io, cleaning, features, utils)
├── epa_project_report.docx           # Full analysis report (Word, with charts)
├── README.md
└── requirements.txt
```

---

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
python fetch_data.py --start 2002 --end 2025
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
  Shape raw: (~156500, 8)
Cleaning data ...
  Shape clean: (156456, 10)
All validations passed.
Generating features ...
  Shape final: (156456, 17)
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
python main.py --fetch --start 2002 --end 2025
```

### Step 6 — Run the tests

```bash
pip install pytest
python -m pytest tests/ -v
```

All 12 tests cover `src/config`, `src/io`, `src/cleaning`, `src/features`, and `src/utils`.

### Step 7 — Explore the notebook (optional)

```bash
pip install jupyter
jupyter notebook notebooks/eda.ipynb
```

---

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

### Usage examples

```bash
# Full available range (24 years)
python fetch_data.py --start 2002 --end 2025

# 2008 financial crisis
python fetch_data.py --start 2008 --end 2014

# Pre-pandemic
python fetch_data.py --start 2015 --end 2020

# Default 6-year range
python fetch_data.py --start 2020 --end 2025

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
| `src/config.py` | Centralized path constants — single place to change all data paths |
| `src/cleaning.py` | Date and dimension parsing with no reference to specific years |
| `src/features.py` | Generic temporal feature engineering (quarter, month, year) |
| `src/viz.py` | Generates all 9 charts with titles that include the temporal range detected in the data |
| `main.py` | Orchestrates the full pipeline (fetch + clean + features + charts) in a single command |
| `tests/test_pipeline.py` | Data-driven tests that validate against the actual dataset |
| `notebooks/eda.ipynb` | Derives `PERIOD_LABEL` from the data and uses it in all chart titles |

### Important notes

- The INE API is public and free; no API key is required.
- The script includes automatic retries (3 attempts with exponential backoff) and a 1s courtesy delay between requests.
- **EPA data is available quarterly from 2002.** If `--start` is set to a year before 2002, the INE API will return data from 2002 onwards without raising an error.
- The full pipeline (`main.py`) runs cleaning, features, and generation of all 9 charts in `charts/`. All components are period-agnostic: they contain no hardcoded dates.
- The intentional dirt in the dirty CSV is deterministic (seed=42), so running twice with the same period produces exactly the same file.

---

## Dependencies

```
pandas
numpy
matplotlib
seaborn
requests        # INE API calls
python-docx     # Word report generation
openpyxl        # (optional, for Excel export)
jupyter         # For interactive notebook use
pytest          # Test suite
```

Install with: `pip install -r requirements.txt`

---

*Full analysis report with embedded charts available in [`epa_project_report.docx`](epa_project_report.docx). Report compiled from the full 2002–2025 EPA dataset (156,456 observations across 96 quarters). Source: Instituto Nacional de Estadística (INE) — Encuesta de Población Activa.*
