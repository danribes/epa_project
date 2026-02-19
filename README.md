# Analisis del Mercado Laboral Espanol (EPA)

Proyecto de analisis exploratorio de datos (EDA) sobre el mercado laboral espanol, utilizando datos abiertos del Instituto Nacional de Estadistica (INE) — Encuesta de Poblacion Activa (EPA). El proyecto esta disenado para funcionar con **cualquier periodo** de datos EPA (trimestrales desde 2002).

## 1) Objetivo

Entender la estructura del mercado laboral espanol por provincia, sexo y sector economico, su evolucion trimestral, y las desigualdades territoriales y de genero en empleo y desempleo. El periodo de analisis es configurable por el usuario (por defecto 2020-2025).

## 2) Dataset

- **Fuente:** API publica del INE — [servicios.ine.es/wstempus/js](https://servicios.ine.es/wstempus/js)
  - Tabla 65345: Poblacion 16+ por relacion con la actividad, sexo y provincia
  - Tabla 65349: Tasas de actividad, paro y empleo por provincia y sexo
  - Tabla 65354: Ocupados por sector economico y provincia
  - Tabla 65219: Tasas de paro por sexo y grupo de edad
  - Tabla 65086: Activos por nacionalidad, sexo y grupo de edad
  - Tabla 65112: Ocupados por nacionalidad, sexo y grupo de edad
- **Filas/columnas:** ~40,700 filas x 8 columnas (raw, para un rango de 6 anos), ~40,700 x 17 (tras limpieza + features). El tamano exacto depende del periodo seleccionado por el usuario.
- **Variables clave:** provincia, sexo, tipo de actividad, fecha (trimestral), valor (miles de personas o %)
- **Datos adicionales:** respuestas JSON crudas de la API en `data/raw/`
- **Nota metodologica (grafico 9):** La API del INE no publica una tabla con tasas de paro desglosadas simultaneamente por nacionalidad y grupo de edad. Para obtenerlas, se descargaron las tablas 65086 (activos) y 65112 (ocupados) con las mismas dimensiones (nacionalidad x sexo x edad) y se calculo: `tasa_paro = (activos - ocupados) / activos * 100`. El resultado fue validado contra la tabla oficial 65336 (tasas de paro por nacionalidad) con coincidencia exacta.

## 3) Preguntas

- Q1: ¿Cuales son las provincias con mayor y menor tasa de paro? ¿Ha cambiado el ranking a lo largo del periodo?
- Q2: ¿Existe brecha de genero en las tasas de actividad, empleo y paro? ¿Varia por provincia?
- Q3: ¿Como se distribuye el empleo por sector economico y como varia geograficamente?
- Q4: ¿Como ha evolucionado el empleo total a lo largo del periodo?
- Q5: ¿Existe estacionalidad en el empleo/paro (trimestral)? ¿Afecta mas a unas provincias que a otras?
- Q6: ¿Como varia la tasa de paro segun el grupo de edad? ¿Que diferencias hay por sexo?
- Q7: ¿Como ha evolucionado el paro juvenil (16-19 y 20-24 anos) frente al total a lo largo del periodo?
- Q8: ¿Existe brecha de desempleo entre trabajadores espanoles y extranjeros? ¿Varia segun la edad?

## 4) Data issues & fixes

| Problema | Solucion |
|---|---|
| Nombres de columna sucios (espacios, mayusculas) | `strip().lower().replace(' ', '_')` |
| Valor como texto con coma decimal (`203,2`) | `.str.replace(",", ".")` + `pd.to_numeric` |
| Fechas en 5 formatos distintos (ISO, dd/mm, ms, textual) | Parser custom con fallbacks |
| Serie_nombre en mayusculas/minusculas inconsistente | Parsing sobre version `.lower()` con mapping canonico |
| Todas las dimensiones empaquetadas en un solo string | Parsing regex por tabla para extraer provincia, sexo, actividad |
| ~3% de nulls en valor | Mantenidos como NaN (no imputados) |
| 20 filas duplicadas | `drop_duplicates()` por clave compuesta |

## 5) Pipeline

```
fetch (fetch_data.py) -> raw CSV -> clean (src/cleaning.py) -> validate (src/utils.py) -> features (src/features.py) -> export (data/processed/) -> charts (src/viz.py -> charts/)
```

El pipeline completo — incluyendo la generacion de los 9 graficos — se ejecuta con un solo comando (`python main.py --fetch`). Los graficos se guardan automaticamente en `charts/`.

## 6) Hallazgos

> **Nota:** Los hallazgos a continuacion corresponden al periodo por defecto (2020-2025). Al ejecutar el proyecto con un periodo diferente, los resultados variaran.

1. **Fuerte desigualdad territorial:** Las provincias del sur (Andalucia, Extremadura, Canarias) mantienen tasas de paro significativamente mas altas que las del norte (Pais Vasco, Navarra, Aragon). Esta brecha se ha mantenido estable a lo largo del periodo. (ver grafico 1 y 6)

2. **Brecha de genero persistente pero reduciendose:** La tasa de paro femenina es consistentemente mas alta que la masculina, aunque la diferencia se ha ido estrechando. (ver grafico 2)

3. **Economia terciarizada:** El sector servicios domina abrumadoramente el empleo (>75%), con agricultura, industria y construccion en niveles relativamente estables. (ver grafico 3)

4. **Evolucion del empleo total:** El empleo total ha mostrado una trayectoria al alza a lo largo del periodo analizado. (ver grafico 5)

5. **Concentracion del empleo:** La distribucion de empleo por provincia esta altamente sesgada — Madrid y Barcelona concentran una proporcion desproporcionada. (ver grafico 4)

6. **Paro juvenil extremo:** Los menores de 25 anos sufren tasas de paro muy superiores a la media nacional. El grupo 16-19 supera el 30% y el grupo 20-24 ronda el 22%, frente al ~10% general. La brecha de genero es menor entre jovenes. (ver grafico 7)

7. **Tendencia descendente del paro juvenil:** A lo largo del periodo, el paro juvenil ha descendido significativamente, aunque sigue triplicando (16-19) y duplicando (20-24) la tasa general respectivamente. (ver grafico 8)

8. **Brecha por nacionalidad en todas las edades:** Los trabajadores extranjeros presentan tasas de paro superiores a los espanoles en todos los grupos de edad. La brecha relativa es mayor en edades centrales (45-54: 6.7% vs 12.0%) y mayores (55+: 8.3% vs 15.7%), mientras que entre jovenes (16-24) la diferencia absoluta es menor (~3pp). (ver grafico 9)

## 7) Estructura del proyecto

```
epa_project/
├── fetch_data.py                        # Descarga de datos del INE
├── main.py                              # Pipeline end-to-end
├── data/
│   ├── raw/
│   │   ├── epa_mercado_laboral_dirty.csv       # CSV principal (filas dependen del periodo)
│   │   ├── epa_mercado_laboral_raw.csv         # CSV sin suciedad extra
│   │   ├── epa_poblacion_actividad_sexo_provincia_raw.json
│   │   ├── epa_tasas_actividad_paro_empleo_provincia_raw.json
│   │   ├── epa_ocupados_sector_provincia_raw.json
│   │   ├── epa_tasas_paro_edad_raw.json
│   │   ├── epa_activos_nacionalidad_edad_raw.json
│   │   └── epa_ocupados_nacionalidad_edad_raw.json
│   └── processed/
│       └── epa_mercado_laboral_clean.csv       # Datos limpios (filas x 17)
├── charts/
│   ├── 01_tasa_paro_por_provincia.png
│   ├── 02_brecha_genero_paro.png
│   ├── 03_empleo_por_sector.png
│   ├── 04_distribucion_ocupados.png
│   ├── 05_evolucion_empleo_total.png
│   ├── 06_heatmap_paro_ccaa.png
│   ├── 07_paro_por_edad.png
│   ├── 08_paro_juvenil_evolucion.png
│   └── 09_paro_edad_nacionalidad.png
├── src/
│   ├── __init__.py
│   ├── io.py                            # Carga y guardado de datos
│   ├── cleaning.py                      # Limpieza de datos
│   ├── features.py                      # Feature engineering
│   ├── viz.py                           # Graficos reutilizables
│   └── utils.py                         # Validaciones y utilidades
├── README.md
└── requirements.txt
```

## 8) Como ejecutar

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

Este paso descarga las 6 tablas de la EPA desde la API publica del INE, genera los ficheros JSON crudos y los CSV raw y dirty en `data/raw/`. El parametro `--start` y `--end` definen el rango de anos a descargar.

### Paso 5 — Ejecutar el pipeline de limpieza + graficos

```bash
python main.py
```

Salida esperada:

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

Alternativamente, se pueden combinar descarga + limpieza + graficos en un solo comando:

```bash
python main.py --fetch --start 2020 --end 2025
```

### Paso 6 — Explorar el notebook (opcional)

```bash
pip install jupyter
jupyter notebook notebooks/eda.ipynb
```

Tambien existe una version ya ejecutada (`notebooks/eda_executed.ipynb`) para consultar los resultados sin re-ejecutar.

## 9) Reproducir con un periodo diferente

El proyecto esta disenado para funcionar con **cualquier periodo** de datos EPA. Para cambiar el rango temporal:

> **Importante:** La EPA publica datos trimestrales **desde 2002**. Si se especifica un ano de inicio anterior a 2002, la API del INE simplemente devolvera los datos desde 2002 en adelante, sin generar error. El pipeline procesara los datos disponibles sin problemas, pero el periodo real de los graficos y resultados sera 2002–(ano de fin), no el solicitado.

### Paso a paso

1. **Elegir el periodo.** La EPA publica datos trimestrales desde 2002. Ejemplo: 2015-2020.

2. **Descargar los datos.** El script `fetch_data.py` se conecta a la API del INE usando el parametro `date=YYYYMMDD:YYYYMMDD` para solicitar el rango exacto.

```bash
python fetch_data.py --start 2015 --end 2020
```

Esto descarga las 6 tablas y genera:
- `data/raw/*.json` — respuestas JSON crudas de la API (una por tabla)
- `data/raw/epa_mercado_laboral_raw.csv` — CSV combinado limpio
- `data/raw/epa_mercado_laboral_dirty.csv` — CSV con suciedad intencional

3. **Ejecutar el pipeline.** El codigo de limpieza, features y graficos es completamente agnostico al periodo — no tiene fechas hardcodeadas. Los 9 graficos se generan automaticamente en `charts/`.

```bash
python main.py
```

4. **Explorar el notebook (opcional).** El notebook `eda.ipynb` lee del CSV dirty y se adapta automaticamente al periodo descargado:
   - Los **titulos de todos los graficos** incluyen el rango temporal detectado en los datos (e.g. "2015–2020").
   - Los **graficos 7-9** (edad, juventud, nacionalidad) leen los JSON crudos de `data/raw/` y se adaptan al periodo.
   - Las **conclusiones** estan redactadas de forma agnostica al periodo.
   - No es necesario modificar ninguna celda del notebook.

```bash
jupyter notebook notebooks/eda.ipynb
```

### Que tablas descarga `fetch_data.py`

| Tabla INE | Descripcion | Uso |
|---|---|---|
| 65345 | Poblacion 16+ por actividad, sexo y provincia | CSV principal |
| 65349 | Tasas de actividad/paro/empleo por provincia y sexo | CSV principal |
| 65354 | Ocupados por sector economico y provincia | CSV principal |
| 65219 | Tasas de paro por sexo y grupo de edad | Graficos 7-8 |
| 65086 | Activos por nacionalidad, sexo y grupo de edad | Grafico 9 (merge) |
| 65112 | Ocupados por nacionalidad, sexo y grupo de edad | Grafico 9 (merge) |

### Ejemplos de uso

```bash
# Periodo original del proyecto
python fetch_data.py --start 2020 --end 2025

# Crisis financiera 2008
python fetch_data.py --start 2008 --end 2014

# Pre-pandemia
python fetch_data.py --start 2015 --end 2020

# Rango largo (20 anos)
python fetch_data.py --start 2005 --end 2025

# Solo descargar, sin generar CSV dirty
python fetch_data.py --start 2020 --end 2025 --no-dirty

# Fetch + limpieza en un solo comando
python main.py --fetch --start 2015 --end 2020
```

### Diseno adaptativo al periodo

Todo el codigo del proyecto es **agnostico al periodo seleccionado**. No contiene fechas hardcodeadas. Los componentes que se adaptan automaticamente son:

| Componente | Mecanismo de adaptacion |
|---|---|
| `fetch_data.py` | Parametros `--start` / `--end` para definir el rango |
| `src/cleaning.py` | Parsing de fechas y dimensiones sin referencia a anos concretos |
| `src/features.py` | Feature engineering temporal generico (trimestre, mes, year) |
| `src/viz.py` | Genera los 9 graficos con titulos que incluyen el rango temporal detectado en los datos. Graficos 1-6 derivan el periodo del DataFrame; graficos 7-9 leen los JSON crudos y detectan el ultimo trimestre disponible |
| `main.py` | Orquesta todo el pipeline (fetch + clean + features + charts) en un solo comando |
| `notebooks/eda.ipynb` | Deriva `PERIOD_LABEL` de los datos (`df_feat['anyo'].min()` / `.max()`) y lo usa en todos los titulos de graficos |

### Notas importantes

- La API del INE es publica y gratuita; no requiere API key.
- El script incluye reintentos automaticos (3 intentos con backoff exponencial) y un delay de cortesia de 1s entre peticiones.
- **Los datos de la EPA estan disponibles trimestralmente desde 2002.** Si se especifica `--start` con un ano anterior a 2002, la API del INE devolvera los datos desde 2002 sin generar error. El pipeline funcionara correctamente, pero los resultados reflejaran el periodo real disponible (2002 en adelante), no el solicitado.
- El pipeline completo (`main.py`) ejecuta limpieza, features y generacion de los 9 graficos en `charts/`. Todos los componentes son agnosticos al periodo: no contienen fechas hardcodeadas.
- La suciedad intencional del CSV dirty es determinista (seed=42), por lo que ejecutar dos veces con el mismo periodo produce exactamente el mismo fichero.
