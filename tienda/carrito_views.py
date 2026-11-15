"""
Vistas del carrito de compras y checkout con pasarela de pagos simulada.
"""
import json
import re

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_GET

from .models import Carrito, ItemCarrito, ItemPedido, Pedido, Producto


# ------------------------------------------------------------------ helpers
def _get_carrito(request):
    """Obtiene o crea el carrito asociado a la sesión actual."""
    if not request.session.session_key:
        request.session.create()
    key = request.session.session_key
    carrito, _ = Carrito.objects.get_or_create(session_key=key)
    return carrito


def _carrito_badge(carrito):
    """Número para el badge del ícono del carrito."""
    return carrito.cantidad_total


# ------------------------------------------------------------------ carrito
@require_POST
def agregar_al_carrito(request):
    """Agrega un producto al carrito (AJAX)."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST

    producto_id = data.get("producto_id")
    talla = data.get("talla", "M")
    cantidad = int(data.get("cantidad", 1))

    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    carrito = _get_carrito(request)

    item, created = ItemCarrito.objects.get_or_create(
        carrito=carrito, producto=producto, talla=talla,
        defaults={"cantidad": cantidad},
    )
    if not created:
        item.cantidad += cantidad
        item.save()

    return JsonResponse({
        "ok": True,
        "mensaje": f"{producto.nombre} ({talla}) agregado al carrito.",
        "badge": _carrito_badge(carrito),
        "total_items": carrito.cantidad_total,
    })


@require_GET
def ver_carrito(request):
    """Página del carrito."""
    carrito = _get_carrito(request)
    items = carrito.items.select_related("producto", "producto__equipo").all()
    return render(request, "tienda/carrito.html", {
        "carrito": carrito,
        "items": items,
    })


@require_POST
def actualizar_item(request, item_id):
    """Actualiza la cantidad de un item (AJAX)."""
    carrito = _get_carrito(request)
    item = get_object_or_404(ItemCarrito, pk=item_id, carrito=carrito)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST

    nueva_cantidad = int(data.get("cantidad", 1))
    if nueva_cantidad < 1:
        item.delete()
    else:
        item.cantidad = nueva_cantidad
        item.save()

    return JsonResponse({
        "ok": True,
        "badge": _carrito_badge(carrito),
        "total": int(carrito.total),
        "cantidad_total": carrito.cantidad_total,
        "subtotal": int(item.subtotal) if nueva_cantidad >= 1 else 0,
    })


@require_POST
def eliminar_item(request, item_id):
    """Elimina un item del carrito (AJAX)."""
    carrito = _get_carrito(request)
    item = get_object_or_404(ItemCarrito, pk=item_id, carrito=carrito)
    item.delete()

    return JsonResponse({
        "ok": True,
        "badge": _carrito_badge(carrito),
        "total": int(carrito.total),
        "cantidad_total": carrito.cantidad_total,
    })


@require_GET
def badge_carrito(request):
    """Devuelve solo el conteo del carrito (para actualizar el badge)."""
    carrito = _get_carrito(request)
    return JsonResponse({"badge": _carrito_badge(carrito)})


# ------------------------------------------------------------------ checkout
@require_GET
def checkout(request):
    """Página del checkout con formulario de datos y pasarela simulada."""
    carrito = _get_carrito(request)
    items = carrito.items.select_related("producto", "producto__equipo").all()
    if not items.exists():
        return redirect("carrito")
    return render(request, "tienda/checkout.html", {
        "carrito": carrito,
        "items": items,
    })


@require_POST
def procesar_pago(request):
    """Procesa el pago simulado y crea el pedido."""
    carrito = _get_carrito(request)
    items = carrito.items.select_related("producto").all()

    if not items.exists():
        return redirect("carrito")

    # Datos del formulario
    nombre = request.POST.get("nombre", "").strip()
    email = request.POST.get("email", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    direccion = request.POST.get("direccion", "").strip()
    ciudad = request.POST.get("ciudad", "").strip()
    numero_tarjeta = request.POST.get("numero_tarjeta", "").replace(" ", "")
    titular = request.POST.get("titular", "").strip()
    vencimiento = request.POST.get("vencimiento", "").strip()
    cvv = request.POST.get("cvv", "").strip()

    # Validación básica
    errores = []
    if not nombre:
        errores.append("El nombre es obligatorio.")
    if not email or "@" not in email:
        errores.append("Introduce un email válido.")
    if not direccion:
        errores.append("La dirección es obligatoria.")
    if not ciudad:
        errores.append("La ciudad es obligatoria.")
    if not numero_tarjeta or len(numero_tarjeta) < 13:
        errores.append("Número de tarjeta inválido.")
    if not titular:
        errores.append("El nombre del titular es obligatorio.")
    if not vencimiento or not re.match(r"^\d{2}/\d{2}$", vencimiento):
        errores.append("Fecha de vencimiento inválida (MM/AA).")
    if not cvv or len(cvv) < 3:
        errores.append("CVV inválido.")

    if errores:
        return render(request, "tienda/checkout.html", {
            "carrito": carrito,
            "items": items,
            "errores": errores,
            "form_data": request.POST,
        })

    # === PASARELA SIMULADA ===
    # En producción aquí se integraría con Stripe, PayU, MercadoPago, etc.
    # Simulamos que el pago siempre es exitoso.
    pago_exitoso = True

    if not pago_exitoso:
        return render(request, "tienda/checkout.html", {
            "carrito": carrito,
            "items": items,
            "errores": ["El pago fue rechazado. Intenta con otra tarjeta."],
            "form_data": request.POST,
        })

    # Crear el pedido
    pedido = Pedido.objects.create(
        nombre=nombre,
        email=email,
        telefono=telefono,
        direccion=direccion,
        ciudad=ciudad,
        total=carrito.total,
        ultimos_4=numero_tarjeta[-4:],
        estado_pedido="pagado",
    )

    # Crear los items del pedido
    for item in items:
        ItemPedido.objects.create(
            pedido=pedido,
            producto=item.producto,
            nombre_producto=item.producto.nombre,
            version=item.producto.version,
            talla=item.talla,
            precio=item.producto.precio,
            cantidad=item.cantidad,
        )

    # Vaciar el carrito
    carrito.items.all().delete()

    return redirect("confirmacion", numero=pedido.numero)


@require_GET
def confirmacion(request, numero):
    """Página de confirmación del pedido."""
    pedido = get_object_or_404(Pedido, numero=numero)
    items = pedido.items.all()
    return render(request, "tienda/confirmacion.html", {
        "pedido": pedido,
        "items": items,
    })
