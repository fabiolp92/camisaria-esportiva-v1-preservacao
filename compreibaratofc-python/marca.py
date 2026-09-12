# -*- coding: utf-8 -*-
"""Recorta a arte da marca e gera os arquivos que o site e as redes usam.

    python marca.py

Entrada: as imagens da marca, na pasta arte/
Saída:   os ícones e a capa, direto em web/, mais a pasta arte/redes/
         com os tamanhos certos pro Instagram e pro Facebook.

Rodar de novo é seguro: ele só reescreve os arquivos que gera.

SE A ARTE MUDAR
Troque os arquivos em arte/ e reconfira as duas linhas de recorte lá embaixo
(CAMISA_NA_QUADRADA e ESCUDO_NA_QUADRADA). São coordenadas dentro da imagem:
(esquerda, topo, direita, base), em pixels. Rode o script e olhe os arquivos
gerados — se o recorte cortou algo, mexa nos números e rode de novo.
"""
import os
from PIL import Image, ImageOps, ImageStat

AQUI  = os.path.dirname(os.path.abspath(__file__))
ARTE  = os.path.join(AQUI, "arte")
WEB   = os.path.join(AQUI, "web")
REDES = os.path.join(ARTE, "redes")

QUADRADA = "marca-quadrada.jpg"    # o quadro de perto, quadrado
LARGA    = "marca-larga.jpg"       # a estante inteira, deitada

# Onde está cada coisa dentro da marca-quadrada.jpg (1024x1024)
CAMISA_NA_QUADRADA = (275, 225, 750, 620)   # a camisa preta com o escudo
ESCUDO_NA_QUADRADA = (525, 318, 638, 418)   # só o escudo CE


def abrir(nome):
    caminho = os.path.join(ARTE, nome)
    if not os.path.exists(caminho):
        raise SystemExit(f"Não achei {caminho}.\n"
                         f"Coloque as imagens da marca na pasta arte/ "
                         f"com os nomes: {QUADRADA} e {LARGA}")
    return Image.open(caminho).convert("RGB")


def cor_de_fundo(img, caixa=(0, 0, 40, 40)):
    """A cor média de um cantinho da arte. Serve pra completar espaço vazio
    com um tom que pertence à imagem, em vez de um preto ou branco chapado
    que denunciaria a montagem."""
    return tuple(int(v) for v in ImageStat.Stat(img.crop(caixa)).mean[:3])


def quadrado(img, margem=0.08, fundo=None):
    """Centraliza a arte num quadrado, com respiro em volta."""
    fundo = fundo or cor_de_fundo(img)
    l = int(max(img.size) * (1 + margem * 2))
    tela = Image.new("RGB", (l, l), fundo)
    tela.paste(img, ((l - img.width) // 2, (l - img.height) // 2))
    return tela


def recorta_proporcao(img, larg, alt):
    """Corta pelo centro na proporção pedida e redimensiona, sem distorcer."""
    return ImageOps.fit(img, (larg, alt), Image.LANCZOS, centering=(0.5, 0.5))


def encaixa(img, larg, alt, fundo=None):
    """O contrário do recorta: cabe a arte INTEIRA no tamanho pedido e
    preenche o que sobra. Usado no story do Instagram, que é 9:16 — cortar
    a arte quadrada nessa proporção comeria metade do logo."""
    fundo = fundo or cor_de_fundo(img)
    copia = img.copy()
    copia.thumbnail((larg, alt), Image.LANCZOS)
    tela = Image.new("RGB", (larg, alt), fundo)
    tela.paste(copia, ((larg - copia.width) // 2, (alt - copia.height) // 2))
    return tela


def main():
    os.makedirs(WEB, exist_ok=True)
    os.makedirs(REDES, exist_ok=True)

    quad  = abrir(QUADRADA)
    larga = abrir(LARGA)
    pergaminho = cor_de_fundo(quad, (300, 250, 340, 290))

    camisa = quadrado(quad.crop(CAMISA_NA_QUADRADA), 0.06, pergaminho)
    escudo = quadrado(quad.crop(ESCUDO_NA_QUADRADA), 0.14, pergaminho)

    feitos = []

    # ------------------------------------------------------------ ícones
    # No favicon quem manda é a SILHUETA, não o detalhe. A 16px o escudo
    # com as letras CE vira uma mancha; a camisa preta no pergaminho
    # continua reconhecível. Por isso a camisa vale pra todos os tamanhos.
    for tam, nome in [(16, "favicon-16.png"), (32, "favicon-32.png"),
                      (48, "favicon-48.png"), (180, "apple-touch-icon.png"),
                      (512, "icone-512.png")]:
        camisa.resize((tam, tam), Image.LANCZOS).save(os.path.join(WEB, nome))
        feitos.append(nome)
    camisa.resize((48, 48), Image.LANCZOS).save(
        os.path.join(WEB, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    feitos.append("favicon.ico")

    # o emblema ao lado do nome, no topo do site
    camisa.resize((152, 152), Image.LANCZOS).save(os.path.join(WEB, "marca-ce.png"))
    feitos.append("marca-ce.png")

    # o escudo sozinho, pra quando precisar de um selo pequeno
    escudo.resize((256, 256), Image.LANCZOS).save(os.path.join(WEB, "escudo-ce.png"))
    feitos.append("escudo-ce.png")

    # -------------------------------------------------------- capa de link
    # É o que aparece quando alguém manda o link no WhatsApp ou no Facebook.
    # 1200x630 é a medida que os dois usam.
    recorta_proporcao(larga, 1200, 630).save(
        os.path.join(WEB, "capa-camisaria-esportiva.jpg"), "JPEG",
        quality=88, optimize=True)
    feitos.append("capa-camisaria-esportiva.jpg")

    # -------------------------------------------------------------- redes
    madeira = cor_de_fundo(larga, (0, 0, 60, 60))
    redes = [
        ("instagram-perfil.jpg",  recorta_proporcao(quad, 640, 640)),
        ("instagram-post.jpg",    recorta_proporcao(quad, 1080, 1080)),
        ("instagram-story.jpg",   encaixa(quad, 1080, 1920, madeira)),
        ("facebook-capa.jpg",     recorta_proporcao(larga, 1640, 624)),
        ("facebook-perfil.jpg",   recorta_proporcao(quad, 512, 512)),
        ("whatsapp-perfil.jpg",   recorta_proporcao(quad, 640, 640)),
    ]
    for nome, img in redes:
        img.save(os.path.join(REDES, nome), "JPEG", quality=90, optimize=True)

    print(f"\nweb/  {len(feitos)} arquivos:")
    for f in feitos:
        print(f"   {f}")
    print(f"\narte/redes/  {len(redes)} arquivos:")
    for n, _ in redes:
        print(f"   {n}")
    print("\nOs de web/ entram no site na próxima publicação (python publicar.py).")
    print("Os de arte/redes/ são pra você subir no Instagram e no Facebook.")


if __name__ == "__main__":
    main()
