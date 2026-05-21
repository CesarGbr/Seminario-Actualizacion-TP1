# CHANGELOG

Todas las modificaciones relevantes de este proyecto se documentan aqui.

---

## [Sprint 1] - Dia 1

### Agregado
- Creacion del repositorio del proyecto.
- Configuracion inicial del entorno en Google Colab.
- Vinculacion con GitHub mediante token.
- Creacion de `README.md` y `CHANGELOG.md`.

### Detalles
- Se definio el objetivo del proyecto.
- Se documento el contexto del problema.
- Se listaron las entidades principales del sistema.

---

## [Sprint 1] - Dia 2

### Agregado
- Creacion de la estructura base en `src/price_manager`.
- Implementacion inicial de:
  - `entities.py`
  - `repositories.py`
  - `services.py`
  - `preload_data.py`
  - `console.py`
  - `main.py`

### Cambios
- Ajuste de rutas para ejecucion en Colab.
- Organizacion del flujo del notebook (setup, git, estructura, modulos).
- Uso de `PYTHONPATH` para resolver imports en ejecucion.

### Correcciones
- Resolucion de conflicto entre ramas `main` y `master`.
- Correccion de rutas de trabajo del repositorio.
- Mejora de configuracion de Git para evitar exponer token.

---

## [Sprint 1] - Dia 3

### Cambios
- Incorporacion del parametro `import_default_data` en `main()` para controlar carga inicial de datos.
- Ajustes en `main.py` para mantener ejecucion estable en entorno local/notebook.

### Correcciones
- Solucion de error por argumento inesperado en `main(import_default_data=True)`.
- Validacion del flujo de inicio sin bloquear en consola durante pruebas.

---

## [Sprint 1] - Dia 4

### Agregado
- Incorporacion de entidades requeridas por la bateria de tests del notebook:
  - `Moneda`
  - `TipoCotizacion`
- Incorporacion de repositorios:
  - `RepositorioMoneda`
  - `RepositorioTipoCotizacion`
- Incorporacion de servicios:
  - `ServicioMoneda`
  - `ServicioTipoCotizacion`

### Cambios
- Ajustes en `Precio` y `CotizacionDolar` para trabajar con los objetos del dominio usados en tests.
- Normalizacion de tipos de cotizacion para soportar variantes de texto (ejemplo: "Dolar Blue").

---

## [Sprint 1] - Dia 5

### Cambios
- Ajustes en `ServicioProducto` para exponer `obtener(id)` con validacion por excepcion.
- Ajustes en `ServicioStock` para exponer:
  - `registrar_movimiento(producto_id, delta)`
  - `obtener_stock(producto_id)`
- Ajustes en `ServicioCotizacionDolar` para exponer:
  - `registrar_cotizacion(cotizacion)`
  - `obtener_historico(tipo_cotizacion_id)`

### Correcciones
- Correccion de consulta de historico por tipo para alinear nombre de tipo vs tipo normalizado en repositorio.
- Correccion de errores por encoding en nombres de cotizacion provenientes de notebook/CSV.

---

## [Sprint 1] - Dia 6

### Cambios
- Actualizacion de `preload_data.py` para usar argumentos nombrados y constructores vigentes.
- Actualizacion de `console.py` para crear `Precio` con argumentos nombrados.
- Unificacion de imports internos del paquete en modulo `src.price_manager.*`.

### Correcciones
- Resolucion de `ModuleNotFoundError` por mezcla de esquemas de import.
- Verificacion de compilacion de modulos con `compileall`.

---

## [Sprint 1] - Dia 7

### Validacion final
- Ejecucion de script de verificacion equivalente a la celda de test unitario del notebook.
- Confirmacion de funcionamiento de CRUD principal, stock y cotizaciones historicas.
- Confirmacion de integracion de carga inicial (`import_default_data=True`) sin romper el arranque.

### Estado
- El proyecto queda alineado con los requerimientos de evaluacion sobre la celda de tests.
- Notebook sin cambios estructurales obligatorios.

---

## [Sprint 1] - Dia 8

### Agregado
- Integracion de cotizacion dolar en tiempo real en `services.py`.
- Integracion de comparacion con competencia web (`books.toscrape.com`) mediante `ServicioCompetenciaWeb`.

