# -*- coding: utf-8 -*-
"""Quanto cada peça é procurada. Serve pra ordenar as vitrines.

POR QUE ISSO EXISTE
Em ordem alfabética o acervo abre em Aberdeen, AEK Atenas e Albacete. São
peças legítimas, mas ninguém entra num site de camisa retrô procurando
Albacete. Entra procurando Brasil 94, Flamengo 81, Milan 88/89, Napoli do
Maradona. Esta tabela põe essas na frente.

ISTO É OPINIÃO, NÃO É DADO
Não existe estatística de procura do seu acervo — ele acabou de subir. O que
está aqui é uma leitura do mercado brasileiro de camisa de coleção: que
clubes vendem, que anos as pessoas procuram pelo nome. Quando você começar
a receber pedidos no WhatsApp, VOCÊ vai saber melhor que eu. Aí é só mexer
nos números: o que estiver errado, corrija aqui e rode `python publicar.py`
de novo.

COMO A CONTA FUNCIONA
    peso do time      x10     é o que mais pesa
    ano icônico       +25     "Brasil 1994" vale mais que "Brasil 2014"
    edição especial   +15     nome de jogador, final, centenário
    temporada atual    +8     camisa do ano vende sozinha
    é retrô            +5     desempate a favor do acervo antigo
    calção, meião     -25     acessório não abre vitrine
    marcada por você  +100    a coluna 'destaque' da planilha ganha de tudo
"""

# =====================================================================
# PESO DO TIME — de 5 (vende sozinho) a 1 (nicho)
# =====================================================================
# O que não estiver listado vale 1. Não é desprezo: é que camisa do
# Albacete não é o que traz gente pro site.
PESO = {}

def _p(nivel, times):
    for t in times:
        PESO[t] = nivel

# 5 — os que qualquer brasileiro reconhece
_p(5, ["Brasil", "Flamengo", "Real Madrid", "FC Barcelona", "Argentina"])

# 4 — grandes do Brasil e da Europa
_p(4, ["Corinthians", "Palmeiras", "São Paulo", "Santos", "Vasco da Gama",
       "Grêmio", "Cruzeiro", "Internacional", "Atlético Mineiro",
       "Botafogo", "Fluminense",
       "Manchester United", "AC Milan", "Juventus", "Liverpool",
       "Inter de Milão", "Bayern de Munique", "Paris Saint-Germain",
       "Alemanha", "Itália", "França", "Portugal", "Inglaterra", "Holanda"])

# 3 — conhecidos, procura constante
_p(3, ["Arsenal", "Chelsea", "Manchester City", "Tottenham", "Napoli",
       "Ajax", "Borussia Dortmund", "Atlético de Madrid", "Porto",
       "Benfica", "Sporting CP", "Boca Juniors", "River Plate",
       "Espanha", "Uruguai", "México", "Colômbia", "Japão", "Croácia",
       "Bahia", "Sport Recife", "Athletico Paranaense", "Ceará",
       "Red Bull Bragantino", "Fortaleza"])

# 2 — o colecionador procura, o torcedor comum não
_p(2, ["Parma", "Fiorentina", "Lazio", "AS Roma", "Sevilla", "Valencia",
       "Real Betis", "Celtic", "Rangers FC", "Newcastle United",
       "Everton", "Leeds United", "Nottingham Forest", "Aston Villa",
       "Olympique de Marselha", "Olympique de Lyon", "Galatasaray",
       "Estrela Vermelha", "PSV Eindhoven", "Feyenoord", "Udinese",
       "Torino", "Bélgica", "Nigéria", "Camarões", "Chile", "Peru",
       "Paraguai", "Estados Unidos", "Coreia do Sul", "Iugoslávia",
       "União Soviética", "Tchecoslováquia", "Dinamarca", "Escócia",
       "Peñarol", "Nacional", "Colo-Colo", "Independiente",
       "Remo", "Paysandu", "Náutico", "Santa Cruz", "Figueirense",
       "Chapecoense", "Coritiba", "Vitória", "Goiás", "América de Cali"])


