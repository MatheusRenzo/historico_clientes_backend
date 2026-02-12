from rest_framework.permissions import BasePermission
from accounts.tenant import get_cliente_context
from accounts.models import UserClienteRole

ROLE_RANK = {
    UserClienteRole.ANALISTA: 1,
    UserClienteRole.GERENTE_PROJETO: 2,
    UserClienteRole.LIDER: 3,
}

class HasClienteRoleAtLeast(BasePermission):
    """
    Ex.: permission_classes = [IsAuthenticated, HasClienteRoleAtLeast.required(UserClienteRole.GERENTE_PROJETO)]
    """

    required_role = UserClienteRole.ANALISTA

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        _, role = get_cliente_context(request)
        return ROLE_RANK.get(role, 0) >= ROLE_RANK.get(self.required_role, 0)

    @classmethod
    def required(cls, role):
        # cria uma classe “configurada”
        return type(f"HasRoleAtLeast_{role}", (cls,), {"required_role": role})
