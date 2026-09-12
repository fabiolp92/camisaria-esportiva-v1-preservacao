# =====================================================================
#  CE-001 - Versionamento inicial do projeto Camisaria Esportiva FC
#  Gerado por Claude em 12/09/2026.
#
#  O que faz:  cria o repositorio Git local, confere o que vai entrar,
#              faz o primeiro commit e (opcional) envia para o GitHub.
#  O que NAO faz: nao apaga nada, nao altera nenhum arquivo do projeto,
#              nao faz push forcado. Se algo sair do esperado, para.
#
#  Basta executar. Ele pergunta antes de cada passo que importa.
# =====================================================================

$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.Encoding]::UTF8
$PROJETO = 'C:\Projetos\compreibaratofc-python'
$LIMITE_ARQUIVOS = 1500   # acima disso, quase certo que o .gitignore falhou
$LIMITE_MB = 50           # arquivo individual grande demais para o GitHub

function Titulo($t) {
    Write-Host ''
    Write-Host ('=' * 70) -ForegroundColor DarkCyan
    Write-Host "  $t" -ForegroundColor Cyan
    Write-Host ('=' * 70) -ForegroundColor DarkCyan
}
function Ok($t)    { Write-Host "  [ok]    $t" -ForegroundColor Green }
function Aviso($t) { Write-Host "  [aviso] $t" -ForegroundColor Yellow }
function Parar($t) {
    Write-Host ''
    Write-Host "  [PAROU] $t" -ForegroundColor Red
    Write-Host ''
    Write-Host '  Nada foi enviado. Copie esta tela e mande para o Claude.' -ForegroundColor Red
    Write-Host ''
    Read-Host '  Enter para fechar'
    exit 1
}
function Perguntar($t) {
    Write-Host ''
    $r = Read-Host "  $t  (s/n)"
    return ($r -eq 's' -or $r -eq 'S')
}

Titulo 'CE-001 - Primeiro commit do Camisaria Esportiva'

# ---------------------------------------------------------------- 1. Ambiente
Titulo '1 de 7 - Conferindo o ambiente'

try { $v = (git --version) 2>$null } catch { $v = $null }
if (-not $v) {
    Parar 'O Git nao esta instalado (ou nao esta no PATH). Instale em https://git-scm.com/download/win e rode este arquivo de novo.'
}
Ok "$v"

if (-not (Test-Path $PROJETO)) { Parar "A pasta $PROJETO nao existe." }
Set-Location $PROJETO
Ok "Pasta: $PROJETO"

# confere que e mesmo o projeto certo, e nao uma pasta parecida
foreach ($marca in @('publicar.py', 'modelos.py', '.gitignore')) {
    if (-not (Test-Path (Join-Path $PROJETO $marca))) {
        Parar "Nao encontrei '$marca' aqui. Esta pasta nao parece ser o projeto. Conferir antes de continuar."
    }
}
Ok 'Arquivos-marca do projeto encontrados'

$tamGitignore = (Get-Item -Force (Join-Path $PROJETO '.gitignore')).Length
if ($tamGitignore -lt 1000) {
    Parar "O .gitignore tem apenas $tamGitignore bytes. O correto tem cerca de 3.400 e cobre os 4 GB de acervo. Com este, o commit tentaria subir tudo. Avise o Claude antes de continuar."
}
Ok ".gitignore presente ($tamGitignore bytes)"

# ---------------------------------------------------------------- 2. Repositorio
Titulo '2 de 7 - Repositorio local'

if (Test-Path (Join-Path $PROJETO '.git')) {
    Aviso 'Ja existe um repositorio Git nesta pasta.'
    Write-Host ''
    git status --short --branch
    Write-Host ''
    Write-Host '  Este script so faz o primeiro commit, entao nao vai mexer aqui.' -ForegroundColor Yellow
    Read-Host '  Enter para fechar'
    exit 0
}

git init -b main 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    # Git anterior a 2.28 nao aceita '-b'
    git init | Out-Null
    if ($LASTEXITCODE -ne 0) { Parar 'Falhou ao criar o repositorio.' }
    git branch -M main | Out-Null
}
Ok 'Repositorio criado, branch principal: main'

