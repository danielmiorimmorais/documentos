---
name: video-legendas
description: "Traz o conteúdo integral de um ou mais vídeos para dentro do Claude como texto pela via leve: subir o vídeo no YouTube como não listado, baixar as legendas e entregar a transcrição — em vez de fazer upload do arquivo de vídeo, que estoura limites, trava a tela do Google e leva a sessão a erros 500 em cadeia. Use sempre que Daniel quiser transcrever, resumir, analisar, cotar ou 'passar a limpo' um vídeo, uma aula, uma palestra, uma reunião ou uma gravação — inclusive quando a gravação vier partida em vários vídeos que na verdade são uma sessão só (o caso 'por que três vídeos'), caso em que as legendas são juntadas em ordem numa transcrição contínua — mesmo que ele diga só 'transcreve esse vídeo', 'o que tem nessa gravação', 'me resume essa aula', 'junta esses vídeos' ou 'pega a sessão inteira'. Use também quando um upload de vídeo estiver falhando, travando ou dando erro de servidor: a saída é trocar de caminho, não insistir no upload."
---

# Vídeo → texto pela via das legendas do YouTube

**Regra de ouro: nunca leve vídeo bruto para dentro do contexto do Claude.** Nem por upload no chat, nem por MCP, nem por tela do Google. Vídeo é caríssimo em tokens e é justamente o que trava a sessão (ver a seção **Erros 500** abaixo). O YouTube transcreve vídeo de graça e cospe texto. Texto é leve. Esta skill terceiriza a parte pesada ao YouTube e deixa para o Claude só o que ele faz bem: limpar, juntar e pensar sobre texto.

Consequência prática: **esta skill não exige um modelo forte.** Ela foi desenhada para rodar bem em modelos bem abaixo do Fable, porque a inteligência não está no modelo — está na escolha do caminho leve. A seção **Modelo e reasoning** fecha isso.

## Quando usar / quando não

Use quando o insumo é um ou mais vídeos e o que se quer é o **conteúdo** deles (transcrição, resumo, análise, citação, índice). Use também quando um upload de vídeo estiver falhando — a saída é trocar de caminho.

Não use para editar vídeo, cortar clipe, ler o que está *na imagem* (slides, gráficos, rostos, texto na tela que não é falado). Legenda só captura o que foi **dito**. Se o essencial está na imagem e não na fala, avise Daniel: aí não tem atalho, é análise de vídeo mesmo, e ela deve ser feita fora do Claude ou com um modelo de visão dedicado, num arquivo pequeno.

## O fluxo, de ponta a ponta

```
[vídeo local]  --sobe-->  [YouTube, não listado]  --YouTube transcreve-->  [legenda .srt/.vtt]
      |                                                                            |
   (Daniel)                                                                    (Daniel baixa)
                                                                                    |
                                                                                    v
[Claude limpa + junta em ordem]  <--upload das legendas--  [Daniel manda os arquivos no chat]
      |
      v
[transcrição contínua]  -->  o que foi pedido: resumo / análise / cotação / índice
```

Divisão de trabalho: **Daniel** faz o que precisa de conta logada e de rede (subir no YouTube, baixar as legendas, mandar no chat). **Claude** faz o que é texto (limpar, juntar, pensar). Não inverta: o Claude, neste ambiente remoto, **não consegue** baixar do YouTube (ver **Ambiente remoto**).

## Passo a passo

### 1. Subir no YouTube — Daniel

- Enviar em https://studio.youtube.com → **Criar → Enviar vídeos**.
- Visibilidade **Não listado** (não precisa ser público; não listado já gera legenda e não aparece em buscas). Privado também gera legenda e é mais fechado, mas exige estar logado para o yt-dlp — não listado é o mais simples.
- Se a gravação é uma sessão partida em várias partes, subir **as três (ou N) partes** e, de preferência, colocá-las numa **playlist não listada na ordem certa**. A playlist é o que deixa o Claude juntar sem adivinhar ordem.
- Esperar o YouTube processar a legenda automática. Vídeo longo pode levar de minutos a algumas horas depois do fim do processamento. A aba **Legendas** no Studio mostra quando "Automático" fica pronto.

### 2. Baixar as legendas — Daniel

Dois caminhos. O manual sempre funciona; o `yt-dlp` é mais rápido para várias partes.

**Manual (YouTube Studio):** Studio → **Legendas** → idioma → **⋮ → Fazer o download → .srt**. Um arquivo por vídeo.

**yt-dlp (terminal da máquina do Daniel, com acesso ao YouTube):**

