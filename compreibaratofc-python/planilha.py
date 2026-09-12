# -*- coding: utf-8 -*-
"""Gera a planilha de preços a partir do catálogo, pra abrir no Google Sheets.

    python planilha.py

Sai um arquivo `planilha-precos.csv` com UMA LINHA POR PEÇA. Você importa no
Google Sheets uma vez e depois edita lá: preço, destaque, ativo.

POR QUE UMA LINHA POR PEÇA, e não uma tabela de regras com dez linhas
A regra dá o preço de partida, mas quem vende sabe que a Zidane 95/97 não vale
o mesmo que uma retrô qualquer. Com uma linha por peça você muda o preço de UMA
camisa sem mexer em mais nada. A regra entra só como valor inicial.

RODAR DE NOVO NÃO APAGA O QUE VOCÊ EDITOU
Se o arquivo já existe, o script lê o que está lá e preserva preço, custo,
destaque, ativo e observação de cada peça que já conhecia. Peça nova entra com
o preço da regra; peça que saiu do catálogo é avisada no fim, pra você decidir.
É o mesmo princípio do cache das fotos: o trabalho manual nunca é refeito.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts import banco

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(AQUI, "planilha-precos.csv")

CUSTO_PADRAO = 65        # o que você paga por peça, em média
COLUNAS = ["chave", "time", "grupo", "temporada", "fotos",
           "preco", "custo", "destaque", "ativo", "observacao"]
EDITAVEIS = ["preco", "custo", "destaque", "ativo", "observacao"]


# ------------------------------------------------------------------- a regra
# A ORDEM importa: o TIPO da peça decide primeiro, e só depois a versão. Um kit
# infantil retrô é kit infantil (duas peças), não uma retrô solta.
def grupo_e_preco(p):
    if p["genero"] == "infantil":
        return "Kit infantil", 285
    if p["categoria"] == "jaqueta":
        return "Jaqueta / agasalho", 359
    if p["categoria"] == "kit":
        return "Conjunto adulto", 390
    if p["categoria"] in ("calcao", "calca"):
        return "Calção / calça", 99
    if p["categoria"] in ("regata", "polo", "cropped"):
        return p["categoria"].capitalize(), 149
    if p["categoria"] in ("meiao", "luva"):
        return p["categoria"].capitalize(), 99
    if p["uniforme"] == "retro":
        return "Retrô", 275
    if p["versao"] == "jogador":
        genero = "Feminino" if p["genero"] == "feminino" else "Masculino"
        return f"{genero} · Jogador", 250
    genero = "Feminino" if p["genero"] == "feminino" else "Masculino"
    return f"{genero} · Torcedor", 219


def ler_o_que_ja_existe():
    """O que você já editou na planilha, indexado pela chave da peça."""
    if not os.path.exists(CSV):
        return {}
    with open(CSV, newline="", encoding="utf-8-sig") as f:
        return {l["chave"]: l for l in csv.DictReader(f) if l.get("chave")}


def main():
    con = banco.abrir()
    antigo = ler_o_que_ja_existe()

    linhas, novas = [], 0
    for p in con.execute("""
            SELECT p.*, t.nome AS time,
                   (SELECT COUNT(*) FROM fotos WHERE produto_id = p.id) AS n_fotos
            FROM produtos p JOIN times t ON t.id = p.time_id
            ORDER BY t.nome, p.temporada, p.categoria, p.uniforme"""):
        grupo, preco = grupo_e_preco(p)
        ja = antigo.get(p["chave"])
        if ja is None:
            novas += 1
        linhas.append({
            "chave": p["chave"],
            "time": p["time"],
            "grupo": grupo,
            "temporada": (p["ano_retro"] or p["temporada"] or ""),
            "fotos": p["n_fotos"],
            # o que você editou ganha SEMPRE do que a regra sugere
            "preco": (ja or {}).get("preco") or preco,
            "custo": (ja or {}).get("custo") or CUSTO_PADRAO,
            "destaque": (ja or {}).get("destaque", ""),
            "ativo": (ja or {}).get("ativo") or "SIM",
            "observacao": (ja or {}).get("observacao", ""),
        })

    with open(CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)

    sumiram = sorted(set(antigo) - {l["chave"] for l in linhas})

    print(f"\nplanilha-precos.csv  —  {len(linhas)} peças")
    if antigo:
        print(f"  {len(linhas) - novas} já estavam na planilha (preço e ajustes preservados)")
        print(f"  {novas} peças novas, com o preço da regra")
    if sumiram:
        print(f"\n  {len(sumiram)} peças saíram do catálogo e não estão mais na planilha:")
        for c in sumiram[:10]:
            print(f"    {c}")
        if len(sumiram) > 10:
            print(f"    ... e mais {len(sumiram) - 10}")

    print("\nResumo por grupo:")
    por = {}
    for l in linhas:
        g = por.setdefault(l["grupo"], [0, 0])
        g[0] += 1
        g[1] += int(l["preco"])
    for g, (n, soma) in sorted(por.items(), key=lambda x: -x[1][0]):
        print(f"  {g:22s} {n:5d} peças   preço médio R$ {soma // n}")

    print("\nComo abrir no Google Sheets:")
    print("  1. sheets.new  (cria uma planilha em branco)")
    print("  2. Arquivo > Importar > Fazer upload > planilha-precos.csv")
    print("  3. Em 'Tipo de importação' escolha 'Substituir planilha'")
    print("  4. Clique na coluna A > Formatar > Quebra de texto > Cortar")
    print("     (sem isso a chave ocupa cinco linhas de altura em cada peça)")
    print("\nDepois de editar os preços no Sheets, pra o site enxergar:")
    print("  Arquivo > Fazer download > CSV, salve por cima de planilha-precos.csv")
    print("  e rode:  python build.py")


if __name__ == "__main__":
    main()
