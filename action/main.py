"""Prototype « L'ACTION QUI A TOUT CHANGÉ » — une action mythique racontée comme un thriller,
reconstituée sur un terrain 3D stylisé (pions aux couleurs des équipes, caméra qui bouge), voix off,
gros titre en deux lignes et sous-titres mot à mot. Aucune image de match.

Épisode 1 : le tir de Ray Allen, finale NBA 2013, match 6 (faits : NBA.com, Andscape, SI, theScore, Yahoo Sports).
usage : python -m action.main [--out docs/proto] [--frames 0,5,10 pour des images de test]"""
import argparse, math, os, re, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from chiffre import tts
from chiffre.render import W, H, FPS, WHITE, font, text_img, blit, ease_out, ease_back
from top10.main import outlined, chunks, words_from_last, captions, whoosh, _sine, SR

YEL = (255, 214, 10)
RED = (235, 52, 64)
GREEN = (60, 220, 120)
HEAT = (152, 0, 46)
SPURS = (190, 198, 206)
WOOD = (219, 176, 122)

# ---------------------------------------------------------------- script (cue, petite ligne, grande ligne, couleur, voix)
SCENES = [
    ("H", "FINALE NBA · IL RESTE", "28 SECONDES", YEL,
     "[excited] Il reste vingt-huit secondes en finale NBA. La fête est prête… mais l'histoire va basculer."),
    ("CTX", "JUIN 2013 · MATCH 6", "SAN ANTONIO +5", SPURS,
     "Juin 2013, match six. San Antonio mène de cinq points. Encore une victoire… et les Spurs sont champions."),
    ("ROPE", "LA FÊTE SE PRÉPARE", "CORDES JAUNES", YEL,
     "Autour du terrain, la sécurité déroule déjà les cordes jaunes. Des milliers de fans de Miami ont quitté la salle."),
    ("BACK", "MIAMI REVIENT…", "IL FAUT 3 POINTS", RED,
     "LeBron marque à trois points. Moins deux. Puis Leonard ne met qu'un lancer franc sur deux. Miami doit marquer à trois points."),
    ("MISS", "DERNIÈRE CHANCE", "RATÉ !", RED,
     "Dernière chance. LeBron tire à trois points… [surprised] raté !"),
    ("REB", "CHRIS BOSH", "ARRACHE LE REBOND", WHITE,
     "Mais Chris Bosh arrache le rebond, au milieu des joueurs de San Antonio."),
    ("LOOK", "ET LÀ…", "REGARDE RAY ALLEN", YEL,
     "Et là… regarde bien Ray Allen."),
    ("CORNER", "IL RECULE", "DANS LE COIN", YEL,
     "Il recule vers le coin, se place derrière la ligne à trois points… et reçoit le ballon."),
    ("SHOT", "IL TIRE · IL RESTE", "5,2 SECONDES", WHITE,
     "Il tire… à cinq secondes de la fin."),
    ("IN", "DEDANS !", "95 – 95", GREEN,
     "[excited] Dedans ! Quatre-vingt-quinze partout !"),
    ("WHY", "PAS UN HASARD", "DES ANNÉES DE TRAVAIL", YEL,
     "Ce recul vers le coin ? Il le travaillait à l'entraînement depuis des années."),
    ("WIN", "PROLONGATION, PUIS MATCH 7", "MIAMI CHAMPION", RED,
     "Miami gagne en prolongation… puis le match sept. Le Heat est champion !"),
    ("E", "LE PLUS GRAND TIR DES FINALES ?", "OUI OU NON ?", YEL,
     "[excited] Le plus grand tir de l'histoire des finales : oui ou non ? Dis-le en commentaire !"),
]
SEGS = [(c, v) for c, _, _, _, v in SCENES]
ORDER = [c for c, *_ in SCENES]
INFO = {c: (a, b, col) for c, a, b, col, _ in SCENES}
FILE = "action_ray_allen_2013"

# score / horloge affichés par scène (horloge seulement quand elle est vérifiée)
SCORE = {"H": (89, 94, "0:28.2"), "CTX": (89, 94, "0:28.2"), "ROPE": (89, 94, None), "BACK": (92, 95, None),
         "MISS": (92, 95, None), "REB": (92, 95, None), "LOOK": (92, 95, None), "CORNER": (92, 95, None),
         "SHOT": (92, 95, "0:05.2"), "IN": (95, 95, None), "WHY": (95, 95, None), "WIN": (103, 100, "FINAL · PROL."),
         "E": (95, 95, None)}

# ---------------------------------------------------------------- caméra (pieds ; x à droite, y vers la caméra, z en haut ; panier en (0, 5.25))
UP = np.array([0.0, 0.0, 1.0])


class Cam:
    def __init__(self, pos, tgt, f):
        self.pos, self.tgt, self.f = np.array(pos, float), np.array(tgt, float), float(f)
        fw = self.tgt - self.pos; fw /= np.linalg.norm(fw)
        r = np.cross(UP, fw)
        if np.linalg.norm(r) < 1e-6: r = np.array([1.0, 0, 0])
        r /= np.linalg.norm(r); u = np.cross(fw, r)
        self.R = np.stack([r, -u, fw])                      # repère caméra (x droite, y bas, z avant)
        K = np.array([[self.f, 0, W / 2], [0, self.f, H / 2], [0, 0, 1]])
        self.M = K @ np.hstack([self.R, (-self.R @ self.pos)[:, None]])

    def proj(self, p):
        q = self.M @ np.append(np.asarray(p, float), 1.0)
        if q[2] <= 0.5: return None
        return q[0] / q[2], q[1] / q[2], q[2]


