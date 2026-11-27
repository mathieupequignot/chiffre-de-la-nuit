"""Format « L'ACTION QUI A TOUT CHANGÉ » — une action mythique racontée comme un thriller, reconstituée sur un
terrain 3D stylisé (pions aux couleurs des équipes, caméra qui bouge), voix off, gros titre en deux lignes,
sous-titres mot à mot, nappe sonore maison. Aucune image de match, aucune musique protégée.

Chaque épisode est un fichier JSON (action/episodes/*.json) : scènes (titre, voix, caméra, score), joueurs,
déplacements, ballon, effets. Mode d'emploi et carnet : action/FORMAT.md.
usage : python -m action.main --episode action/episodes/ray_allen_2013.json [--out docs/proto] [--queue-at "AAAA-MM-JJ HH:MM"]
        [--frames "k:CUE:0.5,12.3"]  (images de test, sans voix si pas de clé ElevenLabs)"""
import argparse, json, math, os, re, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from chiffre import tts
from chiffre.render import W, H, FPS, WHITE, text_img, blit, ease_out, ease_back
from top10.main import outlined, chunks, words_from_last, captions, whoosh, _sine, SR

YEL = (255, 214, 10)
RED = (235, 52, 64)
GREEN = (60, 220, 120)
WOOD = (219, 176, 122)
NAMED = {"yellow": YEL, "red": RED, "green": GREEN, "white": WHITE, "silver": (190, 198, 206), "blue": (60, 140, 255),
         "orange": (255, 140, 30)}
RIM = np.array([0.0, 5.25, 10.0])
UP = np.array([0.0, 0.0, 1.0])

EP = {}; SC = {}; ORDER = []; TEAM = {}


def col(v, default=WHITE):
    if v is None: return default
    return NAMED[v] if isinstance(v, str) else tuple(v)


def load(path):
    global EP, SC, ORDER, TEAM
    EP = json.load(open(path, encoding="utf-8"))
    ORDER = [s["cue"] for s in EP["scenes"]]
    SC = {s["cue"]: s for s in EP["scenes"]}
    TEAM = {k: dict(code=v["code"], color=tuple(v["color"]), num=tuple(v.get("num", (255, 255, 255))),
                    shorts=tuple(v.get("shorts", (24, 24, 28)))) for k, v in EP["teams"].items()}


# ---------------------------------------------------------------- caméra (pieds ; x à droite, y vers la caméra, z en haut ; panier en (0, 5.25))
class Cam:
    def __init__(self, pos, tgt, f):
        self.pos, self.tgt, self.f = np.array(pos, float), np.array(tgt, float), float(f)
        fw = self.tgt - self.pos; fw /= np.linalg.norm(fw)
        r = np.cross(UP, fw)
        if np.linalg.norm(r) < 1e-6: r = np.array([1.0, 0, 0])
        r /= np.linalg.norm(r); u = np.cross(fw, r)
        self.R = np.stack([r, -u, fw])
        K = np.array([[self.f, 0, W / 2], [0, self.f, H / 2], [0, 0, 1]])
        self.M = K @ np.hstack([self.R, (-self.R @ self.pos)[:, None]])

    def proj(self, p):
        q = self.M @ np.append(np.asarray(p, float), 1.0)
        if q[2] <= 0.5: return None
        return q[0] / q[2], q[1] / q[2], q[2]


def lerp(a, b, k): return a + (b - a) * k


def cam_mix(a, b, k): return lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)


# plans de caméra prêts à l'emploi (position, cible, focale) ; un épisode peut aussi donner des nombres
PRESETS = {
    "wide": ((0, 70, 46), (0, 15, 0), 1500), "wide_close": ((8, 64, 40), (0, 13, 0), 1550),
    "wide_left": ((-30, 70, 60), (0, 14, 0), 1300), "wide_right": ((30, 70, 60), (0, 14, 0), 1300),
    "high_left": ((-24, 66, 66), (0, 18, 0), 1100), "high_right": ((28, 66, 70), (0, 18, 0), 1100),
    "top": ((0, 30, 52), (0, 8, 0), 1450), "top_right": ((12, 30, 52), (12, 8, 0), 1450), "top_left": ((-12, 30, 52), (-12, 8, 0), 1450),
    "paint": ((10, 30, 16), (1, 7, 6), 1400), "rim": ((14, 18, 11), (0, 5.5, 9.5), 1700),
    "wing_right": ((24, 36, 22), (12, 12, 4), 1500), "wing_left": ((-24, 36, 22), (-12, 12, 4), 1500),
    "corner_right": ((22, 40, 30), (14, 8, 3), 1300), "corner_left": ((-22, 40, 30), (-14, 8, 3), 1300),
    "side_right": ((12, 38, 15), (11.5, 5, 8), 980), "side_left": ((-12, 38, 15), (-11.5, 5, 8), 980),
    "top_key": ((-14, 52, 30), (-2, 12, 4), 1500), "celebrate": ((0, 60, 26), (0, 26, 4), 1300),
}


