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
    # o fornecedor escreve o conjunto de quatro jeitos. Os prefixos mais longos
    # TÊM que vir antes do "conjunto-" seco, senão sobra "de-treino-" grudado no
    # nome do time e a peça é recusada por "time não existe".
    ("conjunto-de-treino-", dict(genero="masculino", categoria="kit",     versao="kit")),
    ("conjunto-de-viagem-", dict(genero="masculino", categoria="kit",     versao="kit")),
    ("conjunto-treino-",    dict(genero="masculino", categoria="kit",     versao="kit")),
    ("conjunto-viagem-",    dict(genero="masculino", categoria="kit",     versao="kit")),
    ("conjunto-",           dict(genero="masculino", categoria="kit",     versao="kit")),
    ("uniforme-completo-",  dict(genero="masculino", categoria="kit",     versao="kit")),
    ("uniforme-goleiro-",   dict(genero="masculino", categoria="camisa",  versao="torcedor")),
    ("uniforme-",           dict(genero="masculino", categoria="camisa",  versao="torcedor")),
    ("casaco-",             dict(genero="masculino", categoria="jaqueta", versao=None)),
    ("camisa-polo-",        dict(genero="masculino", categoria="polo",    versao=None)),
    ("polo-",               dict(genero="masculino", categoria="polo",    versao=None)),
    ("jaqueta-",            dict(genero="masculino", categoria="jaqueta", versao=None)),
    ("agasalho-",           dict(genero="masculino", categoria="jaqueta", versao=None)),
    ("calcao-",             dict(genero="masculino", categoria="calcao",  versao=None)),
    ("camisa-",             dict(genero="masculino", categoria="camisa",  versao="torcedor")),
    ("corta-vento-",        dict(genero="masculino", categoria="jaqueta", versao=None)),
    ("moletom-",            dict(genero="masculino", categoria="jaqueta", versao=None)),
    ("regata-",             dict(genero="masculino", categoria="regata",  versao=None)),
    ("cropped-",            dict(genero="feminino",  categoria="cropped", versao=None)),
    ("short-",              dict(genero="feminino",  categoria="calcao",  versao=None)),
    ("calca-",              dict(genero="masculino", categoria="calca",   versao=None)),
    ("meiao-",              dict(genero="masculino", categoria="meiao",   versao=None)),
    ("luva-",               dict(genero="masculino", categoria="luva",    versao=None)),
]

GENERO_PALAVRA = {"feminina": "feminino", "feminino": "feminino",
                  "infantil": "infantil"}

ROMANO = {"i": "uniforme1", "ii": "uniforme2", "iii": "uniforme3",
          "iv": "uniforme4"}

ROTULO_UNIFORME = {"uniforme1": "1º Uniforme", "uniforme2": "2º Uniforme",
                   "uniforme3": "3º Uniforme", "uniforme4": "4º Uniforme",
                   "retro": "Retrô", "goleiro": "Goleiro", "treino": "Linha de Treino",
                   "pre-jogo": "Pré-Jogo", "cropped": "Cropped", "regata": "Regata",
                   "aquecimento": "Aquecimento"}

# variantes que não são goleiro/treino viram "edição" — a peça mantém o
# uniforme que já tinha e ganha este rótulo extra. Se uma variante nova
# aparecer e não estiver aqui, ela não é recusada: o rótulo é gerado a partir
# do slug e o relatório avisa pra eu revisar o texto.
ROTULO_EDICAO = {
    "one-piece":       "Edição One Piece",
    "travis-scott":    "Edição Travis Scott",
    "off-white":       "Edição Off-White",
    "efteling":        "Edição Efteling",
    "pantera-negra":   "Pantera Negra",
    "estilo-retro":    "Estilo Retrô",
    "sou-vascaino":    "Sou Vascaíno",
    "edicao-especial": "Edição Especial",
    "centenario":      "Centenário",
    "2-estrelas":      "2 Estrelas",
    "125-anos":        "125 Anos",
    "150-anos":        "150 Anos",
    "120-anos":        "120 Anos",
    "100-anos":        "100 Anos",
    "oktoberfest":     "Oktoberfest",
    "originals":       "Originals",
    "icon":            "Icon",
    "cr7":             "CR7",
    "casual":          "Linha Casual",
    "spzl":            "SPZL",
    "bravest-mary":    "Bravest Mary",
    "ted-lasso":       "Ted Lasso",
    "manga-longa":     "Manga Longa",
    "corta-vento":     "Corta-Vento",
    "goleiro":         "Goleiro",
    "treino":          "Linha de Treino",
    "aquecimento":     "Aquecimento",
    "pre-jogo":        "Pré-Jogo",
}

# erros de digitação do fornecedor na temporada — uma linha por erro, não uma
# regra "esperta". Quando aparecer o próximo, é só acrescentar aqui.
CORRECOES_TEMPORADA = {"26-26": "26-27", "24-24": "24-25"}

