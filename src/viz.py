import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _period_label(df):
    return f"{int(df['year'].min())}–{int(df['year'].max())}"


def _load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _json_to_df(series_list, parse_nombre):
    """Flatten JSON series into a DataFrame using a custom nombre parser."""
    rows = []
    for serie in series_list:
        nombre = serie['Nombre'].strip()
        parsed = parse_nombre(nombre)
        if parsed is None:
            continue
        for dp in serie.get('Data', []):
            row = {**parsed,
                   'fecha': pd.Timestamp(dp['Fecha'], unit='ms'),
                   'anyo': dp['Anyo'],
                   'valor': dp['Valor']}
            rows.append(row)
    return pd.DataFrame(rows)


def _parse_edad(nombre_lower):
    """Extract age group string from a serie name."""
    m = re.search(r'(?:de )?(\d+)\s+(?:y más|a \d+)\s+años', nombre_lower)
    if not m:
        return None
    # Return the full match for grouping
    start = m.start()
    end = m.end()
    raw = nombre_lower[start:end].strip()
    # Capitalise first letter
    return raw[0].upper() + raw[1:]


# ---------------------------------------------------------------------------
# Chart 1 — Tasa de paro por provincia
# ---------------------------------------------------------------------------

def plot_paro_por_provincia(df, trimestre=None, save_path=None):
    """Horizontal bar chart of unemployment rate by province."""
    period = _period_label(df)
    mask = (
        (df['tabla'] == 65349) &
        (df['actividad'].str.contains('paro', case=False, na=False)) &
        (df['sexo'] == 'Ambos sexos') &
        (~df['es_nacional'])
    )
    data = df[mask].copy()
    if trimestre is None:
        trimestre = data['trimestre'].dropna().max()
    data = data[data['trimestre'] == trimestre].dropna(subset=['valor'])
    data = data.sort_values('valor', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 14))
    median_val = data['valor'].median()
    colors = ['#e74c3c' if v > median_val else '#2ecc71' for v in data['valor'].values]
    ax.barh(data['provincia'], data['valor'], color=colors)
    ax.set_xlabel('Tasa de paro (%)')
    ax.set_title(f'Tasa de paro por provincia — {trimestre} ({period})')
    ax.axvline(median_val, color='gray', linestyle='--', alpha=0.7, label='Mediana')
    ax.legend()
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 2 — Brecha de genero en tasa de paro
# ---------------------------------------------------------------------------

def plot_brecha_genero(df, save_path=None):
    """Line chart of unemployment rate by sex over time."""
    period = _period_label(df)
    mask = (
        (df['tabla'] == 65349) &
        (df['actividad'].str.contains('paro', case=False, na=False)) &
        (df['sexo'].isin(['Hombres', 'Mujeres'])) &
        (df['es_nacional'])
    )
    data = df[mask].sort_values('fecha')

    fig, ax = plt.subplots(figsize=(12, 5))
    for sexo, color in [('Hombres', '#3498db'), ('Mujeres', '#e74c3c')]:
        sub = data[data['sexo'] == sexo]
        ax.plot(sub['fecha'], sub['valor'], marker='o', label=sexo, color=color, linewidth=2)
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Tasa de paro (%)')
    ax.set_title(f'Evolucion de la tasa de paro por sexo — Total Nacional ({period})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 3 — Empleo por sector economico
# ---------------------------------------------------------------------------

def plot_empleo_por_sector(df, save_path=None):
    """Line chart of employment by economic sector."""
    period = _period_label(df)
    mask = (
        (df['tabla'] == 65354) &
        (df['es_nacional']) &
        (~df['actividad'].str.contains('Total', case=False, na=False))
    )
    data = df[mask].copy()
    data['sector'] = data['actividad'].str.replace('Ocupados - ', '', regex=False)
    data = data.sort_values('fecha')

    fig, ax = plt.subplots(figsize=(12, 5))
    colors = {'Agricultura': '#27ae60', 'Industria': '#2980b9',
              'Construcción': '#f39c12', 'Servicios': '#8e44ad'}
    for sector in data['sector'].unique():
        sub = data[data['sector'] == sector]
        ax.plot(sub['fecha'], sub['valor'], marker='o',
                label=sector, color=colors.get(sector, 'gray'), linewidth=2)
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Ocupados (miles)')
    ax.set_title(f'Empleo por sector economico — Total Nacional ({period})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 4 — Distribucion de ocupados por provincia
# ---------------------------------------------------------------------------

def plot_distribucion_ocupados(df, save_path=None):
    """Horizontal bar chart of average occupied population by province."""
    period = _period_label(df)
    mask = (
        (df['tabla'] == 65345) &
        (df['actividad'].str.contains('Ocupados', case=False, na=False)) &
        (df['sexo'] == 'Ambos sexos') &
        (~df['es_nacional'])
    )
    data = df[mask].dropna(subset=['valor']).copy()
    avg = data.groupby('provincia')['valor'].mean().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 14))
    colors = ['#2980b9' if v < avg.median() else '#e67e22' for v in avg.values]
    ax.barh(avg.index, avg.values, color=colors)
    ax.set_xlabel('Ocupados (miles, media del periodo)')
    ax.set_title(f'Distribucion media de ocupados por provincia ({period})')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 5 — Evolucion del empleo total
