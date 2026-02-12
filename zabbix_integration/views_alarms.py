from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from zabbix_integration.services.alarms_sync import (
    sync_active_alarms,
    sync_alarm_events,
    sync_alerts_sent,
)

from zabbix_integration.models import ZabbixAlarm, ZabbixAlarmEvent, ZabbixAlertSent


class ZabbixSyncAlarmsView(APIView):
    """
    POST /api/zabbix/sync/alarms/
    Body: {"cliente": 1, "since_hours": 24}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente = request.data.get("cliente")
        since_hours = int(request.data.get("since_hours", 24))
        if not cliente:
            return Response({"detail": "cliente é obrigatório"}, status=400)

        r1 = sync_active_alarms(int(cliente), since_hours=since_hours)
        r2 = sync_alarm_events(int(cliente), since_hours=since_hours)
        return Response({"status": "ok", **r1, **r2})


class ZabbixSyncAlertsSentView(APIView):
    """
    POST /api/zabbix/sync/alerts/
    Body: {"cliente": 1, "since_hours": 24}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente = request.data.get("cliente")
        since_hours = int(request.data.get("since_hours", 24))
        if not cliente:
            return Response({"detail": "cliente é obrigatório"}, status=400)

        r = sync_alerts_sent(int(cliente), since_hours=since_hours)
        return Response({"status": "ok", **r})


class ZabbixAlarmsListView(APIView):
    """
    GET /api/zabbix/alarms/?cliente=1
    Retorna alarmes ATIVOS no seu banco.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cliente = request.query_params.get("cliente")
        if not cliente:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        qs = ZabbixAlarm.objects.filter(cliente_id=int(cliente)).order_by("-clock")[:500]
        data = [
            {
                "eventid": a.eventid,
                "name": a.name,
                "severity": a.severity,
                "acknowledged": a.acknowledged,
                "clock": a.clock.isoformat(),
                "hostid": a.hostid,
                "hostname": a.hostname,
            }
            for a in qs
        ]
        return Response(data)


class ZabbixAlarmEventsListView(APIView):
    """
    GET /api/zabbix/alarm-events/?cliente=1
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cliente = request.query_params.get("cliente")
        if not cliente:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        qs = ZabbixAlarmEvent.objects.filter(cliente_id=int(cliente)).order_by("-clock")[:500]
        data = [
            {
                "eventid": e.eventid,
                "name": e.name,
                "severity": e.severity,
                "acknowledged": e.acknowledged,
                "clock": e.clock.isoformat(),
                "hostid": e.hostid,
                "hostname": e.hostname,
            }
            for e in qs
        ]
        return Response(data)


class ZabbixAlertsSentListView(APIView):
    """
    (Opcional) GET /api/zabbix/alerts-sent/?cliente=1
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cliente = request.query_params.get("cliente")
        if not cliente:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        qs = ZabbixAlertSent.objects.filter(cliente_id=int(cliente)).order_by("-clock")[:500]
        data = [
            {
                "alertid": a.alertid,
                "eventid": a.eventid,
                "clock": a.clock.isoformat(),
                "sendto": a.sendto,
                "subject": a.subject,
                "status": a.status,
            }
            for a in qs
        ]
        return Response(data)
