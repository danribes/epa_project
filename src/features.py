import pandas as pd


CCAA_MAP = {
    'Almería': 'Andalucía', 'Cádiz': 'Andalucía', 'Córdoba': 'Andalucía',
    'Granada': 'Andalucía', 'Huelva': 'Andalucía', 'Jaén': 'Andalucía',
    'Málaga': 'Andalucía', 'Sevilla': 'Andalucía',
    'Huesca': 'Aragón', 'Teruel': 'Aragón', 'Zaragoza': 'Aragón',
    'Asturias': 'Asturias',
    'Balears, Illes': 'Illes Balears',
    'Palmas, Las': 'Canarias', 'Santa Cruz de Tenerife': 'Canarias',
    'Cantabria': 'Cantabria',
    'Ávila': 'Castilla y León', 'Burgos': 'Castilla y León', 'León': 'Castilla y León',
    'Palencia': 'Castilla y León', 'Salamanca': 'Castilla y León',
    'Segovia': 'Castilla y León', 'Soria': 'Castilla y León',
    'Valladolid': 'Castilla y León', 'Zamora': 'Castilla y León',
    'Albacete': 'Castilla-La Mancha', 'Ciudad Real': 'Castilla-La Mancha',
    'Cuenca': 'Castilla-La Mancha', 'Guadalajara': 'Castilla-La Mancha',
    'Toledo': 'Castilla-La Mancha',
    'Barcelona': 'Cataluña', 'Girona': 'Cataluña', 'Lleida': 'Cataluña',
    'Tarragona': 'Cataluña',
    'Alicante/Alacant': 'Comunitat Valenciana', 'Castellón/Castelló': 'Comunitat Valenciana',
    'Valencia/València': 'Comunitat Valenciana',
    'Badajoz': 'Extremadura', 'Cáceres': 'Extremadura',
    'Coruña, A': 'Galicia', 'Lugo': 'Galicia', 'Ourense': 'Galicia',
    'Pontevedra': 'Galicia',
    'Madrid': 'Comunidad de Madrid',
    'Murcia': 'Región de Murcia',
    'Navarra': 'Navarra',
    'Araba/Álava': 'País Vasco', 'Bizkaia': 'País Vasco', 'Gipuzkoa': 'País Vasco',
    'Rioja, La': 'La Rioja',
    'Ceuta': 'Ceuta', 'Melilla': 'Melilla',
    'Total Nacional': 'Total Nacional',
}

PERIODO_MAP = {19: 'T4', 20: 'T1', 21: 'T2', 22: 'T3'}

TABLA_MAP = {65345: 'Poblacion', 65349: 'Tasas', 65354: 'Ocupados por sector'}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features: temporal, CCAA mapping, flags."""
    out = df.copy()

    # Temporal
    out['trimestre'] = out['fecha'].dt.to_period('Q').astype('string')
    out['mes'] = out['fecha'].dt.month
    out['year'] = out['fecha'].dt.year
    out['trimestre_label'] = out['periodo_id'].map(PERIODO_MAP).fillna('Otro')

    # Source table
    out['fuente'] = out['tabla'].map(TABLA_MAP)

    # National flag
    out['es_nacional'] = out['provincia'].str.lower().str.contains('total nacional', na=False)

    # CCAA
    out['ccaa'] = out['provincia'].map(CCAA_MAP).fillna('Desconocida')

    return out