# A temporada que vale hoje. Serve de reserva pras peças que o fornecedor
# anuncia SEM ano nenhum no nome (a linha casual, as SPZL). Trocar aqui quando
# virar a temporada.
TEMPORADA_ATUAL = "26-27"

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
         r"vallejo", r"creme", r"marrom", r"preto", r"camisa", r"jogador",
         r"titular", r"third-kit", r"home-kit", r"away-kit",
         r"feminina", r"feminino", r"manga-longa", r"fa-cup", r"tdk",
         r"corta-vento", r"retro", r"calcio", r"edicao-limitada", r"edicao-comemorativa", r"estreia",
         r"cristiano-ronaldo", r"makaay", r"umbro", r"reggae",
         r"reebok", r"algodao", r"tang", r"polo", r"bukta", r"hummel",
         r"futebol-espanhol", r"away", r"terceira", r"torcedor", r"mizuno",
         r"casual", r"spzl", r"visitante", r"exclusiva", r"estilo", r"stadium",
         r"original-x-thrasher-x-afa", r"cactus-jack", r"travis-scott",
         r"total-90"]

# variantes que viram peça própria em vez de virar 1º/2º/3º uniforme
VARIANTES = [("goleiro", "goleiro"), ("treino", "treino"), ("pre-jogo", "pre-jogo"),
             # o corta-vento é uma peça, não um acabamento: sem isso ele e o
             # casaco de treino da mesma seleção geram a MESMA chave de jaqueta
             ("corta-vento", "corta-vento"),
             ("x-one-piece", "one-piece"), ("x-travis-scott", "travis-scott"),
             ("x-off-white", "off-white"), ("125-anos", "125-anos"), ("150-anos", "150-anos"),
             ("100-anos", "100-anos"), ("120-anos", "120-anos"),
             ("edicao-especial", "edicao-especial"), ("centenario", "centenario"),
             # "cr7" tem 3 letras e era descartado como token curto, então a
             # Edição Especial CR7 de Portugal virava cópia da Edição Especial
             # comum. É provavelmente a peça mais vendável do lote — fica.
             ("cr7", "cr7"), ("casual", "casual"), ("spzl", "spzl"),
             # a colab Travis Scott vem sem o "x-" nesta linha, e sem rótulo
             # ela virava só "Brasil - Retrô", como se fosse uma retrô comum
             ("cactus-jack", "travis-scott"),
             # colab da marca de café com o Vasco: sem o rótulo ela virava
             # "Vasco da Gama 26/27 1º Uniforme" — que é OUTRA camisa
             ("bravest", "bravest-mary"), ("ted-lasso", "ted-lasso"),
             ("efteling", "efteling"), ("pantera-negra", "pantera-negra"),
             ("estilo-retro", "estilo-retro"), ("2-estrelas", "2-estrelas"),
             ("sou-vascaino", "sou-vascaino"),
             # linhas que o fornecedor usa nas adultas e que sao peca propria:
             # sem isso a Oktoberfest e a titular do Bayern geram a MESMA chave
             ("manga-longa", "manga-longa"), ("aquecimento", "aquecimento"),
             ("oktoberfest", "oktoberfest"), ("originals", "originals"),
             ("icon", "icon"), ("pre-jogo", "pre-jogo")]

