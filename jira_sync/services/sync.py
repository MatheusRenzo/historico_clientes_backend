from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils.dateparse import parse_datetime, parse_date

from jira_sync.models import JiraConnection, JiraProject, JiraIssue
from jira_sync.services.jira_client_api import JiraClient

from parametro.services import get_parametro_cliente



def _safe_dt(value: str | None):
    if not value:
        return None
    # Jira devolve ISO com timezone, parse_datetime lida bem
    return parse_datetime(value)


def _safe_date(value: str | None):
    if not value:
        return None
    return parse_date(value)


def sync_projects_for_cliente(cliente_id: int) -> dict:
    """
    Sincroniza projetos do Jira para a conexão do cliente.
    """
    conn = JiraConnection.objects.select_related("cliente").get(cliente_id=cliente_id, ativo=True)
    print("Conexão: " + conn.base_url)
    prefixo_api_jira = get_parametro_cliente(1, "prefixo_api_jira")
    Jira_Id = get_parametro_cliente(1, "Jira_Id")
    baseurl = conn.base_url #f"{prefixo_api_jira}{Jira_Id}"
    print("baseurl: " + baseurl)
    email_user = get_parametro_cliente(1, "jira_user_name")
    apitoken = get_parametro_cliente(1, "jira_password")


    client = JiraClient(
        base_url=baseurl,
        email=email_user,
        api_token=apitoken,
    )
    print(baseurl)
    print(email_user)
    #print(apitoken)
    #print(client)
    upserted = 0
    created = 0

    with transaction.atomic():
        for p in client.iter_projects(max_results=50):
            # Campos do endpoint /project/search
            jira_id = str(p.get("id"))
            key = p.get("key")
            name = p.get("name")

            if not key or not name or not jira_id:
                continue

            lead = p.get("lead") or {}
            is_private = bool(p.get("isPrivate") or False)
            archived = bool(p.get("archived") or False)
            project_type = p.get("projectTypeKey") or p.get("projectType")  # depende do retorno
            url = p.get("self")

            obj, was_created = JiraProject.objects.update_or_create(
                jira_connection=conn,
                key=key,
                defaults={
                    "jira_id": jira_id,
                    "name": name,
                    "project_type": project_type,
                    "is_private": is_private,
                    "archived": archived,
                    "lead_account_id": lead.get("accountId"),
                    "lead_display_name": lead.get("displayName"),
                    "url": url,
                    "raw": p,
                },
            )

            upserted += 1
            if was_created:
                created += 1

    return {"cliente_id": cliente_id, "upserted": upserted, "created": created}


def sync_issues_for_cliente(cliente_id: int, jql: str, contrato_id: int | None = None) -> dict:
    """
    Sincroniza issues do Jira usando um JQL e grava em JiraIssue.
    - cliente_id: define a conexão JiraConnection
    - jql: consulta Jira (ex: 'project=ENG order by updated desc')
    - contrato_id: opcional (mapeia tudo para um contrato específico)
    """
    conn = JiraConnection.objects.select_related("cliente").get(cliente_id=cliente_id, ativo=True)
    client = JiraClient(conn.base_url, conn.email, conn.api_token)

    upserted = 0
    created = 0

    # contrato opcional (evita buscar sempre)
    contrato = None
    if contrato_id:
        from contratos.models import Contrato
        contrato = Contrato.objects.get(id=contrato_id)

    with transaction.atomic():
        for issue in client.iter_issues(jql=jql, max_results=50):
            jira_id = str(issue.get("id"))
            key = issue.get("key")
            fields = issue.get("fields") or {}

            if not jira_id or not key:
                continue

            project = fields.get("project") or {}
            issuetype = fields.get("issuetype") or {}
            status = (fields.get("status") or {}).get("name")
            priority = (fields.get("priority") or {}).get("name")

            assignee = fields.get("assignee") or {}
            reporter = fields.get("reporter") or {}

            summary = fields.get("summary") or ""
            description = fields.get("description")

            labels = fields.get("labels")
            components = fields.get("components")
            components_names = [c.get("name") for c in (components or []) if c.get("name")]

            jira_created_at = _safe_dt(fields.get("created"))
            jira_updated_at = _safe_dt(fields.get("updated"))
            jira_resolved_at = _safe_dt(fields.get("resolutiondate"))
            due_date = _safe_date(fields.get("duedate"))

            # Tempo: alguns campos podem vir em fields['timetracking'] e/ou em seconds
            timetracking = fields.get("timetracking") or {}
            original_est = fields.get("timeoriginalestimate") or timetracking.get("originalEstimateSeconds")
            time_spent = fields.get("timespent") or timetracking.get("timeSpentSeconds")

            defaults = {
                "cliente_id": cliente_id,
                "contrato": contrato,  # pode ser None
                "project_key": project.get("key"),
                "issue_type": issuetype.get("name"),
                "summary": summary[:255],
                "description": description,
                "status": status,
                "priority": priority,
                "assignee_account_id": assignee.get("accountId"),
                "assignee_display_name": assignee.get("displayName"),
                "reporter_account_id": reporter.get("accountId"),
                "reporter_display_name": reporter.get("displayName"),
                "labels": labels,
                "components": components_names,
                "raw": issue,
                "jira_created_at": jira_created_at,
                "jira_updated_at": jira_updated_at,
                "jira_resolved_at": jira_resolved_at,
                "due_date": due_date,
                "original_estimate_seconds": original_est,
                "time_spent_seconds": time_spent,
            }

            obj, was_created = JiraIssue.objects.update_or_create(
                jira_id=jira_id,
                defaults={**defaults, "key": key},  # garante key atualizado
            )

            upserted += 1
            if was_created:
                created += 1

    return {"cliente_id": cliente_id, "jql": jql, "upserted": upserted, "created": created}
