# HANDOFF — Claude (Cowork) → ChatGPT

**Projeto:** Camisaria Esportiva FC
**Data:** 12/09/2026
**Autor:** Claude, sessão Cowork ligada ao notebook `lp` (Windows)
**Propósito:** sincronizar o estado real do projeto. Contém (1) a verificação
pedida no handoff mestre e (2) uma frente de trabalho inteira na V1 que não
aparece em nenhum documento do Drive.

---

## 0. O QUE ESTA SESSÃO PODE E NÃO PODE FAZER

Importante para o roteamento de tickets. As capacidades variam por sessão e
esta está **degradada** em relação ao que o handoff mestre assume.

| Capacidade | Estado |
|---|---|
| Ler pastas e arquivos do notebook | **OK** |
| Copiar arquivos do notebook para análise | **OK** |
| Ler e escrever no Google Drive | **OK** |
| Executar comandos no notebook (`device_bash`) | **INDISPONÍVEL** |
| Controlar mouse/teclado do notebook | disponível, requer aprovação |
| Ambiente Linux próprio com Python/Node | **OK** (isolado, não é a máquina do usuário) |

**Consequência direta:** nesta sessão eu **não consigo** rodar `git`, `python`,
`pip` ou PowerShell no notebook. Qualquer ticket que dependa de executar
comando local precisa: (a) de uma sessão com shell, (b) de o usuário colar os
comandos, ou (c) de eu digitar em uma janela do PowerShell via controle de
mouse/teclado — lento e frágil, último recurso.

O handoff mestre atribui a "Claude Work" as operações de Git local. **Nesta
sessão isso não é executável.** Não é recusa, é indisponibilidade técnica.

---

## 1. VERIFICAÇÃO PEDIDA — RESULTADOS

Método: leitura direta do sistema de arquivos do notebook + leitura do Drive.
**Nenhum script executado. Nenhum arquivo da V1 alterado.**

### 1.A — CE-001 (Git/GitHub): NÃO INICIADO

Não é "parcial". Não existe repositório.

