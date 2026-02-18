from django.db import transaction
from django.utils import timezone

from .models import ContratoTarefa, TarefaTimer, TarefaTimerPausa


def _sec_between(a, b):
    return int((b - a).total_seconds())


@transaction.atomic
def iniciar_timer(tarefa: ContratoTarefa, usuario, observacao: str | None = None) -> TarefaTimer:
    # opcional: impedir 2 timers rodando do mesmo usuário (mesmo em outra tarefa)
    # TarefaTimer.objects.select_for_update().filter(usuario=usuario, estado=TarefaTimer.Estado.RODANDO).exists()

    # impede timer rodando duplicado na mesma tarefa
    timer = (
        TarefaTimer.objects.select_for_update()
        .filter(tarefa=tarefa, usuario=usuario, estado__in=[TarefaTimer.Estado.RODANDO, TarefaTimer.Estado.PAUSADO])
        .first()
    )
    if timer:
        return timer

    timer = TarefaTimer.objects.create(
        tarefa=tarefa,
        usuario=usuario,
        estado=TarefaTimer.Estado.RODANDO,
        ultimo_inicio_em=timezone.now(),
        observacao=observacao,
    )

    # muda status da tarefa automaticamente
    if tarefa.status == ContratoTarefa.Status.ABERTA:
        tarefa.status = ContratoTarefa.Status.EM_ANDAMENTO
        tarefa.save(update_fields=["status", "atualizado_em"])

    return timer


@transaction.atomic
def pausar_timer(timer: TarefaTimer) -> TarefaTimer:
    if timer.estado != TarefaTimer.Estado.RODANDO:
        return timer

    now = timezone.now()

    # soma trabalho desde ultimo_inicio_em
    if timer.ultimo_inicio_em:
        timer.segundos_trabalhados += _sec_between(timer.ultimo_inicio_em, now)

    timer.estado = TarefaTimer.Estado.PAUSADO
    timer.ultimo_pause_em = now
    timer.ultimo_inicio_em = None
    timer.save()

    TarefaTimerPausa.objects.create(timer=timer, inicio=now)
    return timer


@transaction.atomic
def retomar_timer(timer: TarefaTimer) -> TarefaTimer:
    if timer.estado != TarefaTimer.Estado.PAUSADO:
        return timer

    now = timezone.now()

    # fecha última pausa aberta
    pausa = (
        TarefaTimerPausa.objects.select_for_update()
        .filter(timer=timer, fim__isnull=True)
        .order_by("-inicio")
        .first()
    )
    if pausa:
        pausa.fim = now
        pausa.save(update_fields=["fim"])
        timer.segundos_pausados += _sec_between(pausa.inicio, now)

    timer.estado = TarefaTimer.Estado.RODANDO
    timer.ultimo_inicio_em = now
    timer.ultimo_pause_em = None
    timer.save()
    return timer


@transaction.atomic
def finalizar_timer(timer: TarefaTimer, descricao_apontamento: str | None = None, concluir_tarefa: bool = True) -> dict:
    now = timezone.now()

    if timer.estado == TarefaTimer.Estado.RODANDO and timer.ultimo_inicio_em:
        timer.segundos_trabalhados += _sec_between(timer.ultimo_inicio_em, now)

    if timer.estado == TarefaTimer.Estado.PAUSADO:
        # fecha pausa aberta se existir
        pausa = (
            TarefaTimerPausa.objects.select_for_update()
            .filter(timer=timer, fim__isnull=True)
            .order_by("-inicio")
            .first()
        )
        if pausa:
            pausa.fim = now
            pausa.save(update_fields=["fim"])
            timer.segundos_pausados += _sec_between(pausa.inicio, now)

    timer.estado = TarefaTimer.Estado.FINALIZADO
    timer.finalizado_em = now
    timer.ultimo_inicio_em = None
    timer.ultimo_pause_em = None
    timer.save()

    # grava Apontamento em horas (Decimal)
    horas = round(timer.segundos_trabalhados / 3600, 2)

    #apont = Apontamento.objects.create(
    #    tarefa=timer.tarefa,
    #    data=now.date(),
    #    horas=horas,
    #    descricao=descricao_apontamento or f"Timer finalizado ({timer.segundos_trabalhados}s trabalhados)",
    #)

    if concluir_tarefa:
        timer.tarefa.status = ContratoTarefa.Status.CONCLUIDA
        timer.tarefa.save(update_fields=["status", "atualizado_em"])

    return {
        "timer_id": timer.id,
        #"apontamento_id": apont.id,
        "segundos_trabalhados": timer.segundos_trabalhados,
        "segundos_pausados": timer.segundos_pausados,
        "horas_lancadas": float(horas),
    }
