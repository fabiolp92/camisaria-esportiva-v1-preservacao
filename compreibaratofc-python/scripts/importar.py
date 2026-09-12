# -*- coding: utf-8 -*-
"""Lê uma pasta de fotos do fornecedor, otimiza tudo e grava no banco.

    python scripts/importar.py fotos_originais/criancas1

Cada subpasta é uma peça; os arquivos dentro dela são o conjunto de fotos
daquela peça, na ordem do nome. O script:
  1. descobre time/gênero/uniforme/temporada pelo nome da pasta
  2. comprime cada foto pra ~35KB em WebP
  3. grava em site/fotos/ com o nome do padrão
  4. registra produto, fotos e coleções no banco

Rodar de novo com a mesma pasta atualiza em vez de duplicar. E é RÁPIDO: foto que
não mudou de origem não é recomprimida (cache em site/.cache-fotos.json), e o que
sobra roda em todos os núcleos do processador ao mesmo tempo.
"""
import os, re, sys, json, time, collections, unicodedata
from concurrent.futures import ProcessPoolExecutor
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import banco, fornecedor, imagens

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA_FOTOS = os.path.join(AQUI, "site", "fotos")
CACHE = os.path.join(AQUI, "site", ".cache-fotos.json")
EXTENSOES = (".webp", ".jpg", ".jpeg", ".png")


# --------------------------------------------------------------- nome do arquivo
def _pedaco(texto):
    """Vira pedaço de nome de arquivo: sem acento, sem espaço, minúsculo."""
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def nome_de_arquivo(time_slug, item, ordem, total):
    """<time>-<genero>-<temporada>-<uniforme>-<versao>[-<variante>][-N].webp

    O nome carrega a peça inteira, então é o mesmo no GitHub (tudo plano) e na
    árvore de pastas do Desktop. Trocar uma foto é sempre 'mesmo nome'."""
    partes = [time_slug, item["genero"]]
    # O tipo da peça entra no nome do arquivo pelo mesmo motivo que entra na
    # chave: a jaqueta retrô da Alemanha 1990, a regata retrô e o calção retrô
    # são três peças, e sem isso as três gravavam no mesmo arquivo.
    if item["categoria"] not in ("camisa", "kit"):
        partes.append(item["categoria"])
    partes += [item["temporada"] or "retro", item["uniforme"]]
    if item["uniforme"] == "retro":
        # sem isso, Real Madrid 11-12, 17-18 e 17-18-II geram o MESMO nome de
        # arquivo (time+genero+"retro"+"retro") e uma sobrescreve a foto da
        # outra em silêncio — o ano e o uniforme-base é o que distingue.
        if item.get("ano_retro"):
            partes.append(item["ano_retro"])
        if item.get("uniforme_base") and item["uniforme_base"] != "uniforme1":
            partes.append(item["uniforme_base"])
    if item["versao"]:
        partes.append(item["versao"])
    if item["variante"]:
        partes.append(item["variante"])
    # O rótulo de edição entra na CHAVE do catálogo, então tem que entrar no
    # nome do arquivo também. Sem isso a Flamengo titular e a Flamengo preta
    # gravam no mesmo arquivo e uma apaga a foto da outra.
    if item.get("rotulo_edicao"):
        partes.append(_pedaco(item["rotulo_edicao"]))
    base = "-".join(partes)
    if total > 1:
        base += f"-{ordem}"
    return base + ".webp"


# ---------------------------------------------------------------------- cache
def _ler_cache():
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}          # cache é derivado: se sumir ou corromper, recomprime tudo


def _gravar_cache(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=1)


def _assinatura(origem, alvo_kb):
    st = os.stat(origem)
    return {"origem": os.path.basename(os.path.dirname(origem)) + "/" + os.path.basename(origem),
            "mtime": int(st.st_mtime), "origem_bytes": st.st_size, "alvo_kb": alvo_kb}


def _cache_vale(entrada, assin, destino):
    """Só reaproveita se a foto de origem for a MESMA (nome, data, tamanho), o
    alvo de KB for o mesmo, o arquivo de destino existir e tiver exatamente o
    tamanho que ficou registrado. Qualquer diferença: recomprime."""
    if not entrada:
        return False
    for k in ("origem", "mtime", "origem_bytes", "alvo_kb"):
        if entrada.get(k) != assin[k]:
            return False
    try:
        return os.path.getsize(destino) == entrada.get("bytes")
    except OSError:
        return False


