from __future__ import annotations

from price_manager.entities.entities import Precio
from price_manager.services.services import (
  ServicioCotizacionDolar,
  ServicioPrecio,
  ServicioProducto,
  ServicioStock,
)


class PriceManagerConsole:
  """Interfaz de consola para operar el sistema."""

  def __init__(
    self,
    servicio_producto: ServicioProducto,
    servicio_stock: ServicioStock,
    servicio_precio: ServicioPrecio,
    servicio_cotizacion: ServicioCotizacionDolar,
  ) -> None:
    self._servicio_producto = servicio_producto
    self._servicio_stock = servicio_stock
    self._servicio_precio = servicio_precio
    self._servicio_cotizacion = servicio_cotizacion

  def run(self) -> None:
    while True:
      print("\n=== PRICE MANAGER ===")
      print("1. Listar productos")
      print("2. Buscar producto por ID")
      print("3. Actualizar precio")
      print("4. Listar stock")
      print("5. Mostrar stock bajo")
      print("0. Salir")

      opcion = input("Seleccione opcion: ").strip()
      if opcion == "1":
        self._listar_productos()
      elif opcion == "2":
        self._buscar_producto()
      elif opcion == "3":
        self._actualizar_precio()
      elif opcion == "4":
        self._listar_stock()
      elif opcion == "5":
        self._stock_bajo()
      elif opcion == "0":
        print("Saliendo...")
        break
      else:
        print("Opcion invalida")

  def _listar_productos(self) -> None:
    productos = self._servicio_producto.listar_todos()
    if not productos:
      print("No hay productos cargados")
      return

    for producto in productos:
      print(
        f"ID: {producto.id} | {producto.nombre} | "
        f"{producto.precio.valor} {producto.precio.moneda}"
      )

  def _buscar_producto(self) -> None:
    producto_id = int(input("ID producto: "))
    producto = self._servicio_producto.buscar_por_id(producto_id)
    if producto is None:
      print("Producto no encontrado")
      return

    print(f"Nombre: {producto.nombre}")
    print(f"Descripcion: {producto.descripcion}")
    print(f"Categoria: {producto.categoria.nombre}")
    print(f"Proveedor: {producto.proveedor.nombre_legal}")
    print(f"Precio: {producto.precio.valor} {producto.precio.moneda}")

  def _actualizar_precio(self) -> None:
    producto_id = int(input("ID producto: "))
    valor = float(input("Nuevo precio: "))
    moneda = input("Moneda (ARS/USD): ").strip().upper()

    producto = self._servicio_producto.buscar_por_id(producto_id)
    if producto is None:
      raise ValueError(f"No existe producto con id {producto_id}")

    precio_actualizado = Precio(producto.precio.id, valor, moneda)
    self._servicio_precio.actualizar(precio_actualizado)
    producto.precio = precio_actualizado
    self._servicio_producto.actualizar(producto)
    print(f"Precio actualizado: {producto.precio.valor} {producto.precio.moneda}")

  def _listar_stock(self) -> None:
    for item in self._servicio_stock.listar_todos():
      print(
        f"Stock ID: {item.id} | Producto: {item.producto.nombre} | "
        f"Almacen: {item.almacen} | Cantidad: {item.cantidad}"
      )

  def _stock_bajo(self) -> None:
    minimo = int(input("Minimo: "))
    resultados = [item for item in self._servicio_stock.listar_todos() if item.cantidad < minimo]
    if not resultados:
      print("No hay productos con stock bajo")
      return

    for item in resultados:
      print(f"{item.producto.nombre}: {item.cantidad}")
