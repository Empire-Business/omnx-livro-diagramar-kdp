#!/usr/bin/env python3
"""Confere o PDF do miolo contra as regras oficiais da Amazon KDP para paperback sem sangria.

Uso:
    validar_pdf.py <arquivo.pdf> --formato 6x9 [--papel branco|creme]

Imprime JSON com ok, erros, avisos, medidas e o que não pôde ser medido.
Com o Poppler instalado (pdffonts e pdftotext) mede fontes, margens e páginas em branco de verdade.
Sem ele, faz a conferência básica e diz o que ficou de fora.
Imagens não são medidas: margem e resolução de imagem ficam para o Previewer da KDP.

Códigos de saída: 0 sem erros | 1 pedido inválido | 2 achou erros
"""
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # não deixa __pycache__ dentro da skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kdp_regras as regras  # noqa: E402

TOLERANCIA_PT = 1.0
TOLERANCIA_MARGEM_PT = 0.75
PONTOS = 72.0


def rodar(programa, *argumentos):
    caminho = shutil.which(programa)
    if not caminho:
        return None
    try:
        resultado = subprocess.run([caminho] + list(argumentos), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=180)
    except subprocess.TimeoutExpired:
        return None
    if resultado.returncode != 0:
        return None
    return resultado.stdout.decode("utf-8", errors="replace")


def contar_paginas(dados, caminho):
    saida = rodar("pdfinfo", caminho)
    if saida:
        achado = re.search(r"^Pages:\s+(\d+)", saida, re.M)
        if achado:
            return int(achado.group(1))
    if b"/ObjStm" in dados:
        return None
    return len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", dados))


def conferir_fontes(dados, caminho, resultado):
    saida = rodar("pdffonts", caminho)
    if saida is not None:
        faltando = []
        for linha in saida.splitlines()[2:]:
            colunas = linha.split()
            if len(colunas) >= 5 and colunas[-5] == "no":
                faltando.append(colunas[0])
        if faltando:
            resultado["erros"].append("Fontes não incorporadas: {}.".format(", ".join(faltando)))
        resultado["medidas"]["fontes"] = max(0, len(saida.splitlines()) - 2)
        return
    resultado["nao_medido"].append("Fontes medidas por leitura simples do arquivo; instale o Poppler para confirmar.")
    descritores = len(re.findall(rb"/FontDescriptor", dados))
    arquivos = len(re.findall(rb"/FontFile[23]?\b", dados))
    if arquivos < descritores or (descritores == 0 and re.search(rb"/Subtype\s*/Type1\b", dados)):
        resultado["erros"].append("Há fontes que parecem não estar incorporadas.")


