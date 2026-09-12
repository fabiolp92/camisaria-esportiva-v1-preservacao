# AUDITORIA-SEGREDOS-CE-001.md

**Projeto:** Camisaria Esportiva FC · V1
**Tarefa:** CE-001 — Risco 1 do `GIT_VERSIONING_RULES.md` (§5)
**Data:** 12/09/2026
**Resultado:** **LIMPO — nenhum segredo encontrado. O primeiro commit está liberado.**

---

## 1. O que foi verificado

Todos os 18 arquivos `.py` do projeto, mais os dois `LEIA-ME`:

**Raiz:** `baixar.py`, `build.py`, `publicar.py`, `modelos.py`, `marca.py`, `posts.py`, `planilha.py`, `raras.py`, `instalar.py`
**`scripts/`:** `fornecedor.py`, `importar.py`, `paginas.py`, `exportar.py`, `banco.py`, `cobica.py`, `imagens.py`, `semear.py`, `ce003_normalizar.py`
**Textos:** `LEIA-ME.txt`, `LEIA-ME-PUBLICAR.txt`

Os quatro arquivos que a §5 mandava priorizar — `baixar.py`, `scripts/fornecedor.py`, `publicar.py`, `instalar.py` — estão entre eles.

## 2. Padrões procurados

- Palavras-chave: senha, password, passwd, pwd, secret, token, api_key, apikey, credential, auth, ftp, cpanel, sftp, ssh, bearer
- Formatos de chave: `sk-…`, `AKIA…` (AWS), cabeçalhos `Basic …`
- URLs com credencial embutida (`protocolo://usuario:senha@host`)
- Atribuições do tipo `user =`, `login =`, `host =`, `porta =`, `conta =`
- E-mails e endereços de servidor

## 3. O que apareceu — e por que não é segredo

| Ocorrência | Onde | Avaliação |
|---|---|---|
| `cPanel` | `publicar.py` (bloco `HTACCESS`, instruções de upload) e `LEIA-ME-PUBLICAR.txt` | Texto explicativo e marcador gerado pelo próprio cPanel. Nenhuma credencial. |
| `token` | comentários em `scripts/fornecedor.py` e `scripts/importar.py` | Refere-se a token de *texto* na quebra de nomes ("cr7" era descartado como token curto). Sem relação com autenticação. |
| `www.clubsimports.com` | `baixar.py`, `scripts/fornecedor.py` | URL pública do fornecedor. O download usa apenas `User-Agent`, sem cookie, sessão, login ou cabeçalho de autorização. |
| `camisariaesportiva.com.br`, `wa.me/…`, Instagram, Facebook, Google Fonts | `paginas.py`, `publicar.py`, `marca.py` | Endereços públicos da própria loja. |
| `googlede0be7ed28f500b2.html` | `web/` | Arquivo de verificação do Search Console. Público por natureza — precisa ser servido para funcionar. |

**Nenhuma senha, chave de API, token de acesso, credencial de FTP/cPanel ou arquivo `.env` foi encontrado em qualquer parte do código.**

## 4. Por que o código não tem credencial

A arquitetura da V1 não precisa de nenhuma:

- **Download do fornecedor** (`baixar.py`): HTTP público, só `User-Agent`. Não há login.
- **Publicação** (`publicar.py`): gera a pasta `publicar/` e um `.zip` no disco. O upload é **manual**, pelo Gerenciador de Arquivos do cPanel. O script nunca fala com o servidor.
- **Banco** (`scripts/banco.py`): SQLite em arquivo local. Sem usuário nem senha.

Ou seja: não é que a credencial esteja bem guardada — é que não existe credencial no fluxo.

## 5. Proteção para o futuro

O `.gitignore` (§8) já bloqueia preventivamente `.env`, `.env.*`, `segredos.py`, `credenciais.json`, `*.pem`, `*.key`, `*.pfx`, `ftp.cfg` e `.netrc`. Se um dia a publicação virar automática por FTP ou API, a credencial vai para um desses arquivos — nunca para dentro de um `.py`.

## 6. Efeito sobre o CE-001

O Risco 1 era o **único bloqueante** do primeiro commit (§5 do `GIT_VERSIONING_RULES.md`). Ele está resolvido.

Continua valendo, por outro motivo, a decisão da §1: **o repositório deve ser privado**, porque `planilha-precos.csv` carrega a coluna `custo`.