# ------------------------------------------------------------------ compressão
# Palavras que descrevem a peça ou a loja, nunca a diferença entre duas
# camisas. Sem esta lista a Portugal titular virava "Seleção Copa Mundo".
PALAVRAS_VAZIAS = {
    "camisa", "camisas", "cropped", "short", "kit", "conjunto", "selecao",
    "copa", "mundo", "feminina", "feminino", "masculino", "infantil",
    "oficial", "uniforme", "reserva", "titular", "jogador", "torcedor",
    "adidas", "puma", "nike", "umbro", "edicao", "especial", "the", "com",
    "retro", "retrô", "oficial",
    # ligação e palavras de anúncio que sozinhas não distinguem nada — sem elas
    # o rótulo saía "Viagem De Do" e "Edição Especial · Alemanha Do"
    "de", "do", "da", "dos", "das", "e", "em", "para", "por",
    "viagem", "treino", "limitada", "comemorativa", "casaco", "jaqueta",
    "polo", "regata", "calcao", "moletom", "agasalho", "reebok", "kappa",
    "anos", "icons", "edicoes", "tang", "hummel", "futebol", "espanhol",
    # o "x" das colaborações ("x-louis-vuitton") nunca distingue sozinho
    "x",
    # palavras de uniforme: já viraram 1º/2º/3º na classificação, então repetir
    # aqui só produzia rótulo feio ("Iii Rosa", "Terceira Rosa")
    "ii", "iii", "iv", "terceira", "third", "away", "home", "titular", "reserva",
    # marketing e palavras que a chave já carrega ("Versão Jogador", "Pré-Jogo")
    "pre", "jogo", "versao", "player", "lancamento", "atleta", "mizuno",
    "socio", "tecnica", "fc", "afc", "cf", "sc", "ud", "cp", "sp",
}
# o nome do próprio time também não distingue duas peças DO MESMO time — ele é
# comum às duas por definição, mesmo quando escrito de formas diferentes
# ("selecao-alemanha" numa pasta e "alemanha" na outra).

# Palavras DE VERDADE com cara de código: cinco letras, sem número, no fim do
# nome. É a lista que protege a "Flamengo Preta" de virar cópia da titular.
# Toda cor entra aqui — é o caso real que aparece; um código nunca é uma cor.
PALAVRAS_QUE_PARECEM_CODIGO = {
    "preta", "preto", "verde", "creme", "areia", "vinho", "lilas", "salmao",
    "icons", "retro", "betis", "gola", "kobe", "lasso", "oasis", "zico",
    "messi", "pele", "liga", "casa", "fora", "nova", "velha",
}


# Códigos que parecem palavra mas são lixo do fornecedor. Uma linha por caso,
# acrescentada quando o relatório aponta. É mais honesto que uma regra esperta:
# "pyeii" e "preta" têm exatamente a mesma cara, só o significado separa.
CODIGOS_CONHECIDOS = {"pyeii", "gpe9r", "uapjw", "hxgdz", "chlbl",
                      "wbohd", "tmwsn", "shxiv", "gqyru", "xfvtp", "iosbp",
                      "tmykx", "nbrkl", "ngbra", "tdfbu", "rrsjo", "azypt"}


# Como o fornecedor abrevia cada time. "psg" e "Paris Saint-Germain" são a
# mesma coisa, então "psg" também não distingue duas peças do PSG — sem isto o
# rótulo saía "Edição Especial · Psg".
# Só entram os apelidos CURTOS (até duas palavras): são as siglas — "psg",
# "sl-benfica", "as-monaco". Apelidos longos como "selecao-alemanha-azul"
# carregam descrição junto, e o "azul" ali é a cor da camisa — a diferença
# entre duas peças de verdade. Deixar entrar apagaria essa diferença.
_PEDACOS_DO_TIME = {}
for _apelido, _alvo in fornecedor.APELIDOS.items():
    _partes = _apelido.split("-")
    if len(_partes) <= 2:
        _PEDACOS_DO_TIME.setdefault(_alvo, set()).update(_partes)


