@echo off
REM Atalho para rodar o limpar-raiz.ps1 sem esbarrar na politica de execucao
REM do PowerShell. Basta dar dois cliques neste arquivo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0limpar-raiz.ps1"
