import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify


class Equipo(models.Model):
    TIPOS = [("seleccion", "Selección"), ("club", "Club")]
    nombre = models.CharField(max_length=80, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    pais = models.CharField(max_length=60, blank=True)
    liga = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["nombre"]

    @property
    def slug(self):
        """Se usa en las URLs y para nombrar el escudo: 'Bayern Múnich' -> 'bayern-munich'."""
        return slugify(self.nombre)

    @property
    def grupo(self):
        """Liga a la que pertenece; las selecciones se agrupan aparte."""
        if self.liga:
            return self.liga
        return "Selecciones" if self.tipo == "seleccion" else "Otras ligas"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    EQUIPACION = [("local", "Local"), ("visitante", "Visitante"),
                  ("tercera", "Tercera"), ("sin_definir", "Por definir")]
    VERSIONES = [("fan", "Fan"), ("player", "Player")]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="productos")
    nombre = models.CharField(max_length=120)
    version = models.CharField(max_length=10, choices=VERSIONES, default="fan")
    codigo = models.CharField(max_length=60, blank=True, db_index=True)  # ej. "producto_018"
    equipacion = models.CharField(max_length=12, choices=EQUIPACION, default="local")
    retro = models.BooleanField(default=False)
    temporada = models.CharField(max_length=10, blank=True)   # vacía si no se conoce (retro)
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    color_principal = models.CharField(max_length=7, default="#FFFFFF")
    color_secundario = models.CharField(max_length=7, default="#000000")
    imagen = models.ImageField(upload_to="camisetas/", blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    @property
    def c1(self):
        return self.color_principal

    @property
    def c2(self):
        return self.color_secundario

    @property
    def equipacion_definida(self):
        return self.equipacion != "sin_definir"

    @property
    def meta(self):
        """'Retro · Local · 1998' (solo las partes que existen)."""
        partes = []
        if self.retro:
            partes.append("Retro")
        if self.equipacion_definida:
            partes.append(self.get_equipacion_display())
        if self.temporada:
            partes.append(self.temporada)
        return " · ".join(partes)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # La versión Fan y la Player de una misma camiseta comparten equipación, temporada y retro
        if self.codigo:
            (Producto.objects.filter(equipo=self.equipo, codigo=self.codigo)
             .exclude(pk=self.pk)
             .update(equipacion=self.equipacion, temporada=self.temporada, retro=self.retro))

    def __str__(self):
        return f"{self.nombre} ({self.get_version_display()}) {self.temporada}"


# ======================================================================
# Carrito de compras (vinculado a usuario o sesión)
# ======================================================================

class Carrito(models.Model):
    """Carrito vinculado a un usuario (si está autenticado) o a una sesión del navegador."""
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="carritos"
    )
    session_key = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.usuario:
            return f"Carrito {self.pk} (Usuario: {self.usuario.username})"
        return f"Carrito {self.pk} ({self.session_key[:8] if self.session_key else 'sin sesión'}…)"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def cantidad_total(self):
        return sum(item.cantidad for item in self.items.all())


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    talla = models.CharField(max_length=5)
    cantidad = models.PositiveIntegerField(default=1)
    agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("carrito", "producto", "talla")
        ordering = ["-agregado"]

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f"{self.producto.nombre} ({self.talla}) x{self.cantidad}"


# ======================================================================
# Pedidos (se crean al completar el checkout)
# ======================================================================

ESTADOS_PEDIDO = [
    ("pendiente", "Pendiente"),
    ("pagado", "Pagado"),
    ("enviado", "Enviado"),
    ("entregado", "Entregado"),
    ("cancelado", "Cancelado"),
]


class Pedido(models.Model):
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="pedidos"
    )
    numero = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nombre = models.CharField(max_length=120)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField()
    ciudad = models.CharField(max_length=80)
    estado_pedido = models.CharField(max_length=12, choices=ESTADOS_PEDIDO, default="pendiente")
    total = models.DecimalField(max_digits=12, decimal_places=0)
    # Datos simulados de pago
    ultimos_4 = models.CharField(max_length=4, blank=True)
    metodo_pago = models.CharField(max_length=30, default="tarjeta_simulada")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"Pedido {self.numero.hex[:8].upper()} · ${self.total}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    nombre_producto = models.CharField(max_length=150)
    version = models.CharField(max_length=10)
    talla = models.CharField(max_length=5)
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    cantidad = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.precio * self.cantidad

    def __str__(self):
        return f"{self.nombre_producto} ({self.talla}) x{self.cantidad}"
