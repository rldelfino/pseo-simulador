"""Marca da Datalab Global no simulador imobiliário: um bloco isométrico (o "dado" e o "imóvel") com três barras que sobem na face da esquerda.

Desenhado à mão em SVG (sem filtro, sem brilho, sem órbita): faces chapadas em três tons de verde, cantos arredondados
pelo traço, fio de separação entre as faces. A geometria é calculada aqui (ângulos de 30 graus, proporções exatas), não
digitada no olho. `python gerar_icones.py` transforma estas formas em favicon, ícones e imagem de compartilhamento.
"""
import math

# bloco isométrico em viewBox 64x64
CX, CY, R = 32.0, 33.0, 24.0
DX = R * math.sqrt(3) / 2  # meia largura do hexágono
DY = R / 2                 # meia altura das laterais

TOPO = (CX, CY - R)
UD = (CX + DX, CY - DY)    # canto de cima, direita
BD = (CX + DX, CY + DY)    # canto de baixo, direita
BASE = (CX, CY + R)
BE = (CX - DX, CY + DY)    # canto de baixo, esquerda
UE = (CX - DX, CY - DY)    # canto de cima, esquerda
MEIO = (CX, CY)

TOM_TOPO = "#6ee7b7"
TOM_ESQ = "#10b981"
TOM_DIR = "#047857"
TOM_BARRA = "#ecfdf5"
FUNDO_ESCURO = "#04251c"


def _pts(*ps):
    return " ".join("%.2f,%.2f" % p for p in ps)


def _barras():
    """Três barras na face da esquerda, paralelas às arestas (a base e o topo da face descem para a direita)."""
    incl = DY / DX  # inclinação das arestas da face esquerda
    x0 = UE[0]
    larg, vao = 3.6, 2.6
    alturas = (7.0, 12.0, 17.0)
    ini = x0 + 3.4
    saida = []
    for k, h in enumerate(alturas):
        xa = ini + k * (larg + vao)
        xb = xa + larg
        base_a = BE[1] + (xa - x0) * incl
        base_b = BE[1] + (xb - x0) * incl
        pts = ((xa, base_a - 3.2), (xb, base_b - 3.2), (xb, base_b - 3.2 - h), (xa, base_a - 3.2 - h))
        saida.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="0.9" stroke-linejoin="round"/>' % (_pts(*pts), TOM_BARRA, TOM_BARRA))
    return "".join(saida)


def marca(com_barras=True, id_classe=None):
    """Só o bloco, sem fundo. `com_barras=False` para tamanhos muito pequenos."""
    esq = _pts(UE, MEIO, BASE, BE)
    dir_ = _pts(UD, BD, BASE, MEIO)
    topo = _pts(TOPO, UD, MEIO, UE)
    traco = 'stroke="%s" stroke-width="1.1" stroke-linejoin="round"' % FUNDO_ESCURO
    corpo = ('<polygon points="%s" fill="%s" %s/><polygon points="%s" fill="%s" %s/><polygon points="%s" fill="%s" %s/>'
             % (esq, TOM_ESQ, traco, dir_, TOM_DIR, traco, topo, TOM_TOPO, traco))
    # fio de luz na aresta de cima (acabamento, não efeito)
    luz = '<polyline points="%s" fill="none" stroke="#d1fae5" stroke-width="0.9" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>' % _pts(UE, TOPO, UD)
    return corpo + (_barras() if com_barras else "") + luz


def svg_marca(tamanho=64, com_barras=True, titulo=None):
    t = '<title>%s</title>' % titulo if titulo else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="%d" height="%d" role="img" aria-label="Datalab Global">%s%s</svg>'
            % (tamanho, tamanho, t, marca(com_barras)))


def svg_icone(tamanho=64, com_barras=True):
    """Ícone quadrado (favicon / app): fundo escuro de cantos arredondados e o bloco centralizado."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="%d" height="%d" role="img" aria-label="Datalab Global">'
            '<rect width="64" height="64" rx="15" fill="#052e22"/><rect x="0.75" y="0.75" width="62.5" height="62.5" rx="14.25" fill="none" stroke="#10b981" stroke-opacity="0.45" stroke-width="1.5"/>'
            '<g transform="translate(6.4 5.6) scale(0.8)">%s</g></svg>' % (tamanho, tamanho, marca(com_barras)))


if __name__ == "__main__":
    print(svg_icone())
