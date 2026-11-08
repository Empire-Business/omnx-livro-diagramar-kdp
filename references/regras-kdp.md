# Regras oficiais da Amazon KDP para o miolo de paperback

Consultadas nas páginas de ajuda da KDP em **08/11/2026**. Elas não trazem data de atualização. Antes de um lançamento
importante, abra as páginas de novo. Os números usados pelos scripts ficam em `scripts/kdp_regras.py`.

| Página | Endereço |
|---|---|
| Set Trim Size, Bleed, and Margins | https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6 |
| Paperback Submission Guidelines | https://kdp.amazon.com/en_US/help/topic/G201857950 |
| Paperback Fonts | https://kdp.amazon.com/en_US/help/topic/G202145450 |
| Fix Paperback and Hardcover Formatting Issues | https://kdp.amazon.com/en_US/help/topic/G201834260 |
| Save Your Manuscript File | https://kdp.amazon.com/en_US/help/topic/G202145060 |
| Build Your Book (Word) | https://kdp.amazon.com/en_US/help/topic/G202145400 |

## Margens (sem sangria)

| Páginas | Interna mínima | Superior, inferior e externa |
|---|---|---|
| 24 a 150 | 0,375 pol. (9,6 mm) | mínimo 0,25 pol. (6,4 mm) |
| 151 a 300 | 0,5 pol. (12,7 mm) | mínimo 0,25 pol. |
| 301 a 500 | 0,625 pol. (15,9 mm) | mínimo 0,25 pol. |
| 501 a 700 | 0,75 pol. (19,1 mm) | mínimo 0,25 pol. |
| 701 a 828 | 0,875 pol. (22,3 mm) | mínimo 0,25 pol. |

A KDP recomenda ficar um pouco acima do mínimo, porque itálico pode passar da caixa de texto. A skill aplica o mínimo
oficial da faixa mais 0,125 pol. de folga na interna e 0,75 pol. nas outras três margens. Essas folgas são escolha de
leitura da skill, não regra da Amazon.

## Fonte

- Tamanho mínimo: **7 pt**.
- Toda fonte precisa estar incorporada ao PDF ("Embedded" ou "Embedded Subset"). A página Save Your Manuscript File
  prefere incorporação completa; o Chrome incorpora subconjunto, que a página Paperback Fonts aceita.
- Os tutoriais de Word da KDP sugerem de 9 a 12 pt no corpo, conforme a fonte. É dica, não exigência. A skill usa 11 pt
  por padrão.
- A licença da fonte é responsabilidade do autor.

## Páginas

- Mínimo de 24. O máximo depende do formato, da tinta e do papel. Exemplo: 6 x 9 pol. em tinta preta vai de 24 a 828 em
  papel branco e de 24 a 776 em papel creme. A tabela completa está em `scripts/kdp_regras.py`.
- O total é arredondado para cima até um número par.
- Páginas em branco seguidas: até 4 no início ou no meio, até 10 no fim.
- Numeração sequencial, pares à esquerda e ímpares à direita.

## Arquivo

- Miolo em páginas individuais, com o tamanho exato do formato escolhido quando não há sangria.
- Até 650 MB, sem bloqueio, senha ou criptografia. Nome de arquivo sem emoji ou caractere especial.
- Sem marcas de corte, marcadores (bookmarks), comentários, anotações e objetos invisíveis.
- Imagens em pelo menos 300 DPI. Transparências e camadas achatadas.
- A KDP prefere PDF/X-1a. O navegador gera PDF comum, sem essa certificação. Se o Previewer da KDP reclamar, exporte de
  um programa de editoração.

## Título e autor

Título, nome do autor e dados têm de ser iguais no miolo, na capa, na página de direitos e no cadastro. "John T. Smith"
no cadastro e "J.T. Smith" no arquivo gera erro.

## O que a skill não mede

Margem de imagem, resolução, PDF/X e o resultado do Previewer. O Previewer da KDP, no envio do livro, é a palavra final.
