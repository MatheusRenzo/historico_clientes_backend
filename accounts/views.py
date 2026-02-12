from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserClienteMembership  # ajuste o import conforme seu app


User = get_user_model()


class LoginWithClienteView(APIView):
    permission_classes = [AllowAny]

    """
    POST /api/auth/login/
    Body:
    {
      "username": "thiago",   // pode ser username ou email
      "password": "123",
      "cliente": 1
    }
    """

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        cliente_id = request.data.get("cliente")

        if not username or not password or not cliente_id:
            return Response(
                {"detail": "Informe username, password e cliente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1) autenticação: tenta username; se falhar, tenta email
        user = authenticate(request, username=username, password=password)
        if user is None:
            # tenta por email (caso o front mande email no campo username)
            try:
                u = User.objects.get(email__iexact=username)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is None:
            return Response({"detail": "Credenciais inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"detail": "Usuário inativo."}, status=status.HTTP_403_FORBIDDEN)

        # 2) valida vínculo com o cliente + pega role
        membership = (
            UserClienteMembership.objects
            .select_related("cliente")
            .filter(user=user, cliente_id=int(cliente_id), ativo=True)
            .first()
        )
        if not membership:
            return Response(
                {"detail": "Usuário não possui acesso a este cliente."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 3) gera JWT
        refresh = RefreshToken.for_user(user)

        # 4) retorna payload para o front
        full_name = (user.get_full_name() or "").strip()
        if not full_name:
            # fallback: tenta primeiro nome do username
            full_name = user.username

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
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
            status=status.HTTP_200_OK,
        )
