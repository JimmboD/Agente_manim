"""Paquete de dominio del editor de escenas.

Contiene la capa independiente de HTTP: configuración, seguridad, proyectos,
workspace, plantillas multiarchivo, construcción de contexto, proveedores LLM y
asistente de código. No hay representación intermedia: el buffer del editor es
la fuente de verdad.
"""

__all__ = [
    "config",
    "security",
    "projects",
    "workspace",
    "context",
    "template_bundles",
    "http",
    "llm",
    "prompts",
    "code_assistant",
    "workspace_api",
]
