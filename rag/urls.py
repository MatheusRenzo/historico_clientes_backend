from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import RagDocumentViewSet, RagAskView

router = DefaultRouter()
router.register(r"rag/docs", RagDocumentViewSet, basename="rag-docs")

urlpatterns = [
    path("rag/ask/", RagAskView.as_view(), name="rag-ask"),
]
urlpatterns += router.urls
