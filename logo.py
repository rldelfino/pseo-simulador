"""Marca da Datalab Global: o frasco com órbita e barras dos simuladores irmãos (copiada EXATAMENTE de 006-pseo-simulador-homeequity/layout.py,
constante LOGO), padronizada em todos os produtos em 21/11/2026. O desenho usa `currentColor`: dentro do `.tile` a cor vem de `--ac` (verde do
imobiliário, #10b981); nos ícones e no favicon a cor é passada por `svg_marca(cor=...)`. `python gerar_icones.py` gera os arquivos de marca."""

COR = "#10b981"  # --ac do simulador imobiliário

SVG = '<svg viewBox="0 0 44 44" width="32" height="32" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="22" cy="29" rx="19" ry="6.2" transform="rotate(-22 22 29)" stroke-width="1.3" opacity=".6"/><path d="M17.5 11.5h9M18.8 11.5V22L9.7 37.6a2.3 2.3 0 0 0 2 3.4h20.6a2.3 2.3 0 0 0 2-3.4L25.2 22V11.5" stroke-width="2"/><g fill="currentColor" stroke="none"><rect x="16" y="34" width="2.2" height="4.6" rx=".6"/><rect x="19.6" y="31" width="2.2" height="7.6" rx=".6"/><rect x="23.2" y="33" width="2.2" height="5.6" rx=".6"/><rect x="26.8" y="29.5" width="2.2" height="9.1" rx=".6"/><rect x="19.4" y="6.6" width="1.7" height="3.4" rx=".5"/><rect x="22.4" y="5" width="1.7" height="5" rx=".5"/><rect x="25.4" y="3.6" width="1.7" height="6.4" rx=".5"/><circle cx="31" cy="9.5" r="1.3"/><circle cx="35.5" cy="5.6" r="1.3"/></g><path d="M31 9.5l4.5-3.9" stroke-width="1.3"/></svg>'

LOGO = '<span class="tile">' + SVG + "</span>"


def svg_marca(tamanho=32, cor=COR):
    """O mesmo SVG do 006, no tamanho e na cor pedidos (para PNG, favicon e og-image)."""
    return SVG.replace('width="32" height="32"', 'width="%d" height="%d"' % (tamanho, tamanho)).replace('stroke="currentColor"', 'stroke="%s"' % cor, 1).replace('fill="currentColor"', 'fill="%s"' % cor)


def svg_icone(tamanho=64, cor=COR):
    """Ícone quadrado (favicon.svg): fundo escuro de cantos arredondados, borda na cor da marca e a marca no centro."""
    interno = svg_marca(40, cor).replace("<svg ", '<svg x="12" y="12" ', 1)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="%d" height="%d" role="img" aria-label="Datalab Global">'
            '<rect width="64" height="64" rx="16" fill="#06251c"/><rect x="0.75" y="0.75" width="62.5" height="62.5" rx="15.25" fill="none" stroke="%s" stroke-opacity="0.5" stroke-width="1.5"/>%s</svg>' % (tamanho, tamanho, cor, interno))
