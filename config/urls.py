from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from clientes.views import ClienteViewSet
from contratos.views import ContratoViewSet, ContratoTarefaViewSet
from tarefas.views import TarefaViewSet, ApontamentoViewSet
from auth_api import views as auth_views

router = DefaultRouter()
router.register(r"clientes", ClienteViewSet)
router.register(r"contratos", ContratoViewSet)
router.register(r"contratos-tarefas", ContratoTarefaViewSet)
#router.register(r"tarefas", TarefaViewSet)
router.register(r"tarefas", TarefaViewSet, basename="tarefas")
router.register(r"apontamentos", ApontamentoViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/auth/", include("auth_api.urls")),
    path("api/", include("parametro.urls")),
    #path("api/", include("contratos.urls")),
    #path("api/", include("tarefas.urls")),
    path("api/", include("jira_sync.urls")),
    path("api/", include("rag.urls")),
    path("api/", include("zabbix_integration.urls")),
    path("api/", include("accounts.urls")),
    path("api/", include("contratos.analytics.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)