def camspec(v):
    if isinstance(v, str): v = PRESETS[v]
    return np.array(v[0], float), np.array(v[1], float), float(v[2])


# ---------------------------------------------------------------- joueurs, ballon
def player_state(T, t):
    k, a, b = T.at(t)
    pos = {n: np.array(v["pos"], float) for n, v in EP["players"].items()}
    for c in ORDER:
        if c == k: break
        for n, m in SC[c].get("moves", {}).items(): pos[n] = np.array(m["to"], float)
    p = (t - a) / max(b - a, 1e-3)
    S_ = SC[k]
    z = {n: 0.0 for n in pos}
    for n, m in S_.get("moves", {}).items():
        p0, p1 = m.get("p", [0, 1])
        start = np.array(m["from"], float) if "from" in m else pos[n]
        e = ease_out(min(1, max(0, (p - p0) / max(p1 - p0, 1e-3))))
        pos[n] = lerp(start, np.array(m["to"], float), e)
    for n, (p0, p1, hgt) in S_.get("jumps", {}).items():
        if p0 <= p <= p1: z[n] = hgt * math.sin(math.pi * (p - p0) / (p1 - p0))
    for i, n in enumerate(S_.get("celebrate", [])):
        if p > 0.45: z[n] = 2.2 * abs(math.sin((t - a) * 5 + i * 0.6))
    return pos, z, k, p, t - a


def arms_up(k, p, n):
    S_ = SC[k]
    r = S_.get("arms", {}).get(n)
    return bool((r and r[0] <= p <= r[1]) or (n in S_.get("celebrate", []) and p > 0.45))


def arc(p0, p1, apex, u):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    q = lerp(p0, p1, u); q[2] += apex * 4 * u * (1 - u); return q


def hand(pos, z, n, h=7.6):
    x, y = pos[n]; return np.array([x, y, z[n] + h])


def point(spec, pos, z, h):
    if isinstance(spec, str):
        if spec == "rim": return RIM + [0, 0, 0.6]
        return hand(pos, z, spec, h)
    return np.array(spec, float)


def ball_state(pos, z, k, p):
    """Opérations du ballon d'une scène : dribble, hold, pass, shot (make/miss), arc, through, at."""
    ops = SC[k].get("ball", [])
    if not ops: return None
    op = next((o for o in ops if o.get("p", [0, 1])[0] <= p < o.get("p", [0, 1])[1]), ops[-1] if p >= ops[-1].get("p", [0, 1])[1] else None)
    if op is None: return None
    p0, p1 = op.get("p", [0, 1]); u = min(1, max(0, (p - p0) / max(p1 - p0, 1e-3))); kind = op["do"]
    if kind == "dribble":
        x, y = pos[op["who"]]; return np.array([x + 0.9, y - 0.4, 1.2 + abs(math.sin(p * 18 + p0)) * 1.6])
    if kind == "hold": return hand(pos, z, op["who"], op.get("h", 7.6))
    if kind == "at": return np.array(op["at"], float)
    if kind == "pass":
        return arc(point(op["from"], pos, z, op.get("hf", 6.0)), point(op["to"], pos, z, op.get("ht", 4.5)), op.get("apex", 2.5), u)
    if kind == "arc":
        return arc(point(op["from"], pos, z, op.get("hf", 7.6)), point(op["to"], pos, z, op.get("ht", 7.6)), op.get("apex", 2.0), u)
    if kind == "shot":
        src = point(op.get("from", op.get("who")), pos, z, op.get("hf", 7.8))
        dst = RIM + ([0, 0, 0.6] if op.get("result", "make") == "make" else [-0.6, 0, 0.4])
        return arc(src, dst, op.get("apex", 9), u)
    if kind == "through": return lerp(RIM + [0, 0, 0.6], np.array([0, 5.25, op.get("floor", 2.0)]), u)
    return None


# ---------------------------------------------------------------- textures (sol, tribunes)
S = 14  # pixels par pied pour le sol