### Cambios
- Refuerzo de `_fetch_dolar_rate` con headers HTTP y fallback por endpoint especifico (`/v1/dolares/{tipo}`).
- Incorporacion de calculo de confianza de match en comparacion de productos.
- Incorporacion de sugerencias en casos de busqueda ambigua contra competencia.

### Correcciones
- Correccion de colision de IDs en `CotizacionDolar` y `Precio` al combinar carga con ID manual + altas automaticas.
- Mejoras de tolerancia de red y mensajes de integracion para escenarios sin conectividad.

---

## [Sprint 1] - Dia 9

### Cambios
- Rediseño de UX de `console.py`:
  - seleccion guiada de producto,
  - flujo de vuelta (`b`) en pasos intermedios,
  - mensajes de error mas claros para cliente.
- Busqueda aproximada en nombres de productos (fuzzy) con sugerencias y confirmacion.
- Seleccion por indice cuando hay multiples productos similares.

### Agregado
- Submenu contextual al buscar producto:
  - actualizar precio,
  - comparar con competencia,
  - eliminar producto.
- Visualizacion dual de precios (ARS/USD) usando cotizacion Oficial de referencia.

### Correcciones
- Limpieza de textos y menu para mayor coherencia funcional.

---

## [Sprint 1] - Dia 10

### Agregado
- Alta de producto desde CLI (`Crear producto`) con flujo completo:
  - seleccionar o crear categoria,
  - seleccionar o crear proveedor,
  - crear precio y producto asociados.
- Bajas desde CLI:
  - producto,
  - categoria,
  - proveedor (con validacion de uso por productos).
- Gestion de cotizaciones desde CLI:
  - listar,
  - actualizar manual,
  - eliminar.

### Cambios
- Reorganizacion del menu principal:
  - `Gestion de catalogos`,
  - `Gestion de cotizaciones`.

### Correcciones
- Bloqueo de eliminacion de categoria/proveedor cuando existen productos asociados.
- Eliminacion de stock asociado al borrar producto.

---

## [Sprint 1] - Dia 11

### Agregado
- Persistencia de salida a CSV en `preload_data.py` mediante `guardar_datos(...)`.
- Escritura de estado completo al salir de la app (`main.py`, bloque `finally`).

### Cambios
- Serializacion de entidades a:
  - `categorias.csv`
  - `proveedores.csv`
  - `cotizaciones.csv`
  - `precios.csv`
  - `productos.csv`
  - `stock.csv`

### Validacion
- Compilacion general de modulos actualizados.
- Prueba de escritura de CSV en carpeta de prueba del workspace.
- Verificacion de flujo completo CLI + persistencia de cambios.

---

## [Sprint 2] - Dia 1

### Agregado
- Nuevo modulo `src/price_manager/database/connection.py`.
- Clase `ConexionDB` con:
  - inicializacion de `engine` SQLAlchemy,
  - factory de sesiones (`sessionmaker`),
  - validacion de conexion (`SELECT 1`),
  - cierre de recursos del engine.
- Context manager de transacciones (`transaccion`) con `commit/rollback/close` automatico.

### Cambios
- Preparacion de la base del proyecto para pasar de persistencia en memoria/CSV a base de datos relacional.

---

## [Sprint 2] - Dia 2

### Agregado
- Nuevo modulo `src/price_manager/models/models.py` con modelos ORM:
  - `CategoriaModel`
  - `ProveedorModel`
  - `MonedaModel`
  - `TipoCotizacionModel`
  - `PrecioModel`
  - `CotizacionDolarModel`
  - `ProductoModel`
  - `StockModel`
- Definicion de relaciones y restricciones de integridad (FK, unique y checks).
- Funcion `crear_tablas(engine)` para crear estructura fisica en DB.

### Cambios
- Alineacion de tipos/campos para soportar el dominio existente y relaciones entre entidades.

---

## [Sprint 2] - Dia 3

### Agregado
- Nuevo modulo `src/price_manager/migrations/migrations.py`.
- Implementacion de `migrar_datos(carpeta_csvs, carpeta_sqls)` para:
  - leer CSV del TP1,
  - poblar tablas en la base de datos en orden de dependencias,
  - generar archivos `.sql` de insercion por tabla.