def _palavras_que_distinguem(pasta, comuns, nome_do_time=None):
    """O que esta pasta tem de próprio, em relação às outras do mesmo grupo.

    O nome do time nunca distingue duas peças DO MESMO time — ele é comum às
    duas por definição, mesmo quando o fornecedor escreve de jeitos diferentes
    ("selecao-alemanha" numa pasta e "alemanha" na outra). Sem isso o rótulo
    saía "Edição Especial · Alemanha"."""
    do_time = set()
    if nome_do_time:
        do_time = set(_pedaco(nome_do_time).split("-"))
        do_time |= _PEDACOS_DO_TIME.get(nome_do_time, set())
    # guarda a POSIÇÃO de cada palavra: sem isso "st-patricks-day" saía como
    # "Patricks Day St", porque o "st" era jogado pro fim da lista
    saida, curtos = [], []
    fim = pasta.split("-")[-1]
    for pos, t in enumerate(pasta.split("-")):
        if t in comuns or t.isdigit():
            continue
        # a ORDEM importa: primeiro o token inteiro, porque "npnx9" só é
        # reconhecido como código enquanto tem o dígito. Só depois tira o
        # dígito de cópia, senão "jogador1" escapa e vira o rótulo "· Jogador".
        if t in do_time or t in PALAVRAS_VAZIAS or t in CODIGOS_CONHECIDOS \
                or _codigo_aleatorio(t):
            continue
        # O código que o fornecedor gruda ao republicar às vezes vem só com
        # letras ("iwwli", "qwpeh", "mttqn") e escapava do teste acima, que
        # exige um número. Só vale para o ÚLTIMO pedaço do nome — é onde ele
        # sempre fica — e nunca para as palavras de verdade da lista acima.
        # Isto muda só o RÓTULO; quem decide o que é cópia é o _mesma_pasta.
        if (t is not None and t == fim and len(t) == 5 and t.isalpha()
                and t not in PALAVRAS_QUE_PARECEM_CODIGO):
            continue
        # ...mas o dígito só sai se sobrar palavra: em "cr7" ele FAZ PARTE do
        # nome, e tirá-lo deixava "cr", que era descartado como token curto —
        # foi assim que a Edição Especial CR7 de Portugal virou cópia da comum.
        sem_digito = re.sub(r"\d+$", "", t)
        if len(sem_digito) > 2:
            t = sem_digito
        if t in do_time or t in PALAVRAS_VAZIAS or t in CODIGOS_CONHECIDOS:
            continue
        if len(t) <= 2:
            # "gola-v": o "v" sozinho não diz nada, mas colado no "gola" diz.
            # Só entra se já houver uma palavra de verdade antes dele.
            curtos.append((pos, t))
            continue
        saida.append((pos, t))
    if saida:
        saida += [(pos, t) for pos, t in curtos if t.isalpha()]
    return [t for _, t in sorted(saida)]


def _codigo_aleatorio(t):
    """'e6moy', '1xaz4', 'gt4xh' — o código que o fornecedor gruda no fim de
    alguns endereços. Serve pra não virar nome de edição no catálogo. Aqui dá
    pra exigir um dígito, porque errar só deixa o rótulo feio, não apaga peça."""
    return (len(t) == 5 and t.isalnum()
            and any(c.isdigit() for c in t) and any(c.isalpha() for c in t))


def _mesma_pasta(a, b):
    """As duas pastas são o MESMO anúncio republicado?

    É cópia quando a única diferença entre os dois endereços é um dígito
    colado no fim ("...-25-26" e "...-25-261") ou o código aleatório que o
    fornecedor gruda ao republicar ("...-1472t" e "...-111wx").

    NÃO é cópia quando sobra uma palavra de verdade: "...-26-27-1c5ux" e
    "...-26-27-preta" são a titular e a preta, duas camisas. Antes desta regra
    a preta era apagada em silêncio, porque "preta" tem a mesma cara de um
    código. Na dúvida o catálogo fica com uma peça a mais — que aparece no
    relatório — em vez de perder uma de verdade."""
    def limpo(x):
        # tira o código ANTES do dígito solto: em "…-gzxl7" o 7 final faz
        # parte do código, e cortá-lo primeiro descaracterizava o resto
        sem = "-".join(t for t in x.split("-") if t and not _codigo_aleatorio(t))
        return re.sub(r"\d+$", "", sem).strip("-")
    return limpo(a) == limpo(b)