def _floor_tex():
    x0, x1, y0, y1 = -34, 34, -8, 62
    im = Image.new("RGBA", ((x1 - x0) * S, (y1 - y0) * S), (26, 26, 32, 255)); d = ImageDraw.Draw(im)
    P = lambda x, y: ((x - x0) * S, (y - y0) * S)
    d.rectangle([*P(-25, 0), *P(25, 62)], fill=WOOD + (255,))
    rng = np.random.default_rng(4)
    for x in np.arange(-25, 25, 0.75):
        c = tuple(int(v * (0.92 + 0.08 * rng.random())) for v in WOOD)
        d.rectangle([*P(x, 0), *P(x + 0.74, 62)], fill=c + (255,))
    lw = 3; L = (255, 255, 255, 255); paint = col(EP.get("paint"), TEAM["A"]["color"])
    d.rectangle([*P(-8, 0), *P(8, 19)], fill=paint + (255,), outline=L, width=lw)
    d.ellipse([*P(-6, 13), *P(6, 25)], outline=L, width=lw)
    d.arc([*P(-4, 1.25), *P(4, 9.25)], 0, 180, fill=L, width=lw)
    d.line([P(-22, 0), P(-22, 14.2)], fill=L, width=lw); d.line([P(22, 0), P(22, 14.2)], fill=L, width=lw)
    ang = math.degrees(math.asin((14.2 - 5.25) / 23.75))
    d.arc([*P(-23.75, 5.25 - 23.75), *P(23.75, 5.25 + 23.75)], ang, 180 - ang, fill=L, width=lw)
    d.rectangle([*P(-25, 0), *P(25, 62)], outline=L, width=lw)
    d.line([P(-25, 47), P(25, 47)], fill=L, width=lw)
    d.ellipse([*P(-6, 41), *P(6, 53)], outline=L, width=lw)
    t = text_img(EP.get("floor_text", "L'ACTION QUI A TOUT CHANGÉ"), "Black", 64, (255, 255, 255)).rotate(90, expand=True)
    im.alpha_composite(t, (int(P(-29.5, 0)[0]), int(P(0, 12)[1])))
    im.alpha_composite(t.rotate(180), (int(P(26.6, 0)[0]), int(P(0, 12)[1])))
    return im


def _crowd_tex(wft, hft, s, seed, frac=1.0):
    w, h = int(wft * s), int(hft * s)
    im = Image.new("RGBA", (w, h), (14, 14, 20, 255)); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    pal = [(235, 235, 235), (230, 230, 230), TEAM["A"]["color"], TEAM["B"]["color"], (30, 30, 34), (250, 200, 60), (90, 120, 200)]
    row = 2.4 * s; band = 3.2 * s; y = 0.0
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
    d.rectangle([0, h - band, w, h - band + s * 0.3], fill=TEAM["A"]["color"] + (255,))
    msg = text_img(f"{EP.get('floor_text', '')}  ·  L'ACTION QUI A TOUT CHANGÉ  ·  ", "Black", int(s * 1.5), (255, 255, 255))
    x = 0
    while x < w:
        im.alpha_composite(msg, (x, int(h - band / 2 - msg.height / 2 + s * 0.15))); x += msg.width
    return im


class Plane:
    """Surface plane texturée : monde = O + U*px + V*py."""
    def __init__(self, tex, O, U, V):
        self.tex, self.O, self.U, self.V = tex, np.array(O, float), np.array(U, float), np.array(V, float)

    def draw(self, canvas, cam, scale=1.0):
        Hm = cam.M @ np.array([[*self.U, 0], [*self.V, 0], [*self.O, 1]]).T
        Hm = np.diag([scale, scale, 1.0]) @ Hm
        try: Hi = np.linalg.inv(Hm)
        except np.linalg.LinAlgError: return
        Hi = Hi / Hi[2, 2] if abs(Hi[2, 2]) > 1e-12 else Hi
        cw, ch = canvas.size
        out = self.tex.transform((cw, ch), Image.PERSPECTIVE, tuple(Hi.flatten()[:8]), Image.BILINEAR, fillcolor=(0, 0, 0, 0))
        c = self.O + self.U * self.tex.width / 2 + self.V * self.tex.height / 2
        pr = cam.proj(c); g = Hi[2]
        ref = np.sign(g[0] * pr[0] * scale + g[1] * pr[1] * scale + g[2]) if pr is not None else (np.sign(g[2]) or 1)
        poly = _clip([(0, 0), (cw, 0), (cw, ch), (0, ch)], lambda q: ref * (g[0] * q[0] + g[1] * q[1] + g[2]) - 1e-9)
        if len(poly) < 3: return
        m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
        out.putalpha(Image.fromarray(np.minimum(np.asarray(out.getchannel("A")), np.asarray(m))))
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


def draw_hoop(c, cam, net_swish=0.0, shake=0.0):
    d = ImageDraw.Draw(c)
    _poly3(d, cam, [(-0.4, -4, 0), (0.4, -4, 0), (0.4, -4, 12), (-0.4, -4, 12)], fill=(40, 40, 48, 255))
    _poly3(d, cam, [(-0.3, -4, 11.4), (0.3, -4, 11.4), (0.3, 4, 11.4), (-0.3, 4, 11.4)], fill=(60, 60, 70, 255))
    _poly3(d, cam, [(-3, 4, 9.5), (3, 4, 9.5), (3, 4, 13), (-3, 4, 13)], fill=(255, 255, 255, 70), outline=(255, 255, 255, 255))
    _poly3(d, cam, [(-1, 4.02, 10), (1, 4.02, 10), (1, 4.02, 11.5), (-1, 4.02, 11.5)], outline=(255, 255, 255, 255))
    ring = [(RIM[0] + shake + 0.75 * math.cos(a), RIM[1] + 0.75 * math.sin(a), 10) for a in np.linspace(0, 2 * math.pi, 25)]
    bot = [(RIM[0] + 0.45 * math.cos(a), RIM[1] + 0.45 * math.sin(a), 8.6 - net_swish * 0.6) for a in np.linspace(0, 2 * math.pi, 25)]
    for a, b in zip(ring[::2], bot[::2]):
        pa, pb = cam.proj(a), cam.proj(b)
        if pa and pb: d.line([pa[:2], pb[:2]], fill=(255, 255, 255, 200), width=2)
    pr = [cam.proj(p) for p in ring]
    if all(pr): d.line([q[:2] for q in pr], fill=(255, 100, 20, 255), width=max(3, int(cam.f / pr[0][2] * 0.18)))


