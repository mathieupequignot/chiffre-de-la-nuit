"""Série « 5 trucs fous sur… » — top 10 décompté, sous-titres mot à mot, visuels animés, voix off.
Épisode 1 : Victor Wembanyama (faits vérifiés : ESPN, CBS, Eurohoops, Sixth Tone, Le 10 Sport, Brut, Business Cool, Orange).
usage : python -m top10.main [--out out_top10]"""
import argparse, math, os, re, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from chiffre import tts
from chiffre.render import (W, H, FPS, ACCENT, WHITE, GREY, font, text, text_img, blit, panel,
                            build_bg, bg_at, ease_out, ease_back)

SR = 48000
YEL = (255, 214, 10)
RED = (235, 64, 52)
GREEN = (52, 211, 120)
SILVER = (196, 206, 214)

PHOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "wemby.png")
N = 5
EPISODES = {
    # cue = identifiant du visuel ; num = numéro affiché
    "a": dict(
        title=("5 TRUCS FOUS", "SUR WEMBY"), header="5 TRUCS FOUS SUR WEMBY",
        cover=("5 TRUCS", "FOUS SUR", "WEMBY"), file="5_trucs_fous_wemby",
        num={"10": 5, "9": 4, "7": 3, "4": 2, "1": 1},
        segs=[
            ("H", "[excited] Tu crois connaître Wemby ? Voici cinq trucs complètement fous sur lui."),
            ("10", "Numéro cinq. À onze ans, il mesurait déjà un mètre quatre-vingt-onze… autant que sa mère !"),
            ("9", "Numéro quatre. Son envergure ? Deux mètres quarante-trois. Plus large qu'une voiture !"),
            ("7", "Numéro trois. À dix ans, il fait un essai au FC Barcelone… et il préfère rester à Nanterre."),
            ("4", "Numéro deux. Après un match à New York, il donne rendez-vous à ses fans… pour jouer aux échecs, sous la pluie. Battu deux fois par des pros… mais il a battu son frère."),
            ("1", "[excited] Et numéro un. Pendant sa retraite chez les moines Shaolin, tout le monde mange végan… mais plusieurs fois par jour, une camionnette venait le chercher pour un repas protéiné… à l'extérieur des murs !"),
            ("E", "[excited] Lequel t'a le plus surpris ? Dis-le en commentaire… et dis-moi quel joueur tu veux dans le prochain épisode !"),
        ]),
    "b": dict(
        title=("5 TRUCS QUE TU", "IGNORES SUR WEMBY"), header="CE QUE TU IGNORES SUR WEMBY",
        cover=("5 TRUCS QUE", "TU IGNORES SUR", "WEMBY"), file="5_trucs_wemby_tu_ne_savais_pas",
        num={"6": 5, "8": 4, "5": 3, "3": 2, "2": 1},
        segs=[
            ("H", "[excited] Cinq trucs que tu ne savais pas sur Wemby… et le numéro un va te faire rire."),
            ("6", "Numéro cinq. Depuis son arrivée en NBA, il a pris plus de treize kilos… de muscle."),
            ("8", "Numéro quatre. Son père faisait du triple saut : record à quinze mètres cinquante-six… et le cent mètres en onze secondes."),
            ("5", "Numéro trois. [surprised] Il a encore grandi ! Deux mètres vingt-deux à son arrivée en NBA… deux mètres vingt-six aujourd'hui sur sa fiche officielle."),
            ("3", "Numéro deux. Il a passé dix jours chez les moines Shaolin : crâne rasé, kung-fu tous les jours, et réveil à quatre heures et demie."),
            ("2", "[laughs] Et numéro un. Problème : les lits du temple faisaient un mètre quatre-vingt-dix. Il ne pouvait même pas étendre ses jambes !"),
            ("E", "[excited] Lequel t'a le plus surpris ? Dis-le en commentaire… et dis-moi quel joueur tu veux dans le prochain épisode !"),
        ]),
}
EP = EPISODES["a"]
TITLE, HEADER, NUM, SEGS = EP["title"], EP["header"], EP["num"], EP["segs"]
ORDER = [c for c, _ in SEGS]


VIS = {}


def use(ep):
    """ep : 'a'/'b' (épisodes Wemby) ou chemin d'un épisode JSON (voir top10/SERIE.md)."""
    global EP, TITLE, HEADER, NUM, SEGS, ORDER, VIS, PHOTO
    if ep in EPISODES:
        EP = EPISODES[ep]
    else:
        import json
        J = json.load(open(ep, encoding="utf-8"))
        facts = J["facts"]  # du n°5 au n°1
        n = len(facts)
        EP = dict(title=tuple(J["title"]), header=J["header"], cover=tuple(J["cover"]), file=J["file"],
                  num={f"f{i}": n - i for i in range(n)}, nba_id=J.get("nba_id"),
                  segs=[("H", J["hook"])] + [(f"f{i}", f["voice"]) for i, f in enumerate(facts)] + [("E", J["outro"])])
        VIS = {f"f{i}": f["visual"] for i, f in enumerate(facts)}
        EP["json"] = J
        ph = os.path.join(os.path.dirname(PHOTO), J.get("photo", "none.png"))
        PHOTO = ph
    TITLE, HEADER, NUM, SEGS = EP["title"], EP["header"], EP["num"], EP["segs"]
    ORDER = [c for c, _ in SEGS]
    global N
    N = len(NUM)


