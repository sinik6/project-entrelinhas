"""[010] O disparador: 21h30, quem já entregou, uma vez por dia, 404/410, janela até 23h00, falha sem repetir, texto, oráculo."""

import json
import logging
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pytest
from django.db import connections

from apps.lembretes import disparador
from apps.lembretes.models import AssinaturaPush, LembreteEnviado

from .conftest import entregou, sp


def rodar(agora, envio):
    return disparador.enviar_lembretes(agora, envio)


def test_req_19_1_as_21h30_envia_a_quem_ainda_nao_entregou(pessoas, envio):
    """[010] REQ-19.1."""
    ana, bia = pessoas("ana"), pessoas("bia")

    resumo = rodar(sp(2026, 11, 5, 21, 30), envio)

    assert envio.usuarios == sorted([ana.pk, bia.pk])
    assert resumo["enviados"] == 2


def test_req_19_1_antes_das_21h30_nao_envia_nada(pessoas, envio):
    """[010] REQ-19.1: 21h29min59s ainda é cedo."""
    pessoas("ana")

    rodar(sp(2026, 11, 5, 21, 29, 59), envio)

    assert envio.chamadas == []
    assert LembreteEnviado.objects.count() == 0


def test_req_19_5_ate_as_23h_envia_atrasado_e_depois_pula_o_dia(pessoas, envio):
    """[010] REQ-19.5: 22h59min59s envia; 23h00 pula."""
    pessoas("ana")

    rodar(sp(2026, 11, 5, 23, 0, 0), envio)
    assert envio.chamadas == []
    rodar(sp(2026, 11, 5, 22, 59, 59), envio)
    assert len(envio.chamadas) == 1


def test_req_19_2_quem_ja_entregou_o_dia_nao_recebe(pessoas, envio):
    """[010] REQ-19.2."""
    ana, bia = pessoas("ana"), pessoas("bia")
    entregou(ana, date(2026, 11, 5))

    rodar(sp(2026, 11, 5, 21, 30), envio)

    assert envio.usuarios == [bia.pk]
    assert not LembreteEnviado.objects.filter(usuario=ana).exists(), (
        "quem já entregou nem é marcado"
    )


def test_req_19_2_entrega_de_outro_dia_nao_conta(pessoas, envio):
    """[010] REQ-19.2: só o registro do dia (em São Paulo) dispensa o aviso."""
    ana = pessoas("ana")
    entregou(ana, date(2026, 11, 4))

    rodar(sp(2026, 11, 5, 21, 30), envio)

    assert envio.usuarios == [ana.pk]


def test_req_19_2_21h30_de_sao_paulo_ja_e_o_dia_seguinte_no_utc(pessoas, envio):
    """[010] REQ-19.2: 21h30 de 05/11 em SP é 00h30 UTC de 06/11; o dia que vale é o de São Paulo."""
    ana = pessoas("ana")
    entregou(ana, date(2026, 11, 5))

    rodar(sp(2026, 11, 5, 21, 30).astimezone(__import__("datetime").timezone.utc), envio)

    assert envio.chamadas == []


def test_req_19_3_so_um_aviso_por_pessoa_por_dia(pessoas, envio):
    """[010] REQ-19.3: segunda execução no mesmo dia não envia nada."""
    pessoas("ana")

    primeira = rodar(sp(2026, 11, 5, 21, 30), envio)
    segunda = rodar(sp(2026, 11, 5, 22, 0), envio)

    assert primeira["enviados"] == 1 and segunda["enviados"] == 0
    assert len(envio.chamadas) == 1


def test_req_19_3_no_dia_seguinte_envia_de_novo(pessoas, envio):
    """[010] REQ-19.3: a trava é por dia."""
    pessoas("ana")

    rodar(sp(2026, 11, 5, 21, 30), envio)
    rodar(sp(2026, 11, 6, 21, 30), envio)

    assert len(envio.chamadas) == 2


