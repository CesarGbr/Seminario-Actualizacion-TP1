# %%writefile price_manager/ui/console.py

from __future__ import annotations

import csv
from difflib import get_close_matches
from datetime import date
from pathlib import Path

from price_manager.entities.entities import Precio
from price_manager.entities.entities import Categoria, CotizacionDolar, Producto, Proveedor
from price_manager.services.services import (
    ConfiguracionRequeridaError,
    ServicioCompetenciaWeb,
    ServicioCategoria,
    ServicioCotizacionDolar,
    ServicioPrecio,
    ServicioProducto,
    ServicioProveedor,
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
        servicio_competencia: ServicioCompetenciaWeb,
        servicio_categoria: ServicioCategoria,
        servicio_proveedor: ServicioProveedor,
    ) -> None:
        self._servicio_producto = servicio_producto
        self._servicio_stock = servicio_stock
        self._servicio_precio = servicio_precio
        self._servicio_cotizacion = servicio_cotizacion
        self._servicio_competencia = servicio_competencia
        self._servicio_categoria = servicio_categoria
        self._servicio_proveedor = servicio_proveedor

    def run(self) -> None:
        self._verificar_cotizacion_inicial()
        while True:
            print("\n=== PRICE MANAGER ===")
            print("1. Listar productos")
            print("2. Buscar producto")
            print("3. Actualizar precio")
            print("8. Crear producto")
            print("4. Listar stock")
            print("5. Mostrar stock bajo")
            print("6. Actualizar cotizacion dolar en tiempo real")
            print("7. Comparar precio con competencia web")
            print("9. Gestion de catalogos")
            print("10. Gestion de cotizaciones")
            print("11. Recotizar productos segun dolar")
            print("12. Obtener cotizaciones por API")
            print("13. Ver lista de precios bimonetaria")
            print("14. Exportar precios a CSV (todos los tipos de moneda)")
            print("0. Salir")

            opcion = input("Seleccione opcion: ").strip()
            try:
                if opcion == "1":
                    self._listar_productos()
                elif opcion == "2":
                    self._buscar_producto()
                elif opcion == "3":
                    self._actualizar_precio()
                elif opcion == "8":
                    self._crear_producto()
                elif opcion == "4":
                    self._listar_stock()
                elif opcion == "5":
                    self._stock_bajo()
                elif opcion == "6":
                    self._actualizar_cotizacion_tiempo_real()
                elif opcion == "7":
                    self._comparar_competencia()
                elif opcion == "9":
                    self._menu_catalogos()
                elif opcion == "10":
                    self._menu_cotizaciones()
                elif opcion == "11":
                    self._recotizar_productos_por_dolar()
                elif opcion == "12":
                    self._obtener_cotizaciones_por_api()
                elif opcion == "13":
                    self._ver_precios_bimonetarios()
                elif opcion == "14":
                    self._exportar_precios_csv_todos_tipos()
                elif opcion == "0":
                    print("Saliendo...")
                    break
                else:
                    print("Opcion invalida")
            except ConfiguracionRequeridaError as exc:
                self._mostrar_error_configuracion(exc)
            except ValueError as exc:
                print(f"Error de validacion: {exc}")
            except RuntimeError as exc:
                print(f"Error de integracion: {exc}")
            except Exception as exc:
                print(f"Error inesperado: {exc}")

    @staticmethod
    def _mostrar_error_configuracion(exc: ConfiguracionRequeridaError) -> None:
        print(f"Configuracion faltante: {exc}")
        print("Completa API_URL en .env para habilitar esa funcionalidad.")

    def _verificar_cotizacion_inicial(self) -> None:
        """Chequeo al iniciar: garantiza decision explicita sobre cotizacion del dia."""
        hoy = date.today()
        cotizacion_hoy = self._servicio_cotizacion.buscar_por_tipo_y_fecha(
            "Oficial", hoy
        )
        if cotizacion_hoy is not None:
            print(
                f"Cotizacion de hoy cargada: {cotizacion_hoy.tipo} = "
                f"{cotizacion_hoy.valor:.2f} ({hoy.isoformat()})"
            )
            return

        confirmar = (
            input(
                f"No hay cotizacion Oficial para hoy ({hoy.isoformat()}). "
                "Desea actualizarla ahora? [s/n]: "
            )
            .strip()
            .lower()
        )
        if confirmar != "s":
            print("Continuando sin actualizar cotizacion inicial.")
            return

        try:
            cotizacion = self._servicio_cotizacion.actualizar_cotizacion_tiempo_real(
                "Oficial"
            )
            print(
                f"Cotizacion inicial actualizada: {cotizacion.tipo} = "
                f"{cotizacion.valor:.2f} ({cotizacion.fecha.isoformat()})"
            )
        except ConfiguracionRequeridaError as exc:
            self._mostrar_error_configuracion(exc)
        except RuntimeError as exc:
            print(f"No se pudo actualizar cotizacion inicial: {exc}")

    def _read_int(self, prompt: str, allow_back: bool = False) -> int | None:
        raw = input(prompt).strip()
        if allow_back and raw.lower() == "b":
            return None
        return int(raw)

    def _read_float(self, prompt: str, allow_back: bool = False) -> float | None:
        raw = input(prompt).strip()
        if allow_back and raw.lower() == "b":
            return None
        return float(raw)

    def _listar_productos(self, productos: list | None = None) -> None:
        productos = (
            productos
            if productos is not None
            else self._servicio_producto.listar_todos()
        )
        if not productos:
            print("No hay productos cargados")
            return

        cotizacion_ref = self._servicio_cotizacion.obtener_ultima_por_tipo("OFICIAL")
        if cotizacion_ref is not None:
            print(
                f"Cotizacion de referencia (OFICIAL): {cotizacion_ref.valor:.2f} ARS/USD"
            )
        else:
            print("Cotizacion de referencia (OFICIAL): no disponible")

        for producto in productos:
            precio_line = self._formatear_precio_dual(
                producto.precio.valor,
                producto.precio.moneda,
                cotizacion_ref.valor if cotizacion_ref else None,
            )
            print(f"ID: {producto.id} | {producto.nombre} | {precio_line}")

    def _seleccionar_producto(self) -> object | None:
        """Seleccion guiada de producto. Retorna None si usuario vuelve."""
        while True:
            productos = self._servicio_producto.listar_todos()
            if not productos:
                print("No hay productos cargados")
                return None

            print("\nSeleccione producto:")
            print("1. Ver todos")
            print("2. Buscar por nombre")
            print("3. Ingresar ID")
            print("b. Volver")
            opcion = input("Opcion: ").strip().lower()

            if opcion == "b":
                return None

            if opcion == "1":
                self._listar_productos(productos)
                producto_id = self._read_int(
                    "ID producto (o 'b' para volver): ", allow_back=True
                )
                if producto_id is None:
                    continue
                producto = self._servicio_producto.buscar_por_id(producto_id)
                if producto is None:
                    print("Producto no encontrado")
                    continue
                return producto

            if opcion == "2":
                termino = input("Texto a buscar en nombre: ").strip().lower()
                filtrados = [p for p in productos if termino in p.nombre.lower()]
                if not filtrados:
                    # Fuzzy matching para tolerar typos y aproximaciones.
                    nombres = [p.nombre for p in productos]
                    cercanos = get_close_matches(
                        termino, [n.lower() for n in nombres], n=5, cutoff=0.45
                    )
                    if cercanos:
                        sugeridos = [
                            p for p in productos if p.nombre.lower() in cercanos
                        ]
                        print("No hubo coincidencia exacta.")
                        if len(sugeridos) == 1:
                            principal = sugeridos[0]
                            print(
                                "Este es el producto que quisiste decir?: "
                                f"{principal.nombre} (ID {principal.id}, {principal.precio.valor:.2f} {principal.precio.moneda})"
                            )
                            confirm = input("Confirmar [s/n]: ").strip().lower()
                            if confirm == "s":
                                return principal
                        else:
                            print("Se encontraron varias opciones similares:")
                            for idx, prod in enumerate(sugeridos, start=1):
                                print(
                                    f"{idx}. {prod.nombre} (ID {prod.id}, {prod.precio.valor:.2f} {prod.precio.moneda})"
                                )
                            indice = self._read_int(
                                "Elegi indice (o 'b' para volver): ", allow_back=True
                            )
                            if indice is None:
                                continue
                            if 1 <= indice <= len(sugeridos):
                                return sugeridos[indice - 1]
                            print("Indice fuera de rango.")
                            continue
                        print("Alternativas sugeridas:")
                        self._listar_productos(sugeridos)
                        print("Podes elegir por ID o refinar texto.")
                        continue
                if not filtrados:
                    print("No se encontraron productos con ese texto")
                    continue
                if len(filtrados) == 1:
                    unico = filtrados[0]
                    print(
                        f"Se selecciono automaticamente: {unico.nombre} (ID {unico.id})"
                    )
                    return unico
                self._listar_productos(filtrados)
                producto_id = self._read_int(
                    "ID producto (o 'b' para volver): ", allow_back=True
                )
                if producto_id is None:
                    continue
                producto = self._servicio_producto.buscar_por_id(producto_id)
                if producto is None:
                    print("Producto no encontrado")
                    continue
                return producto

            if opcion == "3":
                producto_id = self._read_int(
                    "ID producto (o 'b' para volver): ", allow_back=True
                )
                if producto_id is None:
                    continue
                producto = self._servicio_producto.buscar_por_id(producto_id)
                if producto is None:
                    print("Producto no encontrado")
                    continue
                return producto

            print("Opcion invalida")

    def _buscar_producto(self) -> None:
        producto = self._seleccionar_producto()
        if producto is None:
            return

        self._mostrar_detalle_producto(producto)
        while True:
            print("\nAcciones para este producto:")
            print("1. Actualizar precio")
            print("2. Comparar con competencia")
            print("3. Eliminar producto")
            print("b. Volver")
            accion = input("Opcion: ").strip().lower()
            if accion == "b":
                return
            if accion == "1":
                self._actualizar_precio_producto(producto)
                self._mostrar_detalle_producto(producto)
                continue
            if accion == "2":
                self._comparar_competencia_producto(producto)
                continue
            if accion == "3":
                eliminado = self._eliminar_producto_objetivo(producto)
                if eliminado:
                    return
                continue
            print("Opcion invalida")

    def _mostrar_detalle_producto(self, producto) -> None:
        cotizacion_ref = self._servicio_cotizacion.obtener_ultima_por_tipo("OFICIAL")
        print(f"Nombre: {producto.nombre}")
        print(f"Descripcion: {producto.descripcion}")
        print(f"Categoria: {producto.categoria.nombre}")
        print(f"Proveedor: {producto.proveedor.nombre_legal}")
        print(
            f"Precio: {self._formatear_precio_dual(producto.precio.valor, producto.precio.moneda, cotizacion_ref.valor if cotizacion_ref else None)}"
        )

    def _actualizar_precio_producto(self, producto) -> None:
        valor = self._read_float("Nuevo precio (o 'b' para volver): ", allow_back=True)
        if valor is None:
            return
        moneda = input("Moneda (ARS/USD) o 'b' para volver: ").strip().upper()
        if moneda.lower() == "b":
            return
        precio_actualizado = Precio(id=producto.precio.id, valor=valor, moneda=moneda)
        self._servicio_precio.actualizar(precio_actualizado)
        producto.precio = precio_actualizado
        self._servicio_producto.actualizar(producto)
        print(f"Precio actualizado: {producto.precio.valor} {producto.precio.moneda}")

    def _actualizar_precio(self) -> None:
        producto = self._seleccionar_producto()
        if producto is None:
            return

        self._actualizar_precio_producto(producto)

    def _listar_stock(self) -> None:
        stock_items = self._servicio_stock.listar_todos()
        if not stock_items:
            print("No hay stock cargado")
            return
        for item in stock_items:
            print(
                f"Stock ID: {item.id} | Producto: {item.producto.nombre} | "
                f"Almacen: {item.almacen} | Cantidad: {item.cantidad}"
            )

    def _stock_bajo(self) -> None:
        minimo = self._read_int("Minimo (o 'b' para volver): ", allow_back=True)
        if minimo is None:
            return
        resultados = [
            item
            for item in self._servicio_stock.listar_todos()
            if item.cantidad < minimo
        ]
        if not resultados:
            print("No hay productos con stock bajo")
            return

        for item in resultados:
            print(f"{item.producto.nombre}: {item.cantidad}")

    def _actualizar_cotizacion_tiempo_real(self) -> None:
        tipo = input(
            "Tipo (Oficial/Blue/Bolsa/CCL/Cripto/Tarjeta/Mayorista) o 'b' para volver: "
        ).strip()
        if tipo.lower() == "b":
            return
        tipo = tipo or "Oficial"
        cotizacion_hoy = self._servicio_cotizacion.buscar_por_tipo_y_fecha(
            tipo, date.today()
        )
        if cotizacion_hoy is not None:
            print(
                f"Ya existe cotizacion para hoy ({date.today().isoformat()}): "
                f"{cotizacion_hoy.tipo} = {cotizacion_hoy.valor:.2f}"
            )
            return

        confirmar = (
            input(
                f"No hay cotizacion cargada para hoy ({date.today().isoformat()}) en tipo {tipo}. "
                "Desea actualizar ahora? [s/n]: "
            )
            .strip()
            .lower()
        )
        if confirmar != "s":
            print("Actualizacion cancelada por el usuario.")
            return

        cotizacion = self._servicio_cotizacion.actualizar_cotizacion_tiempo_real(tipo)
        print(
            f"Cotizacion actualizada: {cotizacion.tipo} = {cotizacion.valor:.2f} "
            f"(fecha {cotizacion.fecha.isoformat()})"
        )

    def _seleccionar_o_crear_categoria(self) -> Categoria | None:
        while True:
            categorias = self._servicio_categoria.listar_todos()
            print("\nCategoria:")
            print("1. Elegir existente")
            print("2. Crear nueva")
            print("b. Volver")
            opcion = input("Opcion: ").strip().lower()
            if opcion == "b":
                return None
            if opcion == "1":
                if not categorias:
                    print("No hay categorias cargadas.")
                    continue
                for idx, cat in enumerate(categorias, start=1):
                    print(f"{idx}. {cat.nombre} (ID {cat.id})")
                indice = self._read_int(
                    "Indice categoria (o 'b' para volver): ", allow_back=True
                )
                if indice is None:
                    continue
                if 1 <= indice <= len(categorias):
                    return categorias[indice - 1]
                print("Indice fuera de rango.")
                continue
            if opcion == "2":
                nombre = input("Nombre categoria (o 'b' para volver): ").strip()
                if nombre.lower() == "b":
                    continue
                next_id = max((c.id for c in categorias), default=0) + 1
                categoria = Categoria(id=next_id, nombre=nombre)
                return self._servicio_categoria.crear(categoria)
            print("Opcion invalida.")

    def _seleccionar_categoria_existente(self) -> Categoria | None:
        categorias = self._servicio_categoria.listar_todos()
        if not categorias:
            print("No hay categorias cargadas.")
            return None
        print("\nCategorias disponibles:")
        for idx, cat in enumerate(categorias, start=1):
            print(f"{idx}. {cat.nombre} (ID {cat.id})")
        indice = self._read_int(
            "Indice categoria (o 'b' para volver): ", allow_back=True
        )
        if indice is None:
            return None
        if 1 <= indice <= len(categorias):
            return categorias[indice - 1]
        print("Indice fuera de rango.")
        return None

    def _seleccionar_o_crear_proveedor(self) -> Proveedor | None:
        while True:
            proveedores = self._servicio_proveedor.listar_todos()
            print("\nProveedor:")
            print("1. Elegir existente")
            print("2. Crear nuevo")
            print("b. Volver")
            opcion = input("Opcion: ").strip().lower()
            if opcion == "b":
                return None
            if opcion == "1":
                if not proveedores:
                    print("No hay proveedores cargados.")
                    continue
                for idx, prov in enumerate(proveedores, start=1):
                    print(
                        f"{idx}. {prov.nombre_legal} (ID {prov.id}) | {prov.contacto}"
                    )
                indice = self._read_int(
                    "Indice proveedor (o 'b' para volver): ", allow_back=True
                )
                if indice is None:
                    continue
                if 1 <= indice <= len(proveedores):
                    return proveedores[indice - 1]
                print("Indice fuera de rango.")
                continue
            if opcion == "2":
                nombre = input("Nombre legal proveedor (o 'b' para volver): ").strip()
                if nombre.lower() == "b":
                    continue
                contacto = input("Contacto proveedor (o 'b' para volver): ").strip()
                if contacto.lower() == "b":
                    continue
                next_id = max((p.id for p in proveedores), default=0) + 1
                proveedor = Proveedor(id=next_id, nombre=nombre, contacto=contacto)
                return self._servicio_proveedor.crear(proveedor)
            print("Opcion invalida.")

    def _seleccionar_proveedor_existente(self) -> Proveedor | None:
        proveedores = self._servicio_proveedor.listar_todos()
        if not proveedores:
            print("No hay proveedores cargados.")
            return None
        print("\nProveedores disponibles:")
        for idx, prov in enumerate(proveedores, start=1):
            print(f"{idx}. {prov.nombre_legal} (ID {prov.id}) | {prov.contacto}")
        indice = self._read_int(
            "Indice proveedor (o 'b' para volver): ", allow_back=True
        )
        if indice is None:
            return None
        if 1 <= indice <= len(proveedores):
            return proveedores[indice - 1]
        print("Indice fuera de rango.")
        return None

    def _crear_producto(self) -> None:
        print("\nAlta de producto (ingrese 'b' para volver en cualquier paso)")
        nombre = input("Nombre producto: ").strip()
        if nombre.lower() == "b":
            return
        descripcion = input("Descripcion: ").strip()
        if descripcion.lower() == "b":
            return
        valor = self._read_float("Precio: ", allow_back=True)
        if valor is None:
            return
        moneda = input("Moneda (ARS/USD): ").strip().upper()
        if moneda.lower() == "b":
            return

        categoria = self._seleccionar_o_crear_categoria()
        if categoria is None:
            return
        proveedor = self._seleccionar_o_crear_proveedor()
        if proveedor is None:
            return

        next_price_id = (
            max((p.id for p in self._servicio_precio.listar_todos()), default=0) + 1
        )
        precio = self._servicio_precio.crear(
            Precio(id=next_price_id, valor=valor, moneda=moneda)
        )
        next_product_id = (
            max((p.id for p in self._servicio_producto.listar_todos()), default=0) + 1
        )
        producto = Producto(
            id=next_product_id,
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            categoria=categoria,
            proveedor=proveedor,
        )
        self._servicio_producto.crear(producto)
        print(
            f"Producto creado: ID {producto.id} | {producto.nombre} | {precio.valor:.2f} {precio.moneda}"
        )

    def _comparar_competencia(self) -> None:
        producto = self._seleccionar_producto()
        if producto is None:
            return
        self._comparar_competencia_producto(producto)

    def _comparar_competencia_producto(self, producto) -> None:
        cotizacion_ref = self._servicio_cotizacion.obtener_ultima_por_tipo("OFICIAL")
        try:
            result = self._servicio_competencia.comparar_producto(
                nombre_producto=producto.nombre,
                precio_local=producto.precio.valor,
            )
        except RuntimeError as exc:
            error_text = str(exc)
            if "No se pudo consultar web de competencia" in error_text:
                print("No fue posible consultar la web de competencia en este momento.")
                print(
                    "Recomendacion: reintentar mas tarde o verificar conectividad de red."
                )
                return
            if "No se encontraron productos en la web de competencia" in error_text:
                print("La web de competencia no devolvio productos para comparar.")
                print("Recomendacion: reintentar en unos minutos.")
                return
            if "Busqueda ambigua en competencia" in error_text:
                print("Busqueda ambigua. Elegi una sugerencia para comparar:")
                sugerencias = self._servicio_competencia.sugerir_productos(
                    nombre_producto=producto.nombre,
                    precio_local=producto.precio.valor,
                    limit=5,
                )
                if not sugerencias:
                    print("No se pudieron generar sugerencias en este momento.")
                    return
                for idx, item in enumerate(sugerencias, start=1):
                    print(
                        f"{idx}. {item['title']} | ARS {item['price_ars']:.2f} "
                        f"| match {item['match_confidence']:.1f}%"
                    )
                indice = self._read_int(
                    "Indice sugerencia (o 'b' para volver): ", allow_back=True
                )
                if indice is None:
                    return
                if not 1 <= indice <= len(sugerencias):
                    print("Indice fuera de rango.")
                    return
                elegida = sugerencias[indice - 1]
                result = self._servicio_competencia.comparar_producto_con_titulo(
                    nombre_producto=producto.nombre,
                    precio_local=producto.precio.valor,
                    competitor_title=str(elegida["title"]),
                )
            else:
                print(f"No se pudo comparar: {error_text}")
                return

        print("\nComparacion web (starcomputacion.com.ar)")
        print(
            "Producto local: "
            f"{producto.nombre} | Precio local: "
            f"{self._formatear_precio_dual(result['local_price'], producto.precio.moneda, cotizacion_ref.valor if cotizacion_ref else None)}"
        )
        print(f"Match competencia: {result['competitor_title']}")
        print(f"Confianza de match: {result['match_confidence']:.1f}%")
        print(f"Precio competencia: ARS {result['competitor_price_ars']:.2f}")
        print(
            f"Diferencia numerica: {result['difference']:.2f} ({result['difference_pct']:.2f}%)"
        )
        print(f"URL: {result['competitor_url']}")
        print("Nota: comparacion referencial segun match por nombre.")

    def _formatear_precio_dual(
        self, valor: float, moneda: str, cotizacion_ars_usd: float | None
    ) -> str:
        moneda_norm = (moneda or "").strip().upper()
        if cotizacion_ars_usd is None or cotizacion_ars_usd <= 0:
            return f"{valor:.2f} {moneda_norm}"

        if moneda_norm == "USD":
            ars = valor * cotizacion_ars_usd
            return f"{valor:.2f} USD | {ars:.2f} ARS"
        if moneda_norm == "ARS":
            usd = valor / cotizacion_ars_usd
            return f"{valor:.2f} ARS | {usd:.2f} USD"
        return f"{valor:.2f} {moneda_norm}"

    def _precio_en_ars_y_usd(
        self, valor: float, moneda: str, cotizacion_ars_usd: float
    ) -> tuple[float, float]:
        moneda_norm = (moneda or "").strip().upper()
        if moneda_norm == "USD":
            return valor * cotizacion_ars_usd, valor
        if moneda_norm == "ARS":
            return valor, valor / cotizacion_ars_usd
        raise ValueError(f"Moneda no soportada para conversion: {moneda_norm}")

    def _obtener_ultimas_cotizaciones(self) -> dict[str, CotizacionDolar]:
        cotizaciones = self._servicio_cotizacion.listar_todos()
        ultimas: dict[str, CotizacionDolar] = {}
        for cotizacion in cotizaciones:
            actual = ultimas.get(cotizacion.tipo)
            if actual is None or (cotizacion.fecha, cotizacion.id) > (
                actual.fecha,
                actual.id,
            ):
                ultimas[cotizacion.tipo] = cotizacion
        return dict(sorted(ultimas.items(), key=lambda item: item[0]))

    def _obtener_cotizaciones_por_api(self) -> None:
        cotizaciones = self._servicio_cotizacion.obtener_cotizaciones()
        if not cotizaciones:
            print("No se registraron cotizaciones desde la API.")
            return
        print(f"Se registraron/actualizaron {len(cotizaciones)} cotizaciones.")
        for cotizacion in sorted(
            cotizaciones,
            key=lambda item: (item.fecha, item.tipo, item.id),
        ):
            print(
                f"ID {cotizacion.id} | {cotizacion.tipo} | "
                f"{cotizacion.fecha.isoformat()} | {cotizacion.valor:.2f}"
            )

    def _ver_precios_bimonetarios(self) -> None:
        productos = self._servicio_producto.listar_todos()
        if not productos:
            print("No hay productos cargados")
            return

        ultimas = self._obtener_ultimas_cotizaciones()
        if not ultimas:
            print("No hay cotizaciones cargadas. Primero obtenelas por API.")
            return

        opciones = list(ultimas.values())
        print("\nTipo de cotizacion para vista bimonetaria:")
        for idx, cotizacion in enumerate(opciones, start=1):
            print(
                f"{idx}. {cotizacion.tipo} | {cotizacion.valor:.2f} "
                f"({cotizacion.fecha.isoformat()})"
            )

        indice = self._read_int("Indice tipo (o 'b' para volver): ", allow_back=True)
        if indice is None:
            return
        if not 1 <= indice <= len(opciones):
            print("Indice fuera de rango.")
            return

        seleccionada = opciones[indice - 1]
        if seleccionada.valor <= 0:
            print("La cotizacion seleccionada es invalida.")
            return

        print(
            f"\nLista bimonetaria usando {seleccionada.tipo} "
            f"({seleccionada.valor:.2f} ARS/USD)"
        )
        for producto in sorted(productos, key=lambda item: item.id):
            ars, usd = self._precio_en_ars_y_usd(
                producto.precio.valor,
                producto.precio.moneda,
                seleccionada.valor,
            )
            print(
                f"ID {producto.id} | {producto.nombre} | "
                f"ARS {ars:.2f} | USD {usd:.2f} ({seleccionada.tipo})"
            )

    def _exportar_precios_csv_todos_tipos(self) -> None:
        productos = self._servicio_producto.listar_todos()
        if not productos:
            print("No hay productos para exportar.")
            return

        ultimas = self._obtener_ultimas_cotizaciones()
        if not ultimas:
            print("No hay cotizaciones cargadas. Primero obtenelas por API.")
            return

        output_dir = (
            Path(__file__).resolve().parents[1]
            / "migrations"
            / "csv"
            / "export_precios"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "producto_id",
            "producto_nombre",
            "moneda_origen",
            "precio_origen",
            "tipo_cotizacion",
            "fecha_cotizacion",
            "cotizacion_ars_usd",
            "precio_ars",
            "precio_usd",
        ]

        archivos_generados: list[Path] = []
        for cotizacion in ultimas.values():
            if cotizacion.valor <= 0:
                continue

            file_path = output_dir / f"precios_{cotizacion.tipo.lower()}.csv"
            with file_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for producto in sorted(productos, key=lambda item: item.id):
                    ars, usd = self._precio_en_ars_y_usd(
                        producto.precio.valor,
                        producto.precio.moneda,
                        cotizacion.valor,
                    )
                    writer.writerow(
                        {
                            "producto_id": producto.id,
                            "producto_nombre": producto.nombre,
                            "moneda_origen": producto.precio.moneda,
                            "precio_origen": f"{producto.precio.valor:.4f}",
                            "tipo_cotizacion": cotizacion.tipo,
                            "fecha_cotizacion": cotizacion.fecha.isoformat(),
                            "cotizacion_ars_usd": f"{cotizacion.valor:.4f}",
                            "precio_ars": f"{ars:.4f}",
                            "precio_usd": f"{usd:.4f}",
                        }
                    )
            archivos_generados.append(file_path)

        if not archivos_generados:
            print("No se genero ningun archivo CSV por falta de cotizaciones validas.")
            return

        print("Exportacion completada. Archivos generados:")
        for file_path in archivos_generados:
            print(f"- {file_path}")

    def _eliminar_producto(self) -> None:
        producto = self._seleccionar_producto()
        if producto is None:
            return
        self._eliminar_producto_objetivo(producto)

    def _eliminar_producto_objetivo(self, producto) -> bool:
        confirmar = (
            input(f"Confirmar eliminacion de '{producto.nombre}'? [s/n]: ")
            .strip()
            .lower()
        )
        if confirmar != "s":
            print("Eliminacion cancelada.")
            return False
        self._servicio_stock.eliminar_por_producto(producto.id)
        self._servicio_producto.eliminar(producto.id)
        print(f"Producto eliminado: {producto.nombre} (ID {producto.id})")
        return True

    def _eliminar_categoria(self) -> None:
        categoria = self._seleccionar_categoria_existente()
        if categoria is None:
            return
        en_uso = [
            p
            for p in self._servicio_producto.listar_todos()
            if p.categoria.id == categoria.id
        ]
        if en_uso:
            print("No se puede eliminar: la categoria esta asociada a productos.")
            print("Productos que la usan:")
            for prod in en_uso:
                print(f"- {prod.nombre} (ID {prod.id})")
            return
        confirmar = (
            input(f"Confirmar eliminacion de categoria '{categoria.nombre}'? [s/n]: ")
            .strip()
            .lower()
        )
        if confirmar != "s":
            print("Eliminacion cancelada.")
            return
        self._servicio_categoria.eliminar(categoria.id)
        print(f"Categoria eliminada: {categoria.nombre} (ID {categoria.id})")

    def _eliminar_proveedor(self) -> None:
        proveedor = self._seleccionar_proveedor_existente()
        if proveedor is None:
            return
        en_uso = [
            p
            for p in self._servicio_producto.listar_todos()
            if p.proveedor.id == proveedor.id
        ]
        if en_uso:
            print("No se puede eliminar: el proveedor esta asociado a productos.")
            print("Productos que lo usan:")
            for prod in en_uso:
                print(f"- {prod.nombre} (ID {prod.id})")
            return
        confirmar = (
            input(
                f"Confirmar eliminacion de proveedor '{proveedor.nombre_legal}'? [s/n]: "
            )
            .strip()
            .lower()
        )
        if confirmar != "s":
            print("Eliminacion cancelada.")
            return
        self._servicio_proveedor.eliminar(proveedor.id)
        print(f"Proveedor eliminado: {proveedor.nombre_legal} (ID {proveedor.id})")

    def _menu_catalogos(self) -> None:
        while True:
            print("\nGestion de catalogos")
            print("1. Eliminar categoria")
            print("2. Eliminar proveedor")
            print("b. Volver")
            opcion = input("Opcion: ").strip().lower()
            if opcion == "b":
                return
            if opcion == "1":
                self._eliminar_categoria()
            elif opcion == "2":
                self._eliminar_proveedor()
            else:
                print("Opcion invalida")

    def _listar_cotizaciones(self) -> None:
        cotizaciones = self._servicio_cotizacion.listar_todos()
        if not cotizaciones:
            print("No hay cotizaciones cargadas.")
            return
        for cot in sorted(cotizaciones, key=lambda x: (x.fecha, x.tipo, x.id)):
            print(
                f"ID {cot.id} | {cot.tipo} | {cot.fecha.isoformat()} | {cot.valor:.2f}"
            )

    def _actualizar_cotizacion_manual(self) -> None:
        cot_id = self._read_int(
            "ID cotizacion a actualizar (o 'b' para volver): ", allow_back=True
        )
        if cot_id is None:
            return
        cot = self._servicio_cotizacion.buscar_por_id(cot_id)
        if cot is None:
            print("Cotizacion no encontrada.")
            return
        nuevo_valor = self._read_float(
            "Nuevo valor (o 'b' para volver): ", allow_back=True
        )
        if nuevo_valor is None:
            return
        cot.valor = nuevo_valor
        self._servicio_cotizacion.actualizar(cot)
        print(f"Cotizacion actualizada: ID {cot.id} | {cot.tipo} | {cot.valor:.2f}")

    def _eliminar_cotizacion(self) -> None:
        cot_id = self._read_int(
            "ID cotizacion a eliminar (o 'b' para volver): ", allow_back=True
        )
        if cot_id is None:
            return
        cot = self._servicio_cotizacion.buscar_por_id(cot_id)
        if cot is None:
            print("Cotizacion no encontrada.")
            return
        confirmar = (
            input(
                f"Confirmar eliminacion de cotizacion ID {cot.id} ({cot.tipo} {cot.fecha.isoformat()})? [s/n]: "
            )
            .strip()
            .lower()
        )
        if confirmar != "s":
            print("Eliminacion cancelada.")
            return
        ok = self._servicio_cotizacion.eliminar(cot.id)
        if ok:
            print("Cotizacion eliminada.")
        else:
            print("No se pudo eliminar la cotizacion.")

    def _menu_cotizaciones(self) -> None:
        while True:
            print("\nGestion de cotizaciones")
            print("1. Listar cotizaciones")
            print("2. Actualizar cotizacion manual")
            print("3. Eliminar cotizacion")
            print("b. Volver")
            opcion = input("Opcion: ").strip().lower()
            if opcion == "b":
                return
            if opcion == "1":
                self._listar_cotizaciones()
            elif opcion == "2":
                self._actualizar_cotizacion_manual()
            elif opcion == "3":
                self._eliminar_cotizacion()
            else:
                print("Opcion invalida")

    def _recotizar_productos_por_dolar(self) -> None:
        print("\nRecotizacion por dolar")
        print("1. Convertir precios USD -> ARS")
        print("2. Convertir precios ARS -> USD")
        print("b. Volver")
        opcion = input("Opcion: ").strip().lower()
        if opcion == "b":
            return
        if opcion not in {"1", "2"}:
            print("Opcion invalida")
            return

        tipo = input(
            "Tipo de cotizacion (Oficial/Blue/Bolsa/CCL/Cripto/Tarjeta/Mayorista): "
        ).strip()
        tipo = tipo or "Oficial"

        cotizacion_ref = self._servicio_cotizacion.obtener_ultima_por_tipo(tipo)
        if cotizacion_ref is None:
            confirmar = (
                input(
                    f"No hay cotizacion cargada para tipo {tipo}. "
                    "Desea actualizarla online ahora? [s/n]: "
                )
                .strip()
                .lower()
            )
            if confirmar != "s":
                print("No se puede recotizar sin una cotizacion de referencia.")
                return
            cotizacion_ref = (
                self._servicio_cotizacion.actualizar_cotizacion_tiempo_real(tipo)
            )

        factor = cotizacion_ref.valor
        if factor <= 0:
            print("La cotizacion de referencia es invalida.")
            return

        if opcion == "1":
            moneda_origen, moneda_destino = "USD", "ARS"
            transformar = lambda valor: valor * factor
        else:
            moneda_origen, moneda_destino = "ARS", "USD"
            transformar = lambda valor: valor / factor

        actualizados = 0
        productos = self._servicio_producto.listar_todos()
        for producto in productos:
            moneda_actual = (producto.precio.moneda or "").strip().upper()
            if moneda_actual != moneda_origen:
                continue
            nuevo_valor = transformar(producto.precio.valor)
            precio_actualizado = Precio(
                id=producto.precio.id,
                valor=nuevo_valor,
                moneda=moneda_destino,
                fecha=date.today(),
            )
            self._servicio_precio.actualizar(precio_actualizado)
            producto.precio = precio_actualizado
            self._servicio_producto.actualizar(producto)
            actualizados += 1

        if actualizados == 0:
            print(
                f"No habia productos en {moneda_origen} para recotizar con tipo {cotizacion_ref.tipo}."
            )
            return

        print(
            f"Recotizacion completada: {actualizados} productos ({moneda_origen} -> "
            f"{moneda_destino}) con {cotizacion_ref.tipo} = {cotizacion_ref.valor:.2f}."
        )