# como o fornecedor escreve -> como o catálogo escreve
APELIDOS = {
    "barcelona": "FC Barcelona", "milan": "AC Milan", "inter-de-milao": "Inter de Milão",
    "psg": "Paris Saint-Germain", "lyon": "Olympique de Lyon",
    "olympique-marseille": "Olympique de Marselha", "fc-porto": "Porto",
    "olympique-lyon": "Olympique de Lyon", "manchester-city": "Manchester City",
    "ec-vitoria": "Vitória", "club-america": "Club América",
    # como o fornecedor escreve as retrôs — nomes antigos, siglas e erros dele
    "1-fc-koln": "FC Köln", "koln": "FC Köln",
    "atleticod-de-madrid": "Atlético de Madrid",
    "bayer-leverusen": "Bayer Leverkusen",
    "ca-osasuna": "Osasuna", "ca-independiente": "Independiente",
    "deportivo-de-la-coruna": "Deportivo La Coruña",
    "hamburgo": "Hamburger SV", "hamburgo-sv": "Hamburger SV",
    "olympique-de-marseille": "Olympique de Marselha",
    "roma": "AS Roma", "stuttgart": "VfB Stuttgart",
    "sporting-lisboa": "Sporting CP", "rc-strasbourg": "Strasbourg",
    "fc-girondins-de-bordeaux": "Bordeaux", "girondins-de-bordeaux": "Bordeaux",
    "frankfurt": "Eintracht Frankfurt", "bayern-munique": "Bayern de Munique",
    "rcd-mallorca": "Mallorca", "getafe-cf": "Getafe", "granada-cf": "Granada",
    "cadiz-cf": "Cádiz", "hercules-cf": "Hércules", "watford-fc": "Watford",
    "coventry": "Coventry City", "aberdeen-fc": "Aberdeen",
    "fc-st-pauli": "St. Pauli", "besiktas-jk": "Beşiktaş",
    "club-brugge-kv": "Club Brugge", "aek-athens": "AEK Atenas",
    "u-s-cremonese": "Cremonese", "cremonese-calcio": "Cremonese",
    "padova-calcio": "Padova", "perugia-calcio": "Perugia",
    "hannover": "Hannover 96", "hannover-92": "Hannover 96",
    "selecao-uniao-sovietica": "União Soviética", "selecao-iugoslavia": "Iugoslávia",
    "iugoslavia": "Iugoslávia", "selecao-bulgaria": "Bulgária",
    "selecao-irlanda": "Irlanda", "tchecoslovaquia": "Tchecoslováquia",
    "selecao-tchecoslovaquia": "Tchecoslováquia",
    "athletico-pr": "Athletico Paranaense", "brondby": "Brøndby",
    "sporting": "Sporting CP", "betis": "Real Betis",
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
    "al-nassr": "Al-Nassr", "al-nassr-fc": "Al-Nassr", "club-leon": "Club León",
    "cruz-azul": "Cruz Azul", "levante-ud": "Levante UD",
    "los-angeles-fc": "Los Angeles FC", "malaga": "Málaga CF", "monterrey": "Monterrey",
    "rangers-fc": "Rangers FC", "rc-lens": "RC Lens", "real-oviedo": "Real Oviedo",
    "sporting-gijon": "Sporting Gijón", "cordoba-cf": "Córdoba CF", "celtic": "Celtic",
    # seleções da leva das seleções — inclusive os erros de digitação dele
    "selecao-guatemala": "Guatemala", "selecao-honduras": "Honduras",
    "selecao-jamaica": "Jamaica", "jamaica": "Jamaica",
    "selecao-albania": "Albânia", "selecao-el-salvador": "El Salvador",
    "selecao-bolivia": "Bolívia", "selecao-eslovenia": "Eslovênia",
    "selecao-finlandia": "Finlândia", "selecao-guine-equatorial": "Guiné Equatorial",
    "selecao-hungria": "Hungria", "selecao-indonesia": "Indonésia",
    "selecao-israel": "Israel", "selecao-mali": "Mali",
    "selecao-pais-de-gales": "País de Gales", "pais-de-gales": "País de Gales",
    "selecao-filipinas": "Filipinas", "selecao-grecia": "Grécia",
    "selecao-islandia": "Islândia", "selecao-malasia": "Malásia",
    "selecao-romenia": "Romênia",
    "selecao-emirados-arabes-unidos": "Emirados Árabes Unidos",
    "selecao-emirados-arabe-unidos": "Emirados Árabes Unidos",
    "selecao-bosnia-herzegovina": "Bósnia e Herzegovina",
    "bosnia-herzegovina": "Bósnia e Herzegovina",
    "selecao-republica-tcheca": "Chéquia", "republica-tcheca": "Chéquia",
    "selecao-alemanh": "Alemanha",          # falta o "a" no anúncio dele
    "selecao-holanda": "Holanda", "selecao-belgica": "Bélgica",
    "selecao-japao": "Japão", "selecao-italia": "Itália",
    "selecao-gana": "Gana", "selecao-nigeria": "Nigéria",
    "selecao-canada": "Canadá", "selecao-peru": "Peru",
    "original-x-thrasher-x-afa-argentina": "Argentina",
    # clubes espanhóis — como o fornecedor escreve na leva da Espanha
    "atletico-madrid": "Atlético de Madrid", "rcd-espanyol": "Espanyol",
    "rc-celta": "Celta de Vigo", "celta-vigo": "Celta de Vigo",
    "tenerife": "CD Tenerife", "cd-tenerife": "CD Tenerife",
    "cd-castellon": "CD Castellón", "ud-almeria": "UD Almería",
    "sd-eibar": "SD Eibar", "elche-cf": "Elche", "burgos-cf": "Burgos CF",
    "leganes": "Leganés", "real-murcia": "Real Murcia",
    "recreativo-de-huelva": "Recreativo de Huelva", "albacete": "Albacete",
    "clube-do-remo": "Remo",
    # brasileiros — Botafogo-PB e Botafogo-SP são OUTROS clubes, não o do Rio.
    # Sem estas linhas as camisas deles iam pro site com o escudo errado.
    "botafogo-pb": "Botafogo-PB", "botafogo-sp": "Botafogo-SP",
    "ec-bahia": "Bahia", "red-bull-bragantino": "Red Bull Bragantino",
    "bragantino": "Red Bull Bragantino", "santa-cruz": "Santa Cruz",
    "ceara": "Ceará", "chapecoense": "Chapecoense", "figueirense": "Figueirense",
    "sport-recife": "Sport Recife", "atletico-mineiro": "Atlético Mineiro",
    # ingleses — o fornecedor abrevia e mistura sigla com nome inteiro
    "birmingham": "Birmingham City", "bournemouth": "AFC Bournemouth",
    "afc-bournemouth": "AFC Bournemouth", "afc-richmond": "AFC Richmond",
    "brentford-fc": "Brentford", "brighton-hove-albion": "Brighton",
    "qpr": "Queens Park Rangers", "queens-park-rangers": "Queens Park Rangers",
    "ipswich-town-fc": "Ipswich Town", "wrexham-afc": "Wrexham",
    "norwich-city-fc": "Norwich City", "newcastle": "Newcastle United",
    "newcastle-united-fc": "Newcastle United", "liverpool-fc": "Liverpool",
    "chelsea-fc": "Chelsea", "sunderland-afc": "Sunderland",
    "tottenham-hotspur": "Tottenham", "west-bromwich-albion": "West Bromwich",
    "west-ham-united": "West Ham United", "sheffield-wed": "Sheffield Wednesday",
    # italianos
    "como-1907": "Como", "palermo-fc": "Palermo", "ravenna-fc": "Ravenna",
    "inter-milao": "Inter de Milão", "internazionale": "Inter de Milão",
    "bologna-fc": "Bologna", "torino-fc": "Torino", "venezia-fc": "Venezia",
    "cagliari-calcio": "Cagliari", "parma-calcio": "Parma",
    # alemães
    "sv-werder-bremen": "Werder Bremen", "werder-bremen": "Werder Bremen",
    "vfl-bochum": "VfL Bochum", "bochum": "VfL Bochum",
    "union-berlin": "Union Berlin", "fc-union-berlin": "Union Berlin",
    "nuremberg": "Nuremberg", "1-fc-nurnberg": "Nuremberg",
    "rot-weiss-essen": "Rot-Weiss Essen", "st-pauli": "St. Pauli",
    "schalke-04": "Schalke 04", "fc-schalke-04": "Schalke 04",
    "hamburgo-sv": "Hamburger SV", "vfb-stuttgart": "VfB Stuttgart",
    # portugueses
    "sl-benfica": "Benfica", "sc-braga": "Braga", "fc-famalicao": "Famalicão",
    "os-belenenses": "Belenenses", "vitoria-guimaraes": "Vitória de Guimarães",
    # franceses — ele alterna entre o nome completo e o apelido curto
    "marseille": "Olympique de Marselha", "om": "Olympique de Marselha",
    "monaco": "AS Monaco", "as-monaco": "AS Monaco",
    "racing-strasbourg": "Strasbourg", "rc-strasbourg": "Strasbourg",
    "as-saint-etienne": "Saint-Étienne", "saint-etienne": "Saint-Étienne",
    "stade-rennais": "Rennes", "stade-rennes": "Rennes",
    "paris-fc": "Paris FC", "versailles": "Versailles",
    "lille-osc": "Lille", "losc-lille": "Lille", "losc": "Lille",
    "lens": "RC Lens", "olympique-lyonnais": "Olympique de Lyon",
    # argentinos — o "ca-"/"atletico-" da frente e o nome da cidade no fim
    "atletico-rosario-central": "Rosario Central", "rosario-central": "Rosario Central",
    "estudiantes-la-plata": "Estudiantes de La Plata",
    "ca-river-plate": "River Plate", "river": "River Plate",
    "ca-boca-juniors": "Boca Juniors", "ca-san-lorenzo": "San Lorenzo",
    "newells-old-boys": "Newell's Old Boys", "almirante-brown": "Almirante Brown",
    # o resto do mundo — MLS, Liga MX, Turquia, Grécia, Escócia, Japão, Arábia
    "al-ahly-sc": "Al Ahly", "al-hilal": "Al-Hilal", "atlas-fc": "Atlas",
    "cd-olimpia": "Olimpia", "cf-montreal": "CF Montréal",
    "club-tijuana-xolos": "Club Tijuana", "tijuana": "Club Tijuana",
    "chivas": "Chivas Guadalajara", "deportivo-toluca": "Toluca",
    "estrela-vermalha": "Estrela Vermelha", "f-c-copenhagen": "FC Copenhagen",
    "gnk-dinamo-zagreb": "Dinamo Zagreb", "los-angeles-galaxy": "LA Galaxy",
    "los-angeles": "LA Galaxy", "new-york-city": "New York City FC",
    "pumas-unam": "Pumas UNAM", "rangers": "Rangers FC",
    "rsc-anderlecht": "Anderlecht", "san-diego": "San Diego FC",
    "st-louis": "St. Louis City", "psv": "PSV Eindhoven",
    "vancouver-whitecaps": "Vancouver Whitecaps", "urawa-red-diamonds": "Urawa Red Diamonds",
    "nagoya-grampus": "Nagoya Grampus", "kyoto-sanga": "Kyoto Sanga",
    "cerezo-osaka": "Cerezo Osaka", "fc-tokyo": "FC Tokyo",
    "montevideo-city-torque": "Montevideo City Torque",
    "maria-bravest-mary-vasco": "Vasco da Gama",
    "maria-bravest-coffee-mary-vasco": "Vasco da Gama",
    # NÃO é a Irlanda: são duas seleções diferentes, e o achar_time encurtava
    # "irlanda-do-norte" até bater em "Irlanda" e sobrava "Norte" como rótulo
    "selecao-irlanda-do-norte": "Irlanda do Norte",
    "irlanda-do-norte": "Irlanda do Norte",
}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def _limpar(n):
    ped = n.split("-")
    # PRIMEIRO o código aleatório do fim, DEPOIS o dígito de cópia. Invertido,
    # a regra do dígito comia um número de dentro do código ("16940" virava
    # "1694") e a temporada saía errada.
    #
    # O código tem 5 caracteres e SEMPRE pelo menos um número ("zpu0a",
    # "1472t", "16940"). Exigir o número evita comer palavra de verdade:
    # "betis" tem 5 letras e estava sumindo do Real Betis.
    #
    # Cuidado com o caso "20251": é a temporada 2025 com o dígito de cópia
    # colado, não código. Já "16940" é código de verdade. O que separa os dois
    # é o ano fazer sentido: 2025 sim, 1694 não. Sem esta distinção, 25 peças
    # das seleções perdiam a temporada inteira e eram recusadas.
    ult = ped[-1]
    ano_com_digito = (len(ult) == 5 and ult.isdigit()
                      and 1960 <= int(ult[:4]) <= 2027)
    if (len(ult) == 5 and ult not in CAUDA and re.fullmatch(r"[a-z0-9]{5}", ult)
            and any(c.isdigit() for c in ult) and not ano_com_digito):
        n = "-".join(ped[:-1])
    # dígito de cópia colado no fim da temporada, em todas as formas que o
    # fornecedor usa: 25-261, 2026-20271, 19901, 20161
    n = re.sub(r"((?:\d{2}-\d{2})|(?:\d{4}-\d{4})|(?:19\d{2})|(?:20\d{2}))\d$", r"\1", n)
    for r in RUIDO:
        n = re.sub(rf"(?:^|-){r}(?=-|$)", "", n)
    return n.strip("-")