# ---------------------------------------------------------------------------

def plot_evolucion_empleo_total(df, save_path=None):
    """Line chart of total employment evolution (national)."""
    period = _period_label(df)
    mask = (
        (df['tabla'] == 65345) &
        (df['actividad'].str.contains('Ocupados', case=False, na=False)) &
        (df['sexo'] == 'Ambos sexos') &
        (df['es_nacional'])
    )
    data = df[mask].dropna(subset=['valor']).sort_values('fecha')

    vmin, vmax = data['valor'].min(), data['valor'].max()
    buffer = (vmax - vmin) * 0.10
    y_bottom = vmin - buffer

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(data['fecha'], data['valor'], marker='o', color='#2c3e50', linewidth=2)
    ax.fill_between(data['fecha'], data['valor'], y_bottom, alpha=0.15, color='#2c3e50')
    ax.set_ylim(bottom=y_bottom)
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Ocupados (miles)')
    ax.set_title(f'Evolucion del empleo total — Total Nacional ({period})')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 6 — Heatmap de paro por CCAA
# ---------------------------------------------------------------------------

def plot_heatmap_paro_ccaa(df, save_path=None):
    """Heatmap of unemployment rate by CCAA and quarter."""
    period = _period_label(df)
    mask = (
        (df['tabla'] == 65349) &
        (df['actividad'].str.contains('paro', case=False, na=False)) &
        (df['sexo'] == 'Ambos sexos') &
        (~df['es_nacional']) &
        (df['ccaa'] != 'Desconocida')
    )
    data = df[mask].dropna(subset=['valor']).copy()
    data['valor'] = data['valor'].astype(float)

    pivot = data.pivot_table(values='valor', index='ccaa', columns='trimestre', aggfunc='mean')
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(14, 10))
    sns.heatmap(pivot, annot=False, cmap='RdYlGn_r', ax=ax,
                linewidths=0.5, cbar_kws={'label': 'Tasa de paro (%)'})
    ax.set_title(f'Tasa de paro media por CCAA y trimestre ({period})')
    ax.set_xlabel('Trimestre')
    ax.set_ylabel('Comunidad Autonoma')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 7 — Tasa de paro por grupo de edad (from JSON table 65219)
# ---------------------------------------------------------------------------

def _parse_nombre_65219(nombre):
    """Parse serie name from table 65219 into sexo + edad."""
    lower = nombre.lower()
    if 'ambos sexos' in lower:
        sexo = 'Ambos sexos'
    elif 'hombres' in lower:
        sexo = 'Hombres'
    elif 'mujeres' in lower:
        sexo = 'Mujeres'
    else:
        return None
    edad = _parse_edad(lower)
    if edad is None:
        return None
    return {'sexo': sexo, 'edad': edad}


