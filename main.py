"""
Script principal da MARIA - Assistente de IA de Escritório.
Interface CLI para interação com o usuário via terminal.

Uso:
    python main.py

Comandos especiais:
    sair, exit - Encerra a aplicação
    limpar - Limpa o histórico da conversa
    ajuda - Mostra comandos disponíveis
"""

import sys
import logging
from datetime import datetime
from core.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, LOG_LEVEL, MAX_MENSAGENS_HISTORICO
from core.ollama_client import OllamaClient, OllamaClientError
from core.chat_session import ChatSession, interpretar_confirmacao
from core.tools_schema import TOOLS_SCHEMA, executar_ferramenta_real
from core.session_storage import salvar_sessao, listar_sessoes_salvas, carregar_sessao


# Configurar encoding do stdout para UTF-8 (evita erros no Windows)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    # Python < 3.7 não tem reconfigure, ignorar silenciosamente
    pass

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def mostrar_boas_vindas():
    """Exibe mensagem de boas-vindas ao usuário."""
    print("\n" + "=" * 60)
    print("       MARIA - Assistente de IA de Escritório")
    print("=" * 60)
    print("\nOlá! Eu sou a MARIA, sua assistente de escritório.")
    print("Rodando 100% localmente no seu computador, sem internet.\n")
    print("Como posso ajudar você hoje?")
    print("-" * 60)
    print("Comandos: 'ajuda' | 'limpar' | 'retomar' | 'sair'\n")


def mostrar_ajuda():
    """Exibe lista de comandos disponíveis."""
    print("\n--- Comandos Disponíveis ---")
    print("  ajuda    - Mostra esta mensagem de ajuda")
    print("  limpar   - Limpa o histórico da conversa")
    print("  retomar  - Retoma uma conversa salva de uma execução anterior")
    print("  sair     - Encerra a aplicação")
    print("  exit     - Encerra a aplicação (alternativo)")
    print("-" * 30)
    print("\nDica: você pode pedir em linguagem natural, como")
    print("  'crie uma planilha de gastos' ou")
    print("  'crie um documento com uma carta de apresentação'.")
    print("A MARIA identificará automaticamente e perguntará antes de criar.\n")


def gerar_mensagem_confirmacao(tool_call: dict) -> str:
    """
    Gera uma mensagem legível de confirmação para o usuário.
    
    Args:
        tool_call: Dicionário com 'name' e 'arguments' da tool call
        
    Returns:
        String com a mensagem de confirmação
    """
    nome = tool_call.get("name", "")
    args = tool_call.get("arguments", {})
    
    if nome == "criar_planilha":
        nome_arquivo = args.get("nome_arquivo", "planilha")
        colunas = args.get("colunas", [])
        lista_colunas = ", ".join(colunas) if colunas else "sem colunas definidas"
        return (f'Entendi! Vou criar uma planilha chamada "{nome_arquivo}" '
                f'com as colunas: {lista_colunas}.\n'
                f'Posso seguir com a criação? (responda sim ou não)')
    
    elif nome == "criar_documento":
        nome_arquivo = args.get("nome_arquivo", "documento")
        titulo = args.get("titulo", "Sem título")
        conteudo = args.get("conteudo", "")
        preview = conteudo[:80].strip()
        if len(conteudo) > 80:
            preview += "..."
        preview_texto = f'\nInício do conteúdo: "{preview}"' if preview else ""
        return (f'Entendi! Vou criar um documento chamado "{nome_arquivo}" '
                f'com o título "{titulo}".{preview_texto}\n'
                f'Posso seguir com a criação? (responda sim ou não)')

    elif nome == "editar_planilha":
        nome_arquivo = args.get("nome_arquivo", "planilha")
        colunas = args.get("colunas", [])
        lista_colunas = ", ".join(colunas) if colunas else "sem colunas definidas"
        qtd_linhas = len(args.get("linhas") or [])
        return (f'Entendi! Vou SOBRESCREVER a planilha "{nome_arquivo}" '
                f'com as colunas: {lista_colunas} ({qtd_linhas} linha(s) de dados).\n'
                f'Esta ação substitui o conteúdo atual do arquivo. Posso seguir? (responda sim ou não)')
    
    else:
        return f'Vou executar a ação "{nome}". Posso prosseguir? (responda sim ou não)'