# ---------------------------------------------------------------- outils de dessin
def emoji(ch, size):
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
        im = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((70, 70), ch, font=f, embedded_color=True, anchor="mm")
        im = im.crop(im.getbbox() or (0, 0, 140, 140))
        return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)
    except Exception:
        return None


def outlined(txt, w, s, fill, stroke=10, sc=(0, 0, 0)):
    f = font(w, s)
    bb = f.getbbox(txt, stroke_width=stroke)
    im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), txt, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=sc + (255,))
    return im


def bar(c, x0, y, wfull, frac, h, color, alpha=1.0, label=None, val=None):
    panel(c, [x0, y - h / 2, x0 + wfull, y + h / 2], (255, 255, 255, 22), alpha, r=h / 2)
    if frac > 0.01:
        panel(c, [x0, y - h / 2, x0 + max(h, wfull * frac), y + h / 2], color + (255,), alpha, r=h / 2)
    if label:
        text(c, label, "Black", 46, WHITE, x0, y - h / 2 - 40, anchor="lm", alpha=alpha)
    if val:
        text(c, val, "Black", 54, color, x0 + wfull, y - h / 2 - 40, anchor="rm", alpha=alpha)


def num(v, p, dec=2):
    s = f"{v * p:.{dec}f}"
    return s.replace(".", ",")


PH = None


def _fit(ph, bw, bh):
    k = min(bw / ph.width, bh / ph.height)
    return ph.resize((max(1, int(ph.width * k)), max(1, int(ph.height * k))), Image.LANCZOS)


def _fade(im, start):
    f = Image.new("L", im.size, 255); d = ImageDraw.Draw(f)
    for y in range(im.height):
        v = max(0, (y - im.height * start) / (im.height * (1 - start)))
        d.line([0, y, im.width, y], fill=int(255 * (1 - v)))
    im.putalpha(Image.composite(im.getchannel("A"), Image.new("L", im.size, 0), f))
    return im


