# -*- coding: utf-8 -*-
"""Banco -> arquivos que o site consome.

Gera três coisas em site/:
  fotos-do-banco.js   o bloco FOTOS, no formato que o dados.js já entende
  catalogo.json       o catálogo inteiro, pra qualquer coisa futura
                      (páginas de coleção, busca, exportar pro WhatsApp)
  colecoes.json       as vitrines e quantas peças tem em cada uma

O site continua estático: nada aqui precisa de servidor. O banco é a fonte,
estes arquivos são a fotografia dela no momento do build.
"""
import csv, io, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import banco

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(AQUI, "site")
PLANILHA = os.path.join(AQUI, "planilha-precos.csv")


def catalogo(con):
    prods = []
    for p in con.execute("""
            SELECT p.*, t.nome AS time, t.slug AS time_slug, t.liga, t.raiz, t.grupo
            FROM produtos p JOIN times t ON t.id = p.time_id
            ORDER BY t.nome, p.temporada, p.uniforme"""):
        fotos = [f["arquivo"] for f in con.execute(
            "SELECT arquivo FROM fotos WHERE produto_id = ? ORDER BY ordem", (p["id"],))]
        cols = [c["slug"] for c in con.execute(
            """SELECT c.slug FROM colecoes c JOIN produto_colecao pc ON pc.colecao_id = c.id
               WHERE pc.produto_id = ? ORDER BY c.ordem""", (p["id"],))]
        prods.append({"chave": p["chave"], "time": p["time"], "time_slug": p["time_slug"],
                      "liga": p["liga"], "raiz": p["raiz"], "grupo": p["grupo"],
                      "genero": p["genero"], "categoria": p["categoria"],
                      "uniforme": p["uniforme"], "temporada": p["temporada"],
                      "versao": p["versao"], "variante": p["variante"],
                      "edicao": p["edicao"], "ano_retro": p["ano_retro"],
                      "preco": p["preco"], "fotos": fotos, "colecoes": cols})
    return prods


def bloco_fotos(prods):
    """O mesmo formato que o dados.js usa: string quando é uma foto só,
    lista quando é conjunto."""
    linhas = []
    for p in prods:
        if not p["fotos"]:
            continue
        if len(p["fotos"]) == 1:
            linhas.append(f'    "{p["chave"]}": "{p["fotos"][0]}",')
        else:
            itens = ",\n".join(f'      "{c}"' for c in p["fotos"])
            linhas.append(f'    "{p["chave"]}": [\n{itens}],')
    return "\n".join(linhas) + ("\n" if linhas else "")


def do_painel():
    """Preço, destaque e ativo saem da PLANILHA, não do banco.

    O banco é derivado: `build.py tudo` apaga e refaz a tabela de produtos, e
    qualquer preço guardado lá some junto. A planilha é o único lugar onde há
    trabalho HUMANO, então é ela a fonte. Sem o arquivo, o site sai sem preço —
    não é erro, é só a planilha ainda não ter sido baixada do Sheets."""
    if not os.path.exists(PLANILHA):
        return {}
    painel = {}
    with io.open(PLANILHA, newline="", encoding="utf-8-sig") as f:
        for l in csv.DictReader(f):
            chave = (l.get("chave") or "").strip()
            if not chave:
                continue
            try:
                preco = int(float((l.get("preco") or "").replace(",", ".")))
            except ValueError:
                preco = None
            sim = lambda v: (v or "").strip().upper() in ("SIM", "S", "X", "TRUE", "1")
            nao = (l.get("ativo") or "SIM").strip().upper() in ("NAO", "NÃO", "N", "FALSE", "0")
            painel[chave] = {"preco": preco, "destaque": sim(l.get("destaque")),
                             "ativo": not nao}
    return painel


def bloco_precos(prods):
    """Mesmo formato do bloco_fotos, um objeto à parte — o catalogo.html
    ainda não lê isso (é a tarefa seguinte); por ora é só pra não perder o
    preço no caminho entre o banco e o site."""
    linhas = [f'    "{p["chave"]}": {p["preco"]},' for p in prods if p["fotos"] and p["preco"] is not None]
    return "\n".join(linhas) + ("\n" if linhas else "")


def exportar(con):
    os.makedirs(SAIDA, exist_ok=True)
    prods = catalogo(con)

    # a planilha manda: preço, destaque e o que fica fora do site
    painel = do_painel()
    for p in prods:
        linha = painel.get(p["chave"])
        p["destaque"] = bool(linha and linha["destaque"])
        if linha and linha["preco"] is not None:
            p["preco"] = linha["preco"]
    fora = [p["chave"] for p in prods if painel.get(p["chave"], {}).get("ativo") is False]
    if fora:
        prods = [p for p in prods if p["chave"] not in set(fora)]

    io.open(os.path.join(SAIDA, "fotos-do-banco.js"), "w", encoding="utf-8").write(
        bloco_fotos(prods) +
        "\n// PRECOS — bloco à parte, ainda não lido pelo site (fica pra quando\n"
        "// o catalogo.html passar a gerar os produtos a partir do catalogo.json)\n" +
        bloco_precos(prods))
    json.dump(prods, io.open(os.path.join(SAIDA, "catalogo.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    cols = []
    for c in con.execute("SELECT * FROM colecoes ORDER BY ordem"):
        n = con.execute("SELECT COUNT(*) FROM produto_colecao WHERE colecao_id = ?",
                        (c["id"],)).fetchone()[0]
        cols.append({"slug": c["slug"], "nome": c["nome"],
                     "descricao": c["descricao"], "pecas": n})
    json.dump(cols, io.open(os.path.join(SAIDA, "colecoes.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if painel:
        com = sum(1 for p in prods if p["preco"] is not None)
        dest = sum(1 for p in prods if p["destaque"])
        print(f"   planilha: {com} com preço, {dest} em destaque"
              + (f", {len(fora)} fora do site" if fora else ""))
        if dest == 0:
            print("   AVISO: nenhuma peça em destaque. Se você marcou SIM na "
                  "coluna 'destaque' do Sheets, baixe a planilha de novo "
                  "(Arquivo > Fazer download > CSV) por cima de "
                  "planilha-precos.csv e rode este build outra vez.")
    else:
        print("   AVISO: planilha-precos.csv não encontrada — o site sai sem preço.")
    return prods, cols


if __name__ == "__main__":
    con = banco.abrir()
    prods, cols = exportar(con)
    com_foto = [p for p in prods if p["fotos"]]
    print(f"{len(com_foto)} peças com foto, {sum(len(p['fotos']) for p in com_foto)} fotos")
    print("\ncoleções:")
    for c in cols:
        print(f"  {c['nome']:24s} {c['pecas']:4d} peças")
    print(f"\ngerados em site/: fotos-do-banco.js, catalogo.json, colecoes.json")
