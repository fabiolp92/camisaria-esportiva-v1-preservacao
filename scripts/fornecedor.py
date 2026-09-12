# -*- coding: utf-8 -*-
"""Traduz o jeito do fornecedor nomear as pastas para o nosso modelo de produto.

O fornecedor batiza cada pasta com tudo que a gente precisa:

    kit-infantil-athletic-bilbao-ii-25-26
    └─ família ──┘└── time ──┘ └┘ └─ temporada
                            uniforme

Então dá pra classificar centenas de kits sem abrir uma foto. Este arquivo é o
MAPA entre as duas estruturas — é aqui que se mexe quando o fornecedor mandar
uma família nova (femininas, agasalhos, conjuntos adulto).
"""
import re
import unicodedata

# ------------------------------------------------------------------ famílias
# O prefixo da pasta diz gênero, categoria e versão da peça.
# Acrescentar uma linha aqui é como o projeto passa a entender uma linha nova
# do fornecedor. A ordem importa: o primeiro prefixo que casar é o que vale,
# então os mais específicos vêm primeiro.
FAMILIAS = [
    ("kit-infantil-",       dict(genero="infantil",  categoria="kit",     versao="kit")),
    ("conjunto-infantil-",  dict(genero="infantil",  categoria="kit",     versao="kit")),
    ("camisa-feminina-",    dict(genero="feminino",  categoria="camisa",  versao="torcedor")),
    ("kit-feminino-",       dict(genero="feminino",  categoria="kit",     versao="kit")),
    ("conjunto-",           dict(genero="masculino", categoria="kit",     versao="kit")),
    ("jaqueta-",            dict(genero="masculino", categoria="jaqueta", versao=None)),
    ("agasalho-",           dict(genero="masculino", categoria="jaqueta", versao=None)),
    ("calcao-",             dict(genero="masculino", categoria="calcao",  versao=None)),
    ("camisa-",             dict(genero="masculino", categoria="camisa",  versao="torcedor")),
]

ROMANO = {"ii": "uniforme2", "iii": "uniforme3", "iv": "uniforme4"}

ROTULO_UNIFORME = {"uniforme1": "1º Uniforme", "uniforme2": "2º Uniforme",
                   "uniforme3": "3º Uniforme", "uniforme4": "4º Uniforme",
                   "retro": "Retrô"}

# palavras que aparecem no fim do nome e NÃO são código aleatório
CAUDA = {"oficial", "adidas", "puma", "nike", "preto", "creme", "marrom", "copia",
         "uniforme", "reserva", "vinotinto", "eusebio", "vallejo", "centenario",
         "especial", "anos", "jogo", "pre", "estilo", "retro", "treino", "goleiro",
         "mundo", "copa", "do", "de", "x", "one", "piece", "travis", "scott", "off",
         "white", "efteling", "sou", "vascaino", "pantera", "negra", "estrelas",
         "edicao", "fc", "cf", "ud", "cp", "sc"}

# frases que descrevem a peça, nunca o time — saem antes de qualquer coisa
RUIDO = [r"copa-do-mundo", r"copa-\d{4}", r"copa", r"uniforme-oficial",
         r"uniforme-reserva", r"edicao-\d+-anos", r"edicao-especial", r"\d+-anos",
         r"estilo-retro", r"pre-jogo", r"2-estrelas", r"x-one-piece",
         r"x-travis-scott", r"x-off-white", r"pantera-negra", r"sou-vascaino",
         r"oficial", r"uniforme", r"reserva", r"copia", r"adidas", r"puma", r"nike",
         r"goleiro", r"treino", r"efteling", r"centenario", r"vinotinto", r"eusebio",
         r"vallejo", r"creme", r"marrom", r"preto"]

# variantes que viram peça própria em vez de virar 1º/2º/3º uniforme
VARIANTES = [("goleiro", "goleiro"), ("treino", "treino"), ("pre-jogo", "pre-jogo"),
             ("x-one-piece", "one-piece"), ("x-travis-scott", "travis-scott"),
             ("x-off-white", "off-white"), ("125-anos", "125-anos"),
             ("100-anos", "100-anos"), ("120-anos", "120-anos"),
             ("edicao-especial", "edicao-especial"), ("centenario", "centenario"),
             ("efteling", "efteling"), ("pantera-negra", "pantera-negra"),
             ("estilo-retro", "estilo-retro"), ("2-estrelas", "2-estrelas"),
             ("sou-vascaino", "sou-vascaino")]

