@echo off
REM Atalho para rodar o git-inicial.ps1 sem esbarrar na politica de execucao
REM do PowerShell. Basta dar dois cliques neste arquivo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0git-inicial.ps1"
