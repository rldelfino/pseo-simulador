"""Boas práticas oficiais de Google e Bing (13/nov/2026): lastmod real, sitemap enxuto e guias com fontes."""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lastmod

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "paginas_seo")
gerada = os.path.isdir(PASTA)


def test_registrar_mantem_a_data_se_o_conteudo_nao_mudou_e_avanca_se_mudou():
    m = {}
    d1 = lastmod.registrar(m, "k", "<p>a</p>", agora="2026-01-01T00:00:00+00:00")
    assert lastmod.registrar(m, "k", "<p>a</p>", agora="2026-02-02T00:00:00+00:00") == d1 == "2026-01-01T00:00:00+00:00"
    assert lastmod.registrar(m, "k", "<p>b</p>", agora="2026-03-03T00:00:00+00:00") == "2026-03-03T00:00:00+00:00"


def test_data_br():
    assert lastmod.data_br("2026-11-13T14:00:00+00:00") == "13/11/2026"


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_sitemap_tem_lastmod_iso_com_hora_e_sem_changefreq_priority():
    with open(os.path.join(PASTA, "sitemap.xml"), encoding="utf-8") as f:
        xml = f.read()
    assert "<changefreq>" not in xml and "<priority>" not in xml  # o Bing ignora; o Google também
    lms = re.findall(r"<lastmod>([^<]+)</lastmod>", xml)
    assert len(lms) == xml.count("<loc>") > 50
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00", x) for x in lms)
    assert len(set(lms)) > 1, "todas as URLs com a mesma data = lastmod falso"


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_manifesto_cobre_todas_as_urls_do_sitemap():
    m = lastmod.carregar()
    with open(os.path.join(PASTA, "sitemap.xml"), encoding="utf-8") as f:
        urls = re.findall(r"<loc>([^<]+)</loc>", f.read())
    faltando = [u for u in urls if "url:" + u not in m]
    assert not faltando, faltando[:5]


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_todo_guia_mostra_data_de_atualizacao_e_fontes_oficiais():
    guias = [n for n in os.listdir(PASTA) if n.startswith("aprenda-") and n.endswith(".html")]
    assert len(guias) >= 10
    for nome in guias:
        with open(os.path.join(PASTA, nome), encoding="utf-8") as f:
            h = f.read()
        assert re.search(r"Texto atualizado em \d{2}/\d{2}/\d{4}", h), nome
        externos = [u for u in re.findall(r'href="(https?://[^"]+)"', h)
                    if re.search(r"gov\.br|bcb\.gov|caixa\.gov|procon", u)]
        assert externos, f"{nome}: guia sem nenhuma fonte oficial"


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_fontes_dos_guias_sao_https_e_sem_duplicata():
    from gerador import FONTES_GUIAS
    for slug, fontes in FONTES_GUIAS.items():
        urls = [u for u, _ in fontes]
        assert len(urls) == len(set(urls)), slug
        assert all(u.startswith("https://") for u in urls), slug


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_guias_com_exemplo_calculado_trazem_numeros_do_simulador():
    for slug in ("aprenda-sac-x-price", "aprenda-ltv-financiamento-imobiliario",
                 "aprenda-amortizacao-extraordinaria", "aprenda-cet-iof-financiamento-imobiliario",
                 "aprenda-fgts-financiamento-imobiliario", "aprenda-financiamento-x-consorcio-imobiliario",
                 "aprenda-minha-casa-minha-vida-faixas-limites", "aprenda-passo-a-passo-financiar-imovel-documentos"):
        with open(os.path.join(PASTA, slug + ".html"), encoding="utf-8") as f:
            h = f.read()
        assert "Exemplo calculado" in h and len(re.findall(r"R\$ [\d.]+(?:,\d{2})?", h)) >= 2, slug


def test_amortizacao_extra_nao_sofre_erro_de_ponto_flutuante():
    import exemplos_guias
    # 300.000 em 360 meses, extra de 30.000 após 24 parcelas: 250.000 / 833,33 = exatamente 300 meses restantes
    _, meses, _ = exemplos_guias._sac_com_extra(300_000, 360, 11.5, 24, 30_000, "prazo")
    assert meses == 324


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_hubs_oferecem_link_para_copiar_e_compartilhar():
    hubs = [n for n in os.listdir(PASTA) if n.startswith("banco-") and n.endswith(".html")]
    assert len(hubs) >= 10
    for n in hubs:
        with open(os.path.join(PASTA, n), encoding="utf-8") as f:
            h = f.read()
        assert "Link para esta página" in h and "&lt;a href=" in h, n
        assert h.count('rel="noopener nofollow"') >= 4, n  # botões de compartilhar sem passar autoridade


