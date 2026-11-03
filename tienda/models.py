from django.db import models

class Equipo(models.Model):
    TIPOS = [("seleccion", "Selección"), ("club", "Club")]
    nombre = models.CharField(max_length=80, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    pais = models.CharField(max_length=60, blank=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    EQUIPACION = [("local", "Local"), ("visitante", "Visitante"),
                  ("tercera", "Tercera"), ("retro", "Retro")]
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="productos")
    nombre = models.CharField(max_length=120)
    equipacion = models.CharField(max_length=10, choices=EQUIPACION, default="local")
    temporada = models.CharField(max_length=10)               # "2026" o "25/26"
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    color_principal = models.CharField(max_length=7, default="#FFFFFF")
    color_secundario = models.CharField(max_length=7, default="#000000")
    #imagen = models.ImageField(upload_to="camisetas/", blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    # Alias para que el template actual siga funcionando
    @property
    def c1(self): return self.color_principal
    @property
    def c2(self): return self.color_secundario

    def __str__(self):
        return f"{self.nombre} {self.temporada}"