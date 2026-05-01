# Contributing to Abelito OS

## Desarrollo local

1. Crear entorno virtual e instalar dependencias:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Ejecutar checks básicos:

```bash
python -m pytest -q
```

## Cómo agregar una habilidad/capacidad

1. Crear módulo en `apps/` o `skills/` según corresponda.
2. Documentar propósito, entradas/salidas y dependencias.
3. Incluir fallback cuando falten ejecutables externos opcionales.
4. Agregar tests unitarios y, si aplica, tests de integración.

## Estilo

- Mantener cambios pequeños y atómicos.
- No introducir dependencias sin justificación.
- Validar rutas de error además de ruta feliz.

## Pull Requests

- Describir claramente el problema y la solución.
- Referenciar archivos tocados y evidencias de pruebas ejecutadas.
