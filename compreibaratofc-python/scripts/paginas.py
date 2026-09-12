# -*- coding: utf-8 -*-
"""Gera as páginas que o Google lê: uma por time, uma por coleção, e o mapa.

Chamado pelo publicar.py. Não roda sozinho.

POR QUE ISSO EXISTE
O catálogo é uma página só que monta tudo com JavaScript. Isso é ótimo pra
quem já está no site e péssimo pra ser achado: o Google entende JavaScript,
mas continua ranqueando muito melhor uma página que já vem pronta, com um
título só dela, um texto só dela e as fotos no HTML.

Quem procura no Google não digita "catálogo de camisas". Digita "camisa
retrô do Parma", "camisa da Fiorentina 98". São 332 buscas diferentes, e
cada uma merece uma página. Escrever 332 à mão é impossível; gerar é uma
tarde de código que não se repete.

O QUE ELE GERA
    camisa-<time>.html      332 páginas, uma por time, com as peças reais
    <coleção>.html            9 páginas de coleção (retrô, kids, copa...)
    times.html                o índice — é por ele que o Google chega nas 332
    sitemap.xml               a lista de tudo, pro Search Console
"""
import html
import os
import re
import unicodedata
from datetime import date
from urllib.parse import quote

from scripts import cobica

# =====================================================================
# O ARTIGO ANTES DO NOME
# =====================================================================
# "Camisa do Palmeiras", "Camisa da Juventus", "Camisa de Portugal".
# Não tem regra: é decoreba. Errar isso num título é o tipo de coisa que
# faz o site parecer feito por robô — então vai escrito, não adivinhado.
#
# O padrão é "do". Só o que foge está listado.
ARTIGO_DA = {
    # seleções femininas
    "Albânia", "Alemanha", "Argentina", "Argélia", "Arábia Saudita", "Austrália",
    "Bolívia", "Bulgária", "Bélgica", "Bósnia e Herzegovina", "Chéquia",
    "Colômbia", "Coreia do Sul", "Costa Rica", "Costa do Marfim", "Croácia",
    "Dinamarca", "Escócia", "Eslovênia", "Espanha", "Finlândia", "França",
    "Grécia", "Guatemala", "Guiné Equatorial", "Holanda", "Hungria",
    "Indonésia", "Inglaterra", "Irlanda", "Irlanda do Norte", "Islândia",
    "Itália", "Iugoslávia", "Jamaica", "Jordânia", "Malásia", "Nigéria",
    "Noruega", "Nova Zelândia", "Polônia", "RD Congo", "Romênia", "Suécia",
    "Suíça", "Tchecoslováquia", "Tunísia", "Turquia", "Ucrânia",
    "União Soviética", "Venezuela", "África do Sul", "Áustria",
    # clubes femininos (quase todos italianos)
    "AS Roma", "Atalanta", "Chapecoense", "Cremonese", "Fiorentina",
    "Juventus", "Lazio", "Udinese", "Inter de Milão", "Estrela Vermelha",
    "Real Sociedad", "Universidad Católica", "Universidad de Chile",
    "Sampdoria", "Portuguesa", "Ponte Preta", "Ferroviária",
}
ARTIGO_DE = {"Cabo Verde", "Camarões", "Curaçao", "El Salvador", "Gana",
             "Honduras", "Israel", "Portugal"}
ARTIGO_DOS = {"Estados Unidos", "Emirados Árabes Unidos"}
ARTIGO_DAS = {"Filipinas"}


def de(time):
    if time in ARTIGO_DA:  return "da " + time
    if time in ARTIGO_DE:  return "de " + time
    if time in ARTIGO_DOS: return "dos " + time
    if time in ARTIGO_DAS: return "das " + time
    return "do " + time


def slug(txt):
    t = unicodedata.normalize("NFD", txt)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def esc(s):
    return html.escape(str(s), quote=True)


# =====================================================================
# MOLDE
# =====================================================================
MOLDE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light only">
<meta name="theme-color" content="#151310">
<title>{titulo}</title>
<meta name="description" content="{descricao}">
<link rel="canonical" href="{dominio}/{arquivo}">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="favicon-16.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Camisaria Esportiva FC">
<meta property="og:locale" content="pt_BR">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descricao}">
<meta property="og:url" content="{dominio}/{arquivo}">
<meta property="og:image" content="{og_imagem}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,600&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="pagina.css">
<script type="application/ld+json">{jsonld}</script>
</head>
<body>
<div id="topo"></div>
<header class="capa">
  <div class="limite">
    <nav class="trilha">{trilha}</nav>
    <h1>{h1}</h1>
    <p>{chamada}</p>
    <div class="precos">
{precos}
    </div>
  </div>
