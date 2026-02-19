<p align="center">
  <h1 align="center">Análisis del Mercado Laboral Español (EPA)</h1>
  <p align="center">
    Análisis exploratorio de datos (EDA) del mercado laboral español<br>
    usando datos abiertos del <strong>Instituto Nacional de Estadística</strong> (INE)
  </p>
  <p align="center">
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python"></a>
    <a href="https://pandas.pydata.org/"><img src="https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white" alt="Pandas"></a>
    <a href="https://matplotlib.org/"><img src="https://img.shields.io/badge/Matplotlib-3.x-11557C" alt="Matplotlib"></a>
    <a href="https://seaborn.pydata.org/"><img src="https://img.shields.io/badge/Seaborn-0.13-4C72B0" alt="Seaborn"></a>
    <a href="https://servicios.ine.es/wstempus/js"><img src="https://img.shields.io/badge/Datos-INE%20API-E4002B" alt="INE API"></a>
  </p>
</p>

---

## Objetivo

Entender la estructura del mercado laboral español por provincia, sexo y sector económico, su evolución trimestral, y las desigualdades territoriales y de género en empleo y desempleo. El periodo de análisis es **configurable por el usuario** (por defecto 2020–2025). El proyecto está diseñado para funcionar con **cualquier periodo** de datos EPA (trimestrales desde 2002).

## Inicio rápido

```bash
git clone https://github.com/danribes/epa_project.git
cd epa_project/
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py --fetch --start 2020 --end 2025
```

> Esto descarga las 6 tablas de la EPA desde la API pública del INE, ejecuta la limpieza, genera features y produce los 9 gráficos en `charts/`.

## Dataset