def gerar_nome_sessao() -> str:
    """Gera o nome do arquivo da sessão atual com base no timestamp de início."""
    return f"sessao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


def salvar_sessao_silenciosamente(sessao: ChatSession, nome_sessao: str) -> None:
    """Salva a sessão em disco sem interromper o loop de chat em caso de falha."""
    try:
        salvar_sessao(sessao.to_dict(), nome_sessao)
    except (PermissionError, OSError) as error:
        logger.warning(f"Falha ao salvar sessão automaticamente: {error}")
        print(f"\n[AVISO] Não foi possível salvar a sessão automaticamente: {error}")


def tratar_comando_retomar(sessao: ChatSession, nome_sessao_atual: str) -> tuple[ChatSession, str]:
    """
    Trata o comando 'retomar': lista sessões salvas e carrega a escolhida.

    Returns:
        Tupla (sessao, nome_sessao_atual) — a mesma sessão/nome recebidos
        se a retomada for cancelada ou falhar.
    """
    if sessao.tem_acao_pendente():
        sessao.limpar_acao_pendente()
        print("\nAção pendente cancelada para retomar outra sessão.")

    sessoes_disponiveis = listar_sessoes_salvas()
    if not sessoes_disponiveis:
        print("\nNenhuma sessão salva encontrada.")
        return sessao, nome_sessao_atual

    print("\n--- Sessões salvas (mais recentes primeiro) ---")
    for indice, info in enumerate(sessoes_disponiveis, start=1):
        print(f"  {indice}. {info['nome_arquivo']} ({info['qtd_mensagens']} mensagens)")

    escolha = input("Digite o número da sessão para retomar (ou Enter para cancelar): ").strip()
    if not escolha:
        print("\nRetomada cancelada.")
        return sessao, nome_sessao_atual

    try:
        indice_escolhido = int(escolha)
        sessao_escolhida = sessoes_disponiveis[indice_escolhido - 1]
    except (ValueError, IndexError):
        print("\nSeleção inválida. Retomada cancelada.")
        return sessao, nome_sessao_atual

    try:
        dados_sessao = carregar_sessao(sessao_escolhida["caminho"])
        nova_sessao = ChatSession.from_dict(dados_sessao)
        print(f"\nSessão '{sessao_escolhida['nome_arquivo']}' retomada com "
              f"{nova_sessao.contar_mensagens()} mensagem(ns).")
        return nova_sessao, sessao_escolhida["nome_arquivo"]
    except ValueError as error:
        print(f"\n[ERRO] Não foi possível retomar a sessão: {error}")
        return sessao, nome_sessao_atual


