"""_redirects do Cloudflare Pages depois do enxugamento (20/11/2026): limites, destinos, sem cadeia nem loop e todas as páginas removidas cobertas."""
import os
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import conferir_redirects as cr  # noqa: E402


def test_regras_dentro_dos_limites_do_cloudflare_e_todas_301():
    regras = cr.ler_regras()
    din = [r for r in regras if cr._dinamica(r[0])]
    assert len(regras) - len(din) <= cr.LIMITE_ESTATICAS and len(din) <= cr.LIMITE_DINAMICAS
    assert all(r[2] == 301 for r in regras)


def test_curinga_casa_como_o_cloudflare():
    regras = [("/simulador-itau-*", "/banco-itau", 301), ("/x", "/y", 301)]
    assert cr.seguir("/simulador-itau-500-mil-360-meses", regras) == ("/banco-itau", 1, False)
    assert cr.seguir("/x", regras) == ("/y", 1, False)
    assert cr.seguir("/nada", regras) == ("/nada", 0, False)
    assert cr.seguir("/a", [("/a", "/b", 301), ("/b", "/a", 301)])[2] is True  # loop detectado


def test_sem_cadeia_sem_loop_e_destinos_existem():
    r = cr.conferir()
    assert not r["erros"], r["erros"][:5]


@pytest.mark.skipif(subprocess.run(["git", "cat-file", "-e", cr.REF_ANTES], cwd=RAIZ, capture_output=True).returncode != 0, reason="commit de referência fora do clone")
def test_toda_pagina_removida_tem_301_de_um_salto_para_pagina_existente():
    r = cr.conferir()
    assert r["removidas"] and r["removidas"] >= 1799
    assert r["cobertas"] == r["removidas"]
