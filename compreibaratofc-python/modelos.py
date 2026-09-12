# -*- coding: utf-8 -*-
"""Prepara as fotos de referência e os prompts para gerar os modelos na IA,
e depois padroniza o que a IA devolveu.

COMO SE USA (dois comandos, um antes e um depois da IA)

    python modelos.py preparar
        Escolhe as peças, copia a foto de cada uma pra pasta `gerar/` e
        escreve, do lado de cada foto, o prompt pronto pra colar. Também
        escreve `gerar/LISTA.txt`, que é a sua lista de tarefas.

    python modelos.py padronizar
        Depois que você gerar as imagens e salvar em `gerados/`, este
        comando corta, redimensiona, converte pra webp, renomeia com o
        nome que o site espera e joga em `web/modelos/`.

POR QUE ESTE ARQUIVO EXISTE
A parte cara de gerar imagem não é a IA — é decidir QUAL camisa, achar a
foto dela no meio de 11 mil arquivos, montar o prompt e depois renomear
tudo na mão. Isso é o que este arquivo faz.

O QUE ELE NÃO FAZ
Ele não gera imagem. Você gera na sua IA, salva em `gerados/` mantendo o
número do começo do nome, e roda `padronizar`.

UMA DECISÃO IMPORTANTE, PRA VOCÊ SABER QUE FOI DE PROPÓSITO
A foto de modelo NUNCA substitui a foto real da peça no cartão. Modelo
gerado por IA é um desenho da camisa: o escudo escorrega, o patrocínio
vira rabisco. O site inteiro promete "a foto é a peça que existe" — se
o cartão passar a mostrar um desenho, a promessa cai.
Então o modelo entra em dois lugares só:
    - no banner do topo, onde vende o clima e ninguém confere costura
    - como foto EXTRA na ficha, depois da foto real
"""

import io
import json
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CATALOGO = os.path.join(AQUI, "site", "catalogo.json")
GERAR = os.path.join(AQUI, "gerar")
GERADOS = os.path.join(AQUI, "gerados")
ELENCO = os.path.join(AQUI, "elenco")
SAIDA = os.path.join(AQUI, "web", "modelos")

try:
    from PIL import Image
except ImportError:
    Image = None

sys.path.insert(0, AQUI)
from scripts import cobica                                    # noqa: E402


# =====================================================================
# OS PERFIS — a sua biblioteca de modelos
# =====================================================================
# Estão aqui em cima porque é o que você vai querer mexer. Trocar,
# acrescentar ou tirar um perfil daqui muda os prompts de todas as
# próximas gerações, sem mexer em mais nada.
#
# O rodízio é automático: o perfil 1 vai na primeira peça, o 2 na
# segunda, e assim por diante. Assim a vitrine não fica com oito fotos
# do mesmo rosto.

HOMENS = [
    "Homem jovem adulto, aproximadamente 25 anos, pele clara, cabelo castanho "
    "escuro curto e bem penteado, aparência brasileira, corpo atlético porém "
    "natural, barba muito curta, expressão confiante e natural",

    "Homem jovem adulto, aproximadamente 23 anos, pele clara, cabelo loiro "
    "escuro curto, olhos claros, corpo atlético natural, rosto jovem, sem barba",

    "Homem jovem adulto negro, aproximadamente 25 anos, pele negra, cabelo "
    "afro curto bem cuidado, corpo atlético natural, aparência brasileira, "
    "rosto marcante e simpático",

    "Homem jovem adulto de aparência asiática, aproximadamente 24 anos, cabelo "
    "preto curto e moderno, pele clara, corpo atlético natural, aparência "
    "elegante",

    "Homem jovem adulto brasileiro, aproximadamente 27 anos, pele morena, "
    "cabelo preto curto, barba curta bem aparada, corpo atlético natural, "
    "aparência simpática",

    "Homem jovem adulto negro, aproximadamente 28 anos, pele negra, cabelo "
    "raspado, barba curta, físico atlético natural, postura confiante",

    "Homem jovem adulto, aproximadamente 21 anos, pele clara, cabelo castanho "
    "médio levemente ondulado, sem barba, corpo magro e atlético, aparência "
    "jovem brasileira",

    "Homem adulto, aproximadamente 35 anos, pele morena clara, cabelo castanho "
    "escuro curto, barba bem aparada, corpo atlético natural, aparência "
    "sofisticada",
]

MULHERES = [
    "Mulher jovem adulta, aproximadamente 24 anos, pele morena clara, cabelo "
    "castanho escuro longo preso em rabo de cavalo, corpo atlético natural, "
    "aparência brasileira, expressão confiante",

    "Mulher jovem adulta, aproximadamente 25 anos, pele clara, cabelo loiro "
    "preso, olhos claros, corpo atlético natural, aparência esportiva",

    "Mulher jovem adulta negra, aproximadamente 25 anos, pele negra, cabelo "
    "afro natural bem cuidado, corpo atlético, aparência brasileira, expressão "
    "confiante",

    "Mulher jovem adulta de aparência asiática, aproximadamente 23 anos, cabelo "
    "preto longo, corpo atlético natural, aparência moderna e esportiva",

    "Mulher jovem adulta, aproximadamente 27 anos, pele clara, cabelo castanho "
    "curto, corpo atlético natural, aparência moderna e esportiva",

    "Mulher jovem adulta negra, aproximadamente 26 anos, pele negra, tranças "
    "longas, corpo atlético natural, aparência brasileira, expressão confiante",

    "Mulher jovem adulta brasileira, pele morena, cabelo castanho longo, corpo "
    "atlético natural, aparência saudável e esportiva",

    "Mulher jovem adulta, aproximadamente 24 anos, pele clara, cabelo ruivo "
    "natural, corpo atlético, expressão confiante",
]

MENINOS = [
    "Menino de aproximadamente 8 anos, pele clara, cabelo castanho curto, "
    "aparência brasileira, expressão alegre e natural",
    "Menino negro de aproximadamente 9 anos, cabelo afro curto, expressão "
    "alegre, aparência brasileira",
    "Menino de aproximadamente 7 anos, pele morena, cabelo preto curto, "
    "aparência brasileira, expressão alegre",
    "Menino de aproximadamente 10 anos, aparência asiática, cabelo preto curto, "
    "expressão alegre",
    "Menino de aproximadamente 8 anos, pele clara, cabelo loiro curto, "
    "aparência europeia",
    "Menino negro de aproximadamente 10 anos, cabelo afro curto, aparência "
    "brasileira, expressão alegre",
    "Menino de aproximadamente 6 anos, pele clara, cabelo castanho, aparência "
    "infantil natural",
    "Menino de aproximadamente 11 anos, pele morena, cabelo castanho escuro, "
    "aparência brasileira",
]

MENINAS = [
    "Menina de aproximadamente 8 anos, pele clara, cabelo castanho longo preso "
    "em rabo de cavalo, expressão alegre e natural",
    "Menina negra de aproximadamente 9 anos, cabelo afro natural, expressão "
    "alegre",
    "Menina de aproximadamente 7 anos, pele morena, cabelo preto preso, "
    "expressão alegre",
    "Menina de aproximadamente 10 anos, aparência asiática, cabelo preto longo",
    "Menina de aproximadamente 8 anos, pele clara, cabelo loiro",
    "Menina negra de aproximadamente 7 anos, cabelo afro natural",
    "Menina de aproximadamente 10 anos, pele clara, cabelo castanho",
    "Menina de aproximadamente 9 anos, pele morena, cabelo castanho escuro",
]


