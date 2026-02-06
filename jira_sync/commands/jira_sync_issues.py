from django.core.management.base import BaseCommand
from jira_sync.services.sync import sync_issues_for_cliente


class Command(BaseCommand):
    help = "Sincroniza issues do Jira por JQL para um cliente."

    def add_arguments(self, parser):
        parser.add_argument("--cliente", type=int, required=True)
        parser.add_argument("--jql", type=str, required=True)
        parser.add_argument("--contrato", type=int, required=False)

    def handle(self, *args, **options):
        cliente_id = options["cliente"]
        jql = options["jql"]
        contrato_id = options.get("contrato")

        result = sync_issues_for_cliente(cliente_id, jql=jql, contrato_id=contrato_id)
        self.stdout.write(self.style.SUCCESS(f"OK: {result}"))