# ---------------------------------------------------------------- 3. Identidade
Titulo '3 de 7 - Identidade do autor dos commits'

$nome  = (git config --get user.name)  2>$null
$email = (git config --get user.email) 2>$null

if ([string]::IsNullOrWhiteSpace($nome)) {
    Write-Host '  O Git ainda nao sabe seu nome.' -ForegroundColor Yellow
    $nome = Read-Host '  Seu nome (ex.: Fabio Lopes)'
    if ([string]::IsNullOrWhiteSpace($nome)) { Parar 'Nome vazio.' }
    git config user.name $nome
}
if ([string]::IsNullOrWhiteSpace($email)) {
    Write-Host '  O Git ainda nao sabe seu e-mail.' -ForegroundColor Yellow
    Write-Host '  Use o mesmo e-mail da sua conta do GitHub.' -ForegroundColor DarkGray
    $email = Read-Host '  Seu e-mail'
    if ([string]::IsNullOrWhiteSpace($email)) { Parar 'E-mail vazio.' }
    git config user.email $email
}
Ok "Autor: $nome <$email>"

# ---------------------------------------------------------------- 4. Conferencia
Titulo '4 de 7 - O que vai entrar no commit'
Write-Host '  Este e o passo que importa. Lendo a lista...' -ForegroundColor DarkGray
Write-Host '  (le a lista sem copiar nada, entao e rapido)' -ForegroundColor DarkGray

$lista = git -c core.quotepath=false status --porcelain -uall
if ($LASTEXITCODE -ne 0) { Parar 'Falhou ao ler o status.' }

$caminhos = @()
foreach ($linha in $lista) {
    if ($linha.Length -gt 3) { $caminhos += $linha.Substring(3).Trim('"') }
}
$total = $caminhos.Count
Write-Host ''
Write-Host "  Arquivos a versionar: $total" -ForegroundColor White

if ($total -eq 0) { Parar 'Nenhum arquivo a versionar. Algo esta errado.' }

# quebra por pasta de primeiro nivel
$porPasta = @{}
foreach ($c in $caminhos) {
    $p = $c -replace '\\', '/'
    $topo = if ($p.Contains('/')) { ($p -split '/')[0] + '/' } else { '(raiz)' }
    if ($porPasta.ContainsKey($topo)) { $porPasta[$topo]++ } else { $porPasta[$topo] = 1 }
}
Write-Host ''
Write-Host '  Por pasta:' -ForegroundColor White
$porPasta.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
    Write-Host ('    {0,-22} {1,6}' -f $_.Key, $_.Value)
}

# pastas que JAMAIS podem aparecer
$proibidas = @('fotos_originais/', 'publicar/', 'pacotes/', 'posts/', 'gerar/', 'gerados/', 'testes/')
$vazou = @()
foreach ($pr in $proibidas) { if ($porPasta.ContainsKey($pr)) { $vazou += $pr } }
if ($caminhos | Where-Object { ($_ -replace '\\','/') -like 'site/fotos/*' }) { $vazou += 'site/fotos/' }

if ($vazou.Count -gt 0) {
    Parar ("O .gitignore deixou passar pasta(s) de acervo: " + ($vazou -join ', ') + ". Nao commite assim - seriam GB de imagens. Avise o Claude.")
}
Ok 'Nenhuma pasta de acervo vazou'

if ($total -gt $LIMITE_ARQUIVOS) {
    Parar "Sao $total arquivos, acima do limite de seguranca ($LIMITE_ARQUIVOS). O esperado e algo entre 50 e 400. Avise o Claude antes de continuar."
}
Ok "Contagem dentro do esperado (limite de seguranca: $LIMITE_ARQUIVOS)"

# arquivos individualmente grandes
$grandes = @()
$bytes = 0
foreach ($c in $caminhos) {
    $f = Join-Path $PROJETO $c
    if (Test-Path $f -PathType Leaf) {
        $t = (Get-Item -Force $f).Length
        $bytes += $t
        if ($t -gt ($LIMITE_MB * 1MB)) { $grandes += ('{0}  ({1:N1} MB)' -f $c, ($t / 1MB)) }
    }
}
Write-Host ''
Write-Host ('  Tamanho total: {0:N1} MB' -f ($bytes / 1MB)) -ForegroundColor White
if ($grandes.Count -gt 0) {
    Aviso "Arquivo(s) acima de $LIMITE_MB MB - o GitHub rejeita acima de 100 MB:"
    $grandes | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
    if (-not (Perguntar 'Continuar mesmo assim?')) { Parar 'Cancelado por voce.' }
}

