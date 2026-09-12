# -*- coding: utf-8 -*-
"""Põe no lugar os arquivos que o Windows extraiu dentro de subpastas.

    python instalar.py

O "Extrair tudo" do Windows cria uma pasta com o nome do zip e joga tudo lá
dentro. Como o projeto espera os arquivos na raiz, eles ficam um nível fundo
demais e nada funciona. Este script move cada um pro lugar certo.

Ele é seguro de rodar mais de uma vez: se já estiver tudo no lugar, ele diz
isso e não faz nada. E ele nunca apaga arquivo seu — só remove as pastas de
extração depois de tirar tudo de dentro.
"""
import os
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

# As pastas que o Windows cria, e o arquivo que prova que é ela mesma.
# Procuro pelo arquivo em vez de confiar no nome porque o Windows às vezes
# aninha duas vezes (camisaria-marca\camisaria-marca\...).
PACOTES = [
    ("camisaria-site-completo", "publicar.py"),
    ("camisaria-marca", "marca.py"),
]

# Onde cada coisa tem que terminar. "" quer dizer a raiz do projeto.
DESTINO = {
    "publicar.py": "", "marca.py": "", "LEIA-ME-PUBLICAR.txt": "",
    "instalar.py": None,          # None = ignora, é este próprio arquivo
}


def achar(nome_pasta, marcador):
    """Acha a pasta de extração, mesmo que o Windows tenha aninhado duas
    vezes. Devolve o caminho onde o marcador realmente está."""
    for base in (os.path.join(AQUI, nome_pasta),
                 os.path.join(AQUI, nome_pasta, nome_pasta)):
        if os.path.isfile(os.path.join(base, marcador)):
            return base
    # última tentativa: procura em qualquer subpasta de primeiro nível
    if os.path.isdir(os.path.join(AQUI, nome_pasta)):
        for d, _, arqs in os.walk(os.path.join(AQUI, nome_pasta)):
            if marcador in arqs:
                return d
    return None


def mover(origem, destino, movidos, substituidos):
    """Move um arquivo, avisando quando substitui algo que já existia."""
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if os.path.exists(destino):
        os.remove(destino)
        substituidos.append(os.path.relpath(destino, AQUI))
    else:
        movidos.append(os.path.relpath(destino, AQUI))
    shutil.move(origem, destino)


def main():
    movidos, substituidos, nao_achados = [], [], []

    for nome, marcador in PACOTES:
        base = achar(nome, marcador)
        if base is None:
            if os.path.isfile(os.path.join(AQUI, marcador)):
                print(f"   {nome}: já estava no lugar")
            else:
                nao_achados.append((nome, marcador))
            continue

        # anda pela pasta extraída inteira e recria a mesma estrutura na raiz
        for pasta, _, arquivos in os.walk(base):
            relativo = os.path.relpath(pasta, base)
            relativo = "" if relativo == "." else relativo
            for arq in arquivos:
                if DESTINO.get(arq, "não listado") is None:
                    continue
                mover(os.path.join(pasta, arq),
                      os.path.join(AQUI, relativo, arq),
                      movidos, substituidos)

        # a pasta de extração agora só tem esqueleto vazio
        shutil.rmtree(os.path.join(AQUI, nome), ignore_errors=True)
        print(f"   {nome}: desmontada")

    if nao_achados:
        print("\nNão achei estas pastas:")
        for nome, marcador in nao_achados:
            print(f"   {nome}  (procurei por {marcador} dentro dela)")
        print("Extraia os .zip antes de rodar isto.")

    print(f"\n{len(movidos)} arquivos novos, {len(substituidos)} substituídos")
    if substituidos:
        print("\nSubstituídos (era a versão antiga, agora é a nova):")
        for s in sorted(substituidos):
            print(f"   {s}")

    # ---------------------------------------------------- conferência
    # De nada adianta mover se faltar peça. Aqui eu confiro que tudo que o
    # publicar.py vai precisar está mesmo onde ele espera.
    precisa = [
        "publicar.py", "marca.py", "LEIA-ME-PUBLICAR.txt",
        "scripts/paginas.py", "scripts/exportar.py", "scripts/banco.py",
        "scripts/importar.py", "scripts/fornecedor.py", "scripts/imagens.py",
        "web/index.html", "web/catalogo.html", "web/nav.js", "web/pagina.css",
        "web/marca-ce.png", "web/favicon.ico", "web/capa-camisaria-esportiva.jpg",
        "arte/marca-banner.jpg", "arte/marca-larga.jpg", "arte/marca-quadrada.jpg",
        "build.py", "planilha-precos.csv", "site/catalogo.json",
    ]
    faltando = [p for p in precisa
                if not os.path.exists(os.path.join(AQUI, p.replace("/", os.sep)))]

    print()
    if faltando:
        print("FALTANDO — o publicar.py não vai rodar sem isto:")
        for f in faltando:
            print(f"   {f}")
        print("\nMe mande esta lista que eu reenvio o que faltou.")
        return 1

    print("Está tudo no lugar. Pode seguir:")
    print("    python build.py tudo")
    print("    python publicar.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
