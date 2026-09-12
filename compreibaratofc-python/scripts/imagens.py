# -*- coding: utf-8 -*-
"""Compressão das fotos. É a única parte pesada do projeto, e roda na sua máquina.

Regra: entre caber grande e feio, ou menor e nítido, escolhe nítido. As fotos do
fornecedor têm fundo de tela quadriculada, que é caríssimo de comprimir — a 900px
elas só entrariam em 35KB com qualidade 26, e aí a camisa vira borrão. Então a
gente desce a dimensão até a qualidade voltar a ficar acima de Q_BOM.

Truque de velocidade: a busca binária só precisa SABER o tamanho, não precisa de
um arquivo bonito. Então ela roda com method=0 (rápido) e só o vencedor é gravado
de novo com METODO (lento e menor). São até 63 codificações caras por foto viradas
em 63 baratas mais uma cara.
"""
import io
from PIL import Image

ALVO_KB = 35
LADOS   = (900, 800, 700, 620, 550, 480, 420, 360, 320)
Q_MIN, Q_MAX = 14, 92
Q_BOM   = 50
METODO       = 4   # esforço do WebP na gravação final
METODO_BUSCA = 0   # esforço durante a busca: serve só pra medir tamanho


def quadrar(im):
    """Deixa a foto 1:1 completando com a cor da borda, pra peça caber inteira
    no card sem corte e sem barra visível."""
    w, h = im.size
    if w == h:
        return im
    lado = max(w, h)
    faixa = max(2, min(w, h) // 40)
    px = (list(im.crop((0, 0, w, faixa)).getdata()) +
          list(im.crop((0, h - faixa, w, h)).getdata()) +
          list(im.crop((0, 0, faixa, h)).getdata()) +
          list(im.crop((w - faixa, 0, w, h)).getdata()))
    cor = tuple(sorted(p[i] for p in px)[len(px) // 2] for i in range(3))
    fundo = Image.new("RGB", (lado, lado), cor)
    fundo.paste(im, ((lado - w) // 2, (lado - h) // 2))
    return fundo


def _tamanho(im, q, formato, metodo=METODO):
    b = io.BytesIO()
    if formato == "WEBP":
        im.save(b, "WEBP", quality=q, method=metodo)
    else:
        im.save(b, "JPEG", quality=q, optimize=True, progressive=True)
    return b.tell(), b.getvalue()


def _maior_q(im, alvo, formato):
    """Maior qualidade que ainda cabe no alvo, por busca binária: ~6 tentativas
    em vez das 27 de descer de 2 em 2."""
    lo, hi, achado = Q_MIN, Q_MAX, None
    while lo <= hi:
        meio = (lo + hi) // 2
        tam, dados = _tamanho(im, meio, formato, METODO_BUSCA)
        if tam <= alvo:
            achado = (meio, tam, dados); lo = meio + 1
        else:
            hi = meio - 1
    return achado


def _gravar(destino, im, q, formato, alvo, dados_busca):
    """Regrava o vencedor com o esforço alto. method maior gera arquivo MENOR na
    mesma qualidade, então normalmente cabe folgado — mas se por qualquer motivo
    estourar o alvo, fica o resultado da busca, que já sabemos que cabia."""
    if formato == "WEBP":
        tam, dados = _tamanho(im, q, formato, METODO)
        if tam > alvo:
            dados = dados_busca
    else:
        dados = dados_busca
    open(destino, "wb").write(dados)
    return len(dados)


def comprimir(origem, destino, alvo_kb=ALVO_KB):
    """Grava a foto otimizada e devolve (bytes, largura)."""
    formato = "WEBP" if destino.lower().endswith(".webp") else "JPEG"
    alvo = alvo_kb * 1024
    original = quadrar(Image.open(origem).convert("RGB"))
    reserva = reserva_im = None
    for lado in LADOS:
        im = original.copy()
        im.thumbnail((lado, lado), Image.LANCZOS)
        r = _maior_q(im, alvo, formato)
        if r and r[0] >= Q_BOM:
            return _gravar(destino, im, r[0], formato, alvo, r[2]), im.width
        if r and (reserva is None or r[0] > reserva[0]):
            reserva, reserva_im = r, im
    if reserva:
        return _gravar(destino, reserva_im, reserva[0], formato, alvo, reserva[2]), reserva_im.width
    dados = _tamanho(im, Q_MIN, formato, METODO)[1]
    open(destino, "wb").write(dados)
    return len(dados), im.width