# como o fornecedor escreve -> como o catálogo escreve
APELIDOS = {
    "barcelona": "FC Barcelona", "milan": "AC Milan", "inter-de-milao": "Inter de Milão",
    "psg": "Paris Saint-Germain", "lyon": "Olympique de Lyon",
    "olympique-marseille": "Olympique de Marselha", "fc-porto": "Porto",
    "sporting-cp": "Sporting CP", "psv-eindhoven": "PSV Eindhoven",
    "atletico-de-madrid": "Atlético de Madrid", "athletic-bilbao": "Athletic Bilbao",
    "bayern-de-munique": "Bayern de Munique", "borussia-dortmund": "Borussia Dortmund",
    "real-betis": "Real Betis", "sevilla-fc": "Sevilla", "valencia-cf": "Valencia",
    "manchester-united": "Manchester United", "manchester-city": "Manchester City",
    "newcastle-united": "Newcastle United", "newcastle": "Newcastle United",
    "west-ham": "West Ham United", "vasco": "Vasco da Gama",
    "vasco-da-gama": "Vasco da Gama", "aston-villa": "Aston Villa",
    "boca-juniors": "Boca Juniors", "colo-colo": "Colo-Colo",
    "inter-miami": "Inter Miami", "rb-leipzig": "RB Leipzig",
    "sporting-braga": "Braga", "real-madrid": "Real Madrid", "arsenal": "Arsenal",
    "chelsea": "Chelsea", "everton": "Everton", "napoli": "Napoli", "ajax": "Ajax",
    "benfica": "Benfica", "villarreal": "Villarreal", "cruzeiro": "Cruzeiro",
    "internacional": "Internacional", "flamengo": "Flamengo", "girona": "Girona",
    "selecao-brasil": "Brasil", "selecao-alemanha": "Alemanha",
    "selecao-alemanha-azul": "Alemanha", "selecao-espanha": "Espanha",
    "selecao-franca": "França", "selecao-portugal": "Portugal",
    "selecao-inglaterra": "Inglaterra", "selecao-mexico": "México",
    "selecao-uruguai": "Uruguai", "selecao-colombia": "Colômbia",
    "colombia": "Colômbia", "selecao-equador": "Equador",
    "selecao-croacia": "Croácia", "selecao-noruega": "Noruega",
    "selecao-suecia": "Suécia", "selecao-suica": "Suíça",
    "selecao-turquia": "Turquia", "selecao-escocia": "Escócia",
    "selecao-chile": "Chile", "selecao-paraguai": "Paraguai",
    "selecao-venezuela": "Venezuela", "selecao-marrocos": "Marrocos",
    "selecao-argentina": "Argentina", "selecao-estados-unidos": "Estados Unidos",
    "selecao-coreia-do-sul": "Coreia do Sul", "selecao-australia": "Austrália",
    "selecao-argelia": "Argélia", "selecao-senegal": "Senegal",
    "selecao-tunisia": "Tunísia", "selecao-catar": "Catar",
    "selecao-panama": "Panamá", "selecao-cabo-verde": "Cabo Verde",
    "selecao-africa-do-sul": "África do Sul", "selecao-arabia-saudita": "Arábia Saudita",
}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def _limpar(n):
    n = re.sub(r"(\d{2}-\d{2})1$", r"\1", n)                 # cópia do fornecedor
    ped = n.split("-")
    if len(ped[-1]) == 5 and ped[-1] not in CAUDA and re.fullmatch(r"[a-z0-9]{5}", ped[-1]):
        n = "-".join(ped[:-1])                               # código aleatório no fim
    for r in RUIDO:
        n = re.sub(rf"(?:^|-){r}(?=-|$)", "", n)
    return n.strip("-")


def _temporada(nome):
    """O fornecedor escreve de cinco jeitos: 2026-2027, 2025-2026, 2025-26,
    25-26 e só 2026."""
    for padrao, conv in (
        (r"(20\d{2})-(20\d{2})", lambda m: f"{m.group(1)[2:]}-{m.group(2)[2:]}"),
        (r"(20\d{2})-(\d{2})",   lambda m: f"{m.group(1)[2:]}-{m.group(2)}"),
        (r"(?<!\d)(\d{2})-(\d{2})(?!\d)", lambda m: f"{m.group(1)}-{m.group(2)}"),
        (r"(?<!\d)(2025|2026)(?!\d)", lambda m: "26-27" if m.group(1) == "2026" else "25-26"),
    ):
        m = re.search(padrao, nome)
        if m:
            return conv(m), (nome[:m.start()] + nome[m.end():]).strip("-").replace("--", "-")
    return None, nome


def familia_de(pasta):
    for prefixo, dados in FAMILIAS:
        if pasta.startswith(prefixo):
            return prefixo, dict(dados)
    return None, None