def test_req_19_1_cada_aparelho_da_pessoa_recebe(pessoas, envio):
    """[010] REQ-19.1: 3 aparelhos, 3 envios, uma marca de dia."""
    pessoas("ana", n_assinaturas=3)

    resumo = rodar(sp(2026, 11, 5, 21, 30), envio)

    assert len(envio.chamadas) == 3 and resumo["enviados"] == 3
    assert LembreteEnviado.objects.count() == 1


def test_req_19_1_quem_nao_tem_grupo_nao_recebe(pessoas, envio):
    """[010] REQ-19.1: sem grupo não há o que entregar."""
    pessoas("solo", com_grupo=False)

    rodar(sp(2026, 11, 5, 21, 30), envio)

    assert envio.chamadas == []


def test_req_19_4_assinatura_inexistente_no_servico_de_push_e_removida(pessoas, envio):
    """[010] REQ-19.4: 404 ou 410 do serviço de push."""
    pessoas("ana", n_assinaturas=2)
    envio.respostas["https://fcm.googleapis.com/fcm/send/ana-0"] = "gone"

    resumo = rodar(sp(2026, 11, 5, 21, 30), envio)

    assert resumo["removidos"] == 1 and resumo["enviados"] == 1
    assert [a.endpoint for a in AssinaturaPush.objects.all()] == [
        "https://fcm.googleapis.com/fcm/send/ana-1"
    ]


def test_req_19_8_falha_de_um_aparelho_nao_para_os_outros_e_nao_repete_no_dia(
    pessoas, envio, caplog
):
    """[010] REQ-19.8: erro de rede num aparelho; o outro recebe; a segunda execução não tenta de novo."""
    pessoas("ana", n_assinaturas=2)
    envio.respostas["https://fcm.googleapis.com/fcm/send/ana-0"] = "falha"

    with caplog.at_level(logging.DEBUG):
        resumo = rodar(sp(2026, 11, 5, 21, 30), envio)
        rodar(sp(2026, 11, 5, 21, 40), envio)

    assert resumo["falhas"] == 1 and resumo["enviados"] == 1
    assert len(envio.chamadas) == 2
    assert AssinaturaPush.objects.count() == 2, "falha comum não apaga a assinatura"
    registrado = "\n".join(r.getMessage() for r in caplog.records)
    assert "fcm.googleapis.com" not in registrado, "endereço do aparelho não vai ao log"


def test_req_19_8_excecao_inesperada_no_envio_e_contada_como_falha(pessoas, envio):
    """[010] REQ-19.8: o disparador não cai por causa de um aparelho."""
    pessoas("ana", n_assinaturas=2)
    envio.respostas["https://fcm.googleapis.com/fcm/send/ana-0"] = RuntimeError("explodiu")

    resumo = rodar(sp(2026, 11, 5, 21, 30), envio)

    assert resumo["falhas"] == 1 and resumo["enviados"] == 1


def test_req_19_6_a_carga_e_generica_sem_nome_texto_nem_parceiro(pessoas, envio):
    """[010] REQ-19.6 / CTL-85: só título, corpo genérico e o endereço da tela Hoje."""
    ana, bia = pessoas("ana"), pessoas("bia")
    entregou(bia, date(2026, 11, 5))

    rodar(sp(2026, 11, 5, 21, 30), envio)

    carga = envio.chamadas[0][2]
    assert json.loads(carga) == {
        "titulo": "Entrelinhas",
        "corpo": "Hora de escrever o seu dia.",
        "url": "#/hoje",
    }
    for proibido in ("Ana", "Bia", "registro de teste", ana.email, bia.email):
        assert proibido not in carga


@pytest.mark.django_db(transaction=True)
def test_abu_23_dois_processos_ao_mesmo_tempo_nao_duplicam_avisos(pessoas, envio):
    """[010] ABU-23 / REQ-19.3: 6 execuções simultâneas (threads reais); cada pessoa recebe uma vez."""
    pessoas("ana"), pessoas("bia")
    largada = threading.Barrier(6)

    def tentar(_):
        try:
            largada.wait(timeout=20)
            return rodar(sp(2026, 11, 5, 21, 30), envio)["enviados"]
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=6) as pool:
        total = sum(pool.map(tentar, range(6)))

    assert total == 2
    assert len(envio.chamadas) == 2
    assert LembreteEnviado.objects.count() == 2