def plot_paro_por_edad(raw_dir, save_path=None):
    """Grouped bar chart of unemployment rate by age group and sex (latest quarter)."""
    raw_dir = Path(raw_dir)
    data = _json_to_df(_load_json(raw_dir / 'epa_tasas_paro_edad_raw.json'),
                       _parse_nombre_65219)
    if data.empty:
        return

    period = f"{int(data['anyo'].min())}–{int(data['anyo'].max())}"
    last_fecha = data['fecha'].max()
    latest = data[data['fecha'] == last_fecha].copy()

    # Order age groups logically
    age_order = sorted(latest['edad'].unique(),
                       key=lambda x: int(re.search(r'\d+', x).group()))
    latest['edad'] = pd.Categorical(latest['edad'], categories=age_order, ordered=True)
    latest = latest.sort_values('edad')

    fig, ax = plt.subplots(figsize=(14, 6))
    sexos = ['Ambos sexos', 'Hombres', 'Mujeres']
    colors = {'Ambos sexos': '#95a5a6', 'Hombres': '#3498db', 'Mujeres': '#e74c3c'}
    width = 0.25
    x = np.arange(len(age_order))

    for i, sexo in enumerate(sexos):
        sub = latest[latest['sexo'] == sexo].set_index('edad').reindex(age_order)
        ax.bar(x + i * width, sub['valor'].values, width, label=sexo,
               color=colors[sexo], alpha=0.85)

    trim_label = pd.Timestamp(last_fecha).to_period('Q')
    ax.set_xticks(x + width)
    ax.set_xticklabels(age_order, rotation=45, ha='right')
    ax.set_xlabel('Grupo de edad')
    ax.set_ylabel('Tasa de paro (%)')
    ax.set_title(f'Tasa de paro por grupo de edad y sexo — {trim_label} ({period})')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 8 — Evolucion del paro juvenil vs total (from JSON table 65219)
# ---------------------------------------------------------------------------