# =====================================================================
# O ELENCO — 32 pessoas fixas, geradas uma vez e usadas pra sempre
# =====================================================================
# POR QUE ISSO EXISTE
# Descrever a pessoa por texto em cada geração dá 55 rostos diferentes. O
# site fica parecendo banco de imagem: cada cartão uma pessoa nova, nenhuma
# cara que se repete. Marca de verdade tem elenco — as mesmas pessoas
# aparecem em campanhas diferentes, e é isso que faz o site parecer uma
# loja e não uma colagem.
#
# Como o Gemini aceita DUAS imagens de referência ao mesmo tempo, dá pra
# fazer do jeito certo:
#     ETAPA A  gera cada pessoa UMA vez, sozinha, de camiseta lisa
#     ETAPA B  para cada camisa: "esta pessoa (imagem 1) vestindo esta
#              camisa (imagem 2)"
#
# 32 gerações na etapa A, e depois cada camisa custa uma geração só. E o
# elenco não vence: camisa nova daqui a seis meses usa as mesmas pessoas.
# os crachás: H1..H8 homens, M1..M8 mulheres, B1..B8 meninos, G1..G8 meninas
ELENCOS = {"H": HOMENS, "M": MULHERES, "B": MENINOS, "G": MENINAS}


def _id_de(lista, i):
    """H3, M1, B5... o crachá de cada pessoa do elenco.

    Se a pasta elenco/ já tiver gente, o rodízio anda SÓ entre quem existe.
    Sem isso, gerar 4 homens não bastava: o rodízio pedia H5 e H6 para os
    dois últimos banners e você teria que gerar seis. Assim os oito banners
    cabem em quem você já tem — H1, H2, H3, H4, H1, H2... — e repetir rosto
    entre campanhas é justamente o que marca de verdade faz."""
    for prefixo, l in ELENCOS.items():
        if l is lista:
            tem = _disponiveis(prefixo)
            if tem:
                return tem[i % len(tem)]
            return "%s%d" % (prefixo, i % len(l) + 1)
    return ""


_CACHE_ELENCO = {}


def _disponiveis(prefixo):
    """Os crachás desse tipo que já estão gerados, em ordem."""
    if prefixo not in _CACHE_ELENCO:
        tem = [c for c in _elenco_existente() if c[:1] == prefixo]
        _CACHE_ELENCO[prefixo] = sorted(tem, key=lambda c: int(c[1:] or 0))
    return _CACHE_ELENCO[prefixo]


# A pessoa sozinha, de camiseta lisa. Camiseta lisa é de propósito: com
# estampa, a IA da etapa B mistura o desenho antigo com a camisa nova.
PROMPT_ELENCO = (
    "IMAGEM VERTICAL 3:4. Retrato de corpo inteiro de uma pessoa fictícia. "
    "{perfil}. "
    "Vestindo camiseta lisa cinza claro, sem nenhuma estampa, escrita ou "
    "logo; {baixo}. "
    "Em pé, de frente para a câmera, braços relaxados ao lado do corpo, "
    "postura natural, expressão simpática e tranquila, olhando para a "
    "câmera. Corpo inteiro visível, da cabeça aos pés, com uma folga acima "
    "da cabeça e abaixo dos pés. "
    "Fundo cinza claro liso e uniforme, sem objetos, sem cenário, sem "
    "sombra dura, sem equipamento de estúdio visível. Luz de estúdio suave "
    "e uniforme vindo da frente. "
    "Fotografia hiper-realista de catálogo, alta resolução, nitidez total "
    "no rosto e na roupa. "
    "Rosto original, genérico e anônimo — não deve se parecer com nenhuma "
    "pessoa famosa, atleta ou celebridade."
)

NEGATIVO_ELENCO = (
    "estampa na camiseta, logo, escrita, texto, marca d'água, moldura, "
    "borda, colagem, mãos deformadas, dedos extras, rosto deformado, "
    "olhos tortos, membros extras, corpo cortado, cabeça cortada, pés "
    "cortados, fundo poluído, objetos, cenário, sombra dura, equipamento "
    "de estúdio, softbox, tripé, celebridade, rosto de pessoa famosa, "
    "baixa resolução, desfoque, pose sensual, roupa justa demais"
)

# A etapa B: a mesma pessoa, agora com a nossa camisa.
# O cabeçalho se ajusta ao número de imagens porque o banner de família usa
# três pessoas e três camisas — dizer "duas imagens" ali confunde a IA.
def vestir(n_pessoas, n_pecas):
    linhas = ["Você recebeu %d imagens." % (n_pessoas + n_pecas)]
    i = 1
    for k in range(n_pessoas):
        linhas.append("IMAGEM %d = pessoa %d." % (i, k + 1)
                      if n_pessoas > 1 else "IMAGEM %d = a pessoa." % i)
        i += 1
    for k in range(n_pecas):
        linhas.append("IMAGEM %d = peça de roupa %d." % (i, k + 1)
                      if n_pecas > 1 else "IMAGEM %d = a peça de roupa." % i)
        i += 1
    if n_pessoas == 1:
        corpo = ("Gere uma nova fotografia da MESMA PESSOA da imagem 1 — "
                 "mesmo rosto, mesmo tom de pele, mesmo cabelo, mesma idade, "
                 "mesma altura e mesmo tipo físico — vestindo exatamente a "
                 "peça da imagem seguinte. A pessoa tem que ser reconhecível "
                 "como a mesma da imagem 1.")
    else:
        corpo = ("Gere uma nova fotografia com AS MESMAS %d PESSOAS das "
                 "primeiras imagens — mesmos rostos, mesmos tons de pele, "
                 "mesmos cabelos, mesmas idades e mesmos tipos físicos — cada "
                 "uma vestindo exatamente uma das peças das imagens "
                 "seguintes. As pessoas têm que ser reconhecíveis como as "
                 "mesmas das imagens de referência." % n_pessoas)
    return "\n".join(linhas) + "\n\n" + corpo + "\n\n"


# =====================================================================
# OS PEDAÇOS FIXOS DO PROMPT
# =====================================================================
# A frase que protege a camisa. Ela se repete em todos os prompts porque
# é a única coisa que separa "modelo vestindo a nossa camisa" de "modelo
# vestindo uma camisa que a IA inventou parecida com a nossa".
FIDELIDADE = (
    "Vestindo exatamente a camisa esportiva fornecida como imagem de "
    "referência. A camisa deve ser reproduzida com fidelidade absoluta, "
    "preservando exatamente suas cores, escudo, patrocinadores, logos, "
    "padrões, gola, mangas, costuras, textura, tecido e proporções. "
    "Não criar novos elementos na camisa e não modificar nenhum detalhe."
)

# Duas travas que só apareceram quando as primeiras imagens ficaram
# prontas — e as duas são sérias.
#
# ROSTO: a IA puxa rosto de jogador conhecido quando você pede "modelo
# vestindo camisa do Arsenal no Emirates". Uma das imagens de teste saiu
# com dois rostos reconhecíveis de atletas reais. Isso não pode ir pro
# site: usar a cara de uma pessoa real pra vender produto sem autorização
# dela é problema, e não é problema pequeno.
#
# TEXTO NO CENÁRIO: a IA escreve. Na mesma imagem o letreiro do estádio
# saiu "EMIRAOR" e apareceu um "BLISTEAM" inventado na barra da camisa.
# Texto errado no fundo faz o site inteiro parecer falsificado.
SEM_ROSTO_CONHECIDO = (
    "Rosto de modelo anônimo, genérico e original. O rosto NÃO deve se "
    "parecer com nenhum jogador de futebol real, atleta profissional ou "
    "pessoa pública conhecida."
)

SEM_TEXTO_NO_FUNDO = (
    "Nenhum texto legível no cenário: sem letreiros, sem placas, sem nome "
    "de estádio escrito, sem tipografia ao fundo, sem faixas com palavras."
)

