#!/usr/bin/env python3
"""
legendas_para_texto.py — converte legendas .srt/.vtt (inclusive as
automáticas e duplicadas do YouTube) em texto corrido e limpo.

Uso:
    python3 legendas_para_texto.py parte1.srt parte2.srt -o transcricao.txt
    python3 legendas_para_texto.py *.vtt            # imprime no stdout

Vários arquivos são concatenados NA ORDEM em que aparecem na linha de
comando, com um marcador "=== Parte N ===" entre eles. Nomeie os
arquivos com prefixo numérico (01-, 02-, 03-) para que o shell os
ordene sozinho.

O que ele faz:
- descarta cabeçalho WEBVTT, numeração de cue e linhas de timestamp;
- remove tags de estilo (<c>, <00:00:01.000>, {\\an8}, etc.);
- desfaz a duplicação "rolante" das auto-subs do YouTube, em que cada
  cue reexibe a linha anterior acrescida de uma palavra;
- junta em parágrafos legíveis.

Não corrige pontuação nem ortografia: isso é decisão de conteúdo e fica
para a revisão humana/modelo. O objetivo é entregar texto limpo, não
reescrito.
"""
import argparse
import re
import sys

TAG = re.compile(r"<[^>]+>")            # <c>, <00:00:01.000>, </c>...
BRACE = re.compile(r"\{\\[^}]*\}")       # {\an8}, {\pos(...)}
TS_ARROW = re.compile(r"-->")            # linha de timestamp
TS_ONLY = re.compile(r"^\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}")
CUE_NUM = re.compile(r"^\d+$")           # numeração de cue do .srt
HEADER = re.compile(r"^(WEBVTT|Kind:|Language:|NOTE\b|STYLE\b|X-TIMESTAMP)", re.I)


def limpar_arquivo(texto):
    """Recebe o conteúdo bruto de um .srt/.vtt e devolve a lista de
    linhas de fala, já sem tags e sem a duplicação rolante."""
    linhas = []
    for raw in texto.splitlines():
        linha = raw.strip("﻿").strip()
        if not linha:
            continue
        if HEADER.match(linha):
            continue
        if TS_ARROW.search(linha) or TS_ONLY.match(linha):
            continue
        if CUE_NUM.match(linha):
            continue
        linha = BRACE.sub("", TAG.sub("", linha)).strip()
        # o YouTube às vezes escapa entidades
        linha = (linha.replace("&nbsp;", " ").replace("&amp;", "&")
                      .replace("&lt;", "<").replace("&gt;", ">")
                      .replace("&#39;", "'").replace("&quot;", '"'))
        linha = re.sub(r"[ \t]+", " ", linha).strip()
        if linha:
            linhas.append(linha)

    # Desfaz a duplicação rolante: se a última linha guardada é prefixo
    # da atual (a auto-sub "digitando"), a atual substitui a anterior;
    # se são iguais, ignora; senão, é conteúdo novo.
    saida = []
    for linha in linhas:
        if saida:
            ult = saida[-1]
            if linha == ult:
                continue
            if linha.startswith(ult):
                saida[-1] = linha
                continue
            if ult.startswith(linha):
                continue
        saida.append(linha)
    return saida


def reflui(linhas):
    """Junta as linhas em parágrafos. Quebra de parágrafo quando a linha
    anterior termina em pontuação forte; senão, emenda com espaço."""
    if not linhas:
        return ""
    paragrafos = []
    atual = linhas[0]
    for linha in linhas[1:]:
        if re.search(r"[.!?…:]$", atual) or len(atual) > 350:
            paragrafos.append(atual)
            atual = linha
        else:
            atual += " " + linha
    paragrafos.append(atual)
    return "\n\n".join(paragrafos)


def main():
    ap = argparse.ArgumentParser(description="Legendas .srt/.vtt -> texto limpo")
    ap.add_argument("arquivos", nargs="+", help="arquivos .srt/.vtt em ordem")
    ap.add_argument("-o", "--saida", help="arquivo de saída (padrão: stdout)")
    ap.add_argument("--sem-marcador", action="store_true",
                    help="não inserir '=== Parte N ===' entre arquivos")
    args = ap.parse_args()

    blocos = []
    for i, caminho in enumerate(args.arquivos, 1):
        try:
            with open(caminho, encoding="utf-8", errors="replace") as f:
                bruto = f.read()
        except OSError as e:
            print(f"aviso: não li {caminho}: {e}", file=sys.stderr)
            continue
        texto = reflui(limpar_arquivo(bruto))
        if len(args.arquivos) > 1 and not args.sem_marcador:
            blocos.append(f"=== Parte {i}: {caminho} ===\n\n{texto}")
        else:
            blocos.append(texto)

    resultado = "\n\n\n".join(b for b in blocos if b.strip()).rstrip() + "\n"

    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as f:
            f.write(resultado)
        palavras = len(resultado.split())
        print(f"ok: {args.saida} — {palavras} palavras, "
              f"{len(blocos)} arquivo(s)", file=sys.stderr)
    else:
        sys.stdout.write(resultado)


if __name__ == "__main__":
    main()