def test_exemplos_dos_guias_restantes_batem_com_o_calculo():
    import gerador
    r = gerador.formatar_reais
    c = gerador.calcular_sac_price
    fgts = gerador.EXEMPLOS_GUIAS["aprenda-fgts-financiamento-imobiliario"]
    assert r(c(320_000, 360, 11.5)["p1_sac"]) in fgts and r(c(280_000, 360, 11.5)["p1_sac"]) in fgts
    cons = gerador.EXEMPLOS_GUIAS["aprenda-financiamento-x-consorcio-imobiliario"]
    assert r(c(300_000, 240, 11.5)["total_sac"] - 300_000) in cons
    import guias_novos
    guias = {g["slug"]: g["corpo_html"] for g in guias_novos.montar_guias(c, r)}
    mcmv = guias["aprenda-minha-casa-minha-vida-faixas-limites"]
    assert r(c(320_000, 360, 11.5, 400_000)["p1_sac"]) in mcmv and r(c(480_000, 360, 11.5, 600_000)["p1_sac"]) in mcmv
    passo = guias["aprenda-passo-a-passo-financiar-imovel-documentos"]
    for anos in (20, 30, 35):
        assert r(c(280_000, anos * 12, 11.5, 350_000)["p1_sac"]) in passo


def test_mcmv_nao_afirma_que_a_parcela_cabe_quando_a_renda_passa_do_limite():
    import gerador
    import guias_novos
    r = gerador.formatar_reais
    corpo = next(g["corpo_html"] for g in guias_novos.montar_guias(gerador.calcular_sac_price, r)
                 if g["slug"] == "aprenda-minha-casa-minha-vida-faixas-limites")
    renda3 = gerador.calcular_sac_price(320_000, 360, 11.5, 400_000)["renda_sugerida"]
    assert (renda3 > 9_600) == ("a parcela não caberia nessa regra" in corpo.split("Exemplo calculado")[1].split("Faixa 3:")[1].split("Faixa 4:")[0])


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_comparador_cita_o_mes_da_taxa_usa_virgula_e_nao_diz_mesma_condicao():
    with open(os.path.join(PASTA, "comparador-bancos.html"), encoding="utf-8") as f:
        bruto = f.read()
    h = re.sub(r"<[^>]+>", " ", bruto)
    assert re.search(r"Com as taxas do último mês fechado do Banco Central \([a-zç]+ de \d{4}\)", h)
    assert not re.search(r"Em \d{2}/\d{2}/\d{4}, entre os", h)
    assert not re.search(r"\d\.\d{2}% a\.a\.", bruto), "taxa com ponto decimal na tabela"
    assert "mesma condição" not in h and "entrada mínima de cada um" in h


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_comparador_e_comparacoes_sem_trofeu_numeracao_ou_destaque():
    nomes = ["comparador-bancos.html"] + sorted(n for n in os.listdir(PASTA)
                                                 if n.startswith("financiamento-imobiliario-") and n.endswith("-anos.html"))
    assert len(nomes) >= 10
    for nome in nomes:
        with open(os.path.join(PASTA, nome), encoding="utf-8") as f:
            h = f.read()
        assert "🏆" not in h, nome
        assert not re.search(r'font-bold text-xs">#\d+<', h), nome
        assert "bg-emerald-500/10 border-emerald-500/30" not in h, nome


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_hubs_trazem_analise_propria_com_numeros_do_calculo_e_sem_recomendar():
    import gerador
    bacen = gerador._taxas_bacen_atuais()
    media = sum(bacen.values()) / len(bacen)
    hubs = [n for n in os.listdir(PASTA) if n.startswith("banco-") and n.endswith(".html")]
    assert len(hubs) >= 10
    for n in hubs:
        with open(os.path.join(PASTA, n), encoding="utf-8") as f:
            h = re.sub(r"<[^>]+>", " ", f.read())
        assert "frente à média dos bancos" in h and "Exemplo calculado" in h, n
        bloco = h[h.index("frente à média dos bancos"):h.index("Antes de pedir a proposta")]
        assert f"{media:.2f}".replace(".", ",") + "% ao ano" in bloco, n
        assert not re.search(r"\b(melhor|pior|recomend[ao]|vencedor)\b", bloco.replace("Não é recomendação de banco", "")), n
    with open(os.path.join(PASTA, "dados-abertos.html"), encoding="utf-8") as f:
        assert '"keywords"' in f.read()


@pytest.mark.skipif(not gerada, reason="paginas_seo/ não gerada")
def test_dados_abertos_mostra_doi_hugging_face_e_markup_com_identifier():
    import gerador
    with open(os.path.join(PASTA, "dados-abertos.html"), encoding="utf-8") as f:
        h = f.read()
    assert f'href="{gerador.URL_ZENODO_DOI}"' in h and f'href="{gerador.URL_HUGGINGFACE}"' in h
    assert f'"identifier": "{gerador.URL_ZENODO_DOI}"' in h and gerador.URL_HUGGINGFACE in h
    with open(os.path.join(PASTA, "dados", "README.md"), encoding="utf-8") as f:
        assert gerador.URL_ZENODO_DOI in f.read()
