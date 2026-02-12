from rest_framework.exceptions import PermissionDenied
from accounts.models import UserClienteMembership

def get_cliente_context(request):
    cliente_id = request.headers.get("X-Cliente-Id") or request.query_params.get("cliente")
    if not cliente_id:
        raise PermissionDenied("Informe o cliente via header X-Cliente-Id ou query ?cliente=ID.")

    m = UserClienteMembership.objects.filter(
        user=request.user,
        cliente_id=int(cliente_id),
        ativo=True,
    ).select_related("cliente").first()

    if not m:
        raise PermissionDenied("Usuário não possui acesso a este cliente.")

    return m.cliente, m.role