```bash
# listar o que existe de legenda num vídeo
yt-dlp --list-subs "URL_DO_VIDEO"

# baixar SÓ a legenda (sem o vídeo), auto e manual, PT e EN, já em .srt
yt-dlp --skip-download --write-auto-subs --write-subs \
       --sub-langs "pt.*,en.*" --convert-subs srt \
       -o "%(autonumber)02d-%(title)s.%(ext)s" \
       "URL_DO_VIDEO"

# playlist inteira, em ordem — o autonumber (01-, 02-, 03-) preserva a sequência
yt-dlp --yes-playlist --skip-download --write-auto-subs --write-subs \
       --sub-langs "pt.*,en.*" --convert-subs srt \
       -o "%(playlist_index)02d-%(title)s.%(ext)s" \
       "URL_DA_PLAYLIST"
```

Notas que economizam frustração:
- `--write-auto-subs` pega a legenda **automática** (a que o YouTube gera). `--write-subs` pega a **manual/oficial**, se o criador subiu uma. Pedir as duas e usar a melhor.
- `pt.*` casa `pt`, `pt-BR`, `pt-orig` etc. Se `--list-subs` mostrar outro código, ajustar.
- `--convert-subs srt` é importante: o script de limpeza espera `.srt` ou `.vtt`, e `.srt` é o mais limpo.
- O prefixo numérico (`01-`, `02-`, `03-`) é o que garante a ordem na hora de juntar.

### 3. Mandar as legendas no chat — Daniel

Fazer upload dos arquivos `.srt`/`.vtt` no chat do Claude, **em ordem** (ou nomeados com o prefixo numérico do passo 2). São arquivos de texto pequenos; nunca travam. É aqui que o "eu upo elas" acontece.

### 4. Limpar e juntar — Claude

Legenda automática do YouTube vem suja: timestamps, tags de estilo, e — o pior — **cada linha repete a anterior** (efeito de "digitação" das auto-subs). Não entregar isso cru. Rodar o script incluído:

```bash
python3 scripts/legendas_para_texto.py 01-parte.srt 02-parte.srt 03-parte.srt -o transcricao.txt
```

Ele remove timestamps e tags, desfaz a duplicação rolante das auto-subs, reflui em parágrafos e concatena os arquivos **na ordem em que forem passados**, com um marcador `=== Parte N ===` entre eles. Passar os arquivos na ordem correta (o glob `*.srt` já sai ordenado se os nomes têm prefixo numérico).

Depois de gerar o `.txt`, ler e fazer uma passada de sanidade: a auto-sub erra nomes próprios, termos técnicos e não põe pontuação boa. Corrigir o óbvio, marcar `[inaudível?]` onde a legenda claramente falhou, e **não inventar** conteúdo que a legenda não traz. A legenda é a fonte; o Claude normaliza, não reescreve.

### 5. Fazer o trabalho pedido — Claude

Com a transcrição em mãos, executar o que Daniel pediu: resumo, análise, cotação de trechos, índice com marcas de tempo (as marcas de tempo estão nos `.srt` originais, se precisar reancorar), tradução, etc. Entregar o `.txt` da transcrição junto, para Daniel guardar.

## Vários vídeos = uma sessão só (o caso "três vídeos")

Quando uma gravação foi cortada em três (ou N) vídeos por limite de tamanho/duração, o objetivo é a **sessão inteira**, não cada pedaço. O tratamento:

1. Garantir a **ordem** — pela playlist, pelo prefixo numérico do arquivo, ou perguntando a Daniel se estiver ambíguo. Ordem errada arruína a transcrição.
2. Juntar com o script (um marcador `=== Parte N ===` por arquivo).
3. Cuidar da **emenda**: o corte entre partes às vezes parte uma frase no meio. Ao revisar, costurar a frase que atravessa a fronteira e remover uma eventual saudação/recapitulação repetida no início da parte seguinte.
4. Tratar o resultado como **um** documento. Resumo, índice e análise cobrem a gravação inteira, não três resumos soltos.

## Ambiente remoto: por que o Claude não baixa aqui

Neste ambiente de execução remota, a saída de rede passa por um proxy que **bloqueia o YouTube** (respostas `403 Forbidden` no túnel). Testado: `yt-dlp` instala e roda, mas não conecta ao YouTube daqui. Portanto o download das legendas é **sempre** na máquina do Daniel (ou no Studio, no navegador dele). O Claude entra depois que os arquivos chegam no chat. Não gaste tentativas tentando baixar do container — não é limitação de código, é a política de rede do ambiente.

## Por que a sessão dos vídeos travou: dois modos de falha

Esta skill nasceu de uma sessão ("Por que três vídeos") que travou. Há **dois** modos de falha em jogo, e eles se somam. Documentados para não repetir:

