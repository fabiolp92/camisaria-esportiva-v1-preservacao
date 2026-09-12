# -*- coding: utf-8 -*-
"""Baixa as fotos de uma categoria inteira do site do fornecedor.

    python baixar.py mulher
    python baixar.py futebol/retro retro
    python baixar.py futebol/times-espanhois espanha

O primeiro argumento é o caminho da categoria (o que vem depois de
clubsimports.com/). O segundo, opcional, é o nome da pasta local; sem ele o
script usa o último pedaço do caminho.

O resultado sai pronto pro build:

    fotos_originais/<pasta>/<nome-do-produto>/01.webp, 02.webp, ...

Pode parar no meio (Ctrl+C) e rodar de novo: peça já concluída é pulada sem nem
abrir a página. Só usa a biblioteca padrão do Python — nada pra instalar.

COMO AS FOTOS SÃO ENCONTRADAS
A loja é feita em Nuvemshop. A galeria da peça NÃO está nas tags <img> da
página — essas o navegador monta depois, e no HTML cru só aparecem as fotos dos
"produtos relacionados" lá embaixo. Pegar as <img> traria foto de outra camisa
misturada. A lista de verdade está num JSON dentro da própria página, em
"images":[...], com o nome de cada arquivo na ordem certa. É de lá que a gente
lê.
"""
import os, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

SITE = "https://www.clubsimports.com"
AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO_RAIZ = os.path.join(AQUI, "fotos_originais")
NAVEGADOR = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
PAUSA = 0.4            # segundos entre peças, pra não martelar o site
TAMANHO = "1024-1024"  # versão grande; o build depois reduz pra 35KB
MARCA_PRONTA = ".ok"   # peça só é considerada baixada quando este arquivo existe


def pegar(url, tentativas=3):
    """Baixa uma URL e devolve os bytes. Tenta de novo se a rede oscilar."""
    for n in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": NAVEGADOR})
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if n == tentativas - 1:
                raise
        except Exception:
            if n == tentativas - 1:
                raise
        time.sleep(1.5 * (n + 1))
    return None


def produtos_da_categoria(caminho, verboso=True):
    """Percorre as páginas e devolve os endereços dos produtos, sem repetir.

    Para quando uma página não traz produto NENHUM. Não dá pra parar no 404: o
    site responde 200 até na página 99, só que vazia."""
    vistos, ordem, pagina = set(), [], 1
    while True:
        url = f"{SITE}/{caminho}/" if pagina == 1 else f"{SITE}/{caminho}/page/{pagina}/"
        html = pegar(url)
        if not html:
            break
        achados = re.findall(r"https://www\.clubsimports\.com/produtos/[^\"'/]+/",
                             html.decode("utf-8", "ignore"))
        novos = [u for u in dict.fromkeys(achados) if u not in vistos]
        if not novos:
            break
        for u in novos:
            vistos.add(u)
            ordem.append(u)
        if verboso:
            print(f"\r  lendo o catálogo: página {pagina}, {len(ordem)} peças",
                  end="", flush=True)
        pagina += 1
        time.sleep(PAUSA)
    if verboso:
        print()
    return ordem


def fotos_do_produto(url):
    """Endereços das fotos grandes da peça, na ordem em que a loja mostra."""
    html = pegar(url)
    if not html:
        return []
    h = html.decode("utf-8", "ignore")

    # o caminho da loja no servidor de imagens sai da própria página
    m = re.search(r"https://acdn[^\"'\s]*?/products/", h)
    if not m:
        return []
    loja = m.group(0)

    # o PRIMEIRO bloco "images":[...] é o da peça; os de baixo são os
    # relacionados. Conta colchetes pra achar onde ele fecha.
    i = h.find('"images":[')
    if i < 0:
        return []
    inicio = i + len('"images":')
    prof, fim = 0, None
    for j in range(inicio, len(h)):
        if h[j] == "[":
            prof += 1
        elif h[j] == "]":
            prof -= 1
            if prof == 0:
                fim = j + 1
                break
    if fim is None:
        return []

    nomes = re.findall(r'"image":"([^"]+)"', h[inicio:fim])
    limpos = [re.sub(r"\.(jpg|jpeg|png|webp)$", "", n, flags=re.I) for n in nomes]
    return [f"{loja}{n}-{TAMANHO}.webp" for n in dict.fromkeys(limpos)]


def baixar_uma(args):
    destino, url = args
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return True
    try:
        dados = pegar(url)
        if not dados:
            return False
        with open(destino, "wb") as f:
            f.write(dados)
        return True
    except Exception:
        return False


