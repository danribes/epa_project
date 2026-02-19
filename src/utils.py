import pandas as pd


def assert_columns(df: pd.DataFrame, required: list[str]):
    """Raise if required columns are missing."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f'Missing columns: {missing}')


def validate_clean(df: pd.DataFrame):
    """Basic validations on the cleaned DataFrame."""
    assert_columns(df, ['tabla', 'serie_cod', 'anyo', 'periodo_id', 'valor',
                        'fecha', 'provincia', 'sexo', 'actividad'])
    assert df.duplicated(subset=['tabla', 'serie_cod', 'anyo', 'periodo_id']).sum() == 0, \
        'Duplicates remain!'
    assert pd.api.types.is_numeric_dtype(df['valor']), \
        f'valor is not numeric! dtype={df["valor"].dtype}'
    assert pd.api.types.is_datetime64_any_dtype(df['fecha']), \
        'fecha is not datetime!'
    assert df['sexo'].isin(['Ambos sexos', 'Hombres', 'Mujeres']).all(), \
        f'sexo has unexpected values: {df["sexo"].unique()}'
    print('All validations passed.')