def _adotar_do_disco(destino, origem, alvo_kb):
    """A foto já está pronta no disco? Devolve (bytes, largura) ou None.

    Vale quando o arquivo de destino existe, não está vazio, é mais novo que a
    foto de origem e cabe no alvo de KB. É a mesma regra que qualquer
    ferramenta de build usa: se o resultado é mais recente que a matéria-prima,
    não precisa refazer."""
    try:
        if not os.path.exists(destino):
            return None
        b = os.path.getsize(destino)
        if b == 0 or b > alvo_kb * 1024 * 1.10:
            return None
        if os.path.getmtime(destino) < os.path.getmtime(origem):
            return None
        with Image.open(destino) as im:
            return b, im.width
    except Exception:
        return None


def _silenciar_ctrl_c():
    """Roda em cada processo filho: faz o Ctrl+C ser tratado só pelo processo
    principal, em vez de cada filho cuspir a própria pilha de erro na tela."""
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def comprimir_uma(args):
    """Roda dentro dos processos paralelos, então precisa estar aqui fora.

    Nunca levanta erro: uma foto quebrada (arquivo vazio, download pela metade,
    formato estranho) tem que custar UMA foto, não a importação inteira. O erro
    volta como texto e vira uma linha no relatório."""
    origem, destino, alvo_kb = args
    try:
        b, w = imagens.comprimir(origem, destino, alvo_kb)
        return destino, b, w, None
    except Exception as e:
        return destino, None, None, f"{type(e).__name__}: {e}"


def _comprimir_lote(tarefas, ja_feitas, total, verboso):
    """Distribui a compressão entre os núcleos. Se o paralelo falhar por qualquer
    motivo, cai pra um processo só em vez de abortar a importação."""
    saida, erros, feitas = {}, {}, ja_feitas

    def _guardar(destino, b, w, err):
        if err:
            erros[destino] = err
        else:
            saida[destino] = (b, w)

    def _conta():
        if verboso:
            print(f"\r  {feitas}/{total} fotos", end="", flush=True)

    nucleos = min(len(tarefas), os.cpu_count() or 1)
    if nucleos > 1:
        try:
            with ProcessPoolExecutor(max_workers=nucleos,
                                     initializer=_silenciar_ctrl_c) as ex:
                for destino, b, w, err in ex.map(comprimir_uma, tarefas, chunksize=4):
                    _guardar(destino, b, w, err)
                    feitas += 1
                    _conta()
            return saida, erros
        except Exception as e:
            print(f"\n  (paralelo não rolou: {e} — seguindo em um processo só)")
            saida.clear(); erros.clear()
            feitas = ja_feitas

    for t in tarefas:
        destino, b, w, err = comprimir_uma(t)
        _guardar(destino, b, w, err)
        feitas += 1
        _conta()
    return saida, erros