</header>
<div class="limite"><main>
{corpo}
</main></div>
<footer>
  <a href="index.html">Início</a> · <a href="catalogo.html">Acervo completo</a> ·
  <a href="times.html">Todos os times</a> · <a href="camisas-retro.html">Retrô</a> ·
  <a href="kit-infantil.html">Kit Infantil</a><br>
  <a href="https://www.instagram.com/camisariaesportivafc/" target="_blank" rel="noopener">Instagram</a> ·
  <a href="https://www.facebook.com/camisariaesportivafc" target="_blank" rel="noopener">Facebook</a><br><br>
  Camisaria Esportiva FC · camisariaesportiva.com.br<br>
  Imagens ilustrativas. Marcas e escudos pertencem aos seus titulares.
</footer>
<script src="dados.js"></script>
<script src="nav.js"></script>
<script>montarTopo('landing');</script>
</body>
</html>
"""

NOME_GENERO = {"masculino": "Masculino", "feminino": "Feminino", "infantil": "Infantil"}


def rotulo_peca(p):
    from publicar import rotulo
    return rotulo(p)


def descricao_peca(p, rot):
    t = p.get("temporada")
    t = t.replace("-", "/") if t and t != "retro" else ""
    return " · ".join(x for x in (rot, t, NOME_GENERO.get(p["genero"], "")) if x)


def foto_de(p):
    return p["fotos"][0] if p["fotos"] else ""


def zap(whats, p, rot):
    from urllib.parse import quote
    texto = (f"Olá! Tenho interesse nesta peça da Camisaria Esportiva FC:\n\n"
             f"{p['time']} — {descricao_peca(p, rot)}\nR$ {p['preco']}\n\n"
             f"Pode me passar os tamanhos disponíveis?")
    return f"https://wa.me/{whats}?text={quote(texto)}"


def cartao(p, whats):
    rot = rotulo_peca(p)
    d = descricao_peca(p, rot)
    return f'''<a class="item" href="{esc(zap(whats, p, rot))}" target="_blank" rel="noopener">
      <div class="f"><img src="{esc(foto_de(p))}" alt="{esc(p['time'] + ' ' + d)}"
           loading="lazy" width="400" height="400"></div>
      <div class="c"><span class="l">{esc(p['liga'])}</span><span class="n">{esc(p['time'])}</span>
      <span class="m">{esc(d)}</span>
      <span class="p">R$ {p['preco']}</span>
      <span class="z">Consultar no WhatsApp</span></div></a>'''


def grade(pecas, whats):
    return '<div class="grade">' + "\n".join(cartao(p, whats) for p in pecas) + "</div>"


def faixa_precos(pecas):
    """A faixa de preço da própria página. Numa página de calção não faz
    sentido anunciar 'Torcedor R$219' — o que ela vende é calção."""
    por = {}
    for p in pecas:
        rot = rotulo_peca(p)
        if p["categoria"] == "kit":
            k = "Kit infantil" if p["genero"] == "infantil" else "Conjunto"
        elif p["categoria"] != "camisa":
            k = {"calcao": "Calção", "jaqueta": "Jaqueta", "regata": "Regata",
                 "polo": "Polo", "cropped": "Cropped"}.get(p["categoria"], "Peça")
        elif p["uniforme"] == "retro":
            k = "Retrô"
        elif p["versao"] == "jogador":
            k = "Jogador"
        else:
            k = "Torcedor"
        por.setdefault(k, []).append(p["preco"])
    ordem = ["Torcedor", "Jogador", "Retrô", "Kit infantil", "Conjunto",
             "Jaqueta", "Calção", "Regata", "Polo", "Cropped"]
    linhas = []
    for k in ordem:
        if k in por and len(linhas) < 3:
            v = min(por[k])
            linhas.append(f'      <div><span class="q">{k}</span>'
                          f'<span class="v">R${v}</span></div>')
    return "\n".join(linhas)


# =====================================================================
# A SUA POLÍTICA — o que o Google mostra ao lado do preço
# =====================================================================
# ISTO VIRA COMPROMISSO PÚBLICO. O Google exibe essas informações na
# busca, e cliente cobra. Só está escrito aqui o que você confirmou.
#
# TROCA — você disse: troco, cliente paga o frete de devolução.
TROCA_DIAS = 7                 # prazo pra pedir a troca
TROCA_QUEM_PAGA = "cliente"    # "cliente", "loja", ou None pra não declarar

# FRETE — você disse: grátis acima de um valor. Faltam os dois números.
# Enquanto estiverem em None, o site NÃO declara frete nenhum, e o Search
# Console segue avisando que falta. Isso é melhor que declarar errado:
# valor de frete errado na busca é reclamação na certa.
#
# Quando souber, troque:
#     FRETE_GRATIS_ACIMA = 399     grátis a partir de R$ 399
#     FRETE_ABAIXO_DISSO = 30      quanto custa abaixo desse valor
FRETE_GRATIS_ACIMA = None
FRETE_ABAIXO_DISSO = None
FRETE_PREPARO_DIAS = (1, 3)    # quantos dias úteis você leva pra postar
FRETE_ENTREGA_DIAS = (5, 12)   # quantos dias úteis os Correios levam


def politica_de_troca():
    """O bloco que o Google chama de hasMerchantReturnPolicy."""
    if not TROCA_QUEM_PAGA:
        return None
    return {
        "@type": "MerchantReturnPolicy",
        "applicableCountry": "BR",
        "returnPolicyCategory":
            "https://schema.org/MerchantReturnFiniteReturnWindow",
        "merchantReturnDays": TROCA_DIAS,
        "returnMethod": "https://schema.org/ReturnByMail",
        "returnFees": ("https://schema.org/ReturnShippingFees"
                       if TROCA_QUEM_PAGA == "cliente"
                       else "https://schema.org/FreeReturn"),
    }


def politica_de_frete(preco):
    """O bloco shippingDetails.

    Como cada peça tem o preço dela, dá pra dizer a verdade peça a peça:
    a que passa do limite sai com frete zero, a que não passa sai com o
    valor. Sem faixa e sem "a partir de" — cada anúncio diz o que vale
    pra ele."""
    if FRETE_GRATIS_ACIMA is None or FRETE_ABAIXO_DISSO is None:
        return None
    gratis = float(preco) >= float(FRETE_GRATIS_ACIMA)
    valor = 0 if gratis else FRETE_ABAIXO_DISSO
    return {
        "@type": "OfferShippingDetails",
        "shippingRate": {"@type": "MonetaryAmount",
                         "value": f"{valor}.00", "currency": "BRL"},
        "shippingDestination": {"@type": "DefinedRegion",
                                "addressCountry": "BR"},
        "deliveryTime": {
            "@type": "ShippingDeliveryTime",
            "handlingTime": {"@type": "QuantitativeValue",
                             "minValue": FRETE_PREPARO_DIAS[0],
                             "maxValue": FRETE_PREPARO_DIAS[1],
                             "unitCode": "DAY"},
            "transitTime": {"@type": "QuantitativeValue",
                            "minValue": FRETE_ENTREGA_DIAS[0],
                            "maxValue": FRETE_ENTREGA_DIAS[1],
                            "unitCode": "DAY"}},
    }


def oferta(p, endereco):
    o = {"@type": "Offer", "price": f"{p['preco']}.00",
         "priceCurrency": "BRL",
         "url": endereco,
         "availability": "https://schema.org/InStock",
         "seller": {"@type": "Organization",
                    "name": "Camisaria Esportiva FC"}}
    troca = politica_de_troca()
    if troca:
        o["hasMerchantReturnPolicy"] = troca
    frete = politica_de_frete(p["preco"])
    if frete:
        o["shippingDetails"] = frete
    return o


def descricao_longa(p, rot):
    """A frase que o Google mostra embaixo do produto. Sai dos campos da
    peça — nada inventado."""
    partes = [p["time"]]
    if rot:
        partes.append(rot)
    t = p.get("temporada")
    if t and t != "retro":
        partes.append("temporada " + t.replace("-", "/"))
    if p.get("ano_retro"):
        partes.append("retrô " + str(p["ano_retro"]))
    if p.get("liga"):
        partes.append(p["liga"])
    corte = {"masculino": "modelagem masculina",
             "feminino": "modelagem feminina",
             "infantil": "tamanho infantil"}.get(p["genero"])
    if corte:
        partes.append(corte)
    frase = ", ".join(partes)
    return (frase + ". Peça de acervo da Camisaria Esportiva FC, fotografada "
            "uma a uma. Pedido pelo WhatsApp, envio para todo o Brasil.")


def jsonld_lista(nome, pecas, dominio, limite=24):
    """Os dados que o Google lê de cada peça.

    O QUE NÃO ESTÁ AQUI, E É DE PROPÓSITO
    O Search Console reclama que faltam "review" e "aggregateRating" — as
    estrelinhas de avaliação. Elas não estão aqui porque o acervo ainda
    não teve nenhuma avaliação. Escrever nota de cliente que não existe é
    exatamente o que o Google pune, e é mentira. O aviso fica lá até
    existirem avaliações de verdade; ele é "não crítico" e não tira o
    site da busca."""
    import json
    itens = []
    for i, p in enumerate(pecas[:limite], 1):
        rot = rotulo_peca(p)
        endereco = (f"{dominio}/catalogo.html?time="
                    + quote(p["time"]))
        itens.append({
            "@type": "ListItem", "position": i,
            "item": {"@type": "Product",
                     "name": f"{p['time']} — {descricao_peca(p, rot)}",
                     "description": descricao_longa(p, rot),
                     "image": f"{dominio}/{foto_de(p)}",
                     "url": endereco,
                     "sku": slug(p["chave"])[:80],
                     "itemCondition": "https://schema.org/NewCondition",
                     "brand": {"@type": "Brand", "name": "Camisaria Esportiva FC"},
                     "offers": oferta(p, endereco)}})
    return json.dumps({"@context": "https://schema.org", "@type": "ItemList",
                       "name": nome, "numberOfItems": len(pecas),
                       "itemListElement": itens}, ensure_ascii=False)


# =====================================================================
# PÁGINA DE TIME
# =====================================================================
def pagina_time(time, pecas, todas, dominio, whats):
    arquivo = f"camisa-{slug(time)}.html"
    selecao = pecas[0]["raiz"] == "selecoes"
    liga = pecas[0]["liga"]
    nome_de = de(time)

    atuais = [p for p in pecas if p.get("temporada") not in (None, "retro")]
    retros = [p for p in pecas if p.get("uniforme") == "retro"]
    kids   = [p for p in pecas if p["genero"] == "infantil"]
    # "a partir de" tem que ser o preço da CAMISA. Dizer "a partir de R$99"
    # numa página de camisas, quando o R$99 é o calção, é meia verdade.
    camisas = [p for p in pecas if p["categoria"] == "camisa"] or pecas
    menor  = min(p["preco"] for p in camisas)

    # a ordem em que as peças aparecem: atual primeiro, retrô depois
    def ano(p):
        t = p.get("temporada") or ""
        m = re.fullmatch(r"(\d{2})-(\d{2})", t)
        if m:
            a = int(m.group(1)); return 1900 + a if a >= 60 else 2000 + a
        return int(t) if t.isdigit() else 0
    ordenadas = sorted(pecas, key=lambda p: (-ano(p), rotulo_peca(p)))

    partes = []
    if atuais: partes.append(f"{len(atuais)} da temporada atual")
    if retros: partes.append(f"{len(retros)} retrô")
    if kids:   partes.append(f"{len(kids)} infantil")
    resumo = ", ".join(partes[:-1]) + (" e " + partes[-1] if len(partes) > 1 else
                                       (partes[0] if partes else ""))

    chamada = (f"{len(pecas)} peça{'s' if len(pecas) > 1 else ''} {nome_de} no acervo"
               + (f" — {resumo}" if resumo else "")
               + f". A partir de R${menor}, com envio para todo o Brasil e "
                 f"pedido direto no WhatsApp.")

    titulo = (f"Camisa {nome_de} — "
              + ("Retrô, " if retros else "")
              + "Torcedor e Jogador | Camisaria Esportiva FC")
    descricao = (f"Camisa {nome_de} no acervo da Camisaria Esportiva FC: "
                 + (f"{len(retros)} edições retrô, " if retros else "")
                 + f"{len(pecas)} peças fotografadas uma a uma. "
                   f"A partir de R${menor}. Pedido pelo WhatsApp.")

    # times da mesma liga, pro Google (e o visitante) andarem pelo site
    vizinhos = sorted({p["time"] for p in todas
                       if p["liga"] == liga and p["time"] != time})[:12]
    lista_vizinhos = " · ".join(
        f'<a href="camisa-{slug(t)}.html">{esc(t)}</a>' for t in vizinhos)

    corpo = [f"<h2>Camisa {esc(nome_de)} disponível agora</h2>",
             f"<p>Estas são as peças {esc(nome_de)} que estão fotografadas e prontas "
             f"para pedido. Clique na peça e o WhatsApp abre com o modelo já escrito "
             f"na mensagem — você só confirma o tamanho.</p>",
             grade(ordenadas, whats)]

    if retros:
        anos = sorted({rotulo_peca(p).split(" · ")[0].replace("Retrô ", "")
                       for p in retros if rotulo_peca(p).startswith("Retrô")})
        if anos:
            corpo.append(f"<h2>Camisa retrô {esc(nome_de)}</h2>")
            corpo.append(f"<p>São {len(retros)} edições retrô {esc(nome_de)} no acervo, "
                         f"das temporadas {esc(', '.join(anos[:10]))}"
                         f"{' e outras' if len(anos) > 10 else ''}. "
                         f"Retrô é a peça que some do fornecedor e não volta: quando "
                         f"acaba, acabou.</p>")

    corpo.append(f"<h2>Quanto custa a camisa {esc(nome_de)}</h2>")
    faixas = {}
    for p in pecas:
        faixas.setdefault(p["preco"], 0)
        faixas[p["preco"]] += 1
    linhas = ", ".join(f"<strong>R${v}</strong> ({n} peça{'s' if n > 1 else ''})"
                       for v, n in sorted(faixas.items()))
    corpo.append(f"<p>{linhas}. Preço fechado por peça: aqui o que define o valor "
                 f"é a peça, não o tamanho do pedido.</p>")

    corpo.append("<h2>Versão jogador ou versão torcedor?</h2>")
    corpo.append("<p>A <strong>versão torcedor</strong> tem modelagem mais solta e "
                 "tecido mais encorpado — é a mais pedida para o dia a dia. A "
                 "<strong>versão jogador</strong> é mais justa e mais leve, igual à "
                 "que o atleta usa em campo.</p>")

    if vizinhos:
        corpo.append(f"<h2>Outros times {esc('da ' + liga if not selecao else 'do mesmo grupo')}</h2>")
        corpo.append(f'<p class="atalhos-linha">{lista_vizinhos}</p>')

    corpo.append('<div class="cta"><h2>Não achou o uniforme que queria?</h2>'
                 f'<p>Nem tudo que passa por aqui chega a entrar no site. Diga o ano '
                 f'e o uniforme {esc(nome_de)} que você procura — se existir, eu acho.</p>'
                 f'<a class="btn" href="https://wa.me/{whats}?text='
                 + __import__("urllib.parse", fromlist=["quote"]).quote(
                     f"Olá! Estou procurando uma camisa {nome_de}. Pode me ajudar?")
                 + '" target="_blank" rel="noopener">Falar no WhatsApp</a></div>')

    trilha = ('<a href="index.html">Início</a> › '
              + ('<a href="camisas-selecoes.html">Seleções</a>' if selecao
                 else '<a href="camisas-clubes.html">Clubes</a>')
              + f" › {esc(time)}")

    return arquivo, MOLDE.format(
        titulo=esc(titulo), descricao=esc(descricao), dominio=dominio,
        arquivo=arquivo, og_imagem=f"{dominio}/{foto_de(ordenadas[0])}",
        jsonld=jsonld_lista(f"Camisas {nome_de}", ordenadas, dominio),
        trilha=trilha, h1=f"Camisas {esc(nome_de)}", chamada=esc(chamada),
        precos=faixa_precos(pecas), corpo="\n".join(corpo))


# =====================================================================
# PÁGINAS DE COLEÇÃO
# =====================================================================
COLECOES = [
    ("camisas-selecoes.html", "Camisas de Seleções", "Seleções",
     lambda p: p["raiz"] == "selecoes",
     "Camisas de seleções nacionais: Copa de 2026, uniformes atuais e as retrô "
     "que marcaram as Copas anteriores."),
    ("camisas-clubes.html", "Camisas de Clubes", "Clubes",
     lambda p: p["raiz"] != "selecoes",
     "Camisas de clubes da Europa, do Brasil e da América do Sul — dos gigantes "
     "aos times que quase ninguém tem."),
    ("camisas-retro.html", "Camisas Retrô", "Retrô",
     lambda p: p.get("uniforme") == "retro",
     "Uniformes clássicos de várias épocas: Copas, finais, camisas com nome de "
     "jogador. Retrô é o que some do fornecedor e não volta."),
    ("kit-infantil.html", "Kit Infantil de Time", "Kit Infantil",
     lambda p: p["genero"] == "infantil",
     "Kit infantil com camisa e calção do mesmo uniforme, de clubes e seleções."),
    ("calcoes-de-time.html", "Calções de Time", "Calções",
     lambda p: p["categoria"] in ("calcao", "calca"),
     "Calção do mesmo uniforme da camisa, para fechar o conjunto."),
    ("jaquetas-de-time.html", "Jaquetas e Agasalhos de Time", "Jaquetas",
     lambda p: p["categoria"] == "jaqueta",
     "Jaquetas, corta-ventos e agasalhos de treino de clubes e seleções."),
    ("edicoes-especiais.html", "Edições Especiais", "Edições especiais",
     lambda p: "edicoes" in p.get("colecoes", []),
     "Colaborações, aniversários, camisas comemorativas e edições limitadas — "
     "o que sai de linha primeiro."),
    ("copa-2026.html", "Camisas da Copa 2026", "Copa 2026",
     lambda p: "copa-2026" in p.get("colecoes", []),
     "As camisas das seleções para a Copa do Mundo de 2026, versão jogador e "
     "torcedor, mais o kit infantil."),
    ("camisas-femininas.html", "Camisas Femininas", "Femininas",
     lambda p: p["genero"] == "feminino",
     "Modelagem feminina de clubes e seleções, versão torcedor."),
]


def intercalar(pecas):
    """Espalha os times. Ordenar pela procura junta seis Argentina seguidas
    e depois seis Brasil; assim sai a melhor de cada time, depois a segunda
    de cada, e por aí. A primeira tela mostra doze times diferentes."""
    filas = {}
    for p in pecas:
        filas.setdefault(p["time"], []).append(p)
    ordem = list(filas.values())
    fora, i = [], 0
    while len(fora) < len(pecas):
        for fila in ordem:
            if i < len(fila):
                fora.append(fila[i])
        i += 1
    return fora


def pagina_colecao(arquivo, nome, curto, filtro, texto, todas, dominio, whats,
                   mostrar=48):
    pecas = [p for p in todas if filtro(p)]
    if not pecas:
        return None
    menor = min(p["preco"] for p in pecas)
    times = sorted({p["time"] for p in pecas})

    # A ordem é a da PROCURA, não a alfabética. Numa página de retrô, ordem
    # alfabética abre em Aberdeen e AEK Atenas — peças legítimas que ninguém
    # foi ali procurar. Ver scripts/cobica.py.
    ordenadas = intercalar(sorted(pecas, key=lambda p: -cobica.pontos(p)))

    chamada = (f"{len(pecas)} peças de {len(times)} times no acervo, a partir de "
               f"R${menor}. {texto}")
    corpo = [f"<h2>{esc(nome)} no acervo</h2>",
             f"<p>{esc(texto)} Abaixo estão "
             + (f"as {mostrar} mais recentes" if len(pecas) > mostrar
                else f"as {len(pecas)}")
             + f" — o acervo tem {len(pecas)}. Clique na peça e o WhatsApp abre "
               f"com o modelo já escrito.</p>",
             grade(ordenadas[:mostrar], whats)]
    if len(pecas) > mostrar:
        corpo.append(f'<p><a href="catalogo.html?busca=">Ver as {len(pecas)} '
                     f'no acervo completo →</a></p>')

    corpo.append(f"<h2>Times com {esc(curto.lower())} no acervo</h2>")
    corpo.append('<p class="atalhos-linha">' + " · ".join(
        f'<a href="camisa-{slug(t)}.html">{esc(t)}</a>' for t in times[:60]) +
        (f' · <a href="times.html">e mais {len(times)-60}</a>' if len(times) > 60 else '')
        + "</p>")

    titulo = f"{nome} — {len(pecas)} peças | Camisaria Esportiva FC"
    descricao = f"{texto} {len(pecas)} peças de {len(times)} times, a partir de R${menor}. Pedido pelo WhatsApp."
    return arquivo, MOLDE.format(
        titulo=esc(titulo), descricao=esc(descricao), dominio=dominio,
        arquivo=arquivo, og_imagem=f"{dominio}/{foto_de(ordenadas[0])}",
        jsonld=jsonld_lista(nome, ordenadas, dominio),
        trilha=f'<a href="index.html">Início</a> › {esc(curto)}',
        h1=esc(nome), chamada=esc(chamada),
        precos=faixa_precos(pecas), corpo="\n".join(corpo))


# =====================================================================
# ÍNDICE DE TIMES
# =====================================================================
def pagina_times(todas, dominio):
    por_time = {}
    for p in todas:
        por_time.setdefault(p["time"], []).append(p)
    selecoes = sorted(t for t, ps in por_time.items() if ps[0]["raiz"] == "selecoes")
    clubes   = sorted(t for t, ps in por_time.items() if ps[0]["raiz"] != "selecoes")

    def lista(nomes):
        return '<p class="atalhos-linha">' + " · ".join(
            f'<a href="camisa-{slug(t)}.html">{esc(t)}</a> '
            f'<small>({len(por_time[t])})</small>' for t in nomes) + "</p>"

    corpo = [f"<h2>Seleções ({len(selecoes)})</h2>", lista(selecoes),
             f"<h2>Clubes ({len(clubes)})</h2>", lista(clubes)]
    n = len(por_time)
    return "times.html", MOLDE.format(
        titulo=esc(f"Todos os {n} times do acervo | Camisaria Esportiva FC"),
        descricao=esc(f"A lista completa dos {n} times com peça no acervo: "
                      f"{len(selecoes)} seleções e {len(clubes)} clubes, "
                      f"cada um com sua página."),
        dominio=dominio, arquivo="times.html",
        og_imagem=f"{dominio}/capa-camisaria-esportiva.jpg",
        jsonld='{"@context":"https://schema.org","@type":"CollectionPage",'
               '"name":"Todos os times"}',
        trilha='<a href="index.html">Início</a> › Times',
        h1="Todos os times do acervo",
        chamada=esc(f"{n} times entre seleções e clubes, cada um com a sua página "
                    f"e as peças que estão fotografadas. O número ao lado é quantas "
                    f"peças daquele time existem no acervo."),
        precos="", corpo="\n".join(corpo))


# =====================================================================
# SITEMAP
# =====================================================================
def sitemap(arquivos, dominio):
    hoje = date.today().isoformat()
    urls = []
    for arq, prio in arquivos:
        loc = f"{dominio}/" if arq == "index.html" else f"{dominio}/{arq}"
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{hoje}</lastmod>"
                    f"<priority>{prio}</priority></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")


# =====================================================================
def gerar(pecas, saida, dominio, whats):
    dominio = dominio.rstrip("/")
    por_time = {}
    for p in pecas:
        por_time.setdefault(p["time"], []).append(p)

    feitos = [("index.html", "1.0"), ("catalogo.html", "0.9"), ("times.html", "0.7")]

    arq, txt = pagina_times(pecas, dominio)
    open(os.path.join(saida, arq), "w", encoding="utf-8", newline="").write(txt)
    n = 1

    for a, nome, curto, filtro, texto in COLECOES:
        r = pagina_colecao(a, nome, curto, filtro, texto, pecas, dominio, whats)
        if not r:
            continue
        arq, txt = r
        open(os.path.join(saida, arq), "w", encoding="utf-8", newline="").write(txt)
        feitos.append((arq, "0.8")); n += 1

    for time, lista in sorted(por_time.items()):
        arq, txt = pagina_time(time, lista, pecas, dominio, whats)
        open(os.path.join(saida, arq), "w", encoding="utf-8", newline="").write(txt)
        feitos.append((arq, "0.6")); n += 1

    open(os.path.join(saida, "sitemap.xml"), "w", encoding="utf-8", newline="").write(
        sitemap(feitos, dominio))
    open(os.path.join(saida, "robots.txt"), "w", encoding="utf-8", newline="").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {dominio}/sitemap.xml\n")

    print(f"   {n} páginas geradas ({len(por_time)} times + "
          f"{n - len(por_time) - 1} coleções + índice)")
    print(f"   sitemap.xml com {len(feitos)} endereços")
    return n
