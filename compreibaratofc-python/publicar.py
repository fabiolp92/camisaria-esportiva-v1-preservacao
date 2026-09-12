# -*- coding: utf-8 -*-
"""Monta a pasta pronta para subir no Hostgator.

    python build.py tudo      (antes, pra o catalogo.json estar em dia)
    python publicar.py        (depois)

O que ele faz, em ordem:
  1. lê  site/catalogo.json      — as 2.597 peças, com preço e destaque
  2. gera publicar/acervo.json   — o mesmo catálogo, mas enxuto pro navegador
  3. gera publicar/dados.js      — a lista de times que o menu do site usa
  4. copia web/                  — as páginas, o CSS, os ícones
  5. copia site/fotos/           — só as fotos que o site vai mostrar
  6. gera .htaccess e sitemap.xml
  7. avisa o tamanho da pasta e o que mudou desde a última vez

Nada aqui apaga nada seu: a pasta publicar/ é descartável, dá pra apagar e
gerar de novo quando quiser.
"""
import io
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts import cobica

# ---------------------------------------------------------------- AJUSTES
# Quantas fotos de cada peça vão pro site. Uma é a foto do card; a segunda
# costuma ser as costas da camisa, que é o que o colecionador quer ver.
#
# Cada foto pesa ~32 KB. A conta muda bastante:
#     1 foto  ->  2.597 arquivos, ~83 MB
#     2 fotos ->  5.165 arquivos, ~165 MB
#     todas   -> 11.243 arquivos, ~360 MB
# O resto das fotos continua guardado no seu PC pra mandar no WhatsApp.
FOTOS_POR_PECA = 2

DOMINIO  = "https://camisariaesportiva.com.br"
INSTAGRAM = "https://www.instagram.com/camisariaesportivafc/"
FACEBOOK  = "https://www.facebook.com/camisariaesportivafc"
WHATSAPP = "551151234079"

AQUI     = os.path.dirname(os.path.abspath(__file__))
CATALOGO = os.path.join(AQUI, "site", "catalogo.json")
FOTOS    = os.path.join(AQUI, "site", "fotos")
WEB      = os.path.join(AQUI, "web")
SAIDA    = os.path.join(AQUI, "publicar")

# nomes bonitos pra coisas que no banco são código
NOME_UNIFORME = {
    "uniforme1": "1º Uniforme", "uniforme2": "2º Uniforme",
    "uniforme3": "3º Uniforme", "uniforme4": "4º Uniforme",
    "retro": "Retrô", "goleiro": "Goleiro", "treino": "Treino",
    "pre-jogo": "Pré-jogo", "aquecimento": "Aquecimento",
}
NOME_CATEGORIA = {
    "camisa": "Camisa", "kit": "Kit", "calcao": "Calção", "calca": "Calça",
    "jaqueta": "Jaqueta", "regata": "Regata", "polo": "Polo",
    "cropped": "Cropped", "meiao": "Meião", "luva": "Luva",
}


# =====================================================================
# 1. O ACERVO ENXUTO
# =====================================================================
# O catalogo.json tem 2 MB. Num celular no 4G isso é meio segundo parado
# antes de qualquer coisa aparecer. Aqui ele vira ~300 KB usando dois
# truques simples:
#
#   a) os textos que se repetem (time, liga, grupo) viram números que
#      apontam pra uma lista no começo do arquivo. "Real Madrid" aparece
#      uma vez em vez de 40.
#   b) cada peça vira uma LISTA em vez de um objeto, então os nomes dos
#      campos não se repetem 2.597 vezes.
#
# A ordem das colunas está em COLUNAS e o catalogo.html lê ela de lá —
# se um dia entrar campo novo, muda aqui e o site acompanha sozinho.
COLUNAS = ["time", "liga", "grupo", "raiz", "genero", "categoria", "uniforme",
           "temporada", "versao", "edicao", "preco", "destaque",
           "foto", "nfotos", "colecoes", "chave", "cobica", "modelo"]


