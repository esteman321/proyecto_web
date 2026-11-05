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
    temporada = models.CharField(max_length=10)
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # La versión Fan y la Player de una misma camiseta comparten equipación, temporada y retro
        if self.codigo:
            (Producto.objects.filter(equipo=self.equipo, codigo=self.codigo)
             .exclude(pk=self.pk)
             .update(equipacion=self.equipacion, temporada=self.temporada, retro=self.retro))

    def __str__(self):
        return f"{self.nombre} ({self.get_version_display()}) {self.temporada}"