# ------------------------------------------------------------------- importação
# ------------------------------------------------------- duplicatas do fornecedor
def resolver_duplicatas(itens):
    """Decide o que é peça de verdade e o que é anúncio republicado.

    Fica fora de importar() de propósito: assim dá pra rodar esta mesma
    decisão sobre uma lista de nomes de pasta, sem tocar em foto nenhuma, e
    conferir uma leva nova ANTES de comprimir as primeiras 5.000 fotos."""
    # duas pastas descrevendo a MESMA peça: fica a que tem mais fotos.
    # ano_retro e uniforme_base entram na chave por causa das retros: sem eles,
    # Real Madrid 11-12, 17-18 e 17-18-II (três anos/uniformes diferentes)
    # pareceriam a MESMA peça e duas delas seriam descartadas como cópia.
    def _chave_dedup(i):
        return (i["time"], i["genero"], i["categoria"], i["uniforme"],
                i["temporada"], i["versao"], i["variante"],
                i["ano_retro"], i["uniforme_base"])

    bons = [i for i in itens if not i["fora"]]
    grupos = collections.defaultdict(list)
    for i in bons:
        grupos[_chave_dedup(i)].append(i)

    finais = []
    for grupo in grupos.values():
        if len(grupo) == 1:
            finais.append(grupo[0])
            continue
        # Duas ou mais pastas descrevendo a mesma coisa. Só é cópia de verdade
        # quando os NOMES das pastas são praticamente iguais (o fornecedor
        # republica o anúncio e muda um dígito ou um código no fim). Quando os
        # nomes diferem de fato — "flamengo-feminina-26-27" e
        # "flamengo-feminina-26-27-preta" — são camisas DIFERENTES, e descartar
        # uma seria perda silenciosa. Nesse caso a palavra que as separa vira
        # o rótulo da peça, e o relatório pede conferência do texto.
        comuns = set(grupo[0]["pasta"].split("-"))
        for i in grupo[1:]:
            comuns &= set(i["pasta"].split("-"))
        for i in grupo:
            i["_extra"] = _palavras_que_distinguem(i["pasta"], comuns, i["time"])

        # A peça BASE é a que não tem palavra própria — é a versão normal, e
        # fica com o nome limpo. As outras é que ganham rótulo. Escolher pela
        # quantidade de fotos, como eu fazia antes, dava o contrário: a "Zico"
        # virava base e a Edição Especial comum era descartada.
        base = min(grupo, key=lambda i: (len(i["_extra"]), -len(i["arquivos"])))
        finais.append(base)

        # As comparações são contra TUDO que já ficou do grupo, não só contra a
        # base. Três anúncios "Alemanha Edição Especial" em que o 2º e o 3º são
        # idênticos entre si mas diferentes da base: comparando só com a base,
        # os dois passavam e geravam a mesma chave.
        mantidos = [base]
        for i in grupo:
            if i is base:
                continue
            # Sem palavra própria = mesmo anúncio republicado com um código
            # diferente no fim. Inventar rótulo aqui produzia "· 27", "· E6Moy".
            # O rótulo do grupo SOMA ao que a peça já tinha, nunca substitui.
            # Substituindo, a "Goleiro Manga Longa" perdia o "Goleiro" e virava
            # só "Manga Longa" — batendo de frente com a manga longa comum.
            ja = set(_pedaco(i.get("rotulo_edicao") or "").split("-"))
            novos = [t for t in i["_extra"] if t not in ja]
            # Sem palavra nova E com o MESMO rótulo da base = o mesmo anúncio
            # republicado. Antes eu só olhava se a peça tinha rótulo, e aí as
            # sete "Inglaterra Edição Especial" passavam todas, com a mesma
            # chave — e a trava 2 derrubava a importação inteira. Rótulo
            # DIFERENTE continua sendo peça diferente e é preservado.
            if novos:
                # "cr7" vira "CR7" e não "Cr7": palavra com número é sigla
                txt = " ".join(w.upper() if any(c.isdigit() for c in w)
                               else w.title() for w in novos)
                antes = i.get("rotulo_edicao")
                rotulo = f"{antes} · {txt}" if antes else txt
            else:
                rotulo = i.get("rotulo_edicao")

            copia = any(_mesma_pasta(i["pasta"], m["pasta"])
                        or (rotulo or "") == (m.get("rotulo_edicao") or "")
                        for m in mantidos)
            if copia:
                i["fora"] = "cópia de outra pasta igual, com menos fotos"
            else:
                if rotulo != i.get("rotulo_edicao"):
                    i["rotulo_edicao"] = rotulo
                    i["aviso_rotulo"] = True
                finais.append(i)
                mantidos.append(i)

    return finais


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

    finais = resolver_duplicatas(itens)

    finais.sort(key=lambda i: (i["time"], i["temporada"] or "", i["uniforme"]))

    # Trava 1: nenhum item pode citar um time que não está no banco. Conferir
    # ANTES de comprimir a primeira foto evita parar no meio da importação.
    fantasmas = sorted({i["time"] for i in finais if i["time"] not in times})
    if fantasmas:
        raise SystemExit("Estes times não existem no times.json: " + ", ".join(fantasmas) +
                         "\nNenhuma foto foi gravada.")

    # Trava 2: duas peças DIFERENTES nunca podem gerar a mesma chave de catálogo.
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

    # Trava 3: e nunca podem gerar o mesmo NOME DE ARQUIVO — que é outro jeito de
    # uma peça apagar a foto da outra, e a trava 2 não pega.
    pornome = collections.defaultdict(list)
    for i in finais:
        t = times[i["time"]]
        n = len(i["arquivos"])
        for k in range(1, n + 1):
            pornome[nome_de_arquivo(t["slug"], i, k, n)].append(i["pasta"])
    colididos = {k: v for k, v in pornome.items() if len(set(v)) > 1}
    if colididos:
        linhas = ["Duas peças diferentes geraram o mesmo nome de arquivo.",
                  "Nenhuma foto foi gravada. Me mande esta lista:"]
        for k, v in sorted(colididos.items()):
            linhas.append(f"  {k}")
            linhas += [f"      {p}" for p in sorted(set(v))]
        raise SystemExit("\n".join(linhas))

    # --- 1. produtos e coleções primeiro (rápido, sem tocar em imagem)
    trabalhos = []          # (item, pid, ordem, total, origem, destino, nome)
    for item in finais:
        t = times[item["time"]]
        chave = fornecedor.chave_do_produto(item)
        con.execute("""INSERT INTO produtos (time_id, genero, categoria, uniforme,
                          temporada, versao, variante, edicao, ano_retro, chave)
                       VALUES (?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(chave) DO UPDATE SET time_id=excluded.time_id,
                          edicao=excluded.edicao""",
                    (t["id"], item["genero"], item["categoria"], item["uniforme"],
                     item["temporada"], item["versao"], item["variante"],
                     item.get("rotulo_edicao"), item.get("ano_retro"), chave))
        pid = con.execute("SELECT id FROM produtos WHERE chave = ?", (chave,)).fetchone()["id"]
        con.execute("DELETE FROM fotos WHERE produto_id = ?", (pid,))
        con.execute("DELETE FROM produto_colecao WHERE produto_id = ?", (pid,))
        for slug in fornecedor.colecoes_do_produto(item, t):
            if slug in colecoes:
                con.execute("INSERT OR IGNORE INTO produto_colecao VALUES (?,?)",
                            (pid, colecoes[slug]))

        n_total = len(item["arquivos"])
        for n, arq in enumerate(item["arquivos"], 1):
            nome = nome_de_arquivo(t["slug"], item, n, n_total)
            trabalhos.append((item, pid, n, n_total, nome,
                              os.path.join(pasta_raiz, item["pasta"], arq),
                              os.path.join(SAIDA_FOTOS, nome), arq))

    # --- 2. separa o que já está pronto do que precisa comprimir
    cache = _ler_cache()
    # Começa do cache que já existe. Antes começava vazio e gravava por cima:
    # importar "mulher" apagava as 670 fotos de "criancas1" do cache, e o build
    # seguinte recomprimia tudo do zero. Foi o que queimou uma rodada inteira.
    novo_cache, prontos, tarefas = dict(cache), {}, []
    for (item, pid, n, n_total, nome, origem, destino, arq) in trabalhos:
        assin = _assinatura(origem, alvo_kb)
        ent = cache.get(nome)
        if _cache_vale(ent, assin, destino):
            prontos[destino] = (ent["bytes"], ent["largura"])
            novo_cache[nome] = ent
            continue
        # Sem registro no cache, mas o arquivo está lá e é mais novo que a foto
        # de origem: foi comprimido numa rodada anterior e o registro se perdeu.
        # Recomprimir seria jogar minutos fora pra chegar no mesmo arquivo.
        pronto = _adotar_do_disco(destino, origem, alvo_kb)
        if pronto:
            prontos[destino] = pronto
            e = dict(assin); e["bytes"], e["largura"] = pronto
            novo_cache[nome] = e
            continue
        tarefas.append((origem, destino, alvo_kb))

    total = len(trabalhos)
    if verboso:
        print(f"  {len(prontos)} fotos já prontas (cache), {len(tarefas)} para comprimir")

    t0 = time.time()
    feitos, erros = _comprimir_lote(tarefas, len(prontos), total, verboso) if tarefas else ({}, {})
    if verboso and total:
        print()
    segundos = time.time() - t0

    # --- 3. grava as linhas das fotos no banco (aqui, na thread principal)
    tamanhos, fotos_ruins = [], []
    for (item, pid, n, n_total, nome, origem, destino, arq) in trabalhos:
        r = prontos.get(destino) or feitos.get(destino)
        if r is None:
            fotos_ruins.append((f"{item['pasta']}/{arq}", erros.get(destino, "não comprimiu")))
            continue
        b, w = r
        tamanhos.append(b)
        con.execute("""INSERT INTO fotos (produto_id, arquivo, ordem, bytes, largura, origem)
                       VALUES (?,?,?,?,?,?)""",
                    (pid, f"fotos/{nome}", n, b, w, f"{item['pasta']}/{arq}"))
        if nome not in novo_cache:
            e = _assinatura(origem, alvo_kb); e["bytes"] = b; e["largura"] = w
            novo_cache[nome] = e

    con.commit()
    _gravar_cache(novo_cache)
    return finais, [i for i in itens if i["fora"]], tamanhos, {
        "cache": len(prontos), "comprimidas": len(tarefas) - len(fotos_ruins),
        "segundos": segundos, "fotos_ruins": fotos_ruins}


