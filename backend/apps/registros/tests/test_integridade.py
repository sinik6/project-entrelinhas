"""[005] O banco garante o que a aplicação garante, e a limpeza de fotos não apaga o que uma entrega acabou de anexar (auditoria da 005)."""

import threading
from datetime import date
from types import SimpleNamespace

import pytest
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from apps.acesso.models import Perfil
from apps.fotos.models import Foto
from apps.registros import services
from apps.registros.models import Registro

from .conftest import entregar, foto_manuscrito


def _grupo_e_autor(dono):
    perfil = Perfil.objects.get(usuario__email="dono@example.com")
    return perfil.grupo, perfil.usuario


def _criar(dono, **extra):
    grupo, autor = _grupo_e_autor(dono)
    dados = {
        "grupo": grupo,
        "autor": autor,
        "data": date(2026, 11, 5),
        "texto": "x" * 20,
        "visibilidade": "full",
        "entregue_em": timezone.now(),
    }
    dados.update(extra)
    with transaction.atomic():
        return Registro.objects.create(**dados)


def test_ctl_34_banco_recusa_visibilidade_desconhecida(dono):
    """[005] CTL-34: `visibilidade` fora de full, private e partial não entra, nem por fora da aplicação."""
    with pytest.raises(IntegrityError):
        _criar(dono, visibilidade="secreto")


def test_ctl_38_banco_recusa_trecho_alem_do_texto_em_pontos_de_codigo(dono):
    """[005] CTL-38: o trecho cabe no texto; o PostgreSQL em UTF8 conta pontos de código (emoji é 1)."""
    with pytest.raises(IntegrityError):
        _criar(dono, visibilidade="partial", trecho_inicio=0, trecho_fim=21)
    assert _criar(dono, visibilidade="partial", trecho_inicio=0, trecho_fim=20).pk
    emoji = _criar(
        dono,
        data=date(2026, 11, 6),
        texto="😀" * 12,
        visibilidade="partial",
        trecho_inicio=0,
        trecho_fim=12,
    )
    assert emoji.pk
    with pytest.raises(IntegrityError):
        _criar(
            dono,
            data=date(2026, 11, 7),
            texto="😀" * 12,
            visibilidade="partial",
            trecho_inicio=0,
            trecho_fim=13,
        )


def test_ctl_38_banco_recusa_trecho_fora_do_partial_e_trecho_vazio(dono):
    """[005] CTL-38: trecho só em `partial`, com fim maior que o início."""
    with pytest.raises(IntegrityError):
        _criar(dono, visibilidade="full", trecho_inicio=0, trecho_fim=5)
    with pytest.raises(IntegrityError):
        _criar(dono, visibilidade="partial", trecho_inicio=5, trecho_fim=5)
    with pytest.raises(IntegrityError):
        _criar(dono, visibilidade="partial")


def test_ctl_36_banco_recusa_foto_com_registro_que_nao_esta_anexada(dono):
    """[005] CTL-36: foto num registro conta como anexada."""
    registro = _criar(dono)
    foto = foto_manuscrito(dono)

    with pytest.raises(IntegrityError), transaction.atomic():
        Foto.objects.filter(pk=foto).update(registro=registro, anexada=False)
    Foto.objects.filter(pk=foto).update(registro=registro, anexada=True)


def test_req_8_5_o_ramo_do_integrity_error_tambem_responde_409(dono, relogio, monkeypatch):
    """[005] REQ-8.5 / CTL-34: se a checagem prévia não enxergar o registro do dia, a restrição do banco ainda dá 409."""
    relogio.fixar(2026, 11, 5, 15)
    assert entregar(dono).status_code == 201
    real = Registro.objects

    class SemEnxergar:
        def filter(self, *args, **kwargs):
            return SimpleNamespace(exists=lambda: False)

        def create(self, **kwargs):
            return real.create(**kwargs)

    monkeypatch.setattr(services.Registro, "objects", SemEnxergar())
    foto = foto_manuscrito(dono)

    resposta = entregar(dono, fotos=[foto])

    assert resposta.status_code == 409
    assert resposta.json() == {"detalhe": "Você já entregou o registro de hoje."}
    assert Foto.objects.get(pk=foto).anexada is False


@pytest.mark.django_db(transaction=True)
def test_req_6_9_limpeza_nao_apaga_foto_que_outro_processo_esta_anexando(dono, pasta_de_fotos):
    """[005] REQ-6.9: com a foto travada por uma entrega em andamento, a limpeza a deixa (skip locked)."""
    from datetime import timedelta

    foto = foto_manuscrito(dono)
    Foto.objects.filter(pk=foto).update(criada_em=timezone.now() - timedelta(hours=30))
    travada, liberar = threading.Event(), threading.Event()

    def entrega_em_andamento():
        try:
            with transaction.atomic():
                Foto.objects.select_for_update().get(pk=foto)
                travada.set()
                liberar.wait(timeout=20)
        finally:
            connection.close()

    fio = threading.Thread(target=entrega_em_andamento)
    fio.start()
    assert travada.wait(timeout=20)
    try:
        from apps.fotos import servicos

        apagadas = servicos.limpar_avulsas_antigas()
    finally:
        liberar.set()
        fio.join()

    assert apagadas == 0
    assert Foto.objects.filter(pk=foto).exists()
    assert any(foto in p.name for p in pasta_de_fotos.iterdir())


def test_req_6_9_limpeza_reconfere_a_foto_na_hora_de_apagar(dono, pasta_de_fotos, monkeypatch):
    """[005] REQ-6.9: se uma entrega anexou a foto depois de ela entrar na lista de candidatas, a limpeza a deixa."""
    from datetime import timedelta

    from apps.fotos import servicos

    foto = foto_manuscrito(dono)
    Foto.objects.filter(pk=foto).update(criada_em=timezone.now() - timedelta(hours=30))
    original = Foto.objects.select_for_update

    def anexando_no_meio_tempo(*args, **kwargs):
        Foto.objects.filter(pk=foto).update(
            anexada=True
        )  # a entrega chegou entre a lista e a trava
        return original(*args, **kwargs)

    monkeypatch.setattr(Foto.objects, "select_for_update", anexando_no_meio_tempo)

    apagadas = servicos.limpar_avulsas_antigas()

    assert apagadas == 0
    assert Foto.objects.filter(pk=foto).exists()
    assert any(foto in p.name for p in pasta_de_fotos.iterdir())