| Verificação | Resultado |
|---|---|
| `C:\Projetos\compreibaratofc-python\.git` | não existe |
| `C:\Projetos\.git` | não existe |
| `C:\Users\fabio\OneDrive\Desktop\site-github\` | **pasta vazia** |
| `.gitignore` no projeto | existe — 85 bytes, mtime 30/06/2026 |

O listador usado exibe arquivos ocultos (lista `.gitignore` e `__pycache__`),
portanto a ausência de `.git` é conclusiva. Nenhum commit, nenhum push, nenhum
remote. A execução anterior parou antes de o `git init` persistir, ou rodou em
diretório temporário descartado.

**Risco a registrar:** o `.gitignore` de 85 bytes é o original do projeto V1.
Pelo tamanho, não cobre `fotos_originais/` (~3,3 GB), `site/` (~332 MB),
`publicar/` (~157 MB), `pacotes/`, `gerados/`, `gerar/` nem `elenco/`. Um
`git add .` com ele tenta versionar o acervo inteiro. **Reescrever o
`.gitignore` é pré-requisito do CE-001, não um detalhe.**

### 1.B — CE-003 (reconciliação comercial): PARCIAL

**O relatório existe e está correto. O arquivo de dados não foi encontrado.**

Li integralmente `docs/COMMERCIAL_RECONCILIATION.md` (Drive, 46.869 bytes,
criado 12/09/2026 01:11 UTC). As três confirmações pedidas conferem:

| Controle | Valor |
|---|---:|
| Registros CSV legado / XLSX / normalizado | 2.597 / 2.597 / 2.597 |
| Chaves coincidentes | 2.597 |
| Chaves ausentes em qualquer fonte | 0 |
| Divergências preço / custo / ativo / destaque / observação / fotos | 0 |
| Divergências de temporada antes → depois | 525 → 0 |
| Ativos / destaques na saída | 2.597 / 20 |
| **Casos pendentes de decisão humana** | **0** |

O relatório registra tratamento monetário por `Decimal` (sem `float`), com
`preco_centavos`/`custo_centavos` inteiros na saída, e traz apêndice com as
525 correções linha a linha. Metodologicamente sólido.

**Arquivos referenciados pelo relatório que NÃO foram localizados:**

| Arquivo | Google Drive | Notebook |
|---|---|---|
| `data/catalog-commercial-normalized.csv` | ausente | pasta `data/` não existe |
| `docs/ce-003/resultado.json` | ausente | pasta `docs/` não existe |
| `docs/ce-003/divergencias-completas.csv` | ausente | pasta `docs/` não existe |

A pasta `docs` do Drive (`1N9J0qMYWw0bxf31SDIKqZPQN5u69PVts`) contém 15 itens
— todos `.md` mais o zip — e nenhum deles é o CSV. A raiz
`C:\Projetos\compreibaratofc-python` não tem `docs/` nem `data/`.

**Por que importa:** o insumo do CE-005 é o CSV normalizado, não o relatório.
Sem ele, a migração recomeça do XLSX e refaz as 525 correções de temporada.

Hipótese mais provável: gerados em diretório temporário da execução anterior e
nunca persistidos. Não consigo confirmar — `Downloads` não está entre as
pastas conectadas a esta sessão.

### 1.C — `SPRINT_01_STATUS.md`

Criado no Drive em `Camisaria Esportiva > docs`, com as evidências acima.
ID `1eAHVPbLaxAX2_-RbIV6mzjfhoyuSnJ2y`.

---

## 2. FRENTE DE TRABALHO NÃO DOCUMENTADA — ATENÇÃO

Esta é a parte mais importante deste handoff para a sincronização.

Entre 30/08 e 08/09/2026 houve uma frente de trabalho contínua sobre a V1,
comigo, que **não aparece em nenhum documento do Drive** (`AUDIT_V1.md`,
`REUSE_V1.md`, `BACKLOG.md`, `PRODUCT_MODEL_V2.md` etc. foram escritos em
11/09 sem esse contexto).

Consequência: **o `REUSE_V1.md` e o `PRODUCT_MODEL_V2.md` provavelmente estão
subestimando o que a V1 já resolve.** Vários problemas que a V2 planeja
resolver do zero já têm solução testada em produção.

### 2.1 — O que foi construído na V1

**Agrupamento de variantes (resolve um problema que a V2 vai reencontrar).**
O fornecedor entrega cada variação como produto solto: a mesma camisa aparece
como torcedor, jogador, feminina e manga longa — 4 a 5 registros. Foi criado
um identificador de **modelo** derivado da chave (removendo gênero, "Versão
Torcedor", "Versão Jogador", "Manga Longa"):

```
2.597 peças  →  2.195 modelos
```

Implementado em `publicar.py` (`modelo_chave()`, coluna `modelo` no
`acervo.json`). **Isto é exatamente o `product` vs `product_variants` do
modelo V2.** A regra de derivação já está escrita e validada contra as 2.597
peças — inclusive o caso difícil: nas retrô o número do uniforme só existe no
texto da chave (o campo `uniforme` é sempre `"retro"`), então agrupar por
campo juntava indevidamente 1º, 2º e 3º uniforme. **Recomendo que o CE-004
reaproveite essa regra em vez de reinventá-la.**

**Ordenação por procura (`scripts/cobica.py`).** Tabela editável de peso por
time + anos icônicos + penalidade para acessórios. Substitui a ordem
alfabética (que abria o acervo em "Aberdeen, AEK Atenas, Albacete"). Também
existe um `intercalar()` round-robin que evita 6 peças do mesmo time seguidas.
Equivalente funcional de um campo `relevance_score` na V2.

**Ficha de produto.** Galeria com miniaturas, variantes selecionáveis com
preço por variante, seletor de tamanho (P–XXGG; 16–28 infantil), mensagem de
WhatsApp montada com versão + tamanho, e bloco "Mais do \<time\>".

**Navegação por atalhos.** Fileira contextual: sem time selecionado mostra as
portas do acervo; com um time selecionado vira o índice daquele time com
contagem por gaveta.

**342 páginas estáticas com SEO** (`scripts/paginas.py`) — uma por time mais
coleções, cada uma com JSON-LD `ItemList`/`Product`.

**Correção de dados estruturados** (em resposta a avisos do Search Console):
adicionados `description`, `url`, `sku`, `itemCondition`, `seller` e
`hasMerchantReturnPolicy`. **Deliberadamente NÃO adicionados** `review` e
`aggregateRating` — não existem avaliações reais, e inventá-las viola a
política do Google. O aviso permanece e é não crítico.

### 2.2 — Elenco de modelos por IA (CONCLUÍDO)

Existe um sistema de duas etapas em `modelos.py` (59 KB), e o elenco **já foi
gerado e está no notebook**:

- **Etapa A** — 10 pessoas fictícias geradas uma vez (H1–H4 homens: branco,
  loiro, negro, asiático; M1–M4 mulheres: morena, loira, negra, asiática;
  B1 menino; G1 menina). Todas 896×1200, 3:4, camiseta cinza lisa, fundo
  neutro, enquadramento consistente (topo da cabeça entre 5% e 8%, altura
  ocupada entre 90% e 94%).
- **Etapa B** — para cada camisa, Gemini recebe 2 imagens (pessoa + peça) e o
  prompt "mesma pessoa da imagem 1 vestindo a peça da imagem 2".

`modelos.py` seleciona as peças pela tabela de procura, localiza a foto no
meio de 11.243 arquivos, escreve os prompts, copia pessoa e peça lado a lado,
e depois corta/redimensiona/renomeia o resultado. Comandos: `elenco`,
`renomear`, `elenco-ok`, `trocar`, `preparar`, `padronizar`, `listar`.

Plano: 55 imagens em 5 fases. **Fase 1 (8 banners) preparada; 1 gerada e
aprovada** (Manchester United 07-08, 1376×768, identidade do modelo
preservada, camisa fiel, lado esquerdo livre para texto).

**Regra de integridade adotada, que a V2 deve herdar:** a foto de modelo
**nunca** substitui a foto real da peça no cartão de produto. Modelo gerado
por IA é uma reprodução — escudo escorrega, letra miúda vira ruído (verificado
empiricamente: a inscrição comemorativa da final de 2008 saiu ilegível). A
foto de modelo entra em dois lugares apenas: banner do topo, e como foto extra
na ficha com aviso visível *"Imagem ilustrativa · a peça é a das fotos
anteriores"*. Isto sustenta a promessa "a foto do site é a peça que existe",
que é o principal ativo de confiança de uma loja que fecha por WhatsApp.

### 2.3 — Conteúdo

`ROTEIROS-E-LEGENDAS.txt` (18,6 KB): 16 formatos de vídeo com lacunas em
colchetes, calendário de 5 semanas, política de hashtags. Inclui formatos
específicos para feminina e infantil.

Restrição de marca vigente: **não usar "oficial", "licenciada", "original" ou
"autêntica"** em nenhum lugar — site, bio, legendas ou imagens geradas. Está
no negative prompt das gerações também.

### 2.4 — DESCOMPASSO: a V1 no notebook está atrasada

| Arquivo | No notebook | Versão validada |
|---|---:|---:|
| `modelos.py` | 59.019 | 59.019 ✓ aplicado |
| `scripts/cobica.py` | 9.432 | 9.432 ✓ aplicado |
| `publicar.py` | 20.133 | **23.541** ✗ |
| `scripts/paginas.py` | 24.088 | **29.239** ✗ |
| `web/index.html` | — | **44.627** ✗ |
| `web/catalogo.html` | — | **59.897** ✗ |
| `web/nav.js` | — | **14.392** ✗ |
| `web/pagina.css` | — | **4.067** ✗ |

As pastas `elenco/`, `gerar/` e `gerados/` existem no notebook — o fluxo de
geração foi executado. Mas o pacote com arredondamento visual, banner com
modelo, ficha de peça, voltar-ao-topo e correções de dados estruturados
**nunca foi aplicado**.

**Efeito prático:** o `publicar.py` de 20.133 bytes não sabe ler
`web/modelos/` nem `banners.json`. Os banners gerados **não chegam ao site**.

Isso não bloqueia a V2, mas está aberto desde 07/09 e não consta de nenhum
backlog.

---

## 3. LACUNA DE CATÁLOGO — decisão comercial pendente

Levantado a partir do `catalogo.json` (2.597 peças):

**Apenas 223 das 2.597 peças (8,6%) são dos 27 clubes do Brasileirão.**

| Clube | Peças | O que falta |
|---|---:|---|
| Flamengo | 60 | — |
| Vasco / Cruzeiro | 22 / 22 | 2º uniforme 26/27 (Vasco) |
| Internacional / Botafogo / Fluminense | 16 cada | infantil |
| Grêmio | 13 | infantil |
| Corinthians | 10 | infantil |
| São Paulo / Santos | 8 / 7 | infantil |
| Atlético-MG / Bahia | 6 / 6 | 1º uniforme 26/27, infantil |
| Sport / Vitória | 5 / 4 | 2º uniforme, infantil |
| **Palmeiras** | **3** | 1º e 2º uniforme 26/27, feminina, infantil |
| Athletico-PR / Coritiba | 3 / 3 | 1º uniforme, feminina, infantil |
| Ceará / Bragantino / Chapecoense | 1 cada | quase tudo |
| **Fortaleza, Juventude, Mirassol, Goiás, Atlético-GO, Criciúma, Cuiabá** | **0** | tudo |

**Causa identificada:** as 15 pastas baixadas do fornecedor são `africa`,
`agasalhos`, `alemanha`, `argentina`, `brasil`, `conjuntos`, `criancas1`,
`espanha`, `franca`, `inglaterra`, `italia`, `mulher`, `portugal`, `retro`,
`selecoes`. A pasta `brasil` é a **seleção** brasileira. **A categoria de
clubes brasileiros do fornecedor nunca foi baixada.**

Isto é anterior a qualquer decisão de arquitetura: um e-commerce brasileiro
com 3 peças do Palmeiras e zero do Fortaleza tem um problema de sortimento,
não de tecnologia. Sugiro tratar como ticket de negócio com prioridade acima
do CE-005.

---

## 4. DECISÕES REGISTRADAS NESTA FRENTE

Para não serem revertidas por desconhecimento:

1. Foto de modelo por IA nunca substitui foto real de produto (ver 2.2).
2. Não usar "oficial / licenciada / original / autêntica".
3. Não declarar `review`/`aggregateRating` sem avaliações reais.
4. **Política de troca confirmada pelo usuário:** 7 dias, devolução por conta
   do cliente, pelos Correios, Brasil. Já escrita no JSON-LD.
5. **Frete:** o usuário definiu "grátis a partir de 3 camisas; abaixo disso,
   valor dos Correios". **Isto não é declarável em `shippingDetails`** — o
   Google exige valor concreto por oferta, e o limiar é por quantidade, não
   por valor, além de a tarifa ser calculada. O campo fica de fora e o aviso
   correspondente do Search Console permanece. Se a V2 tiver carrinho com
   cálculo de frete, o campo passa a ser declarável.

---

## 5. PREMISSA NÃO VERIFICADA

O handoff mestre trata como fato que *"a HostGator possui a pasta completa
equivalente ao conteúdo de `C:\Projetos`"*, e essa premissa é o único
fundamento da decisão de não fazer backup local adicional.

**É uma declaração do usuário, não uma verificação.** Não foi conferida nesta
tarefa nem em nenhuma que eu possa comprovar. Recomendo marcá-la como premissa
nos documentos até que alguém liste o conteúdo remoto — a listagem do
`public_html` via cPanel resolve em minutos e elimina um risco de perda total.

---

## 6. PRÓXIMOS PASSOS SUGERIDOS

Ordem recomendada, com a restrição de execução da seção 0:

| # | Ação | Bloqueio |
|---|---|---|
| 1 | Regerar e persistir `catalog-commercial-normalized.csv` em projeto + Drive | precisa de shell |
| 2 | Reescrever `.gitignore` antes de qualquer `git add` | pode ser entregue como arquivo pronto |
| 3 | CE-001 — init, commit, remote, push | precisa de shell ou do usuário |
| 4 | Ticket de negócio: baixar categoria de clubes brasileiros do fornecedor | decisão do usuário |
| 5 | Aplicar o pacote parado da V1 (seção 2.4) | arrastar arquivos, sem shell |
| 6 | CE-004 — modelo de dados V2, **reaproveitando a regra de modelo/variante da seção 2.1** | ChatGPT + Claude Code |

Para o item 2 eu posso entregar o `.gitignore` pronto nesta sessão, junto com
a lista exata do que deve e não deve subir, sem precisar de shell. Basta
pedir.

---

*Documento gerado por Claude (Cowork) em 12/09/2026 para sincronização com o
ChatGPT. Todos os números vêm de leitura direta do notebook `lp`, do Google
Drive ou do `catalogo.json`; nenhum foi estimado.*
