#!/usr/bin/env python3
"""Transforma capítulos em Markdown no PDF do miolo de um livro impresso para a Amazon KDP.

Uso:
    diagramar.py --capitulos <pasta> --titulo "..." --autor "..." --saida <pasta>
                 [--formato 6x9] [--papel branco|creme] [--subtitulo "..."] [--ano 2026] [--isbn ...]
                 [--corpo 11] [--fonte "Georgia"] [--idioma pt-BR]

Cada arquivo .md da pasta é um capítulo, em ordem natural de nome, com um título "# ..." na primeira
linha de conteúdo. Arquivos com nome começando em "pre-" (dedicatória, por exemplo) entram antes do
sumário, sem número de página e fora do sumário.

Calcula a margem interna pelo número real de páginas: diagrama, conta e refaz se a faixa mudar.
Só usa biblioteca padrão e um navegador Chrome, Edge ou Chromium já instalado.

Códigos de saída: 0 pronto | 1 pedido inválido | 4 falta navegador | 5 falha ao gerar o PDF
"""
import argparse
import datetime
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.dont_write_bytecode = True  # não deixa __pycache__ dentro da skill
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kdp_regras as regras  # noqa: E402

MARGEM_EXTERNA_PADRAO = 0.75  # escolha de leitura; o mínimo oficial está em kdp_regras
FOLGA_INTERNA = 0.125  # a KDP recomenda ficar um pouco acima do mínimo; itálico pode passar da caixa de texto
TEMPO_LIMITE = 180
TAMANHO_TITULO = 1.6


def sair(codigo, status, mensagem, o_que_fazer):
    print(json.dumps({"status": status, "mensagem": mensagem, "o_que_fazer": o_que_fazer}, ensure_ascii=False, indent=2))
    sys.exit(codigo)


def achar_navegador():
    candidatos = [os.environ.get("CHROME_PATH", "")]
    for nome in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "chrome", "msedge"):
        candidatos.append(shutil.which(nome) or "")
    if sys.platform == "darwin":
        for app in ("Google Chrome", "Chromium", "Microsoft Edge", "Brave Browser"):
            candidatos.append("/Applications/{0}.app/Contents/MacOS/{0}".format(app))
    if os.name == "nt":
        for base in (os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""), os.environ.get("LOCALAPPDATA", "")):
            if base:
                candidatos.append(str(Path(base) / "Google/Chrome/Application/chrome.exe"))
                candidatos.append(str(Path(base) / "Microsoft/Edge/Application/msedge.exe"))
    for caminho in candidatos:
        if caminho and Path(caminho).is_file():
            return caminho
    return None


def chave_natural(caminho):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", caminho.name)]


def inline(texto, pasta):
    """Markdown de linha: negrito, itálico, código, link e imagem."""
    guardados = []

    def guardar(marcado):
        guardados.append(marcado)
        return "\x00{}\x00".format(len(guardados) - 1)

    def imagem(achado):
        caminho = (pasta / achado.group(2)).resolve()
        return guardar('<img src="{}" alt="{}">'.format(caminho.as_uri(), html.escape(achado.group(1), quote=True)))

    def link(achado):
        return guardar("{} ({})".format(html.escape(achado.group(1)), html.escape(achado.group(2))))

    texto = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", imagem, texto)
    texto = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, texto)
    texto = re.sub(r"`([^`]+)`", lambda m: guardar("<code>{}</code>".format(html.escape(m.group(1)))), texto)
    texto = html.escape(texto, quote=False)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texto)
    texto = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", texto)
    texto = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", texto)
    return re.sub(r"\x00(\d+)\x00", lambda m: guardados[int(m.group(1))], texto)


