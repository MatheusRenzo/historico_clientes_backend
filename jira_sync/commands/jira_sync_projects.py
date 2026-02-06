from django.core.management.base import BaseCommand
from jira_sync.services.sync import sync_projects_for_cliente


class Command(BaseCommand):
    help = "Sincroniza projetos do Jira para um cliente (via JiraConnection)."

    def add_arguments(self, parser):
        parser.add_argument("--cliente", type=int, required=True)

    def handle(self, *args, **options):
        cliente_id = options["cliente"]
        result = sync_projects_for_cliente(cliente_id)
        self.stdout.write(self.style.SUCCESS(f"OK: {result}"))
