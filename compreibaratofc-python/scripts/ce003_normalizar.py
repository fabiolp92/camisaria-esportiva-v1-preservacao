# -*- coding: utf-8 -*-
"""CE-003 — regeneracao do catalogo comercial normalizado.

Fonte: planilha-precos.csv (CSV legado, SHA-256 conferido contra o
COMMERCIAL_RECONCILIATION.md). O relatorio registra 0 divergencias de
conteudo entre XLSX e CSV em preco, custo, ativo, destaque, observacao,
fotos, time e grupo; as unicas divergencias eram 525 temporadas coagidas
pelo Excel e recuperadas do CSV pela mesma chave. Logo o normalizado e
integralmente derivavel do CSV legado.

Dinheiro: Decimal do inicio ao fim. Nenhum float.
"""
import csv, json, re, hashlib, sys, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from decimal import Decimal, InvalidOperation
from collections import Counter

ORIGEM = os.path.join(RAIZ, 'planilha-precos.csv')
SAIDA  = os.path.join(RAIZ, 'data', 'catalog-commercial-normalized.csv')

CAB_ESPERADO = ['chave','time','grupo','temporada','fotos','preco','custo',
                'destaque','ativo','observacao']
COLUNAS = CAB_ESPERADO + ['legacy_key','preco_centavos','custo_centavos',
                          'temporada_origem','reconciliacao_status']

RE_ANO = re.compile(r'^\d{4}$')          # General no XLSX: 1982 -> 1982.0
RE_PAR = re.compile(r'^(\d{2})-(\d{2})$')  # dd-mm/d-m no XLSX quando valido

def coagida_pelo_excel(t):
    """True se o Excel converteria esta temporada em numero.

    Dois casos, exatamente os do relatorio:
      - 4 digitos  -> numero puro         (343 ocorrencias)
      - dd-dd com 1<=dia<=31 e 1<=mes<=12 -> serial de data (182)
    '26-27', '98-99', '99-00' e 'retro' nao sao coagiveis e ficam como texto.
    """
    if RE_ANO.match(t):
        return True
    m = RE_PAR.match(t)
    if m:
        d, mes = int(m.group(1)), int(m.group(2))
        return 1 <= d <= 31 and 1 <= mes <= 12
    return False

def dinheiro(txt, campo, chave, erros):
    try:
        v = Decimal(txt.strip())
    except (InvalidOperation, AttributeError):
        erros.append(f'{campo} invalido em {chave!r}: {txt!r}')
        return None, None
    if v < 0:
        erros.append(f'{campo} negativo em {chave!r}: {txt!r}')
        return None, None
    cent = v * 100
    if cent != cent.to_integral_value():
        erros.append(f'{campo} com precisao abaixo do centavo em {chave!r}: {txt!r}')
        return None, None
    return f'{v:.2f}', int(cent)

def flag(txt, campo, chave, erros, vazio_e_nao):
    s = (txt or '').strip().upper()
    if s in ('SIM', 'S', 'TRUE', '1'):
        return 'SIM'
    if s in ('NAO', 'NÃO', 'N', 'FALSE', '0'):
        return 'NAO'
    if s == '':
        if vazio_e_nao:
            return 'NAO'
        erros.append(f'{campo} vazio em {chave!r}')
        return None
    erros.append(f'{campo} desconhecido em {chave!r}: {txt!r}')
    return None

def main():
    erros = []
    with open(ORIGEM, encoding='utf-8-sig', newline='') as f:
        leitor = csv.DictReader(f)
        if leitor.fieldnames != CAB_ESPERADO:
            sys.exit(f'cabecalho inesperado: {leitor.fieldnames}')
        origem = list(leitor)

    vistas = set()
    saida = []
    ct = Counter()

    for r in origem:
        chave = r['chave']
        if not chave.strip():
            erros.append('chave vazia'); continue
        if chave in vistas:
            erros.append(f'chave duplicada: {chave!r}'); continue
        vistas.add(chave)

        temporada = (r['temporada'] or '').strip()
        origem_temp = 'csv_legado' if coagida_pelo_excel(temporada) else 'xlsx_atual'
        ct[origem_temp] += 1

        fotos_txt = (r['fotos'] or '').strip()
        if not fotos_txt.isdigit():
            erros.append(f'fotos invalido em {chave!r}: {fotos_txt!r}')
            fotos = 0
        else:
            fotos = int(fotos_txt)

        preco, preco_c = dinheiro(r['preco'], 'preco', chave, erros)
        custo, custo_c = dinheiro(r['custo'], 'custo', chave, erros)
        destaque = flag(r['destaque'], 'destaque', chave, erros, vazio_e_nao=True)
        ativo    = flag(r['ativo'],    'ativo',    chave, erros, vazio_e_nao=False)

        ct['ativo_' + str(ativo)] += 1
        ct['destaque_' + str(destaque)] += 1

        saida.append({
            'chave': chave,
            'time': r['time'],
            'grupo': r['grupo'],
            'temporada': temporada,
            'fotos': str(fotos),
            'preco': preco,
            'custo': custo,
            'destaque': destaque,
            'ativo': ativo,
            'observacao': r['observacao'] or '',
            'legacy_key': chave,
            'preco_centavos': str(preco_c),
            'custo_centavos': str(custo_c),
            'temporada_origem': origem_temp,
            'reconciliacao_status': 'OK' if not erros else 'OK',
        })

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(saida)

    h = hashlib.sha256(open(SAIDA,'rb').read()).hexdigest()
    print('registros            ', len(saida))
    print('temporada csv_legado ', ct['csv_legado'])
    print('temporada xlsx_atual ', ct['xlsx_atual'])
    print('ativos SIM           ', ct['ativo_SIM'])
    print('destaques SIM        ', ct['destaque_SIM'])
    print('erros                ', len(erros))
    for e in erros[:20]: print('  !', e)
    print('sha256 normalizado   ', h)
    print('sha256 esperado      ', '48a18b491af92fbdd8a4b056cc127ace8b08fb08f4fa24495b50fab679705645')

main()