def _temporada(nome):
    """O fornecedor escreve de cinco jeitos: 2026-2027, 2025-2026, 2025-26,
    25-26 e só 2026.

    Cuidado com os clubes que têm NÚMERO no nome: em "hannover-96-26-27" o
    primeiro par que aparece é "96-26", que não é temporada nenhuma — é o 96 do
    Hannover colado no 26 da temporada. Em "schalke-04-26-27" era pior: o
    "04-26" era arrancado e sobrava "schalke-27" como nome do time.

    Por isso a busca junta TODOS os pares possíveis (inclusive os que se
    sobrepõem) e fica com o primeiro que é uma temporada de verdade — dois anos
    seguidos. Se nenhum for, devolve o primeiro, que é o que ela fazia antes."""
    candidatos = []
    for padrao, conv in (
        (r"(20\d{2})-(20\d{2})", lambda m: f"{m.group(1)[2:]}-{m.group(2)[2:]}"),
        (r"(20\d{2})-(\d{2})",   lambda m: f"{m.group(1)[2:]}-{m.group(2)}"),
        (r"(?<!\d)(\d{2})-(\d{2})(?!\d)", lambda m: f"{m.group(1)}-{m.group(2)}"),
        (r"(?<!\d)(2025|2026)(?!\d)", lambda m: "26-27" if m.group(1) == "2026" else "25-26"),
    ):
        # o (?=...) faz a varredura achar pares sobrepostos: sem isso, depois de
        # casar "96-26" a busca continua DEPOIS do 26 e nunca vê o "26-27"
        for m in re.finditer(f"(?={padrao})", nome):
            inteiro = re.match(padrao, nome[m.start():])
            if inteiro:
                ini, fim = m.start(), m.start() + inteiro.end()
                candidatos.append((conv(inteiro), ini, fim))
        if candidatos:
            break
    if not candidatos:
        return None, nome
    bons = [c for c in candidatos if temporada_valida(CORRECOES_TEMPORADA.get(c[0], c[0]))]
    valor, ini, fim = (bons or candidatos)[0]
    return valor, (nome[:ini] + nome[fim:]).strip("-").replace("--", "-")


