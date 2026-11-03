from django.shortcuts import render
from .models import Producto

def home(request):
    productos = Producto.objects.filter(activo=True).select_related("equipo").order_by("-creado")[:12]
    return render(request, "./tienda/home.html", {"productos": productos})