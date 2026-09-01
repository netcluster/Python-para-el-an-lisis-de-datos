"""
pipeline.py - Script ETL ejecutable desde terminal

Uso:
    python pipeline.py
    python pipeline.py --fecha 2024-02-15
    python pipeline.py --input "lo que sea" --output "lo que sea" --fecha 2024-02-15
    
Registra el flujo en: logs/pipeline_etl.log
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# 1. Ruta base del proyecto (donde reside pipeline.py)
BASE_DIR = Path(__file__).resolve().parent

# 2. Agregar carpeta 'src' al path
src_path = BASE_DIR / "src"
sys.path.insert(0, str(src_path))

try:
    from utils import cargar_multiples_csv, limpiar_espacios, configurar_logging
except ImportError as e:
    raise ImportError(f"No se pudo importar desde 'src/utils.py': {e}")


# ==================================================================
# FUNCIÓN PRINCIPAL DEL PIPELINE
# ==================================================================

def ejecutar_pipeline(fecha_procesamiento=None, input_val="data/raw", output_val="data/processed"):
    """Ejecuta el pipeline ETL completo.
    
    Args:
        fecha_procesamiento (str): Fecha de corte (YYYY-MM-DD).
        input_val (any): Parámetro o contenido de entrada.
        output_val (any): Parámetro o contenido de salida.
    """
    if not fecha_procesamiento:
        fecha_procesamiento = datetime.now().strftime('%Y-%m-%d')

    # Carpetas físicas fijas del proyecto
    dir_raw = BASE_DIR / "data" / "raw"
    dir_processed = BASE_DIR / "data" / "processed"
    dir_logs = BASE_DIR / "logs"

    # Asegurar que existan las carpetas de salida y logs
    dir_processed.mkdir(parents=True, exist_ok=True)
    dir_logs.mkdir(parents=True, exist_ok=True)

    # Configurar logging
    logger = configurar_logging(str(dir_logs / "pipeline_etl.log"))
    logger.info(f"INICIANDO PIPELINE ETL - Fecha: {fecha_procesamiento} | Input: {input_val} | Output: {output_val}")

    # ETAPA 1: EXTRACT (Extracción de datos) ------------------------
    try:
        logger.info(f"Cargando archivos CSV desde: {dir_raw}")
        df_ventas_py = cargar_multiples_csv(str(dir_raw), patron="*.csv")
        
        archivo_productos = dir_raw / "Productos.xlsx"
        if not archivo_productos.exists():
            raise FileNotFoundError(f"No se encontró el archivo 'Productos.xlsx' en: {archivo_productos}")
        
        df_productos = pd.read_excel(archivo_productos)

        # Consumir API de tipo de cambio
        logger.info("Consultando API de tipo de cambio...")
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        datos = response.json()

        # Convertir a DataFrame
        df_cambios = pd.Series(datos['rates']).to_frame().reset_index()
        df_cambios.columns = ['moneda', 'tasa']
        df_cambios['fecha_consulta'] = fecha_procesamiento

    except Exception as e:
        logger.error(f"Error en la etapa de EXTRACT: {e}")
        raise

    # ETAPA 2: TRANSFORM (Transformación de datos) -------------------
    try:
        logger.info("Transformando datos...")
        df_ventas_py = limpiar_espacios(df_ventas_py)
        df_combinado = pd.merge(df_ventas_py, df_productos, on='producto', how='left')
    except Exception as e:
        logger.error(f"Error en la etapa de TRANSFORM: {e}")
        raise

    # ETAPA 3: LOAD (Carga de datos) ---------------------------------
    try:
        ruta_tasas = dir_processed / "tasas_cambio.csv"
        ruta_combinadas = dir_processed / "ventas_combinadas.csv"

        logger.info(f"Guardando resultados en: {dir_processed}")
        df_cambios.to_csv(ruta_tasas, index=False)
        df_combinado.to_csv(ruta_combinadas, index=False)

    except Exception as e:
        logger.error(f"Error en la etapa de LOAD: {e}")
        raise

    logger.info("PIPELINE ETL FINALIZADO CON ÉXITO")
    print("\n✓ Pipeline ejecutado correctamente")
    print(f"  - Fecha de proceso : {fecha_procesamiento}")
    print(f"  - Input recibido   : {input_val}")
    print(f"  - Output recibido  : {output_val}")


# ==================================================================
# FUNCIÓN main y configuración de argumentos en línea de comandos
# ==================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Pipeline ETL de unidad 4'
    )
    # Parametrización
    parser.add_argument(
        '--fecha',
        type=str,
        default=None,
        help='Fecha de procesamiento (YYYY-MM-DD). Por defecto: hoy'
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw",
        help="Contenido o valor de entrada"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed",
        help="Contenido o valor de salida"
    )

    args = parser.parse_args()  # Con paréntesis ()

    # Ejecutar pipeline pasando los argumentos recibidos
    ejecutar_pipeline(
        fecha_procesamiento=args.fecha,
        input_val=args.input,
        output_val=args.output
    )


if __name__ == '__main__':
    main()