def familia_de(pasta):
    for prefixo, dados in FAMILIAS:
        if pasta.startswith(prefixo):
            return prefixo, dict(dados)
    # As vezes ele inverte e escreve "aston-villa-camisa-25-26-holte-end", com o
    # time na frente. Se a palavra "camisa" aparece em qualquer lugar, e camisa.
    if "camisa" in pasta.split("-"):
        return "", dict(genero="masculino", categoria="camisa", versao="torcedor")
    return None, None


def achar_time(slug, nomes_de_times):
    """Acha o time mesmo com texto de marketing colado no fim do nome.

    Nas camisas adultas o fornecedor escreve coisas como
    "napoli-serie-a-champions-league" ou "barcelona-third-kit-fc-barcelona".
    Listar cada frase nova numa lista de ruido seria enxugar gelo. Em vez
    disso a gente encurta o slug da direita pra esquerda ate bater com um time
    de verdade — do mais longo pro mais curto, pra "inter-de-milao" nunca
    virar "inter".

    Devolve (nome_do_time, sobra) — a sobra e o texto que ficou pendurado
    depois do nome, que serve pra saber se era so marketing."""
    ped = [x for x in slug.split("-") if x]
    for corte in range(len(ped), 0, -1):
        s = "-".join(ped[:corte])
        t = APELIDOS.get(s)
        if t and t in nomes_de_times:
            return t, "-".join(ped[corte:])
        alvo = norm(s.replace("selecao-", ""))
        t = next((n for n in nomes_de_times if norm(n) == alvo), None)
        if t:
            return t, "-".join(ped[corte:])
    # Última tentativa: o dígito de cópia caiu em cima do NOME DO TIME, porque o
    # time estava no fim do endereço ("camisa-casual-inter-miami1"). Tira o
    # dígito e procura de novo — sem isto, quatro camisas da linha casual do
    # Inter Miami sumiam.
    if ped and re.search(r"\d$", ped[-1]) and not ped[-1].isdigit():
        limpo = ped[:-1] + [re.sub(r"\d+$", "", ped[-1])]
        if limpo[-1]:
            return achar_time("-".join(limpo), nomes_de_times)
    return None, slug