def markdown_para_html(texto, pasta, avisos, nome):
    """Converte o subconjunto de Markdown usado em livro. Tabela e HTML cru viram aviso."""
    linhas = texto.replace("\r\n", "\n").split("\n")
    saida, paragrafo, lista, citacao = [], [], None, []

    def fechar():
        nonlocal paragrafo, lista, citacao
        if paragrafo:
            saida.append("<p>{}</p>".format(inline(" ".join(paragrafo), pasta)))
            paragrafo = []
        if lista:
            tag, itens = lista
            saida.append("<{0}>{1}</{0}>".format(tag, "".join("<li>{}</li>".format(inline(i, pasta)) for i in itens)))
            lista = None
        if citacao:
            saida.append("<blockquote><p>{}</p></blockquote>".format(inline(" ".join(citacao), pasta)))
            citacao = []

    for bruta in linhas:
        linha = bruta.strip()
        if not linha:
            fechar()
            continue
        titulo = re.match(r"^(#{1,3})\s+(.*)$", linha)
        if titulo:
            fechar()
            nivel = len(titulo.group(1))
            saida.append("<h{0}>{1}</h{0}>".format(nivel, inline(titulo.group(2).strip(), pasta)))
            continue
        if re.fullmatch(r"(\*\s*){3,}|(-\s*){3,}|(_\s*){3,}", linha):
            fechar()
            saida.append('<p class="separador">* * *</p>')
            continue
        if linha.startswith(">"):
            if paragrafo or lista:
                fechar()
            citacao.append(linha.lstrip("> ").strip())
            continue
        item = re.match(r"^(?:[-*+]\s+|(\d+)[.)]\s+)(.*)$", linha)
        if item:
            if paragrafo or citacao:
                fechar()
            tag = "ol" if item.group(1) else "ul"
            if not lista or lista[0] != tag:
                fechar()
                lista = (tag, [])
            lista[1].append(item.group(2))
            continue
        if "|" in linha and re.search(r"\|\s*:?-{2,}", linha):
            avisos.append("{}: tabela em Markdown não é suportada e saiu como texto.".format(nome))
        if linha.startswith("<"):
            avisos.append("{}: HTML dentro do texto saiu como texto: {}".format(nome, linha[:40]))
        if lista:
            fechar()
        if citacao:
            fechar()
        paragrafo.append(linha)
    fechar()
    return "\n".join(saida)


def montar_css(formato, interna, externa, corpo, fonte):
    largura, altura, _ = regras.FORMATOS[formato]
    numero = "font: {}pt {}; color: #000;".format(max(corpo - 1, regras.FONTE_MINIMA_PT), fonte)
    return """
@page {{ size: {l}in {a}in; margin: {e}in; }}
@page :left {{ margin-left: {e}in; margin-right: {i}in; @bottom-left {{ content: counter(page); {n} }} }}
@page :right {{ margin-left: {i}in; margin-right: {e}in; @bottom-right {{ content: counter(page); {n} }} }}
@page frente:left {{ @bottom-left {{ content: none; }} }}
@page frente:right {{ @bottom-right {{ content: none; }} }}
html, body {{ margin: 0; padding: 0; background: #fff; color: #000; }}
body {{ font: {c}pt/1.45 {f}; text-align: justify; hyphens: auto; orphans: 2; widows: 2; }}
p {{ margin: 0; text-indent: 1.4em; }}
h1 + p, h2 + p, h3 + p, blockquote + p, .separador + p, .imagem + p {{ text-indent: 0; }}
h1, h2, h3 {{ text-align: left; hyphens: none; break-after: avoid; font-weight: bold; line-height: 1.2; }}
h1 {{ font-size: {t}em; margin: 1.5in 0 0.6in; }}
h2 {{ font-size: 1.2em; margin: 1.2em 0 0.5em; }}
h3 {{ font-size: 1.05em; margin: 1em 0 0.4em; }}
blockquote {{ margin: 0.8em 1.2em; font-style: italic; }}
blockquote p {{ text-indent: 0; }}
ul, ol {{ margin: 0.5em 0 0.5em 1.4em; padding: 0; }}
.separador {{ text-align: center; text-indent: 0; margin: 0.9em 0; }}
img {{ max-width: 100%; height: auto; display: block; margin: 0.8em auto; break-inside: avoid; }}
code {{ font-family: monospace; font-size: 0.92em; }}
section {{ break-before: page; }}
section:first-of-type {{ break-before: auto; }}
.frente {{ page: frente; }}
.rosto {{ text-align: center; hyphens: none; }}
.rosto h1 {{ text-align: center; margin: 1.6in 0 0.3in; font-size: 2em; }}
.rosto .sub {{ font-size: 1.2em; margin-bottom: 1in; text-indent: 0; }}
.rosto .autor {{ font-size: 1.2em; text-indent: 0; }}
.direitos {{ text-align: left; font-size: 0.9em; hyphens: none; padding-top: 3.8in; }}
.direitos p {{ text-indent: 0; margin-bottom: 0.5em; }}
.sumario h1 {{ margin-top: 0.5in; }}
.sumario ol {{ list-style: none; margin: 0; }}
.sumario li {{ display: flex; align-items: baseline; gap: 0.5em; margin-bottom: 0.45em; text-align: left; hyphens: none; }}
.sumario .nome {{ flex: 1; }}
.branca p {{ color: #fff; }}
""".format(l=largura, a=altura, e=externa, i=interna, n=numero, c=corpo, f=fonte, t=TAMANHO_TITULO)