def lerp(a, b, k): return a + (b - a) * k


def cam_mix(a, b, k):
    return lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)


def C(pos, tgt, f): return (np.array(pos, float), np.array(tgt, float), float(f))


WIDE = C((0, 78, 44), (0, 16, 0), 1550)
CAMS = {   # (début de scène, fin de scène)
    "H": (C((-30, 70, 60), (0, 14, 0), 1300), C((-10, 62, 40), (0, 14, 2), 1500)),
    "CTX": (C((0, 70, 46), (0, 15, 0), 1500), C((8, 64, 40), (0, 13, 0), 1550)),
    "ROPE": (C((28, 66, 70), (0, 18, 0), 1100), C((-24, 66, 66), (0, 18, 0), 1100)),
    "BACK": (C((0, 64, 40), (0, 15, 0), 1500), C((-6, 58, 34), (-2, 14, 2), 1550)),
    "MISS": (C((-14, 52, 30), (-2, 12, 4), 1500), C((-6, 40, 26), (0, 8, 5), 1500)),
    "REB": (C((10, 30, 16), (1, 7, 6), 1400), C((14, 26, 14), (2, 7, 6), 1450)),
    "LOOK": (C((24, 36, 22), (12, 12, 4), 1500), C((26, 30, 18), (13, 11, 4), 1700)),
    "CORNER": (C((22, 40, 30), (14, 8, 3), 1300), C((32, 30, 20), (18, 6, 4), 1400)),
    "SHOT": (C((12, 38, 15), (11.5, 5, 8), 980), C((11, 35, 14), (11.5, 5, 8.5), 1020)),
    "IN": (C((14, 18, 11), (0, 5.5, 9.5), 1700), C((10, 20, 13), (0, 6, 9), 1500)),
    "WHY": (C((12, 13, 62), (12, 7, 0), 2100), C((12, 12, 58), (12, 7, 0), 2100)),
    "WIN": (C((0, 60, 26), (0, 26, 4), 1300), C((12, 56, 30), (0, 26, 4), 1300)),
    "E": (C((-20, 70, 46), (0, 16, 0), 1350), C((20, 70, 46), (0, 16, 0), 1350)),
}

# ---------------------------------------------------------------- joueurs (pions)
# nom : (équipe, numéro, étiquette)
PL = {"lebron": ("H", "6", "LEBRON"), "allen": ("H", "34", "RAY ALLEN"), "bosh": ("H", "1", "BOSH"),
      "h4": ("H", "", None), "h5": ("H", "", None),
      "s1": ("S", "", None), "s2": ("S", "", None), "s3": ("S", "", None), "s4": ("S", "", None), "s5": ("S", "", None)}
INIT = {"lebron": (-6, 27), "allen": (16, 21), "bosh": (-4, 13), "h4": (-21, 8), "h5": (7, 15),
        "s1": (-5, 24.5), "s2": (14, 18.5), "s3": (-2.5, 9.5), "s4": (-18, 8.5), "s5": (4, 11.5)}
# déplacements par scène : nom -> ((x, y), p0, p1) en fraction de la scène
MOVES = {
    "BACK": {"lebron": ((-9, 25), 0.0, 0.3), "s1": ((-8, 23), 0.0, 0.3)},
    "MISS": {"bosh": ((-1, 10), 0.4, 1.0), "s3": ((0.5, 8), 0.4, 1.0), "s5": ((3, 9), 0.4, 1.0),
             "allen": ((12, 14), 0.2, 1.0), "s2": ((10, 13), 0.2, 1.0)},
    "REB": {"bosh": ((1.5, 8.5), 0.0, 0.3)},
    "CORNER": {"allen": ((23, 4.5), 0.0, 0.62), "s2": ((15, 9), 0.0, 0.8)},
    "SHOT": {"s2": ((20.5, 5.5), 0.0, 0.5)},
    "WIN": {"lebron": ((-4, 30), 0, 0.5), "allen": ((3, 29), 0, 0.5), "bosh": ((0, 33), 0, 0.5),
            "h4": ((-8, 33), 0, 0.5), "h5": ((7, 33), 0, 0.5),
            "s1": ((-22, 12), 0, 0.6), "s2": ((22, 12), 0, 0.6), "s3": ((-16, 4), 0, 0.6), "s4": ((-24, 20), 0, 0.6), "s5": ((18, 4), 0, 0.6)},
}
JUMPS = {"REB": {"bosh": (0.12, 0.42, 3.2), "s3": (0.1, 0.38, 2.4), "s5": (0.14, 0.4, 2.2)},
         "SHOT": {"allen": (0.05, 0.3, 2.0)}, "BACK": {"lebron": (0.08, 0.2, 1.6)}, "MISS": {"lebron": (0.3, 0.45, 1.8)}}
RIM = np.array([0.0, 5.25, 10.0])


