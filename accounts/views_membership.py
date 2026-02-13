from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from accounts.models import UserClienteMembership, UserClienteRole
from django.contrib.auth import get_user_model

User = get_user_model()


class AddMembershipView(APIView):
    """
    POST /api/auth/users/{user_id}/memberships/
    Body: {"cliente": 1, "role": "ANALISTA"}
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, user_id: int):
        cliente = request.data.get("cliente")
        role = request.data.get("role")

        if not cliente or not role:
            return Response({"detail": "Informe cliente e role."}, status=400)

        user = User.objects.get(id=user_id)

        obj, created = UserClienteMembership.objects.update_or_create(
            user=user,
            cliente_id=int(cliente),
            defaults={"role": role, "ativo": True},
        )

        return Response(
            {"user_id": user.id, "cliente": obj.cliente_id, "role": obj.role, "ativo": obj.ativo},
            status=201 if created else 200,
        )
