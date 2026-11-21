"""Servidor local de paginas_seo/ que imita o Cloudflare Pages: URLs sem .html e os cabeçalhos de paginas_seo/_headers (inclusive o "!" que
remove um cabeçalho herdado). Serve só para os testes de navegador (fora do CI). Uso nos testes: `with servir() as base: ...`.
"""
import contextlib
import fnmatch
import http.server
import os
import threading

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(AQUI, "paginas_seo")


def ler_regras(caminho=None):
    """[(padrão, [(nome, valor|None)])]; valor None = remover o cabeçalho."""
    regras = []
    atual = None
    with open(caminho or os.path.join(PASTA, "_headers"), encoding="utf-8") as f:
        for linha in f:
            bruto = linha.rstrip("\r\n")
            if not bruto.strip() or bruto.lstrip().startswith("#"):
                continue
            if not bruto.startswith((" ", "\t")):
                atual = (bruto.strip(), [])
                regras.append(atual)
            elif atual is not None:
                t = bruto.strip()
                if t.startswith("!"):
                    atual[1].append((t[1:].strip(), None))
                elif ":" in t:
                    nome, valor = t.split(":", 1)
                    atual[1].append((nome.strip(), valor.strip()))
    return regras


def cabecalhos_para(caminho_url, regras):
    saida = {}
    for padrao, itens in regras:
        if fnmatch.fnmatchcase(caminho_url, padrao):
            for nome, valor in itens:
                if valor is None:
                    saida.pop(nome, None)
                elif nome in saida:
                    saida[nome] = saida[nome] + ", " + valor
                else:
                    saida[nome] = valor
    return saida


def _manipulador(regras):
    class M(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=PASTA, **k)

        def log_message(self, *a):
            pass

        def translate_path(self, path):
            p = path.split("?", 1)[0].split("#", 1)[0]
            if p.endswith("/"):
                p += "index"
            real = super().translate_path(p)
            if not os.path.exists(real) and os.path.exists(real + ".html"):
                return real + ".html"
            return real

        def end_headers(self):
            u = getattr(self, "path", "/").split("?", 1)[0]
            for nome, valor in cabecalhos_para(u, regras).items():
                if nome.lower() == "content-security-policy":
                    # o WebKit tenta https em 127.0.0.1 por causa de upgrade-insecure-requests; no servidor local (http) a diretiva sai
                    valor = valor.replace("; upgrade-insecure-requests", "")
                self.send_header(nome, valor)
            super().end_headers()
    return M


@contextlib.contextmanager
def servir(porta=0):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", porta), _manipulador(ler_regras()))
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield "http://127.0.0.1:%d" % srv.server_address[1]
    finally:
        srv.shutdown()
        srv.server_close()
