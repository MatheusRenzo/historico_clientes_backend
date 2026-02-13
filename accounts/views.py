from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import UserClienteMembership, UserClienteRole  # ajuste o import conforme seu app
#from accounts.serializers import CreateUserWithClienteSerializer
from accounts.permissions import HasClienteRoleAtLeast

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

User = get_user_model()

class LoginWithClienteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        cliente_id = request.data.get("cliente")

        if not username or not password or not cliente_id:
            return Response(
                {"detail": "Informe username, password e cliente."},
                status=400,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            try:
                u = User.objects.get(email__iexact=username)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is None:
            return Response({"detail": "Credenciais inválidas."}, status=401)

        if not user.is_active:
            return Response({"detail": "Usuário inativo."}, status=403)

        membership = (
            UserClienteMembership.objects
            .select_related("cliente")
            .filter(user=user, cliente_id=int(cliente_id), ativo=True)
            .first()
        )

        if not membership:
            return Response(
                {"detail": "Usuário não possui acesso a este cliente."},
                status=403,
            )

        # ✅ Gera token usando o mesmo serializer do TokenObtainPairView
        serializer = TokenObtainPairSerializer(
            data={"username": user.username, "password": password}
        )
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data

        full_name = (user.get_full_name() or "").strip() or user.username

        return Response(
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": {
                    "id": user.id,
                    "nome": full_name,
                    "email": user.email,
                },
                "cliente": {
                    "id": membership.cliente_id,
                    "nome": membership.cliente.nome,
                },
                "role": membership.role,
            },
            status=200,
        )


class CreateUserView(APIView):
    """
    POST /api/auth/users/
    Cria usuário e vincula a um cliente com role.

    Body:
    {
      "username": "ana",
      "email": "ana@empresa.com",
      "nome": "Ana",
      "sobrenome": "Silva",
      "password": "Senha@123",
      "cliente": 1,
      "role": "ANALISTA"
    }
    """
    permission_classes = [IsAuthenticated, HasClienteRoleAtLeast.required(UserClienteRole.LIDER)]

    def post(self, request):
        ser = CreateUserWithClienteSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        user = ser.save()

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "nome": (user.get_full_name() or user.username).strip(),
                "cliente": int(request.data.get("cliente")),
                "role": request.data.get("role"),
            },
            status=status.HTTP_201_CREATED,
        )

class MeClientsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ms = (
            request.user.memberships
            .filter(ativo=True)
            .select_related("cliente")
            .order_by("cliente__nome")
        )
        return Response([
            {"cliente_id": m.cliente_id, "cliente_nome": m.cliente.nome, "role": m.role}
            for m in ms
        ])
