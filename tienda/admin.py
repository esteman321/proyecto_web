from django.contrib import admin
from .models import Equipo, Producto, Carrito, ItemCarrito, Pedido, ItemPedido


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "liga", "pais")
    list_filter = ("tipo", "liga")
    search_fields = ("nombre",)


def _marcar(equipacion, etiqueta):
    @admin.action(description=f"Marcar como equipación {etiqueta}")
    def accion(modeladmin, request, queryset):
        n = 0
        for p in queryset:
            p.equipacion = equipacion
            p.save()
            n += 1
        modeladmin.message_user(request, f"{n} camisetas marcadas como {etiqueta}.")
    accion.__name__ = f"marcar_{equipacion}"
    return accion


@admin.action(description="Marcar como RETRO")
def marcar_retro(modeladmin, request, queryset):
    for p in queryset:
        p.retro = True
        p.save()


@admin.action(description="Quitar marca RETRO")
def quitar_retro(modeladmin, request, queryset):
    for p in queryset:
        p.retro = False
        p.save()


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "equipo", "version", "equipacion", "retro", "temporada", "precio", "activo")
    list_editable = ("equipacion", "retro", "temporada", "precio", "activo")
    list_filter = ("version", "equipacion", "retro", "temporada", "activo", "equipo__liga")
    search_fields = ("nombre", "codigo", "equipo__nombre")
    list_per_page = 100
    ordering = ("equipo__nombre", "codigo", "version")   # Fan y Player quedan juntas
    actions = [_marcar("local", "Local"), _marcar("visitante", "Visitante"),
               _marcar("tercera", "Tercera"), marcar_retro, quitar_retro]


class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0
    readonly_fields = ("producto", "talla", "cantidad", "subtotal")


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ("pk", "session_key", "cantidad_total", "total", "actualizado")
    readonly_fields = ("session_key",)
    inlines = [ItemCarritoInline]


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ("producto", "nombre_producto", "version", "talla", "precio", "cantidad", "subtotal")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("numero", "nombre", "email", "ciudad", "total", "estado_pedido", "creado")
    list_filter = ("estado_pedido", "creado")
    search_fields = ("nombre", "email", "numero")
    readonly_fields = ("numero", "creado")
    list_editable = ("estado_pedido",)
    inlines = [ItemPedidoInline]