def player_state(T, t):
    k, a, b = T.at(t)
    pos = {n: np.array(v, float) for n, v in INIT.items()}
    for c in ORDER:
        if c == k: break
        for n, (tg, _, _) in MOVES.get(c, {}).items(): pos[n] = np.array(tg, float)
    p = (t - a) / max(b - a, 1e-3)
    z = {n: 0.0 for n in pos}
    for n, (tg, p0, p1) in MOVES.get(k, {}).items():
        e = ease_out(min(1, max(0, (p - p0) / max(p1 - p0, 1e-3)))) if p1 > p0 else 1
        pos[n] = lerp(pos[n], np.array(tg, float), e)
    for n, (p0, p1, hgt) in JUMPS.get(k, {}).items():
        if p0 <= p <= p1: z[n] = hgt * math.sin(math.pi * (p - p0) / (p1 - p0))
    if k == "WIN":
        for n in ("lebron", "allen", "bosh", "h4", "h5"):
            ph = {"lebron": 0, "allen": 0.5, "bosh": 1.1, "h4": 1.7, "h5": 2.3}[n]
            if p > 0.45: z[n] = 2.2 * abs(math.sin((t - a) * 5 + ph))
    return pos, z, k, p, t - a


def arc(p0, p1, apex, u):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    q = lerp(p0, p1, u); q[2] += apex * 4 * u * (1 - u); return q


def hand(pos, z, n, h=7.6):
    x, y = pos[n]; return np.array([x, y, z[n] + h])


def ball_state(pos, z, k, p):
    if k in ("H", "CTX", "ROPE"):
        x, y = pos["lebron"]; return np.array([x + 0.9, y - 0.4, 1.2 + abs(math.sin(p * 18)) * 1.6])
    if k == "BACK":
        if p < 0.08: return hand(pos, z, "lebron")
        if p < 0.3: return arc(hand(pos, z, "lebron"), RIM + [0, 0, 0.3], 9, (p - 0.08) / 0.22)
        if p < 0.4: return lerp(RIM + [0, 0, 0.3], np.array([0, 5.25, 1]), (p - 0.3) / 0.1)
        x, y = pos["lebron"]; return np.array([x + 0.9, y - 0.4, 1.2 + abs(math.sin(p * 18)) * 1.6])
    if k == "MISS":
        if p < 0.3:
            x, y = pos["lebron"]; return np.array([x + 0.9, y - 0.4, 1.2 + abs(math.sin(p * 20)) * 1.6])
        if p < 0.72: return arc(hand(pos, z, "lebron"), RIM + [-0.6, 0, 0.4], 9, (p - 0.3) / 0.42)
        return arc(RIM + [-0.6, 0, 0.4], np.array([1.5, 8.5, 9.0]), 2.2, (p - 0.72) / 0.28)
    if k == "REB":
        if p < 0.27: return arc(np.array([1.5, 8.5, 9.0]), hand(pos, z, "bosh", 8.4), 1.0, p / 0.27)
        return hand(pos, z, "bosh", 8.4 if p < 0.42 else 6.0)
    if k == "LOOK":
        return hand(pos, z, "bosh", 6.0)
    if k == "CORNER":
        if p < 0.5: return hand(pos, z, "bosh", 6.0)
        if p < 0.8: return arc(hand(pos, z, "bosh", 6.0), hand(pos, z, "allen", 4.5), 2.5, (p - 0.5) / 0.3)
        return hand(pos, z, "allen", 4.5)
    if k == "SHOT":
        if p < 0.12: return hand(pos, z, "allen", 7.8)
        return arc(np.array([23, 4.5, 9.0]), RIM + [0, 0, 0.6], 5.5, min(1, (p - 0.12) / 0.88))
    if k == "IN":
        u = min(1, p / 0.35); return lerp(RIM + [0, 0, 0.6], np.array([0, 5.25, 2]), u) if p < 0.5 else np.array([0.8, 6.5, 0.8])
    if k == "WIN":
        x, y = pos["lebron"]; return np.array([x, y, z["lebron"] + 9])
    return None


# ---------------------------------------------------------------- textures (sol, tribunes)
S = 14  # pixels par pied pour le sol