| | Detalle |
|---|---|
| **Fuente** | API pública del INE — [servicios.ine.es/wstempus/js](https://servicios.ine.es/wstempus/js) |
| **Tablas** | 65345 (población), 65349 (tasas), 65354 (sectores), 65219 (paro por edad), 65086 (activos por nacionalidad), 65112 (ocupados por nacionalidad) |
| **Tamaño** | ~40.700 filas x 8 cols (raw, 6 años) ➜ ~40.700 x 17 (tras limpieza + features) |
| **Variables clave** | provincia, sexo, tipo de actividad, fecha (trimestral), valor (miles de personas o %) |
| **Datos adicionales** | Respuestas JSON crudas de la API en `data/raw/` |

> **Nota metodológica (gráfico 9):** La API del INE no publica una tabla con tasas de paro desglosadas simultáneamente por nacionalidad y grupo de edad. Para obtenerlas, se descargaron las tablas 65086 (activos) y 65112 (ocupados) con las mismas dimensiones (nacionalidad x sexo x edad) y se calculó: `tasa_paro = (activos - ocupados) / activos * 100`. El resultado fue validado contra la tabla oficial 65336 con coincidencia exacta.

## Preguntas de investigación

| # | Pregunta | Gráfico |
|---|---|---|
| Q1 | ¿Cuáles son las provincias con mayor y menor tasa de paro? ¿Ha cambiado el ranking? | 1, 6 |
| Q2 | ¿Existe brecha de género en las tasas de actividad, empleo y paro? | 2 |
| Q3 | ¿Cómo se distribuye el empleo por sector económico y cómo varía geográficamente? | 3 |
| Q4 | ¿Cómo ha evolucionado el empleo total a lo largo del periodo? | 4, 5 |
| Q5 | ¿Existe estacionalidad en el empleo/paro (trimestral)? | 6 |
| Q6 | ¿Cómo varía la tasa de paro según el grupo de edad? ¿Diferencias por sexo? | 7 |
| Q7 | ¿Cómo ha evolucionado el paro juvenil (16–19 y 20–24 años) frente al total? | 8 |
| Q8 | ¿Existe brecha de desempleo entre trabajadores españoles y extranjeros? | 9 |

## Data issues & fixes

| Problema | Solución |
|---|---|
| Nombres de columna sucios (espacios, mayúsculas) | `strip().lower().replace(' ', '_')` |
| Valor como texto con coma decimal (`203,2`) | `.str.replace(",", ".")` + `pd.to_numeric` |
| Fechas en 5 formatos distintos (ISO, dd/mm, ms, textual) | Parser custom con fallbacks |
| Serie_nombre en mayúsculas/minúsculas inconsistente | Parsing sobre versión `.lower()` con mapping canónico |
| Todas las dimensiones empaquetadas en un solo string | Parsing regex por tabla para extraer provincia, sexo, actividad |
| ~3% de nulls en valor | Mantenidos como NaN (no imputados) |
| 20 filas duplicadas | `drop_duplicates()` por clave compuesta |

## Pipeline

```
fetch_data.py ➜ raw CSV ➜ cleaning.py ➜ utils.py ➜ features.py ➜ data/processed/ ➜ viz.py ➜ charts/
```

El pipeline completo — incluyendo la generación de los 9 gráficos — se ejecuta con un solo comando:

```bash
python main.py --fetch --start 2020 --end 2025
```

## Hallazgos

> **Nota:** Los hallazgos a continuación corresponden al periodo por defecto (2020–2025). Al ejecutar el proyecto con un periodo diferente, los resultados variarán.

| # | Hallazgo | Gráfico |
|---|---|---|
| 1 | **Fuerte desigualdad territorial** — Las provincias del sur (Andalucía, Extremadura, Canarias) mantienen tasas de paro significativamente más altas que las del norte (País Vasco, Navarra, Aragón). | 1, 6 |
| 2 | **Brecha de género persistente pero reduciéndose** — La tasa de paro femenina es consistentemente más alta que la masculina, aunque la diferencia se ha ido estrechando. | 2 |
| 3 | **Economía terciarizada** — El sector servicios domina abrumadoramente el empleo (>75%), con agricultura, industria y construcción estables. | 3 |
| 4 | **Evolución positiva del empleo total** — El empleo total ha mostrado una trayectoria al alza a lo largo del periodo analizado. | 5 |
| 5 | **Concentración del empleo** — Madrid y Barcelona concentran una proporción desproporcionada del empleo. | 4 |
| 6 | **Paro juvenil extremo** — Los menores de 25 años sufren tasas de paro muy superiores a la media nacional (16–19: >30%, 20–24: ~22%, general: ~10%). | 7 |
| 7 | **Tendencia descendente del paro juvenil** — El paro juvenil ha descendido significativamente, aunque sigue triplicando (16–19) y duplicando (20–24) la tasa general. | 8 |
| 8 | **Brecha por nacionalidad en todas las edades** — Los trabajadores extranjeros presentan tasas de paro superiores a los españoles en todos los grupos de edad. | 9 |

## Estructura del proyecto

```
epa_project/
├── fetch_data.py                     # Descarga de datos del INE
├── main.py                           # Pipeline end-to-end
├── data/
│   ├── raw/                          # JSON crudos + CSV raw/dirty
│   └── processed/                    # CSV limpio (filas x 17)
├── charts/                           # 9 gráficos PNG generados
├── notebooks/
│   └── eda.ipynb                     # Notebook interactivo de análisis
├── src/
│   ├── __init__.py
│   ├── io.py                         # Carga y guardado de datos
│   ├── cleaning.py                   # Limpieza de datos
│   ├── features.py                   # Feature engineering
│   ├── viz.py                        # Gráficos reutilizables
│   └── utils.py                      # Validaciones y utilidades
├── epa_project_report.docx           # Informe completo del proyecto
├── README.md
└── requirements.txt
```

## Cómo ejecutar

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/danribes/epa_project.git
cd epa_project/
```

### Paso 2 — Crear un entorno virtual (recomendado)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 3 — Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4 — Descargar datos del INE

```bash
python fetch_data.py --start 2020 --end 2025
```

Este paso descarga las 6 tablas de la EPA desde la API pública del INE, genera los ficheros JSON crudos y los CSV raw y dirty en `data/raw/`. Los parámetros `--start` y `--end` definen el rango de años a descargar.

### Paso 5 — Ejecutar el pipeline de limpieza + gráficos

```bash
python main.py
```

<details>
<summary>Salida esperada</summary>

```
Cargando datos desde .../data/raw/epa_mercado_laboral_dirty.csv ...
  Shape raw: (40724, 8)
Limpiando datos ...
  Shape clean: (40704, 10)
All validations passed.
Generando features ...
  Shape final: (40704, 17)
Guardado en .../data/processed/epa_mercado_laboral_clean.csv

Generando graficos ...
  -> 01_tasa_paro_por_provincia.png
  -> 02_brecha_genero_paro.png
  -> 03_empleo_por_sector.png
  -> 04_distribucion_ocupados.png
  -> 05_evolucion_empleo_total.png
  -> 06_heatmap_paro_ccaa.png
  -> 07_paro_por_edad.png
  -> 08_paro_juvenil_evolucion.png
  -> 09_paro_edad_nacionalidad.png
Graficos guardados en charts/
```
</details>

Alternativamente, se pueden combinar descarga + limpieza + gráficos en un solo comando:

```bash
python main.py --fetch --start 2020 --end 2025
```

### Paso 6 — Explorar el notebook (opcional)

```bash
pip install jupyter
jupyter notebook notebooks/eda.ipynb
```

## Reproducir con un periodo diferente

El proyecto está diseñado para funcionar con **cualquier periodo** de datos EPA. Para cambiar el rango temporal:

> **Importante:** La EPA publica datos trimestrales **desde 2002**. Si se especifica un año de inicio anterior a 2002, la API del INE simplemente devolverá los datos desde 2002 en adelante, sin generar error.

### Paso a paso

1. **Elegir el periodo.** La EPA publica datos trimestrales desde 2002. Ejemplo: 2015–2020.

2. **Descargar los datos.** El script `fetch_data.py` se conecta a la API del INE usando el parámetro `date=YYYYMMDD:YYYYMMDD` para solicitar el rango exacto.

   ```bash
   python fetch_data.py --start 2015 --end 2020
   ```

   Esto descarga las 6 tablas y genera:
   - `data/raw/*.json` — respuestas JSON crudas de la API (una por tabla)
   - `data/raw/epa_mercado_laboral_raw.csv` — CSV combinado limpio
   - `data/raw/epa_mercado_laboral_dirty.csv` — CSV con suciedad intencional

3. **Ejecutar el pipeline.** El código de limpieza, features y gráficos es completamente agnóstico al periodo — no tiene fechas hardcodeadas. Los 9 gráficos se generan automáticamente en `charts/`.

   ```bash
   python main.py
   ```

4. **Explorar el notebook (opcional).** El notebook `eda.ipynb` lee del CSV dirty y se adapta automáticamente al periodo descargado:
   - Los **títulos de todos los gráficos** incluyen el rango temporal detectado en los datos (e.g. "2015–2020").
   - Los **gráficos 7–9** (edad, juventud, nacionalidad) leen los JSON crudos y se adaptan al periodo.
   - Las **conclusiones** están redactadas de forma agnóstica al periodo.
   - No es necesario modificar ninguna celda del notebook.

   ```bash
   jupyter notebook notebooks/eda.ipynb
   ```

### Tablas descargadas por `fetch_data.py`

| Tabla INE | Descripción | Uso |
|---|---|---|
| 65345 | Población 16+ por actividad, sexo y provincia | CSV principal |
| 65349 | Tasas de actividad/paro/empleo por provincia y sexo | CSV principal |
| 65354 | Ocupados por sector económico y provincia | CSV principal |
| 65219 | Tasas de paro por sexo y grupo de edad | Gráficos 7–8 |
| 65086 | Activos por nacionalidad, sexo y grupo de edad | Gráfico 9 (merge) |
| 65112 | Ocupados por nacionalidad, sexo y grupo de edad | Gráfico 9 (merge) |

### Ejemplos de uso

```bash
# Periodo original del proyecto
python fetch_data.py --start 2020 --end 2025

# Crisis financiera 2008
python fetch_data.py --start 2008 --end 2014

# Pre-pandemia
python fetch_data.py --start 2015 --end 2020

# Rango largo (20 años)
python fetch_data.py --start 2005 --end 2025

# Solo descargar, sin generar CSV dirty
python fetch_data.py --start 2020 --end 2025 --no-dirty

# Fetch + limpieza en un solo comando
python main.py --fetch --start 2015 --end 2020
```

### Diseño adaptativo al periodo

Todo el código del proyecto es **agnóstico al periodo seleccionado**. No contiene fechas hardcodeadas:

| Componente | Mecanismo de adaptación |
|---|---|
| `fetch_data.py` | Parámetros `--start` / `--end` para definir el rango |
| `src/cleaning.py` | Parsing de fechas y dimensiones sin referencia a años concretos |
| `src/features.py` | Feature engineering temporal genérico (trimestre, mes, year) |
| `src/viz.py` | Genera los 9 gráficos con títulos que incluyen el rango temporal detectado en los datos |
| `main.py` | Orquesta todo el pipeline (fetch + clean + features + charts) en un solo comando |
| `notebooks/eda.ipynb` | Deriva `PERIOD_LABEL` de los datos y lo usa en todos los títulos de gráficos |

### Notas importantes

- La API del INE es pública y gratuita; no requiere API key.
- El script incluye reintentos automáticos (3 intentos con backoff exponencial) y un delay de cortesía de 1s entre peticiones.
- **Los datos de la EPA están disponibles trimestralmente desde 2002.** Si se especifica `--start` con un año anterior a 2002, la API del INE devolverá los datos desde 2002 sin generar error.
- El pipeline completo (`main.py`) ejecuta limpieza, features y generación de los 9 gráficos en `charts/`. Todos los componentes son agnósticos al periodo: no contienen fechas hardcodeadas.
- La suciedad intencional del CSV dirty es determinista (seed=42), por lo que ejecutar dos veces con el mismo periodo produce exactamente el mismo fichero.