def temporada_valida(t):
    """Aceita qualquer temporada NN-NN de anos consecutivos, de 60-61 ate 26-27.

    Antes a lista era fixa em 25-26 e 26-27, e o PSG IV 20-21 caia fora como se
    fosse erro de digitacao. Peca de temporada antiga nao e erro — e raridade,
    que e justamente o que a marca vende."""
    if not t:
        return False
    m = re.fullmatch(r"(\d{2})-(\d{2})", t)
    if not m:
        return False
    a, b = int(m.group(1)), int(m.group(2))
    if (a + 1) % 100 != b:
        return False
    return a >= 60 or a <= 26


def classificar(pasta, nomes_de_times):
    """pasta -> dicionário descrevendo a peça, ou com 'fora' explicando por que
    ela não entra no catálogo."""
    prefixo, fam = familia_de(pasta)
    if not fam:
        return {"pasta": pasta, "fora": "família de produto desconhecida "
                                        "(veja FAMILIAS no fornecedor.py)"}

    # Nas adultas o fornecedor marca a versao e o uniforme por extenso:
    # "camisa-real-madrid-reserva-jogador-26-27" e o 2o uniforme, versao jogador.
    ped_cru = pasta.split("-")
    # Nas femininas ele escreve o genero DEPOIS do time ("camisa-gremio-iii-
    # feminina-25-26"), entao o prefixo da familia diz "masculino" e erra. A
    # palavra manda, esteja onde estiver.
    for _t in ped_cru:
        if _t in GENERO_PALAVRA:
            fam["genero"] = GENERO_PALAVRA[_t]
            break
    if "jogador" in ped_cru and fam.get("versao"):
        fam["versao"] = "jogador"
    # o fornecedor alterna entre romano (ii, iii) e palavra (reserva, away,
    # terceira). Sem as palavras, a "Getafe Away" e a "Getafe Titular" viravam
    # as duas o 1º uniforme, e o rótulo saía "· Away".
    uni_texto = None
    for palavra, uni in (("reserva", "uniforme2"), ("away", "uniforme2"),
                         ("terceira", "uniforme3"), ("third", "uniforme3"),
                         ("titular", "uniforme1"), ("home", "uniforme1")):
        if palavra in ped_cru:
            uni_texto = uni
            break

    variante = next((v for chave, v in VARIANTES if chave in pasta), None)
    retro = "retro" in pasta.split("-")[:4]

    p = pasta[len(prefixo):]
    if p.startswith("retro-"):
        p = p[6:]
    # "copa-2026" (sem "do-mundo") vira ruído puro no _limpar e some com o
    # ano junto — guarda ele aqui pra virar temporada de reserva mais embaixo,
    # sem interferir em "copa-do-mundo-2026" (que já funciona sozinho).
    m_copa = re.search(r"copa-(\d{4})(?!\d)", p)
    p = _limpar(p)
    temporada, p = _temporada(p)
    if temporada is None and m_copa and m_copa.group(1) == "2026":
        temporada = "26-27"
    temporada = CORRECOES_TEMPORADA.get(temporada, temporada)
    p = re.sub(r"(?:^|-)(19\d{2}|20\d{2})(?=-|$)", "", p).strip("-")

    uniforme, ped = "uniforme1", [t for t in p.split("-") if t]
    for i, t in enumerate(ped):
        if t in ROMANO:
            uniforme, ped = ROMANO[t], ped[:i] + ped[i + 1:]
            break
    if uniforme == "uniforme1" and uni_texto:
        uniforme = uni_texto
    # Às vezes ele numera com algarismo em vez de romano: "camisa-vasco-3-26-27"
    # é o 3º uniforme, não o titular. Sem isto a terceira camisa do Vasco, do
    # Inter e do Palmeiras ia pro site como se fosse a titular.
    #
    # O algarismo só vale quando vem LOGO DEPOIS do nome do time. Nas camisas de
    # jogador o número também aparece solto ("italia-ii-2026-di-marco-3"), mas aí
    # ele vem depois do nome do atleta — e essa é a diferença que separa as duas.
    if uniforme == "uniforme1" and ped:
        _t, _sobra = achar_time("-".join(ped), nomes_de_times)
        _primeira = _sobra.split("-")[0] if _sobra else ""
        if _t and _primeira in ("2", "3", "4"):
            uniforme = {"2": "uniforme2", "3": "uniforme3", "4": "uniforme4"}[_primeira]
            _i = ped.index(_primeira)
            ped = ped[:_i] + ped[_i + 1:]
        elif ped[-1] == "2":
            # o caso antigo: "camisa-selecao-brasil-2-2026", em que o time não
            # foi reconhecido pelo caminho de cima
            uniforme, ped = "uniforme2", ped[:-1]

    # guarda o uniforme ANTES de qualquer sobrescrita — é o que faz a chave e
    # o nome de arquivo de retrôs diferentes (mesmo time, anos ou uniformes
    # diferentes) não colidirem mais.
    uniforme_base = uniforme
    # "Camisa Flamengo Feminina - 1981": ano cheio e nenhuma temporada. Nao e
    # erro de digitacao, e peca antiga — retro sem a palavra retro.
    if not retro and temporada is None and re.search(r"(?<!\d)(19\d{2}|20[0-2]\d)(?!\d)", pasta):
        retro = True
    # "…-nike-total-90-retro": a palavra retrô aparece no FIM, não no começo, e
    # não há ano nenhum. Como isto só vale quando não achamos temporada — e sem
    # temporada a peça seria recusada — no pior caso ela entra como "Retrô" sem
    # ano, que é melhor do que sumir do catálogo.
    if not retro and temporada is None and "retro" in pasta.split("-"):
        retro = True
    # "…-sevilla-fc-90-92-retro": 90-92 não é temporada (são dois anos de
    # distância), é o intervalo em que o modelo existiu. Com a palavra retrô no
    # nome, a peça é retrô com esse intervalo — não um erro de digitação.
    if (not retro and temporada and not temporada_valida(temporada)
            and "retro" in pasta.split("-")):
        retro = True
    ano_retro = None
    if retro:
        # tira o dígito de cópia do fim ("...-07-081") antes de procurar o ano,
        # senão "07-08" não casa e a peça é recusada por "retrô sem ano"
        limpo_ano = re.sub(r"(\d{2}-\d{2}|19\d{2}|20\d{2})\d$", r"\1", pasta)
        # mesma armadilha do Hannover 96 e do Schalke 04: em
        # "retro-hannover-96-91-92" o primeiro par é "96-91", que não existe.
        # Fica com o primeiro intervalo de anos SEGUIDOS; se não houver nenhum,
        # com o primeiro que aparecer, como era antes.
        achados = [x.group(1) for x in
                   re.finditer(r"(?=((?<!\d)(?:\d{2}-\d{2}|19\d{2}|20\d{2})(?!\d)))",
                               limpo_ano)]
        bons = [a for a in achados if temporada_valida(a)]
        ano_retro = (bons or achados or [None])[0]
        uniforme, temporada = "retro", "retro"

    rotulo_edicao, aviso_rotulo = None, False
    if variante and retro:
        # Numa retrô o uniforme já é "retro", então goleiro e manga longa não
        # podem virar uniforme — viram rótulo. Sem isso a Alemanha 1990, a
        # Alemanha 1990 manga longa e a Alemanha 1990 goleiro geravam a MESMA
        # peça e duas eram descartadas.
        rotulo_edicao = ROTULO_EDICAO.get(variante)
        if rotulo_edicao is None:
            rotulo_edicao = variante.replace("-", " ").title()
            aviso_rotulo = True
    elif variante:
        if variante == "goleiro":
            uniforme = "goleiro"
        elif variante == "treino":
            uniforme = "treino"
        elif variante == "aquecimento":
            uniforme = "aquecimento"
        elif variante == "pre-jogo":
            # treino e pre-jogo sao pecas diferentes; juntar as duas no mesmo
            # uniforme faz Flamengo treino e Flamengo pre-jogo gerarem a MESMA
            # chave, e a trava para a importacao inteira.
            uniforme = "pre-jogo"
        else:
            rotulo_edicao = ROTULO_EDICAO.get(variante)
            if rotulo_edicao is None:
                rotulo_edicao = variante.replace("-", " ").title()
                aviso_rotulo = True

    slug = "-".join(ped)
    # o apelido so vale se o nome pra onde ele aponta existir MESMO no times.json,
    # e o slug pode vir com marketing colado no fim — achar_time cuida dos dois.
    time, sobra = achar_time(slug, nomes_de_times)

    item = dict(fam, pasta=pasta, time=time, uniforme=uniforme, temporada=temporada,
                variante=variante, ano_retro=ano_retro, uniforme_base=uniforme_base,
                rotulo_edicao=rotulo_edicao, aviso_rotulo=aviso_rotulo,
                slug_fornecedor=slug, sobra=sobra, fora=None)

    if not time:
        item["fora"] = f"time '{slug}' não está no times.json"
    elif retro:
        pass   # retrô sem ano entra como "Retrô" mesmo; a peça é boa demais
               # pra ser jogada fora só porque o fornecedor não datou o anúncio
    elif not temporada_valida(temporada):
        # Peça sem NENHUM ano no nome — nem temporada, nem ano de retrô. É a
        # linha casual e as camisas de estilo, que o fornecedor anuncia sem
        # data. Como não há ano nenhum, não pode ser retrô: entra na temporada
        # atual e o relatório avisa, em vez de sumir do catálogo.
        sem_ano = not re.search(r"(?<!\d)(\d{2}-\d{2}|19\d{2}|20[0-2]\d)(?!\d)", pasta)
        if temporada is None and sem_ano:
            item["temporada"] = TEMPORADA_ATUAL
            item["aviso_temporada"] = True
        else:
            item["fora"] = f"temporada '{temporada}' não reconhecida"
    return item