def _floor_tex():
    x0, x1, y0, y1 = -34, 34, -8, 62
    im = Image.new("RGBA", ((x1 - x0) * S, (y1 - y0) * S), (26, 26, 32, 255)); d = ImageDraw.Draw(im)
    P = lambda x, y: ((x - x0) * S, (y - y0) * S)
    # parquet
    d.rectangle([*P(-25, 0), *P(25, 62)], fill=WOOD + (255,))
    rng = np.random.default_rng(4)
    for i, x in enumerate(np.arange(-25, 25, 0.75)):
        c = tuple(int(v * (0.92 + 0.08 * rng.random())) for v in WOOD)
        d.rectangle([*P(x, 0), *P(x + 0.74, 62)], fill=c + (255,))
    lw = 3; L = (255, 255, 255, 255)
    # raquette
    d.rectangle([*P(-8, 0), *P(8, 19)], fill=HEAT + (255,), outline=L, width=lw)
    d.ellipse([*P(-6, 13), *P(6, 25)], outline=L, width=lw)
    d.arc([*P(-4, 1.25), *P(4, 9.25)], 0, 180, fill=L, width=lw)
    # ligne à 3 points
    d.line([P(-22, 0), P(-22, 14.2)], fill=L, width=lw); d.line([P(22, 0), P(22, 14.2)], fill=L, width=lw)
    ang = math.degrees(math.asin((14.2 - 5.25) / 23.75))
    d.arc([*P(-23.75, 5.25 - 23.75), *P(23.75, 5.25 + 23.75)], ang, 180 - ang, fill=L, width=lw)
    # limites, milieu de terrain
    d.rectangle([*P(-25, 0), *P(25, 62)], outline=L, width=lw)
    d.line([P(-25, 47), P(25, 47)], fill=L, width=lw)
    d.ellipse([*P(-6, 41), *P(6, 53)], outline=L, width=lw)
    # inscription au sol (bord de terrain)
    t = text_img("FINALE NBA 2013", "Black", 64, (255, 255, 255)).rotate(90, expand=True)
    im.alpha_composite(t, (int(P(-29.5, 0)[0]), int(P(0, 12)[1])))
    im.alpha_composite(t.rotate(180), (int(P(26.6, 0)[0]), int(P(0, 12)[1])))
    return im


def _crowd_tex(wft, hft, s, seed, frac=1.0):
    w, h = int(wft * s), int(hft * s)
    im = Image.new("RGBA", (w, h), (14, 14, 20, 255)); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    pal = [(235, 235, 235), (230, 230, 230), (152, 0, 46), (200, 30, 60), (30, 30, 34), (250, 200, 60), (90, 120, 200)]
    row = 2.4 * s; band = 3.2 * s
    y = 0.0
    while y < h - band:
        x = rng.random() * 0.8 * s
        while x < w:
            if rng.random() < frac:
                c = pal[rng.integers(len(pal))]; r = s * (0.55 + 0.15 * rng.random())
                d.ellipse([x - r, y + 0.3 * s, x + r, y + 0.3 * s + 2.2 * r], fill=c + (255,))
                d.ellipse([x - r * 0.6, y - 0.6 * s, x + r * 0.6, y + 0.4 * s], fill=(70, 50, 40, 255))
            x += 1.5 * s * (0.85 + 0.3 * rng.random())
        y += row
    im = im.filter(ImageFilter.GaussianBlur(s * 0.18))
    d = ImageDraw.Draw(im)
    d.rectangle([0, h - band, w, h], fill=(10, 10, 14, 255))
    d.rectangle([0, h - band, w, h - band + s * 0.3], fill=HEAT + (255,))
    msg = text_img("FINALE NBA 2013  ·  L'ACTION QUI A TOUT CHANGÉ  ·  ", "Black", int(s * 1.5), (255, 255, 255))
    x = 0
    while x < w:
        im.alpha_composite(msg, (x, int(h - band / 2 - msg.height / 2 + s * 0.15))); x += msg.width
    return im


class Plane:
    """Surface plane texturée : monde = O + U*px + V*py."""
    def __init__(self, tex, O, U, V):
        self.tex, self.O, self.U, self.V = tex, np.array(O, float), np.array(U, float), np.array(V, float)

    def draw(self, canvas, cam, scale=1.0):
        Hm = cam.M @ np.array([[*self.U, 0], [*self.V, 0], [*self.O, 1]]).T   # 3x3 : (px,py,1) -> écran homogène
        Sm = np.diag([scale, scale, 1.0]); Hm = Sm @ Hm
        try: Hi = np.linalg.inv(Hm)
        except np.linalg.LinAlgError: return
        Hi = Hi / Hi[2, 2] if abs(Hi[2, 2]) > 1e-12 else Hi
        cw, ch = canvas.size
        out = self.tex.transform((cw, ch), Image.PERSPECTIVE, tuple(Hi.flatten()[:8]), Image.BILINEAR, fillcolor=(0, 0, 0, 0))
        # demi-plan valide (devant la caméra) : signe de la 3e ligne de Hi
        c = self.O + self.U * self.tex.width / 2 + self.V * self.tex.height / 2
        pr = cam.proj(c)
        g = Hi[2]
        if pr is not None:
            ref = np.sign(g[0] * pr[0] * scale + g[1] * pr[1] * scale + g[2])
        else:
            ref = np.sign(g[2]) or 1
        poly = _clip([(0, 0), (cw, 0), (cw, ch), (0, ch)], lambda q: ref * (g[0] * q[0] + g[1] * q[1] + g[2]) - 1e-9)
        if len(poly) < 3: return
        m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
        a = Image.fromarray(np.minimum(np.asarray(out.getchannel("A")), np.asarray(m)))
        out.putalpha(a)
        canvas.alpha_composite(out)


def _clip(poly, f):
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]; fa, fb = f(a), f(b)
        if fa >= 0: out.append(a)
        if (fa >= 0) != (fb >= 0):
            k = fa / (fa - fb); out.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
    return out


# ---------------------------------------------------------------- dessin des objets 3D
def _poly3(d, cam, pts, **kw):
    q = [cam.proj(p) for p in pts]
    if any(v is None for v in q): return
    d.polygon([(v[0], v[1]) for v in q], **kw)