def head_box(ph):
    """Carré autour de la tête : haut de la silhouette, centré sur les pixels opaques du haut."""
    a = np.array(ph.getchannel("A")) > 40
    rows = np.where(a.any(1))[0]; top = int(rows[0]) if len(rows) else 0
    full = ph.height / ph.width > 1.25  # photo en pied
    side = int(ph.height * 0.17) if full else (int(ph.height * 0.62) if ph.height < ph.width else int(ph.width * 0.46))
    band = a[top:top + max(4, int(side * 0.6))]
    xs = np.where(band.any(0))[0]
    cx = int(xs.mean()) if len(xs) else ph.width // 2
    x0 = max(0, min(ph.width - side, cx - side // 2)); y0 = max(0, top - int(side * 0.06))
    return (x0, y0, x0 + side, y0 + side)


def load_photo():
    """Photo détourée (portrait ou en pied) : grande (accroche), moyenne (fin), avatar rond (en-tête)."""
    if not os.path.exists(PHOTO):
        return None
    ph = Image.open(PHOTO).convert("RGBA")
    full = ph.height / ph.width > 1.25
    big = _fade(_fit(ph, 1180, 1250), 0.72 if full else 0.62)
    mid = _fade(_fit(ph, 860, 950), 0.65 if full else 0.55)
    face = ph.crop(head_box(ph)).resize((110, 110), Image.LANCZOS)
    av = Image.new("RGBA", (124, 124), (0, 0, 0, 0)); da = ImageDraw.Draw(av)
    da.ellipse([0, 0, 123, 123], fill=ACCENT + (255,))
    bgc = Image.new("RGBA", (110, 110), (30, 30, 40, 255)); bgc.alpha_composite(face)
    m = Image.new("L", (110, 110), 0); ImageDraw.Draw(m).ellipse([0, 0, 109, 109], fill=255)
    av.paste(bgc, (7, 7), m)
    return {"big": big, "mid": mid, "avatar": av, "raw": ph}


# ---------------------------------------------------------------- timeline / sous-titres
class TL:
    def __init__(self, cues, total):
        self.c = {k: (a, b) for k, a, b in cues}
        self.total = total + 1.2
        ks = [k for k, _, _ in cues]
        self.span = {}
        for i, k in enumerate(ks):
            a = 0.0 if i == 0 else self.c[k][0] - 0.12
            b = self.c[ks[i + 1]][0] - 0.12 if i + 1 < len(ks) else self.total
            self.span[k] = (a, b)

    def at(self, t):
        for k, (a, b) in self.span.items():
            if a <= t < b:
                return k, t - a, b - a
        return ORDER[-1], t, 1


def words_from_last():
    """[(mot, début, fin)] depuis l'horodatage caractère de la dernière synthèse (balises [..] ignorées)."""
    L = tts.LAST
    if not L:
        return []
    txt, st, en = L["text"], L["starts"], L["ends"]
    out = []
    for m in re.finditer(r"\[[^\]]*\]|\S+", txt):
        w = m.group(0)
        if w.startswith("["):
            continue
        a, b = m.start(), min(m.end() - 1, len(st) - 1)
        if a < len(st):
            out.append((w, st[a], en[b]))
    return out


def chunks(words, maxn=3):
    """Groupes de 1 à 3 mots, coupés à la ponctuation."""
    g, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= maxn or re.search(r"[.!?…:,;]$", w[0]):
            g.append(cur); cur = []
    if cur: g.append(cur)
    return g


def captions(c, t, groups):
    for g in groups:
        a, b = g[0][1], g[-1][2] + 0.12
        if a - 0.05 <= t < b:
            ims = []
            for w, ws, we in g:
                on = ws - 0.03 <= t
                col = YEL if (ws - 0.03 <= t < we + 0.08) else WHITE
                ims.append((outlined(w.upper().strip("…"), "Black", 82, col, 9), on, ws))
            tot = sum(i.width for i, _, _ in ims) + 18 * (len(ims) - 1)
            sc = 1.0 if tot < 980 else 980 / tot
            x = W / 2 - tot * sc / 2
            for im, on, ws in ims:
                pop = 0.86 + 0.14 * ease_back(min(1, (t - ws) / 0.16)) if on else 1
                blit(c, im, x + im.width * sc / 2, 1515, scale=sc * pop, alpha=1 if on else 0.0)
                x += (im.width + 18) * sc
            return


# ---------------------------------------------------------------- visuels génériques (épisodes en JSON)
COLS = {"accent": ACCENT, "silver": SILVER, "yellow": YEL, "red": RED, "green": GREEN, "brown": (150, 100, 60),
        "blue": (0, 54, 120), "wine": (165, 0, 68)}


def _num_anim(v, e):
    """Anime un nombre écrit à la française ('1,91', '+13', '15,56') ; renvoie le texte tel quel sinon."""
    m = re.fullmatch(r"([+-]?)(\d+)(?:,(\d+))?", v)
    if not m:
        return v
    dec = len(m.group(3) or "")
    x = float(m.group(2) + "." + (m.group(3) or "0"))
    return m.group(1) + f"{x * e:.{dec}f}".replace(".", ",")


def generic(c, V, p, cy=900):
    a = min(1, p / 0.25); e = ease_out((p - 0.5) / 1.2)
    t = V.get("type", "big")
    pop = 0.85 + 0.15 * ease_back(min(1, p / 0.4))
    if t == "big":
        val = _num_anim(V["value"], e) if V.get("count", True) else V["value"]
        text(c, val + V.get("unit", ""), "Black", 220, WHITE, W / 2, cy - 60, alpha=a, scale=pop, maxw=1000)
        if V.get("label"): text(c, V["label"], "Black", 58, ACCENT, W / 2, cy + 100, alpha=a * ease_out((p - 1.2) / 0.4), maxw=960)
        if V.get("sub"): text(c, V["sub"], "Black", 52, SILVER, W / 2, cy + 190, alpha=ease_out((p - 2.2) / 0.4), maxw=960)
    elif t == "bars":
        if V.get("value"): text(c, V["value"], "Black", 190, WHITE, W / 2, cy - 200, alpha=a, scale=pop, maxw=1000)
        if V.get("label"): text(c, V["label"], "Black", 58, ACCENT, W / 2, cy - 40, alpha=a, maxw=960)
        for i, (lab, val, frac, col) in enumerate(V["bars"]):
            g = ease_out((p - 1.0 - 0.6 * i) / 0.9)
            bar(c, 120, cy + 120 + i * 170, 840, g * frac, 52, COLS.get(col, ACCENT), min(1, g * 2), lab, val)
        if V.get("note"): text(c, V["note"], "Black", 56, YEL, W / 2, cy + 120 + len(V["bars"]) * 170, alpha=ease_out((p - 3.0) / 0.4), maxw=960)
    elif t == "versus":
        b1, b2 = ease_out((p - 0.4) / 0.4), ease_out((p - 2.0) / 0.4)
        panel(c, [110, cy - 250, 970, cy - 70], COLS.get(V.get("no_col", "wine"), RED) + (255,), b1, r=34)
        text(c, V["no"], "Black", 76, WHITE, W / 2, cy - 160, alpha=b1, maxw=820)
        if b2 > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(lay).line([150, cy - 230, 930, cy - 90], fill=RED + (int(255 * b2),), width=18); c.alpha_composite(lay)
        panel(c, [110, cy + 40, 970, cy + 220], COLS.get(V.get("yes_col", "blue"), GREEN) + (255,), b2, r=34)
        text(c, V["yes"], "Black", 76, WHITE, W / 2, cy + 130, alpha=b2, maxw=820)
        if V.get("sub"): text(c, V["sub"], "Black", 56, SILVER, W / 2, cy + 320, alpha=b1, maxw=960)
    elif t == "list":
        text(c, V["value"], "Black", 180, WHITE, W / 2, cy - 160, alpha=a, scale=pop, maxw=1000)
        if V.get("label"): text(c, V["label"], "Black", 58, ACCENT, W / 2, cy - 30, alpha=a, maxw=960)
        for i, lab in enumerate(V.get("items", [])[:3]):
            b = ease_out((p - 1.6 - 0.9 * i) / 0.35)
            panel(c, [150, cy + 70 + i * 120, 930, cy + 170 + i * 120], (255, 255, 255, 24), b, r=26)
            text(c, lab, "Black", 50, YEL if i == len(V["items"]) - 1 else WHITE, W / 2, cy + 120 + i * 120, alpha=b, maxw=740)
    elif t == "emoji":
        if V.get("top"):
            b1 = ease_out((p - 0.3) / 0.4)
            panel(c, [130, cy - 330, 950, cy - 170], COLS.get(V.get("top_col", "green"), GREEN) + (255,), b1, r=30)
            text(c, V["top"], "Black", 56, WHITE, W / 2, cy - 250, alpha=b1, maxw=760)
        em = emoji(V.get("emoji", "🏀"), 260)
        b2 = ease_out((p - 1.2) / 0.6)
        k_ = 0.75 if (V.get("top") and V.get("bottom")) else 1.0  # entre deux bandeaux : emoji plus petit (pas de chevauchement)
        if em is not None: blit(c, em, W / 2, cy + (15 if k_ < 1 else 10), alpha=b2, scale=k_ * (0.8 + 0.2 * ease_back(min(1, max(0, p - 1.2) / 0.4))))
        if V.get("bottom"):
            b3 = ease_out((p - 3.0) / 0.4)
            panel(c, [90, cy + 200, 990, cy + 360], YEL + (255,), b3, r=30)
            text(c, V["bottom"], "Black", 54, (20, 20, 20), W / 2, cy + 280, alpha=b3, maxw=860)
    if V.get("shout"):
        st = V.get("shout_at", 3.4)
        text(c, V["shout"], "Black", 104, YEL, W / 2, 610, alpha=ease_out((p - st) / 0.3),
             scale=0.8 + 0.2 * ease_back(min(1, max(0, p - st) / 0.3)), maxw=980)


# ---------------------------------------------------------------- visuels par fait (épisodes Wemby codés à la main)
def visual(c, k, p, d, SIL):
    """p : secondes depuis le début du fait ; d : durée du fait."""
    if k in VIS:
        return generic(c, VIS[k], p * max(1.0, 6.0 / max(d, 0.5)))  # fait court : animations accélérées
    a = min(1, p / 0.25)
    e = ease_out((p - 0.5) / 1.2)
    cy = 900
    if k == "10":
        text(c, num(1.91, e) + " m", "Black", 230, WHITE, W / 2, cy - 40, alpha=a, scale=0.85 + 0.15 * ease_back(min(1, p / 0.4)))
        text(c, "AUTANT QUE SA MÈRE", "Black", 58, ACCENT, W / 2, cy + 110, alpha=a * ease_out((p - 2.2) / 0.4))
        text(c, "À SEULEMENT 11 ANS", "Black", 58, SILVER, W / 2, cy + 200, alpha=a * ease_out((p - 1.2) / 0.4))
    elif k == "9":
        text(c, num(2.43, e) + " m", "Black", 200, WHITE, W / 2, cy - 190, alpha=a)
        text(c, "D'ENVERGURE", "Black", 60, ACCENT, W / 2, cy - 30, alpha=a)
        g = ease_out((p - 1.0) / 1.0)
        bar(c, 120, cy + 120, 840, g, 46, ACCENT, a, "WEMBY", "2,43 m")
        bar(c, 120, cy + 280, 840, g * 1.80 / 2.43, 46, SILVER, a * ease_out((p - 1.4) / 0.4), "UNE VOITURE", "≈ 1,80 m")
    elif k == "8":
        text(c, num(15.56, e) + " m", "Black", 190, WHITE, W / 2, cy - 90, alpha=a)
        text(c, "RECORD DE SON PÈRE AU TRIPLE SAUT", "Black", 46, ACCENT, W / 2, cy + 40, alpha=a, maxw=960)
        b = ease_out((p - 2.2) / 0.5)
        panel(c, [190, cy + 120, 890, cy + 270], (255, 255, 255, 26), b, r=30)
        text(c, "100 M EN 11 SECONDES", "Black", 64, YEL, W / 2, cy + 195, alpha=b, maxw=660)
    elif k == "7":
        b1, b2 = ease_out((p - 0.4) / 0.4), ease_out((p - 2.0) / 0.4)
        panel(c, [110, cy - 250, 970, cy - 70], (165, 0, 68, 255), b1, r=34)
        text(c, "FC BARCELONE", "Black", 80, WHITE, W / 2, cy - 160, alpha=b1)
        if b2 > 0:
            c2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(c2)
            dd.line([150, cy - 230, 930, cy - 90], fill=RED + (int(255 * b2),), width=18)
            c.alpha_composite(c2)
        panel(c, [110, cy + 40, 970, cy + 220], (0, 54, 120, 255), b2, r=34)
        text(c, "NANTERRE ✓", "Black", 80, WHITE, W / 2, cy + 130, alpha=b2)
        text(c, "À 10 ANS", "Black", 56, SILVER, W / 2, cy + 320, alpha=b1)
    elif k == "6":
        text(c, "+" + num(13, e, 0) + " KG", "Black", 230, WHITE, W / 2, cy - 30, alpha=a, scale=0.85 + 0.15 * ease_back(min(1, p / 0.4)))
        text(c, "DE MUSCLE DEPUIS LA NBA", "Black", 58, ACCENT, W / 2, cy + 140, alpha=a * ease_out((p - 1.5) / 0.4), maxw=960)
    elif k == "5":
        g = ease_out((p - 0.6) / 1.0)
        base = 1300
        for i, (lab, v, col, tt) in enumerate([("ARRIVÉE EN NBA", 2.22, SILVER, 0.6), ("AUJOURD'HUI", 2.26, ACCENT, 3.0)]):
            b = ease_out((p - tt) / 0.6)
            x = 330 + i * 420; hgt = (v - 1.8) / 0.5 * 560 * b
            panel(c, [x - 110, base - hgt, x + 110, base], col + (255,), min(1, b * 2) * a, r=24)
            text(c, num(v, 1) + " m", "Black", 84, WHITE, x, base - hgt - 60, alpha=b)
            text(c, lab, "Black", 40, SILVER, x, base + 50, alpha=b, maxw=380)
        text(c, "+4 CM ?!", "Black", 110, YEL, W / 2, 620, alpha=ease_out((p - 4.0) / 0.4),
             scale=0.8 + 0.2 * ease_back(min(1, max(0, p - 4.0) / 0.3)))
    elif k == "4":
        s = 64; x0, y0 = W / 2 - 4 * s, cy - 330
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        for i in range(8):
            for j in range(8):
                col = (235, 220, 190) if (i + j) % 2 == 0 else (120, 82, 50)
                dd.rectangle([x0 + i * s, y0 + j * s, x0 + (i + 1) * s, y0 + (j + 1) * s], fill=col + (int(255 * a),))
        c.alpha_composite(lay)
        k_ = emoji("♟️", 130) or text_img("♟", "Black", 130, WHITE)
        blit(c, k_, W / 2, y0 + 4 * s, alpha=a, scale=0.9 + 0.1 * math.sin(p * 3))
        r = ease_out((p - 4.5) / 0.5)
        text(c, "2 DÉFAITES (CONTRE DES PROS)", "Black", 50, SILVER, W / 2, cy + 250, alpha=r, maxw=960)
        text(c, "1 VICTOIRE CONTRE SON FRÈRE", "Black", 58, YEL, W / 2, cy + 340, alpha=ease_out((p - 6.0) / 0.5), maxw=960)
    elif k == "3":
        text(c, "10 JOURS", "Black", 190, WHITE, W / 2, cy - 160, alpha=a, scale=0.85 + 0.15 * ease_back(min(1, p / 0.4)))
        text(c, "CHEZ LES MOINES SHAOLIN", "Black", 60, ACCENT, W / 2, cy - 30, alpha=a, maxw=960)
        for i, (lab, tt) in enumerate([("CRÂNE RASÉ", 2.0), ("KUNG-FU TOUS LES JOURS", 2.8), ("RÉVEIL À 4H30", 4.0)]):
            b = ease_out((p - tt) / 0.35)
            panel(c, [170, cy + 70 + i * 120, 910, cy + 170 + i * 120], (255, 255, 255, 24), b, r=26)
            text(c, lab, "Black", 52, YEL if i == 2 else WHITE, W / 2, cy + 120 + i * 120, alpha=b, maxw=700)
    elif k == "2":
        L = 840; x0 = W / 2 - L / 2
        bed = emoji("🛏️", 200)
        if bed is not None:
            blit(c, bed, W / 2, cy - 340, alpha=a, scale=0.9 + 0.1 * ease_back(min(1, p / 0.4)))
        b = ease_out((p - 0.6) / 0.6)
        lb = L * 1.90 / 2.24
        bar(c, x0, cy + 90, L, b * 1.90 / 2.24, 70, (150, 100, 60), b, "LE LIT", "1,90 m")
        g = ease_out((p - 2.2) / 0.8)
        bar(c, x0, cy + 230, L, g, 70, ACCENT, g, "WEMBY", "2,24 m")
        o = ease_out((p - 3.2) / 0.4)
        if o > 0:
            panel(c, [x0 + lb, cy + 195, x0 + L, cy + 265], RED + (255,), o, r=35)
            text(c, "34 CM DE TROP", "Black", 46, RED, x0 + (lb + L) / 2, cy + 330, alpha=o)
        sh = min(1, p / 0.3) * (1 - ease_out((p - 3.3) / 0.3))
        text(c, "10 JOURS CHEZ LES MOINES SHAOLIN", "Black", 50, ACCENT, W / 2, cy - 140, alpha=sh, maxw=960)
        text(c, "ÇA DÉPASSE !", "Black", 110, YEL, W / 2, cy - 140, alpha=ease_out((p - 3.6) / 0.3),
             scale=0.8 + 0.2 * ease_back(min(1, max(0, p - 3.6) / 0.3)))
    elif k == "1":
        b1 = ease_out((p - 0.4) / 0.4)
        panel(c, [140, cy - 330, 940, cy - 170], (34, 120, 60, 255), b1, r=30)
        text(c, "MENU VÉGAN AU TEMPLE", "Black", 58, WHITE, W / 2, cy - 250, alpha=b1, maxw=740)
        van = emoji("🚐", 260)
        b2 = ease_out((p - 3.5) / 0.6)
        if van is not None:
            blit(c, van, W / 2 + (1 - b2) * 700, cy + 10, alpha=b2)
        b3 = ease_out((p - 6.0) / 0.4)
        panel(c, [90, cy + 200, 990, cy + 360], (255, 214, 10, 255), b3, r=30)
        text(c, "REPAS PROTÉINÉ HORS DES MURS", "Black", 56, (20, 20, 20), W / 2, cy + 280, alpha=b3, maxw=860)
        steak = emoji("🍗", 120)
        if steak is not None and b3 > 0:
            blit(c, steak, 960, cy + 180, alpha=b3, rot=12 * math.sin(p * 4))


def frame(t, T, parts, groups, SIL, intro_sil):
    c = bg_at(t, parts)
    k, p, d = T.at(t)
    # ------- accroche
    if k == "H":
        if PH is not None:
            blit(c, PH["big"], W / 2, 1180, scale=1.0 + 0.05 * p)
        elif intro_sil is not None:
            blit(c, intro_sil, W / 2, 1050, alpha=1, scale=1.0 + 0.04 * p)
        z = 0.82 + 0.18 * ease_back(min(1, (t + 0.05) / 0.35))
        t0, t1 = outlined(TITLE[0], "Black", 150, WHITE, 12), outlined(TITLE[1], "Black", 150, YEL, 12)
        blit(c, t0, W / 2, 470, scale=z * min(1, 1000 / t0.width))
        blit(c, t1, W / 2, 650, scale=z * min(1, 1000 / t1.width))
    elif k == "E":
        if PH is not None:
            blit(c, PH["mid"], W / 2, 1270, alpha=min(1, p / 0.4))
        text(c, "LEQUEL T'A LE PLUS", "Black", 92, WHITE, W / 2, 620, alpha=min(1, p / 0.3))
        text(c, "SURPRIS ?", "Black", 150, YEL, W / 2, 760, alpha=min(1, p / 0.3), scale=0.85 + 0.15 * ease_back(min(1, p / 0.4)))
        b = ease_out((p - 2.2) / 0.5)
        panel(c, [140, 860, 940, 1060], (20, 20, 28, 235), b, r=34)
        text(c, "PROCHAIN ÉPISODE :", "Black", 50, SILVER, W / 2, 920, alpha=b)
        text(c, "TU CHOISIS LE JOUEUR", "Black", 62, ACCENT, W / 2, 995, alpha=b, maxw=760)
    else:
        n = NUM[k]
        # en-tête de série + barre de progression
        if PH is not None:
            blit(c, PH["avatar"], 150, 180)
        text(c, HEADER, "Black", 44, SILVER, W / 2 + 40, 175, alpha=1, maxw=700)
        prog = (N - n + min(1, p / d)) / N
        panel(c, [140, 225, 940, 239], (255, 255, 255, 30), 1, r=7)
        panel(c, [140, 225, 140 + 800 * prog, 239], ACCENT + (255,), 1, r=7)
        # numéro
        pop = ease_back(min(1, p / 0.3))
        col = YEL if n == 1 else ACCENT
        disc = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); dd = ImageDraw.Draw(disc)
        dd.ellipse([10, 10, 290, 290], fill=col + (255,))
        disc.alpha_composite(text_img(f"{n}", "Black", 170, (12, 12, 16)), (150 - text_img(f"{n}", "Black", 170, (12, 12, 16)).width // 2, 150 - text_img(f"{n}", "Black", 170, (12, 12, 16)).height // 2 - 8))
        blit(c, disc, W / 2, 430, scale=0.62 * (0.5 + 0.5 * pop), rot=(1 - pop) * 25)
        visual(c, k, p, d, SIL)
    captions(c, t, groups)
    return c.convert("RGB")


# ---------------------------------------------------------------- son
def _sine(f, d, decay=8):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-decay * t)


def whoosh(d=0.45):
    n = int(d * SR); x = np.random.default_rng(1).normal(0, 1, n)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    y = np.convolve(x, np.ones(30) / 30, mode="same") * env
    return y / (np.abs(y).max() + 1e-9)


def pop():
    return _sine(880, 0.18, 22) * 0.8 + _sine(1320, 0.18, 30) * 0.4


def ding():
    return _sine(1046, 0.9, 4) + 0.5 * _sine(1568, 0.9, 5)


def mix(voice_wav, T, out_wav):
    with wave.open(voice_wav) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, w.getnchannels()).mean(1) / 32768
    n = int(T.total * SR); out = np.zeros(n, np.float32); out[:len(v)] += v[:n] * 1.0

    def add(x, t, g):
        i = int(t * SR); x = x[: max(0, n - i)]; out[i:i + len(x)] += x * g

    for k, (a, b) in T.span.items():
        if k not in ("H",):
            add(whoosh(), max(0, a - 0.1), 0.10)
        if k.isdigit():
            add(pop(), a + 0.05, 0.12)
    add(ding(), T.span[next(k for k, v in NUM.items() if v == 1)][0] + 0.05, 0.10)
    out = np.clip(out, -1, 1)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- miniature
# couleurs d'équipe (fond de la miniature) — clé = nom du fichier photo
TEAM = {"wemby": (0, 0, 0), "lebron": (0, 107, 182), "curry": (29, 66, 138), "doncic": (85, 37, 130),
        "giannis": (0, 71, 27), "sga": (0, 125, 195), "edwards": (12, 35, 64), "jokic": (13, 34, 64),
        "durant": (206, 17, 65), "flagg": (0, 83, 188), "kyrie": (0, 83, 188)}


def _rays(size, center, color, n=18, alpha=70):
    im = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, cy = center; R = 2600
    for i in range(n):
        a0 = 2 * math.pi * i / n; a1 = a0 + math.pi / n * 0.55
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))],
                  fill=color + (alpha,))
    return im.filter(ImageFilter.GaussianBlur(6))


