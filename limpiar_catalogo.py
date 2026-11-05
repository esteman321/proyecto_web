
from django.db import transaction
from django.core.files.storage import default_storage
from tienda.models import Producto, Equipo

# Obtener información antes de eliminar.
total_productos = Producto.objects.count()
total_equipos = Equipo.objects.count()

imagenes = set(
    Producto.objects.exclude(imagen="")
    .values_list("imagen", flat=True)
)

print("\n========== RESUMEN DE LIMPIEZA ==========")
print(f"Productos encontrados: {total_productos}")
print(f"Equipos encontrados: {total_equipos}")
print(f"Imágenes encontradas: {len(imagenes)}")

# Eliminar registros.
with transaction.atomic():
    Producto.objects.all().delete()
    Equipo.objects.all().delete()

# Eliminar archivos físicos.
eliminadas = 0
errores = []

for imagen in imagenes:
    try:
        if default_storage.exists(imagen):
            default_storage.delete(imagen)
            eliminadas += 1
    except Exception as error:
        errores.append((imagen, str(error)))

print("\n========== LIMPIEZA FINALIZADA ==========")
print(f"Productos restantes: {Producto.objects.count()}")
print(f"Equipos restantes: {Equipo.objects.count()}")
print(f"Imágenes eliminadas: {eliminadas}")

if errores:
    print("\nArchivos que no pudieron eliminarse:")
    for imagen, error in errores:
        print(f"{imagen}: {error}")
