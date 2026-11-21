"""Gera os arquivos de marca a partir do SVG desenhado em logo.py: logo-full.png (cabeçalho), favicon (svg, ico, 32, 192),
apple-touch-icon, logo-schema.png (512, para o schema Organization) e og-image.png (1200x630).

Precisa do Playwright (Chromium) e do Pillow; roda na máquina do dono, fora do CI. Os arquivos ficam em paginas_seo/ e são versionados.
Uso: python gerar_icones.py
"""
import os

from PIL import Image
from playwright.sync_api import sync_playwright

import logo

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "paginas_seo")
FONTES = "file:///" + os.path.join(SAIDA, "fonts").replace("\\", "/")

CSS_FONTES = ("@font-face{font-family:'Inter';font-weight:300 700;src:url('%s/inter-latin.woff2') format('woff2')}"
              "@font-face{font-family:'Playfair Display';font-weight:600 700;src:url('%s/playfair-display-latin.woff2') format('woff2')}" % (FONTES, FONTES))


def _icone_svg(lado, com_barras):
    # versão do ícone com o bloco maior (preenche melhor o quadrado) para favicon e app
    s = logo.svg_icone(lado, com_barras).replace("translate(6.4 5.6) scale(0.8)", "translate(3.2 2.35) scale(0.9)")
    return s


def _pagina(corpo, w, h, fundo="transparent", extra_css=""):
    return ("<html><head><meta charset='utf-8'><style>%s*{box-sizing:border-box;margin:0;padding:0}body{width:%dpx;height:%dpx;background:%s;overflow:hidden;%s}</style></head><body>%s</body></html>"
            % (CSS_FONTES, w, h, fundo, extra_css, corpo))


def _logo_full_html():
    corpo = ("<div style=\"display:flex;align-items:center;gap:6px;height:192px;padding-left:2px\">"
             + logo.svg_marca(176) +
             "<div style=\"display:flex;flex-direction:column;line-height:1\">"
             "<b style=\"font-family:'Playfair Display',serif;font-weight:700;font-size:78px;letter-spacing:-.01em;color:#fff\">Datalab</b>"
             "<i style=\"font-family:'Inter',sans-serif;font-style:normal;font-weight:600;font-size:26px;letter-spacing:.46em;color:#10b981;margin-top:10px;padding-left:4px\">GLOBAL</i>"
             "</div></div>")
    return _pagina(corpo, 488, 192)


def _og_html():
    corpo = ("<div style=\"padding:76px 84px;height:630px;color:#f8fafc;font-family:'Inter',sans-serif;"
             "background:radial-gradient(at 85% 0%,#0f2a24 0,transparent 55%),radial-gradient(at 0% 100%,#0b3b2d 0,transparent 55%),#020617\">"
             "<div style=\"display:flex;align-items:center;gap:20px\">" + logo.svg_marca(120) +
             "<div><b style=\"display:block;font-family:'Playfair Display',serif;font-size:58px;font-weight:700;line-height:1\">Datalab</b>"
             "<i style=\"display:block;font-style:normal;font-size:20px;letter-spacing:.46em;color:#10b981;font-weight:600;margin-top:10px\">GLOBAL</i></div></div>"
             "<h1 style=\"font-family:'Playfair Display',serif;font-weight:600;font-size:74px;line-height:1.08;margin-top:54px;max-width:1000px\">"
             "Quanto vai custar o seu <span style='color:#34d399'>financiamento?</span></h1>"
             "<p style=\"margin-top:26px;font-size:30px;color:#a3b1c6\">Parcela SAC e Price, CET e taxas de 11 bancos. Grátis, sem cadastro.</p></div>")
    return _pagina(corpo, 1200, 630, "#020617")


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch()

        def foto(html, w, h, nome, transparente=True, escala=1):
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=escala)
            # as fontes são arquivos locais: a página precisa vir de file:// (com set_content o Chromium bloqueia o @font-face)
            tmp = os.path.join(SAIDA, "_tmp_icone.html")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(html)
            pg.goto("file:///" + tmp.replace("\\", "/"))
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(400)
            pg.screenshot(path=os.path.join(SAIDA, nome), omit_background=transparente)
            pg.close()
            os.remove(tmp)

        foto(_logo_full_html(), 488, 192, "logo-full.png")
        foto(_pagina(_icone_svg(32, False), 32, 32), 32, 32, "favicon-32.png")
        foto(_pagina(_icone_svg(192, True), 192, 192), 192, 192, "favicon-192.png")
        foto(_pagina(_icone_svg(180, True), 180, 180, "#020617"), 180, 180, "apple-touch-icon.png", transparente=False)
        foto(_pagina(_icone_svg(512, True), 512, 512), 512, 512, "logo-schema.png")
        foto(_pagina(_icone_svg(256, True), 256, 256), 256, 256, "_icone-256.png")
        foto(_og_html(), 1200, 630, "og-image.png", transparente=False)
        b.close()
    img = Image.open(os.path.join(SAIDA, "_icone-256.png")).convert("RGBA")
    img.save(os.path.join(SAIDA, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    os.remove(os.path.join(SAIDA, "_icone-256.png"))
    with open(os.path.join(SAIDA, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(_icone_svg(64, False) + "\n")
    with open(os.path.join(SAIDA, "logo.svg"), "w", encoding="utf-8") as f:
        f.write(logo.svg_marca(256) + "\n")


if __name__ == "__main__":
    main()