def _outline_sticker(ph, px=12, col=(255, 255, 255)):
    """Contour blanc façon autocollant + ombre portée."""
    pad = px * 4
    a = ph.getchannel("A").point(lambda v: 255 if v > 60 else 0)
    A = Image.new("L", (ph.width + 2 * pad, ph.height + 2 * pad), 0); A.paste(a, (pad, pad))
    st = A.filter(ImageFilter.MaxFilter(2 * (px // 2) + 1)).filter(ImageFilter.MaxFilter(2 * (px // 2) + 1)).filter(ImageFilter.GaussianBlur(1.2))
    out = Image.new("RGBA", A.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", A.size, (0, 0, 0, 255)); sh.putalpha(st.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.8)))
    out.alpha_composite(sh, (14, 22))
    wl = Image.new("RGBA", A.size, col + (255,)); wl.putalpha(st); out.alpha_composite(wl)
    out.alpha_composite(ph, (pad, pad))
    return out


def cover(SIL, out):
    key = os.path.splitext(os.path.basename(PHOTO))[0]
    tc = tuple(EP.get("json", {}).get("color") or TEAM.get(key) or (40, 50, 70))
    # fond : dégradé radial couleur d'équipe -> presque noir
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - 1250) / H * 1.1) ** 2)
    k = np.clip(1 - d * 1.5, 0, 1)[..., None]
    base = np.array([10, 10, 16], float); hi = np.array(tc, float) * 0.85 + np.array([255, 255, 255]) * 0.15
    if max(tc) < 30: hi = np.array([255, 150, 40], float) * 0.75
    c = Image.fromarray((base + (hi - base) * k ** 1.3).astype(np.uint8), "RGB").convert("RGBA")
    c.alpha_composite(_rays((W, H), (W // 2, 1150), (255, 255, 255), alpha=34))
    # joueur
    if PH is not None:
        ph = PH["raw"]; full = ph.height / ph.width > 1.25
        P = _fit(ph, 1180, 1500 if full else 1150)
        S = _outline_sticker(P)
        blit(c, S, W / 2, max(H - S.height / 2 + (140 if full else 60), 900 + S.height / 2))
    elif SIL is not None:
        big = SIL.resize((int(SIL.width * 1.6), int(SIL.height * 1.6)), Image.LANCZOS)
        blit(c, big, W / 2, 1250)
    # vignette haut pour la lisibilité du titre
    g = Image.new("L", (1, H)); [g.putpixel((0, y), int(230 * max(0, 1 - y / 720))) for y in range(H)]
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 255)); shade.putalpha(g.resize((W, H))); c.alpha_composite(shade)
    l1, l2, l3 = EP["cover"]
    # badge rond « 5 » + ligne 1/2
    bd = Image.new("RGBA", (250, 250), (0, 0, 0, 0)); dd = ImageDraw.Draw(bd)
    dd.ellipse([8, 8, 242, 242], fill=(0, 0, 0, 255)); dd.ellipse([18, 18, 232, 232], fill=RED + (255,))
    n5 = outlined(str(N), "Black", 190, WHITE, 0); blit(bd, n5, 125, 128)
    head = " ".join([l1, l2]).replace(str(N) + " ", "", 1) if l1.startswith(str(N)) else " ".join([l1, l2])
    words = head.split(); half = (len(words) + 1) // 2
    hl = [" ".join(words[:half]), " ".join(words[half:])]
    blit(c, bd, 180, 300, rot=-8)
    for i, t in enumerate(hl):
        im = outlined(t, "Black", 118, WHITE, 12)
        blit(c, im, 330 + min(im.width, 720) / 2, 235 + i * 135, scale=min(1, 720 / im.width))
    name = outlined(l3, "Black", 300, YEL, 18)
    blit(c, name, W / 2, 560, scale=min(1, 1030 / name.width), rot=-4)
    # bandeau d'accroche
    tag = EP.get("json", {}).get("cover_tag") or "LE N°1 VA TE CHOQUER"
    ti = outlined(tag, "Black", 64, WHITE, 0)
    rib = Image.new("RGBA", (ti.width + 70, ti.height + 40), RED + (255,)); rib.alpha_composite(ti, (35, 20))
    sh = Image.new("RGBA", (rib.width + 12, rib.height + 12), (0, 0, 0, 0)); sh.paste((0, 0, 0, 255), (12, 12, rib.width + 12, rib.height + 12)); sh.alpha_composite(rib)
    blit(c, sh, W / 2, 760, rot=3, scale=min(1, 900 / sh.width))
    e = emoji("🤯", 140)
    if e is not None:
        blit(c, e, 985, 730, rot=12)
    c.convert("RGB").save(out, quality=92)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="out_top10"); ap.add_argument("--episode", default="a")
    ap.add_argument("--queue-at", help="'AAAA-MM-JJ HH:MM' : programme la publication (Instagram, YouTube, brouillon TikTok) + aperçu Discord")
    a = ap.parse_args(); use(a.episode)
    os.makedirs(a.out, exist_ok=True)
    global PH
    PH = load_photo()
    from quiz.main import silhouette
    pid = EP.get("nba_id") or "wembavi01"
    SIL = silhouette({"id": pid}, 420, qmark=False)
    intro = silhouette({"id": pid}, 900, qmark=False)
    vw = os.path.join(a.out, "voix.wav")
    cues, total = tts.synth(SEGS, vw)
    T = TL(cues, total)
    groups = chunks(words_from_last())
    if not groups:  # mode test sans voix : sous-titres approximatifs
        ws = []
        for k, s, e in cues:
            txt = re.sub(r"\[[^\]]*\]", "", dict(SEGS)[k]).split()
            for i, w_ in enumerate(txt):
                ws.append((w_, s + (e - s) * i / len(txt), s + (e - s) * (i + 1) / len(txt)))
        groups = chunks(ws)
    parts = build_bg((40, 50, 70))
    silent = os.path.join(a.out, "video.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-maxrate", "4M", "-bufsize", "8M", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i in range(int(T.total * FPS)):
        p.stdin.write(frame(i / FPS, T, parts, groups, SIL, intro).tobytes())
    p.stdin.close(); p.wait()
    aud = os.path.join(a.out, "audio.wav"); mix(vw, T, aud)
    final = os.path.join(a.out, EP["file"] + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", aud, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-shortest", final], check=True)
    cover(SIL, os.path.join(a.out, EP["file"] + ".jpg"))
    print("Vidéo :", final, f"{T.total:.1f}s")
    if a.queue_at:
        schedule(final, os.path.join(a.out, EP["file"] + ".jpg"), a.queue_at)


def schedule(video, cover_path, at):
    """Met l'épisode dans la file de publication et l'envoie sur Discord (❌ sur le message = annulation)."""
    from publish import queue
    from chiffre import discord_post
    J = EP.get("json", {})
    tags = " ".join(J.get("hashtags", ["#NBA", "#basketball", "#NBAFrance", "#basket", "#lesaviezvous"]))
    base = J.get("caption", " ".join(TITLE).title())
    yt_title = J.get("yt_title", " ".join(TITLE).capitalize())
    msg = (f"**🎬 Nouvel épisode « {' '.join(TITLE).lower()} »** — publication automatique le {at} "
           f"(Instagram + YouTube ; brouillon TikTok quelques heures avant).\n"
           f"Mets ❌ sur ce message pour l'annuler. Sources des faits : {', '.join(J.get('sources', [])) or '—'}")
    mid = None
    if os.environ.get("DISCORD_BOT_TOKEN"):
        try:
            mid = discord_post.post(video, msg[:1900], cover_path)
        except Exception as ex:  # vidéo trop lourde pour Discord (limite ~10 Mo) : aperçu allégé en 720p
            print("Aperçu Discord pleine qualité impossible :", ex)
            light = os.path.splitext(video)[0] + "_apercu.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", "scale=720:-2", "-c:v", "libx264", "-preset", "veryfast",
                            "-b:v", "1400k", "-maxrate", "1600k", "-bufsize", "3200k", "-c:a", "aac", "-b:a", "96k", light], check=True)
            try:
                mid = discord_post.post(light, (msg + "\n(Aperçu allégé ; la publication se fait en pleine qualité.)")[:1900], cover_path)
            except Exception as ex2:
                print("Aperçu Discord impossible :", ex2)
                discord_post.notify(msg[:1800] + "\n(Vidéo trop lourde pour l'aperçu Discord.)")
            finally:
                if os.path.exists(light): os.remove(light)
    key = "top5_" + EP["file"]
    queue.add(key, video, cover_path, f"{base}\n\nAbonne-toi pour la suite 🔔\n\n{tags}", f"{yt_title} #Shorts",
              f"{base}\n\n#Shorts {tags}", at, mid, f"{base}\n\n{tags}")
    print("Programmé :", key, at)


if __name__ == "__main__":
    main()