# =====================================================================
# 1b. O MODELO — o que junta as variações da mesma camisa
# =====================================================================
# O fornecedor manda cada variação como uma peça solta: a Arsenal 26/27
# aparece cinco vezes (torcedor, jogador, feminina, e as duas de manga
# longa). Na vitrine isso vira cinco cartões iguais lado a lado — e o
# site parece uma planilha.
#
# Aqui cada peça recebe o número do MODELO a que pertence. O modelo é a
# chave sem as palavras que descrevem a variação: gênero, "Versão
# Torcedor", "Versão Jogador", "Manga Longa". Sobra
# "Arsenal - 26/27 - 2º Uniforme" — e as cinco peças caem no mesmo número.
#
# POR QUE VEM DA CHAVE E NÃO DOS CAMPOS
# Nas retrô o número do uniforme só existe no texto da chave: a coluna
# `uniforme` de todas elas é "retro". Agrupar por campo juntava a 1ª, a 2ª
# e a 3ª do Milan 07/08 num modelo só. Pela chave, não junta.
_VARIACAO = re.compile(
    r"\b(vers[aã]o\s+)?(torcedor|jogador|player|fan)\b|"
    r"\bmanga\s+longa\b|\bfeminina?\b|\binfantil\b|\bjuvenil\b|\bkids?\b",
    re.I)


def modelo_chave(p):
    partes = p["chave"].split(" - ")
    partes = [partes[0]] + partes[2:]          # fora o gênero
    limpo = []
    for trecho in partes:
        trecho = _VARIACAO.sub(" ", trecho)
        trecho = re.sub(r"\s+", " ", trecho).strip(" ·-")
        if trecho:
            limpo.append(trecho)
    return " - ".join(limpo) or p["chave"]


def _dicionario(pecas, campo):
    vistos = []
    indice = {}
    for p in pecas:
        v = p.get(campo)
        if v not in indice:
            indice[v] = len(vistos)
            vistos.append(v)
    return vistos, indice


def _foto_base(peca):
    """Devolve (base, quantas) quando as fotos seguem 'base-1.webp',
    'base-2.webp'... e (None, lista) quando não seguem.

    2.568 das 2.597 peças seguem o padrão. As 29 que não seguem são peças
    de foto única com nome antigo — por isso o caminho alternativo existe
    em vez de eu forçar todas no molde."""
    nomes = [f.split("/")[-1] for f in peca["fotos"]]
    m = re.fullmatch(r"(.+)-1\.webp", nomes[0]) if nomes else None
    if m and all(n == f"{m.group(1)}-{i}.webp" for i, n in enumerate(nomes, 1)):
        return m.group(1), len(nomes)
    return None, nomes


TEMPORADA = re.compile(r"\d{2}/\d{2}|\d{4}")


def rotulo(p):
    """O texto que descreve a peça: '2º Uniforme Versão Torcedor · Manga Longa',
    'Retrô 1998 · 2º Uniforme', 'Jaqueta 26/27 · Corta-Vento · Originals'.

    Vem da CHAVE, não dos campos soltos. A chave é montada pelo fornecedor.py
    com tudo que identifica a peça — inclusive coisas que não têm coluna
    própria no banco, como "2º Uniforme" de uma retrô. Montar o rótulo a
    partir dos campos perdia justamente essas.

    A chave é "Time - Gênero - Temporada - Descrição...". Fora time e gênero
    (que o card já mostra), sobra a descrição. A temporada também sai quando
    é só o ano, porque o card mostra ela do lado — mas "Retrô 1998" fica,
    que aí o ano É a informação."""
    cru = p["chave"].split(" - ")[2:]
    partes = cru[1:] if (cru and TEMPORADA.fullmatch(cru[0])) else cru
    texto = " · ".join(partes) or " · ".join(cru)
    # "Jaqueta 98/99" numa peça de temporada 98-99 mostrava o ano duas vezes:
    # uma no rótulo e outra na coluna da temporada. Tira a repetição.
    t = (p.get("temporada") or "").replace("-", "/")
    if t and t != "retro":
        texto = texto.replace(" " + t, "").replace(t + " ", "").strip(" ·")
    return texto or " · ".join(cru)


