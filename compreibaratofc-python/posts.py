# -*- coding: utf-8 -*-
"""Monta as imagens de post a partir do seu próprio acervo.

    python posts.py              as 30 peças mais procuradas
    python posts.py 60           as 60 mais procuradas
    python posts.py Flamengo     só as do Flamengo

Saída: a pasta posts/, com dois arquivos por peça —
    ..._feed.jpg     1080x1080, o post do Instagram e do Facebook
    ..._story.jpg    1080x1920, o story

Mais um posts/LEGENDAS.txt com a legenda de cada uma, pronta pra copiar.

POR QUE GERAR EM VEZ DE MONTAR NO CANVA
São 2.597 peças. Montar uma a uma à mão é o tipo de trabalho que começa
animado e para na terceira semana. Aqui você roda um comando e tem trinta
posts prontos, no mesmo enquadramento e na mesma tipografia — que é o que
faz um perfil parecer loja e não bagunça.

O QUE MUDAR
    CORES e MARGENS lá embaixo, se quiser mexer no visual.
    A foto vem de site/fotos/, a mesma que está no site.
"""
import io
import json
import os
import sys
import unicodedata

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts import cobica

AQUI   = os.path.dirname(os.path.abspath(__file__))
FOTOS  = os.path.join(AQUI, "site", "fotos")
FONTES = os.path.join(AQUI, "arte", "fontes")
SAIDA  = os.path.join(AQUI, "posts")
CATALOGO = os.path.join(AQUI, "site", "catalogo.json")

WHATSAPP = "(11) 5123-4079"
SITE     = "camisariaesportiva.com.br"
ARROBA   = "@camisariaesportivafc"

# ------------------------------------------------------------ as cores
# As mesmas da arte: pergaminho, nogueira e o dourado do escudo.
PERGAMINHO = (243, 236, 224)
PAPEL      = (250, 246, 239)
TINTA      = (31, 24, 17)
NOGUEIRA   = (42, 28, 18)
OURO       = (169, 127, 78)
OURO_CLARO = (201, 166, 117)
SUAVE      = (122, 109, 92)


def fonte(nome, tamanho):
    caminho = os.path.join(FONTES, nome)
    if not os.path.exists(caminho):
        raise SystemExit(
            f"Não achei a fonte {caminho}.\n"
            f"A pasta arte/fontes/ tem que ter os quatro .ttf que vieram no zip.")
    return ImageFont.truetype(caminho, tamanho)


def slug(txt):
    t = unicodedata.normalize("NFD", txt)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    # só a-z e 0-9: "º" e "ª" passam no isalnum() do Python e viram nome de
    # arquivo esquisito na hora de subir pro Instagram.
    t = "".join(c if ("a" <= c <= "z" or "0" <= c <= "9") else "-" for c in t)
    while "--" in t:
        t = t.replace("--", "-")
    return t.strip("-")


def quebrar(desenho, texto, f, largura):
    """Quebra o texto em linhas que cabem na largura. O PIL não faz isso
    sozinho, e nome de time é imprevisível: 'Ajax' e 'Borussia
    Mönchengladbach' na mesma tipografia."""
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if desenho.textlength(teste, font=f) <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def centrado(d, texto, f, y, cor, largura_tela, espaco=0):
    if espaco:
        w = sum(d.textlength(c, font=f) + espaco for c in texto) - espaco
        x = (largura_tela - w) / 2
        for c in texto:
            d.text((x, y), c, font=f, fill=cor)
            x += d.textlength(c, font=f) + espaco
    else:
        w = d.textlength(texto, font=f)
        d.text(((largura_tela - w) / 2, y), texto, font=f, fill=cor)


def rotulo_curto(p):
    """'Retrô 1986', 'Retrô 95-97 · Zidane', '1º Uniforme 26/27'."""
    partes = p["chave"].split(" - ")[2:]
    return " · ".join(partes) if partes else ""


# =====================================================================
# DE ONDE VEM A FOTO
# =====================================================================
# A foto do SITE tem 320 a 480 pixels — ela foi comprimida pra 35 KB de
# propósito, pra o site abrir rápido. Ampliar isso pra um post de 1080
# fica borrado.
#
# A ORIGINAL do fornecedor tem 1024 e está em fotos_originais/. O caminho
# dela está no site/.cache-fotos.json, que o build escreve: ele guarda,
# pra cada foto do site, de qual arquivo ela veio. Só que guarda sem o
# nome da leva ("retro/", "selecoes/"...), então a gente monta um índice
# uma vez e depois é consulta direta.
_INDICE = None


