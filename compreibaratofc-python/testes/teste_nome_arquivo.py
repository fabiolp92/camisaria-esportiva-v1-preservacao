# -*- coding: utf-8 -*-
"""Regressão: nenhuma peça de fotos_originais/criancas1 pode gerar o mesmo
nome de arquivo que outra peça diferente.

O bug que isso pega: peças retrô do mesmo time com anos ou uniformes-base
diferentes (Real Madrid 11-12, 17-18 e 17-18 II) reduziam pro mesmo nome
"<time>-<genero>-retro-retro.webp" e a última importada apagava a foto das
outras em silêncio.

Não toca no banco nem comprime imagem — só repete a classificação e a
deduplicação de scripts/importar.py em memória, pra ficar rápido.

    python testes/teste_nome_arquivo.py
"""
import collections
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AQUI)
from scripts import fornecedor, importar

PASTA = os.path.join(AQUI, "fotos_originais", "criancas1")
TIMES_JSON = os.path.join(AQUI, "dados", "times.json")


def _finais_e_slugs():
    times = json.load(io.open(TIMES_JSON, encoding="utf-8"))
    nomes = [t["nome"] for t in times]
    slugs = {t["nome"]: t["slug"] for t in times}

    subpastas = sorted(d for d in os.listdir(PASTA)
                       if os.path.isdir(os.path.join(PASTA, d)))
    itens = []
    for d in subpastas:
        it = fornecedor.classificar(d, nomes)
        it["arquivos"] = sorted(f for f in os.listdir(os.path.join(PASTA, d))
                                if f.lower().endswith(importar.EXTENSOES))
        if not it["arquivos"]:
            it["fora"] = "pasta sem foto"
        itens.append(it)

    # mesma deduplicação de scripts/importar.py:importar() — inclui ano_retro
    # e uniforme_base, senão retros diferentes (mesmo time, anos diferentes)
    # se confundiriam antes mesmo de chegar no teste de nome de arquivo.
    bons = [i for i in itens if not i["fora"]]
    melhor = {}
    for i in bons:
        ch = (i["time"], i["genero"], i["categoria"], i["uniforme"],
              i["temporada"], i["versao"], i["variante"],
              i["ano_retro"], i["uniforme_base"])
        if ch not in melhor or len(i["arquivos"]) > len(melhor[ch]["arquivos"]):
            melhor[ch] = i
    return list(melhor.values()), slugs


def teste_sem_nome_repetido():
    finais, slugs = _finais_e_slugs()
    origem = collections.defaultdict(list)
    for item in finais:
        slug = slugs[item["time"]]
        total = len(item["arquivos"])
        for n in range(1, total + 1):
            nome = importar.nome_de_arquivo(slug, item, n, total)
            origem[nome].append(item["pasta"])

    repetidos = {nome: pastas for nome, pastas in origem.items() if len(pastas) > 1}
    if repetidos:
        linhas = ["nomes de arquivo repetidos:"]
        for nome, pastas in sorted(repetidos.items()):
            linhas.append(f"  {nome}")
            linhas += [f"      {p}" for p in pastas]
        raise AssertionError("\n".join(linhas))

    total_arquivos = sum(len(v) for v in origem.values())
    print(f"OK: {len(finais)} peças, {total_arquivos} nomes de arquivo, nenhum repetido")


if __name__ == "__main__":
    teste_sem_nome_repetido()