- Generacion de SQL en `src/price_manager/migrations/sql/`:
  - `categorias.sql`
  - `proveedores.sql`
  - `monedas.sql`
  - `tipos_cotizacion.sql`
  - `precios.sql`
  - `cotizaciones_dolar.sql`
  - `productos.sql`
  - `stock.sql`

### Correcciones
- Soporte de re-ejecucion de migracion con limpieza controlada de datos previos.
- Cierre explicito de conexiones al finalizar la migracion.

---

## [Sprint 2] - Dia 4

### Cambios
- Refactor completo de `src/price_manager/repositories/repositories.py` para usar SQLAlchemy en lugar de estructuras en memoria.
- Mantencion de la interfaz de repositorios usada por servicios/UI para evitar romper contratos.
- Mapeo bidireccional entre modelos ORM y entidades de dominio.
- Carga de relaciones (`producto/precio/categoria/proveedor`, `stock/producto`) en lecturas.

### Correcciones
- Manejo de errores de integridad de base de datos con mensajes de validacion de dominio.
- Validaciones de unicidad funcional (ejemplo: stock por producto y cotizacion por tipo+fecha).

---

## [Sprint 2] - Dia 5

### Cambios
- Actualizacion de `src/price_manager/main.py` para flujo 100% base de datos.
- Reemplazo de carga/guardado por CSV por migracion inicial:
  - `migrar_datos(...)` cuando `import_default_data=True`.
- Eliminacion de persistencia final a CSV al cerrar la aplicacion.

### Agregado
- Integracion operativa de migracion + repositorios DB como flujo principal de arranque.

---

## [Sprint 2] - Dia 6

### Agregado
- Archivo `.env` con `API_URL=https://dolarapi.com/v1/dolares`.
- Integracion de `python-dotenv` para configuracion por entorno.
- Nueva funcion `obtener_cotizaciones()` en `ServicioCotizacionDolar` para:
  - consultar API de dolar,
  - parsear datos/fechas,
  - registrar o actualizar cotizaciones en DB.

### Cambios
- Ajuste de `_fetch_dolar_rate` para usar `API_URL` configurable.
- Ajuste de `actualizar_cotizacion_tiempo_real` para crear o actualizar cotizacion diaria sin conflictos de ID.
- Actualizacion de `requirements.txt` con:
  - `SQLAlchemy`
  - `python-dotenv`

---

## [Sprint 2] - Dia 7

### Agregado
- Nuevas opciones en `src/price_manager/ui/console.py`:
  - obtener cotizaciones por API,
  - ver lista de precios bimonetaria en ARS/USD segun tipo de cotizacion seleccionado,
  - exportar precios a CSV para todos los tipos de cotizacion disponibles.
- Exportacion de archivos CSV por tipo en:
  - `src/price_manager/migrations/csv/export_precios/`.

### Cambios
- Incorporacion de helpers de conversion monetaria y seleccion de ultima cotizacion por tipo para mejorar la visualizacion y exportacion.

---

## [Sprint 2] - Dia 8

### Cambios
- `API_URL` pasa a ser obligatoria para funcionalidades de cotizacion online.
- Eliminacion del fallback hardcodeado de URL en `src/price_manager/services/services.py`.
- Incorporacion de error de configuracion explicito (`ConfiguracionRequeridaError`) cuando falta `API_URL`.

### Agregado

---

---

## [Sprint 2] - Dia 9

### Correcciones
- Ajuste en `src/price_manager/services/services.py` para resolver correctamente la ruta del archivo `.env` tanto en ejecucion local como en Google Colab/Jupyter.
- Incorporacion de fallback para entornos donde `__file__` no esta definido.

### Cambios
- Mejora de compatibilidad entre Visual Studio Code y Google Colab.
- Validacion de carga de `API_URL` desde `.env` en ambos entornos.

### Detalles
- El cambio evita errores al ejecutar o importar `services.py` desde notebooks, manteniendo el comportamiento original en ejecucion local.
- Manejo especifico en `src/price_manager/ui/console.py` para mostrar aviso claro al usuario cuando falta `API_URL` en `.env`.

### Correcciones
- Aislamiento del fallo de configuracion: si falta `API_URL`, solo se bloquean funciones que dependen de cotizacion online y el resto del sistema sigue operativo.