def pagina_html(titulo, idioma, css, corpo):
    return '<!doctype html><html lang="{}"><head><meta charset="utf-8"><title>{}</title><style>{}</style></head><body>{}</body></html>'.format(
        html.escape(idioma, quote=True), html.escape(titulo), css, corpo)


class Impressora:
    """Gera PDFs pelo navegador e conta as páginas."""

    def __init__(self, navegador, pasta_temp):
        self.navegador = navegador
        self.pasta_temp = pasta_temp
        self.perfil = str(pasta_temp / "perfil")
        self.n = 0

    def pdf(self, conteudo_html):
        self.n += 1
        origem = self.pasta_temp / "p{}.html".format(self.n)
        destino = self.pasta_temp / "p{}.pdf".format(self.n)
        origem.write_text(conteudo_html, encoding="utf-8")
        comando = [self.navegador, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                   "--no-pdf-header-footer", "--user-data-dir=" + self.perfil,
                   "--print-to-pdf=" + str(destino), origem.as_uri()]
        try:
            subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=TEMPO_LIMITE)
        except subprocess.TimeoutExpired:
            sair(5, "falha_pdf", "O navegador demorou demais para gerar o PDF.", "Tente de novo com menos capítulos para achar o problema.")
        if not destino.exists():
            sair(5, "falha_pdf", "O navegador não gerou o PDF.", "Atualize o navegador e tente de novo.")
        return destino

    def paginas(self, conteudo_html):
        dados = self.pdf(conteudo_html).read_bytes()
        return len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", dados))


def ler_capitulos(pasta, avisos):
    arquivos = sorted((p for p in pasta.glob("*.md") if not p.name.startswith(".")), key=chave_natural)
    pre, capitulos = [], []
    for arquivo in arquivos:
        texto = arquivo.read_text(encoding="utf-8")
        achado = re.search(r"^#\s+(.+)$", texto, re.M)
        if not achado:
            sair(1, "capitulo_sem_titulo", "{} não tem título começando com '# '.".format(arquivo.name),
                 "Peça à pessoa o título do capítulo. Não invente.")
        item = {"nome": arquivo.name, "titulo": achado.group(1).strip(), "html": markdown_para_html(texto, arquivo.parent, avisos, arquivo.name)}
        (pre if arquivo.name.lower().startswith("pre-") else capitulos).append(item)
    if not capitulos:
        sair(1, "sem_capitulos", "Não achei capítulos .md em {}.".format(pasta), "Confira a pasta com a pessoa.")
    return pre, capitulos