def draw_player(c, cam, x, y, z, team, num, label, dim=1.0, glow=0.0, up=False, run=None):
    foot, head = cam.proj((x, y, z)), cam.proj((x, y, z + 6.6))
    if not foot or not head: return
    sh = cam.proj((x, y, 0))
    hgt = foot[1] - head[1]
    if hgt < 4: return
    s = abs(hgt); wbody = s * 0.36
    T_ = TEAM[team]; colr = T_["color"]; dark = tuple(int(v * 0.55) for v in colr)
    lay = Image.new("RGBA", c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if sh:
        d.ellipse([sh[0] - wbody * 0.8, sh[1] - wbody * 0.22, sh[0] + wbody * 0.8, sh[1] + wbody * 0.22], fill=(0, 0, 0, 90))
    if glow > 0 and sh:
        r = wbody * 1.3
        d.ellipse([sh[0] - r * 1.4, sh[1] - r * 0.42, sh[0] + r * 1.4, sh[1] + r * 0.42], outline=YEL + (int(255 * glow),), width=max(3, int(s * 0.04)))
    fx, fy = foot[0], foot[1]
    skin = (120, 84, 60, 255)
    for sgn in (-1, 1):
        lift = max(0, (math.sin(run + (0 if sgn < 0 else math.pi)) * s * 0.06) if run is not None else 0)
        d.rounded_rectangle([fx + sgn * wbody * 0.22 - wbody * 0.12, fy - s * 0.3, fx + sgn * wbody * 0.22 + wbody * 0.12, fy - lift],
                            radius=wbody * 0.1, fill=skin)
        d.ellipse([fx + sgn * wbody * 0.22 - wbody * 0.16, fy - lift - wbody * 0.12, fx + sgn * wbody * 0.22 + wbody * 0.16, fy - lift + wbody * 0.06], fill=(245, 245, 245, 255))
    d.rounded_rectangle([fx - wbody * 0.46, fy - s * 0.46, fx + wbody * 0.46, fy - s * 0.26], radius=wbody * 0.15, fill=T_["shorts"] + (255,))
    aw = max(3, int(wbody * 0.2))
    for sgn in (-1, 1):
        sx_, sy_ = fx + sgn * wbody * 0.46, fy - s * 0.74
        if up: hx_, hy_ = fx + sgn * wbody * 0.42, fy - s * 1.1
        else:
            sw = (math.sin(run + (0 if sgn > 0 else math.pi)) * wbody * 0.25) if run is not None else 0
            hx_, hy_ = fx + sgn * wbody * 0.66 + sw * 0.3, fy - s * 0.42 - abs(sw) * 0.3
        d.line([sx_, sy_, hx_, hy_], fill=skin, width=aw)
        d.ellipse([hx_ - aw * 0.6, hy_ - aw * 0.6, hx_ + aw * 0.6, hy_ + aw * 0.6], fill=skin)
    d.rounded_rectangle([fx - wbody / 2, fy - s * 0.8, fx + wbody / 2, fy - s * 0.4], radius=wbody * 0.35, fill=colr + (255,))
    d.rounded_rectangle([fx + wbody * 0.12, fy - s * 0.78, fx + wbody / 2, fy - s * 0.42], radius=wbody * 0.3, fill=dark + (110,))
    hr = s * 0.115; hx, hy = fx, fy - s * 0.88
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=skin)
    d.ellipse([hx - hr * 0.55, hy - hr * 0.7, hx - hr * 0.05, hy - hr * 0.25], fill=(255, 255, 255, 60))
    if num and s > 40:
        ti = text_img(num, "Black", max(10, int(s * 0.16)), T_["num"])
        lay.alpha_composite(ti, (int(fx - ti.width / 2), int(fy - s * 0.62 - ti.height / 2)))
    if dim < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * dim)))
    c.alpha_composite(lay)
    if label and s > 30:
        blit(c, _tag(label, int(min(46, max(24, s * 0.12)))), fx, fy - s * 1.08, alpha=max(dim, 0.4))


