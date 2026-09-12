# GIT_VERSIONING_RULES.md

**Projeto:** Camisaria Esportiva FC
**Tarefa:** CE-001 — versionamento seguro da V1
**Autor:** Claude Work (gerente operacional)
**Data:** 12/09/2026
**Status:** `.gitignore` definitivo entregue e instalado. **Nenhum comando Git foi executado.**

---

## 0. Escopo e restrições respeitadas

- Nenhum comando Git, Python ou PowerShell foi executado.
- A V1 original não foi alterada em lógica: a única escrita no repositório foi o próprio arquivo `.gitignore`.
- A análise foi feita por **leitura** da árvore de diretórios e do cabeçalho da planilha comercial.

---

## 1. Decisão estruturante: **o repositório deve ser PRIVADO**

`planilha-precos.csv` tem o seguinte cabeçalho:

```
chave,time,grupo,temporada,fotos,preco,custo,destaque,ativo,observacao
```

A coluna **`custo`** é o preço de compra no fornecedor. Exemplo real da linha 2: preço 219, custo 65 — margem de 3,4×.

Consequências:

1. O repositório **não pode ser público** em nenhuma hipótese, nem "temporariamente para testar".
2. Se o `custo` vazar, qualquer concorrente reconstrói a tabela de fornecedor da operação inteira.
3. Se em algum momento se quiser um repositório público (ex.: para o GitHub Pages da V2), ele tem de ser **um segundo repositório**, sem esse arquivo — e não uma abertura deste.

Alternativa, se a preferência for repositório público desde já: remover a coluna `custo` da planilha versionada e manter os custos num arquivo local ignorado (`planilha-custos.csv`, adicionado ao `.gitignore`). Isso é uma decisão do dono do negócio, não operacional, e fica registrada aqui como pendente.

---

## 2. O que ENTRA no Git

### 2.1 Código Python — o núcleo do repositório
| Arquivo | Papel |
|---|---|
| `baixar.py` | download do acervo do fornecedor |
| `build.py` | orquestrador do pipeline |
| `publicar.py` | gera `publicar/` e os pacotes |
| `modelos.py` | fábrica de modelos IA e banners |
| `marca.py` | geração das artes de marca |
| `posts.py` | geração dos posts de rede social |
| `planilha.py`, `raras.py`, `instalar.py`, `exportar.py` | utilitários |
| `scripts/importar.py` | importação para o SQLite |
| `scripts/fornecedor.py` | parsing do catálogo do fornecedor (41 KB — o maior ativo de regra de negócio) |
| `scripts/paginas.py` | geração das 342 páginas + JSON-LD |
| `scripts/banco.py`, `scripts/cobica.py`, `scripts/imagens.py`, `scripts/semear.py`, `scripts/ce003_normalizar.py` | módulos de apoio |
| `testes/teste_nome_arquivo.py` | teste existente |

### 2.2 Fonte web (`web/`)
HTML, CSS e JS **fonte** — não os 342 HTML gerados.
`index.html`, `catalogo.html`, `nav.js`, `pagina.css`, as 24 páginas-modelo de clube/seleção, `CNAME`, `robots.txt`, e os ícones de marca (`favicon*`, `escudo-ce.png`, `marca-ce.png`, `icone-512.png`, `apple-touch-icon.png`, `capa-camisaria-esportiva.jpg` — ~360 KB no total, estáveis, é o que efetivamente sobe para o servidor).

### 2.3 Dados estruturais e comerciais
| Arquivo | Tamanho | Por quê |
|---|---|---|
| `site/catalogo.json` | 2,1 MB | **JSON mestre.** Texto puro, diffável. É o snapshot que reconstrói o catálogo sem o SQLite. |
| `site/colecoes.json` | 1,4 KB | definição das coleções |
| `dados/times.json` | 102 KB | **mapeamento curado à mão** de nomes de time, apelidos e slugs. Se perder, não se regenera — só se refaz. |
| `planilha-precos.csv` | 278 KB | CSV comercial: preço, custo, ativo, destaque |
| `requirements.txt` | 13 B | dependências |

### 2.4 Insumos irreproduzíveis
| Caminho | Tamanho | Por quê |
|---|---|---|
| `elenco/*.webp` (10 arquivos) | ~340 KB | O elenco de modelos IA aprovado (H1–H4, M1–M4, B1, G1). Gerado uma única vez, aprovado visualmente. **Regerar não devolve as mesmas pessoas.** É o ativo mais insubstituível do repositório por byte. |
| `elenco/CONFERIR.jpg` | 130 KB | folha de conferência que dá identidade a cada crachá |
| `arte/fontes/*.ttf` | 236 KB | Inter e Playfair Display. Licença SIL OFL — redistribuição permitida. Sem elas `marca.py` e `posts.py` não rodam em outra máquina. |
| `arte/marca-*.jpg` | ~430 KB | artes de marca de referência |

