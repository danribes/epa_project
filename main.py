import argparse
from datetime import datetime

from src.config import ROOT, DATA_RAW, DATA_PROCESSED, CHARTS_DIR, RAW_PATH, OUT_PATH
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

    # Clean previous outputs before starting
    for d in (DATA_PROCESSED, CHARTS_DIR):
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    f.unlink()
    print("Limpiados datos procesados y graficos anteriores.")

    if args.fetch:
        from fetch_data import fetch_all
        start = args.start or (datetime.now().year - 5)
        end = args.end or datetime.now().year
        fetch_all(start, end, DATA_RAW)
        print()

    print(f"Cargando datos desde {RAW_PATH} ...")
    df = load_csv(RAW_PATH)
    print(f"  Shape raw: {df.shape}")

    print("Limpiando datos ...")
    df = clean(df)
    print(f"  Shape clean: {df.shape}")
    validate_clean(df)

    print("Generando features ...")
    df = build_features(df)
    print(f"  Shape final: {df.shape}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Guardado en {OUT_PATH}")

    print("\nGenerando graficos ...")
    generate_all_charts(df, DATA_RAW, CHARTS_DIR)
    print("Graficos guardados en charts/")


if __name__ == "__main__":
    main()