# -------------------------------------------------------------------- relatório
def _rotulo(i):
    """Como a peça aparece no relatório: uniforme + ano da retrô + edição."""
    if i["uniforme"] == "retro":
        r = "Retrô " + (i.get("ano_retro") or "").replace("-", "/")
        base = i.get("uniforme_base")
        if base and base != "uniforme1":
            r += " " + fornecedor.ROTULO_UNIFORME.get(base, base)
    else:
        r = fornecedor.ROTULO_UNIFORME.get(i["uniforme"], i["uniforme"])
    if i.get("rotulo_edicao"):
        r += " · " + i["rotulo_edicao"]
    # sem isso um Cropped e uma camisa do mesmo time viram duas linhas iguais
    # no relatório, e não dá pra conferir de olho qual é qual
    extra = {"kit": "Kit", "calcao": "Calção", "cropped": "Cropped",
             "jaqueta": "Jaqueta"}.get(i["categoria"])
    if extra:
        r = f"{extra} · {r}"
    return r.strip()


def relatorio(finais, fora, tamanhos, tempos=None):
    linhas = [f"IMPORTAÇÃO — {len(finais) + len(fora)} pastas",
              f"  entraram: {len(finais)} peças, {len(tamanhos)} fotos"]
    if tamanhos:
        linhas.append(f"  peso médio {sum(tamanhos)/len(tamanhos)/1024:.1f} KB "
                      f"(maior {max(tamanhos)/1024:.1f} KB), "
                      f"total {sum(tamanhos)/1024/1024:.1f} MB")
    if tempos:
        linhas.append(f"  {tempos['comprimidas']} comprimidas e {tempos['cache']} "
                      f"reaproveitadas do cache, em {tempos['segundos']:.0f}s")
    linhas.append("")
    for i in finais:
        temp = "" if i["uniforme"] == "retro" else (i["temporada"] or "")
        # Preço não aparece aqui de propósito: foto é foto. Quem define preço
        # é a planilha, e misturar os dois só cria número errado no relatório.
        linhas.append(f"  {i['time']:24s} {i['genero']:9s} {_rotulo(i):40s} "
                      f"{temp:6s} ({len(i['arquivos'])} fotos)")

    ruins = (tempos or {}).get("fotos_ruins") or []
    if ruins:
        linhas += ["", f"FOTOS QUE NÃO ABRIRAM: {len(ruins)}",
                   "  (a peça entrou mesmo assim, só sem esta foto)"]
        for caminho, erro in ruins:
            linhas.append(f"    {caminho:62s} -> {erro}")

    avisos = [i for i in finais if i.get("aviso_rotulo")]
    if avisos:
        linhas += ["", f"VARIANTES SEM RÓTULO — confira o texto: {len(avisos)}"]
        for i in avisos:
            linhas.append(f"    {i['pasta']:62s} -> variante '{i['variante']}' "
                          f"virou rótulo \"{i['rotulo_edicao']}\"")

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
    finais, fora, tamanhos, tempos = importar(con, pasta)
    texto = relatorio(finais, fora, tamanhos, tempos)
    with open(os.path.join(AQUI, "relatorio-importacao.txt"), "w", encoding="utf-8") as f:
        f.write(texto)
    print(texto[:texto.index("\n\n")] if "\n\n" in texto else texto)
    print("\nrelatório completo em relatorio-importacao.txt")
    print("banco:", banco.resumo(con))