def rosto(args):
    sub = '<p class="sub">{}</p>'.format(html.escape(args.subtitulo)) if args.subtitulo else ""
    return '<section class="frente rosto"><h1>{}</h1>{}<p class="autor">{}</p></section>'.format(
        html.escape(args.titulo), sub, html.escape(args.autor))


def direitos(args):
    partes = ["<p>© {} {}. Todos os direitos reservados.</p>".format(args.ano, html.escape(args.autor))]
    if args.isbn:
        partes.append("<p>ISBN {}</p>".format(html.escape(args.isbn)))
    return '<section class="frente direitos">{}</section>'.format("".join(partes))


def sumario(capitulos, numeros):
    itens = "".join('<li><span class="nome">{}</span><span>{}</span></li>'.format(html.escape(c["titulo"]), n)
                    for c, n in zip(capitulos, numeros))
    return '<section class="frente sumario"><h1>Sumário</h1><ol>{}</ol></section>'.format(itens)


BRANCA = '<section class="frente branca"><p>&nbsp;</p></section>'


def diagramar(args, impressora, capitulos, pre, interna):
    """Conta as páginas de cada parte e monta o livro. Devolve (html, paginas, numeros)."""
    css = montar_css(args.formato, interna, args.margem_externa, args.corpo, args.fonte)
    pag = lambda corpo: pagina_html(args.titulo, args.idioma, css, corpo)  # noqa: E731
    frente = [rosto(args), direitos(args)] + ['<section class="frente">{}</section>'.format(p["html"]) for p in pre]
    paginas_frente = [impressora.paginas(pag(parte)) for parte in frente]
    paginas_cap = [impressora.paginas(pag("<section>{}</section>".format(c["html"]))) for c in capitulos]
    provisorio = sumario(capitulos, [999] * len(capitulos))
    paginas_sumario = impressora.paginas(pag(provisorio))

    partes, atual = [], 0
    def colocar(trecho, n_paginas, recto=False):
        nonlocal atual
        if recto and atual % 2 == 1:
            partes.append(BRANCA)
            atual += 1
        partes.append(trecho)
        inicio = atual + 1
        atual += n_paginas
        return inicio

    for trecho, n in zip(frente, paginas_frente):
        colocar(trecho, n, recto=True)
    if atual % 2 == 1:
        partes.append(BRANCA)
        atual += 1

    # O sumário entra depois: precisa dos números dos capítulos, que dependem do tamanho dele.
    indice_sumario = len(partes)
    partes.append("")
    atual += paginas_sumario

    numeros = []
    for capitulo, n in zip(capitulos, paginas_cap):
        numeros.append(colocar("<section>{}</section>".format(capitulo["html"]), n, recto=True))
    partes[indice_sumario] = sumario(capitulos, numeros)
    if atual % 2 == 1:  # a KDP arredonda para par; a branca final evita surpresa
        partes.append(BRANCA)
        atual += 1
    return pag("".join(partes)), atual, numeros


def nome_seguro(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-") or "livro"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Diagrama o miolo de um livro impresso para a Amazon KDP.")
    parser.add_argument("--capitulos", required=True)
    parser.add_argument("--titulo", required=True)
    parser.add_argument("--autor", required=True)
    parser.add_argument("--saida", required=True)
    parser.add_argument("--formato", default="6x9")
    parser.add_argument("--papel", default="branco", choices=["branco", "creme"])
    parser.add_argument("--subtitulo", default="")
    parser.add_argument("--ano", type=int, default=datetime.date.today().year)
    parser.add_argument("--isbn", default="")
    parser.add_argument("--corpo", type=float, default=11.0)
    parser.add_argument("--fonte", default="Georgia, 'Times New Roman', serif")
    parser.add_argument("--idioma", default="pt-BR")
    parser.add_argument("--margem-externa", type=float, default=MARGEM_EXTERNA_PADRAO)
    args = parser.parse_args()

    if args.formato not in regras.FORMATOS:
        sair(1, "formato_invalido", "O formato {} não está na lista da KDP.".format(args.formato),
             "Formatos aceitos: {}.".format(", ".join(regras.FORMATOS)))
    if args.corpo < regras.FONTE_MINIMA_PT:
        sair(1, "fonte_pequena", "Corpo {} pt está abaixo do mínimo oficial de {} pt.".format(args.corpo, regras.FONTE_MINIMA_PT), "Use um corpo maior.")
    if args.margem_externa < regras.MARGEM_EXTERNA_MINIMA:
        sair(1, "margem_pequena", "Margem de {} pol. abaixo do mínimo oficial de {} pol.".format(args.margem_externa, regras.MARGEM_EXTERNA_MINIMA), "Use uma margem maior.")
    pasta = Path(args.capitulos).expanduser().resolve()
    if not pasta.is_dir():
        sair(1, "pasta_invalida", "Não achei a pasta {}.".format(pasta), "Confira o caminho com a pessoa.")
    navegador = achar_navegador()
    if not navegador:
        sair(4, "falta_navegador", "Não encontrei Chrome, Edge ou Chromium.", "Peça para instalar o Google Chrome ou indique CHROME_PATH.")

    avisos = []
    pre, capitulos = ler_capitulos(pasta, avisos)
    saida = Path(args.saida).expanduser().resolve()
    saida.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="kdp-") as temp:
        impressora = Impressora(navegador, Path(temp))
        interna = regras.MARGEM_INTERNA[0][1] + FOLGA_INTERNA
        for _ in range(6):
            pagina, total, numeros = diagramar(args, impressora, capitulos, pre, interna)
            necessaria = regras.margem_interna_minima(total)
            if necessaria is None or necessaria + FOLGA_INTERNA <= interna:
                break
            interna = necessaria + FOLGA_INTERNA  # só aumenta: nunca oscila e nunca fica abaixo do mínimo
        pdf_final = impressora.pdf(pagina)
        reais = len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", pdf_final.read_bytes()))
        if reais != total:
            avisos.append("Previ {} páginas e saíram {}. Confira o sumário.".format(total, reais))
        nome_pdf = "{}-miolo-{}.pdf".format(nome_seguro(args.titulo), args.formato.replace(".", "_"))
        destino = saida / nome_pdf
        versao = 1
        while destino.exists():
            versao += 1
            destino = saida / "{}-miolo-{}-v{}.pdf".format(nome_seguro(args.titulo), args.formato.replace(".", "_"), versao)
        shutil.copyfile(str(pdf_final), str(destino))

    minimo = regras.margem_interna_minima(reais)
    if reais < regras.PAGINAS_MINIMAS:
        avisos.append("O livro tem {} páginas; a KDP exige no mínimo {}.".format(reais, regras.PAGINAS_MINIMAS))
    maximo = regras.FORMATOS[args.formato][2][args.papel]
    if reais > maximo:
        avisos.append("O livro tem {} páginas; o máximo para {} em papel {} é {}.".format(reais, args.formato, args.papel, maximo))
    if args.corpo < 9:
        avisos.append("Corpo {} pt é aceito pela KDP (mínimo {} pt), mas fica difícil de ler.".format(args.corpo, regras.FONTE_MINIMA_PT))
    relatorio = {
        "status": "pronto", "pdf": str(destino), "paginas": reais, "formato": args.formato, "papel": args.papel,
        "margens_polegadas": {"interna": interna, "externa": args.margem_externa, "superior": args.margem_externa, "inferior": args.margem_externa},
        "margem_interna_minima_oficial": minimo, "corpo_pt": args.corpo, "fonte": args.fonte,
        "capitulos": [{"titulo": c["titulo"], "pagina": n} for c, n in zip(capitulos, numeros)],
        "avisos": avisos,
    }
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
