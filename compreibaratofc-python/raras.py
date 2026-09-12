# -*- coding: utf-8 -*-
"""Marca as peças raras na planilha: destaque e, em algumas, preço.

    python planilha.py     (primeiro, pra a planilha estar em dia com o catálogo)
    python raras.py        (depois)

POR QUE ISSO É UM ARQUIVO E NÃO UM TRABALHO NO SHEETS
São vinte peças no meio de 2.596 linhas. Achar cada uma na mão é meia hora de
rolagem e chance de errar a linha. Aqui a peça é encontrada pela CHAVE exata —
se alguma não for encontrada, o script AVISA em vez de marcar a errada.

Isto é uma SUGESTÃO INICIAL, não uma regra do sistema. Depois de rodar, quem
manda é a planilha: mude o preço, tire o SIM, acrescente outras. Rodar
`planilha.py` de novo preserva o que você deixou lá.
"""
import csv
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(AQUI, "planilha-precos.csv")

# (chave, preço novo ou None pra manter o que está)
#
# Preço só sobe onde há um NOME ou um TÍTULO na camisa — é o que o colecionador
# procura pelo nome. Nas camisas de Copa o preço fica em 275: o que faz elas
# venderem é aparecer na home, não custar mais caro.
RARAS = [
    # nome de jogador na camisa
    ("Juventus - Masculino - Retrô 95-97 - Zidane", 349),
    ("Alemanha - Masculino - Retrô 1990 - Matthaus", 349),
    ("Alemanha - Masculino - Retrô 1990 - Voller", 349),
    ("Manchester United - Masculino - Retrô 07-08 - Ronaldo Champions", 349),
    # final e centenário
    ("Manchester United - Masculino - Retrô 07-08 - Final Champions League", 329),
    ("Manchester United - Masculino - Retrô 07-08 - Manga Longa · Final Champions League", 329),
    ("Boca Juniors - Masculino - Retrô 2005 - Centenário", 299),
    ("Flamengo - Masculino - Retrô 2012 - Centenário", 299),
    ("Chivas Guadalajara - Masculino - Retrô 1906 - Centenário", 299),
    # Copas — só destaque, preço continua 275
    ("Argentina - Masculino - Retrô 1986", None),
    ("Alemanha - Masculino - Retrô 1990", None),
    ("Holanda - Masculino - Retrô 1978", None),
    ("Colômbia - Masculino - Retrô 1990", None),
    ("França - Masculino - Retrô 1998", None),
    ("Iugoslávia - Masculino - Retrô 1990", None),
    ("União Soviética - Masculino - Retrô 1990", None),
    ("Tchecoslováquia - Masculino - Retrô 1990", None),
    ("Brasil - Masculino - Retrô 1998 - 2º Uniforme", None),
    ("Inglaterra - Masculino - Retrô 1990", None),
    ("México - Masculino - Retrô 1986", None),
]


def main():
    if not os.path.exists(CSV):
        sys.exit("Não achei planilha-precos.csv. Rode antes:  python planilha.py")

    with open(CSV, newline="", encoding="utf-8-sig") as f:
        leitor = csv.DictReader(f)
        colunas = leitor.fieldnames
        linhas = list(leitor)

    por_chave = {l["chave"]: l for l in linhas}
    marcadas, precos, faltando = [], [], []

    for chave, preco in RARAS:
        l = por_chave.get(chave)
        if l is None:
            faltando.append(chave)
            continue
        l["destaque"] = "SIM"
        marcadas.append(chave)
        if preco is not None and l["preco"] != str(preco):
            precos.append((chave, l["preco"], preco))
            l["preco"] = str(preco)

    with open(CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=colunas)
        w.writeheader()
        w.writerows(linhas)

    print(f"\n{len(marcadas)} peças marcadas com destaque")
    for c, antes, agora in precos:
        print(f"  R$ {antes} -> R$ {agora}   {c}")
    if faltando:
        print(f"\n  {len(faltando)} não foram encontradas (nada foi marcado nelas):")
        for c in faltando:
            print(f"    {c}")
        print("  Rode 'python planilha.py' antes deste, pra planilha ficar em dia.")

    total = sum(1 for l in linhas if (l.get("destaque") or "").strip().upper() == "SIM")
    print(f"\nTotal de destaques na planilha agora: {total}")
    print("\nPra ver no Sheets: Arquivo > Importar > planilha-precos.csv > Substituir planilha")
    print("Pra o site enxergar:  python build.py")


if __name__ == "__main__":
    main()
