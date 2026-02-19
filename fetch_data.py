#!/usr/bin/env python3
"""
fetch_data.py — Descarga datos de la EPA desde la API publica del INE.

Descarga las 6 tablas de la EPA necesarias para el proyecto,
las guarda como JSON crudo y genera el CSV combinado (raw y dirty).

Uso:
    python fetch_data.py --start 2020 --end 2025
    python fetch_data.py --start 2015 --end 2020
    python fetch_data.py                             # ultimos 5 anos

Tablas descargadas:
    Principales (combinadas en CSV):
        65345 — Poblacion 16+ por actividad, sexo y provincia
        65349 — Tasas de actividad/paro/empleo por provincia y sexo
        65354 — Ocupados por sector economico y provincia
    Adicionales (solo JSON, para graficos 7-9):
        65219 — Tasas de paro por sexo y grupo de edad
        65086 — Activos por nacionalidad, sexo y grupo de edad
        65112 — Ocupados por nacionalidad, sexo y grupo de edad
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA"

MAIN_TABLES = {
    65345: {
        "name": "epa_poblacion_actividad_sexo_provincia",
        "description": "Poblacion 16+ por actividad, sexo y provincia",
    },
    65349: {
        "name": "epa_tasas_actividad_paro_empleo_provincia",
        "description": "Tasas de actividad/paro/empleo por provincia y sexo",
    },
    65354: {
        "name": "epa_ocupados_sector_provincia",
        "description": "Ocupados por sector economico y provincia",
    },
}

EXTRA_TABLES = {
    65219: {
        "name": "epa_tasas_paro_edad",
        "description": "Tasas de paro por sexo y grupo de edad",
    },
    65086: {
        "name": "epa_activos_nacionalidad_edad",
        "description": "Activos por nacionalidad, sexo y grupo de edad",
    },
    65112: {
        "name": "epa_ocupados_nacionalidad_edad",
        "description": "Ocupados por nacionalidad, sexo y grupo de edad",
    },
}

RAW_CSV_COLUMNS = [
    "tabla", "serie_cod", "serie_nombre", "fecha_ms",
    "anyo", "periodo_id", "valor", "secreto",
]

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def build_url(tabla_id: int, start_year: int, end_year: int) -> str:
    """Build the INE API URL with a date range filter.

    The EPA publishes quarterly data.  To capture full years we request
    from Jan-1 of *start_year* through Dec-31 of *end_year*.
    """
    return f"{BASE_URL}/{tabla_id}?date={start_year}0101:{end_year}1231"


def fetch_table(tabla_id: int, start_year: int, end_year: int,
                max_retries: int = 3, backoff: float = 2.0) -> list[dict]:
    """Fetch a single table from the INE API with retry logic."""
    url = build_url(tabla_id, start_year, end_year)

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
            data = resp.json()

            if not data:
                print(f"  AVISO: Tabla {tabla_id} devolvio 0 series para "
                      f"{start_year}-{end_year}.")
                return []

            if not isinstance(data, list) or "Data" not in data[0]:
                raise ValueError(
                    f"Respuesta inesperada para tabla {tabla_id}: "
                    f"type={type(data).__name__}")

            return data

        except requests.exceptions.RequestException as exc:
            if attempt < max_retries:
                wait = backoff ** attempt
                print(f"  Error intento {attempt}/{max_retries}: {exc}")
                print(f"  Reintentando en {wait:.0f}s ...")
                time.sleep(wait)
            else:
                raise RuntimeError(
                    f"Fallo al descargar tabla {tabla_id} tras "
                    f"{max_retries} intentos: {exc}") from exc


# ---------------------------------------------------------------------------
# JSON → DataFrame
# ---------------------------------------------------------------------------


def flatten_table_json(tabla_id: int,
                       series_list: list[dict]) -> pd.DataFrame:
    """Flatten an INE JSON response into a tabular DataFrame.

    Each element in *series_list* has:
      COD      — series code (e.g. "EPA387793")
      Nombre   — series name (e.g. "Total Nacional. Ambos sexos. ...")
      Data     — list of {Fecha, FK_Periodo, Anyo, Valor, Secreto, ...}
    """
    rows = []
    for serie in series_list:
        cod = serie["COD"]
        nombre = serie["Nombre"].strip()
        for dp in serie.get("Data", []):
            rows.append({
                "tabla": tabla_id,
                "serie_cod": cod,
                "serie_nombre": nombre,
                "fecha_ms": dp["Fecha"],
                "anyo": dp["Anyo"],
                "periodo_id": dp["FK_Periodo"],
                "valor": dp["Valor"],
                "secreto": dp["Secreto"],
            })
    return pd.DataFrame(rows, columns=RAW_CSV_COLUMNS)


# ---------------------------------------------------------------------------
# Dirty CSV generation
# ---------------------------------------------------------------------------


def make_dirty(df_raw: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Apply intentional data-quality issues to the raw DataFrame.

    Transformations (deterministic via *seed*):
      - Dirty column names (spaces, mixed case)
      - ~10 %  comma-decimal separators in valor
      - ~3 %   null values in valor
      - 5 different date formats (from fecha_ms)
      - ~5 %   UPPERCASED serie_nombre
      - 20 duplicate rows
    """
    rng = random.Random(seed)
    n = len(df_raw)

    # -- Fecha: convert ms → 5 mixed human-readable formats --
    date_fmts = ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y", None]

    def format_fecha(ms_val, fmt):
        if pd.isna(ms_val):
            return ""
        ts = pd.Timestamp(int(ms_val), unit="ms")
        if fmt is None:
            return str(int(ms_val))
        return ts.strftime(fmt)

    fechas = [format_fecha(ms, date_fmts[i % len(date_fmts)])
              for i, ms in enumerate(df_raw["fecha_ms"])]

    # -- Valor: ~10 % comma decimals, ~3 % nulls --
    valor_str = df_raw["valor"].astype(str).tolist()
    for idx in rng.sample(range(n), k=int(n * 0.10)):
        if valor_str[idx] != "nan":
            valor_str[idx] = valor_str[idx].replace(".", ",")
    for idx in rng.sample(range(n), k=int(n * 0.03)):
        valor_str[idx] = ""

    # -- Serie_nombre: ~5 % uppercased --
    nombres = df_raw["serie_nombre"].tolist()
    for idx in rng.sample(range(n), k=int(n * 0.05)):
        nombres[idx] = nombres[idx].upper()

    # -- Assemble with dirty column names --
    dirty = pd.DataFrame({
        "Tabla": df_raw["tabla"],
        "Serie_Cod": df_raw["serie_cod"],
        "Serie Nombre": nombres,
        "Anyo": df_raw["anyo"],
        "Periodo_ID": df_raw["periodo_id"],
        " Valor": valor_str,
        "Secreto": df_raw["secreto"],
        "Fecha ": fechas,
    })

    # -- Add 20 duplicate rows --
    dups = dirty.iloc[rng.sample(range(len(dirty)), k=20)].copy()
    dirty = pd.concat([dirty, dups], ignore_index=True)
    dirty = dirty.sample(frac=1, random_state=seed).reset_index(drop=True)

    return dirty


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def fetch_all(start_year: int, end_year: int, output_dir: Path,
              create_dirty: bool = True) -> None:
    """Download all EPA tables and produce raw + dirty CSVs."""
    # Clean previous data files before downloading
    if output_dir.exists():
        for ext in ("*.json", "*.csv"):
            for f in output_dir.glob(ext):
                f.unlink()
        print(f"Limpiados datos anteriores en {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    all_tables = {**MAIN_TABLES, **EXTRA_TABLES}

    print("=" * 60)
    print(f"EPA Data Fetch: {start_year}–{end_year}")
    print(f"Output: {output_dir}")
    print("=" * 60)

    # -- Fetch & save JSON ---------------------------------------------------
    json_data: dict[int, list[dict]] = {}
    for tabla_id, meta in all_tables.items():
        print(f"\n[{tabla_id}] Descargando: {meta['description']} ...")
        data = fetch_table(tabla_id, start_year, end_year)
        json_data[tabla_id] = data

        json_path = output_dir / f"{meta['name']}_raw.json"
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

        total_dp = sum(len(s.get("Data", [])) for s in data)
        print(f"  -> {json_path.name}  ({len(data)} series, "
              f"{total_dp} data points)")

        time.sleep(1)  # API courtesy delay

    # -- Flatten main tables into combined raw CSV ---------------------------
    print("\nCombinando tablas principales en CSV ...")
    frames = []
    for tabla_id in MAIN_TABLES:
        df_t = flatten_table_json(tabla_id, json_data[tabla_id])
        frames.append(df_t)
        print(f"  Tabla {tabla_id}: {len(df_t):,} filas")

    df_raw = pd.concat(frames, ignore_index=True)
    raw_path = output_dir / "epa_mercado_laboral_raw.csv"
    df_raw.to_csv(raw_path, index=False)
    print(f"  -> {raw_path.name}  ({df_raw.shape[0]:,} filas x "
          f"{df_raw.shape[1]} columnas)")

    # -- Dirty CSV -----------------------------------------------------------
    if create_dirty:
        print("\nGenerando CSV con suciedad intencional ...")
        df_dirty = make_dirty(df_raw)
        dirty_path = output_dir / "epa_mercado_laboral_dirty.csv"
        df_dirty.to_csv(dirty_path, index=False)
        print(f"  -> {dirty_path.name}  ({df_dirty.shape[0]:,} filas)")
        print("     ~10% comas decimales | ~3% nulls | 5 formatos de fecha "
              "| ~5% MAYUSCULAS | 20 duplicados")

    print(f"\n{'=' * 60}")
    print("Descarga completada.")
    print(f"{'=' * 60}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    current_year = datetime.now().year
    p = argparse.ArgumentParser(
        description="Descarga datos de la EPA desde la API del INE.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("-s", "--start", type=int, default=current_year - 5,
                   help=f"Ano de inicio (default: {current_year - 5})")
    p.add_argument("-e", "--end", type=int, default=current_year,
                   help=f"Ano de fin (default: {current_year})")
    p.add_argument("--dirty", action=argparse.BooleanOptionalAction,
                   default=True,
                   help="Generar CSV con suciedad (default: True)")
    p.add_argument("-o", "--output-dir", type=Path, default=None,
                   help="Directorio de salida (default: data/raw/)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.start >= args.end:
        print(f"Error: --start ({args.start}) debe ser < --end ({args.end})")
        sys.exit(1)
    if args.end - args.start > 30:
        print(f"Error: rango maximo 30 anos "
              f"({args.end - args.start} solicitados)")
        sys.exit(1)

    root = Path(__file__).resolve().parent
    out_dir = args.output_dir or (root / "data" / "raw")

    fetch_all(args.start, args.end, out_dir, create_dirty=args.dirty)
