"""
pipeline.py - Script ETL ejecutable desde terminal para Retail Andino

Uso:
    python pipeline.py                                     # Parámetros por defecto
    python pipeline.py --fecha 2024-03-01                  # Fecha específica
    python pipeline.py --input data/raw --output data/processed
    
Registra el flujo en: logs/pipeline_etl.log
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# 1. Definir ruta base del proyecto (proyecto_etl)
BASE_DIR = Path(__file__).resolve().parent

# 2. Agregar carpeta 'src' para importar módulos auxiliares
sys.path.insert(0, str(BASE_DIR / "src"))
from utils import cargar_multiples_csv, limpiar_espacios, configurar_logging


# ==================================================================
# FUNCIÓN PRINCIPAL DEL PIPELINE
# ==================================================================

def ejecutar_pipeline(fecha_procesamiento=None, input_dir="data/raw", output_dir="data/processed"):
    """Ejecuta el pipeline ETL completo: Extract, Transform, Load."""

    # Si no se indica fecha, toma la fecha de hoy
    if not fecha_procesamiento:
        fecha_procesamiento = datetime.now().strftime("%Y-%m-%d")

    # Rutas absolutas a partir de BASE_DIR
    input_path = BASE_DIR / input_dir
    output_path = BASE_DIR / output_dir
    carpeta_logs = BASE_DIR / "logs"

    # Crear carpeta de salida si no existe
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    # Iniciar Logging (usa la carpeta logs existente o la crea)
    logger = configurar_logging("pipeline_etl.log", carpeta_logs=carpeta_logs)
    logger.info("=" * 60)
    logger.info(f"INICIANDO PIPELINE ETL - RETAIL ANDINO (Fecha: {fecha_procesamiento})")

    # --------------------------------------------------------------
    # ETAPA 1: EXTRACT (Extracción de datos)
    # --------------------------------------------------------------
    try:
        logger.info(f"Extrayendo archivos CSV de ventas desde: {input_path}")
        df_ventas = cargar_multiples_csv(input_path, patron="ventas_*.csv")

        logger.info("Extrayendo catálogo de productos en Excel...")
        ruta_catalogo = input_path / "productos_retail_andino.xlsx"
        
        # Validación de existencia del archivo Excel
        if not ruta_catalogo.exists():
            raise FileNotFoundError(f"No se encontró el archivo de productos en: {ruta_catalogo}")
        
        df_productos = pd.read_excel(ruta_catalogo)

        logger.info("Consultando API de tipo de cambio USD...")
        url_api = "https://open.er-api.com/v6/latest/USD"
        respuesta = requests.get(url_api, timeout=10)
        respuesta.raise_for_status()
        datos_api = respuesta.json()

        # Convertir tasas de la API a DataFrame
        df_cambios = pd.Series(datos_api["rates"]).to_frame().reset_index()
        df_cambios.columns = ["moneda", "tasa"]
        df_cambios["fecha_consulta"] = fecha_procesamiento

    except Exception as e:
        logger.error(f"Error en la etapa de EXTRACT: {e}")
        raise

    # --------------------------------------------------------------
    # ETAPA 2: TRANSFORM (Transformación y Limpieza)
    # --------------------------------------------------------------
    try:
        logger.info("Limpiando espacios en blanco en datos de ventas y catálogo...")
        df_ventas = limpiar_espacios(df_ventas)
        df_productos = limpiar_espacios(df_productos)

        logger.info("Combinando ventas con catálogo de productos...")
        # Unión por columna común 'producto'
        df_combinado = pd.merge(df_ventas, df_productos, on="producto", how="left")

    except Exception as e:
        logger.error(f"Error en la etapa de TRANSFORM: {e}")
        raise

    # --------------------------------------------------------------
    # ETAPA 3: LOAD (Carga y Guardado)
    # --------------------------------------------------------------
    try:
        ruta_salida_ventas = output_path / "ventas_retail_andino_combinadas.csv"
        ruta_salida_tasas = output_path / "tasas_cambio.csv"

        logger.info(f"Guardando ventas combinadas en: {ruta_salida_ventas}")
        df_combinado.to_csv(ruta_salida_ventas, index=False)

        logger.info(f"Guardando tasas de cambio en: {ruta_salida_tasas}")
        df_cambios.to_csv(ruta_salida_tasas, index=False)

    except Exception as e:
        logger.error(f"Error en la etapa de LOAD: {e}")
        raise

    logger.info("PIPELINE ETL FINALIZADO CON ÉXITO")
    print("\n✓ Pipeline ejecutado correctamente para Retail Andino")
    print(f"  - Fecha de corte : {fecha_procesamiento}")
    print(f"  - Entrada        : {input_path}")
    print(f"  - Salida         : {output_path}")
    print(f"  - Registro Log   : {carpeta_logs / 'pipeline_etl.log'}")


# ==================================================================
# FUNCIÓN main Y CONFIGURACIÓN DE ARGUMENTOS POR TERMINAL
# ==================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline ETL Automatizado - Retail Andino (DataMarket Insights)"
    )
    parser.add_argument(
        "--fecha",
        type=str,
        default=None,
        help="Fecha de procesamiento (formato YYYY-MM-DD). Por defecto: hoy"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw",
        help="Carpeta de entrada (por defecto: data/raw)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed",
        help="Carpeta de salida (por defecto: data/processed)"
    )

    args = parser.parse_args()

    # Ejecutar pipeline
    ejecutar_pipeline(
        fecha_procesamiento=args.fecha,
        input_dir=args.input,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()