Write-Host ''
Write-Host '  Confira a lista acima. O esperado: os .py da raiz, scripts/,' -ForegroundColor DarkGray
Write-Host '  web/, elenco/, docs/, data/, site/catalogo.json e os textos.' -ForegroundColor DarkGray
if (-not (Perguntar 'Esta certo? Fazer o commit?')) { Parar 'Cancelado por voce. O repositorio ficou criado, mas vazio.' }

# ---------------------------------------------------------------- 5. Commit
Titulo '5 de 7 - Primeiro commit'

git add -A
if ($LASTEXITCODE -ne 0) { Parar 'Falhou ao preparar os arquivos.' }

$msg = @"
Primeiro commit - Camisaria Esportiva FC (V1)

Codigo, dados estruturais e documentacao do projeto.
O acervo de imagens (fotos_originais, site/fotos, publicar, pacotes,
gerar, gerados) fica fora do Git por tamanho, conforme .gitignore.

Inclui o catalogo comercial normalizado do CE-003
(data/catalog-commercial-normalized.csv, 2.597 registros).
"@

git commit -m $msg
if ($LASTEXITCODE -ne 0) { Parar 'Falhou ao fazer o commit.' }
Ok 'Commit feito'
Write-Host ''
git --no-pager log --oneline -1
git --no-pager show --stat --oneline HEAD | Select-Object -Last 1

# ---------------------------------------------------------------- 6. Remoto
Titulo '6 de 7 - Enviar para o GitHub (opcional)'
Write-Host '  Se voce ainda nao criou o repositorio no GitHub, crie agora em' -ForegroundColor DarkGray
Write-Host '  https://github.com/new  -  VAZIO, sem README e sem .gitignore.' -ForegroundColor DarkGray
Write-Host '  Sugestao: deixe como Private.' -ForegroundColor DarkGray
Write-Host ''
Write-Host '  Deixe em branco e tecle Enter para pular esta parte.' -ForegroundColor DarkGray
$url = Read-Host '  URL do repositorio (ex.: https://github.com/usuario/camisaria-esportiva.git)'

if ([string]::IsNullOrWhiteSpace($url)) {
    Titulo 'Concluido - so falta o envio'
    Ok 'Commit local pronto.'
    Write-Host ''
    Write-Host '  Para enviar depois, abra o PowerShell nesta pasta e rode:' -ForegroundColor White
    Write-Host '    git remote add origin <url-do-repositorio>' -ForegroundColor Gray
    Write-Host '    git push -u origin main' -ForegroundColor Gray
    Write-Host ''
    Read-Host '  Enter para fechar'
    exit 0
}

git remote add origin $url
if ($LASTEXITCODE -ne 0) { Parar 'Falhou ao registrar o endereco remoto. Confira a URL.' }
Ok "Remoto registrado: $url"

# ---------------------------------------------------------------- 7. Push
Titulo '7 de 7 - Enviando'
Write-Host '  Pode abrir uma janela pedindo login do GitHub. E normal.' -ForegroundColor DarkGray
Write-Host ''

git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Aviso 'O envio falhou, mas o commit local esta salvo e intacto.'
    Write-Host '  Causas comuns: repositorio nao existe, URL errada, ou login recusado.' -ForegroundColor Yellow
    Write-Host '  Para tentar de novo depois:  git push -u origin main' -ForegroundColor Yellow
    Write-Host ''
    Read-Host '  Enter para fechar'
    exit 1
}

Titulo 'Pronto - CE-001 concluido'
Ok 'Repositorio criado, commit feito e enviado ao GitHub.'
Write-Host ''
git --no-pager log --oneline -1
Write-Host ''
Write-Host "  Confira em: $url" -ForegroundColor White
Write-Host ''
Read-Host '  Enter para fechar'
