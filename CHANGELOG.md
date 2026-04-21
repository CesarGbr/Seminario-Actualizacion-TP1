# 📜 CHANGELOG

Todas las modificaciones relevantes de este proyecto se documentan aquí

---

## [Sprint 1] - Día 1

### Agregado
- Creación del repositorio del proyecto.
- Configuración inicial del entorno en Google Colab.
- Vinculación con GitHub mediante token.
- Creación del archivo README.md.
- Creación del archivo CHANGELOG.md.

### Detalles
- Se definió el objetivo del proyecto.
- Se documentó el contexto del problema.
- Se listaron las entidades principales del sistema.

---

## [Sprint 1] - Día 2

### 📌 Agregado
- Creación de la estructura del proyecto bajo el directorio `src/price_manager`.
- Implementación inicial de los módulos:
  - `entities.py`
  - `repositories.py`
  - `services.py`
  - `preload_data.py`
  - `console.py`
  - `main.py`
- Integración del uso de `%%writefile` para la generación de archivos `.py` desde el notebook.
- Configuración del entorno de ejecución mediante `PYTHONPATH`.

### 🔧 Cambios
- Ajuste de rutas del proyecto para adaptarlas al entorno de Google Colab.
- Migración del enfoque manual de creación de archivos a generación dinámica desde el notebook.
- Reorganización del flujo de ejecución del notebook (setup → git → estructura → módulos).

### 🐛 Correcciones
- Resolución de conflicto entre ramas `main` y `master`.
- Corrección de rutas incorrectas (`/content/price_manager` → `/content/Seminario-Actualizacion-TP1`).
- Corrección en la configuración de Git para evitar exposición del token.
- Desactivación controlada del `git push` mediante la variable `desactivar_git_push`.

### 📎 Detalles
- Se estableció una arquitectura modular basada en separación de responsabilidades.
- Se alineó la implementación con los lineamientos de la cátedra (uso de `.py` en lugar de notebook).

---

## [Sprint 1] - Día 3
