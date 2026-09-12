# -*- coding: utf-8 -*-
"""Enche o banco com os 217 times a partir do dados/times.json.

O times.json continua sendo a lista mestra editável à mão — acrescentar um time
lá e rodar isto de novo é como o catálogo cresce. Rodar duas vezes não duplica
nada: quem já existe é atualizado.
"""
import io, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import banco

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMES_JSON = os.path.join(AQUI, "dados", "times.json")


def semear(con):
    times = json.load(io.open(TIMES_JSON, encoding="utf-8"))
    novos = atualizados = 0
    for t in times:
        ja = con.execute("SELECT id FROM times WHERE nome = ?", (t["nome"],)).fetchone()
        campos = (t["slug"], t.get("liga"), t.get("liga_slug"), t.get("raiz"),
                  t.get("grupo"), t.get("base"))
        if ja:
            con.execute("UPDATE times SET slug=?, liga=?, liga_slug=?, raiz=?, grupo=?, "
                        "base=? WHERE nome=?", campos + (t["nome"],))
            atualizados += 1
        else:
            con.execute("INSERT INTO times (nome, slug, liga, liga_slug, raiz, grupo, base) "
                        "VALUES (?,?,?,?,?,?,?)", (t["nome"],) + campos)
            novos += 1
    con.commit()
    return novos, atualizados


if __name__ == "__main__":
    con = banco.abrir()
    novos, atual = semear(con)
    print(f"times: {novos} novos, {atual} atualizados")
    print("banco:", banco.resumo(con))
