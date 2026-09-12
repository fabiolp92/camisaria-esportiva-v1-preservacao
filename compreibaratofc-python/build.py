# -*- coding: utf-8 -*-
"""Roda o projeto inteiro, na ordem certa.

    python build.py tudo                        # importa TODAS as levas de uma vez
    python build.py fotos_originais/criancas1   # importa uma leva só
    python build.py                             # só reconstrói a partir do banco

"tudo" é o de sempre: ele acha sozinho cada pasta dentro de fotos_originais e
importa uma por uma, na ordem alfabética. Como foto já comprimida não é
comprimida de novo, rodar "tudo" depois de acrescentar uma leva nova custa o
tempo só da leva nova.

O `if __name__ == "__main__"` lá embaixo NÃO é enfeite: a compressão roda em
vários processos, e no Windows cada processo filho reimporta este arquivo. Sem a
guarda, cada filho começaria um build novo, e um build começaria outros, sem fim.
"""
import os, sys, time
from scripts import banco, semear, exportar, importar

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGINAIS = os.path.join(AQUI, "fotos_originais")


def levas_pedidas(args):
    """Quais pastas importar, a partir do que veio na linha de comando."""
    if not args:
        return []
    if len(args) == 1 and args[0].lower() in ("tudo", "todas", "all"):
        if not os.path.isdir(ORIGINAIS):
            sys.exit("nao achei a pasta fotos_originais")
        return [os.path.join(ORIGINAIS, d) for d in sorted(os.listdir(ORIGINAIS))
                if os.path.isdir(os.path.join(ORIGINAIS, d))]
    pastas = []
    for a in args:
        p = os.path.abspath(a)
        if not os.path.isdir(p):
            sys.exit(f"nao achei a pasta {p}")
        pastas.append(p)
    return pastas


def limpar_fotos_orfas(con):
    """Apaga de site/fotos os arquivos que nenhum produto usa mais.

    Aparecem quando uma peça troca de nome (ganha um rótulo, por exemplo) e o
    arquivo antigo fica órfão. São arquivos derivados: se um dia sumir por
    engano, o build gera de novo a partir de fotos_originais."""
    pasta = os.path.join(AQUI, "site", "fotos")
    if not os.path.isdir(pasta):
        return 0
    usados = {os.path.basename(r["arquivo"])
              for r in con.execute("SELECT arquivo FROM fotos")}
    apagados = 0
    for f in os.listdir(pasta):
        if f.lower().endswith(".webp") and f not in usados:
            try:
                os.remove(os.path.join(pasta, f)); apagados += 1
            except OSError:
                pass
    return apagados


def main():
    inicio = time.time()
    con = banco.abrir()
    n, a = semear.semear(con)
    print(f"1. times ......... {n} novos, {a} atualizados")

    pastas = levas_pedidas(sys.argv[1:])
    tudo = bool(sys.argv[1:]) and sys.argv[1].lower() in ("tudo", "todas", "all")
    if tudo and pastas:
        # "tudo" reconstrói o catálogo inteiro, então começa do zero. Sem isso
        # sobram fantasmas: quando uma peça troca de rótulo ela vira um produto
        # novo e o antigo fica no banco pra sempre. Foi o que fez a importação
        # dizer 271 peças e o banco 278. As fotos no disco são reaproveitadas,
        # então limpar aqui não custa tempo nenhum.
        con.execute("DELETE FROM produto_colecao")
        con.execute("DELETE FROM fotos")
        con.execute("DELETE FROM produtos")
        con.commit()
    if not pastas:
        print("2. importacao .... pulada (nenhuma pasta informada)")
    else:
        relatorios, tot_p, tot_f, tot_x = [], 0, 0, 0
        for i, pasta in enumerate(pastas, 1):
            nome = os.path.basename(pasta)
            print(f"\n2.{i} {nome}")
            finais, fora, tam, tempos = importar.importar(con, pasta)
            print(f"   {len(finais)} pecas, {len(tam)} fotos, {len(fora)} de fora")
            tot_p += len(finais); tot_f += len(tam); tot_x += len(fora)
            relatorios.append(f"{'='*70}\nLEVA: {nome}\n{'='*70}\n"
                              + importar.relatorio(finais, fora, tam, tempos))
        if len(pastas) > 1:
            print(f"\n2. importacao .... {tot_p} pecas, {tot_f} fotos, "
                  f"{tot_x} de fora, em {len(pastas)} levas")
        with open(os.path.join(AQUI, "relatorio-importacao.txt"),
                  "w", encoding="utf-8") as f:
            f.write("\n\n".join(relatorios))

    if tudo:
        n = limpar_fotos_orfas(con)
        if n:
            print(f"   ({n} fotos antigas removidas de site/fotos)")

    prods, cols = exportar.exportar(con)
    print(f"3. exportacao .... {len([p for p in prods if p['fotos']])} pecas com foto")
    print()
    r = banco.resumo(con)
    print(f"banco: {r['times']} times | {r['produtos']} produtos | {r['fotos']} fotos "
          f"| {r['peso_fotos_mb']:.1f} MB")
    print(f"tempo total: {time.time() - inicio:.0f}s")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Ctrl+C não é erro: o que já foi comprimido continua valendo, e a
        # próxima rodada pega do ponto onde parou.
        print("\n\nParado por você. Nada foi perdido — as fotos já comprimidas")
        print("continuam prontas. Rode o mesmo comando pra continuar de onde parou.")
        raise SystemExit(0)
