from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ZabbixConnectionViewSet, ZabbixHostsView, ZabbixProblemsView, ZabbixSyncLevel1View
from .views_level2 import ZabbixSyncItemsView, ZabbixSyncEventsView, ZabbixSyncHistoryView
from .views_level3 import ZabbixSyncTemplatesView, ZabbixSyncUsersView, ZabbixSyncSLAView
from .views_reporting import ZabbixMonthlyReportView
from .views_sla_ai import ZabbixSlaAnalyzeView
from .views_alarms import ZabbixSyncAlarmsView, ZabbixSyncAlertsSentView, ZabbixAlarmsListView, ZabbixAlarmEventsListView, ZabbixAlertsSentListView

router = DefaultRouter()
router.register(r"zabbix/connections", ZabbixConnectionViewSet, basename="zabbix-connections")

urlpatterns = [
    path("zabbix/hosts/", ZabbixHostsView.as_view(), name="zabbix-hosts"),
    path("zabbix/problems/", ZabbixProblemsView.as_view(), name="zabbix-problems"),
    path("zabbix/sync/level1/", ZabbixSyncLevel1View.as_view()),
    path("zabbix/sync/items/", ZabbixSyncItemsView.as_view()),
    path("zabbix/sync/events/", ZabbixSyncEventsView.as_view()),
    path("zabbix/sync/history/", ZabbixSyncHistoryView.as_view()),
    path("zabbix/sync/templates/", ZabbixSyncTemplatesView.as_view()),
    path("zabbix/sync/users/", ZabbixSyncUsersView.as_view()),
    path("zabbix/sync/sla/", ZabbixSyncSLAView.as_view()),
    path("zabbix/report/monthly/", ZabbixMonthlyReportView.as_view(), name="zabbix-monthly-report"),
    path("zabbix/sla/analyze/", ZabbixSlaAnalyzeView.as_view(), name="zabbix-sla-analyze"),
    path("zabbix/sync/alarms/", ZabbixSyncAlarmsView.as_view(), name="zabbix-sync-alarms"),
    path("zabbix/sync/alerts/", ZabbixSyncAlertsSentView.as_view(), name="zabbix-sync-alerts"),
    path("zabbix/alarms/", ZabbixAlarmsListView.as_view(), name="zabbix-alarms"),
    path("zabbix/alarm-events/", ZabbixAlarmEventsListView.as_view(), name="zabbix-alarm-events"),
    path("zabbix/alerts-sent/", ZabbixAlertsSentListView.as_view(), name="zabbix-alerts-sent"),

]
urlpatterns += router.urls