CARD = (
    "IMAGEM QUADRADA 1:1. Fotografia profissional de e-commerce esportivo. "
    "{perfil}. " + SEM_ROSTO_CONHECIDO + " " + FIDELIDADE +
    " Modelo em pé, postura natural, enquadramento do joelho para cima, camisa "
    "ocupando a maior parte da imagem. Fundo branco puro e uniforme, sem "
    "objetos, sem cenário, sem elementos decorativos. Sem nenhum equipamento "
    "de estúdio visível: sem softbox, sem tripé, sem mesa, sem rolo de fundo, "
    "sem câmera. Iluminação de estúdio profissional, sombras extremamente "
    "suaves, fotografia frontal de catálogo, estética premium de loja "
    "esportiva, produto perfeitamente nítido, hiper-realista, alta resolução."
)

TORCEDORA = (
    "IMAGEM QUADRADA 1:1. Fotografia comercial hiper-realista. {perfil}. "
    + SEM_ROSTO_CONHECIDO + " " + FIDELIDADE +
    " Estilo torcedora casual e elegante, jeans básico, tênis branco, postura "
    "natural e descontraída. Iluminação profissional, ambiente clean, "
    "composição moderna, camisa claramente como elemento principal da imagem, "
    "sem acessórios que escondam o produto. " + SEM_TEXTO_NO_FUNDO
)

KIT = (
    "IMAGEM QUADRADA 1:1. Fotografia profissional de catálogo infantil "
    "esportivo. {perfil}, "
    "usando exatamente o uniforme infantil fornecido como referência. "
    "Manter fielmente todas as características da camisa e do calção: cores, "
    "escudo, logos, patrocinadores e detalhes. Fundo branco, iluminação de "
    "estúdio, corpo inteiro, postura natural e alegre, produto claramente "
    "visível, sem nenhum equipamento de estúdio visível, hiper-realista."
)

JAQUETA = (
    "IMAGEM QUADRADA 1:1. Fotografia profissional de moda esportiva. "
    "{perfil}, usando exatamente a "
    "jaqueta esportiva fornecida como imagem de referência. Preservar "
    "integralmente o design original: cores, zíper, logos, escudos, detalhes, "
    "tecido e modelagem. Postura casual, calça jeans escura e tênis branco. "
    "Ambiente moderno e minimalista, iluminação natural suave, jaqueta como "
    "principal elemento visual, corpo inteiro, hiper-realismo, alta resolução. "
    + SEM_ROSTO_CONHECIDO + " " + SEM_TEXTO_NO_FUNDO
)

CONJUNTO = (
    "IMAGEM QUADRADA 1:1. Fotografia de catálogo esportivo premium. "
    "{perfil}, usando exatamente o "
    "conjunto esportivo fornecido como imagem de referência. Preservar "
    "integralmente camisa, calção, cores, escudos, logos, patrocinadores, "
    "padrões, tecidos e proporções. Modelo em pé, corpo inteiro, postura "
    "natural e esportiva, tênis branco neutro. Fundo branco ou cinza muito "
    "claro, iluminação profissional de estúdio, foco principal no conjunto, "
    "sem equipamento de estúdio visível, hiper-realista, alta resolução. "
    + SEM_ROSTO_CONHECIDO
)

# O negativo. Acrescentei quatro coisas à sua lista, e todas por um
# motivo específico:
#   marca d'água        a IA copia marca d'água de banco de imagem
#   texto em português  ela inventa "CAMISA OFICIAL" na barra do banner
#   selo, etiqueta      ela cola "100% ORIGINAL" no peito da camisa
#   número inventado    ela põe um 10 nas costas de camisa sem número
NEGATIVO = (
    "camisa deformada, logos incorretos, escudo alterado, patrocinador "
    "ilegível, texto inventado, letras erradas, número inventado nas costas, "
    "cores diferentes, camisa amassada excessivamente, mãos deformadas, dedos "
    "extras, braços deformados, anatomia incorreta, rosto deformado, baixa "
    "resolução, fundo poluído, objetos, estádio, torcida, acessórios cobrindo "
    "a camisa, alterações no design original, marca d'água, selo, etiqueta "
    "sobreposta, moldura, borda, colagem, texto sobreposto, "
    # as quatro últimas nasceram das primeiras imagens de teste
    "jogador de futebol famoso, celebridade, rosto de pessoa real conhecida, "
    "sósia de atleta, letreiro, placa com texto, nome de estádio escrito, "
    "tipografia inventada no fundo, letras deformadas no peito da camisa, "
    "texto ilegível na camisa, equipamento de estúdio, softbox, tripé"
)

NEGATIVO_BANNER = NEGATIVO.replace("fundo poluído, objetos, estádio, torcida, ", "")


# =====================================================================
# OS BANNERS
# =====================================================================
# Cada banner é uma cena SUA + uma regra que escolhe a peça no acervo.
# A regra existe pra isto não envelhecer: quando o acervo mudar, o
# banner continua pegando a peça certa sozinho.
#
# `filtro` recebe uma peça e devolve True/False.
# `elenco` diz de que lista de perfis vem o modelo.
BANNERS = [
    dict(
        nome="01-estadio",
        lado="esquerda",
        elenco="homem",
        filtro=lambda p: p.get("destaque") and p.get("uniforme") == "retro"
                         and p.get("categoria") == "camisa",
        cena="Modelo em um estádio de futebol moderno, arquibancadas "
             "desfocadas ao fundo, iluminação dramática de fim de tarde, "
             "atmosfera profissional de futebol, postura confiante. "
             "Modelo posicionado no lado direito da imagem, espaço livre no "
             "lado esquerdo para texto e botão do site.",
        porque="A cara da casa. A peça mais rara do acervo, no lugar mais "
               "nobre da página.",
    ),
    dict(
        nome="02-rua",
        lado="direita",
        elenco="homem",
        filtro=lambda p: p.get("temporada") == "26-27" and _cor(p)
                         and _camisa_de_vitrine(p),
        cena="Modelo caminhando em uma área urbana moderna, arquitetura "
             "contemporânea, iluminação natural, estilo casual esportivo. "
             "Modelo no lado esquerdo, espaço livre no lado direito para texto.",
        porque="A temporada atual numa cor forte — é o que para o dedo de "
               "quem não é colecionador.",
    ),
    dict(
        nome="03-torcida",
        lado="esquerda",
        elenco="homem",
        filtro=lambda p: p["time"] == "Brasil" and p.get("temporada") == "26-27"
                         and _camisa_de_vitrine(p),
        cena="Grupo pequeno de torcedores jovens de etnias diferentes "
             "comemorando juntos em ambiente de futebol, energia positiva, "
             "estádio desfocado ao fundo. Grupo à direita do quadro, metade "
             "esquerda da imagem livre e desimpedida para texto. "
             "Todos usando a mesma camisa da referência.",
        porque="Copa 2026. A seleção é a porta de entrada mais larga que "
               "existe no Brasil.",
    ),
    dict(
        nome="04-mulher",
        lado="direita",
        elenco="mulher",
        filtro=lambda p: p.get("genero") == "feminino"
                         and p.get("temporada") == "26-27"
                         and _camisa_de_vitrine(p),
        cena="Modelo em ambiente urbano moderno relacionado ao futebol, "
             "aparência elegante e esportiva, iluminação cinematográfica. "
             "Espaço negativo à direita para texto.",
        porque="125 peças femininas no acervo e nenhuma aparecendo. Este "
               "banner sozinho abre esse público.",
    ),
    dict(
        nome="05-crianca",
        lado="esquerda",
        elenco="menino",
        filtro=lambda p: p.get("genero") == "infantil"
                         and p.get("temporada") == "26-27"
                         and p.get("uniforme") in ("uniforme1", "uniforme2"),
        cena="Modelo em um pequeno campo de futebol, ambiente ensolarado, "
             "expressão alegre, clima familiar e esportivo, uniforme "
             "completamente visível. Espaço livre à esquerda para texto.",
        porque="O kit infantil é o maior valor por pedido: quem compra pro "
               "filho leva a dele junto.",
    ),
    dict(
        nome="06-familia",
        lado="direita",
        elenco="familia",
        filtro=lambda p: p["time"] == "Flamengo" and p.get("temporada") == "26-27"
                         and p.get("uniforme") == "uniforme1"
                         and _camisa_de_vitrine(p),
        cena="Família brasileira — pai jovem adulto, mãe jovem adulta e uma "
             "criança — todos usando a camisa da referência, sorrindo "
             "naturalmente, estádio moderno desfocado ao fundo, sensação de "
             "união e paixão pelo futebol, iluminação cinematográfica suave. "
             "Espaço livre à direita para texto promocional.",
        porque="É o roteiro 11 do arquivo de legendas virado em imagem: "
               "masculina, feminina e kit no mesmo pedido.",
    ),
    dict(
        nome="07-colecao",
        lado="esquerda",
        elenco="trio",
        filtro=lambda p: p.get("uniforme") == "retro"
                         and p.get("categoria") == "camisa",
        cena="Três modelos — um homem, uma mulher e uma criança, de etnias "
             "diferentes — usando as camisas das referências, composição "
             "sofisticada de campanha de coleção esportiva, ambiente moderno, "
             "iluminação cinematográfica. Os três à direita do quadro, metade "
             "esquerda livre e desimpedida para texto. Estética de grande "
             "marca esportiva.",
        porque="Diz numa imagem só que o acervo serve pra casa inteira.",
    ),
    dict(
        nome="08-premium",
        lado="direita",
        elenco="homem",
        filtro=lambda p: p.get("uniforme") == "retro"
                         and p.get("categoria") == "camisa",
        cena="Fotografia editorial premium de moda esportiva, ambiente "
             "arquitetônico moderno, iluminação sofisticada, fundo levemente "
             "desfocado, modelo em posição natural, camisa como protagonista "
             "absoluta da imagem. Modelo à esquerda do quadro, metade direita "
             "livre e desimpedida para texto.",
        porque="O banner que faz o site parecer caro. Peça rara, cenário "
               "sóbrio, nada de estádio.",
    ),
]