def chave_do_produto(item, ROTULO=ROTULO_UNIFORME):
    """A chave exata que o dados.js usa. Tem que bater, caractere por caractere,
    com a que o catalogo.html gera em JavaScript.

    A variante, o ano da retro e o uniforme-base da retro entram na chave de
    proposito: sem eles, o kit normal do Barcelona e o Barcelona x Travis
    Scott — mesmo time, mesmo uniforme, mesma temporada — geram a MESMA
    chave, e a segunda importacao apaga as fotos da primeira sem avisar.
    Mesma logica pras retros: Real Madrid 11-12, 17-18 e 17-18 II sao tres
    pecas diferentes e precisam de tres chaves diferentes."""
    g = {"masculino": "Masculino", "feminino": "Feminino", "infantil": "Infantil"}[item["genero"]]
    nome = item["time"]
    if item["categoria"] == "jaqueta":
        quando = item.get("ano_retro") or item.get("temporada") or ""
        quando = f" {quando.replace('-', '/')}" if quando and quando != "retro" else ""
        ed = f" - {item['rotulo_edicao']}" if item.get("rotulo_edicao") else ""
        return f"{nome} - {g} - Jaqueta{quando}{ed}"
    if item["uniforme"] == "retro":
        ano = f" {item['ano_retro']}" if item.get("ano_retro") else ""
        base = item.get("uniforme_base")
        extra = f" - {ROTULO[base]}" if base and base != "uniforme1" else ""
        ed = f" - {item['rotulo_edicao']}" if item.get("rotulo_edicao") else ""
        # o tipo da peça entra ANTES do "Retrô": sem isso o calção retrô do
        # Milan 06/07 e a camisa retrô do Milan 06/07 viram a mesma coisa
        tipo = {"calcao": "Calção ", "jaqueta": "Jaqueta ", "regata": "Regata ",
                "cropped": "Cropped ", "polo": "Polo ", "calca": "Calça ",
                "meiao": "Meião ", "luva": "Luva ", "kit": ""}.get(item["categoria"], "")
        return f"{nome} - {g} - {tipo}Retrô{ano}{extra}{ed}"
    temp = item["temporada"].replace("-", "/")
    uni = ROTULO[item["uniforme"]]
    edicao = f" - {item['rotulo_edicao']}" if item.get("rotulo_edicao") else ""
    if item["genero"] == "infantil":
        return f"{nome} - {g} - {temp} - {uni} Kit Infantil{edicao}"
    if item["categoria"] == "regata":
        quando = item.get("ano_retro") or item.get("temporada") or ""
        quando = f" {quando.replace('-', '/')}" if quando and quando != "retro" else ""
        # a regata de treino e a regata do 2º uniforme são duas peças: sem o
        # uniforme na chave elas colidiam e a importação parava
        extra = f" - {uni}" if item["uniforme"] != "uniforme1" else ""
        return f"{nome} - {g} - Regata{quando}{extra}{edicao}"
    if item["categoria"] == "cropped":
        return f"{nome} - {g} - {temp} - Cropped{edicao}"
    if item["categoria"] == "calcao":
        return f"{nome} - {g} - {temp} - Calção {uni}{edicao}"
    # a polo não tem 1º/2º uniforme nem versão: sem um ramo só dela, ela caía no
    # ramo genérico lá embaixo e gerava a MESMA chave da camisa titular
    if item["categoria"] == "polo":
        extra = f" - {uni}" if item["uniforme"] != "uniforme1" else ""
        return f"{nome} - {g} - {temp} - Polo{extra}{edicao}"
    # peças que não são camisa nem uniforme: precisam do próprio ramo, senão
    # caem no genérico lá embaixo e geram a MESMA chave da camisa titular
    if item["categoria"] in ("calca", "meiao", "luva"):
        tipo = {"calca": "Calça", "meiao": "Meião", "luva": "Luva"}[item["categoria"]]
        extra = f" - {uni}" if item["uniforme"] != "uniforme1" else ""
        return f"{nome} - {g} - {temp} - {tipo}{extra}{edicao}"
    # o conjunto adulto tem que dizer que é conjunto: sem isso ele gerava a
    # MESMA chave da camisa titular do mesmo time e da mesma temporada
    if item["categoria"] == "kit":
        return f"{nome} - {g} - {temp} - {uni} Conjunto{edicao}"
    versao = "Versão Jogador" if item["versao"] == "jogador" else "Versão Torcedor"
    return f"{nome} - {g} - {temp} - {uni} {versao}{edicao}"


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


