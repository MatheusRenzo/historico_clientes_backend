from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ZabbixConnectionViewSet, ZabbixHostsView, ZabbixProblemsView, ZabbixSyncLevel1View
from .views_level2 import ZabbixSyncItemsView, ZabbixSyncEventsView, ZabbixSyncHistoryView

router = DefaultRouter()
router.register(r"zabbix/connections", ZabbixConnectionViewSet, basename="zabbix-connections")

urlpatterns = [
    path("zabbix/hosts/", ZabbixHostsView.as_view(), name="zabbix-hosts"),
    path("zabbix/problems/", ZabbixProblemsView.as_view(), name="zabbix-problems"),
    path("zabbix/sync/level1/", ZabbixSyncLevel1View.as_view()),
    path("zabbix/sync/items/", ZabbixSyncItemsView.as_view()),
    path("zabbix/sync/events/", ZabbixSyncEventsView.as_view()),
    path("zabbix/sync/history/", ZabbixSyncHistoryView.as_view()),
]
urlpatterns += router.urls
