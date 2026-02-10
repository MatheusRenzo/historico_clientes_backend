from rest_framework.routers import DefaultRouter
from .views import ParametroViewSet, ParametroClienteViewSet, ItensMonitoramentoViewSet, ContextoClienteViewSet

router = DefaultRouter()
router.register(r"parametros", ParametroViewSet, basename="parametros")
router.register(r"parametros-cliente", ParametroClienteViewSet, basename="parametros-cliente")
router.register(r"itens-monitoramento", ItensMonitoramentoViewSet, basename="itens-monitoramento")
router.register(r"contextos-cliente", ContextoClienteViewSet, basename="contextos")

urlpatterns = router.urls
