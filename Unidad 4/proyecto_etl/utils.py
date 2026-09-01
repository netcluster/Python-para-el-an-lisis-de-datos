"""
utils.py - Funciones auxiliares para el proceso ETL de DataMarket Insights
"""

import glob
import logging
from pathlib import Path
import pandas as pd


def configurar_logging(nombre_archivo="pipeline_etl.log", carpeta_logs=None):
    """Configura el registro de eventos: usa la carpeta logs si existe, y si no, la crea."""
    if carpeta_logs is None:
        base = Path(__file__).resolve().parent
        # Si utils.py está en 'src', la raíz es la carpeta padre
        if base.name == "src":
            base = base.parent
        carpeta_logs = base / "logs"
    else:
        carpeta_logs = Path(carpeta_logs)

    # Si la carpeta logs no existe, la crea; si ya existe, la utiliza
    if not carpeta_logs.exists():
        carpeta_logs.mkdir(parents=True, exist_ok=True)

    ruta_log = carpeta_logs / nombre_archivo

    # Configurar el formato del logging (tanto a archivo como a consola)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(ruta_log, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("ETL_Retail_Andino")


def cargar_multiples_csv(directorio, patron="*.csv"):
    """Carga y concatena todos los archivos CSV que coincidan con el patrón en una sola tabla."""
    ruta_busqueda = Path(directorio) / patron
    archivos = glob.glob(str(ruta_busqueda))

    if not archivos:
        raise FileNotFoundError(f"No se encontraron archivos con el patrón '{patron}' en: {directorio}")

    lista_df = [pd.read_csv(archivo) for archivo in archivos]
    df_consolidado = pd.concat(lista_df, ignore_index=True)
    return df_consolidado


def limpiar_espacios(df):
    """Elimina espacios en blanco al inicio y final de todas las columnas de texto."""
    df_limpio = df.copy()
    for columna in df_limpio.select_dtypes(include="object").columns:
        df_limpio[columna] = df_limpio[columna].astype(str).str.strip()
    return df_limpio