def _tag(label, size, bg=YEL, fg=(20, 20, 24)):
    t = text_img(label, "Black", size, fg)
    im = Image.new("RGBA", (t.width + size, t.height + size // 3), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=size // 3, fill=bg + (255,))
    im.alpha_composite(t, (size // 2, size // 6)); return im


def draw_ball(c, cam, b):
    p, sh = cam.proj(b), cam.proj((b[0], b[1], 0))
    if not p: return
    r = max(4, cam.f * 0.62 / p[2]); d = ImageDraw.Draw(c)
    if sh: d.ellipse([sh[0] - r, sh[1] - r * 0.3, sh[0] + r, sh[1] + r * 0.3], fill=(0, 0, 0, 80))
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(238, 112, 30, 255), outline=(60, 25, 5, 255), width=max(1, int(r * 0.12)))
    d.line([p[0] - r, p[1], p[0] + r, p[1]], fill=(60, 25, 5, 255), width=max(1, int(r * 0.1)))
    d.arc([p[0] - r * 0.6, p[1] - r, p[0] + r * 0.6, p[1] + r], 270, 90, fill=(60, 25, 5, 255), width=max(1, int(r * 0.1)))


def rope_pts(u):
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
    pr = [q for q in (cam.proj((x, y, 0.05)) for x, y in pts) if q]
    n = max(2, int(len(pr) * u))
    for i in range(min(n, len(pr)) - 1):
        if dash and i % 2: continue
        d.line([pr[i][:2], pr[i + 1][:2]], fill=color + (255,), width=8)


def _polyline(pts, n=30):
    pts = [np.array(p, float) for p in pts]
    segs = list(zip(pts, pts[1:])); out = []
    for a, b in segs: out += [lerp(a, b, u) for u in np.linspace(0, 1, max(2, n // len(segs)))]
    return out


# ---------------------------------------------------------------- 2D : titres, score
def title(c, k, tl):
    S_ = SC[k]
    e = min(1, tl / 0.28)
    sm = outlined(S_["small"], "Black", 56, WHITE, 8)
    bg = outlined(S_["big"], "Black", 118, col(S_.get("color"), YEL), 12)
    blit(c, sm, W / 2, 250 - 40 * (1 - ease_out(e)), alpha=e, scale=min(1, 1000 / sm.width))
    blit(c, bg, W / 2, 350, scale=min(1.0, 1000 / bg.width) * (0.7 + 0.3 * ease_back(min(1, max(0, tl - 0.06) / 0.3))),
         alpha=min(1, max(0, tl - 0.06) / 0.12))


def scoreboard(c, k):
    S_ = SC[k]
    if "score" not in S_: return
    a_, b_ = S_["score"]; A, B = TEAM["A"], TEAM["B"]
    im = Image.new("RGBA", (560, 74), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 559, 73], radius=18, fill=(12, 12, 16, 225))
    d.rounded_rectangle([0, 0, 120, 73], radius=18, fill=A["color"] + (255,)); d.rectangle([60, 0, 120, 73], fill=A["color"] + (255,))
    bcol = tuple(int(v * 0.4) for v in B["color"]) if sum(B["color"]) > 500 else B["color"]
    d.rounded_rectangle([439, 0, 559, 73], radius=18, fill=bcol + (255,)); d.rectangle([439, 0, 500, 73], fill=bcol + (255,))
    for txt, x, s in [(A["code"], 60, 34), (f"{a_} – {b_}", 280, 44), (B["code"], 499, 34)]:
        t = text_img(txt, "Black", s, (255, 255, 255)); im.alpha_composite(t, (int(x - t.width / 2), int(37 - t.height / 2)))
    blit(c, im, W / 2, 478)
    if S_.get("clock"):
        t = text_img(S_["clock"], "Black", 34, (20, 20, 24))
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


def scene_cams(k):
    v = SC[k]["cam"]
    if isinstance(v, dict): return camspec(v["from"]), camspec(v.get("to", v["from"]))
    return camspec(v), camspec(v)


def camera(T, t):
    k, a, b = T.at(t)
    i = ORDER.index(k); S_ = SC[k]
    p = (t - a) / max(b - a, 1e-3)
    A, B = scene_cams(k)
    cur = cam_mix(A, B, p if S_.get("slowmo") else ease_out(p))
    if i and t - a < 0.7 and not S_.get("cut"):
        cur = cam_mix(scene_cams(ORDER[i - 1])[1], cur, ease_out((t - a) / 0.7))
    shake = (0.6 - (t - a)) * 0.6 if (S_.get("shake") and t - a < 0.6) else 0.0
    return Cam(cur[0] + shake * np.array([math.sin(t * 90), math.cos(t * 77), 0]), cur[1], cur[2])


# ---------------------------------------------------------------- image
FLOOR = CROWD = GRAD = None


def build():
    global FLOOR, CROWD, GRAD
    FLOOR = Plane(_floor_tex(), (-34, -8, 0), (1 / S, 0, 0), (0, 1 / S, 0))
    s = 8; CROWD = {}
    for kind, frac in (("full", 1.0), ("sparse", 0.15)):
        back = _crowd_tex(68, 34, s, 1, frac); side = _crowd_tex(70, 34, s, 2, frac)
        CROWD[kind] = [Plane(back, (-34, -8, 34), (1 / s, 0, 0), (0, 0, -1 / s)),
                       Plane(side, (-34, 62, 34), (0, -1 / s, 0), (0, 0, -1 / s)),
                       Plane(side.transpose(Image.FLIP_LEFT_RIGHT), (34, -8, 34), (0, 1 / s, 0), (0, 0, -1 / s))]
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for y in range(0, 520): d.line([0, y, W, y], fill=(0, 0, 0, int(170 * (1 - y / 520) ** 1.4)))
    for y in range(1300, H): d.line([0, y, W, y], fill=(0, 0, 0, int(190 * ((y - 1300) / (H - 1300)) ** 1.3)))
    GRAD = g


def _progress(i, p, cue):
    """0 avant la scène `cue`, montée pendant, 1 après (cordes, tribunes qui se vident)."""
    if not cue or cue not in ORDER: return 0.0
    j = ORDER.index(cue)
    return 0.0 if i < j else (min(1, p / 0.8) if i == j else 1.0)


def frame(t, T, groups, bare=False):
    cam = camera(T, t)
    pos, z, k, p, tl = player_state(T, t)
    pos0 = player_state(T, t - 1 / FPS)[0]
    S_ = SC[k]; i = ORDER.index(k)
    c = Image.new("RGBA", (W, H), (10, 10, 14, 255))
    half = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0))
    for pl in CROWD["full"]: pl.draw(half, cam, 0.5)
    empt = _progress(i, p, EP.get("empty_scene"))
    if empt > 0:
        sp = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0))
        for pl in CROWD["sparse"]: pl.draw(sp, cam, 0.5)
        sp.putalpha(sp.getchannel("A").point(lambda v: int(v * empt)))
        half.alpha_composite(sp)
    c.alpha_composite(half.resize((W, H), Image.BILINEAR))
    FLOOR.draw(c, cam)
    draw_rope(c, cam, _progress(i, p, EP.get("rope_scene")))
    for pa in S_.get("paths", []):
        a_, b_ = pa.get("p", [0, 1])
        if p > a_: draw_path(c, cam, _polyline(pa["pts"]), col(pa.get("color"), YEL), u=min(1, (p - a_) / max(b_ - a_, 1e-3)))
    objs = [((cam.proj((0, 4, 10)) or (0, 0, 1e9))[2] + 0.1, "hoop", None)]
    for n in EP["players"]:
        q = cam.proj((*pos[n], 0))
        if q: objs.append((q[2], "pl", n))
    b = ball_state(pos, z, k, p)
    if b is not None:
        q = cam.proj(b)
        if q: objs.append((q[2] - 0.5, "ball", b))
    # traînée du ballon (tirs, passes)
    trail = []
    for j in range(1, 7):
        st = player_state(T, t - j * 0.035)
        if st[2] != k: break
        bb = ball_state(st[0], st[1], st[2], st[3])
        if bb is None: break
        trail.append(bb)
    if b is not None and trail and np.linalg.norm(trail[0] - b) > 0.35:
        d = ImageDraw.Draw(c)
        for j, bb in enumerate(trail):
            q = cam.proj(bb)
            if not q: continue
            r = max(3, cam.f * 0.62 / q[2]) * (1 - j * 0.12)
            d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=(255, 150, 60, int(120 * (1 - j / 7))))
    swish = max(0, 1 - abs(p - 0.25) / 0.25) if S_.get("swish") else 0
    rs = S_.get("rim_shake")
    focus, glows = S_.get("focus"), S_.get("glow", [])
    labels = S_.get("labels", True)
    for depth, kind, o in sorted(objs, key=lambda v: -v[0]):
        if kind == "hoop":
            shake = 0.35 * math.sin(tl * 60) * max(0, 1 - (p - rs[0]) / max(rs[1] - rs[0], 1e-3)) if (rs and rs[0] <= p < rs[1]) else 0.0
            draw_hoop(c, cam, swish, shake)
        elif kind == "ball": draw_ball(c, cam, o)
        else:
            P_ = EP["players"][o]
            show = P_.get("label") if (labels is True or (isinstance(labels, list) and o in labels)) else None
            dim = 0.45 if (focus and o not in focus) else 1.0
            glow = (0.6 + 0.4 * math.sin(t * 8)) if o in glows else 0.0
            v = np.linalg.norm(pos[o] - pos0[o]) * FPS
            run = t * 14 + sum(map(ord, o)) % 7 if v > 2.5 else None
            draw_player(c, cam, *pos[o], z[o], P_["team"], P_.get("num", ""), show, dim, glow, arms_up(k, p, o), run)
    for p_on, lab, w in S_.get("steps", []):
        if p >= p_on:
            q = cam.proj(w)
            if q: blit(c, _tag(lab, 34), q[0], q[1], scale=0.7 + 0.3 * ease_back(min(1, (p - p_on) * 8)))
    if S_.get("flash") and tl < 0.5:
        c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - tl / 0.5)))))
    if S_.get("confetti") and p > 0.4: _confetti(c, t)
    if S_.get("slowmo"):
        e = ease_out(min(1, tl / 0.4)); d = ImageDraw.Draw(c)
        d.rectangle([0, 0, W, 130 * e], fill=(0, 0, 0, 255)); d.rectangle([0, H - 130 * e, W, H], fill=(0, 0, 0, 255))
    if bare: return c
    c.alpha_composite(GRAD)
    title(c, k, tl)
    scoreboard(c, k)
    if S_.get("chip"): chip(c, S_["chip"])
    captions(c, t, groups)
    return c.convert("RGB")