# O 16:9 vai na PRIMEIRA linha de propósito. Nas primeiras oito imagens de
# teste, "proporção 16:9" estava no fim do prompt e as quatro voltaram
# quadradas — a IA lê o começo com mais peso. Cortar um quadrado pra 16:9
# depois corta cabeça ou pé.
CENA_BANNER = (
    "IMAGEM HORIZONTAL 16:9, formato 1920x1080 (paisagem, bem mais larga que "
    "alta). Fotografia publicitária esportiva premium. {perfil}. "
    + SEM_ROSTO_CONHECIDO + " " + FIDELIDADE + " {cena} "
    + SEM_TEXTO_NO_FUNDO +
    " Hiper-realismo, alta resolução, proporção 16:9 horizontal."
)


# =====================================================================
# ESCOLHER AS PEÇAS
# =====================================================================
_CORES = re.compile(r"\b(rosa|verde|preta|branca|azul|dourad\w+)\b", re.I)


def _cor(p):
    return bool(_CORES.search(p.get("chave") or ""))


def _abre_vitrine(p):
    """Peça que serve de referência pra IA. Calção e meião não servem:
    não há corpo pra vestir e a foto vira um retângulo."""
    return p.get("categoria") in ("camisa", "kit", "jaqueta", "regata", "polo")


# Uniformes que NÃO servem de vitrine. Goleiro, treino e pré-jogo são
# peças legítimas, mas ninguém abre um banner com a camisa do goleiro
# reserva — e foi exatamente isso que a primeira versão desta escolha
# fez: pôs "Argentina Goleiro Preto" como a peça número 1 da temporada.
_UNIFORME_FRACO = ("goleiro", "treino", "pre-jogo", "aquecimento")


def _camisa_de_vitrine(p):
    """A camisa que representa o time: 1º, 2º ou 3º uniforme, manga curta.
    Manga longa fica de fora porque na foto de modelo ela esconde o braço
    e some com metade da diferença entre torcedor e jogador."""
    if p.get("categoria") != "camisa":
        return False
    if p.get("uniforme") in _UNIFORME_FRACO:
        return False
    if "manga longa" in (p.get("chave") or "").lower():
        return False
    return True


def carregar():
    with io.open(CATALOGO, encoding="utf-8") as f:
        pecas = json.load(f)
    for p in pecas:
        p["_pontos"] = cobica.pontos(p)
    return pecas


# As peças já escolhidas em qualquer fase. Sem isto, a Manchester United
# 07/08 (que é a de maior pontuação do acervo) aparecia em três banners
# diferentes e o plano inteiro virava a mesma camisa.
_USADAS = set()


def _melhores(pecas, filtro, quantos, um_por_time=True, reservar=True):
    escolhidas, times = [], set()
    for p in sorted(pecas, key=lambda x: -x["_pontos"]):
        if p["chave"] in _USADAS:
            continue
        if not _abre_vitrine(p) or not filtro(p):
            continue
        if um_por_time and p["time"] in times:
            continue
        times.add(p["time"])
        escolhidas.append(p)
        if len(escolhidas) >= quantos:
            break
    if reservar:
        for p in escolhidas:
            _USADAS.add(p["chave"])
    return escolhidas


def _slug(texto):
    import unicodedata
    t = unicodedata.normalize("NFD", texto)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return re.sub(r"-+", "-", t).strip("-")[:60]


# As fases. Cada uma é uma pasta dentro de `gerar/`.
def fases(pecas):
    _USADAS.clear()
    return [
        dict(
            pasta="01-banners",
            titulo="BANNERS DO TOPO",
            porque="Oito imagens que mudam a primeira tela do site inteiro. "
                   "É o maior retorno por imagem gerada — comece por aqui.",
            itens=_banners(pecas),
        ),
        dict(
            pasta="02-temporada",
            titulo="TEMPORADA 26/27 — AS QUE ESTÃO EM ALTA",
            porque="É onde o modelo importa: quem compra camisa da temporada "
                   "quer saber como fica no corpo. Quem compra retrô já sabe "
                   "o que quer.",
            itens=_cartoes(
                _melhores(pecas, lambda p: p.get("temporada") == "26-27"
                          and p.get("genero") == "masculino"
                          and _camisa_de_vitrine(p), 16),
                CARD, HOMENS),
        ),
        dict(
            pasta="03-feminina",
            titulo="MODELAGEM FEMININA",
            porque="125 peças no acervo. Sem foto no corpo, a modelagem "
                   "feminina é invisível — a pessoa não sabe que existe.",
            itens=_cartoes(
                _melhores(pecas, lambda p: p.get("genero") == "feminino"
                          and _camisa_de_vitrine(p), 12),
                TORCEDORA, MULHERES),
        ),
        dict(
            pasta="04-infantil",
            titulo="KIT INFANTIL",
            porque="Maior valor por pedido do acervo. E a foto no corpo "
                   "responde a dúvida do tamanho antes de virar mensagem.",
            itens=_cartoes(
                _melhores(pecas, lambda p: p.get("genero") == "infantil"
                          and p.get("uniforme") not in _UNIFORME_FRACO, 10),
                KIT, MENINOS, MENINAS),
        ),
        dict(
            pasta="05-jaquetas-conjuntos",
            titulo="JAQUETAS E CONJUNTOS",
            porque="São as peças de maior preço (R$359 e R$390) e as que "
                   "menos se entendem numa foto de cabide.",
            itens=_cartoes(
                _melhores(pecas, lambda p: p.get("categoria") == "jaqueta", 5)
                + _melhores(pecas, lambda p: p.get("categoria") == "kit"
                            and p.get("genero") != "infantil", 4),
                None, HOMENS),
        ),
    ]


