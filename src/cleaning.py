import pandas as pd
from datetime import datetime


# Province canonical names (fixes for UPPERCASED variants)
PROVINCIA_FIXES = {
    'albacete': 'Albacete', 'alicante/alacant': 'Alicante/Alacant',
    'almería': 'Almería', 'araba/álava': 'Araba/Álava', 'asturias': 'Asturias',
    'badajoz': 'Badajoz', 'balears, illes': 'Balears, Illes',
    'barcelona': 'Barcelona', 'bizkaia': 'Bizkaia', 'burgos': 'Burgos',
    'cantabria': 'Cantabria', 'castellón/castelló': 'Castellón/Castelló',
    'ceuta': 'Ceuta', 'ciudad real': 'Ciudad Real', 'coruña, a': 'Coruña, A',
    'cuenca': 'Cuenca', 'cáceres': 'Cáceres', 'cádiz': 'Cádiz',
    'córdoba': 'Córdoba', 'gipuzkoa': 'Gipuzkoa', 'girona': 'Girona',
    'granada': 'Granada', 'guadalajara': 'Guadalajara', 'huelva': 'Huelva',
    'huesca': 'Huesca', 'jaén': 'Jaén', 'león': 'León', 'lleida': 'Lleida',
    'lugo': 'Lugo', 'madrid': 'Madrid', 'melilla': 'Melilla',
    'murcia': 'Murcia', 'málaga': 'Málaga', 'navarra': 'Navarra',
    'ourense': 'Ourense', 'palencia': 'Palencia', 'palmas, las': 'Palmas, Las',
    'pontevedra': 'Pontevedra', 'rioja, la': 'Rioja, La',
    'salamanca': 'Salamanca', 'santa cruz de tenerife': 'Santa Cruz de Tenerife',
    'segovia': 'Segovia', 'sevilla': 'Sevilla', 'soria': 'Soria',
    'tarragona': 'Tarragona', 'teruel': 'Teruel', 'toledo': 'Toledo',
    'total nacional': 'Total Nacional',
    'valencia/valència': 'Valencia/València', 'valladolid': 'Valladolid',
    'zamora': 'Zamora', 'zaragoza': 'Zaragoza', 'ávila': 'Ávila',
}

SEXO_CANONICAL = {'ambos sexos': 'Ambos sexos', 'hombres': 'Hombres', 'mujeres': 'Mujeres'}


def canon_prov(s: str) -> str:
    return PROVINCIA_FIXES.get(s.lower().strip(), s.strip().title())


def canon_sexo(s: str) -> str:
    return SEXO_CANONICAL.get(s.lower().strip(), s.strip().title())


def parse_fecha(val) -> pd.Timestamp:
    """Parse date from mixed formats: ISO, dd/mm/yyyy, yyyy/mm/dd, textual, ms timestamp."""
    if pd.isna(val) or val == '<NA>':
        return pd.NaT
    val = str(val).strip()
    if val.isdigit() and len(val) > 10:
        try:
            return pd.Timestamp(int(val), unit='ms')
        except Exception:
            pass
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%b %d, %Y']:
        try:
            return pd.Timestamp(datetime.strptime(val, fmt))
        except (ValueError, AttributeError):
            continue
    try:
        return pd.to_datetime(val, dayfirst=True)
    except Exception:
        return pd.NaT


def _parse_serie_65345(nombre_lower: str) -> dict:
    parts = [p.strip() for p in nombre_lower.split('. ') if p.strip()]
    if parts[0] == 'total nacional':
        return {'provincia': 'Total Nacional', 'sexo': canon_sexo(parts[1]),
                'actividad': parts[3].title()}
    return {'provincia': canon_prov(parts[1]), 'sexo': canon_sexo(parts[0]),
            'actividad': parts[3].title()}


def _parse_serie_65349(nombre_lower: str) -> dict:
    parts = [p.strip() for p in nombre_lower.split('. ') if p.strip()]
    tasa = next((p for p in parts if 'tasa' in p), 'desconocida')
    tasa_display = tasa.replace('tasa de ', 'Tasa de ').replace('la población', 'la poblacion')
    remaining = [p for p in parts if p != tasa and p not in ('total', 'total.', 'personas')]
    provincia, sexo = 'Total Nacional', 'Ambos sexos'
    for r in remaining:
        r_clean = r.rstrip('.')
        if r_clean in ('ambos sexos', 'hombres', 'mujeres'):
            sexo = canon_sexo(r_clean)
        elif r_clean == 'total nacional':
            provincia = 'Total Nacional'
        elif r_clean not in ('total',):
            provincia = canon_prov(r_clean)
    return {'provincia': provincia, 'sexo': sexo, 'actividad': tasa_display}


def _parse_serie_65354(nombre_lower: str) -> dict:
    parts = [p.strip() for p in nombre_lower.split('. ') if p.strip()]
    provincia = canon_prov(parts[0]) if parts[0] != 'ocupados' else 'Total Nacional'
    sector = 'Total'
    for p in parts:
        if p in ('agricultura', 'industria', 'construcción', 'servicios', 'total cnae'):
            sector = p.title()
            break
    return {'provincia': provincia, 'sexo': 'Ambos sexos', 'actividad': f'Ocupados - {sector}'}


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Full cleaning pipeline: column names, types, parsing, dedup."""
    out = df.copy()

    # 1) Column names
    out.columns = [c.strip().lower().replace(' ', '_') for c in out.columns]

    # 2) Numeric: valor
    out['valor'] = out['valor'].astype('string').str.replace(',', '.', regex=False)
    out['valor'] = pd.to_numeric(out['valor'], errors='coerce')

    # 3) serie_nombre: strip, lowercase helper
    out['serie_nombre'] = out['serie_nombre'].astype('string').str.strip()
    out['serie_nombre_lower'] = out['serie_nombre'].str.lower()

    # 4) Parse serie_nombre into provincia, sexo, actividad
    parsers = {65345: _parse_serie_65345, 65349: _parse_serie_65349, 65354: _parse_serie_65354}
    records = []
    for _, row in out.iterrows():
        parser = parsers.get(row['tabla'])
        try:
            parsed = parser(row['serie_nombre_lower']) if parser else {
                'provincia': 'Desconocida', 'sexo': 'Desconocido', 'actividad': 'Desconocida'}
        except Exception:
            parsed = {'provincia': 'Error', 'sexo': 'Error', 'actividad': 'Error'}
        records.append(parsed)
    out = pd.concat([out, pd.DataFrame(records)], axis=1)

    # 5) Dates
    out['fecha'] = out['fecha'].apply(parse_fecha)

    # 6) Normalize sexo
    out['sexo'] = out['sexo'].str.strip().replace(SEXO_CANONICAL)
    out['provincia'] = out['provincia'].str.strip()
    out['actividad'] = out['actividad'].str.strip()

    # 7) Dedup
    out = out.drop_duplicates(subset=['tabla', 'serie_cod', 'anyo', 'periodo_id'])

    # 8) Drop helper columns
    out = out.drop(columns=['serie_nombre_lower', 'secreto'], errors='ignore')

    return out
