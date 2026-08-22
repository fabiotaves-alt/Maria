"""
backend/core/protocolo.py
--------------------------
Leitura e escrita de mensagens JSON, uma por linha, via stdin/stdout.
"""
import sys
import json


def ler_requisicao():
    """
    Lê uma linha de stdin e decodifica como JSON.
    Retorna None no EOF ou em linha em branco.
    Pode levantar json.JSONDecodeError se a linha não for JSON válido —
    o chamador deve tratar essa exceção.
    """
    linha = sys.stdin.readline()
    if not linha:
        return None
    linha = linha.strip()
    if not linha:
        return None
    return json.loads(linha)


def enviar_resposta(id_: str, status: str, dados=None, mensagem_erro: str = None):
    """Serializa e escreve uma resposta em stdout, seguida de flush."""
    resposta = {"id": id_, "status": status, "dados": dados}
    if mensagem_erro:
        resposta["mensagemErro"] = mensagem_erro
    sys.stdout.write(json.dumps(resposta, ensure_ascii=False) + "\n")
    sys.stdout.flush()