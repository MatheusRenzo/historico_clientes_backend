from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import RagDocument
from .serializers import RagDocumentSerializer
from .services import rag_answer, _FAISS_BY_CLIENTE

class RagDocumentViewSet(ModelViewSet):
    queryset = RagDocument.objects.select_related("cliente").all().order_by("-criado_em")
    serializer_class = RagDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {"cliente": ["exact"], "fonte": ["exact"]}

class RagAskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente_id = request.data.get("cliente")
        pergunta = request.data.get("pergunta")
        if not cliente_id or not pergunta:
            return Response({"detail": "Informe 'cliente' e 'pergunta'."}, status=400)

        # opcional: permitir rebuild do índice quando incluir docs novos
        if request.data.get("rebuild") is True:
            _FAISS_BY_CLIENTE.pop(int(cliente_id), None)

        result = rag_answer(int(cliente_id), str(pergunta))
        return Response(result)
