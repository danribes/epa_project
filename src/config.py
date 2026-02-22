"""Centralized path constants for the EPA project."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
CHARTS_DIR = ROOT / "charts"

RAW_PATH = DATA_RAW / "epa_mercado_laboral_dirty.csv"
OUT_PATH = DATA_PROCESSED / "epa_mercado_laboral_clean.csv"