def _confetti(c, t):
    d = ImageDraw.Draw(c); rng = np.random.default_rng(7)
    cols = [(255, 255, 255), TEAM["A"]["color"], RED, YEL]
    for i in range(140):
        x = (rng.random() * W + 40 * math.sin(t * 2 + i)) % W
        y = (rng.random() * H + t * (220 + 160 * rng.random())) % H
        a = t * 4 + i; w_ = 16 * abs(math.cos(a)) + 4
        d.rectangle([x, y, x + w_, y + 10], fill=cols[i % 4] + (255,))


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
        if i >= n or i < 0: return
        x = x[: n - i]; out[i:i + len(x)] += x * g

    # nappe de tension (tic-tac + basse) jusqu'à la scène au ralenti, puis silence ; accord sur la scène « chord »
    end_cue = next((c for c in ORDER if SC[c].get("slowmo")), ORDER[int(len(ORDER) * 0.66)])
    t_end = T.span[end_cue][0]
    tt = np.arange(n) / SR
    ramp = np.clip(tt / max(t_end, 1), 0, 1)
    drone = (np.sin(2 * np.pi * 55 * tt) + 0.5 * np.sin(2 * np.pi * 82.4 * tt) + 0.25 * np.sin(2 * np.pi * 110 * tt)) * (0.04 + 0.07 * ramp)
    out += (drone * (tt < t_end) * np.clip((t_end - tt) / 0.15, 0, 1)).astype(np.float32)
    click = _sine(2400, 0.03, 120); j = 0.0
    while j < t_end - 0.2:
        add(click, j, 0.05 + 0.08 * j / t_end); j += 0.5
    out += (_noise(T.total, 200, 5) * 0.035)[:n].astype(np.float32)
    for c in ORDER[1:]:
        add(whoosh(), max(0, T.span[c][0] - 0.12), 0.09)
    roar = _noise(3.5, 30, 9) * np.minimum(1, np.arange(int(3.5 * SR)) / (0.2 * SR)) * np.exp(-np.arange(int(3.5 * SR)) / SR * 0.8)
    for c in ORDER:
        a, b = T.span[c]
        for fx in SC[c].get("sfx", []):
            name, at = fx[0], (fx[1] if len(fx) > 1 else 0.0)
            t0 = a + (b - a) * at
            if name == "clang":
                x = _sine(220, 0.5, 9); add(x + 0.6 * _sine(330, 0.5, 12)[:len(x)], t0, 0.22)
            elif name == "heartbeat":
                for q in range(int((b - a) / 0.75)):
                    add(_sine(55, 0.22, 18), a + 0.1 + q * 0.75, 0.5); add(_sine(80, 0.18, 20), a + 0.1 + q * 0.75, 0.25)
            elif name == "swish":
                add(_noise(0.25, 6, 3) * np.exp(-np.arange(int(0.25 * SR)) / SR * 14), t0, 0.25)
            elif name == "roar":
                add(roar, t0, 0.2)
            elif name == "chord":
                L = int((T.total - t0) * SR)
                for f_ in (261.6, 329.6, 392.0, 523.3):
                    x = np.sin(2 * np.pi * f_ * np.arange(L) / SR)
                    env = np.clip(np.arange(L) / (0.6 * SR), 0, 1) * np.clip((L - np.arange(L)) / (1.0 * SR), 0, 1)
                    add(x * env, t0, 0.025)
    out = np.clip(out, -1, 1)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- miniature, programmation
