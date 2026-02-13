from django.conf import settings
from django.db import models
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class UserClienteRole(models.TextChoices):
    LIDER = "LIDER", "Líder"
    GERENTE_PROJETO = "GERENTE_PROJETO", "Gerente de Projeto"
    ANALISTA = "ANALISTA", "Analista"


class UserClienteMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=30, choices=UserClienteRole.choices, default=UserClienteRole.ANALISTA)
    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "cliente")
        indexes = [
            models.Index(fields=["user", "ativo"]),
            models.Index(fields=["cliente", "role", "ativo"]),
        ]

    def __str__(self):
        return f"{self.user} -> {self.cliente} ({self.role})"

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