# Preço de cada peça, em reais. Uma tabela só — pra mudar preço, mexe aqui,
# não em três lugares. A ordem de precedência mora em preco_do_produto: a
# primeira regra que casar é a que vale.
PRECOS = {
    "edicao_especial": 319,   # qualquer variante do ROTULO_EDICAO
    "kit_infantil":    279,   # camisa + calção, infantil
    "kit_adulto":      279,   # camisa + calção, masculino/feminino
    "retro":           275,
    "jogador":         250,   # versão jogador
    "torcedor":        219,   # versão torcedor
}


def preco_do_produto(item):
    """Goleiro, treino, pré-jogo e 4º uniforme NÃO são "edição especial" pra
    efeito de preço — pagam o preço normal do tipo de peça que são, por isso
    vêm depois na precedência (rotulo_edicao só existe pras edições de
    verdade, não pra goleiro/treino)."""
    if item.get("rotulo_edicao"):
        return PRECOS["edicao_especial"]
    if item["categoria"] == "kit":
        return PRECOS["kit_infantil"] if item["genero"] == "infantil" else PRECOS["kit_adulto"]
    if item["uniforme"] == "retro":
        return PRECOS["retro"]
    if item["versao"] == "jogador":
        return PRECOS["jogador"]
    return PRECOS["torcedor"]
