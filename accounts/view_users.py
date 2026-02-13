from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from accounts.serializers import CreateUserWithMembershipsSerializer


class CreateUserMultiClienteView(APIView):
    """
    POST /api/auth/users/
    Cria usuário e vincula a múltiplos clientes com roles.

    Body:
    {
      "username": "ana.silva",
      "email": "ana@empresa.com",
      "nome": "Ana",
      "sobrenome": "Silva",
      "password": "Senha@123",
      "memberships": [
        {"cliente": 1, "role": "ANALISTA"},
        {"cliente": 2, "role": "GERENTE_PROJETO"}
      ]
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        ser = CreateUserWithMembershipsSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "nome": (user.get_full_name() or user.username).strip(),
                "memberships": [
                    {"cliente": m.cliente_id, "role": m.role, "ativo": m.ativo}
                    for m in user.memberships.all().order_by("cliente_id")
                ],
            },
            status=status.HTTP_201_CREATED,
        )
