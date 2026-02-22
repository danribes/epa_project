"""Basic tests for the EPA pipeline modules."""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project root is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import ROOT as CFG_ROOT, DATA_RAW, DATA_PROCESSED, RAW_PATH
from src.io import load_csv
from src.cleaning import clean
from src.features import build_features
from src.utils import assert_columns, validate_clean


# ---------------------------------------------------------------------------
# src/config.py
# ---------------------------------------------------------------------------

def test_config_paths_exist():
    """Config paths point to real directories / files."""
    assert CFG_ROOT.is_dir(), f"ROOT {CFG_ROOT} is not a directory"
    assert DATA_RAW.is_dir(), f"DATA_RAW {DATA_RAW} is not a directory"
    assert DATA_PROCESSED.is_dir(), f"DATA_PROCESSED {DATA_PROCESSED} is not a directory"
    assert RAW_PATH.exists(), f"RAW_PATH {RAW_PATH} does not exist"


# ---------------------------------------------------------------------------
# src/io.py
# ---------------------------------------------------------------------------

def test_load_csv_returns_dataframe():
    """load_csv returns a DataFrame with expected shape."""
    df = load_csv(RAW_PATH)
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] > 0, "DataFrame is empty"
    assert df.shape[1] == 8, f"Expected 8 columns, got {df.shape[1]}"


# ---------------------------------------------------------------------------
# src/cleaning.py
# ---------------------------------------------------------------------------

def test_clean_produces_expected_columns():
    """clean() produces the required output columns."""
    df = load_csv(RAW_PATH)
    df_clean = clean(df)
    required = ['tabla', 'serie_cod', 'anyo', 'periodo_id', 'valor',
                'fecha', 'provincia', 'sexo', 'actividad']
    for col in required:
        assert col in df_clean.columns, f"Missing column: {col}"


def test_clean_removes_duplicates():
    """clean() has no duplicates on the composite key."""
    df_clean = clean(load_csv(RAW_PATH))
    dupes = df_clean.duplicated(subset=['tabla', 'serie_cod', 'anyo', 'periodo_id']).sum()
    assert dupes == 0, f"Found {dupes} duplicate rows after cleaning"


def test_clean_valor_is_numeric():
    """valor column is numeric after cleaning."""
    df_clean = clean(load_csv(RAW_PATH))
    assert pd.api.types.is_numeric_dtype(df_clean['valor']), \
        f"valor dtype is {df_clean['valor'].dtype}, expected numeric"


def test_clean_fecha_is_datetime():
    """fecha column is datetime after cleaning."""
    df_clean = clean(load_csv(RAW_PATH))
    assert pd.api.types.is_datetime64_any_dtype(df_clean['fecha']), \
        f"fecha dtype is {df_clean['fecha'].dtype}, expected datetime"


def test_clean_sexo_canonical():
    """sexo column only contains canonical values."""
    df_clean = clean(load_csv(RAW_PATH))
    valid = {'Ambos sexos', 'Hombres', 'Mujeres'}
    unexpected = set(df_clean['sexo'].unique()) - valid
    assert len(unexpected) == 0, f"Unexpected sexo values: {unexpected}"


# ---------------------------------------------------------------------------
# src/features.py
# ---------------------------------------------------------------------------

def test_build_features_adds_columns():
    """build_features adds the 7 expected feature columns."""
    df = build_features(clean(load_csv(RAW_PATH)))
    expected = ['trimestre', 'mes', 'year', 'trimestre_label',
                'fuente', 'es_nacional', 'ccaa']
    for col in expected:
        assert col in df.columns, f"Missing feature column: {col}"


def test_build_features_final_shape():
    """Final DataFrame has 17 columns."""
    df = build_features(clean(load_csv(RAW_PATH)))
    assert df.shape[1] == 17, f"Expected 17 columns, got {df.shape[1]}"


# ---------------------------------------------------------------------------
# src/utils.py
# ---------------------------------------------------------------------------

def test_assert_columns_raises_on_missing():
    """assert_columns raises ValueError when columns are missing."""
    df = pd.DataFrame({'a': [1], 'b': [2]})
    with pytest.raises(ValueError, match="Missing columns"):
        assert_columns(df, ['a', 'b', 'c'])


def test_assert_columns_passes_on_present():
    """assert_columns does not raise when all columns present."""
    df = pd.DataFrame({'a': [1], 'b': [2]})
    assert_columns(df, ['a', 'b'])  # should not raise


def test_validate_clean_passes():
    """validate_clean passes on the actual cleaned data."""
    df_clean = clean(load_csv(RAW_PATH))
    validate_clean(df_clean)  # should not raise
