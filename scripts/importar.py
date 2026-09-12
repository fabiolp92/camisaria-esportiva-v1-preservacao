# -*- coding: utf-8 -*-
"""Lê uma pasta de fotos do fornecedor, otimiza tudo e grava no banco.

    python scripts/importar.py fotos_originais/criancas1

Cada subpasta é uma peça; os arquivos dentro dela são o conjunto de fotos
daquela peça, na ordem do nome. O script:
  1. descobre time/gênero/uniforme/temporada pelo nome da pasta
  2. comprime cada foto pra ~35KB em WebP
  3. grava em site/fotos/ com o nome do padrão
  4. registra produto, fotos e coleções no banco

Rodar de novo com a mesma pasta atualiza em vez de duplicar.
"""
import os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import banco, fornecedor, imagens

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA_FOTOS = os.path.join(AQUI, "site", "fotos")
EXTENSOES = (".webp", ".jpg", ".jpeg", ".png")


def nome_de_arquivo(time_slug, item, ordem, total):
    """<time>-<genero>-<temporada>-<uniforme>-<versao>[-<variante>][-N].webp

    O nome carrega a peça inteira, então é o mesmo no GitHub (tudo plano) e na
    árvore de pastas do Desktop. Trocar uma foto é sempre 'mesmo nome'."""
    partes = [time_slug, item["genero"], item["temporada"] or "retro", item["uniforme"]]
    if item["versao"]:
        partes.append(item["versao"])
    if item["variante"]:
        partes.append(item["variante"])
    base = "-".join(partes)
    if total > 1:
        base += f"-{ordem}"
    return base + ".webp"


def importar(con, pasta_raiz, alvo_kb=imagens.ALVO_KB, verboso=True):
    nomes = [r["nome"] for r in con.execute("SELECT nome FROM times")]
    times = {r["nome"]: r for r in con.execute("SELECT * FROM times")}
    colecoes = {r["slug"]: r["id"] for r in con.execute("SELECT slug, id FROM colecoes")}
    os.makedirs(SAIDA_FOTOS, exist_ok=True)

    subpastas = sorted(d for d in os.listdir(pasta_raiz)
                       if os.path.isdir(os.path.join(pasta_raiz, d)))
    itens = []
    for d in subpastas:
        it = fornecedor.classificar(d, nomes)
        it["arquivos"] = sorted(f for f in os.listdir(os.path.join(pasta_raiz, d))
                                if f.lower().endswith(EXTENSOES))
        if not it["arquivos"]:
            it["fora"] = "pasta sem foto"
        itens.append(it)

    # duas pastas descrevendo a MESMA peça: fica a que tem mais fotos
    bons = [i for i in itens if not i["fora"]]
    melhor = {}
    for i in bons:
        ch = (i["time"], i["genero"], i["categoria"], i["uniforme"],
              i["temporada"], i["versao"], i["variante"])
        if ch not in melhor or len(i["arquivos"]) > len(melhor[ch]["arquivos"]):
            melhor[ch] = i
    for i in bons:
        ch = (i["time"], i["genero"], i["categoria"], i["uniforme"],
              i["temporada"], i["versao"], i["variante"])
        if melhor[ch] is not i:
            i["fora"] = "cópia de outra pasta igual, com menos fotos"

    finais = sorted(melhor.values(), key=lambda i: (i["time"], i["temporada"] or "", i["uniforme"]))

    # Segunda trava: nenhum item pode citar um time que nao esta no banco.
    # Conferir ANTES de comprimir a primeira foto evita parar no meio de uma
    # importacao de 15 minutos por causa de um nome errado.
    fantasmas = sorted({i["time"] for i in finais if i["time"] not in times})
    if fantasmas:
        raise SystemExit("Estes times não existem no times.json: " + ", ".join(fantasmas) +
                         "\nNenhuma foto foi gravada.")

    # Trava de seguranca: duas pecas DIFERENTES nunca podem gerar a mesma chave.
    # Se gerarem, o INSERT ... ON CONFLICT(chave) faria a segunda reaproveitar o
    # produto da primeira e o DELETE seguinte apagaria as fotos dela — perda
    # silenciosa de dado, que e o pior tipo de bug. Melhor parar e avisar.
    porchave = collections.defaultdict(list)
    for i in finais:
        porchave[fornecedor.chave_do_produto(i)].append(i)
    repetidas = {k: v for k, v in porchave.items() if len(v) > 1}
    if repetidas:
        linhas = ["Duas peças diferentes geraram a mesma chave de catálogo.",
                  "Nenhuma foto foi gravada. Me mande esta lista:"]
        for k, v in sorted(repetidas.items()):
            linhas.append(f"  {k}")
            linhas += [f"      {x['pasta']}" for x in v]
        raise SystemExit("\n".join(linhas))
    total_fotos = sum(len(i["arquivos"]) for i in finais)
    feitas, tamanhos = 0, []

    for item in finais:
        t = times[item["time"]]
        chave = fornecedor.chave_do_produto(item)
        con.execute("""INSERT INTO produtos (time_id, genero, categoria, uniforme,
                          temporada, versao, variante, chave)
                       VALUES (?,?,?,?,?,?,?,?)
                       ON CONFLICT(chave) DO UPDATE SET time_id=excluded.time_id""",
                    (t["id"], item["genero"], item["categoria"], item["uniforme"],
                     item["temporada"], item["versao"], item["variante"], chave))
        pid = con.execute("SELECT id FROM produtos WHERE chave = ?", (chave,)).fetchone()["id"]
        con.execute("DELETE FROM fotos WHERE produto_id = ?", (pid,))

        n_total = len(item["arquivos"])
        for n, arq in enumerate(item["arquivos"], 1):
            nome = nome_de_arquivo(t["slug"], item, n, n_total)
            destino = os.path.join(SAIDA_FOTOS, nome)
            bytes_, largura = imagens.comprimir(
                os.path.join(pasta_raiz, item["pasta"], arq), destino, alvo_kb)
            tamanhos.append(bytes_)
            con.execute("""INSERT INTO fotos (produto_id, arquivo, ordem, bytes, largura, origem)
                           VALUES (?,?,?,?,?,?)""",
                        (pid, f"fotos/{nome}", n, bytes_, largura,
                         f"{item['pasta']}/{arq}"))
            feitas += 1
            if verboso:
                print(f"\r  {feitas}/{total_fotos} fotos", end="", flush=True)

        con.execute("DELETE FROM produto_colecao WHERE produto_id = ?", (pid,))
        for slug in fornecedor.colecoes_do_produto(item, t):
            if slug in colecoes:
                con.execute("INSERT OR IGNORE INTO produto_colecao VALUES (?,?)",
                            (pid, colecoes[slug]))
    con.commit()
    if verboso and total_fotos:
        print()
    return finais, [i for i in itens if i["fora"]], tamanhos


