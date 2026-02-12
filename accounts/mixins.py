from accounts.tenant import get_cliente_context

class ClienteQuerysetMixin:
    """
    Aplica filtro automatico por cliente no queryset.
    O model precisa ter field 'cliente'.
    """

    def get_cliente(self):
        cliente, _ = get_cliente_context(self.request)
        return cliente

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(cliente=self.get_cliente())