**1. A salvaguarda de uso duplo do Fable 5.1 (`[cyber]`).** O Fable 5.1 carrega salvaguardas de uso duplo intencionalmente abrangentes, que às vezes sinalizam tarefas legítimas de programação e segurança. Trabalho com vídeo enquadrado como "contornar limite/quota", "burlar a tela de upload", download com `yt-dlp` — isso é lido como cyber. Quando dispara, a resposta é sinalizada e a sessão é **alternada para outro modelo** (ex.: Opus 4.8), com a etiqueta `[cyber]`. Confirmado na prática: uma mensagem sobre montar esta própria skill, com a expressão "hackear os limites do Google", foi sinalizada assim. **Este era o palpite original de Daniel, e estava certo.**

**2. Erro 500 do servidor por contexto inchado.** Vídeo/upload = muitos tokens. Chamada gigante é mais sujeita a `Internal server error`. Pior: uma vez inchado o contexto, o `/compact` — que reprocessa tudo — **também** dá 500, e a sessão entra num laço irrecuperável (não avança e não comprime).

**Como distinguir os dois, na prática:**

| Sinal na tela | É... |
|---|---|
| "Alternado para Opus 4.8", etiqueta `[cyber]`/`[bio]`, "as proteções do Fable sinalizaram" | salvaguarda (recusa + troca de modelo; HTTP 200 por baixo) |
| "Erro do servidor" / `API Error: 500 Internal server error` | falha de servidor (contexto grande, carga) |

Os dois se combinam: o caminho pesado enquadrado como "burlar" o Google **atrai a salvaguarda** e ao mesmo tempo **incha o contexto** que gera os 500. Não dá para separar com certeza qual dominou na sessão travada sem o transcript dela, mas ambos apontam para a mesma causa raiz e a mesma cura.

**A lição que a skill aplica:** remover o caminho pesado de vez, e enquadrar o trabalho pelo que ele é. Baixar a legenda automática que o próprio YouTube oferece **não é burlar nada** — é usar um recurso público e legítimo. Falar em "hackear limites" é impreciso e ainda por cima atrai a salvaguarda à toa. Descreva a tarefa como transcrição por legendas, nunca como contorno de limite.

## Modelo e reasoning recomendados

Como o trabalho pesado é do YouTube, sobra pouco para o modelo, e esse pouco é quase todo mecânico. Por isso a skill roda confiável bem abaixo do Fable. Por etapa:

| Etapa | Exigência | Roda confiável em | Reasoning / effort |
|---|---|---|---|
| Limpar + juntar legendas (rodar o script) | mecânica pura | qualquer modelo, incluindo Haiku 4.5 e os modelos locais de Daniel (Gemma/Qwen via `ia-local`) | baixo |
| Decidir ordem das partes, costurar emendas, normalizar termos/nomes | julgamento leve | Sonnet 5 | medium |
| Resumir / analisar / cotar / indexar o conteúdo | julgamento pleno | Opus 5 (padrão), ou Sonnet 5 se o orçamento apertar | high (xhigh/max só se o conteúdo for denso) |

**Se for para escolher um único modelo para rodar a skill inteira de forma confiável: Claude Opus 5 em effort `high`.** É o padrão da casa, tem folga de sobra para a análise e nunca tropeça na parte mecânica. Se o custo importar e o vídeo for aula/conversa comum, **Claude Sonnet 5 em `medium`** entrega a transcrição limpa e um bom resumo — suba para `high` só na etapa de análise. Para a limpeza offline em lote, um modelo local (Gemma Q8, ou Qwen em modo reasoning para decidir ordem/emendas) dá conta via a skill `ia-local`, sem gastar API.

**Evite o Fable 5.1 aqui — e não é só por custo.** O Fable 5.1 carrega as salvaguardas de uso duplo que sinalizam trabalho com vídeo/download como `[cyber]` e trocam o modelo no meio (ver a seção de modos de falha). Opus 5 e Sonnet 5 não carregam esse classificador agressivo, então são **duplamente melhores** para esta skill: mais baratos e sem o risco de falso positivo que interrompe a tarefa. Se, ainda assim, rodar no Fable, descreva a tarefa como transcrição por legendas, nunca como "contornar limite" — o enquadramento é o que puxa o gatilho.

Regra de bolso independente de modelo: **a confiabilidade vem de escolher o caminho leve, não da inteligência do modelo.** Qualquer modelo que siga esta skill sem cair na tentação de processar o vídeo bruto vai entregar.

## O que vai na pasta desta skill

- `scripts/legendas_para_texto.py` — converte `.srt`/`.vtt` (inclusive auto-subs duplicadas do YouTube) em texto limpo, reflui em parágrafos e concatena vários arquivos em ordem. Rodar sempre; não montar o parser de legenda na mão a cada vez.
