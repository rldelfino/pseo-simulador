"""Gera os arquivos de marca a partir da marca padrão dos simuladores (logo.py, a mesma do 006): logo-full.png (cabeçalho das páginas em Tailwind),
favicon (svg, ico, 32, 192), apple-touch-icon, logo-schema.png (512, schema Organization) e og-image.png (1200x630).

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
AC = logo.COR

CSS_FONTES = ("@font-face{font-family:'Inter';font-weight:300 700;src:url('%s/inter-latin.woff2') format('woff2')}"
              "@font-face{font-family:'Playfair Display';font-weight:600 700;src:url('%s/playfair-display-latin.woff2') format('woff2')}" % (FONTES, FONTES))


def _pagina(corpo, w, h, fundo="transparent"):
    return ("<html><head><meta charset='utf-8'><style>%s*{box-sizing:border-box;margin:0;padding:0}body{width:%dpx;height:%dpx;background:%s;overflow:hidden}</style></head><body>%s</body></html>"
            % (CSS_FONTES, w, h, fundo, corpo))


def _icone_html(lado):
    """Ícone quadrado: o mesmo `.tile` do site (gradiente escuro, borda na cor da marca) com a marca dentro."""
    return ("<div style='width:%dpx;height:%dpx;border-radius:%dpx;display:grid;place-items:center;color:%s;"
            "background:linear-gradient(145deg,#0b2f25,#06101c);border:%dpx solid rgba(16,185,129,.55);box-sizing:border-box'>%s</div>"
            % (lado, lado, lado * 0.26, AC, max(1, lado // 40), logo.svg_marca(int(lado * 0.72))))


def _logo_full_html():
    tile = ("<span style=\"width:150px;height:150px;border-radius:40px;display:grid;place-items:center;color:%s;flex:none;"
            "background:linear-gradient(145deg,rgba(16,185,129,.14),rgba(15,23,42,.6));border:2px solid rgba(16,185,129,.4)\">%s</span>" % (AC, logo.svg_marca(100)))
    texto = ("<span style=\"display:flex;flex-direction:column;line-height:1\">"
             "<b style=\"font-family:'Inter',sans-serif;font-size:52px;font-weight:700;letter-spacing:-.02em;color:#fff\">Datalab</b>"
             "<i style=\"font-family:'Inter',sans-serif;font-style:normal;font-size:19px;letter-spacing:.42em;color:%s;margin-top:10px;font-weight:600\">GLOBAL</i></span>" % AC)
    return _pagina("<div style=\"display:flex;align-items:center;gap:18px;height:192px;padding-left:6px\">" + tile + texto + "</div>", 488, 192)


def _og_html():
    tile = ("<span style=\"width:130px;height:130px;border-radius:36px;display:grid;place-items:center;color:%s;"
            "background:linear-gradient(145deg,rgba(16,185,129,.14),rgba(15,23,42,.6));border:2px solid rgba(16,185,129,.4);box-shadow:0 0 60px -10px rgba(16,185,129,.5)\">%s</span>" % (AC, logo.svg_marca(86)))
    corpo = ("<div style=\"padding:70px 80px;height:630px;color:#f8fafc;font-family:'Inter',sans-serif;"
             "background:radial-gradient(at 80% 0%,#1e293b 0,transparent 55%),radial-gradient(at 0% 100%,#0b3b2d 0,transparent 55%),#020617\">"
             "<div style=\"display:flex;align-items:center;gap:22px\">" + tile +
             "<div><b style=\"display:block;font-size:54px;font-weight:700;letter-spacing:-.02em\">Datalab</b>"
             "<i style=\"display:block;font-style:normal;font-size:19px;letter-spacing:.44em;color:%s;margin-top:10px;font-weight:600\">GLOBAL</i></div></div>" % AC +
             "<h1 style=\"font-family:'Playfair Display',serif;font-weight:600;font-size:74px;line-height:1.08;margin-top:50px;max-width:1000px\">"
             "Quanto vai custar o seu <span style='color:#34d399'>financiamento?</span></h1>"
             "<p style=\"margin-top:26px;font-size:30px;color:#a3b1c6\">Parcela SAC e Price, CET e taxas de 11 bancos. Grátis, sem cadastro.</p></div>")
    return _pagina(corpo, 1200, 630, "#020617")


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch()

        def foto(html, w, h, nome, transparente=True):
            pg = b.new_page(viewport={"width": w, "height": h})
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
        for nome, lado in (("favicon-32.png", 32), ("favicon-192.png", 192), ("logo-schema.png", 512), ("_icone-256.png", 256)):
            foto(_pagina(_icone_html(lado), lado, lado), lado, lado, nome)
        foto(_pagina(_icone_html(180), 180, 180, "#020617"), 180, 180, "apple-touch-icon.png", transparente=False)
        foto(_og_html(), 1200, 630, "og-image.png", transparente=False)
        b.close()
    img = Image.open(os.path.join(SAIDA, "_icone-256.png")).convert("RGBA")
    img.save(os.path.join(SAIDA, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    os.remove(os.path.join(SAIDA, "_icone-256.png"))
    with open(os.path.join(SAIDA, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(logo.svg_icone(64) + "\n")
    with open(os.path.join(SAIDA, "logo.svg"), "w", encoding="utf-8") as f:
        f.write(logo.svg_marca(256) + "\n")


if __name__ == "__main__":
    main()