def _indice_originais():
    global _INDICE
    if _INDICE is not None:
        return _INDICE
    _INDICE = {}
    cache = os.path.join(AQUI, "site", ".cache-fotos.json")
    if not os.path.exists(cache):
        return _INDICE
    origens = {k: v.get("origem") for k, v in
               json.load(io.open(cache, encoding="utf-8")).items()}
    originais = os.path.join(AQUI, "fotos_originais")
    if not os.path.isdir(originais):
        return _INDICE
    # onde cada "pasta-da-peça/01.webp" está de verdade
    onde = {}
    for leva in os.listdir(originais):
        caminho_leva = os.path.join(originais, leva)
        if not os.path.isdir(caminho_leva):
            continue
        for pasta in os.listdir(caminho_leva):
            onde[pasta] = os.path.join(caminho_leva, pasta)
    for web, origem in origens.items():
        if not origem or "/" not in origem:
            continue
        pasta, arquivo = origem.split("/", 1)
        base = onde.get(pasta)
        if base:
            _INDICE[web] = os.path.join(base, arquivo)
    return _INDICE


def abrir_foto(p):
    """A original quando existir; a do site como plano B."""
    nome = p["fotos"][0].split("/")[-1]
    caminho = _indice_originais().get(nome)
    if caminho and os.path.exists(caminho):
        return Image.open(caminho).convert("RGB")
    caminho = os.path.join(FOTOS, nome)
    if os.path.exists(caminho):
        return Image.open(caminho).convert("RGB")
    return None


def moldura(tela, caixa, cor=OURO, grossura=3):
    """A linha dourada em volta da foto — é o que amarra o post à marca."""
    d = ImageDraw.Draw(tela)
    d.rectangle(caixa, outline=cor, width=grossura)