def _proximo(contador, chave):
    """Devolve 0, depois 1, depois 2... para cada tipo de elenco."""
    contador[chave] = contador.get(chave, -1) + 1
    return contador[chave]


def _banners(pecas):
    itens = []
    contador = {}
    for i, b in enumerate(BANNERS):
        quantas = 3 if b["elenco"] in ("trio", "familia") else 1
        achadas = _melhores(pecas, b["filtro"], quantas)
        if not achadas:
            continue
        p = achadas[0]
        elenco = {"homem": HOMENS, "mulher": MULHERES,
                  "menino": MENINOS, "familia": HOMENS, "trio": HOMENS}[b["elenco"]]
        perfil = elenco[i % len(elenco)]
        if b["elenco"] == "familia":
            perfil = ("Família brasileira: " + HOMENS[i % 8].lower() + "; "
                      + MULHERES[i % 8].lower() + "; "
                      + MENINOS[i % 8].lower())
        if b["elenco"] == "trio":
            perfil = ("Três modelos: " + HOMENS[(i + 2) % 8].lower() + "; "
                      + MULHERES[(i + 5) % 8].lower() + "; "
                      + MENINAS[(i + 1) % 8].lower())
        # Cada tipo tem o próprio contador, começando do 1. Antes o número
        # vinha da posição do banner na lista: o banner 5 (criança) pedia o
        # B5, o 6 pedia o B6 e o 7 pedia a G8 — três crianças espalhadas no
        # meio de dezesseis. Assim os oito banners cabem em B1, B2 e G1, e
        # você gera duas crianças em vez de vasculhar a lista inteira.
        #
        # É if/elif e não um dicionário de propósito: num dicionário o
        # Python calcula TODOS os valores antes de escolher um, e cada
        # cálculo gastava um número do contador. Dava H1, H4, H7 em vez de
        # H1, H2, H3.
        tipo = b["elenco"]
        if tipo == "homem":
            ator = _id_de(HOMENS, _proximo(contador, "H"))
        elif tipo == "mulher":
            ator = _id_de(MULHERES, _proximo(contador, "M"))
        elif tipo == "menino":
            ator = _id_de(MENINOS, _proximo(contador, "B"))
        elif tipo == "familia":
            ator = "%s + %s + %s" % (_id_de(HOMENS, _proximo(contador, "H")),
                                     _id_de(MULHERES, _proximo(contador, "M")),
                                     _id_de(MENINOS, _proximo(contador, "B")))
        else:                                                      # trio
            ator = "%s + %s + %s" % (_id_de(HOMENS, _proximo(contador, "H")),
                                     _id_de(MULHERES, _proximo(contador, "M")),
                                     _id_de(MENINAS, _proximo(contador, "G")))
        itens.append(dict(
            peca=p, nome=b["nome"], porque=b["porque"], formato="banner",
            lado=b.get("lado", "esquerda"), ator=ator,
            prompt=CENA_BANNER.format(perfil=perfil, cena=b["cena"]),
            negativo=NEGATIVO_BANNER,
            extras=achadas[1:] if b["elenco"] in ("trio", "familia") else [],
        ))
    return itens


def _cartoes(pecas, molde, elenco, elenco2=None):
    itens = []
    for i, p in enumerate(pecas):
        lista = elenco if (elenco2 is None or i % 2 == 0) else elenco2
        perfil = lista[i % len(lista)]
        base = molde
        if base is None:                       # 05: jaqueta ou conjunto
            base = JAQUETA if p.get("categoria") == "jaqueta" else CONJUNTO
        itens.append(dict(
            peca=p, nome="%02d-%s" % (i + 1, _slug(p["chave"])),
            porque="", formato="card", ator=_id_de(lista, i),
            prompt=base.format(perfil=perfil), negativo=NEGATIVO, extras=[],
        ))
    return itens


# =====================================================================
# PREPARAR
# =====================================================================
def _foto_original(p):
    """O caminho da melhor foto da peça: a original de 1024 quando existe."""
    from posts import _indice_originais
    nome = p["fotos"][0].split("/")[-1]
    caminho = _indice_originais().get(nome)
    if caminho and os.path.exists(caminho):
        return caminho
    alternativa = os.path.join(AQUI, "site", "fotos", nome)
    return alternativa if os.path.exists(alternativa) else None