def plot_paro_juvenil_evolucion(raw_dir, save_path=None):
    """Line chart of youth unemployment (16-19, 20-24) vs total over time."""
    raw_dir = Path(raw_dir)
    data = _json_to_df(_load_json(raw_dir / 'epa_tasas_paro_edad_raw.json'),
                       _parse_nombre_65219)
    if data.empty:
        return

    period = f"{int(data['anyo'].min())}–{int(data['anyo'].max())}"
    ambos = data[data['sexo'] == 'Ambos sexos'].copy()

    groups = {
        '16 y más años': {'color': '#2c3e50', 'lw': 3},
        'De 16 a 19 años': {'color': '#e74c3c', 'lw': 2},
        'De 20 a 24 años': {'color': '#e67e22', 'lw': 2},
    }

    fig, ax = plt.subplots(figsize=(12, 6))
    for edad_label, style in groups.items():
        sub = ambos[ambos['edad'] == edad_label].sort_values('fecha')
        if sub.empty:
            continue
        ax.plot(sub['fecha'], sub['valor'], marker='o', markersize=4,
                label=edad_label, color=style['color'], linewidth=style['lw'])

    ax.set_xlabel('Fecha')
    ax.set_ylabel('Tasa de paro (%)')
    ax.set_title(f'Evolucion del paro juvenil vs total — Ambos sexos ({period})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 9 — Tasa de paro por edad y nacionalidad (from JSON tables 65086+65112)
# ---------------------------------------------------------------------------

def _parse_nombre_nac(nombre):
    """Parse serie name from tables 65086/65112 into sexo, edad, nacionalidad."""
    lower = nombre.lower()
    if 'ambos sexos' not in lower:
        return None  # Only use 'Ambos sexos' for this chart
    edad = _parse_edad(lower)
    if edad is None:
        return None
    # Extract nationality
    parts = [p.strip().rstrip('.') for p in nombre.split('. ')]
    # Nationality is typically the 5th field: Total, Española, Extranjera: Total, etc.
    nac = None
    for p in parts:
        pl = p.lower()
        if pl in ('total', 'personas'):
            continue
        if pl in ('española',):
            nac = 'Española'
        elif 'extranjera: total' in pl:
            nac = 'Extranjera'
        elif pl == 'doble nacionalidad':
            nac = 'Doble nacionalidad'
        elif 'extranjera' in pl:
            return None  # Skip sub-categories of foreign
    if nac is None:
        nac = 'Total'
    return {'sexo': 'Ambos sexos', 'edad': edad, 'nacionalidad': nac}


def plot_paro_edad_nacionalidad(raw_dir, save_path=None):
    """Grouped bar chart of unemployment rate by age and nationality."""
    raw_dir = Path(raw_dir)
    activos_json = _load_json(raw_dir / 'epa_activos_nacionalidad_edad_raw.json')
    ocupados_json = _load_json(raw_dir / 'epa_ocupados_nacionalidad_edad_raw.json')

    df_act = _json_to_df(activos_json, _parse_nombre_nac)
    df_ocu = _json_to_df(ocupados_json, _parse_nombre_nac)

    if df_act.empty or df_ocu.empty:
        return

    period = f"{int(df_act['anyo'].min())}–{int(df_act['anyo'].max())}"

    # Use latest quarter
    last_fecha = df_act['fecha'].max()
    act = df_act[df_act['fecha'] == last_fecha].copy()
    ocu = df_ocu[df_ocu['fecha'] == last_fecha].copy()

    # Merge and compute tasa_paro
    merged = act.merge(ocu, on=['sexo', 'edad', 'nacionalidad', 'fecha'],
                       suffixes=('_act', '_ocu'))
    merged['tasa_paro'] = ((merged['valor_act'] - merged['valor_ocu'])
                           / merged['valor_act'] * 100)

    # Filter to Española and Extranjera only
    merged = merged[merged['nacionalidad'].isin(['Española', 'Extranjera'])]
    if merged.empty:
        return

    age_order = sorted(merged['edad'].unique(),
                       key=lambda x: int(re.search(r'\d+', x).group()))
    merged['edad'] = pd.Categorical(merged['edad'], categories=age_order, ordered=True)
    merged = merged.sort_values('edad')

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = {'Española': '#3498db', 'Extranjera': '#e74c3c'}
    width = 0.35
    x = np.arange(len(age_order))

    for i, nac in enumerate(['Española', 'Extranjera']):
        sub = merged[merged['nacionalidad'] == nac].set_index('edad').reindex(age_order)
        vals = sub['tasa_paro'].values
        bars = ax.bar(x + i * width, vals, width, label=nac, color=colors[nac], alpha=0.85)
        for bar, v in zip(bars, vals):
            if not np.isnan(v):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                        f'{v:.1f}%', ha='center', va='bottom', fontsize=8)

    trim_label = pd.Timestamp(last_fecha).to_period('Q')
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(age_order, rotation=45, ha='right')
    ax.set_xlabel('Grupo de edad')
    ax.set_ylabel('Tasa de paro (%)')
    ax.set_title(f'Tasa de paro por edad y nacionalidad — {trim_label} ({period})')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def generate_all_charts(df, raw_dir, charts_dir):
    """Generate all 9 charts and save to charts_dir."""
    charts_dir = Path(charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = Path(raw_dir)

    charts = [
        ("01_tasa_paro_por_provincia.png",
         lambda p: plot_paro_por_provincia(df, save_path=p)),
        ("02_brecha_genero_paro.png",
         lambda p: plot_brecha_genero(df, save_path=p)),
        ("03_empleo_por_sector.png",
         lambda p: plot_empleo_por_sector(df, save_path=p)),
        ("04_distribucion_ocupados.png",
         lambda p: plot_distribucion_ocupados(df, save_path=p)),
        ("05_evolucion_empleo_total.png",
         lambda p: plot_evolucion_empleo_total(df, save_path=p)),
        ("06_heatmap_paro_ccaa.png",
         lambda p: plot_heatmap_paro_ccaa(df, save_path=p)),
        ("07_paro_por_edad.png",
         lambda p: plot_paro_por_edad(raw_dir, save_path=p)),
        ("08_paro_juvenil_evolucion.png",
         lambda p: plot_paro_juvenil_evolucion(raw_dir, save_path=p)),
        ("09_paro_edad_nacionalidad.png",
         lambda p: plot_paro_edad_nacionalidad(raw_dir, save_path=p)),
    ]

    for filename, plot_fn in charts:
        path = charts_dir / filename
        try:
            plot_fn(path)
            print(f"  -> {filename}")
        except Exception as exc:
            print(f"  !! {filename} fallo: {exc}")
