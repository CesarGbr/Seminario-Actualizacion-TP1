# Trabajo Practico 1 - Seminario de Actualizacion
# Price Manager - Star Computacion

Aplicacion de consola (CLI) en Python para gestionar inventario, precios, stock y cotizaciones de dolar para un local de hardware.

## Estado del proyecto

- Sprint actual: Sprint 2.
- Persistencia principal: base de datos SQLite mediante SQLAlchemy.
- Integracion online: cotizaciones desde API configurable por `.env`.

## Funcionalidades principales

- CRUD de productos, precios, categorias y proveedores.
- Gestion de stock.
- Gestion de cotizaciones:
  - alta/actualizacion manual,
  - actualizacion en tiempo real,
  - carga masiva desde API.
- Recotizacion de productos segun tipo de dolar.
- Vista bimonetaria (ARS/USD).
- Exportacion de precios a CSV por tipo de cotizacion.
- Comparacion de precios con competencia web.

## Estructura relevante

- `src/price_manager/main.py`: punto de entrada.
- `src/price_manager/database/connection.py`: conexion y transacciones SQLAlchemy.
- `src/price_manager/models/models.py`: modelos ORM.
- `src/price_manager/repositories/repositories.py`: acceso a datos.
- `src/price_manager/services/services.py`: logica de negocio e integraciones.
- `src/price_manager/ui/console.py`: interfaz CLI.
- `src/price_manager/migrations/migrations.py`: migracion CSV -> DB y generacion SQL.

## Requisitos

- Python 3.10 o superior.
- Dependencias de `requirements.txt`:
  - `SQLAlchemy`
  - `python-dotenv`

## Instalacion

1. Crear entorno virtual (opcional pero recomendado):
   - Windows (PowerShell):
     ```bash
     python -m venv .venv
     .\\.venv\\Scripts\\Activate.ps1
     ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuracion

Crear archivo `.env` en la raiz del proyecto con:

```env
API_URL=https://dolarapi.com/v1/dolares
```

`API_URL` es obligatoria para funciones de cotizacion online.  
Si falta, la app informa el error en la interfaz y solo se bloquean esas funciones.

## Ejecucion

Desde la raiz del repo:

```bash
python src/price_manager/main.py
```

Al iniciar, `main.py` ejecuta migracion inicial de CSV a base de datos y luego abre la consola interactiva.

## Datos y archivos generados

- Base SQLite: `price_manager.db`.
- SQL de migracion: `src/price_manager/migrations/sql/*.sql` (generados automaticamente).
- CSV de exportacion: `src/price_manager/migrations/csv/export_precios/*.csv`.

## Integrantes

- Gonzalez, Rodrigo
- Miranda, Facundo
- Golin, Lucia
- Berti, Juan Ignacio
- Guaimas Rosado, Cesar Gabriel

## Historial de cambios

Ver `CHANGELOG.md` para el detalle por sprint y por dia.
