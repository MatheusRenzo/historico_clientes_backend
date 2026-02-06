from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated  # ou IsAdminUser

from jira_sync.services.sync import sync_projects_for_cliente, sync_issues_for_cliente


class JiraSyncProjectsView(APIView):
    """
    POST /api/jira/sync/projects/
    Body: {"cliente": 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente_id = request.data.get("cliente")
        print(cliente_id)
        if not cliente_id:
            return Response(
                {"detail": "Campo 'cliente' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            print('2')
            result = sync_projects_for_cliente(int(cliente_id))
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JiraSyncIssuesView(APIView):
    """
    POST /api/jira/sync/issues/
    Body: {"cliente": 1, "jql": "project=ENG order by updated desc", "contrato": 10 (opcional)}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente_id = request.data.get("cliente")
        jql = request.data.get("jql")
        contrato_id = request.data.get("contrato")  # opcional

        if not cliente_id:
            return Response(
                {"detail": "Campo 'cliente' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not jql:
            return Response(
                {"detail": "Campo 'jql' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = sync_issues_for_cliente(
                cliente_id=int(cliente_id),
                jql=str(jql),
                contrato_id=int(contrato_id) if contrato_id else None,
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
