from django.db import models

class RagDocument(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE, related_name="rag_docs")
    titulo = models.CharField(max_length=255)
    conteudo = models.TextField()

    fonte = models.CharField(max_length=255, blank=True, null=True)  # ex: "wiki", "pdf", "jira"
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.titulo}"