def cover(T, groups, out):
    C_ = EP["cover"]
    a, b = T.span[C_["scene"]]
    c = frame(a + C_.get("p", 0.5) * (b - a), T, groups, bare=True)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for y in range(0, 900): d.line([0, y, W, y], fill=(0, 0, 0, int(225 * (1 - y / 900) ** 1.2)))
    c.alpha_composite(g)
    l1, l2 = C_["lines"]
    t1 = outlined(l1, "Black", 128, WHITE, 12); blit(c, t1, W / 2, 300, scale=min(1, 1020 / t1.width))
    big = outlined(l2, "Black", 168, YEL, 14); blit(c, big, W / 2, 470, scale=min(1, 1020 / big.width), rot=-3)
    tx = text_img(C_["band"], "Black", 54, (255, 255, 255))
    bb = Image.new("RGBA", (tx.width + 54, tx.height + 18), (0, 0, 0, 0))
    ImageDraw.Draw(bb).rounded_rectangle([0, 0, bb.width - 1, bb.height - 1], radius=16, fill=RED + (255,)); bb.alpha_composite(tx, (27, 9))
    blit(c, bb, W / 2, 660, rot=2, scale=min(1, 980 / bb.width))
    blit(c, _tag("L'ACTION QUI A TOUT CHANGÉ", 34), W / 2, 1760)
    c.convert("RGB").save(out, quality=92)