def relatorio(finais, fora, tamanhos):
    linhas = [f"IMPORTAÇÃO — {len(finais) + len(fora)} pastas",
              f"  entraram: {len(finais)} peças, {len(tamanhos)} fotos"]
    if tamanhos:
        linhas.append(f"  peso médio {sum(tamanhos)/len(tamanhos)/1024:.1f} KB "
                      f"(maior {max(tamanhos)/1024:.1f} KB), "
                      f"total {sum(tamanhos)/1024/1024:.1f} MB")
    linhas.append("")
    for i in finais:
        rot = fornecedor.ROTULO_UNIFORME.get(i["uniforme"], i["uniforme"])
        linhas.append(f"  {i['time']:26s} {i['genero']:10s} {rot:12s} "
                      f"{i['temporada'] or '':6s} ({len(i['arquivos'])} fotos)")
    if fora:
        linhas += ["", f"FICARAM DE FORA: {len(fora)} pastas"]
        motivos = collections.Counter(i["fora"] for i in fora)
        for m, n in motivos.most_common():
            linhas.append(f"  {n:3d}  {m}")
        linhas.append("")
        for i in sorted(fora, key=lambda i: i["fora"]):
            linhas.append(f"    {i['pasta']:62s} -> {i['fora']}")
    return "\n".join(linhas)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: python scripts/importar.py <pasta com as subpastas do fornecedor>")
    pasta = os.path.abspath(sys.argv[1])
    if not os.path.isdir(pasta):
        sys.exit(f"não achei a pasta {pasta}")
    con = banco.abrir()
    finais, fora, tamanhos = importar(con, pasta)
    texto = relatorio(finais, fora, tamanhos)
    open(os.path.join(AQUI, "relatorio-importacao.txt"), "w", encoding="utf-8").write(texto)
    print(texto[:texto.index("\n\n")] if "\n\n" in texto else texto)
    print(f"\nrelatório completo em relatorio-importacao.txt")
    print("banco:", banco.resumo(con))
