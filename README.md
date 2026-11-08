# Livro para KDP

Transforma capítulos em Markdown no PDF do miolo de um livro impresso para a Amazon KDP, com margens calculadas pelo número real de páginas, sumário, numeração e conferência contra as regras oficiais da KDP (consultadas em 08/11/2026; endereços em `references/regras-kdp.md`).

Guia visual: abra o `COMO-FUNCIONA.html` desta pasta (dois cliques; funciona sem internet).

## Como instalar

**Direto do GitHub:** no Claude Code, diga: "Instale a skill a partir de https://github.com/Empire-Business/omnx-livro-diagramar-kdp". Para atualizar, diga: "Atualize a skill a partir de https://github.com/Empire-Business/omnx-livro-diagramar-kdp". A IA baixa e copia os arquivos.

Se você já baixou esta pasta:

O caminho mais fácil é pedir para a sua IA:

1. Abra o Claude Code numa conversa nova.
2. Diga: "Instale a skill omnx-livro-diagramar-kdp a partir desta pasta" e indique onde a pasta está.
3. A IA copia os arquivos. Você vai ver uma mensagem dizendo que a skill foi instalada.
4. Feche e abra a conversa de novo, para a skill aparecer.

### Mac ou Linux, se preferir fazer sem a IA

Peça para a IA executar o arquivo `install.sh`. Ele copia a pasta para `~/.claude/skills/omnx-livro-diagramar-kdp` (`~` é a sua pasta pessoal).

### Windows

1. Peça para a IA: "Copie esta pasta para `%USERPROFILE%\.claude\skills\omnx-livro-diagramar-kdp`".
2. Sem IA: copie a pasta com esse nome para `%USERPROFILE%\.claude\skills\` pelo Explorador de Arquivos.
3. Feche e abra a conversa.

## Como usar

- "Diagrama meu livro para a Amazon KDP."
- "Gera o PDF do miolo em 6x9, papel creme."
- "Confere se este PDF passa nas regras da KDP."
- "Calcula as margens do KDP para um livro de 320 páginas."

## O que você precisa ter

- Claude Code instalado
- Python 3 e Google Chrome, Edge ou Chromium
- Poppler, para medir as margens (a IA instala com o seu aceite)
- Capítulos em Markdown

## O que esta skill não faz

- Capa do livro
- E-book que se ajusta à tela
- Capa dura e imagens que vão até a borda
- Escrever ou mudar o texto
- Cadastrar e enviar o livro na KDP
- Revisar a página de direitos autorais
- Garantir a licença comercial da fonte
- Imagens: margem e resolução de 300 DPI
- PDF/X, formato preferido da KDP: sai PDF comum
- Se o Previewer reclamar, é ele quem manda

## Outra ferramenta

Funciona em Mac, Windows e Linux, no Claude Code e no Codex. Na instalação, a própria IA faz as adaptações necessárias para o seu computador.

Atualizado em 08/11/2026.