def copiar_modelos():
    """Leva web/modelos/ pro site e devolve a lista do que existe.

    A lista vai dentro do acervo.json de propósito. Sem ela, o site teria
    que TENTAR carregar uma foto de modelo pra cada peça e ver se dá 404 —
    2.597 tentativas falhando no celular de quem visita. Assim ele só pede
    o que existe."""
    origem = os.path.join(WEB, "modelos")
    if not os.path.isdir(origem):
        return []
    destino = os.path.join(SAIDA, "modelos")
    os.makedirs(destino, exist_ok=True)
    nomes = []
    for f in sorted(os.listdir(origem)):
        if f.lower().endswith((".webp", ".jpg", ".png")):
            shutil.copy2(os.path.join(origem, f), os.path.join(destino, f))
            nomes.append(f)
    if nomes:
        print(f"   {len(nomes)} fotos de modelo")
    return nomes


def ler_banners():
    """web/modelos/banners.json diz de que peça é cada banner. O modelos.py
    escreve; aqui a gente só lê e passa pro site."""
    caminho = os.path.join(WEB, "modelos", "banners.json")
    if not os.path.exists(caminho):
        return {}
    try:
        return json.load(io.open(caminho, encoding="utf-8"))
    except ValueError:
        print("   AVISO: web/modelos/banners.json está corrompido — ignorado")
        return {}


def acervo(pecas, modelos=None, banners=None):
    for p in pecas:
        p["_rotulo"] = rotulo(p)

    # numera os modelos na ordem em que aparecem
    modelo_num = {}
    for p in pecas:
        k = modelo_chave(p)
        if k not in modelo_num:
            modelo_num[k] = len(modelo_num)
        p["_modelo"] = modelo_num[k]

    dic = {}
    idx = {}
    for campo in ("time", "liga", "grupo", "genero", "categoria",
                  "uniforme", "temporada", "versao", "_rotulo"):
        dic[campo], idx[campo] = _dicionario(pecas, campo)

    colecoes = sorted({c for p in pecas for c in p.get("colecoes", [])})
    col_idx = {c: i for i, c in enumerate(colecoes)}

    linhas = []
    for p in pecas:
        base, n = _foto_base(p)
        foto = base if base else p["fotos"][0].split("/")[-1]
        nfotos = n if base else 0          # 0 = a foto é o nome inteiro
        linhas.append([
            idx["time"][p["time"]],
            idx["liga"][p["liga"]],
            idx["grupo"][p["grupo"]],
            1 if p["raiz"] == "selecoes" else 0,
            idx["genero"][p["genero"]],
            idx["categoria"][p["categoria"]],
            idx["uniforme"][p.get("uniforme")],
            idx["temporada"][p.get("temporada")],
            idx["versao"][p.get("versao")],
            idx["_rotulo"][p["_rotulo"]],
            p.get("preco"),
            1 if p.get("destaque") else 0,
            foto,
            min(nfotos, FOTOS_POR_PECA),
            [col_idx[c] for c in p.get("colecoes", [])],
            p["chave"],
            cobica.pontos(p),
            p["_modelo"],
        ])

    return {
        "gerado": date.today().isoformat(),
        "whatsapp": WHATSAPP,
        "modelos": sorted(m for m in (modelos or []) if not m.endswith(".json")),
        "banners": banners or {},
        "colunas": ["time", "liga", "grupo", "selecao", "genero", "categoria",
                    "uniforme", "temporada", "versao", "rotulo", "preco",
                    "destaque", "foto", "nfotos", "colecoes", "chave",
                    "cobica", "modelo"],
        "dic": {
            "time": dic["time"], "liga": dic["liga"], "grupo": dic["grupo"],
            "genero": dic["genero"], "categoria": dic["categoria"],
            "uniforme": dic["uniforme"], "temporada": dic["temporada"],
            "versao": dic["versao"], "rotulo": dic["_rotulo"],
            "colecao": colecoes,
        },
        "pecas": linhas,
    }


