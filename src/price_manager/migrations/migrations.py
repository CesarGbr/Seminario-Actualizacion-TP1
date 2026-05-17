from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import delete

from price_manager.database.connection import ConexionDB
from price_manager.models.models import (
    CategoriaModel,
    CotizacionDolarModel,
    MonedaModel,
    PrecioModel,
    ProductoModel,
    ProveedorModel,
    StockModel,
    TipoCotizacionModel,
    crear_tablas,
)


def _leer_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"

    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"

    if isinstance(value, date):
        return f"'{value.isoformat()}'"

    if isinstance(value, Decimal):
        return format(value, "f")

    if isinstance(value, bool):
        return "1" if value else "0"

    return str(value)


def _to_insert_sql(table_name: str, values: dict[str, Any]) -> str:
    columns = ", ".join(values.keys())
    payload = ", ".join(_sql_literal(item) for item in values.values())
    return f"INSERT INTO {table_name} ({columns}) VALUES ({payload});"


def _escribir_sql(path: Path, statements: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    contenido = "\n".join(statements)
    if contenido:
        contenido += "\n"
    path.write_text(contenido, encoding="utf-8")


def _catalogo_con_ids(valores: list[str]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    mapping: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    for value in valores:
        normalizado = value.strip().upper()
        if normalizado in mapping:
            continue
        nuevo_id = len(mapping) + 1
        mapping[normalizado] = nuevo_id
        rows.append({"id": nuevo_id, "nombre": normalizado})
    return rows, mapping


def migrar_datos(carpeta_csvs: str, carpeta_sqls: str) -> None:
    """ Funcion encargada de la migracion de datos de csv a sql.
    Se encarga de leer los archivos csv y crear los archivos sql
    para la insercion en la base de datos.

    Args:
        carpeta_csvs (str): Ruta de la carpeta que contiene los archivos csv.
        carpeta_sqls (str): Ruta donde se guardaran los archivos sql.
    """
    carpeta_csv = Path(carpeta_csvs)
    carpeta_sql = Path(carpeta_sqls)

    if not carpeta_csv.exists() or not carpeta_csv.is_dir():
        raise FileNotFoundError(
            f"La carpeta de CSV no existe o no es valida: {carpeta_csv}"
        )

    archivos_requeridos = (
        "categorias.csv",
        "proveedores.csv",
        "precios.csv",
        "cotizaciones.csv",
        "productos.csv",
        "stock.csv",
    )
    faltantes = [
        file_name
        for file_name in archivos_requeridos
        if not (carpeta_csv / file_name).exists()
    ]
    if faltantes:
        listado = ", ".join(faltantes)
        raise FileNotFoundError(f"Faltan archivos CSV requeridos: {listado}")

    categorias_csv = _leer_csv(carpeta_csv / "categorias.csv")
    proveedores_csv = _leer_csv(carpeta_csv / "proveedores.csv")
    precios_csv = _leer_csv(carpeta_csv / "precios.csv")
    cotizaciones_csv = _leer_csv(carpeta_csv / "cotizaciones.csv")
    productos_csv = _leer_csv(carpeta_csv / "productos.csv")
    stock_csv = _leer_csv(carpeta_csv / "stock.csv")

    monedas_rows, moneda_id_by_nombre = _catalogo_con_ids(
        [item["moneda"] for item in precios_csv]
    )
    tipos_rows, tipo_id_by_nombre = _catalogo_con_ids(
        [item["tipo"] for item in cotizaciones_csv]
    )

    categorias_rows = [
        {"id": int(item["id"]), "nombre": item["nombre"].strip()}
        for item in categorias_csv
    ]
    proveedores_rows = [
        {
            "id": int(item["id"]),
            "nombre_legal": item["nombre_legal"].strip(),
            "contacto": item["contacto"].strip(),
        }
        for item in proveedores_csv
    ]
    precios_rows = [
        {
            "id": int(item["id"]),
            "valor": Decimal(item["valor"]),
            "moneda_id": moneda_id_by_nombre[item["moneda"].strip().upper()],
            "fecha_actualizacion": date.fromisoformat(item["fecha_actualizacion"]),
        }
        for item in precios_csv
    ]
    cotizaciones_rows = [
        {
            "id": int(item["id"]),
            "valor": Decimal(item["valor"]),
            "fecha": date.fromisoformat(item["fecha"]),
            "tipo_cotizacion_id": tipo_id_by_nombre[item["tipo"].strip().upper()],
        }
        for item in cotizaciones_csv
    ]
    productos_rows = [
        {
            "id": int(item["id"]),
            "nombre": item["nombre"].strip(),
            "descripcion": item["descripcion"].strip(),
            "precio_id": int(item["precio_id"]),
            "categoria_id": int(item["categoria_id"]),
            "proveedor_id": int(item["proveedor_id"]),
        }
        for item in productos_csv
    ]
    stock_rows = [
        {
            "id": int(item["id"]),
            "producto_id": int(item["producto_id"]),
            "almacen": item["almacen"].strip(),
            "cantidad": int(item["cantidad"]),
        }
        for item in stock_csv
    ]

    sql_por_archivo: list[tuple[str, list[str]]] = [
        (
            "categorias.sql",
            [_to_insert_sql("categorias", row) for row in categorias_rows],
        ),
        (
            "proveedores.sql",
            [_to_insert_sql("proveedores", row) for row in proveedores_rows],
        ),
        (
            "monedas.sql",
            [_to_insert_sql("monedas", row) for row in monedas_rows],
        ),
        (
            "tipos_cotizacion.sql",
            [_to_insert_sql("tipos_cotizacion", row) for row in tipos_rows],
        ),
        (
            "precios.sql",
            [_to_insert_sql("precios", row) for row in precios_rows],
        ),
        (
            "cotizaciones_dolar.sql",
            [
                _to_insert_sql("cotizaciones_dolar", row)
                for row in cotizaciones_rows
            ],
        ),
        (
            "productos.sql",
            [_to_insert_sql("productos", row) for row in productos_rows],
        ),
        (
            "stock.sql",
            [_to_insert_sql("stock", row) for row in stock_rows],
        ),
    ]

    conexion = ConexionDB()
    try:
        crear_tablas(conexion.engine)

        with conexion.transaccion() as sesion:
            sesion.execute(delete(StockModel))
            sesion.execute(delete(ProductoModel))
            sesion.execute(delete(CotizacionDolarModel))
            sesion.execute(delete(PrecioModel))
            sesion.execute(delete(TipoCotizacionModel))
            sesion.execute(delete(MonedaModel))
            sesion.execute(delete(ProveedorModel))
            sesion.execute(delete(CategoriaModel))

            sesion.add_all(
                [CategoriaModel(**row) for row in categorias_rows]
            )
            sesion.add_all(
                [ProveedorModel(**row) for row in proveedores_rows]
            )
            sesion.add_all(
                [MonedaModel(**row) for row in monedas_rows]
            )
            sesion.add_all(
                [TipoCotizacionModel(**row) for row in tipos_rows]
            )
            sesion.add_all(
                [PrecioModel(**row) for row in precios_rows]
            )
            sesion.add_all(
                [CotizacionDolarModel(**row) for row in cotizaciones_rows]
            )
            sesion.add_all(
                [ProductoModel(**row) for row in productos_rows]
            )
            sesion.add_all(
                [StockModel(**row) for row in stock_rows]
            )
    finally:
        conexion.cerrar()

    carpeta_sql.mkdir(parents=True, exist_ok=True)
    for stale_file in carpeta_sql.glob("*.sql"):
        stale_file.unlink()

    for file_name, statements in sql_por_archivo:
        _escribir_sql(carpeta_sql / file_name, statements)