# =====================================================================
def feed(p, foto):
    L = 1080
    tela = Image.new("RGB", (L, L), PAPEL)
    d = ImageDraw.Draw(tela)

    # faixa de pergaminho atrás da foto
    d.rectangle([0, 0, L, 762], fill=PERGAMINHO)

    f = foto.copy()
    f.thumbnail((690, 690), Image.LANCZOS)
    tela.paste(f, ((L - f.width) // 2, 36 + (690 - f.height) // 2))
    moldura(tela, [(L - 726) // 2, 22, (L + 726) // 2, 740], OURO, 3)

    f_time  = fonte("PlayfairDisplay-SemiBold.ttf", 60)
    f_desc  = fonte("Inter-Regular.ttf", 27)
    f_preco = fonte("PlayfairDisplay-SemiBold.ttf", 50)
    f_pe    = fonte("Inter-SemiBold.ttf", 21)

    y = 792
    for linha in quebrar(d, p["time"], f_time, 940)[:2]:
        centrado(d, linha, f_time, y, TINTA, L)
        y += 66

    for linha in quebrar(d, rotulo_curto(p), f_desc, 900)[:1]:
        centrado(d, linha, f_desc, y + 4, SUAVE, L)
        y += 36

    d.line([(L / 2 - 55, y + 20), (L / 2 + 55, y + 20)], fill=OURO, width=2)
    centrado(d, f"R$ {p['preco']}", f_preco, y + 38, TINTA, L)

    d.rectangle([0, L - 64, L, L], fill=NOGUEIRA)
    centrado(d, f"{ARROBA}   ·   {SITE}", f_pe, L - 44, OURO_CLARO, L, espaco=1)
    return tela


def story(p, foto):
    L, A = 1080, 1920
    tela = Image.new("RGB", (L, A), NOGUEIRA)
    d = ImageDraw.Draw(tela)

    # o quadro de pergaminho no meio, como na arte da marca
    d.rectangle([56, 290, L - 56, 1330], fill=PERGAMINHO)
    moldura(tela, [56, 290, L - 56, 1330], OURO, 4)

    f = foto.copy()
    f.thumbnail((880, 880), Image.LANCZOS)
    tela.paste(f, ((L - f.width) // 2, 330 + (880 - f.height) // 2))

    f_selo  = fonte("Inter-SemiBold.ttf", 24)
    f_time  = fonte("PlayfairDisplay-SemiBold.ttf", 74)
    f_desc  = fonte("Inter-Regular.ttf", 31)
    f_preco = fonte("PlayfairDisplay-SemiBold.ttf", 62)
    f_cta   = fonte("Inter-SemiBold.ttf", 29)
    f_pe    = fonte("Inter-SemiBold.ttf", 23)

    centrado(d, "CAMISARIA ESPORTIVA FC", f_selo, 190, OURO_CLARO, L, espaco=5)

    for linha in quebrar(d, p["time"], f_time, 880)[:1]:
        centrado(d, linha, f_time, 1382, (236, 224, 205), L)
    centrado(d, rotulo_curto(p)[:46], f_desc, 1474, OURO_CLARO, L)

    d.line([(L / 2 - 70, 1540), (L / 2 + 70, 1540)], fill=OURO, width=2)
    centrado(d, f"R$ {p['preco']}", f_preco, 1580, (250, 246, 239), L)
    centrado(d, "PEDIDO PELO WHATSAPP", f_cta, 1680, OURO_CLARO, L, espaco=3)
    centrado(d, WHATSAPP, f_cta, 1726, (236, 224, 205), L)

    centrado(d, f"{ARROBA}   ·   {SITE}", f_pe, 1790, OURO, L, espaco=1)
    return tela


# =====================================================================
def legenda(p):
    """A legenda que vai junto. Não inventa história: fala do que a peça é,
    do preço e de como pedir. Quando você quiser contar a história da
    camisa, o texto vai no vídeo — é lá que ele funciona."""
    rot = rotulo_curto(p)
    return (
        f"{p['time']} — {rot}\n"
        f"R$ {p['preco']} · versão {p.get('versao') or 'torcedor'}\n\n"
        f"Peça fotografada aqui, uma a uma. O que está no site é o que existe.\n"
        f"Envio para todo o Brasil, pedido direto no WhatsApp {WHATSAPP}.\n\n"
        f"Acervo completo em {SITE}\n\n"
        f"#{slug(p['time']).replace('-','')} #camisaderetro #camisadetime "
        f"#futebolretro #camisadefutebol #colecionador #{slug(p['liga'].split('·')[0]).replace('-','')}"
    )


def main():
    if not os.path.exists(CATALOGO):
        sys.exit("Não achei site/catalogo.json. Rode antes:  python build.py tudo")

    pecas = [p for p in json.load(io.open(CATALOGO, encoding="utf-8"))
             if p.get("preco")]

    arg = sys.argv[1] if len(sys.argv) > 1 else "30"
    if arg.isdigit():
        quantas, filtro_time = int(arg), None
    else:
        quantas, filtro_time = 999, arg

    if filtro_time:
        pecas = [p for p in pecas if filtro_time.lower() in p["time"].lower()]
        if not pecas:
            sys.exit(f"Nenhuma peça de '{filtro_time}'. Confira o nome do time.")

    pecas.sort(key=lambda p: -cobica.pontos(p))

    # uma peça por time até completar: trinta posts do Real Madrid não é
    # conteúdo, é insistência
    vistos, escolhidas = set(), []
    for p in pecas:
        if not filtro_time and p["time"] in vistos:
            continue
        vistos.add(p["time"])
        escolhidas.append(p)
        if len(escolhidas) >= quantas:
            break

    os.makedirs(SAIDA, exist_ok=True)
    legendas, feitos, sem_foto = [], 0, []

    for i, p in enumerate(escolhidas, 1):
        foto = abrir_foto(p)
        if foto is None:
            sem_foto.append(p["chave"])
            continue
        base = f"{i:02d}-{slug(p['time'])}-{slug(rotulo_curto(p))[:30]}"
        feed(p, foto).save(os.path.join(SAIDA, base + "_feed.jpg"),
                           "JPEG", quality=92, optimize=True)
        story(p, foto).save(os.path.join(SAIDA, base + "_story.jpg"),
                            "JPEG", quality=92, optimize=True)
        legendas.append(f"{'='*66}\n{base}\n{'='*66}\n\n{legenda(p)}\n")
        feitos += 1

    io.open(os.path.join(SAIDA, "LEGENDAS.txt"), "w", encoding="utf-8").write(
        "LEGENDAS DOS POSTS\n"
        "Copie a legenda do arquivo com o mesmo nome da imagem.\n\n"
        + "\n".join(legendas))

    print(f"\n{feitos} posts em posts/  ({feitos * 2} imagens)")
    if sem_foto:
        print(f"\n{len(sem_foto)} sem foto em site/fotos (puladas):")
        for c in sem_foto[:5]:
            print(f"   {c}")
    print("\nAs legendas estão em posts/LEGENDAS.txt")


if __name__ == "__main__":
    main()
