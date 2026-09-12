# =====================================================================
#  Limpeza da raiz C:\Projetos - Camisaria Esportiva FC
#  Gerado por Claude em 12/09/2026.
#
#  O que faz:  move os arquivos soltos da raiz de C:\Projetos para a
#              subpasta _arquivo-raiz-2026-09-12. Nada e apagado.
#  O que NAO faz: nao toca nas pastas compreibaratofc-python e
#              camisaria-esportiva-v2, nao apaga nenhum arquivo.
#
#  Motivo: os arquivos soltos sao uma copia de 07/09 do site. As
#  versoes atuais estao em compreibaratofc-python\web e \publicar.
# =====================================================================

$ErrorActionPreference = 'Stop'
$RAIZ    = 'C:\Projetos'
$DESTINO = Join-Path $RAIZ '_arquivo-raiz-2026-09-12'
$MANTER  = @('compreibaratofc-python', 'camisaria-esportiva-v2', '_arquivo-raiz-2026-09-12')

function Ok($t)    { Write-Host "  [ok]    $t" -ForegroundColor Green }
function Aviso($t) { Write-Host "  [aviso] $t" -ForegroundColor Yellow }
function Parar($t) {
    Write-Host ''
    Write-Host "  [PAROU] $t" -ForegroundColor Red
    Write-Host ''
    Read-Host '  Enter para fechar'
    exit 1
}

Write-Host ''
Write-Host ('=' * 70) -ForegroundColor DarkCyan
Write-Host '  Limpeza da raiz C:\Projetos' -ForegroundColor Cyan
Write-Host ('=' * 70) -ForegroundColor DarkCyan

if (-not (Test-Path $RAIZ)) { Parar "A pasta $RAIZ nao existe." }

# confere que as duas pastas de projeto estao mesmo aqui
foreach ($p in @('compreibaratofc-python', 'camisaria-esportiva-v2')) {
    if (-not (Test-Path (Join-Path $RAIZ $p) -PathType Container)) {
        Parar "Nao encontrei a pasta '$p'. Esta raiz nao parece a certa."
    }
}
Ok 'As duas pastas de projeto estao no lugar'

$itens = @(Get-ChildItem -Force -LiteralPath $RAIZ |
           Where-Object { $MANTER -notcontains $_.Name -and $_.Name -notlike 'limpar-raiz.*' })

if ($itens.Count -eq 0) {
    Ok 'A raiz ja esta limpa. Nada a mover.'
    Read-Host '  Enter para fechar'
    exit 0
}

Write-Host ''
Write-Host "  Itens a mover para _arquivo-raiz-2026-09-12: $($itens.Count)" -ForegroundColor White
Write-Host ''
$itens | ForEach-Object {
    $tipo = if ($_.PSIsContainer) { '[pasta]' } else { '       ' }
    Write-Host ("    {0} {1}" -f $tipo, $_.Name)
}

Write-Host ''
$r = Read-Host '  Mover estes itens?  (s/n)'
if ($r -ne 's' -and $r -ne 'S') { Parar 'Cancelado por voce. Nada foi movido.' }

if (-not (Test-Path $DESTINO)) { New-Item -ItemType Directory -Path $DESTINO | Out-Null }
Ok "Pasta de arquivo morto pronta: $DESTINO"

$movidos = 0
foreach ($i in $itens) {
    $alvo = Join-Path $DESTINO $i.Name
    if (Test-Path -LiteralPath $alvo) {
        Aviso "Ja existe no destino, pulando: $($i.Name)"
        continue
    }
    Move-Item -LiteralPath $i.FullName -Destination $alvo
    $movidos++
}

Write-Host ''
Ok "$movidos item(ns) movido(s). Nada foi apagado."
Write-Host ''
Write-Host '  A raiz agora contem:' -ForegroundColor White
Get-ChildItem -Force -LiteralPath $RAIZ | ForEach-Object { Write-Host "    $($_.Name)" }
Write-Host ''
Write-Host '  Se algo estiver faltando, os arquivos estao intactos em' -ForegroundColor DarkGray
Write-Host "  $DESTINO" -ForegroundColor DarkGray
Write-Host ''
Read-Host '  Enter para fechar'
