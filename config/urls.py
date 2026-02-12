from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from clientes.views import ClienteViewSet
from contratos.views import ContratoViewSet
from tarefas.views import TarefaViewSet, ApontamentoViewSet
from auth_api import views as auth_views

router = DefaultRouter()
router.register(r"clientes", ClienteViewSet)
router.register(r"contratos", ContratoViewSet)
router.register(r"tarefas", TarefaViewSet)
router.register(r"apontamentos", ApontamentoViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    #path("api/auth/", include("auth_api.urls")),
    path("api/", include("parametro.urls")),
    path("api/", include("contratos.urls")),
    path("api/", include("tarefas.urls")),
    path("api/", include("jira_sync.urls")),
    path("api/", include("rag.urls")),
    path("api/", include("zabbix_integration.urls")),
    path("api/", include("accounts.urls")),

]