def schedule(video, cover_path, at):
    """File de publication (Instagram, YouTube, Facebook + brouillon TikTok) + aperçu Discord (❌ = annulation)."""
    from publish import queue
    from chiffre import discord_post
    names = ", ".join(EP.get("source_names", [])) or "—"
    msg = (f"**🎬 « L'action qui a tout changé » : {EP['yt_title']}** — publication automatique le {at} "
           f"(TikTok en brouillon + Instagram, YouTube, Facebook).\nMets ❌ sur ce message pour l'annuler. Sources : {names}")
    mid = None
    if os.environ.get("DISCORD_BOT_TOKEN"):
        light = os.path.splitext(video)[0] + "_apercu.mp4"
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", "scale=720:-2", "-c:v", "libx264", "-preset", "veryfast",
                            "-b:v", "1400k", "-maxrate", "1600k", "-bufsize", "3200k", "-c:a", "aac", "-b:a", "96k", light], check=True)
            mid = discord_post.post(light, msg[:1900], cover_path)
        except Exception as ex:
            print("Aperçu Discord impossible :", ex)
            try: discord_post.notify(msg[:1800])
            except Exception: pass
        finally:
            if os.path.exists(light): os.remove(light)
    tags = " ".join(EP["hashtags"]); cap = EP["caption"]
    queue.add(EP["file"], video, cover_path, f"{cap}\n\nAbonne-toi pour la prochaine action 🔔\n\n{tags}", f"{EP['yt_title']} #Shorts",
              f"{cap}\n\n#Shorts {tags}", at, mid, f"{cap}\n\n{tags}")
    print("Programmé :", EP["file"], at)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default="action/episodes/ray_allen_2013.json")
    ap.add_argument("--out", default="docs/proto"); ap.add_argument("--frames", default="")
    ap.add_argument("--queue-at", help="'AAAA-MM-JJ HH:MM' : programme la publication + aperçu Discord")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    load(a.episode); build()
    segs = [(s["cue"], s["voice"]) for s in EP["scenes"]]
    vw = os.path.join(a.out, "voix_action.wav")
    cues, total = tts.synth(segs, vw)
    words = words_from_last()
    if words:   # début/fin de chaque scène = 1er/dernier mot prononcé
        idx, fixed = 0, []
        for k, txt in segs:
            n = len([w for w in re.findall(r"\[[^\]]*\]|\S+", txt) if not w.startswith("[")])
            if idx + n > len(words): fixed = []; break
            fixed.append((k, words[idx][1], words[idx + n - 1][2])); idx += n
        if fixed: cues = fixed
    T = TL(cues, total)
    if not words:
        for k, s, e in cues:
            txt = re.sub(r"\[[^\]]*\]", "", dict(segs)[k]).split()
            for i, w_ in enumerate(txt): words.append((w_, s + (e - s) * i / len(txt), s + (e - s) * (i + 1) / len(txt)))
    groups = chunks(words)
    if a.frames:
        for spec in a.frames.split(","):
            if spec.startswith("k:"):
                _, k, f = spec.split(":"); s_, e_ = T.span[k]; t = s_ + (e_ - s_) * float(f)
            else: t = float(spec)
            frame(t, T, groups).save(os.path.join(a.out, f"f_{spec.replace(':', '_')}.jpg"), quality=85)
        cover(T, groups, os.path.join(a.out, "cover.jpg"))
        print("durée", round(T.total, 1)); return
    silent = os.path.join(a.out, "action_silent.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i in range(int(T.total * FPS)):
        p.stdin.write(frame(i / FPS, T, groups).tobytes())
    p.stdin.close(); p.wait()
    cov = os.path.join(a.out, EP["file"] + ".jpg"); cover(T, groups, cov)
    aud = os.path.join(a.out, "action_audio.wav"); mix(vw, T, aud)
    final = os.path.join(a.out, EP["file"] + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", aud, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-shortest", final], check=True)
    for f in (silent, aud, vw, vw.replace(".wav", ".mp3")):
        if os.path.exists(f): os.remove(f)
    print("Vidéo :", final, f"{T.total:.1f}s")
    if a.queue_at:
        schedule(final, cov, a.queue_at)


if __name__ == "__main__":
    main()
