"""Montage motion design 1080x1920 piloté par les données (D) et le minutage de la voix (cues)."""
import functools, glob, math, random, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
WHITE, GREY = (255, 255, 255), (150, 152, 165)
ACCENT, GREEN, RED = (255, 122, 26), (52, 211, 120), (226, 27, 77)
INK = (12, 12, 16)
Y = 110


def _font_path(weight):
    import os
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", f"Inter-{weight}.otf")
    if os.path.exists(local):
        return local
    c = [p for p in glob.glob(f"/usr/share/fonts/**/Inter*{weight}*.*tf", recursive=True)
         if "Display" not in p and "Italic" not in p and "Variable" not in p]
    if not c:
        c = glob.glob("/usr/share/fonts/**/DejaVuSans-Bold.ttf", recursive=True)
    return sorted(c, key=len)[0]


@functools.lru_cache(None)
def font(w, s):
    return ImageFont.truetype(_font_path(w), s)


def ease_out(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def ease_back(x, s=1.9):
    x = max(0.0, min(1.0, x)); x -= 1; return x * x * ((s + 1) * x + s) + 1


@functools.lru_cache(None)
def text_img(txt, w, s, color, spacing=0):
    f = font(w, s)
    widths = [f.getlength(c) for c in txt] if spacing else None
    tw = int((sum(widths) + spacing * (len(txt) - 1)) if spacing else f.getlength(txt)) + 8
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (tw, asc + desc + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if spacing:
        x = 4
        for ch, cw in zip(txt, widths):
            d.text((x, 4), ch, font=f, fill=color + (255,)); x += cw + spacing
    else:
        d.text((4, 4), txt, font=f, fill=color + (255,))
    return im


def fit(txt, w, s, maxw, spacing=0):
    """Réduit la taille de police jusqu'à ce que le texte tienne dans maxw."""
    while s > 20 and text_img(txt, w, s, WHITE, spacing).width > maxw:
        s -= 4
    return s


def blit(canvas, im, x, y, anchor="mm", scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    ax = {"l": 0, "m": 0.5, "r": 1}[anchor[0]]; ay = {"t": 0, "m": 0.5, "b": 1}[anchor[1]]
    px, py = int(x - im.width * ax), int(y - im.height * ay)
    canvas.alpha_composite(im, (max(px, 0), max(py, 0)), (max(-px, 0), max(-py, 0)))


def text(canvas, txt, w, s, color, x, y, maxw=None, **kw):
    sp = kw.pop("spacing", 0)
    if maxw:
        s = fit(txt, w, s, maxw, sp)
    blit(canvas, text_img(txt, w, s, color, sp), x, y, **kw)


def panel(canvas, xy, fill, alpha=1.0, r=28, outline=None):
    if alpha <= 0.01: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(xy, radius=r, fill=fill[:3] + (int((fill[3] if len(fill) > 3 else 255) * alpha),),
                        outline=(outline[:3] + (int(outline[3] * alpha),)) if outline else None, width=3)
    canvas.alpha_composite(lay)


@functools.lru_cache(None)
def _badge(code, bg, fg, stripe, size):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im); r = size // 4
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=bg + (255,))
    d.rectangle([0, size * 0.74, size - 1, size * 0.84], fill=stripe + (255,))
    ti = text_img(code, "Black", int(size * 0.34), fg)
    im.alpha_composite(ti, ((size - ti.width) // 2, int(size * 0.38 - ti.height / 2)))
    mask = Image.new("L", (size, size), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=255)
    im.putalpha(Image.composite(im.getchannel("A"), mask, mask))
    return im


def badge(canvas, t, x, y, size, **kw):
    blit(canvas, _badge(t["code"], t["bg"], t["fg"], t["stripe"], size), x, y, **kw)


def build_bg(glow_rgb):
    base = Image.new("RGBA", (W, H), (9, 9, 12, 255))
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lines); c = (255, 255, 255, 14)
    d.ellipse([W / 2 - 260, H - 520, W / 2 + 260, H], outline=c, width=4)
    d.arc([-380, -880, W + 380, 1180], 20, 160, fill=c, width=4)
    d.rectangle([W / 2 - 250, -10, W / 2 + 250, 640], outline=c, width=4)
    d.line([0, H - 260, W, H - 260], fill=c, width=4)
    base.alpha_composite(lines)
    glow = Image.new("RGBA", (W + 600, H + 600), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse([0, 0, 1200, 1100], fill=glow_rgb + (150,))
    g.ellipse([700, 1500, 1680, 2500], fill=ACCENT + (70,))
    glow = glow.filter(ImageFilter.GaussianBlur(200))
    vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse([-250, -150, W + 250, H + 150], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(170))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(vig.point(lambda v: int((255 - v) * 0.7)))
    random.seed(3); grains = []
    for _ in range(4):
        n = Image.effect_noise((W // 2, H // 2), 60).resize((W, H)).convert("L")
        gr = Image.new("RGBA", (W, H), (255, 255, 255, 0)); gr.putalpha(n.point(lambda v: max(0, v - 150) // 6)); grains.append(gr)
    return base, glow, dark, grains


def bg_at(t, parts):
    base, glow, dark, grains = parts
    im = base.copy()
    ox = int(300 + 160 * math.sin(t * 0.35)); oy = int(300 + 120 * math.cos(t * 0.27))
    im.alpha_composite(glow.crop((ox, oy, ox + W, oy + H)))
    im.alpha_composite(dark)
    im.alpha_composite(grains[int(t * 12) % 4])
    return im


class Timeline:
    def __init__(self, cues, total):
        self.cues = cues
        order = []
        for c, a, b in cues:
            if c not in [o[0] for o in order]:
                order.append((c, a))
        self.S = {}
        for i, (c, a) in enumerate(order):
            start = 0.0 if i == 0 else max(0.0, a - 0.2)
            end = (order[i + 1][1] - 0.2) if i + 1 < len(order) else total + 1.4
            self.S[c] = (start, end)
        self.total = total + 1.4
        self.sub = {c: [(a, b) for cc, a, b in cues if cc == c] for c in self.S}

    def at(self, scene, frac):
        a, b = self.S[scene]; return a + (b - a) * frac

    def vis(self, t, scene, tin, fade_in=0.22, fade_out=0.2):
        if scene not in self.S: return 0.0, 0.0
        a, b = self.S[scene]
        if t < tin or t >= b: return 0.0, 0.0
        p = (t - tin) / fade_in
        return min(1.0, p) * min(1.0, (b - t) / fade_out), p


def count(v, t, t0, d=0.45):
    return int(round(v * ease_out((t - t0) / d))) if t >= t0 else 0


def content(t, D, TL):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); vis = TL.vis
    me, opp = D["me"], D["opp"]
    # A — stats
    if "A" in TL.S:
        subs = TL.sub["A"]
        for i, (v, lab) in enumerate(D["rows"]):
            t0 = subs[i][0] if i < len(subs) else TL.S["A"][0] + 0.8 * i
            if i == 0: t0 = 0.0
            y = 560 + 270 * i
            a, p = vis(t, "A", t0)
            if a:
                text(c, str(count(v, t, t0)), "Black", 260, WHITE, 480, y + Y, anchor="rm", alpha=a, scale=0.6 + 0.4 * ease_back(p / 1.6))
                text(c, lab, "ExtraBold", 86, ACCENT, 520, y + Y + 24, anchor="lm", alpha=a * min(1, p), spacing=3, maxw=520)
        if D["banner"] and len(subs) > 3:
            a, p = vis(t, "A", subs[3][0])
            if a:
                panel(c, [100, 1290 + Y, W - 100, 1470 + Y], (255, 255, 255, 235), a)
                text(c, D["banner"], "Black", 66, INK, W / 2, 1382 + Y, alpha=a, scale=0.7 + 0.3 * ease_back(p / 1.5), maxw=820)
    # B — carte joueur
    if "B" in TL.S:
        a, p = vis(t, "B", TL.at("B", 0.12), 0.3)
        if a:
            off = (1 - ease_out(p)) * 140
            panel(c, [80, 430 + Y + off, W - 80, 1400 + Y + off], (255, 255, 255, 18), a, 40, (255, 255, 255, 50))
            badge(c, me, W / 2, 580 + Y + off, 170, alpha=a)
            text(c, D["first"], "Black", 150, WHITE, W / 2, 800 + Y + off, alpha=a, maxw=860)
            text(c, D["last"], "Black", 100, ACCENT, W / 2, 935 + Y + off, alpha=a, maxw=860)
        t0 = TL.at("B", 0.5)
        a, p = vis(t, "B", t0, 0.12)
        if a:
            ti = text_img(D["stamp"], "Black", fit(D["stamp"], "Black", 92, 780), WHITE)
            st = Image.new("RGBA", (ti.width + 100, 180), (0, 0, 0, 0))
            ImageDraw.Draw(st).rounded_rectangle([6, 6, st.width - 6, 174], radius=22, fill=RED + (255,), outline=WHITE + (255,), width=6)
            st.alpha_composite(ti, ((st.width - ti.width) // 2, (180 - ti.height) // 2))
            blit(c, st, W / 2, 1125 + Y, alpha=a, scale=1.0 + 0.7 * (1 - ease_out(p / 2.2)), rot=-5)
        a, p = vis(t, "B", TL.at("B", 0.78))
        if a:
            text(c, D["line"], "ExtraBold", 56, WHITE, W / 2, 1290 + Y, alpha=a, maxw=860)
    # C — adresse
    if "C" in TL.S and D["fg"]:
        m, att = D["fg"]
        a, p = vis(t, "C", TL.S["C"][0])
        if a:
            text(c, "EFFICACITÉ", "Black", 124, WHITE, W / 2, 500 + Y, alpha=a, scale=0.85 + 0.15 * ease_out(p))
        t0 = TL.at("C", 0.5)
        a, p = vis(t, "C", t0)
        if a:
            cx, cy, R = W / 2, 1090 + Y, 290
            ring = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ring)
            d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(255, 255, 255, int(35 * a)), width=36)
            frac = m / att * ease_out((t - t0) / 1.1)
            if frac > 0: d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * frac, fill=ACCENT + (int(255 * a),), width=36)
            c.alpha_composite(ring)
            text(c, f"{count(m, t, t0, 0.9)}/{att}", "Black", 196, WHITE, cx, cy - 20, alpha=a, maxw=500)
            text(c, f"AUX TIRS  ·  {round(100 * frac)} %", "ExtraBold", 40, ACCENT, cx, cy + 125, alpha=a, spacing=2)
    # D — plus/minus
    if "D" in TL.S and D["pm"]:
        a, p = vis(t, "D", TL.S["D"][0])
        if a:
            text(c, "QUAND IL ÉTAIT", "ExtraBold", 76, WHITE, W / 2, 560 + Y, alpha=a, spacing=2)
            text(c, "SUR LE TERRAIN", "ExtraBold", 76, WHITE, W / 2, 652 + Y, alpha=a, spacing=2)
        t0 = TL.at("D", 0.6)
        a, p = vis(t, "D", t0, 0.15)
        if a:
            text(c, f"+{count(D['pm'], t, t0, 0.4)}", "Black", 380, GREEN, W / 2, 1040 + Y, alpha=a, scale=0.6 + 0.4 * ease_back(p / 2.5))
            badge(c, me, W / 2 - 300, 1290 + Y, 96, alpha=a * min(1, p))
            text(c, f"POUR {me['name']}", "Black", 62, WHITE, W / 2 + 50, 1290 + Y, alpha=a * min(1, p), spacing=3, maxw=600)
    # E — score
    if "E" in TL.S:
        a, p = vis(t, "E", TL.S["E"][0])
        if a:
            text(c, "VICTOIRE" if D["win"] else "DÉFAITE", "Black", 132, WHITE, W / 2, 500 + Y, alpha=a, scale=0.85 + 0.15 * ease_out(p))
        for k, (tm, pts, y, frac) in enumerate([(me, D["my_pts"], 830, 0.35), (opp, D["op_pts"], 1090, 0.62)]):
            won = pts == max(D["my_pts"], D["op_pts"])
            t0 = TL.at("E", frac)
            a, p = vis(t, "E", t0)
            if a:
                off = (1 - ease_out(p)) * 420 * (-1 if k == 0 else 1)
                panel(c, [90 + off, y - 110 + Y, W - 90 + off, y + 110 + Y], (255, 255, 255, 30 if won else 16), a, 32,
                      (255, 255, 255, 70 if won else 30))
                badge(c, tm, 205 + off, y + Y, 160, alpha=a)
                text(c, tm["name"], "Black", 78, WHITE if won else GREY, 310 + off, y + Y, anchor="lm", alpha=a, maxw=440)
                text(c, str(count(pts, t, t0 + 0.4, 0.6)), "Black", 132, ACCENT if won else GREY, W - 140 + off, y + Y, anchor="rm", alpha=a)
    # F — punchline
    if "F" in TL.S:
        l1, l2, small = D["punch"]
        a, p = vis(t, "F", TL.S["F"][0])
        if a:
            text(c, l1, "Black", 120, WHITE, W / 2, 660 + Y, alpha=a, scale=0.8 + 0.2 * ease_back(p / 1.5), maxw=900)
        t2 = TL.at("F", 0.3)
        a, p = vis(t, "F", t2)
        if a:
            text(c, l2, "Black", 120, ACCENT, W / 2, 800 + Y, alpha=a, scale=0.8 + 0.2 * ease_back(p / 1.2), maxw=900)
        a, p = vis(t, "F", TL.at("F", 0.62))
        if a:
            panel(c, [100, 1010 + Y, W - 100, 1150 + Y], (255, 255, 255, 235), a)
            text(c, small.upper(), "Black", 58, INK, W / 2, 1080 + Y, alpha=a, scale=0.9 + 0.1 * ease_out(p), maxw=820)
    # G — CTA
    if "G" in TL.S:
        g0 = TL.S["G"][0] + 0.1
        a, p = vis(t, "G", g0, 0.3, 0.01)
        if a:
            text(c, "LE CHIFFRE DE LA NUIT", "Black", 66, ACCENT, W / 2, 760 + Y, alpha=a, spacing=6)
            text(c, "chaque matin", "SemiBold", 46, WHITE, W / 2, 840 + Y, alpha=a)
            if t >= g0 + 0.15:
                btn = Image.new("RGBA", (660, 150), (0, 0, 0, 0)); bd = ImageDraw.Draw(btn)
                bd.rounded_rectangle([0, 0, 659, 149], radius=75, fill=ACCENT + (255,))
                lab = text_img("+  ABONNE-TOI", "Black", 64, (14, 10, 6)); btn.alpha_composite(lab, ((660 - lab.width) // 2, (150 - lab.height) // 2))
                blit(c, btn, W / 2, 1020 + Y, alpha=a, scale=0.6 + 0.4 * ease_back((t - g0 - 0.15) / 0.35))
    return c


def header(im, t, D, TL):
    g = TL.S.get("G", (1e9, 0))[0]
    ha = min(1.0, t / 0.3) * (1.0 if t < g else max(0.0, 1 - (t - g) / 0.3))
    text(im, "LE CHIFFRE DE LA NUIT", "Black", 54, ACCENT, W / 2, 170, alpha=ha, spacing=6)
    badge(im, D["me"], W / 2 - 200, 252, 72, alpha=ha)
    text(im, f"{D['my_pts']} – {D['op_pts']}", "ExtraBold", 46, WHITE, W / 2, 250, alpha=ha)
    badge(im, D["opp"], W / 2 + 200, 252, 72, alpha=ha)
    text(im, D["date_label"], "SemiBold", 30, GREY, W / 2, 330, alpha=ha, spacing=4, maxw=900)


def scene_zoom(t, TL):
    for a, b in TL.S.values():
        if a <= t < b: return 1.0 + 0.035 * (t - a) / max(0.1, b - a)
    return 1.0


def frame(t, D, TL, parts):
    im = bg_at(t, parts)
    c = content(t, D, TL); z = scene_zoom(t, TL)
    if z != 1.0:
        zw, zh = int(W * z), int(H * z)
        c = c.resize((zw, zh), Image.BILINEAR).crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    im.alpha_composite(c)
    header(im, t, D, TL)
    return im.convert("RGB")


def render(D, cues, total, out_mp4):
    TL = Timeline(cues, total)
    parts = build_bg(D["me"]["bg"])
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out_mp4], stdin=subprocess.PIPE)
    for i in range(int(TL.total * FPS)):
        p.stdin.write(frame(i / FPS, D, TL, parts).tobytes())
    p.stdin.close(); p.wait()
    return TL