# =====================================================================
# ANOS ICÔNICOS — o ano em que a camisa virou lembrança
# =====================================================================
# O texto tem que bater EXATAMENTE com o que está no catálogo: às vezes é
# "1994", às vezes "98-99". Rode `python -c "import scripts.cobica as c;
# c.conferir()"` pra ver quais destes não existem no seu acervo.
ICONICAS = {
    # ---------------------------------------------------------- seleções
    ("Brasil", "1994"),        # o tetra nos Estados Unidos
    ("Brasil", "1998"),        # Ronaldo, a final que não aconteceu
    ("Brasil", "2004"),
    ("Brasil", "2006"),
    ("Brasil", "1957"),        # a mais antiga do acervo
    ("Argentina", "1986"),     # Maradona, a mão e o gol do século
    ("Argentina", "1994"),
    ("Argentina", "2014"),
    ("Alemanha", "1990"),      # Matthäus, Völler, a Copa da Itália
    ("Alemanha", "1996"),      # a Euro na Inglaterra
    ("Alemanha", "2014"),      # o 7 a 1
    ("França", "1998"),        # Zidane em casa
    ("França", "2018"),
    ("Holanda", "1978"),       # a laranja de Cruyff
    ("Holanda", "2010"),
    ("Itália", "1994"),        # Baggio e o pênalti
    ("Itália", "2006"),        # a Copa da Alemanha
    ("Inglaterra", "1990"),
    ("Inglaterra", "1998"),
    ("Portugal", "1972"),
    ("Portugal", "2016"),      # a Euro
    ("México", "1986"),
    ("Colômbia", "1990"),      # Higuita e Valderrama
    ("Iugoslávia", "1990"),
    ("União Soviética", "1990"),
    ("Tchecoslováquia", "1990"),
    # ------------------------------------------------------------ Brasil
    ("Flamengo", "1981"),      # Zico e o Mundial
    ("Flamengo", "1990"),
    ("Flamengo", "19-20"),     # Gabigol, a Libertadores da virada
    ("Flamengo", "2009"),
    ("Vasco da Gama", "1997"),
    ("Vasco da Gama", "1998"), # a Libertadores
    ("Vasco da Gama", "2000"),
    ("Botafogo", "1995"),      # Túlio Maravilha
    ("Corinthians", "1982"),   # a Democracia Corintiana
    ("Corinthians", "95-96"),
    ("Fluminense", "1993"),
    ("Grêmio", "97-98"),
    ("Cruzeiro", "93-94"),
    ("Internacional", "1997"),
    ("Atlético Mineiro", "1995"),
    # ------------------------------------------------------------ Europa
    ("Real Madrid", "98-00"),  # a Sétima e a Oitava
    ("Real Madrid", "01-02"),  # o centenário, Zidane na final
    ("Real Madrid", "2014"),   # a Décima
    ("Real Madrid", "96-97"),
    ("FC Barcelona", "08-09"), # o sexteto de Guardiola
    ("FC Barcelona", "98-99"), # o centenário
    ("FC Barcelona", "2006"),  # Ronaldinho
    ("FC Barcelona", "96-97"), # Ronaldo Fenômeno
    ("AC Milan", "88-89"),     # Van Basten, Gullit, Rijkaard
    ("AC Milan", "93-94"),     # o 4 a 0 no Barcelona
    ("AC Milan", "06-07"),     # Kaká
    ("Inter de Milão", "98-99"),  # Ronaldo
    ("Inter de Milão", "02-03"),
    ("Juventus", "95-97"),     # Zidane e Del Piero
    ("Juventus", "97-98"),
    ("Manchester United", "98-99"),  # a tríplice coroa
    ("Manchester United", "07-08"),  # Cristiano Ronaldo em Moscou
    ("Manchester United", "92-94"),  # Cantona
    ("Liverpool", "04-05"),    # a noite de Istambul
    ("Liverpool", "1981"),
    ("Liverpool", "1977"),
    ("Arsenal", "97-99"),      # a era Wenger
    ("Arsenal", "02-04"),      # os invencíveis
    ("Napoli", "87-88"),       # Maradona
    ("Napoli", "88-89"),
    ("Napoli", "90-91"),
    ("Ajax", "94-95"),         # a Champions dos meninos
    ("Ajax", "1998"),
    ("Boca Juniors", "00-01"), # Riquelme, o Mundial
    ("Boca Juniors", "1981"),  # Maradona
    ("River Plate", "1986"),
    ("River Plate", "96-97"),
    ("Paris Saint-Germain", "94-95"),
    ("Paris Saint-Germain", "17-18"),  # Neymar
    ("Borussia Dortmund", "96-97"),    # a Champions
    ("Bayern de Munique", "98-99"),
    ("Chelsea", "2012"),       # a Champions em Munique
    ("Parma", "98-99"),        # a geração Buffon, Cannavaro, Verón
}


# ---------------------------------------------------------------------
# Palavras que aparecem em `edicao` e valem ponto: é peça com história,
# não variação de cor.
EDICAO_FORTE = ("centenário", "centenario", "final", "champions", "mundial",
                "libertadores", "copa", "aniversário", "aniversario",
                "comemorativ")


def _ano(p):
    return (p.get("ano_retro") or p.get("temporada") or "").strip()


def pontos(p, temporada_atual="26-27"):
    """A nota de uma peça. Quanto maior, mais cedo ela aparece."""
    n = PESO.get(p["time"], 1) * 10

    if (p["time"], _ano(p)) in ICONICAS:
        n += 25

    ed = (p.get("edicao") or "").lower()
    if ed:
        n += 15 if any(x in ed for x in EDICAO_FORTE) else 5

    if p.get("temporada") == temporada_atual:
        n += 8
    if p.get("uniforme") == "retro":
        n += 5

    # Calção e meião de time grande não abrem vitrine. Sem esta linha, o
    # "Calção Retrô do Milan" entrava na frente da camisa do Corinthians 82
    # só porque o Milan pesa mais que o Corinthians.
    if p.get("categoria") in ("calcao", "calca", "meiao", "luva"):
        n -= 25
    if p.get("destaque"):
        n += 100
    return n


def conferir(caminho="site/catalogo.json"):
    """Diz quais anos icônicos NÃO existem no acervo — assim a tabela não
    fica cheia de linha morta depois que o catálogo muda."""
    import json
    d = json.load(open(caminho, encoding="utf-8"))
    existem = {(p["time"], _ano(p)) for p in d}
    faltam = sorted(ICONICAS - existem)
    print(f"{len(ICONICAS) - len(faltam)} de {len(ICONICAS)} anos icônicos "
          f"existem no acervo")
    if faltam:
        print("\nNão existem (a linha na tabela não faz nada):")
        for t, a in faltam:
            print(f"   {t} — {a}")
    sem_peso = sorted({p["time"] for p in d} - set(PESO))
    print(f"\n{len(sem_peso)} times sem peso definido (valem 1)")