def medir_palavras(caminho):
    """Devolve lista por página de (largura, altura, [caixas das palavras]), ou None sem Poppler."""
    saida = rodar("pdftotext", "-bbox", caminho, "-")
    if saida is None:
        return None
    paginas = []
    for bloco in re.finditer(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', saida, re.S):
        caixas = []
        for caixa in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', bloco.group(3)):
            texto = html.unescape(caixa.group(5)).strip()
            if texto:
                caixas.append(tuple(float(caixa.group(i)) for i in range(1, 5)))
        paginas.append((float(bloco.group(1)), float(bloco.group(2)), caixas))
    return paginas


def conferir_margens(paginas, total, resultado):
    """Mede o texto de cada página. Página ímpar: interna à esquerda. Par: interna à direita."""
    interna_exigida = regras.margem_interna_minima(total)
    menores = {"interna": 999.0, "externa": 999.0, "superior": 999.0, "inferior": 999.0}
    com_problema = []
    for numero, (largura, altura, caixas) in enumerate(paginas, start=1):
        if not caixas:
            continue
        esquerda = min(c[0] for c in caixas)
        direita = largura - max(c[2] for c in caixas)
        topo = min(c[1] for c in caixas)
        base = altura - max(c[3] for c in caixas)
        interna, externa = (esquerda, direita) if numero % 2 == 1 else (direita, esquerda)
        for chave, valor in (("interna", interna), ("externa", externa), ("superior", topo), ("inferior", base)):
            menores[chave] = min(menores[chave], valor)
        if interna_exigida is not None and interna + TOLERANCIA_MARGEM_PT < interna_exigida * PONTOS:
            com_problema.append(numero)
        elif min(externa, topo, base) + TOLERANCIA_MARGEM_PT < regras.MARGEM_EXTERNA_MINIMA * PONTOS:
            com_problema.append(numero)
    resultado["medidas"]["menor_margem_polegadas"] = {k: round(v / PONTOS, 3) for k, v in menores.items() if v < 999}
    if interna_exigida is not None:
        resultado["medidas"]["margem_interna_exigida_polegadas"] = interna_exigida
    if com_problema:
        resultado["erros"].append("Texto fora da margem mínima nas páginas: {}.".format(", ".join(map(str, com_problema[:20]))))


def conferir_brancas(paginas, resultado):
    sequencia, maior_meio, inicio = 0, 0, None
    for numero, (_, _, caixas) in enumerate(paginas, start=1):
        if caixas:
            if sequencia > maior_meio:
                maior_meio, inicio = sequencia, numero - sequencia
            sequencia = 0
        else:
            sequencia += 1
    fim = sequencia
    resultado["medidas"]["brancas_seguidas_no_meio"] = maior_meio
    resultado["medidas"]["brancas_no_fim"] = fim
    if maior_meio > regras.BRANCAS_SEGUIDAS_MEIO:
        resultado["erros"].append("{} páginas em branco seguidas a partir da {}; o máximo é {}.".format(maior_meio, inicio, regras.BRANCAS_SEGUIDAS_MEIO))
    if fim > regras.BRANCAS_SEGUIDAS_FIM:
        resultado["erros"].append("{} páginas em branco no fim; o máximo é {}.".format(fim, regras.BRANCAS_SEGUIDAS_FIM))


def validar(caminho, formato, papel):
    resultado = {"ok": False, "arquivo": str(caminho), "formato": formato, "papel": papel, "erros": [], "avisos": [], "medidas": {}, "nao_medido": []}
    dados = caminho.read_bytes()
    if not dados.startswith(b"%PDF-"):
        resultado["erros"].append("O arquivo não é um PDF.")
        return resultado
    if len(dados) > regras.TAMANHO_MAXIMO_BYTES:
        resultado["erros"].append("O arquivo passa de 650 MB.")
    if b"/Encrypt" in dados:
        resultado["erros"].append("O PDF está bloqueado ou criptografado.")
    if re.search(rb"/Outlines\b", dados):
        resultado["erros"].append("O PDF tem marcadores (bookmarks); a KDP pede para retirar.")
    if re.search(rb"/Annots\b", dados):
        resultado["avisos"].append("O PDF tem links ou anotações; a KDP pede para retirar.")
    if re.search(rb"/Group\s*<<[^>]*?/S\s*/Transparency", dados) or re.search(rb"/ca\s+0?\.\d", dados):
        resultado["avisos"].append("O PDF pode ter transparência. Confira no Previewer da KDP.")

    largura, altura, maximos = regras.FORMATOS[formato]
    medidas_paginas = {(float(a), float(b)) for a, b in re.findall(rb"/MediaBox\s*\[\s*0(?:\.0+)?\s+0(?:\.0+)?\s+([\d.]+)\s+([\d.]+)\s*\]", dados)}
    esperado = (largura * PONTOS, altura * PONTOS)
    if not medidas_paginas:
        resultado["nao_medido"].append("Não consegui ler o tamanho das páginas no arquivo.")
    for l, a in sorted(medidas_paginas):
        if abs(l - esperado[0]) > TOLERANCIA_PT or abs(a - esperado[1]) > TOLERANCIA_PT:
            resultado["erros"].append("Página de {:.2f} x {:.2f} pol.; o formato {} pede {} x {} pol.".format(l / PONTOS, a / PONTOS, formato, largura, altura))

    total = contar_paginas(dados, str(caminho))
    if total is None:
        resultado["nao_medido"].append("Não consegui contar as páginas. Instale o Poppler.")
    else:
        resultado["medidas"]["paginas"] = total
        if total < regras.PAGINAS_MINIMAS:
            resultado["erros"].append("O PDF tem {} páginas; o mínimo da KDP é {}.".format(total, regras.PAGINAS_MINIMAS))
        if total > maximos[papel]:
            resultado["erros"].append("O PDF tem {} páginas; o máximo para {} em papel {} é {}.".format(total, formato, papel, maximos[papel]))
        if total % 2:
            resultado["avisos"].append("Número ímpar de páginas: a KDP arredonda para par.")

    conferir_fontes(dados, str(caminho), resultado)
    paginas = medir_palavras(str(caminho))
    if paginas is None:
        resultado["nao_medido"].append("Margens e páginas em branco não medidas: falta o Poppler (pdftotext).")
    elif total:
        conferir_margens(paginas, total, resultado)
        conferir_brancas(paginas, resultado)
    resultado["nao_medido"].append("Margem e resolução de imagens: confira no Previewer da KDP.")
    resultado["ok"] = not resultado["erros"]
    return resultado


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Confere o PDF do miolo contra as regras da KDP.")
    parser.add_argument("pdf")
    parser.add_argument("--formato", default="6x9")
    parser.add_argument("--papel", default="branco", choices=["branco", "creme"])
    args = parser.parse_args()
    caminho = Path(args.pdf).expanduser()
    if args.formato not in regras.FORMATOS or not caminho.is_file():
        print(json.dumps({"ok": False, "erros": ["Arquivo ou formato inválido."]}, ensure_ascii=False))
        sys.exit(1)
    resultado = validar(caminho, args.formato, args.papel)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    sys.exit(0 if resultado["ok"] else 2)


if __name__ == "__main__":
    main()