def classificar(pasta, nomes_de_times):
    """pasta -> dicionário descrevendo a peça, ou com 'fora' explicando por que
    ela não entra no catálogo."""
    prefixo, fam = familia_de(pasta)
    if not fam:
        return {"pasta": pasta, "fora": "família de produto desconhecida "
                                        "(veja FAMILIAS no fornecedor.py)"}

    variante = next((v for chave, v in VARIANTES if chave in pasta), None)
    retro = "retro" in pasta.split("-")[:4]

    p = pasta[len(prefixo):]
    if p.startswith("retro-"):
        p = p[6:]
    p = _limpar(p)
    temporada, p = _temporada(p)
    p = re.sub(r"(?:^|-)(19\d{2}|20\d{2})(?=-|$)", "", p).strip("-")

    uniforme, ped = "uniforme1", [t for t in p.split("-") if t]
    for i, t in enumerate(ped):
        if t in ROMANO:
            uniforme, ped = ROMANO[t], ped[:i] + ped[i + 1:]
            break
    # em algumas seleções o 2º uniforme vem como "-2-" em vez de "-ii-"
    if uniforme == "uniforme1" and ped and ped[-1] == "2":
        uniforme, ped = "uniforme2", ped[:-1]
    ano_retro = None
    if retro:
        m = re.search(r"(?<!\d)(\d{2}-\d{2}|19\d{2}|20\d{2})(?!\d)", pasta)
        ano_retro = m.group(1) if m else None
        uniforme, temporada = "retro", "retro"

    slug = "-".join(ped)
    time = APELIDOS.get(slug)
    # o apelido so vale se o nome pra onde ele aponta existir MESMO no times.json.
    # Sem esta checagem, um apelido escrito errado passa na classificacao e so
    # estoura la na hora de gravar, no meio da importacao.
    if time and time not in nomes_de_times:
        time = None
    if not time:
        alvo = norm(slug.replace("selecao-", ""))
        time = next((n for n in nomes_de_times if norm(n) == alvo), None)

    item = dict(fam, pasta=pasta, time=time, uniforme=uniforme, temporada=temporada,
                variante=variante, ano_retro=ano_retro, slug_fornecedor=slug, fora=None)

    if not time:
        item["fora"] = f"time '{slug}' não está no times.json"
    elif uniforme == "uniforme4":
        item["fora"] = "4º uniforme (o catálogo vai até o 3º)"
    elif variante:
        # A peca existe e e boa — Barcelona x Travis Scott, Real Madrid 125 anos,
        # goleiro. So que o catalogo ainda nao tem onde mostrar "edicao especial":
        # ela apareceria como se fosse o 1o uniforme comum. Entra na Fase 3.
        item["fora"] = f"variante '{variante}': o catálogo ainda não tem esse tipo de peça"
    elif retro:
        # Retro infantil ja existe no site, mas o time precisa dos anos cadastrados
        # em RETROS pra cada edicao virar um card separado. Sem isso, as tres retros
        # do Real Madrid virariam uma so.
        item["fora"] = "retrô: falta cadastrar o ano em RETROS"
    elif temporada not in ("26-27", "25-26"):
        item["fora"] = f"temporada '{temporada}' não reconhecida"
    return item


def chave_do_produto(item, ROTULO=ROTULO_UNIFORME):
    """A chave exata que o dados.js usa. Tem que bater, caractere por caractere,
    com a que o catalogo.html gera em JavaScript.

    A variante e o ano da retro entram na chave de proposito: sem eles, o kit
    normal do Barcelona e o Barcelona x Travis Scott — mesmo time, mesmo
    uniforme, mesma temporada — geram a MESMA chave, e a segunda importacao
    apaga as fotos da primeira sem avisar."""
    g = {"masculino": "Masculino", "feminino": "Feminino", "infantil": "Infantil"}[item["genero"]]
    nome = item["time"]
    if item["categoria"] == "jaqueta":
        return f"{nome} - {g} - Jaqueta"
    if item["uniforme"] == "retro":
        ano = f" {item['ano_retro']}" if item.get("ano_retro") else ""
        return f"{nome} - {g} - Retrô{ano}"
    temp = item["temporada"].replace("-", "/")
    uni = ROTULO[item["uniforme"]]
    if item["genero"] == "infantil":
        return f"{nome} - {g} - {temp} - {uni} Kit Infantil"
    if item["categoria"] == "calcao":
        return f"{nome} - {g} - {temp} - Calção {uni}"
    versao = "Versão Jogador" if item["versao"] == "jogador" else "Versão Torcedor"
    return f"{nome} - {g} - {temp} - {uni} {versao}"


def colecoes_do_produto(item, time_row):
    """Em que vitrines esta peça aparece. É o que monta o menu do cliente."""
    saida = []
    if item["genero"] == "infantil":
        saida += ["kids"]
    if item["genero"] == "feminino":
        saida += ["feminino"]
    if item["categoria"] == "kit":
        saida += ["conjuntos"]
    if item["categoria"] == "jaqueta":
        saida += ["agasalhos"]
    if item["uniforme"] == "retro":
        saida += ["retro"]
    if item["variante"] == "goleiro":
        saida += ["goleiro"]
    elif item["variante"]:
        saida += ["edicoes"]
    if time_row and time_row["raiz"] == "selecoes":
        saida += ["copa-2026"]
    if time_row and (time_row["liga"] or "").startswith("Brasileirão"):
        saida += ["brasileirao"]
    if time_row and time_row["grupo"] == "Europa":
        saida += ["europa"]
    return sorted(set(saida))
