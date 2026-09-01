import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path
import logging

# ============================================================================
# FUNCIÓN DE CARGA
# ============================================================================

def cargar_multiples_csv(directorio, patron='*.csv'):
    """
    Carga múltiples archivos CSV desde un directorio.
    
    Args:
        directorio (str): Ruta del directorio
        patron (str): Patrón de búsqueda (ej: 'ventas_*.csv')
        
    Returns:
        pd.DataFrame: Datos consolidados de todos los archivos
    """    
    archivos = glob.glob(os.path.join(directorio, patron))
    
    if not archivos:
        raise FileNotFoundError(f"No se encontraron archivos con patrón: {patron}")
    
    dfs = []
    for archivo in sorted(archivos):
        df = pd.read_csv(archivo)
        dfs.append(df)
    
    return pd.concat(dfs, ignore_index=True)


# ============================================================================
# FUNCIÓN DE TRANSFORMACIÓN
# ============================================================================

def limpiar_espacios(df):
    """
    Elimina espacios en blanco al inicio y final de columnas texto.
    
    Args:
        df (pd.DataFrame): DataFrame a limpiar
        
    Returns:
        pd.DataFrame: DataFrame limpio
    """
    df_limpio = df.copy()
    
    # Aplicar a columnas de tipo object (texto)
    for col in df_limpio.select_dtypes(include='object').columns:
        df_limpio[col] = df_limpio[col].str.strip()
    
    return df_limpio

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

def configurar_logging(nombre_archivo="pipeline.log"):
    """
    Configura el logging para registrar el flujo del pipeline.
    
    Args:
        nombre_archivo (str): Ruta del archivo de log
        
    Returns:
        logging.Logger: Logger configurado
    """ 
    
    base_dir = Path(__file__).resolve().parent.parent

    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_path = logs_dir / nombre_archivo

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Evitar duplicados
    for h in logger.handlers[:]:
        h.close()
        logger.removeHandler(h)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger