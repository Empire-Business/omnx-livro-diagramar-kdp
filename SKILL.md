---
name: omnx-livro-diagramar-kdp
description: "Transforma capítulos em Markdown no PDF do miolo de um livro impresso para a Amazon KDP, com margens calculadas pelo número real de páginas, sumário, numeração e conferência contra as regras oficiais da KDP. Use quando pedirem 'diagramar meu livro para a Amazon', 'preparar o miolo para o KDP', 'gerar o PDF do livro para imprimir', 'calcular margens do KDP', 'validar meu PDF no KDP' ou 'formatar livro de bolso paperback'. Não use para e-book reflowable, capa do livro, livro de capa dura, livro com imagem sangrando até a borda nem para escrever o livro; texto de venda da página do livro é com a rita e trabalho acadêmico em ABNT, com a lucia."
---

# Diagramar livro para a Amazon KDP

Objetivo: gerar o PDF do miolo de um paperback sem sangria, pronto para o Previewer da KDP. Os caminhos desta skill são
relativos à pasta deste `SKILL.md`. Regras oficiais e fontes, com data de consulta, em `references/regras-kdp.md`.

## Antes de começar

Confirme que é paperback sem sangria e que os capítulos estão em Markdown. Se o texto estiver em Word, peça para
exportar ou converta com o aceite da pessoa, sem mudar o conteúdo.

## Passos

1. **Colete**, uma pergunta por vez: pasta dos capítulos, título, nome do autor como cadastrado na KDP, formato (padrão
   `6x9`), papel (branco ou creme), onde salvar. Nunca salve dentro da pasta da skill.
2. **Confira a pasta.** Cada `.md` é um capítulo, em ordem natural de nome, com `# Título`. Arquivos começando com `pre-`
   (dedicatória, por exemplo) entram antes do sumário, sem número. Sem título, pergunte; não invente.
3. **Mostre o plano e peça "pode gerar"**: formato, papel, título, autor, corpo e fonte. Em seguida:
   ```bash
   python3 scripts/diagramar.py --capitulos "<pasta>" --titulo "<título>" --autor "<autor>" --saida "<pasta de saída>" \
       --formato 6x9 --papel branco [--subtitulo "..."] [--ano 2026] [--isbn "..."] [--corpo 11]
   ```
   O script gera folha de rosto, página de direitos, sumário com página de cada capítulo, capítulos em página ímpar e
   numeração. Ele mede as páginas de verdade e, se o livro mudar de faixa, refaz com a margem certa. Nunca sobrescreve:
   cria `-v2`, `-v3`.
4. **Valide:**
   ```bash
   python3 scripts/validar_pdf.py "<pdf>" --formato 6x9 --papel branco
   ```
   Corrija os `erros`. Avalie os `avisos`. Conte à pessoa o que está em `nao_medido`.
5. **Abra o PDF** e olhe a folha de rosto, o sumário e uma página de texto.
6. **Entregue** o PDF, as margens aplicadas, o número de páginas e os avisos. Diga que a palavra final é do Previewer,
   no envio do livro em kdp.amazon.com, que a pessoa faz na conta dela.

## Só as margens

Se a pessoa pedir apenas o cálculo das margens, responda pela tabela de `references/regras-kdp.md`: a interna mínima da
faixa de páginas e as demais, sem gerar PDF.

## Regras

- Os números oficiais estão em `references/regras-kdp.md` e em `scripts/kdp_regras.py`. Não use número de memória. Se a
  pessoa disser que a regra mudou, confira a página da KDP e atualize esses dois arquivos.
- Mínimo oficial de fonte: 7 pt. O padrão da skill é 11 pt por leitura, não por regra da KDP.
- Menos de 24 páginas é erro da KDP: avise e não invente texto nem páginas para completar.
- Não altere o texto dos capítulos. A página de direitos é um modelo simples: a pessoa revisa e decide.
- Não envie nada à KDP nem cadastre o livro. Essa parte é da pessoa.
- Tabelas e HTML dentro do Markdown saem como texto, com aviso no relatório.

## Outro sistema operacional

- Python 3 só com biblioteca padrão, mais Chrome, Edge ou Chromium. No Windows, chame `py -3 scripts/diagramar.py`.
- O navegador é procurado nos lugares comuns de Mac, Windows e Linux; se não achar, defina `CHROME_PATH`. Precisa ser
  uma versão recente, que coloque número de página no rodapé.
- `validar_pdf.py` mede margens e páginas em branco com o Poppler (`pdftotext`, `pdffonts`). Instale com o aceite da
  pessoa: Homebrew no Mac (`poppler`), winget ou o pacote oficial no Windows, apt no Linux (`poppler-utils`). Sem ele, faz
  a conferência básica e lista em `nao_medido` o que ficou de fora.
- A fonte padrão é Georgia, e no Linux cai para uma serifada do sistema. Se trocar de fonte, use uma com licença comercial
  e com as versões itálica e negrito instaladas.
- A IA testa no computador da pessoa e conta o que realmente funcionou.

## Outra ferramenta (Codex e outras)

Compatível com Claude Code, Codex e outras ferramentas de agentes, em Mac, Windows e Linux. Se a pessoa pedir para instalar
fora do Claude Code, a IA dela adapta na hora, testa no computador dela e conta o que realmente funcionou:
