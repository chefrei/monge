import os

# --- Directorios ---
DATA_DIR = 'data'
CONFIG_DIR = 'config'

# --- Archivos ---
ARCHIVO_INVENTARIO = os.path.join(DATA_DIR, "inventario.csv")
ARCHIVO_VENTAS = os.path.join(DATA_DIR, "ventas.csv")
ARCHIVO_CIERRES = os.path.join(DATA_DIR, "cierres.csv")
ARCHIVO_CONFIG = os.path.join(CONFIG_DIR, "settings.json")
ARCHIVO_SECUENCIA = os.path.join(CONFIG_DIR, "sequence.json")
ARCHIVO_CLIENTES = os.path.join(DATA_DIR, "clientes.csv")
DIR_FACTURAS_PDF = os.path.join(DATA_DIR, "facturas_pdf")

# --- Categorías por Defecto ---
DEFAULT_CATEGORIAS = {
    "Comidas": {
        "Cachapa sola": 1.0,
        "Queso de mano 3$": 3.0,
        "Queso de mano 5$": 5.0,
        "Cochino": 1.5,
        "Carne": 2.0,
        "Chorizo": 1.5,
    },
    "Contornos": {
        "Ensalada": 1.5,
        "Yuca": 1.5,
        "Salsas": 1.5
    },
    "Bebidas": {
        "Refresco": 1.5,
        "Malta": 2.0,
        "Jugo": 2.0,
        "Frappé": 3.0
    }
}
