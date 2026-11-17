"""Vistas de autenticación JWT para la API de Tribuna."""
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(["POST"])
@permission_classes([AllowAny])
def registro(request):
    """Crea una nueva cuenta de usuario y devuelve sus datos y tokens JWT."""
    data = request.data or {}
    username = str(data.get("username") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")
    first_name = str(data.get("first_name") or "").strip()
    last_name = str(data.get("last_name") or "").strip()

    if not username:
        return Response({"error": "El nombre de usuario es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
    if not email:
        return Response({"error": "El correo electrónico es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
    if "@" not in email or "." not in email:
        return Response({"error": "Ingresa un correo electrónico válido."}, status=status.HTTP_400_BAD_REQUEST)
    if not password:
        return Response({"error": "La contraseña es obligatoria."}, status=status.HTTP_400_BAD_REQUEST)
    if len(password) < 6:
        return Response({"error": "La contraseña debe tener al menos 6 caracteres."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username__iexact=username).exists():
        return Response({"error": "Este nombre de usuario ya está registrado."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email__iexact=email).exists():
        return Response({"error": "Ya existe una cuenta asociada a este correo electrónico."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    session_key_previa = request.session.session_key
    django_login(request, user)
    from .carrito_views import _get_carrito, _carrito_badge
    carrito = _get_carrito(request, session_key_previa=session_key_previa)
    badge = _carrito_badge(carrito)

    refresh = RefreshToken.for_user(user)

    return Response({
        "mensaje": "¡Registro exitoso! Bienvenido a Tribuna.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
        "badge": badge,
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Inicia sesión con usuario o correo y contraseña, devolviendo tokens JWT."""
    data = request.data or {}
    identificador = str(data.get("username") or "").strip()
    password = str(data.get("password") or "")

    if not identificador or not password:
        return Response({"error": "Debes ingresar tu usuario o correo y la contraseña."}, status=status.HTTP_400_BAD_REQUEST)

    # Permitir login con username o correo electrónico
    username_to_auth = identificador
    if "@" in identificador:
        user_by_email = User.objects.filter(email__iexact=identificador).first()
        if user_by_email:
            username_to_auth = user_by_email.username
        else:
            return Response({"error": "Credenciales inválidas. Verifica tu correo y contraseña."}, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(request, username=username_to_auth, password=password)

    if user is None:
        return Response({"error": "Credenciales inválidas. Verifica tus datos de acceso."}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({"error": "Esta cuenta está desactivada."}, status=status.HTTP_403_FORBIDDEN)

    session_key_previa = request.session.session_key
    django_login(request, user)
    from .carrito_views import _get_carrito, _carrito_badge
    carrito = _get_carrito(request, session_key_previa=session_key_previa)
    badge = _carrito_badge(carrito)

    refresh = RefreshToken.for_user(user)

    return Response({
        "mensaje": f"¡Hola de nuevo, {user.first_name or user.username}!",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
        "badge": badge,
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def logout(request):
    """Cierra la sesión de Django y resetea la sesión actual para no mezclar carritos."""
    django_logout(request)
    request.session.flush()
    return Response({"mensaje": "Sesión cerrada correctamente.", "badge": 0})


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def perfil(request):
    """Devuelve la información del usuario autenticado."""
    user = request.user
    return Response({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    })