def test_abu_23_reinicio_no_meio_do_envio_nao_repete_quem_ja_foi_marcado(pessoas, envio):
    """[010] ABU-23: o processo morre no meio (a marca do dia já estava no banco); ao voltar, ninguém repete."""
    ana, bia = pessoas("ana"), pessoas("bia")
    chamadas = []

    def morre_no_segundo(assinatura, carga):
        chamadas.append(assinatura.usuario_id)
        if len(chamadas) == 2:
            raise KeyboardInterrupt  # não é Exception: imita o processo sendo derrubado

    with pytest.raises(KeyboardInterrupt):
        rodar(sp(2026, 11, 5, 21, 30), morre_no_segundo)
    primeira_ordem = list(chamadas)

    rodar(sp(2026, 11, 5, 21, 35), envio)

    assert len(primeira_ordem) == 2
    assert envio.chamadas == [], "as duas pessoas já estavam marcadas; ninguém recebe duas vezes"
    assert {ana.pk, bia.pk} == set(LembreteEnviado.objects.values_list("usuario_id", flat=True))


def test_limpeza_apaga_marcas_com_mais_de_30_dias(pessoas):
    """[010] LGPD: retenção de 30 dias do registro de envio."""
    ana = pessoas("ana")
    LembreteEnviado.objects.create(usuario=ana, data=date(2026, 9, 1))
    LembreteEnviado.objects.create(usuario=ana, data=date(2026, 10, 20))

    apagadas = disparador.limpar_marcas_antigas(date(2026, 11, 5))

    assert apagadas == 1
    assert LembreteEnviado.objects.count() == 1


def oraculo(pessoas_dados, agora):
    """Definição direta das regras 19.1, 19.2 e 19.5, escrita de outro jeito."""
    hora = agora.hour * 60 + agora.minute
    if not (21 * 60 + 30 <= hora < 23 * 60):
        return set()
    return {
        nome
        for nome, (n_aparelhos, entregou_hoje, _) in pessoas_dados.items()
        if n_aparelhos > 0 and not entregou_hoje
    }


def test_prop_13_o_conjunto_enviado_bate_com_o_oraculo_e_a_segunda_rodada_envia_vazio(
    pessoas, envio
):
    """[010] PROP-13: 60 cenários sorteados (semente fixa), instantes dentro e fora da janela."""
    r = random.Random(1330)
    base_nome = 0
    for rodada in range(60):
        AssinaturaPush.objects.all().delete()
        LembreteEnviado.objects.all().delete()
        from apps.registros.models import Registro

        Registro.objects.all().delete()
        envio.chamadas.clear()
        dia = date(2026, 11, 1) + timedelta(days=rodada % 20)
        dados = {}
        usuarios = {}
        for _ in range(r.randrange(1, 4)):
            base_nome += 1
            nome = f"p{base_nome}"
            n = r.choice([0, 1, 2])
            u = pessoas(nome, n_assinaturas=n)
            ja = r.random() < 0.4
            if ja:
                entregou(u, dia)
            dados[nome] = (n, ja, u)
            usuarios[nome] = u
        agora = sp(
            dia.year,
            dia.month,
            dia.day,
            r.choice([9, 21, 21, 22, 22, 23, 0]),
            r.choice([0, 29, 30, 31, 59]),
        )
        if agora.hour == 0:
            agora = agora + timedelta(
                days=1
            )  # 00h do dia seguinte: outro dia, sem registro: fora da janela

        rodar(agora, envio)

        enviados = {n for n, (_, _, u) in dados.items() if u.pk in envio.usuarios}
        esperado = set() if agora.date() != dia else oraculo(dados, agora)
        assert enviados == esperado, (rodada, agora, dados)
        envio.chamadas.clear()
        rodar(agora, envio)
        assert envio.chamadas == [], "a segunda execução não repete"
