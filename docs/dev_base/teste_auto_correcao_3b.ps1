$ProgressPreference = 'SilentlyContinue'
$model = 'ggml-org/Qwen2.5-Omni-3B-GGUF:Q4_K_M'
$reps = 3

$systemPrompt = @'
Voce e MARIA, assistente de escritorio. Cria e edita planilhas Excel e documentos Word. SEMPRE responda em portugues do Brasil. Para QUALQUER acao de ferramenta, responda APENAS com um objeto JSON, sem texto antes ou depois, sem crases, sem bloco de codigo.

## Ferramentas disponiveis

- criar_planilha
  {"ferramenta":"criar_planilha","nome_arquivo":"...","colunas":["..."]}

- editar_planilha
  {"ferramenta":"editar_planilha","nome_arquivo":"...","colunas":["..."]}

- criar_documento
  {"ferramenta":"criar_documento","nome_arquivo":"...","titulo":"...","conteudo":"..."}

- extrair_dados_planilha
  {"ferramenta":"extrair_dados_planilha","nome_arquivo":"..."}

## Regras

- colunas e sempre lista de strings.
- linhas (opcional, para preencher dados) e lista de objetos, um por linha, com as chaves iguais aos nomes das colunas: [{"Nome":"Maria","Idade":28},{"Nome":"Joao","Idade":34}].
- Conteudo de documento: se o usuario nao especificar, seja breve e coerente.
- Se o arquivo nao foi mencionado antes, responda em texto: Nao encontrei o arquivo [nome]. Deseja listar seus arquivos?
- Cumprimentos e perguntas gerais: responda em texto curto (max. 2 frases).

## Exemplos

Usuario: "Crie planilha com nomes e idades"
MARIA:
{"ferramenta":"criar_planilha","nome_arquivo":"nomes_idades","colunas":["Nome","Idade"]}

Usuario: "Crie uma planilha chamada estoque com as colunas Item e Quantidade. Preencha com: Parafuso 200, Porca 150."
MARIA:
{"ferramenta":"criar_planilha","nome_arquivo":"estoque","colunas":["Item","Quantidade"],"linhas":[{"Item":"Parafuso","Quantidade":200},{"Item":"Porca","Quantidade":150}]}

Usuario: "Crie um oficio solicitando reuniao"
MARIA:
{"ferramenta":"criar_documento","nome_arquivo":"oficio_reuniao","titulo":"Oficio de Solicitacao de Reuniao","conteudo":"Senhor(a) Diretor(a),\n\nSolicitamos reuniao para discutir..."}
'@

$mensagemUsuario = @'
Tenho uma lista de produtos com nome no idioma Mandarim, preço e peso. Crie uma planilha chamada produtos_importados com as colunas Produto, Preço e Peso. Traduza os nomes para português e preencha todas as linhas:

球 - R$ 25,00 - 0,3 kg
玩具娃娃 - R$ 45,00 - 0,5 kg
玩具车 - R$ 35,00 - 0,4 kg
笔记本 - R$ 15,00 - 0,2 kg
文具盒 - R$ 12,00 - 0,15 kg
'@

# Resposta bruta REAL do 3B (EXEC 1 do teste anterior) — contem o bug de
# capitalizacao ("peso" minusculo em vez de "Peso" declarado em colunas)
$respostaBrutaComBug = '{"ferramenta":"criar_planilha","nome_arquivo":"produtos_importados","colunas":["Produto","Preco","Peso"],"linhas":[{"Produto":"Bola","Preco":"R$ 25,00","peso":"0,3 kg"},{"Produto":"brinquedo de boneca","Preco":"r$ 45,00","peso":"0,5 kg"},{"Produto":"carro de brinquedo","Preco":"r$ 35,00","peso":"0,4 kg"},{"Produto":"livro","Preco":"r$ 15,00","peso":"0,2 kg"},{"Produto":"caixa de lápis","Preco":"r$ 12,00","peso":"0,15 kg"}]}'

# Instrucao de revisao GENERICA — nao aponta o bug especifico, testa se o
# modelo consegue se auto-auditar sem pista direta
$instrucaoRevisao = @'
Antes de finalizar, revise cuidadosamente a chamada que voce acabou de gerar. Confira:
- O JSON esta valido e completo?
- Os nomes das chaves dentro de cada item de "linhas" correspondem EXATAMENTE (incluindo maiusculas e minusculas) aos nomes declarados em "colunas"?
- Os valores fazem sentido para os produtos descritos?

Envie a chamada final corrigida, no mesmo formato JSON, sem texto adicional.
'@

