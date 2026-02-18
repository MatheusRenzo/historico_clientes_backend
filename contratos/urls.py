from django.urls import path
from .views_pdf import AnalisarContratoPDFView

urlpatterns = [
    path("contratos/<int:pk>/analisar-pdf/", AnalisarContratoPDFView.as_view(), name="analisar-contrato-pdf"),

]
