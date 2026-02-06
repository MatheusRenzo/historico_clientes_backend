from parametro.models import ParametroCliente


def get_parametro_cliente(cliente_id: int, nome_parametro: str, default=None):
    """
    Retorna o valor de um parâmetro de um cliente.

    :param cliente_id: ID do cliente
    :param nome_parametro: Nome do parâmetro
    :param default: Valor retornado se não encontrar
    """
    try:
        return (
            ParametroCliente.objects
            .only("valor")
            .get(cliente_id=cliente_id, nome=nome_parametro)
            .valor
        )
    except ParametroCliente.DoesNotExist:
        return default