# =====================================================================
# 2. O dados.js — só o que o menu do topo precisa
# =====================================================================
# O dados.js antigo tinha 52 KB de lista escrita à mão, com 217 times e as
# cores de cada um (que existiam pra desenhar um retângulo quando não havia
# foto). Hoje toda peça tem foto e o catálogo tem 332 times. Então ele passa
# a ser GERADO: nunca mais fica desatualizado em relação ao acervo.
def dados_js(pecas):
    times = {}
    for p in pecas:
        t = times.setdefault(p["time"], {
            "nome": p["time"], "liga": p["liga"],
            "selecao": p["raiz"] == "selecoes", "grupo": p["grupo"], "pecas": 0})
        t["pecas"] += 1
    lista = sorted(times.values(), key=lambda t: t["nome"])
    temporadas = sorted({p["temporada"] for p in pecas
                         if p.get("temporada") and p["temporada"] != "retro"},
                        reverse=True)
    linhas = ",\n".join(
        '    {nome:%s, liga:%s, selecao:%s, grupo:%s, pecas:%d}' % (
            json.dumps(t["nome"], ensure_ascii=False),
            json.dumps(t["liga"], ensure_ascii=False),
            "true" if t["selecao"] else "false",
            json.dumps(t["grupo"], ensure_ascii=False), t["pecas"])
        for t in lista)
    temps = ",\n".join(
        '    {chave:%s, label:%s}' % (json.dumps(c), json.dumps(c.replace("-", "/")))
        for c in temporadas)
    return f"""// ============================================================
// GERADO POR publicar.py — NÃO EDITE ESTE ARQUIVO À MÃO.
// Ele é refeito a cada publicação a partir do catálogo. Se você mexer
// aqui, na próxima publicação sua mudança some.
//
// Para mudar o número do WhatsApp: publicar.py, lá em cima, WHATSAPP.
// Para acrescentar um time:        dados/times.json, e rode o build.
// ============================================================
  const WHATSAPP_NUMERO = "{WHATSAPP}";
  const TEMPORADAS = [
{temps}
  ];
  const times = [
{linhas}
  ];
"""


# =====================================================================
# 3. Montar a pasta
# =====================================================================
def achar_web():
    """A pasta web/ é onde ficam as páginas. Na primeira vez ela não existe
    e os arquivos estão soltos em outro lugar — então eu procuro nos lugares
    prováveis e COPIO (nunca movo, nunca apago) pra dentro do projeto."""
    if os.path.isdir(WEB) and any(f.endswith(".html") for f in os.listdir(WEB)):
        return
    candidatos = [
        os.path.dirname(AQUI),                                     # C:\Projetos
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "compreibarato"),
        os.path.join(os.path.expanduser("~"), "Desktop", "compreibarato"),
    ]
    for c in candidatos:
        if not os.path.isdir(c):
            continue
        html = [f for f in os.listdir(c) if f.endswith(".html")]
        if "index.html" not in html:
            continue
        os.makedirs(WEB, exist_ok=True)
        n = 0
        for f in os.listdir(c):
            if f.endswith((".html", ".css", ".js", ".png", ".ico", ".jpg", ".xml", ".txt")) \
               or f == "CNAME":
                shutil.copy2(os.path.join(c, f), os.path.join(WEB, f))
                n += 1
        print(f"   web/ criada com {n} arquivos copiados de {c}")
        print(f"   (os originais continuam lá; pode apagar quando quiser)")
        return
    sys.exit("Não achei as páginas do site (index.html, catalogo.html...).\n"
             f"Crie a pasta {WEB} e coloque os arquivos do site lá dentro.")


def copiar_fotos(pecas):
    os.makedirs(os.path.join(SAIDA, "fotos"), exist_ok=True)
    querem, faltando, bytes_ = set(), [], 0
    for p in pecas:
        for f in p["fotos"][:FOTOS_POR_PECA]:
            querem.add(f.split("/")[-1])
    for nome in sorted(querem):
        origem = os.path.join(FOTOS, nome)
        destino = os.path.join(SAIDA, "fotos", nome)
        if not os.path.exists(origem):
            faltando.append(nome)
            continue
        # só copia se mudou: na segunda publicação isso é quase instantâneo
        if (not os.path.exists(destino)
                or os.path.getmtime(origem) > os.path.getmtime(destino)):
            shutil.copy2(origem, destino)
        bytes_ += os.path.getsize(destino)
    # foto que não é mais do acervo sai da pasta de publicação
    sobra = set(os.listdir(os.path.join(SAIDA, "fotos"))) - querem
    for nome in sobra:
        os.remove(os.path.join(SAIDA, "fotos", nome))
    return len(querem), bytes_, faltando, len(sobra)


