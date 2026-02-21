import argparse
from datetime import datetime
from pathlib import Path

from src.io import load_csv
from src.cleaning import clean
from src.features import build_features
from src.utils import validate_clean
from src.viz import generate_all_charts


def main():
    parser = argparse.ArgumentParser(
        description="EPA pipeline: descarga (opcional) + limpieza + features")
    parser.add_argument("--fetch", action="store_true",
                        help="Descargar datos del INE antes de procesar")
    parser.add_argument("-s", "--start", type=int, default=None,
                        help="Año de inicio (requiere --fetch)")
    parser.add_argument("-e", "--end", type=int, default=None,
                        help="Año de fin (requiere --fetch)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent

    # Clean previous outputs before starting
    for d in (root / "data" / "processed", root / "charts"):
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    f.unlink()
    print("Limpiados datos procesados y graficos anteriores.")

    if args.fetch:
        from fetch_data import fetch_all
        start = args.start or (datetime.now().year - 5)
        end = args.end or datetime.now().year
        fetch_all(start, end, root / "data" / "raw")
        print()

    raw_path = root / "data" / "raw" / "epa_mercado_laboral_dirty.csv"
    out_path = root / "data" / "processed" / "epa_mercado_laboral_clean.csv"

    print(f"Cargando datos desde {raw_path} ...")
    df = load_csv(raw_path)
    print(f"  Shape raw: {df.shape}")

    print("Limpiando datos ...")
    df = clean(df)
    print(f"  Shape clean: {df.shape}")
    validate_clean(df)

    print("Generando features ...")
    df = build_features(df)
    print(f"  Shape final: {df.shape}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Guardado en {out_path}")

    print("\nGenerando graficos ...")
    raw_dir = root / "data" / "raw"
    charts_dir = root / "charts"
    generate_all_charts(df, raw_dir, charts_dir)
    print("Graficos guardados en charts/")


if __name__ == "__main__":
    main()