def _onde_ja_esta(slug, preferida):
    """A peça já foi baixada em alguma leva? Devolve a pasta dela, ou None.

    Olha primeiro na leva atual e depois em todas as outras dentro de
    fotos_originais. Como as categorias do fornecedor se cruzam (uma retrô do
    Milan está em "Retrô" e em "Times italianos"), sem isso a mesma camisa
    seria baixada três ou quatro vezes."""
    if os.path.exists(os.path.join(preferida, MARCA_PRONTA)):
        return preferida
    if not os.path.isdir(DESTINO_RAIZ):
        return None
    for leva in sorted(os.listdir(DESTINO_RAIZ)):
        alvo = os.path.join(DESTINO_RAIZ, leva, slug)
        if os.path.exists(os.path.join(alvo, MARCA_PRONTA)):
            return alvo
    return None


def baixar_categoria(caminho, pasta=None):
    caminho = caminho.strip("/")
    pasta = pasta or caminho.split("/")[-1]
    raiz = os.path.join(DESTINO_RAIZ, pasta)
    os.makedirs(raiz, exist_ok=True)

    print(f"\nCategoria .... {caminho}")
    print(f"Salvando em .. fotos_originais\\{pasta}\n")

    urls = produtos_da_categoria(caminho)
    if not urls:
        sys.exit("Não achei produto nenhum nesse caminho.\n"
                 "Confira o endereço da categoria — é o pedaço que aparece na barra "
                 "do navegador depois de clubsimports.com/")
    print(f"  {len(urls)} peças no catálogo\n")

    baixadas = puladas = vazias = 0
    fotos_total = 0
    falhas = []
    reaproveitadas = []

    def mostrar(i):
        print(f"\r  {i}/{len(urls)}   {baixadas} baixadas · {puladas} já tinha · "
              f"{fotos_total} fotos", end="", flush=True)

    for i, url in enumerate(urls, 1):
        slug = url.rstrip("/").split("/")[-1]
        pasta_peca = os.path.join(raiz, slug)

        # peça concluída numa rodada anterior: pula sem nem abrir a página.
        # A marca .ok só é escrita quando TODAS as fotos baixaram, então uma
        # peça interrompida no meio é refeita em vez de ficar incompleta.
        #
        # Procura em TODAS as levas, não só nesta: a mesma camisa aparece em
        # "Retrô" e em "Times italianos", e baixar de novo é hora jogada fora.
        ja = _onde_ja_esta(slug, pasta_peca)
        if ja:
            if ja != pasta_peca:
                reaproveitadas.append(slug)
            pasta_peca = ja
            puladas += 1
            fotos_total += len([f for f in os.listdir(pasta_peca)
                                if f.lower().endswith(".webp")])
            mostrar(i)
            continue

        fotos = fotos_do_produto(url)
        if not fotos:
            vazias += 1
            falhas.append(slug)
        else:
            os.makedirs(pasta_peca, exist_ok=True)
            tarefas = [(os.path.join(pasta_peca, f"{n:02d}.webp"), u)
                       for n, u in enumerate(fotos, 1)]
            with ThreadPoolExecutor(max_workers=6) as ex:
                ok = list(ex.map(baixar_uma, tarefas))
            fotos_total += sum(1 for x in ok if x)
            if all(ok):
                open(os.path.join(pasta_peca, MARCA_PRONTA), "w").close()
                baixadas += 1
            else:
                falhas.append(slug)
        mostrar(i)
        time.sleep(PAUSA)

    print("\n")
    print(f"PRONTO — {baixadas + puladas} peças, {fotos_total} fotos "
          f"em fotos_originais\\{pasta}")
    if reaproveitadas:
        print(f"  ({len(reaproveitadas)} já tinham sido baixadas em outra leva "
              f"e foram aproveitadas de lá)")
    if falhas:
        print(f"\n  {len(falhas)} peças não vieram completas. Rode o mesmo comando "
              f"de novo que ele tenta só essas:")
        for s in falhas[:15]:
            print(f"    {s}")
        if len(falhas) > 15:
            print(f"    ... e mais {len(falhas) - 15}")
    print(f"\nPróximo passo:  python build.py fotos_originais\\{pasta}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: python baixar.py <categoria> [pasta]\n\n"
                 "exemplos:\n"
                 "  python baixar.py mulher\n"
                 "  python baixar.py futebol/retro retro\n"
                 "  python baixar.py futebol/times-espanhois espanha")
    baixar_categoria(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
