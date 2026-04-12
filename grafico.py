from PIL import Image, ImageDraw
import random


def criar_grafico_pil(largura=600, altura=250):

    img = Image.new("RGB", (largura, altura), "#000000")
    draw = ImageDraw.Draw(img)

    # =========================
    # GRID
    # =========================
    cor_grid = "#16202a"

    for i in range(1, 6):
        y = int((altura / 6) * i)
        draw.line((0, y, largura, y), fill=cor_grid)

    for i in range(1, 6):
        x = int((largura / 6) * i)
        draw.line((x, 0, x, altura), fill=cor_grid)

    # =========================
    # VELAS
    # =========================
    velas = []

    for _ in range(5):
        open_ = random.uniform(1, 2)
        close_ = random.uniform(1, 2)

        high_ = max(open_, close_) + random.uniform(0.1, 0.3)
        low_ = min(open_, close_) - random.uniform(0.1, 0.3)

        velas.append((open_, close_, high_, low_))

    maximo = max(v[2] for v in velas)
    minimo = min(v[3] for v in velas)

    escala = altura / (maximo - minimo + 0.0001)

    x = 40
    largura_vela = 30

    for open_, close_, high_, low_ in velas:

        y_open = altura - ((open_ - minimo) * escala)
        y_close = altura - ((close_ - minimo) * escala)
        y_high = altura - ((high_ - minimo) * escala)
        y_low = altura - ((low_ - minimo) * escala)

        topo = min(y_open, y_close)
        base = max(y_open, y_close)

        if close_ > open_:
            cor = (0, 230, 118)
        else:
            cor = (255, 23, 68)

        # pavio
        draw.line((x + 15, y_high, x + 15, y_low), fill=cor, width=2)

        # corpo
        draw.rectangle((x, topo, x + largura_vela, base), fill=cor)

        x += 80

    return img