def loop_chat():
    """
    Loop principal de interação com o usuário.
    """
    # Inicializar componentes
    try:
        cliente = OllamaClient()
    except Exception as e:
        logger.error(f"Erro ao inicializar cliente: {e}")
        print(f"\nErro ao inicializar cliente: {e}")
        return
    
    sessao = ChatSession(max_mensagens=MAX_MENSAGENS_HISTORICO)
    nome_sessao_atual = gerar_nome_sessao()
    
    mostrar_boas_vindas()
    
    while True:
        try:
            # Ler entrada do usuário
            entrada = input("\nVocê: ").strip()
            
            # Verificar comandos especiais (funcionam mesmo com ação pendente)
            if entrada.lower() in ["sair", "exit"]:
                print("\nEncerrando MARIA. Até logo!")
                break
            
            if entrada.lower() == "ajuda":
                mostrar_ajuda()
                continue
            
            if entrada.lower() == "limpar":
                sessao.limpar_historico()
                sessao.limpar_acao_pendente()  # Cancela qualquer ação pendente
                print("\nHistórico da conversa limpo!")
                continue
            
            if entrada.lower() == "retomar":
                sessao, nome_sessao_atual = tratar_comando_retomar(sessao, nome_sessao_atual)
                continue
            
            if not entrada:
                continue
            
            # Se há ação pendente, tratar entrada como resposta de confirmação
            if sessao.tem_acao_pendente():
                resultado = interpretar_confirmacao(entrada)
                
                if resultado is True:
                    # Confirmado - executar ação real
                    try:
                        nome_acao = sessao.acao_pendente["name"]
                        argumentos = sessao.acao_pendente["arguments"]
                        caminho = executar_ferramenta_real(nome_acao, argumentos)
                        print(f"\n[SISTEMA] {caminho}")
                        sessao.adicionar_mensagem("assistant", caminho)
                        sessao.limpar_acao_pendente()
                        salvar_sessao_silenciosamente(sessao, nome_sessao_atual)
                    except (PermissionError, OSError, ValueError) as e:
                        logger.error(f"Erro ao executar ferramenta: {e}")
                        print(f"\n[ERRO] Não foi possível criar o arquivo: {e}")
                        sessao.limpar_acao_pendente()
                    except Exception as e:
                        logger.error(f"Erro inesperado ao executar ferramenta: {e}")
                        print(f"\n[ERRO] Ocorreu um erro inesperado: {e}")
                        sessao.limpar_acao_pendente()
                
                elif resultado is False:
                    # Negado - cancelar ação
                    print("\nAção cancelada.")
                    sessao.limpar_acao_pendente()
                
                else:
                    # Ambíguo - incrementar contador e verificar
                    sessao.tentativas_confirmacao_ambigua += 1
                    
                    if sessao.tentativas_confirmacao_ambigua >= 2:
                        # Segunda ambiguidade consecutiva - cancelar automaticamente
                        print("\nNão consegui confirmar, cancelando a ação por segurança.")
                        sessao.limpar_acao_pendente()
                    else:
                        # Primeira ambiguidade - pedir novamente
                        print("\nNão entendi. Você confirma a criação? Responda sim ou não.")
                
                continue
            
            # Enviar mensagem para o modelo (apenas se não houver ação pendente)
            try:
                historico_atual = sessao.get_historico_com_system()
                sessao.adicionar_mensagem("user", entrada)

                print("\nMARIA: ", end="", flush=True)
                resposta_textual = ""
                tool_call_final = None

                for chunk, tool_chunk in cliente.chat_com_tools_stream(
                    mensagem_usuario=entrada,
                    historico=historico_atual,
                    tools=TOOLS_SCHEMA
                ):
                    if chunk is not None:
                        print(chunk, end="", flush=True)
                        resposta_textual += chunk
                    if tool_chunk is not None:
                        tool_call_final = tool_chunk

                print()

                if tool_call_final:
                    sessao.definir_acao_pendente(tool_call_final)
                    print(gerar_mensagem_confirmacao(tool_call_final))
                    if resposta_textual.strip():
                        sessao.adicionar_mensagem("assistant", resposta_textual)
                else:
                    if resposta_textual.strip():
                        sessao.adicionar_mensagem("assistant", resposta_textual)
                salvar_sessao_silenciosamente(sessao, nome_sessao_atual)
                
            except OllamaClientError as e:
                print(f"\n[Erro] {e}")
                print("\nDicas:")
                print("  1. Verifique se o Ollama está rodando: ollama serve")
                print("  2. Verifique se o modelo está instalado: ollama pull qwen2.5:7b")
                print("  3. Verifique se a URL http://localhost:11434 está acessível")
                logger.error(f"Erro OllamaClientError: {e}")
                
        except KeyboardInterrupt:
            print("\n\nInterrupção detectada. Digite 'sair' para encerrar ou continue digitando.")
            continue
        except EOFError:
            print("\n\nFim de arquivo detectado. Encerrando.")
            break
    
    print("\nObrigado por usar MARIA!\n")


def main():
    """
    Ponto de entrada principal da aplicação.
    """
    # Verificar dependências
    try:
        import requests
    except ImportError:
        print("\n[ERRO] A biblioteca 'requests' não está instalada.")
        print("Instale com: pip install requests\n")
        sys.exit(1)
    
    # Executar loop principal
    loop_chat()


if __name__ == "__main__":
    main()
