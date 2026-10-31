#!/usr/bin/env python3
"""Genera las carátulas (póster 2:3) y los banners (2:1) de la web de Menger Studio.

Uso: python3 caratulas.py <carpeta_fuentes> <carpeta_salida>
Las fuentes (OFL, Google Fonts): Bungee, Audiowide, PixelifySans, ShareTechMono, Unbounded.
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

JOCS = Path.home() / "Projects/Jocs"
FONTS = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

POSTER = (600, 900)
BANNER = (1280, 640)


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def cover_crop(img, size, focus=(0.5, 0.5)):
    """Recorta y escala `img` para llenar `size` sin deformar."""
    w, h = size
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    img = img.resize((round(iw * scale), round(ih * scale)), Image.LANCZOS)
    iw, ih = img.size
    x = round((iw - w) * focus[0])
    y = round((ih - h) * focus[1])
    return img.crop((x, y, x + w, y + h))


def gradient(size, stops, vertical=True):
    """Capa RGBA con un degradado de (pos, (r,g,b,a))."""
    w, h = size
    g = Image.new("RGBA", size)
    px = g.load()
    n = h if vertical else w
    cols = []
    for i in range(n):
        t = i / max(1, n - 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                k = (t - p0) / max(1e-6, p1 - p0)
                cols.append(tuple(round(a + (b - a) * k) for a, b in zip(c0, c1)))
                break
        else:
            cols.append(stops[-1][1])
    for y in range(h):
        for x in range(w):
            px[x, y] = cols[y] if vertical else cols[x]
    return g


def text_glow(base, xy, text, fnt, fill, glow, radius=14, anchor="mm", stroke=0, stroke_fill=None):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy, text, font=fnt, fill=glow, anchor=anchor, stroke_width=stroke + 4, stroke_fill=glow)
    layer = layer.filter(ImageFilter.GaussianBlur(radius))
    base.alpha_composite(layer)
    d = ImageDraw.Draw(base)
    d.text(xy, text, font=fnt, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def fit_font(name, text, max_w, start, weight=None):
    size = start
    while size > 10:
        f = font(name, size, weight)
        if f.getlength(text) <= max_w:
            return f
        size -= 2
    return font(name, size, weight)


def studio_mark(img, color=(255, 255, 255, 200)):
    d = ImageDraw.Draw(img)
    f = font("Unbounded%5Bwght%5D.ttf", 15, 600)
    w, h = img.size
    # mini alfombra de Menger
    s = 18
    x0, y0 = 26, h - 26 - s
    for i in range(3):
        for j in range(3):
            if i == 1 and j == 1:
                continue
            d.rectangle([x0 + i * s / 3, y0 + j * s / 3, x0 + (i + 1) * s / 3 - 1.5, y0 + (j + 1) * s / 3 - 1.5], fill=color)
    d.text((x0 + s + 10, y0 + s / 2), "MENGER STUDIO", font=f, fill=color, anchor="lm")


def save(img, name):
    img.convert("RGB").save(OUT / f"{name}.webp", "WEBP", quality=84, method=6)


# ---------- Rodamons ----------
def rodamons(size, banner=False):
    shot = Image.open(JOCS / "Rodamons/docs/capturas/05-carrera-1j.png").convert("RGB")
    # quitar el HUD de las esquinas recortando el centro
    shot = shot.crop((180, 120, 1420, 860))
    img = cover_crop(shot, size, (0.5, 0.55)).convert("RGBA")
    w, h = size
    img.alpha_composite(gradient(size, [(0, (255, 120, 40, 120)), (0.35, (0, 0, 0, 0)), (0.62, (0, 0, 0, 0)), (1, (20, 8, 40, 235))]))
    title = fit_font("Bungee-Regular.ttf", "RODAMONS", w * 0.86, 120)
    ty = h * (0.2 if not banner else 0.24)
    text_glow(img, (w / 2, ty), "RODAMONS", title, (255, 214, 64), (255, 90, 0, 255), 16, stroke=5, stroke_fill=(60, 20, 0))
    sub = font("Unbounded%5Bwght%5D.ttf", 22 if not banner else 26, 700)
    d = ImageDraw.Draw(img)
    d.text((w / 2, ty + title.size * 0.8), "KART · 1–4 P", font=sub, fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(40, 10, 0))
    studio_mark(img)
    return img


# ---------- MathDungeon ----------
def mathdungeon(size, banner=False):
    shot = Image.open(JOCS / "MathDungeon/docs/captura_mapa.png").convert("RGB")
    shot = shot.crop((420, 120, 1060, 560))  # la sala con el héroe
    sw, sh = shot.size
    shot = shot.resize((sw * 3, sh * 3), Image.NEAREST)
    img = cover_crop(shot, size, (0.5, 0.5)).convert("RGBA")
    w, h = size
    # viñeta morada
    vig = Image.new("L", size, 0)
    dv = ImageDraw.Draw(vig)
    dv.ellipse([-w * 0.25, -h * 0.1, w * 1.25, h * 1.1], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(80))
    dark = Image.new("RGBA", size, (18, 6, 28, 255))
    img = Image.composite(img, dark, vig)
    img.alpha_composite(gradient(size, [(0, (18, 6, 28, 220)), (0.3, (0, 0, 0, 0)), (0.7, (0, 0, 0, 0)), (1, (18, 6, 28, 240))]))
    pf = "PixelifySans%5Bwght%5D.ttf"
    t1 = fit_font(pf, "MATH", w * 0.6, 150, 700)
    t2 = fit_font(pf, "DUNGEON", w * 0.86, 130, 700)
    if banner:
        t1 = font(pf, 110, 700)
        t2 = font(pf, 110, 700)
        text_glow(img, (w / 2, h * 0.22), "MATH DUNGEON", t2, (255, 210, 90), (200, 60, 255, 255), 18, stroke=4, stroke_fill=(40, 0, 50))
    else:
        text_glow(img, (w / 2, h * 0.13), "MATH", t1, (255, 210, 90), (200, 60, 255, 255), 18, stroke=4, stroke_fill=(40, 0, 50))
        text_glow(img, (w / 2, h * 0.13 + t1.size * 0.95), "DUNGEON", t2, (255, 210, 90), (200, 60, 255, 255), 18, stroke=4, stroke_fill=(40, 0, 50))
    d = ImageDraw.Draw(img)
    sub = font(pf, 30, 500)
    d.text((w / 2, h * 0.86 if not banner else h * 0.78), "ROGUELIKE  ·  + − × ÷", font=sub, fill=(230, 200, 255), anchor="mm")
    studio_mark(img)
    return img


# ---------- FractalBlast ----------
def menger_carpet(d, x, y, s, depth, fill):
    if depth == 0:
        d.rectangle([x, y, x + s, y + s], outline=fill, width=1)
        return
    t = s / 3
    for i in range(3):
        for j in range(3):
            if i == 1 and j == 1:
                d.rectangle([x + t, y + t, x + 2 * t, y + 2 * t], outline=fill, width=2 if depth > 1 else 1)
                continue
            menger_carpet(d, x + i * t, y + j * t, t, depth - 1, fill)


def fractalblast(size, banner=False):
    w, h = size
    rnd = random.Random(7)
    img = gradient(size, [(0, (8, 6, 40, 255)), (0.6, (20, 10, 70, 255)), (1, (60, 10, 80, 255))])
    d = ImageDraw.Draw(img)
    for _ in range(int(w * h / 900)):
        x, y = rnd.random() * w, rnd.random() * h
        b = rnd.randint(90, 255)
        r = rnd.choice([0.6, 0.8, 1.2, 1.8])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, 255, 255))
    # alfombra de Menger brillante
    car = Image.new("RGBA", size, (0, 0, 0, 0))
    dc = ImageDraw.Draw(car)
    s = min(w, h) * (0.95 if not banner else 0.9)
    cx, cy = w / 2, h * (0.52 if not banner else 0.5)
    menger_carpet(dc, cx - s / 2, cy - s / 2, s, 3, (90, 220, 255, 150))
    car = car.rotate(12, resample=Image.BICUBIC, center=(cx, cy))
    glow = car.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(glow)
    img.alpha_composite(car)
    sp = JOCS / "FractalBlast/assets/sprites/kenney"

    def put(name, x, y, scale=1.0, rot=0):
        s_ = Image.open(sp / name).convert("RGBA")
        s_ = s_.resize((round(s_.width * scale), round(s_.height * scale)), Image.LANCZOS)
        if rot:
            s_ = s_.rotate(rot, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(s_, (round(x - s_.width / 2), round(y - s_.height / 2)))
        return s_

    k = 1.0 if not banner else 0.9
    put("meteorBrown_big1.png", w * 0.72, h * 0.42, 1.25 * k, 20)
    fnum = font("Audiowide-Regular.ttf", 42)
    d = ImageDraw.Draw(img)
    d.text((w * 0.72, h * 0.42), "12", font=fnum, fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(60, 30, 10))
    put("enemyRed1.png", w * 0.25, h * 0.33, 0.9 * k, 180)
    put("ufoBlue.png", w * 0.16, h * 0.5, 0.8 * k)
    put("enemyGreen2.png", w * 0.42, h * (0.27 if not banner else 0.4), 0.7 * k, 180)
    for i in range(3):
        put("laserBlue01.png", w * 0.5, h * (0.58 - i * 0.07), 1.0)
    put("playerShip1_blue.png", w * 0.5, h * (0.76 if not banner else 0.8), 1.2 * k)
    img.alpha_composite(gradient(size, [(0, (0, 0, 0, 0)), (0.82, (0, 0, 0, 0)), (1, (10, 0, 30, 200))]))
    title = fit_font("Audiowide-Regular.ttf", "FRACTALBLAST", w * 0.88, 110)
    ty = h * 0.12 if not banner else h * 0.15
    text_glow(img, (w / 2, ty), "FRACTALBLAST", title, (255, 255, 255), (0, 200, 255, 255), 14)
    sub = font("Audiowide-Regular.ttf", 22)
    ImageDraw.Draw(img).text((w / 2, ty + title.size * 0.85), "2 · 3 · 5 · 7", font=sub, fill=(255, 220, 80), anchor="mm")
    studio_mark(img)
    return img


# ---------- Narthex ----------
def narthex(size, banner=False):
    w, h = size
    rnd = random.Random(3)
    img = Image.new("RGBA", size, (2, 8, 6, 255))
    mono = font("ShareTechMono-Regular.ttf", 18)
    glyphs = "ΝΑΡΘΗΞ01ΠΡΟΜΗΘΕΥΣ<>/{}#$%&*+=?ΣΔΩΛΦΨ"
    cell = 18
    # silueta del móvil: la lluvia brilla más dentro
    phone = (w * 0.27, h * 0.22, w * 0.73, h * 0.86) if not banner else (w * 0.62, h * 0.1, w * 0.84, h * 0.92)
    rain = Image.new("RGBA", size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(rain)
    for cx in range(0, w, cell):
        head = rnd.random() * h * 1.4
        length = rnd.uniform(0.3, 0.8) * h
        for cy in range(0, h, cell):
            dist = head - cy
            if dist < 0 or dist > length:
                a = 25
            else:
                a = int(255 * (1 - dist / length) ** 1.6)
            inside = phone[0] < cx < phone[2] and phone[1] < cy < phone[3]
            if inside:
                a = min(255, a + 60)
            col = (180, 255, 210, a) if dist >= 0 and dist < cell else (40, 255, 140, a)
            dr.text((cx, cy), rnd.choice(glyphs), font=mono, fill=col)
    img.alpha_composite(rain.filter(ImageFilter.GaussianBlur(5)))
    img.alpha_composite(rain)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(phone, radius=28, outline=(150, 255, 200, 230), width=4)
    # grietas
    ox, oy = phone[0] + (phone[2] - phone[0]) * 0.62, phone[1] + (phone[3] - phone[1]) * 0.3
    for _ in range(9):
        x, y = ox, oy
        ang = rnd.uniform(0, 2 * math.pi)
        for _ in range(rnd.randint(3, 6)):
            ang += rnd.uniform(-0.6, 0.6)
            nx, ny = x + math.cos(ang) * rnd.uniform(15, 45), y + math.sin(ang) * rnd.uniform(15, 45)
            nx = min(max(nx, phone[0] + 4), phone[2] - 4)
            ny = min(max(ny, phone[1] + 4), phone[3] - 4)
            d.line([x, y, nx, ny], fill=(230, 255, 240, 220), width=2)
            x, y = nx, ny
    # llama de Prometeo dentro del móvil
    fl = Image.new("RGBA", size, (0, 0, 0, 0))
    df = ImageDraw.Draw(fl)
    fx, fy = (phone[0] + phone[2]) / 2, phone[1] + (phone[3] - phone[1]) * 0.62
    fs = (phone[2] - phone[0]) * 0.32
    df.polygon([(fx, fy - fs * 1.4), (fx + fs * 0.55, fy - fs * 0.2), (fx + fs * 0.4, fy + fs * 0.45), (fx, fy + fs * 0.6),
                (fx - fs * 0.4, fy + fs * 0.45), (fx - fs * 0.55, fy - fs * 0.2)], fill=(255, 150, 40, 255))
    df.polygon([(fx, fy - fs * 0.6), (fx + fs * 0.25, fy + fs * 0.1), (fx, fy + fs * 0.45), (fx - fs * 0.25, fy + fs * 0.1)], fill=(255, 235, 140, 255))
    img.alpha_composite(fl.filter(ImageFilter.GaussianBlur(18)))
    img.alpha_composite(fl)
    img.alpha_composite(gradient(size, [(0, (0, 0, 0, 200)), (0.2, (0, 0, 0, 0)), (0.8, (0, 0, 0, 0)), (1, (0, 0, 0, 220))]))
    title = fit_font("ShareTechMono-Regular.ttf", "N A R T H E X", w * 0.84 if not banner else w * 0.48, 84)
    ty = h * 0.1 if not banner else h * 0.5
    tx = w / 2 if not banner else w * 0.32
    text_glow(img, (tx, ty), "N A R T H E X", title, (220, 255, 235), (40, 255, 140, 255), 12)
    sub = font("ShareTechMono-Regular.ttf", 22)
    ImageDraw.Draw(img).text((tx, ty + title.size * 0.85), "> code_cam · AR", font=sub, fill=(255, 170, 60), anchor="mm")
    studio_mark(img)
    return img


for name, fn in [("rodamons", rodamons), ("narthex", narthex), ("fractalblast", fractalblast), ("mathdungeon", mathdungeon)]:
    save(fn(POSTER), f"{name}-poster")
    save(fn(BANNER, banner=True), f"{name}-banner")
    print("ok", name)