HTACCESS = """# php -- BEGIN cPanel-generated handler, do not edit
# Este domínio herda o pacote \u201cPHP\u201d.
# php -- END cPanel-generated handler, do not edit
#
# O bloco acima é do cPanel. Ele não faz nada sozinho — é um marcador que o
# painel do Hostgator usa pra saber qual versão do PHP o domínio segue. Está
# aqui de propósito: se sumir, o seletor de PHP do painel se perde.
# Daqui pra baixo é o que o site precisa.

# 1. Comprime texto antes de mandar. O acervo.json cai de ~400 KB para ~40 KB.
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css text/plain text/xml \\
      application/javascript application/json image/svg+xml
</IfModule>

# 2. Manda o navegador guardar o que não muda. Quem volta não baixa de novo.
#
#    As FOTOS do acervo são .webp e nunca mudam de conteúdo: quando a peça
#    muda, muda o nome do arquivo. Essas podem ficar um ano guardadas.
#
#    O LOGO e os ÍCONES são .png, .jpg e .ico, e esses PODEM mudar sem trocar
#    de nome — foi exatamente o que aconteceu quando a marca foi refeita: o
#    navegador continuou mostrando o emblema velho porque tinha guardado por
#    um ano. Uma semana é o suficiente pra economizar banda sem prender uma
#    troca de identidade.
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/webp        "access plus 1 year"
  ExpiresByType image/jpeg        "access plus 1 week"
  ExpiresByType image/png         "access plus 1 week"
  ExpiresByType image/x-icon      "access plus 1 week"
  ExpiresByType text/css          "access plus 1 week"
  ExpiresByType application/javascript "access plus 1 week"
  ExpiresByType application/json  "access plus 1 hour"
  ExpiresByType text/html         "access plus 1 hour"
</IfModule>

# 3. Endereço único: sempre https e sempre sem www, pra o Google não achar
#    que existem quatro sites iguais.
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteCond %{HTTPS} off
  RewriteRule ^(.*)$ https://%{HTTP_HOST}/$1 [R=301,L]
  RewriteCond %{HTTP_HOST} ^www\\.(.+)$ [NC]
  RewriteRule ^(.*)$ https://%1/$1 [R=301,L]
</IfModule>

# 4. Endereço que não existe cai na home em vez de numa página de erro do
#    Hostgator. O site do CompreiBaratoFC tinha links que sumiram; assim
#    ninguém bate numa parede.
#
#    Só que isso vale pra PÁGINA. Uma foto que falta devolvia a home inteira
#    (22 KB de HTML no lugar de uma imagem), o que é desperdício e confunde o
#    navegador. As duas linhas abaixo mandam foto que não existe responder
#    seca, sem página de erro.
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteRule ^fotos/.+\\.(webp|jpg|jpeg|png)$ - [R=404,L]
</IfModule>

ErrorDocument 404 /index.html
"""


# =====================================================================
# 4. OS PACOTES PRA SUBIR
# =====================================================================
# O Gerenciador de Arquivos do Hostgator trava com arquivo muito grande, e
# um zip de 145 MB é convite pra upload cair no meio. Então saem vários:
# um com o site (leve, é o que muda toda semana) e as fotos em fatias.
FATIA_MB = 45


def empacotar():
    pacotes = os.path.join(AQUI, "pacotes")
    if os.path.isdir(pacotes):
        shutil.rmtree(pacotes)
    os.makedirs(pacotes)

    # --- 1. o site: páginas, css, js, ícones, .htaccess
    caminho = os.path.join(pacotes, "1-site.zip")
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for nome in sorted(os.listdir(SAIDA)):
            cheio = os.path.join(SAIDA, nome)
            if os.path.isfile(cheio):
                z.write(cheio, nome)
    feitos = [("1-site.zip", os.path.getsize(caminho))]

    # --- 2. as fotos, em fatias
    pasta = os.path.join(SAIDA, "fotos")
    fotos = sorted(os.listdir(pasta)) if os.path.isdir(pasta) else []
    limite = FATIA_MB * 1024 * 1024

    def fechar(fatia, n):
        nome = f"2-fotos-{n}.zip"
        c = os.path.join(pacotes, nome)
        # foto já é comprimida: zipar de novo só gasta tempo, então vai cru
        with zipfile.ZipFile(c, "w", zipfile.ZIP_STORED) as z:
            for f in fatia:
                z.write(os.path.join(pasta, f), "fotos/" + f)
        return (nome, os.path.getsize(c))

    fatia, acumulado, n = [], 0, 0
    for f in fotos:
        tam = os.path.getsize(os.path.join(pasta, f))
        if acumulado + tam > limite and fatia:
            n += 1; feitos.append(fechar(fatia, n)); fatia, acumulado = [], 0
        fatia.append(f); acumulado += tam
    if fatia:
        n += 1; feitos.append(fechar(fatia, n))
    return pacotes, feitos


