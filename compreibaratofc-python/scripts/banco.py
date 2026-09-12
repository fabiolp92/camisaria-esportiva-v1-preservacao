# -*- coding: utf-8 -*-
"""O banco do catálogo — um arquivo SQLite, sem servidor nenhum.

Por que SQLite e não MySQL/Postgres: o site é estático (GitHub Pages), então
não existe servidor rodando pra um banco conversar. O que a gente precisa é de
uma FONTE ÚNICA de verdade que o Python leia e escreva, e que gere os arquivos
do site. SQLite é exatamente isso: um arquivo .db do lado do projeto, que o
Python já sabe abrir sem instalar nada, e que você abre no VS Code com a
extensão SQLite pra olhar as tabelas.

Se um dia precisar de pedidos e estoque acessíveis de qualquer lugar, este
mesmo schema sobe pro Postgres sem reescrever nada — as tabelas são as mesmas.
"""
import os
import sqlite3

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO = os.path.join(AQUI, "dados", "catalogo.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

-- Os 217 times. Vem do times.json, que continua sendo a lista mestra.
CREATE TABLE IF NOT EXISTS times (
    id         INTEGER PRIMARY KEY,
    nome       TEXT UNIQUE NOT NULL,      -- "Real Madrid" (com acento, como no site)
    slug       TEXT UNIQUE NOT NULL,      -- "real-madrid"
    liga       TEXT,                      -- "La Liga · Espanha"
    liga_slug  TEXT,
    raiz       TEXT,                      -- clubes | selecoes
    grupo      TEXT,                      -- continente, ou grupo da Copa
    base       TEXT                       -- caminho na árvore de pastas
);

-- Uma linha por PEÇA que existe de verdade (ou seja, que tem foto).
-- O catálogo do site continua gerando as combinações possíveis em JavaScript;
-- aqui só entra o que a gente tem em mãos, senão seriam 217 × dezenas de linhas
-- de produto que não existem.
CREATE TABLE IF NOT EXISTS produtos (
    id         INTEGER PRIMARY KEY,
    time_id    INTEGER NOT NULL REFERENCES times(id) ON DELETE CASCADE,
    genero     TEXT NOT NULL,             -- masculino | feminino | infantil
    categoria  TEXT NOT NULL,             -- camisa | calcao | jaqueta | kit
    uniforme   TEXT,                      -- uniforme1..4 | retro
    temporada  TEXT,                      -- 26-27 | 25-26 | retro
    versao     TEXT,                      -- torcedor | jogador | kit
    variante   TEXT,                      -- goleiro, travis-scott, 125-anos...
    edicao     TEXT,                      -- "Preta", "Zico", "125 Anos"...
    ano_retro  TEXT,                      -- 11-12, 1998... só nas retrôs
    chave      TEXT UNIQUE NOT NULL,      -- a chave exata usada no dados.js
    preco      INTEGER                    -- preço em reais
);
-- Não existe um segundo UNIQUE aqui de propósito. Antes havia um sobre
-- (time, gênero, categoria, uniforme, temporada, versão, variante), e ele
-- rejeitava a Flamengo Preta por ser "igual" à Flamengo titular — os dois
-- campos que as separam (edição e ano da retrô) não estavam nele. Quem define
-- identidade é a `chave`, que é montada a partir de TUDO. Uma definição só.

-- Cada peça pode ter um conjunto de fotos. A ordem é a que aparece na lupa.
CREATE TABLE IF NOT EXISTS fotos (
    id          INTEGER PRIMARY KEY,
    produto_id  INTEGER NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
    arquivo     TEXT UNIQUE NOT NULL,     -- "fotos/real-madrid-...-1.webp"
    ordem       INTEGER NOT NULL,
    bytes       INTEGER,
    largura     INTEGER,
    origem      TEXT,                     -- arquivo original, pra rastrear depois
    UNIQUE (produto_id, ordem)
);

-- Coleções são o jeito do CLIENTE navegar (Copa 2026, Kids, Agasalhos),
-- diferente dos atributos, que são o que a peça É. Uma peça entra em várias.
CREATE TABLE IF NOT EXISTS colecoes (
    id        INTEGER PRIMARY KEY,
    slug      TEXT UNIQUE NOT NULL,
    nome      TEXT NOT NULL,
    descricao TEXT,
    ordem     INTEGER DEFAULT 100
);

CREATE TABLE IF NOT EXISTS produto_colecao (
    produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE,
    colecao_id INTEGER REFERENCES colecoes(id) ON DELETE CASCADE,
    PRIMARY KEY (produto_id, colecao_id)
);

CREATE INDEX IF NOT EXISTS idx_produtos_time ON produtos(time_id);
CREATE INDEX IF NOT EXISTS idx_fotos_produto ON fotos(produto_id);
"""

# As categorias que o cliente vê no menu. É aqui que a estrutura do site cresce:
# acrescentar uma linha nesta lista cria uma coleção nova no catálogo.
COLECOES = [
    ("copa-2026",     "Copa do Mundo 2026", "Camisas e kits das seleções para a Copa de 2026.", 10),
    ("feminino",      "Feminino",           "Modelagem feminina de clubes e seleções.", 20),
    ("kids",          "Kids",               "Kit infantil: camisa e calção do mesmo uniforme.", 30),
    ("conjuntos",     "Conjuntos",          "Camisa e calção juntos, adulto e infantil.", 40),
    ("agasalhos",     "Agasalhos e Jaquetas", "Corta-vento e conjuntos de treino.", 50),
    ("retro",         "Retrô",              "Uniformes clássicos de várias épocas.", 60),
    ("edicoes",       "Edições Especiais",  "Colaborações, aniversários e edições limitadas.", 70),
    ("goleiro",       "Goleiro",            "Uniformes de goleiro.", 80),
    ("brasileirao",   "Times do Brasil",    "Clubes do Brasileirão.", 90),
    ("europa",        "Clubes da Europa",   "Premier League, La Liga, Serie A, Bundesliga e Ligue 1.", 95),
]


def _atualizar_schema(con):
    """Se o banco foi criado por uma versão antiga, recria do zero.

    Dá pra fazer isso sem medo porque o banco é DERIVADO: tudo que está nele
    vem das fotos e do times.json, e reconstruir custa segundos (as fotos já
    comprimidas são reaproveitadas). É mais seguro do que remendar tabela."""
    try:
        colunas = {r[1] for r in con.execute("PRAGMA table_info(produtos)")}
    except Exception:
        return
    if not colunas:
        return                       # banco novo, nada a migrar
    if "edicao" in colunas and "ano_retro" in colunas:
        return                       # já está atualizado
    print("   (banco em formato antigo — recriando, as fotos são aproveitadas)")
    for t in ("produto_colecao", "fotos", "produtos", "colecoes", "times"):
        con.execute(f"DROP TABLE IF EXISTS {t}")
    con.commit()


def abrir(caminho=CAMINHO):
    """Abre (criando se preciso) o banco e garante que o schema está aplicado."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    con = sqlite3.connect(caminho)
    con.row_factory = sqlite3.Row
    _atualizar_schema(con)
    con.executescript(SCHEMA)
    for slug, nome, desc, ordem in COLECOES:
        con.execute("INSERT OR IGNORE INTO colecoes (slug, nome, descricao, ordem) "
                    "VALUES (?,?,?,?)", (slug, nome, desc, ordem))
    con.commit()
    return con


def resumo(con):
    q = lambda s: con.execute(s).fetchone()[0]
    return {
        "times": q("SELECT COUNT(*) FROM times"),
        "produtos": q("SELECT COUNT(*) FROM produtos"),
        "fotos": q("SELECT COUNT(*) FROM fotos"),
        "colecoes": q("SELECT COUNT(*) FROM colecoes"),
        "peso_fotos_mb": (q("SELECT COALESCE(SUM(bytes),0) FROM fotos") or 0) / 1024 / 1024,
    }