def draw_hoop(c, cam, net_swish=0.0):
    d = ImageDraw.Draw(c)
    # poteau + bras
    _poly3(d, cam, [(-0.4, -4, 0), (0.4, -4, 0), (0.4, -4, 12), (-0.4, -4, 12)], fill=(40, 40, 48, 255))
    _poly3(d, cam, [(-0.3, -4, 11.4), (0.3, -4, 11.4), (0.3, 4, 11.4), (-0.3, 4, 11.4)], fill=(60, 60, 70, 255))
    # planche
    _poly3(d, cam, [(-3, 4, 9.5), (3, 4, 9.5), (3, 4, 13), (-3, 4, 13)], fill=(255, 255, 255, 70), outline=(255, 255, 255, 255))
    _poly3(d, cam, [(-1, 4.02, 10), (1, 4.02, 10), (1, 4.02, 11.5), (-1, 4.02, 11.5)], outline=(255, 255, 255, 255))
    # filet
    ring = [(RIM[0] + 0.75 * math.cos(a), RIM[1] + 0.75 * math.sin(a), 10) for a in np.linspace(0, 2 * math.pi, 25)]
    bot = [(RIM[0] + 0.45 * math.cos(a), RIM[1] + 0.45 * math.sin(a), 8.6 - net_swish * 0.6) for a in np.linspace(0, 2 * math.pi, 25)]
    for a, b in zip(ring[::2], bot[::2]):
        pa, pb = cam.proj(a), cam.proj(b)
        if pa and pb: d.line([pa[:2], pb[:2]], fill=(255, 255, 255, 200), width=2)
    pr = [cam.proj(p) for p in ring]
    if all(pr): d.line([q[:2] for q in pr], fill=(255, 100, 20, 255), width=max(3, int(cam.f / pr[0][2] * 0.18)))


def draw_player(c, cam, x, y, z, team, num, label, dim=1.0, glow=0.0):
    foot, head = cam.proj((x, y, z)), cam.proj((x, y, z + 6.6))
    if not foot or not head: return
    sh = cam.proj((x, y, 0))
    hgt = foot[1] - head[1]
    if hgt < 4: return
    s = abs(hgt)
    wbody = s * 0.36
    col = HEAT if team == "H" else SPURS
    dark = tuple(int(v * 0.55) for v in col)
    lay = Image.new("RGBA", c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if sh:
        d.ellipse([sh[0] - wbody * 0.8, sh[1] - wbody * 0.22, sh[0] + wbody * 0.8, sh[1] + wbody * 0.22], fill=(0, 0, 0, 90))
    if glow > 0:
        r = wbody * 1.3
        d.ellipse([sh[0] - r * 1.4, sh[1] - r * 0.42, sh[0] + r * 1.4, sh[1] + r * 0.42], outline=YEL + (int(255 * glow),), width=max(3, int(s * 0.04)))
    fx, fy = foot[0], foot[1]
    # jambes (short) + maillot
    d.rounded_rectangle([fx - wbody * 0.42, fy - s * 0.42, fx + wbody * 0.42, fy], radius=wbody * 0.2, fill=(30, 30, 36, 255) if team == "S" else (24, 24, 28, 255))
    d.rounded_rectangle([fx - wbody / 2, fy - s * 0.8, fx + wbody / 2, fy - s * 0.36], radius=wbody * 0.35, fill=col + (255,))
    d.rounded_rectangle([fx + wbody * 0.12, fy - s * 0.78, fx + wbody / 2, fy - s * 0.38], radius=wbody * 0.3, fill=dark + (110,))
    # tête
    hr = s * 0.115
    hx, hy = fx, fy - s * 0.88
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(120, 84, 60, 255))
    d.ellipse([hx - hr * 0.55, hy - hr * 0.7, hx - hr * 0.05, hy - hr * 0.25], fill=(255, 255, 255, 60))
    if num and s > 40:
        ti = text_img(num, "Black", max(10, int(s * 0.16)), (255, 255, 255) if team == "H" else (20, 20, 24))
        lay.alpha_composite(ti, (int(fx - ti.width / 2), int(fy - s * 0.66 - ti.height / 2)))
    if dim < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * dim)))
    c.alpha_composite(lay)
    if label and s > 30:
        tag = _tag(label, int(min(46, max(24, s * 0.12))))
        blit(c, tag, fx, fy - s * 1.08, alpha=max(dim, 0.4))


