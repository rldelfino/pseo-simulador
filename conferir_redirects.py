"""Confere paginas_seo/_redirects (Cloudflare Pages): limites, destinos que existem, nenhuma cadeia nem loop e cobertura das páginas removidas.

Uso: python conferir_redirects.py [ref_git]   (padrão: d4538d0e3, o estado do site ANTES do enxugamento de 20/11/2026)
Sai com 1 se algo estiver errado. Também é usado por tests/test_redirects.py.
Limites do Cloudflare Pages: 2.000 regras estáticas, 100 com curinga (* ou :placeholder), 2.100 no total.
"""
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(AQUI, "paginas_seo")
LIMITE_ESTATICAS, LIMITE_DINAMICAS = 2000, 100
REF_ANTES = "d4538d0e3"  # commit do main logo antes do enxugamento (1.799 páginas a mais)


def ler_regras(caminho=None):
    regras = []
    with open(caminho or os.path.join(PASTA, "_redirects"), encoding="utf-8") as f:
        for linha in f:
            t = linha.strip()
            if not t or t.startswith("#"):
                continue
            partes = t.split()
            origem, destino = partes[0], partes[1]
            codigo = int(partes[2]) if len(partes) > 2 else 302
            regras.append((origem, destino, codigo))
    return regras


def _dinamica(origem):
    return "*" in origem or ":" in origem


def _casa(origem, caminho):
    """Devolve (True, splat) se `caminho` casa com a regra. Só `*` (curinga) e correspondência exata, que é o que o arquivo usa."""
    if "*" not in origem:
        return (origem == caminho), ""
    pre, _, pos = origem.partition("*")
    if caminho.startswith(pre) and caminho.endswith(pos) and len(caminho) >= len(pre) + len(pos):
        return True, caminho[len(pre):len(caminho) - len(pos) if pos else len(caminho)]
    return False, ""


def seguir(caminho, regras, max_saltos=5):
    """Aplica as regras na ordem (a primeira que casa vale, como no Cloudflare). Devolve (destino_final, saltos, loop)."""
    visitados = [caminho]
    saltos = 0
    while saltos < max_saltos:
        for origem, destino, _ in regras:
            ok, splat = _casa(origem, caminho)
            if ok:
                novo = destino.replace(":splat", splat)
                saltos += 1
                if novo in visitados:
                    return novo, saltos, True
                visitados.append(novo)
                caminho = novo
                break
        else:
            return caminho, saltos, False
    return caminho, saltos, True


def existe(caminho):
    if caminho == "/":
        return os.path.exists(os.path.join(PASTA, "index.html"))
    base = caminho.lstrip("/").split("?")[0].split("#")[0]
    return os.path.exists(os.path.join(PASTA, base + ".html")) or os.path.exists(os.path.join(PASTA, base))


def paginas_antigas(ref=None):
    ref = ref or REF_ANTES
    """Páginas .html que existiam em `ref` e não existem mais em paginas_seo/. None se o git não responder."""
    try:
        saida = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, "paginas_seo"], cwd=AQUI, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    nomes = [n[len("paginas_seo/"):] for n in saida.splitlines() if n.startswith("paginas_seo/") and n.endswith(".html") and "/" not in n[len("paginas_seo/"):]]
    return sorted(n for n in nomes if not os.path.exists(os.path.join(PASTA, n)))


def conferir(ref=None):
    ref = ref or REF_ANTES
    erros = []
    regras = ler_regras()
    din = sum(1 for o, _, _ in regras if _dinamica(o))
    est = len(regras) - din
    if est > LIMITE_ESTATICAS:
        erros.append("%d regras estáticas (limite %d)" % (est, LIMITE_ESTATICAS))
    if din > LIMITE_DINAMICAS:
        erros.append("%d regras com curinga (limite %d)" % (din, LIMITE_DINAMICAS))
    for origem, destino, codigo in regras:
        if codigo != 301:
            erros.append("%s não é 301" % origem)
        fim, saltos, loop = seguir(destino.replace(":splat", "x"), regras)
        if loop or saltos:
            erros.append("cadeia ou loop: %s -> %s -> ... %s (%d salto(s) a mais)" % (origem, destino, fim, saltos))
        if not existe(destino.replace(":splat", "x")):
            erros.append("destino inexistente: %s -> %s" % (origem, destino))
    antigas = paginas_antigas(ref)
    cobertas = 0
    if antigas is not None:
        for nome in antigas:
            if nome in ("404.html",):
                continue
            url = "/" + nome[:-5]
            fim, saltos, loop = seguir(url, regras)
            if saltos != 1 or loop or not existe(fim):
                erros.append("página removida sem 301 direto para uma página que existe: %s -> %s (%d salto(s), loop=%s)" % (url, fim, saltos, loop))
            else:
                cobertas += 1
    return {"estaticas": est, "dinamicas": din, "removidas": None if antigas is None else len(antigas), "cobertas": cobertas, "erros": erros}


if __name__ == "__main__":
    r = conferir(sys.argv[1] if len(sys.argv) > 1 else REF_ANTES)
    print("regras estáticas: %(estaticas)d (limite %(le)d) · com curinga: %(dinamicas)d (limite %(ld)d)" % dict(r, le=LIMITE_ESTATICAS, ld=LIMITE_DINAMICAS))
    print("páginas removidas em relação ao git: %s · com 301 de um salto para página existente: %d" % (r["removidas"], r["cobertas"]))
    for e in r["erros"]:
        print("ERRO " + e)
    print("OK: 0 loops, 0 cadeias, 0 destinos quebrados" if not r["erros"] else "%d erro(s)" % len(r["erros"]))
    sys.exit(1 if r["erros"] else 0)