### 2.5 Documentação, mapeamentos e regras
`LEIA-ME.txt`, `LEIA-ME-PUBLICAR.txt`, `ROTEIROS-E-LEGENDAS.txt`, `PLANO-MODELOS-IA.md`, `ANALISE-MEUKATALOGO.md`, `HANDOFF-CLAUDE-WORK-12-09.md`, `PASSO-A-PASSO-AGORA.txt`, `gerar/LISTA.txt` (mapeamento do que gerar), `posts/LEGENDAS.txt` (33 KB de legendas autorais).

### 2.6 Arquivos de servidor (exceções dentro de `publicar/`)
`publicar/.htaccess`, `publicar/robots.txt`, `publicar/sitemap.xml` — 49 KB somados. São gerados, mas são **o contrato com o Google e com o Apache**. Mantê-los versionados dá histórico de quando uma regra de redirect ou de indexação mudou.

**Volume estimado do repositório: ~7 MB.** Contra ~4 GB com o `.gitignore` anterior.

---

## 3. O que NÃO ENTRA no Git

| Caminho | Volume | Motivo |
|---|---|---|
| `fotos_originais/` | ~3,3 GB / 16.151 arq. | acervo do fornecedor; vai para storage/CDN na V2 |
| `site/fotos/` | ~332 MB / ~11.000 arq. | derivado de `fotos_originais/` pelo `build.py` |
| `site/.cache-fotos.json` | 2,8 MB | cache, reescrito inteiro a cada build |
| `site/fotos-do-banco.js` | 1,2 MB | derivado de `catalogo.json` |
| `dados/catalogo.db` | 3,5 MB | binário, reconstruível — ver §4 |
| `publicar/` (exceto 3 arquivos) | 342 HTML + fotos | saída integral do `publicar.py` |
| `pacotes/` e `*.zip` | ~45 MB por pacote | artefatos de upload |
| `gerados/` | — | saídas brutas de IA, descartáveis |
| `gerar/*` (exceto `LISTA.txt`) | imagens pesadas | insumos de geração |
| `posts/*` (exceto `LEGENDAS.txt`) | 120 JPG, ~30 MB | renderizações regeneráveis |
| `arte/redes/` | — | renderizações, não fontes |
| `relatorio-importacao.txt` | 338 KB | relatório regerado |
| `__pycache__/`, `*.pyc`, `*.ok` | — | subprodutos de execução |
| `.env`, `credenciais.json`, `*.pem`, `*.key`, `ftp.cfg` | — | segredos, preventivo |
| `Thumbs.db`, `desktop.ini`, `.vscode/`, `*.tmp`, `*.bak`, `*.log` | — | SO e editor |

---

## 4. Diretórios ambíguos — e a decisão tomada

### 4.1 `dados/catalogo.db` (3,5 MB) — **FICA DE FORA**
A instrução admitia "SQLite se tecnicamente apropriado como snapshot pequeno". 3,5 MB é pequeno em valor absoluto, mas o critério correto não é o tamanho e sim o comportamento no Git:

- SQLite é binário. O Git não faz delta útil; **cada build grava um blob novo de 3,5 MB**.
- Vinte builds = 70 MB de histórico que nunca encolhe, para um arquivo que `importar.py` reconstrói.
- Já existe um snapshot **textual e diffável** do mesmo conteúdo: `site/catalogo.json`, que entra.

Se a V2 quiser um snapshot congelado do banco, o lugar certo é um *release asset* ou o Drive, não o histórico do repositório.

### 4.2 `publicar/` — **FORA, com três exceções**
É saída de build, e por princípio saída de build não se versiona. Mas `.htaccess`, `robots.txt` e `sitemap.xml` são infraestrutura de SEO cujo histórico tem valor real quando o Search Console reclamar de algo. Custam 49 KB. O `sitemap.xml` vai gerar ruído de diff a cada build — aceitável; se incomodar, remover só ele.

### 4.3 `site/catalogo.json` (2,1 MB) — **ENTRA, com ressalva operacional**
É o JSON mestre e precisa estar versionado. Mas ele é reescrito **inteiro** a cada build, então cada commit dele custa ~2 MB (menos com compressão, mas não pouco).

**Regra operacional:** commitar `site/catalogo.json` apenas em **marcos** — importação nova, correção de dados, fechamento de sprint — e não a cada execução do pipeline.