def _tag(label, size):
    t = text_img(label, "Black", size, (20, 20, 24))
    im = Image.new("RGBA", (t.width + size, t.height + size // 3), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=size // 3, fill=YEL + (255,))
    im.alpha_composite(t, (size // 2, size // 6)); return im


def draw_ball(c, cam, b):
    p, sh = cam.proj(b), cam.proj((b[0], b[1], 0))
    if not p: return
    r = max(4, cam.f * 0.62 / p[2])
    d = ImageDraw.Draw(c)
    if sh: d.ellipse([sh[0] - r, sh[1] - r * 0.3, sh[0] + r, sh[1] + r * 0.3], fill=(0, 0, 0, 80))
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(238, 112, 30, 255), outline=(60, 25, 5, 255), width=max(1, int(r * 0.12)))
    d.line([p[0] - r, p[1], p[0] + r, p[1]], fill=(60, 25, 5, 255), width=max(1, int(r * 0.1)))
    d.arc([p[0] - r * 0.6, p[1] - r, p[0] + r * 0.6, p[1] + r], 270, 90, fill=(60, 25, 5, 255), width=max(1, int(r * 0.1)))


def rope_pts(u):
    """Corde jaune autour du terrain (à 2,5 pieds du sol), dessinée jusqu'à la fraction u."""
    path = [(-27, -2), (27, -2), (27, 50), (-27, 50), (-27, -2)]
    segs = [(np.array(a, float), np.array(b, float)) for a, b in zip(path, path[1:])]
    tot = sum(np.linalg.norm(b - a) for a, b in segs); left = tot * u; out = [segs[0][0]]
    for a, b in segs:
        L = np.linalg.norm(b - a)
        if left >= L: out.append(b); left -= L
        else: out.append(a + (b - a) * left / L); break
    return out


def draw_rope(c, cam, u):
    if u <= 0: return
    d = ImageDraw.Draw(c); pts = rope_pts(u)
    pr = [cam.proj((x, y, 2.6)) for x, y in pts]
    if all(pr): d.line([q[:2] for q in pr], fill=YEL + (255,), width=max(6, int(cam.f / pr[0][2] * 0.5)), joint="curve")
    for x, y in [(-27, -2), (27, -2), (27, 50), (-27, 50), (0, -2), (27, 24), (-27, 24), (0, 50)]:
        a, b = cam.proj((x, y, 0)), cam.proj((x, y, 3.0))
        if a and b: d.line([a[:2], b[:2]], fill=(30, 30, 30, 255), width=max(3, int(cam.f / a[2] * 0.3)))


def draw_path(c, cam, pts, color, u=1.0, dash=True):
    d = ImageDraw.Draw(c)
    pr = [cam.proj((x, y, 0.05)) for x, y in pts]
    pr = [p for p in pr if p]
    n = max(2, int(len(pr) * u))
    for i in range(n - 1):
        if dash and i % 2: continue
        d.line([pr[i][:2], pr[i + 1][:2]], fill=color + (255,), width=8)


# ---------------------------------------------------------------- 2D : titres, score, sons
def title(c, k, tl):
    a, b, col = INFO[k]
    e = min(1, tl / 0.28)
    sm = outlined(a, "Black", 56, WHITE, 8)
    bg = outlined(b, "Black", 118, col, 12)
    sc = min(1.0, 1000 / bg.width)
    blit(c, sm, W / 2, 250 - 40 * (1 - ease_out(e)), alpha=e, scale=min(1, 1000 / sm.width))
    blit(c, bg, W / 2, 350, scale=sc * (0.7 + 0.3 * ease_back(min(1, max(0, tl - 0.06) / 0.3))), alpha=min(1, max(0, tl - 0.06) / 0.12))


def scoreboard(c, k):
    mia, sa, clock = SCORE[k]
    im = Image.new("RGBA", (560, 74), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 559, 73], radius=18, fill=(12, 12, 16, 225))
    d.rounded_rectangle([0, 0, 120, 73], radius=18, fill=HEAT + (255,)); d.rectangle([60, 0, 120, 73], fill=HEAT + (255,))
    d.rounded_rectangle([439, 0, 559, 73], radius=18, fill=(70, 74, 80, 255)); d.rectangle([439, 0, 500, 73], fill=(70, 74, 80, 255))
    for txt, x, f, s in [("MIA", 60, "Black", 34), (f"{mia} – {sa}", 280, "Black", 44), ("SA", 499, "Black", 34)]:
        t = text_img(txt, f, s, (255, 255, 255)); im.alpha_composite(t, (int(x - t.width / 2), int(37 - t.height / 2)))
    blit(c, im, W / 2, 478)
    if clock:
        t = text_img(clock, "Black", 34, (20, 20, 24))
        ch = Image.new("RGBA", (t.width + 30, 52), (0, 0, 0, 0))
        ImageDraw.Draw(ch).rounded_rectangle([0, 0, ch.width - 1, 51], radius=14, fill=YEL + (255,))
        ch.alpha_composite(t, (15, int(26 - t.height / 2))); blit(c, ch, W / 2, 550)


def chip(c, txt, y=1390):
    t = text_img(txt, "ExtraBold", 28, (255, 255, 255))
    im = Image.new("RGBA", (t.width + 50, 46), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, 45], radius=12, fill=(0, 0, 0, 150))
    d.ellipse([14, 16, 28, 30], fill=(235, 52, 64, 255))
    im.alpha_composite(t, (38, int(23 - t.height / 2))); blit(c, im, 40, y, anchor="lm")


class TL:
    def __init__(self, cues, total):
        self.span = {}
        for i, (k, s, e) in enumerate(cues):
            nxt = cues[i + 1][1] - 0.05 if i + 1 < len(cues) else total + 1.6
            self.span[k] = (max(0, s - (0.15 if i else 0)), nxt)
        self.total = self.span[ORDER[-1]][1]

    def at(self, t):
        for k in ORDER:
            a, b = self.span[k]
            if t < b: return k, a, b
        k = ORDER[-1]; return k, *self.span[k]


def camera(T, t):
    k, a, b = T.at(t)
    i = ORDER.index(k)
    p = (t - a) / max(b - a, 1e-3)
    A, B = CAMS[k]
    cur = cam_mix(A, B, ease_out(p) if k != "SHOT" else p)
    if i and t - a < 0.7 and k not in ("IN",):
        prev = CAMS[ORDER[i - 1]][1]
        cur = cam_mix(prev, cur, ease_out((t - a) / 0.7))
    shake = 0.0
    if k == "IN" and t - a < 0.6: shake = (0.6 - (t - a)) * 0.6
    pos = cur[0] + shake * np.array([math.sin(t * 90), math.cos(t * 77), 0])
    return Cam(pos, cur[1], cur[2])


# ---------------------------------------------------------------- image
FLOOR = CROWD = None


def build():
    global FLOOR, CROWD
    ft = _floor_tex()
    FLOOR = Plane(ft, (-34, -8, 0), (1 / S, 0, 0), (0, 1 / S, 0))
    s = 8
    CROWD = {}
    for kind, frac in (("full", 1.0), ("sparse", 0.15)):
        back = _crowd_tex(68, 34, s, 1, frac); side = _crowd_tex(70, 34, s, 2, frac)
        CROWD[kind] = [Plane(back, (-34, -8, 34), (1 / s, 0, 0), (0, 0, -1 / s)),
                       Plane(side, (-34, 62, 34), (0, -1 / s, 0), (0, 0, -1 / s)),
                       Plane(side.transpose(Image.FLIP_LEFT_RIGHT), (34, -8, 34), (0, 1 / s, 0), (0, 0, -1 / s))]


def frame(t, T, groups):
    cam = camera(T, t)
    pos, z, k, p, tl = player_state(T, t)
    c = Image.new("RGBA", (W, H), (10, 10, 14, 255))
    # tribunes (demi-résolution), qui se vident pendant la scène des cordes
    half = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0))
    i_rope = ORDER.index("ROPE"); i = ORDER.index(k)
    empt = 0 if i < i_rope else (min(1, p * 1.3) if i == i_rope else 1)
    if k in ("IN", "WIN") and False: empt = 0
    for pl in CROWD["full"]: pl.draw(half, cam, 0.5)
    if empt > 0:
        sp = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0))
        for pl in CROWD["sparse"]: pl.draw(sp, cam, 0.5)
        sp.putalpha(sp.getchannel("A").point(lambda v: int(v * empt)))
        half.alpha_composite(sp)
    c.alpha_composite(half.resize((W, H), Image.BILINEAR))
    FLOOR.draw(c, cam)
    # spot sur le panier / assombrissement pour la scène « regarde »
    rope_u = 0 if i < i_rope else (min(1, p / 0.8) if i == i_rope else 1)
    draw_rope(c, cam, rope_u)
    if k == "WHY":
        path = [lerp(np.array((12, 14)), np.array((23, 4.5)), u) for u in np.linspace(0, 1, 30)]
        draw_path(c, cam, path, YEL, u=min(1, p * 1.6))
        draw_path(c, cam, [lerp(np.array((1.5, 8.5)), np.array((23, 4.5)), u) for u in np.linspace(0, 1, 30)], (255, 255, 255), u=min(1, max(0, p * 1.6 - 0.4)))
    # objets triés par profondeur
    objs = []
    swish = max(0, 1 - abs(p - 0.25) / 0.25) if k == "IN" else 0
    objs.append(((cam.proj((0, 4, 10)) or (0, 0, 1e9))[2] + 0.1, "hoop", None))
    focus = k in ("LOOK", "CORNER")
    for n, (team, num, label) in PL.items():
        q = cam.proj((*pos[n], 0))
        if q: objs.append((q[2], "pl", n))
    b = ball_state(pos, z, k, p)
    if b is not None:
        q = cam.proj(b)
        if q: objs.append((q[2] - 0.5, "ball", b))
    for depth, kind, o in sorted(objs, key=lambda v: -v[0]):
        if kind == "hoop": draw_hoop(c, cam, swish)
        elif kind == "ball": draw_ball(c, cam, o)
        else:
            team, num, label = PL[o]
            show = label if (k not in ("H", "CTX", "ROPE", "E", "IN") or o == "lebron") else None
            if k == "WIN": show = None
            dim = 0.45 if (focus and o not in ("allen", "bosh")) else 1.0
            glow = (0.6 + 0.4 * math.sin(t * 8)) if (o == "allen" and k in ("LOOK", "CORNER")) else 0.0
            draw_player(c, cam, *pos[o], z[o], team, num, show, dim, glow)
    # effets
    if k == "IN" and tl < 0.5:
        fl = Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - tl / 0.5)))); c.alpha_composite(fl)
    if k == "WIN" and p > 0.4:
        _confetti(c, t)
    if k == "SHOT":  # ralenti : bandes de cinéma
        e = ease_out(min(1, tl / 0.4)); d = ImageDraw.Draw(c)
        d.rectangle([0, 0, W, 130 * e], fill=(0, 0, 0, 255)); d.rectangle([0, H - 130 * e, W, H], fill=(0, 0, 0, 255))
    # dégradés haut/bas pour la lisibilité
    c.alpha_composite(GRAD)
    title(c, k, tl)
    scoreboard(c, k)
    if k in ("MISS", "REB", "LOOK", "CORNER", "SHOT", "WHY"):
        chip(c, "REPLAY · RECONSTITUTION" if k == "WHY" else "RECONSTITUTION SIMPLIFIÉE")
    captions(c, t, groups)
    return c.convert("RGB")