$body = @{
    model = $model
    messages = @(
        @{ role = 'system'; content = $systemPrompt }
        @{ role = 'user'; content = $mensagemUsuario }
        @{ role = 'assistant'; content = $respostaBrutaComBug }
        @{ role = 'user'; content = $instrucaoRevisao }
    )
    temperature = 0.1
    max_tokens = 400
    repeat_last_n = 128
    repeat_penalty = 1.1
    frequency_penalty = 0.0
    presence_penalty = 0.0
    dry_multiplier = 0.8
    dry_base = 1.75
    dry_allowed_length = 2
    dry_penalty_last_n = 64
    top_k = 40
    top_p = 0.95
    min_p = 0.05
} | ConvertTo-Json -Depth 10

$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)

Write-Output "########## Teste Auto-Correcao (3B) — turno extra de revisao ##########"
Write-Output "Bug injetado no turno anterior: chave 'peso' (minuscula) vs coluna 'Peso' declarada"
Write-Output ""

function IgualdadeExataDeConjunto {
    param([string[]]$a, [string[]]$b)
    if (@($a).Count -ne @($b).Count) { return $false }
    $sobra = @($a | Where-Object { @($b) -cnotcontains $_ })
    return $sobra.Count -eq 0
}

1..$reps | ForEach-Object {
    $i = $_
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $r = Invoke-RestMethod -Uri http://127.0.0.1:8080/v1/chat/completions -Method Post -ContentType 'application/json; charset=utf-8' -Body $bodyBytes -TimeoutSec 300
        $sw.Stop()
        $msg = $r.choices[0].message
        $finish = $r.choices[0].finish_reason
        $tokens = $r.usage.completion_tokens
        $content = if ($null -eq $msg.content) { '(null)' } else { $msg.content }

        Write-Output ("  ===== EXEC {0} [{1}ms | finish={2} | tokens={3}] =====" -f $i, $sw.ElapsedMilliseconds, $finish, $tokens)
        Write-Output "  RESPOSTA BRUTA:"
        Write-Output ("  " + $content)
        Write-Output ""

        try {
            $parsed = $content | ConvertFrom-Json
            $nLinhas = if ($null -ne $parsed.linhas) { @($parsed.linhas).Count } else { 0 }
            Write-Output ("  >> JSON valido | linhas={0}" -f $nLinhas)

            if ($nLinhas -gt 0) {
                $colunas = @($parsed.colunas)
                Write-Output ("  >> colunas declaradas: [{0}]" -f ($colunas -join ', '))

                # Auto-consistencia: chaves das linhas devem bater com as PROPIAS colunas
                $autoOk = $true
                $idx = 0
                foreach ($linha in $parsed.linhas) {
                    $idx++
                    $chavesLinha = @($linha.PSObject.Properties.Name)
                    Write-Output ("     linha {0}: chaves = [{1}]" -f $idx, ($chavesLinha -join ', '))
                    # IMPORTANTE: -cnotcontains e case-sensitive. Os operadores padrao do
                    # PowerShell (-in/-notin/-contains) sao case-INSENSITIVE e esconderiam
                    # o bug 'peso' vs 'Peso'.
                    $faltando = @($colunas | Where-Object { $chavesLinha -cnotcontains $_ })
                    $extras   = @($chavesLinha | Where-Object { $colunas -cnotcontains $_ })
                    if ($faltando.Count -gt 0 -or $extras.Count -gt 0) { $autoOk = $false }
                }

                # Referencia: colunas pedidas pelo USUARIO no pedido original
                $refColunas = @('Produto', 'Preço', 'Peso')
                $colunasExatas = IgualdadeExataDeConjunto $colunas $refColunas
                $linhasExatas = $true
                foreach ($linha in $parsed.linhas) {
                    $chavesLinha = @($linha.PSObject.Properties.Name)
                    if (-not (IgualdadeExataDeConjunto $chavesLinha $refColunas)) { $linhasExatas = $false; break }
                }

                if ($colunasExatas -and $linhasExatas) {
                    $veredicto = "CORRIGIU corretamente (colunas == pedido do usuario E chaves das linhas identicas)"
                } elseif ($autoOk) {
                    $veredicto = "AUTO-CONSISTENTE mas DIVERGENTE do pedido (rebaixou coluna Peso->peso em vez de corrigir as linhas)"
                } else {
                    $veredicto = "NAO CORRIGIU (chaves das linhas ainda divergem das proprias colunas)"
                }
                Write-Output ("  >> VEREDITO: {0}" -f $veredicto)
            }
        } catch {
            Write-Output "  >> NAO e JSON valido"
        }
    } catch {
        Write-Output ("  ===== EXEC {0} ERRO =====" -f $i)
        Write-Output ("  " + $_.Exception.Message)
        if ($_.ErrorDetails.Message) { Write-Output ("  BODY: " + $_.ErrorDetails.Message) }
    }
    Write-Output ""
}
