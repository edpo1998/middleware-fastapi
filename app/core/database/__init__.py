"""
Centraliza el MetaData y registra TODAS las tablas.
⚠️ No crees engine ni sesiones aquí (evita efectos colaterales y ciclos).
"""

from sqlmodel import SQLModel
from .db_metadata import metadata  # Base usa el mismo metadata

# 1) Unificar el MetaData de SQLModel ANTES de importar modelos
SQLModel.metadata = metadata

# 2) Importar paquetes de modelos para registrar todas las tablas
#    (cada paquete models/__init__.py debe importar sus módulos internos)
from .mcs_scheme import models as models_mcs # noqa: F401
from .bootstrap_app_scheme import models as models_bootstap_app # noqa: F401



# 3) Re-exportar utilidades
__all__ = ["metadata"]