def _grad():
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for y in range(0, 520):
        d.line([0, y, W, y], fill=(0, 0, 0, int(170 * (1 - y / 520) ** 1.4)))
    for y in range(1300, H):
        d.line([0, y, W, y], fill=(0, 0, 0, int(190 * ((y - 1300) / (H - 1300)) ** 1.3)))
    return g


GRAD = None


def _confetti(c, t):
    d = ImageDraw.Draw(c); rng = np.random.default_rng(7)
    for i in range(140):
        x = (rng.random() * W + 40 * math.sin(t * 2 + i)) % W
        y = (rng.random() * H + t * (220 + 160 * rng.random())) % H
        col = [(255, 255, 255), HEAT, (235, 52, 64), YEL][i % 4]
        a = t * 4 + i; w_, h_ = 16 * abs(math.cos(a)) + 4, 10
        d.rectangle([x, y, x + w_, y + h_], fill=col + (255,))


# ---------------------------------------------------------------- son
def _noise(d, k=40, seed=2):
    x = np.random.default_rng(seed).normal(0, 1, int(d * SR))
    y = np.convolve(x, np.ones(k) / k, mode="same"); return y / (np.abs(y).max() + 1e-9)


def mix(voice_wav, T, out_wav):
    with wave.open(voice_wav) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, w.getnchannels()).mean(1) / 32768
    n = int(T.total * SR); out = np.zeros(n, np.float32); out[:min(n, len(v))] += v[:n]

    def add(x, t, g):
        i = int(t * SR)
        if i >= n: return
        x = x[: n - i]; out[i:i + len(x)] += x * g

    crowd = _noise(T.total, 200, 5) * 0.035
    out += crowd[:n].astype(np.float32)
    for k in ORDER[1:]:
        add(whoosh(), max(0, T.span[k][0] - 0.12), 0.09)
    a, b = T.span["MISS"]; add(_sine(220, 0.5, 9) + 0.6 * _sine(330, 0.5, 12), a + (b - a) * 0.72, 0.22)    # clang
    a, b = T.span["SHOT"]
    for j in range(int((b - a) / 0.75)):                                                                   # battements de cœur
        add(_sine(55, 0.22, 18) + 0.5 * _sine(80, 0.18, 20), a + 0.1 + j * 0.75, 0.5)
    a, b = T.span["IN"]
    add(_noise(0.25, 6, 3) * np.exp(-np.arange(int(0.25 * SR)) / SR * 14), a, 0.25)                       # filet
    roar = _noise(3.5, 30, 9) * np.minimum(1, np.arange(int(3.5 * SR)) / (0.2 * SR)) * np.exp(-np.arange(int(3.5 * SR)) / SR * 0.8)
    add(roar, a + 0.05, 0.22)
    a, b = T.span["WIN"]; add(roar, a + (b - a) * 0.4, 0.18)
    out = np.clip(out, -1, 1)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="docs/proto"); ap.add_argument("--frames", default="")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    global GRAD
    GRAD = _grad(); build()
    vw = os.path.join(a.out, "voix_action.wav")
    cues, total = tts.synth(SEGS, vw)
    T = TL(cues, total)
    groups = chunks(words_from_last())
    if not groups:
        ws = []
        for k, s, e in cues:
            txt = re.sub(r"\[[^\]]*\]", "", dict(SEGS)[k]).split()
            for i, w_ in enumerate(txt): ws.append((w_, s + (e - s) * i / len(txt), s + (e - s) * (i + 1) / len(txt)))
        groups = chunks(ws)
    if a.frames:   # images de test : temps en secondes, ou « k:CUE:fraction »
        for spec in a.frames.split(","):
            if spec.startswith("k:"):
                _, k, f = spec.split(":"); s_, e_ = T.span[k]; t = s_ + (e_ - s_) * float(f)
            else: t = float(spec)
            frame(t, T, groups).save(os.path.join(a.out, f"f_{spec.replace(':', '_')}.jpg"), quality=85)
        print("durée", round(T.total, 1)); return
    silent = os.path.join(a.out, "action_silent.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    cover_t = T.span["CORNER"][0] + 0.8 * (T.span["CORNER"][1] - T.span["CORNER"][0])
    for i in range(int(T.total * FPS)):
        im = frame(i / FPS, T, groups)
        if abs(i / FPS - cover_t) < 0.5 / FPS: im.save(os.path.join(a.out, FILE + ".jpg"), quality=90)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    aud = os.path.join(a.out, "action_audio.wav"); mix(vw, T, aud)
    final = os.path.join(a.out, FILE + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", aud, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-shortest", final], check=True)
    for f in (silent, aud, vw, vw.replace(".wav", ".mp3")):
        if os.path.exists(f): os.remove(f)
    print("Vidéo :", final, f"{T.total:.1f}s")


if __name__ == "__main__":
    main()
