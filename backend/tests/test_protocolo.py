import io
import json
import sys

import pytest

from core.protocolo import ler_requisicao, enviar_resposta


def test_ler_requisicao_valida(monkeypatch):
    entrada = json.dumps({"id": "1", "comando": "ping", "payload": None}) + "\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(entrada))
    req = ler_requisicao()
    assert req["comando"] == "ping"


def test_ler_requisicao_eof(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert ler_requisicao() is None


def test_ler_requisicao_json_invalido(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("{invalido\n"))
    with pytest.raises(json.JSONDecodeError):
        ler_requisicao()


def test_enviar_resposta_formato(capsys):
    enviar_resposta("1", "ok", dados={"pong": True})
    saida = capsys.readouterr().out
    resposta = json.loads(saida)
    assert resposta["id"] == "1"
    assert resposta["status"] == "ok"
    assert resposta["dados"]["pong"] is True