def preparar():
    pecas = carregar()
    if os.path.isdir(GERAR):
        shutil.rmtree(GERAR)
    os.makedirs(GERAR)

    linhas = ["CAMISARIA ESPORTIVA FC — LISTA DE GERAÇÃO DE MODELOS", "=" * 62, ""]
    linhas += [
        "COMO USAR ESTA PASTA",
        "  1. Abra a pasta da fase (comece pela 01).",
        "  2. Cada imagem tem um arquivo .txt do lado, com o mesmo nome.",
        "  3. Na IA: envie a IMAGEM como referência e cole o PROMPT do .txt.",
        "  4. Salve o resultado em `gerados/`, começando com o MESMO número.",
        "     Exemplo: a referência 03-flamengo-....jpg vira 03-qualquer.png",
        "  5. Quando terminar a fase, rode: python modelos.py padronizar",
        "",
    ]
    total = 0
    faltando = []

    for fase in fases(pecas):
        destino = os.path.join(GERAR, fase["pasta"])
        os.makedirs(destino, exist_ok=True)
        linhas += ["", "=" * 62, fase["titulo"], "=" * 62, fase["porque"], ""]

        for item in fase["itens"]:
            p = item["peca"]
            origem = _foto_original(p)
            if not origem:
                faltando.append(p["chave"])
                continue
            ext = os.path.splitext(origem)[1] or ".webp"
            base = item["nome"]
            shutil.copy2(origem, os.path.join(destino, base + ext))

            ator = item.get("ator") or ""
            tem_elenco = ator and os.path.isdir(ELENCO) and all(
                os.path.exists(os.path.join(ELENCO, a.strip() + ".webp"))
                for a in ator.split("+"))
            texto = [
                "PEÇA: " + p["chave"],
                "PREÇO: R$ %s" % p.get("preco"),
                ("IMAGEM 1 (a pessoa): elenco/" + ator.replace(" + ", ".webp + elenco/") + ".webp"
                 if tem_elenco else "MODELO: " + (ator or "—") + "  (elenco ainda não gerado)"),
                ("IMAGEM 2 (a camisa): " if tem_elenco else "REFERÊNCIA: ") + base + ext,
                "FORMATO: " + ("16:9 HORIZONTAL — 1920x1080 (banner). "
                               "Se a sua IA gerar quadrado, procure a opção de "
                               "proporção e escolha 16:9 antes de gerar."
                               if item["formato"] == "banner"
                               else "1:1 quadrado — 1024x1024 (cartão)"),
            ]
            if item.get("lado"):
                texto.append("TEXTO DO SITE ENTRA À " + item["lado"].upper()
                             + " — deixe esse lado da imagem limpo")
            if item["porque"]:
                texto.append("POR QUE ESTA: " + item["porque"])
            for extra in item["extras"]:
                texto.append("REFERÊNCIA EXTRA: " + extra["chave"])
            prompt = item["prompt"]
            if tem_elenco:
                prompt = vestir(len(ator.split("+")),
                                1 + len(item["extras"])) + prompt
            texto += ["", "-" * 62, "PROMPT", "-" * 62, prompt, "",
                      "-" * 62, "NEGATIVE PROMPT", "-" * 62, item["negativo"], ""]
            with io.open(os.path.join(destino, base + ".txt"), "w",
                         encoding="utf-8") as f:
                f.write("\n".join(texto))

            if tem_elenco:
                for k, a in enumerate(ator.split("+"), 1):
                    a = a.strip()
                    sufixo = "-pessoa" if k == 1 else "-pessoa%d" % k
                    shutil.copy2(os.path.join(ELENCO, a + ".webp"),
                                 os.path.join(destino, base + sufixo + ".webp"))
            linhas.append("  [ ] %-30s %-8s %s" % (base, ator, p["chave"][:58]))
            total += 1

        # as referências extras dos banners de família e coleção
        for item in fase["itens"]:
            for k, extra in enumerate(item["extras"], 2):
                origem = _foto_original(extra)
                if origem:
                    ext = os.path.splitext(origem)[1] or ".webp"
                    shutil.copy2(origem, os.path.join(
                        destino, "%s-ref%d%s" % (item["nome"], k, ext)))

    linhas += ["", "=" * 62, "TOTAL: %d imagens para gerar" % total]
    if faltando:
        linhas += ["", "SEM FOTO ORIGINAL (não entraram):"] + \
                  ["  " + c for c in faltando]

    with io.open(os.path.join(GERAR, "LISTA.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")

    print("\n".join(linhas[-6:]))
    print("\npronto: %s" % GERAR)
    print("abra gerar/LISTA.txt e comece pela pasta 01-banners")


# =====================================================================
# PADRONIZAR
# =====================================================================
# Depois da IA. Cada arquivo de `gerados/` é cortado no formato certo,
# encolhido, virado webp e renomeado com o nome que o site procura.
MEDIDAS = {
    "banner": (1600, 900, 150),      # largura, altura, KB alvo
    "card":   (900, 900, 110),
}


NOGUEIRA = (42, 28, 18)          # #2a1c12, o fundo do topo do site


def _cortar(img, larg, alt, lado="esquerda"):
    """Deixa a imagem no formato pedido sem esticar nada.

    Corta quando dá pra cortar. Mas se a imagem for MUITO mais alta que o
    formato — o caso de um 1:1 virando 16:9 — cortar decepa a cabeça ou o
    pé do modelo. Aí, em vez de estragar, ela é encaixada inteira num
    fundo cor de nogueira, encostada no lado oposto ao do texto. O banner
    fica sendo a foto inteira com o fundo do site completando."""
    quero = larg / float(alt)
    tenho = img.width / float(img.height)

    if tenho > quero:                                  # sobra dos lados
        nova = int(img.height * quero)
        x = (img.width - nova) // 2
        img = img.crop((x, 0, x + nova, img.height))
        return img.resize((larg, alt), Image.LANCZOS)

    if tenho >= quero * 0.72:                          # dá pra cortar
        nova = int(img.width / quero)
        y = int((img.height - nova) * 0.20)            # tira mais do pé
        y = max(0, min(y, img.height - nova))
        img = img.crop((0, y, img.width, y + nova))
        return img.resize((larg, alt), Image.LANCZOS)

    # Alta demais pra cortar: encaixa a imagem inteira e completa o resto.
    #
    # O primeiro jeito foi tampar a sobra com nogueira chapada. Ficou um
    # retângulo morto do lado. Agora a sobra é a PRÓPRIA imagem, ampliada
    # e borrada por trás — a foto parece continuar até a borda, e o texto
    # do site ainda se lê por cima porque o borrão é escurecido.
    escala = alt / float(img.height)
    frente = img.resize((max(1, int(img.width * escala)), alt), Image.LANCZOS)

    largo = max(larg, int(img.width * (larg / float(img.width))))
    fundo = img.resize((larg, max(alt, int(img.height * larg / float(img.width)))),
                       Image.LANCZOS)
    y = (fundo.height - alt) // 2
    fundo = fundo.crop((0, y, larg, y + alt))
    try:
        from PIL import ImageFilter, ImageEnhance
        fundo = fundo.filter(ImageFilter.GaussianBlur(28))
        fundo = ImageEnhance.Brightness(fundo).enhance(0.42)
    except ImportError:
        fundo = Image.new("RGB", (larg, alt), NOGUEIRA)

    x = (larg - frente.width) if lado == "esquerda" else 0
    if frente.width >= larg:
        x = (larg - frente.width) // 2
    fundo.paste(frente, (x, 0))
    return fundo


def _gravar(img, caminho, kb):
    for q in (86, 80, 74, 68, 62, 56, 50):
        img.save(caminho, "WEBP", quality=q, method=6)
        if os.path.getsize(caminho) <= kb * 1024:
            return


def _ler_manifesto():
    caminho = os.path.join(SAIDA, "banners.json")
    if os.path.exists(caminho):
        try:
            with io.open(caminho, encoding="utf-8") as f:
                return json.load(f)
        except ValueError:
            pass
    return {}


def padronizar():
    if Image is None:
        print("falta o Pillow: pip install pillow")
        return
    if not os.path.isdir(GERADOS):
        os.makedirs(GERADOS)
        print("criei a pasta `gerados/`. Salve as imagens da IA lá dentro,")
        print("mantendo o número do começo do nome, e rode este comando de novo.")
        return

    pecas = carregar()
    # de "03" -> a peça e o formato
    mapa = {}
    for fase in fases(pecas):
        for item in fase["itens"]:
            numero = item["nome"].split("-")[0]
            mapa[(fase["pasta"], numero)] = item

    os.makedirs(SAIDA, exist_ok=True)
    feitos, perdidos, avisos = 0, [], []
    # o banner precisa dizer de QUE peça ele é: o site mostra o nome, o
    # preço e o botão do WhatsApp já escritos ao lado da imagem
    manifesto = _ler_manifesto()

    for raiz, _, arquivos in os.walk(GERADOS):
        pasta = os.path.basename(raiz)
        for arq in sorted(arquivos):
            if not arq.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue
            numero = arq.split("-")[0].split(".")[0].split("_")[0]
            item = mapa.get((pasta, numero))
            if item is None:                     # tenta achar em qualquer fase
                achou = [v for (f, n), v in mapa.items() if n == numero]
                item = achou[0] if len(achou) == 1 else None
            if item is None:
                perdidos.append(os.path.join(pasta, arq))
                continue

            larg, alt, kb = MEDIDAS[item["formato"]]
            img = Image.open(os.path.join(raiz, arq)).convert("RGB")
            proporcao = img.width / float(img.height)
            if item["formato"] == "banner" and proporcao < 1.4:
                avisos.append("%s veio em %dx%d (quase quadrada). Encaixei "
                              "num fundo escuro, mas fica bem melhor se você "
                              "gerar em 16:9." % (arq, img.width, img.height))
            img = _cortar(img, larg, alt, item.get("lado", "esquerda"))

            p = item["peca"]
            if item["formato"] == "banner":
                nome = "banner-" + item["nome"] + ".webp"
                manifesto[nome] = {"chave": p["chave"],
                                   "lado": item.get("lado") or "esquerda"}
            else:
                # o MESMO nome-base da foto do site, pra o site achar sozinho
                nome = p["fotos"][0].split("/")[-1]
                nome = re.sub(r"-\d+\.webp$", ".webp", nome)
            _gravar(img, os.path.join(SAIDA, nome), kb)
            feitos += 1
            print("  %-46s -> %s" % (arq[:46], nome))

    if manifesto:
        with io.open(os.path.join(SAIDA, "banners.json"), "w",
                     encoding="utf-8") as f:
            json.dump(manifesto, f, ensure_ascii=False, indent=1)

    print("\n%d imagens prontas em web/modelos/" % feitos)
    for a in avisos:
        print("   AVISO: " + a)
    if perdidos:
        print("\nnão consegui identificar (renomeie começando com o número):")
        for x in perdidos:
            print("  " + x)
    print("\nagora rode: python publicar.py")


# =====================================================================
# ETAPA A — GERAR O ELENCO
# =====================================================================
def elenco():
    """Escreve os 32 prompts do elenco. Nenhuma foto de referência: aqui as
    pessoas nascem do zero."""
    destino = os.path.join(GERAR, "00-elenco")
    if os.path.isdir(destino):
        shutil.rmtree(destino)
    os.makedirs(destino)

    # o que vestir da cintura pra baixo, por tipo
    BAIXO = {
        "H": "calça jeans azul escuro reta e tênis branco simples",
        "M": "calça jeans azul escuro reta e tênis branco simples",
        "B": "bermuda azul marinho lisa e tênis branco simples",
        "G": "bermuda azul marinho lisa e tênis branco simples",
    }
    ORDEM = ["H", "M", "B", "G"]

    linhas = [
        "CAMISARIA ESPORTIVA FC — O ELENCO",
        "=" * 62, "",
        "São 32 pessoas. Você gera cada uma UMA VEZ, e elas servem para",
        "todas as camisas do site, agora e daqui a dois anos.",
        "",
        "COMO GERAR (Gemini)",
        "  1. Abra o arquivo .txt da pessoa.",
        "  2. Cole o PROMPT. NÃO envie nenhuma imagem — aqui não tem",
        "     referência, a pessoa está sendo criada agora.",
        "  3. Gere 2 ou 3 variações e fique com a melhor.",
        "  4. Salve em gerados/00-elenco/ com o CRACHÁ no nome:",
        "     H1.png, H2.png, M1.png, B1.png, G1.png...",
        "  5. Quando terminar, rode:  python modelos.py elenco-ok",
        "",
        "O QUE REPROVAR",
        "  mão com seis dedos, rosto assimétrico, pé cortado, camiseta com",
        "  estampa ou escrita, sombra dura no fundo, pose forçada.",
        "",
        "POR ONDE COMEÇAR SE QUISER IR AOS POUCOS",
        "  H1 H2 H3 H4  e  M1 M2 M3 M4  já cobrem os 8 banners.",
        "  B1 B2 e G1 G2 cobrem as crianças da fase 4.",
        "  O resto você gera quando quiser mais variedade.",
        "",
    ]

    total = 0
    for prefixo in ORDEM:
        lista = ELENCOS[prefixo]
        titulo = {"H": "HOMENS", "M": "MULHERES",
                  "B": "MENINOS", "G": "MENINAS"}[prefixo]
        linhas += ["", "=" * 62, titulo, "=" * 62]
        for i, perfil in enumerate(lista):
            cracha = "%s%d" % (prefixo, i + 1)
            texto = [
                "ELENCO: " + cracha,
                "NÃO ENVIE IMAGEM DE REFERÊNCIA. Só o prompt.",
                "FORMATO: 3:4 vertical, corpo inteiro",
                "SALVAR COMO: gerados/00-elenco/%s.png" % cracha,
                "", "-" * 62, "PROMPT", "-" * 62,
                PROMPT_ELENCO.format(perfil=perfil, baixo=BAIXO[prefixo]),
                "", "-" * 62, "NEGATIVE PROMPT", "-" * 62,
                NEGATIVO_ELENCO, "",
            ]
            with io.open(os.path.join(destino, cracha + ".txt"), "w",
                         encoding="utf-8") as f:
                f.write("\n".join(texto))
            linhas.append("  [ ] %-5s %s" % (cracha, perfil[:70]))
            total += 1

    linhas += ["", "=" * 62, "TOTAL: %d pessoas" % total]
    with io.open(os.path.join(destino, "LISTA-ELENCO.txt"), "w",
                 encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")

    print("%d prompts em gerar/00-elenco/" % total)
    print("abra gerar/00-elenco/LISTA-ELENCO.txt")
    print("")
    print("comece por H1 H2 H3 H4 e M1 M2 M3 M4 — já cobrem os 8 banners")


def elenco_ok():
    """Pega o que você gerou em gerados/00-elenco/ e guarda em elenco/ com o
    tamanho e o nome certos. É essa pasta que vira a IMAGEM 1 de todas as
    gerações seguintes."""
    if Image is None:
        print("falta o Pillow: pip install pillow")
        return
    origem = os.path.join(GERADOS, "00-elenco")
    if not os.path.isdir(origem):
        os.makedirs(origem)
        print("criei a pasta gerados/00-elenco/. Salve as pessoas lá,")
        print("com o crachá no nome (H1.png, M3.png...), e rode de novo.")
        return
    os.makedirs(ELENCO, exist_ok=True)

    validos = {"%s%d" % (pre, i + 1)
               for pre, lista in ELENCOS.items() for i in range(len(lista))}
    feitos, ignorados = [], []

    for arq in sorted(os.listdir(origem)):
        if not arq.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue
        cracha = re.split(r"[^A-Za-z0-9]", os.path.splitext(arq)[0])[0].upper()
        if cracha not in validos:
            ignorados.append(arq)
            continue
        img = Image.open(os.path.join(origem, arq)).convert("RGB")
        if img.height > 1280:                     # não precisa de mais que isso
            img = img.resize((int(img.width * 1280 / img.height), 1280),
                             Image.LANCZOS)
        _gravar(img, os.path.join(ELENCO, cracha + ".webp"), 150)
        feitos.append(cracha)

    print("%d pessoas prontas em elenco/" % len(feitos))
    if feitos:
        print("   " + " ".join(sorted(feitos)))
    # O aviso do que falta precisa dizer o que É PRECISO, não o que EXISTE
    # na lista. A lista tem 32 pessoas; oito adultos e duas crianças já
    # cobrem os oito banners inteiros. Dizer "faltam 22" assusta e não é
    # verdade — as outras 22 são variedade opcional, pra quando o site
    # estiver cheio e a mesma cara começar a se repetir demais.
    tem = set(_elenco_existente())
    basico = {"H1", "H2", "H3", "H4", "M1", "M2", "M3", "M4", "B1", "G1"}
    falta_basico = sorted(basico - tem)
    if falta_basico:
        print("\nfalta o basico: " + " ".join(falta_basico))
        print("   (com H1-H4, M1-M4, B1 e G1 os oito banners ficam cobertos)")
    else:
        print("\ntudo que os oito banners precisam ja esta aqui.")
        extras = len(validos - tem)
        if extras:
            print("   as outras %d pessoas do elenco sao opcionais — sao pra"
                  % extras)
            print("   dar variedade quando o site tiver muita foto de modelo.")
    if ignorados:
        print("\nnão entendi o crachá destes (renomeie pra H1.png, M2.png...):")
        for x in ignorados:
            print("   " + x)
    caminho = folha_de_conferencia()
    if caminho:
        print("\nCONFIRA QUEM E QUEM antes de seguir:")
        print("   abra  elenco\\CONFERIR.jpg")
        print("   estao os %d lado a lado com o cracha escrito em cima." % len(feitos))
        print("   se algum estiver trocado:  python modelos.py trocar H2 H3")

    print("\nagora rode: python modelos.py preparar")


# =====================================================================
# RENOMEAR — pra você não ter que digitar H1.png dez vezes
# =====================================================================
# O Python NÃO sabe quem é quem: ele não olha a foto e reconhece que
# aquele é o homem negro. O que ele sabe é a ORDEM em que os arquivos
# foram baixados, que é a data de cada um.
#
# Então ele renomeia pela ordem e monta uma folha de conferência com os
# dez lado a lado e o crachá escrito em cima. Você abre, bate o olho, e
# se algum estiver trocado corrige com um comando só.
ORDEM_BASICA = ["H1", "H2", "H3", "H4", "M1", "M2", "M3", "M4", "B1", "G1"]

QUEM_E = {
    "H1": "homem branco, barba",  "H2": "homem loiro",
    "H3": "homem negro",          "H4": "homem asiatico",
    "M1": "mulher morena",        "M2": "mulher loira",
    "M3": "mulher negra",         "M4": "mulher asiatica",
    "B1": "menino",               "G1": "menina",
}


def _fonte(tamanho):
    from PIL import ImageFont
    for nome in ("arial.ttf", "Arial.ttf", "segoeui.ttf",
                 "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(nome, tamanho)
        except (OSError, IOError):
            pass
    return ImageFont.load_default()


def folha_de_conferencia():
    """Junta o elenco numa imagem só, com o crachá escrito em cada um."""
    from PIL import ImageDraw
    tem = sorted(_elenco_existente(),
                 key=lambda c: (ORDEM_BASICA.index(c) if c in ORDEM_BASICA
                                else 99, c))
    if not tem:
        return None
    larg, alt, faixa = 260, 347, 52
    colunas = min(5, len(tem))
    linhas = (len(tem) + colunas - 1) // colunas
    folha = Image.new("RGB", (colunas * larg, linhas * (alt + faixa)),
                      (250, 246, 239))
    desenho = ImageDraw.Draw(folha)
    fonte = _fonte(23)
    fonte_pe = _fonte(15)
    for i, cracha in enumerate(tem):
        x = (i % colunas) * larg
        y = (i // colunas) * (alt + faixa)
        foto = Image.open(os.path.join(ELENCO, cracha + ".webp"))
        foto.thumbnail((larg - 8, alt - 8), Image.LANCZOS)
        folha.paste(foto, (x + (larg - foto.width) // 2,
                           y + (alt - foto.height) // 2))
        desenho.rectangle([x, y + alt, x + larg, y + alt + faixa],
                          fill=(31, 24, 17))
        desenho.text((x + 12, y + alt + 5), cracha,
                     fill=(201, 166, 117), font=fonte)
        desenho.text((x + 12, y + alt + 31), QUEM_E.get(cracha, ""),
                     fill=(230, 220, 205), font=fonte_pe)
    caminho = os.path.join(ELENCO, "CONFERIR.jpg")
    folha.save(caminho, "JPEG", quality=88)
    return caminho


def renomear():
    """Renomeia os arquivos de gerados/00-elenco/ pela ordem de download."""
    if Image is None:
        print("falta o Pillow: pip install pillow")
        return
    pasta = os.path.join(GERADOS, "00-elenco")
    if not os.path.isdir(pasta):
        os.makedirs(pasta)
        print("criei a pasta gerados/00-elenco/.")
        print("Jogue as 10 imagens la dentro, com o nome que vier do")
        print("Gemini mesmo, e rode este comando de novo.")
        return

    fotos = [f for f in os.listdir(pasta)
             if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
    if len(fotos) != len(ORDEM_BASICA):
        print("achei %d imagens em gerados/00-elenco/ e esperava %d."
              % (len(fotos), len(ORDEM_BASICA)))
        print("Deixe exatamente estas dez na pasta:")
        print("   " + " ".join(ORDEM_BASICA))
        print("Se voce ja renomeou tudo na mao, pule este comando e rode")
        print("direto: python modelos.py elenco-ok")
        return

    # a ordem de download é a data de cada arquivo
    fotos.sort(key=lambda f: os.path.getmtime(os.path.join(pasta, f)))
    print("renomeando pela ordem de download:\n")
    for cracha, arquivo in zip(ORDEM_BASICA, fotos):
        ext = os.path.splitext(arquivo)[1].lower()
        destino = os.path.join(pasta, cracha + ext)
        if os.path.abspath(os.path.join(pasta, arquivo)) != os.path.abspath(destino):
            if os.path.exists(destino):
                os.replace(os.path.join(pasta, arquivo), destino + ".tmp")
                os.replace(destino + ".tmp", destino)
            else:
                os.rename(os.path.join(pasta, arquivo), destino)
        print("   %-40s -> %s  (%s)" % (arquivo[:40], cracha + ext,
                                        QUEM_E[cracha]))
    print("\npronto. agora rode: python modelos.py elenco-ok")


def trocar(a, b):
    """Troca dois crachás de lugar, quando a ordem saiu errada."""
    a, b = a.upper(), b.upper()
    achou = {}
    for pasta in (ELENCO, os.path.join(GERADOS, "00-elenco")):
        if not os.path.isdir(pasta):
            continue
        for f in os.listdir(pasta):
            base, ext = os.path.splitext(f)
            if base.upper() in (a, b):
                achou.setdefault(pasta, []).append((base.upper(), f, ext))
    if not achou:
        print("nao achei %s nem %s." % (a, b))
        return
    for pasta, itens in achou.items():
        if len(itens) != 2:
            print("em %s achei so um dos dois — pulei." % pasta)
            continue
        (n1, f1, e1), (n2, f2, e2) = itens
        tmp = os.path.join(pasta, "_troca_")
        os.rename(os.path.join(pasta, f1), tmp)
        os.rename(os.path.join(pasta, f2), os.path.join(pasta, n1 + e2))
        os.rename(tmp, os.path.join(pasta, n2 + e1))
        print("trocado em %s: %s <-> %s" % (os.path.basename(pasta), n1, n2))
    _CACHE_ELENCO.clear()
    caminho = folha_de_conferencia()
    if caminho:
        print("folha de conferencia atualizada: elenco/CONFERIR.jpg")


def _elenco_existente():
    if not os.path.isdir(ELENCO):
        return []
    return [os.path.splitext(f)[0] for f in os.listdir(ELENCO)
            if f.endswith(".webp")]


def listar():
    """Mostra o que SERIA gerado, sem copiar nada. Serve pra você conferir a
    escolha antes de gastar geração — e pra eu conferir sem as fotos."""
    pecas = carregar()
    total = 0
    for fase in fases(pecas):
        print("\n" + "=" * 66)
        print(fase["titulo"])
        print("=" * 66)
        print(fase["porque"])
        print("")
        for item in fase["itens"]:
            p = item["peca"]
            print("  %-13s R$%-4s %s" % (item["nome"][:13], p.get("preco"),
                                          p["chave"][:76]))
            for extra in item["extras"]:
                print("  %14s        + %s" % ("", extra["chave"][:70]))
            total += 1
    print("\n" + "=" * 66)
    print("TOTAL: %d imagens" % total)


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else "preparar"
    if comando.startswith("prep"):
        preparar()
    elif comando.startswith("padr"):
        padronizar()
    elif comando.startswith("list"):
        listar()
    elif comando in ("elenco", "elenco-ok", "elencook"):
        elenco_ok() if comando != "elenco" else elenco()
    elif comando.startswith("renom"):
        renomear()
    elif comando.startswith("troc"):
        if len(sys.argv) < 4:
            print("use assim:  python modelos.py trocar H2 H3")
        else:
            trocar(sys.argv[2], sys.argv[3])
    elif comando.startswith("confer"):
        c = folha_de_conferencia()
        print("folha em " + c if c else "elenco/ esta vazio")
    else:
        print(__doc__)
