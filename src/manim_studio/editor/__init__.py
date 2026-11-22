"""Paquete de dominio del editor de escenas.

Contiene la capa independiente de HTTP: configuración, seguridad, IR,
persistencia SQLite, generación de código, jobs de render y proveedores LLM.
"""

__all__ = [
    "config",
    "security",
    "db",
    "ir",
    "codegen",
    "jobs",
    "llm",
]
