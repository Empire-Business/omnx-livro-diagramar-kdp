"""Regras oficiais do miolo de paperback na Amazon KDP, consultadas em 08/11/2026.

Fontes:
  https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6  (Set Trim Size, Bleed, and Margins)
  https://kdp.amazon.com/en_US/help/topic/G201857950        (Paperback Submission Guidelines)
  https://kdp.amazon.com/en_US/help/topic/G202145450        (Paperback Fonts)
  https://kdp.amazon.com/en_US/help/topic/G201834260        (Fix Paperback and Hardcover Formatting Issues)

Se a Amazon mudar uma regra, este é o único arquivo a corrigir.
"""

# (até quantas páginas, margem interna mínima em polegadas)
MARGEM_INTERNA = [(150, 0.375), (300, 0.5), (500, 0.625), (700, 0.75), (828, 0.875)]
MARGEM_EXTERNA_MINIMA = 0.25  # superior, inferior e externa, sem sangria
FONTE_MINIMA_PT = 7
PAGINAS_MINIMAS = 24
BRANCAS_SEGUIDAS_MEIO = 4
BRANCAS_SEGUIDAS_FIM = 10
TAMANHO_MAXIMO_BYTES = 650 * 1024 * 1024

# Limite de páginas por formato, tinta preta, Amazon.com: {papel: máximo}
_GRUPO_COMUM = {"branco": 828, "creme": 776}
_GRUPO_8_25 = {"branco": 800, "creme": 750}
_GRUPO_8_5 = {"branco": 590, "creme": 550}
_GRUPO_A4 = {"branco": 780, "creme": 730}

# Formato: (largura, altura, máximos)
FORMATOS = {
    "5x8": (5.0, 8.0, _GRUPO_COMUM),
    "5.06x7.81": (5.06, 7.81, _GRUPO_COMUM),
    "5.25x8": (5.25, 8.0, _GRUPO_COMUM),
    "5.5x8.5": (5.5, 8.5, _GRUPO_COMUM),
    "6x9": (6.0, 9.0, _GRUPO_COMUM),
    "6.14x9.21": (6.14, 9.21, _GRUPO_COMUM),
    "6.69x9.61": (6.69, 9.61, _GRUPO_COMUM),
    "7x10": (7.0, 10.0, _GRUPO_COMUM),
    "7.44x9.69": (7.44, 9.69, _GRUPO_COMUM),
    "7.5x9.25": (7.5, 9.25, _GRUPO_COMUM),
    "8x10": (8.0, 10.0, _GRUPO_COMUM),
    "8.25x6": (8.25, 6.0, _GRUPO_8_25),
    "8.25x8.25": (8.25, 8.25, _GRUPO_8_25),
    "8.5x8.5": (8.5, 8.5, _GRUPO_8_5),
    "8.5x11": (8.5, 11.0, _GRUPO_8_5),
    "8.27x11.69": (8.27, 11.69, _GRUPO_A4),
}


def margem_interna_minima(paginas):
    """Margem interna mínima em polegadas para o número de páginas. None se passar de 828."""
    for limite, margem in MARGEM_INTERNA:
        if paginas <= limite:
            return margem
    return None