def main():
    if not os.path.exists(CATALOGO):
        sys.exit("Não achei site/catalogo.json. Rode antes:  python build.py tudo")

    pecas = json.load(io.open(CATALOGO, encoding="utf-8"))
    print(f"\n{len(pecas)} peças no catálogo")

    sem_preco = [p["chave"] for p in pecas if p.get("preco") is None]
    destaques = sum(1 for p in pecas if p.get("destaque"))
    if sem_preco:
        print(f"   {len(sem_preco)} sem preço (ficam de fora do site):")
        for c in sem_preco[:8]:
            print(f"      {c}")
        pecas = [p for p in pecas if p.get("preco") is not None]
    print(f"   {destaques} em destaque")
    if destaques == 0:
        print("   AVISO: nenhum destaque. A home vai mostrar peças aleatórias.")
        print("   Marque SIM na coluna 'destaque' do Sheets, baixe o CSV por cima")
        print("   de planilha-precos.csv e rode 'python build.py' de novo.")

    achar_web()
    os.makedirs(SAIDA, exist_ok=True)

    # páginas, css, ícones
    copiados = 0
    for f in sorted(os.listdir(WEB)):
        o = os.path.join(WEB, f)
        if os.path.isfile(o) and f != "dados.js":
            shutil.copy2(o, os.path.join(SAIDA, f))
            copiados += 1

    # as fotos de modelo (web/modelos/, feitas pelo modelos.py)
    modelos = copiar_modelos()
    banners = ler_banners()

    # dados gerados
    io.open(os.path.join(SAIDA, "acervo.json"), "w", encoding="utf-8").write(
        json.dumps(acervo(pecas, modelos, banners), ensure_ascii=False,
                   separators=(",", ":")))
    io.open(os.path.join(SAIDA, "dados.js"), "w", encoding="utf-8").write(dados_js(pecas))
    io.open(os.path.join(SAIDA, ".htaccess"), "w", encoding="utf-8", newline="\n").write(HTACCESS)

    try:
        from scripts import paginas
        n_pag = paginas.gerar(pecas, SAIDA, DOMINIO, WHATSAPP)
    except ImportError:
        n_pag = 0
        print("   (scripts/paginas.py não encontrado — sem páginas de time)")

    n_fotos, bytes_, faltando, removidas = copiar_fotos(pecas)

    tam_json = os.path.getsize(os.path.join(SAIDA, "acervo.json"))
    print(f"\npasta publicar/ pronta")
    print(f"   {copiados + 3 + n_pag} arquivos de página  (inclui {n_pag} geradas)")
    print(f"   acervo.json  {tam_json/1024:.0f} KB")
    print(f"   {n_fotos} fotos  {bytes_/1024/1024:.0f} MB"
          + (f"  ({removidas} tiradas)" if removidas else ""))
    if faltando:
        print(f"\n   {len(faltando)} fotos citadas no catálogo não existem em site/fotos:")
        for f in faltando[:5]:
            print(f"      {f}")
        print("   Rode 'python build.py tudo' pra recriá-las.")
    print(f"\n   total: {(bytes_ + tam_json)/1024/1024:.0f} MB")
    pacotes, feitos = empacotar()
    print(f"\npacotes prontos em  pacotes/")
    for nome, tam in feitos:
        print(f"   {nome:20s} {tam/1024/1024:6.1f} MB")
    print("\nPara subir no Hostgator (cPanel > Gerenciador de Arquivos > public_html):")
    print("   1. mande o 1-site.zip e extraia. Isso já atualiza o site inteiro.")
    print("   2. mande cada 2-fotos-N.zip e extraia — pode ser um por vez,")
    print("      e o site funciona mesmo antes de todos subirem (a foto que")
    print("      ainda não chegou aparece em branco).")
    print("   3. apague os .zip do servidor depois de extrair.")


if __name__ == "__main__":
    main()