### 4.4 `elenco/` — **ENTRA**, e é a decisão mais importante
Pela nomenclatura pareceria "saída de IA", que a instrução manda ignorar. É o contrário: é **insumo aprovado**. O elenco foi gerado uma vez, conferido na folha de contato e fixado em H1–H4/M1–M4/B1/G1. Rodar o gerador de novo produz outras pessoas e quebra a consistência de todos os banners. São 340 KB para proteger o ativo criativo inteiro.

### 4.5 `arte/fontes/*.ttf` — **ENTRA**
Verificado: Inter e Playfair Display são SIL Open Font License, que permite redistribuição inclusive comercial. Sem elas o `marca.py` quebra em qualquer outra máquina.

### 4.6 `planilha-precos.csv` — **ENTRA, e força o repositório a ser privado**
Ver §1.

### 4.7 `web/` versus `publicar/`
Ambos têm `index.html`, `catalogo.html`, `nav.js`, `pagina.css`. **`web/` é fonte, `publicar/` é saída.** Editar em `publicar/` é trabalho perdido — o próximo `publicar.py` sobrescreve. Quem chegar depois precisa saber disso.

---

## 5. Riscos antes de qualquer `git add`

### Risco 1 — Segredos no código *(verificar ANTES do primeiro commit)*
**Não foi possível verificar sem executar comandos.** Antes do `git add`, procurar por senha de cPanel, FTP ou token do fornecedor em `baixar.py`, `scripts/fornecedor.py`, `publicar.py` e `instalar.py`. Segredo commitado **não some ao ser apagado depois** — fica no histórico e exige reescrita de histórico e troca da senha. Esta é a única verificação que deve bloquear o primeiro commit.

### Risco 2 — O `.gitignore` só vale para o que ainda não foi rastreado
Ele **impede adicionar**, não remove o que já está no índice. Como não há `.git` nesta pasta, o repositório nasce limpo — desde que o `.gitignore` esteja no lugar **antes** do primeiro `git add`. Ele já está: instalado em 12/09.

### Risco 3 — `git status` e o primeiro `git add` serão lentos
O Git vai avaliar ~16.000 arquivos na primeira passada. Pode levar minutos e parecer travado. É normal, não interromper.

### Risco 4 — Crescimento do histórico por `catalogo.json`
Mitigado pela regra de commit em marcos (§4.3).

### Risco 5 — Direitos de imagem
Mesmo com repositório privado, as fotos do fornecedor não devem entrar. Já estão excluídas por `fotos_originais/` e `site/fotos/`.

### Risco 6 — Repositório público por engano
No `git init` + criação no GitHub, o padrão da interface web costuma vir em "Public". Ver §1.

### Risco 7 — `site-github/` está vazio
A pasta `C:\Users\fabio\OneDrive\Desktop\site-github` está vazia. Se alguém rodar `git init` **ali** achando que é o repositório do projeto, cria um repositório vazio e a V1 continua sem versionamento. O `git init` é em `C:\Projetos\compreibaratofc-python`.

### Risco 8 — OneDrive e `.git` não se dão bem
`C:\Projetos` está fora do OneDrive, o que é correto. Não mover o projeto para dentro de pasta sincronizada: OneDrive corrompe `.git` em sincronização concorrente.

---

## 6. Sequência recomendada (a executar depois, com shell)

1. Verificar segredos no código (Risco 1).
2. Confirmar que o `.gitignore` está em `C:\Projetos\compreibaratofc-python\.gitignore` com 3.149 bytes. *(já confirmado em 12/09)*
3. `git init`
4. `git add -A` seguido de `git status` — **conferir a lista antes de commitar**. Esperado: ~60 arquivos, ~7 MB. Se aparecer qualquer coisa de `fotos_originais/`, `site/fotos/` ou `publicar/` além das três exceções, parar.
5. Primeiro commit.
6. Criar o repositório no GitHub **marcado como Private**.
7. `git remote add origin` + `git push`.

Passos 3 a 7 dependem de sessão com shell e o passo 7 exige login do GitHub — este é fornecido pelo dono do projeto, não pelo agente.

---

## 7. Estado ao final desta tarefa

| Item | Estado |
|---|---|
| `.gitignore` definitivo | **Entregue e instalado** (3.149 bytes) |
| Lista do que entra | §2 |
| Lista do que não entra | §3 |
| Diretórios ambíguos | §4 — 7 casos analisados e decididos |
| Riscos | §5 — 8 riscos, 1 bloqueante (segredos) |
| Comandos Git/Python/PowerShell executados | **Nenhum** |
| V1 alterada | **Não** |
