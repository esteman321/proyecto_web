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
def _get_usuario(request):
    """Devuelve el usuario actual ya sea autenticado por sesión de Django o por JWT."""
    if getattr(request, "user", None) and request.user.is_authenticated:
        return request.user

    auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from rest_framework_simplejwt.authentication import JWTAuthentication
            auth = JWTAuthentication()
            token_str = auth_header.split(" ")[1]
            validated_token = auth.get_validated_token(token_str)
            user = auth.get_user(validated_token)
            if user and user.is_active:
                return user
        except Exception:
            pass
    return None


def _get_carrito(request, session_key_previa=None):
    """
    Obtiene o crea el carrito.
    Si el usuario está autenticado (por sesión o JWT):
      - Se recupera su carrito persistente vinculado a 'usuario'.
      - Si en la sesión actual había un carrito anónimo previo, se fusionan sus productos.
    Si el usuario es anónimo:
      - Se utiliza el carrito asociado a la session_key de la cookie.
    """
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    buscar_anonimo_key = session_key_previa or session_key

    user = _get_usuario(request)

    if user:
        # Carrito persistente del usuario
        carrito_user = Carrito.objects.filter(usuario=user).first()

        # Carrito anónimo de la sesión actual o previa
        carrito_anonimo = None
        if buscar_anonimo_key:
            carrito_anonimo = Carrito.objects.filter(session_key=buscar_anonimo_key, usuario__isnull=True).first()

        if carrito_anonimo and carrito_anonimo != carrito_user:
            if not carrito_user:
                carrito_anonimo.usuario = user
                carrito_anonimo.session_key = session_key
                carrito_anonimo.save()
                return carrito_anonimo
            else:
                # Fusionar items del carrito anónimo al carrito del usuario
                for item_anon in carrito_anonimo.items.all():
                    item_u, created = ItemCarrito.objects.get_or_create(
                        carrito=carrito_user,
                        producto=item_anon.producto,
                        talla=item_anon.talla,
                        defaults={"cantidad": item_anon.cantidad},
                    )
                    if not created:
                        item_u.cantidad += item_anon.cantidad
                        item_u.save()
                carrito_anonimo.delete()

        if not carrito_user:
            carrito_user = Carrito.objects.create(usuario=user, session_key=session_key)
        else:
            if carrito_user.session_key != session_key:
                carrito_user.session_key = session_key
                carrito_user.save(update_fields=["session_key"])

        return carrito_user

    # Usuario anónimo
    carrito, _ = Carrito.objects.get_or_create(
        session_key=session_key,
        usuario__isnull=True,
        defaults={"session_key": session_key},
    )
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

    user = _get_usuario(request)
    form_data = {}
    if user:
        nombre_completo = f"{user.first_name} {user.last_name}".strip() or user.username
        form_data = {
            "nombre": nombre_completo,
            "email": user.email,
        }

    return render(request, "tienda/checkout.html", {
        "carrito": carrito,
        "items": items,
        "form_data": form_data,
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
    pago_exitoso = True

    if not pago_exitoso:
        return render(request, "tienda/checkout.html", {
            "carrito": carrito,
            "items": items,
            "errores": ["El pago fue rechazado. Intenta con otra tarjeta."],
            "form_data": request.POST,
        })

    # Crear el pedido vinculado al usuario si está autenticado
    user = _get_usuario(request)
    pedido = Pedido.objects.create(
        usuario=user,
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
