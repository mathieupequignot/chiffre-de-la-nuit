"""Quiz « Qui est ce joueur ? » : parcours de franchises + années, compte à rebours, réponse en commentaire.
usage : python -m quiz.main [--player ID] [--no-post]"""
import argparse, datetime as dt, json, math, os, random, subprocess, sys, traceback, wave
from zoneinfo import ZoneInfo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from chiffre import tts, discord_post
from chiffre.render import (W, H, FPS, ACCENT, WHITE, GREY, font, text, text_img, blit, panel,
                            build_bg, bg_at, ease_out, ease_back)
from chiffre.teams import team, NICK

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
LEVELS = {"facile": ("FACILE", (52, 211, 120)), "moyen": ("MOYEN", ACCENT), "difficile": ("DIFFICILE", (226, 27, 77))}
CITY = {"LAL": "LOS ANGELES", "LAC": "LOS ANGELES"}
STEP, FINAL = 1.5, 6          # écart entre deux cartes ; secondes de compte à rebours après la dernière carte
CARD_TOP, CARD_BOTTOM, BAR_Y = 450, 1400, 1535
GAP = 46
LIVELY = {"stability": 0.25, "similarity_boost": 0.75, "style": 0.7, "use_speaker_boost": True}


# codes Basketball-Reference -> (ville, surnom, couleur, liseré) ; codes actuels -> couleurs de chiffre/teams.py
BREF = {"BRK": "BKN", "CHO": "CHA", "PHO": "PHX"}
HIST = {
    "SEA": ("SEATTLE", "SUPERSONICS", (0, 101, 58), (255, 194, 32)),
    "NJN": ("NEW JERSEY", "NETS", (0, 42, 96), (205, 16, 65)),
    "NOH": ("NEW ORLEANS", "HORNETS", (0, 119, 139), (40, 0, 113)),
    "NOK": ("NEW ORLEANS", "HORNETS", (0, 119, 139), (40, 0, 113)),
    "CHH": ("CHARLOTTE", "HORNETS", (0, 119, 139), (40, 0, 113)),
    "CHA": ("CHARLOTTE", "BOBCATS", (242, 101, 49), (0, 47, 95)),
    "VAN": ("VANCOUVER", "GRIZZLIES", (0, 178, 169), (228, 98, 40)),
    "WSB": ("WASHINGTON", "BULLETS", (0, 43, 92), (227, 24, 55)),
    "KCK": ("KANSAS CITY", "KINGS", (0, 45, 98), (200, 16, 46)),
    "SDC": ("SAN DIEGO", "CLIPPERS", (200, 16, 46), (29, 66, 148)),
}


def _one(code):
    if code in HIST:
        c, n, bg, st = HIST[code]; return dict(city=c, nick=n, bg=bg, stripe=st)
    code = BREF.get(code, code)
    d = team(code)
    return dict(city=CITY.get(code, d["name"]), nick=NICK.get(code, "").upper(), bg=d["bg"], stripe=d["stripe"])


def team_info(t):
    """t : code ou liste de codes d'une même franchise (ex. ["NJN", "BRK"])."""
    codes = t if isinstance(t, list) else [t]
    parts = [_one(c) for c in codes]
    info = dict(parts[-1])
    cities = list(dict.fromkeys(p["city"] for p in parts)); nicks = list(dict.fromkeys(p["nick"] for p in parts))
    info["city"] = " / ".join(cities); info["nick"] = " / ".join(nicks)
    return info


# ---------------- format v2 : le jeu démarre à la 1re seconde, accroche variée
V2 = os.environ.get("QUIZ_FORMAT", "v2") == "v2"
HOOKS = [
    ("90 % des fans se trompent sur celui-là…", "90 % DES FANS SE TROMPENT"),
    ("Si tu trouves celui-là, t'es un vrai fan de NBA.", "SI TU TROUVES, T'ES UN VRAI"),
    ("Personne ne le trouve du premier coup…", "PERSONNE NE TROUVE DU 1ER COUP"),
    ("Trouve-le avant la fin du chrono !", "TROUVE-LE AVANT LA FIN DU CHRONO"),
    ("Seuls les vrais fans vont trouver ce joueur !", "SEULS LES VRAIS FANS TROUVENT"),
    ("Celui-là, tu le connais forcément…", "TU LE CONNAIS FORCÉMENT"),
]


# ---------------- timeline
class TL:
    def __init__(self, P, intro_cues, intro_len, outro_len):
        self.cues = {c: (a, b) for c, a, b in intro_cues}
        self.I = 0.0 if V2 else intro_len + 0.25
        self.n = len(P["teams"])
        self.Tb = 0.15 if V2 else self.I + 0.3       # début du chrono + 1re carte
        self.Dur = math.ceil(self.n * STEP) + FINAL   # durée totale du chrono (secondes entières)
        self.Te = self.Tb + self.Dur                  # fin du chrono
        self.To = self.Te + 0.35                      # début de la voix de fin
        self.total = self.To + outro_len + 0.9

    def card_t(self, i):
        if V2 and i == 0:
            return -0.5  # la 1re franchise est déjà à l'écran dès la 1re image
        return self.Tb + i * STEP


# ---------------- image
def qmark(size, color):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, size - 1, size - 1], fill=(20, 20, 26, 255), outline=color + (255,), width=max(6, size // 40))
    ti = text_img("?", "Black", int(size * 0.62), color)
    im.alpha_composite(ti, ((size - ti.width) // 2, int(size * 0.47 - ti.height / 2)))
    return im


def level_badge(c, P, x, y, alpha=1.0, scale=1.0, s=46):
    lab, col = LEVELS[P["level"]]
    ti = text_img(f"NIVEAU  {lab}", "Black", s, (12, 12, 16), spacing=4)
    im = Image.new("RGBA", (ti.width + 70, ti.height + 34), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=col + (255,))
    im.alpha_composite(ti, (35, 17))
    blit(c, im, x, y, alpha=alpha, scale=scale)


def _lum(c): return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _vivid(c):
    """Couleur d'équipe éclaircie et saturée (même teinte) pour un rendu vif."""
    import colorsys
    h, sat, v = colorsys.rgb_to_hsv(*[x / 255 for x in c])
    if sat > 0.25:
        sat, v = max(sat, 0.75), max(v, 0.78)
    r, g, b = colorsys.hsv_to_rgb(h, sat, v)
    return int(r * 255), int(g * 255), int(b * 255)


def _gap(n):
    return GAP if n <= 6 else 34


# ---------------- silhouette (indice visuel) : photo officielle NBA -> ombre noire
NBA_IDS = json.load(open(os.path.join(HERE, "nba_ids.json")))
SIL = None          # image de la silhouette du joueur en cours (None = ancienne mise en page)
SIL_Y, SIL_H = 655, 430


def silhouette(P, size_h=430, src=None, qmark=True):
    """Silhouette noire cerclée de jaune à partir de la photo officielle (fond transparent)."""
    import io, requests
    try:
        if src is None:
            pid = NBA_IDS.get(P["id"]) or P["id"]  # identifiant Basketball-Reference connu, ou identifiant NBA direct
            r = requests.get(f"https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png", timeout=20)
            r.raise_for_status(); src = Image.open(io.BytesIO(r.content))
        a = src.convert("RGBA").getchannel("A").point(lambda v: 255 if v > 110 else 0)
        box = a.getbbox()
        if not box or (box[2] - box[0]) * (box[3] - box[1]) < 0.05 * a.width * a.height:
            return None
        a = a.crop(box)
        sc = size_h / a.height; a = a.resize((max(1, int(a.width * sc)), size_h), Image.LANCZOS)
        pad = 40
        A = Image.new("L", (a.width + 2 * pad, a.height + pad), 0); A.paste(a, (pad, pad))
        edge = A.filter(ImageFilter.MaxFilter(13))
        glow = edge.filter(ImageFilter.GaussianBlur(14))
        im = Image.new("RGBA", A.size, (255, 196, 0, 0))
        im.putalpha(glow.point(lambda v: int(v * 0.9)))
        ring = Image.new("RGBA", A.size, (255, 196, 0, 255)); ring.putalpha(edge)
        im.alpha_composite(ring)
        body = Image.new("RGBA", A.size, (14, 10, 30, 255)); body.putalpha(A)
        im.alpha_composite(body)
        q = text_img("?", "Black", int(size_h * 0.42), (255, 196, 0))
        if qmark: im.alpha_composite(q, ((im.width - q.width) // 2, int(pad + a.height * 0.42 - q.height / 2)))
        return im
    except Exception as e:  # pas de photo : on garde la mise en page classique
        print("silhouette indisponible :", e)
        return None


def _geom(n):
    gap = _gap(n) if SIL is None else min(_gap(n), 30)
    ct = CARD_TOP if SIL is None else SIL_Y + SIL_H / 2 + 50
    h = min(132, (CARD_BOTTOM - ct - gap * (n - 1)) / n)
    tot = n * h + (n - 1) * gap
    top = ct + (CARD_BOTTOM - ct - tot) / 2
    return h, top


def arrow(c, i, t0, t, n, dim=1.0):
    """Flèche entre la carte i-1 et la carte i (apparaît juste avant la carte i)."""
    p = (t - (t0 - 0.35)) / 0.3
    if p <= 0: return
    a = min(1, p) * dim
    h, top = _geom(n)
    g = _gap(n) if SIL is None else min(_gap(n), 30); yc = top + i * (h + g) - g / 2 + (1 - ease_out(p)) * -18
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for dx, col in ((0, (255, 210, 60)),):
        d.line([(W / 2 - 26, yc - 12), (W / 2, yc + 12), (W / 2 + 26, yc - 12)], fill=col + (int(255 * a),), width=10, joint="curve")
    c.alpha_composite(lay)


def card(c, i, info, years, t0, t, n, dim=1.0):
    p = (t - t0) / 0.4
    if p <= 0: return
    a = min(1, p * 1.6) * dim
    h, top = _geom(n)
    y0 = top + i * (h + (_gap(n) if SIL is None else min(_gap(n), 30)))
    sc = 0.55 + 0.45 * ease_back(min(1, p))
    x0, x1 = 70, 1010 - 70
    bg = _vivid(tuple(info["bg"])); st = tuple(info["stripe"])
    fg = (15, 15, 20) if _lum(bg) > 170 else WHITE
    cw, ch = int(x1 - x0), int(h)
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    grad = Image.new("RGBA", (cw, ch))
    gd = ImageDraw.Draw(grad)
    dark = tuple(int(v * 0.62) for v in bg)
    for x in range(cw):
        f = x / cw
        gd.line([(x, 0), (x, ch)], fill=tuple(int(bg[k] * (1 - f) + dark[k] * f) for k in range(3)) + (255,))
    gd.rectangle([0, ch - 12, cw, ch], fill=st + (255,))
    mask = Image.new("L", (cw, ch), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw - 1, ch - 1], radius=28, fill=255)
    im.paste(grad, (0, 0), mask)
    # numéro d'étape
    d = ImageDraw.Draw(im)
    d.ellipse([22, ch / 2 - 30, 82, ch / 2 + 30], fill=(255, 255, 255, 235))
    num = text_img(str(i + 1), "Black", 36, (20, 20, 26))
    im.alpha_composite(num, (52 - num.width // 2, int(ch / 2 - num.height / 2)))
    city = text_img(info["city"], "Black", int(h * 0.34), fg)
    if city.width > 470: city = city.resize((470, int(city.height * 470 / city.width)), Image.LANCZOS)
    im.alpha_composite(city, (104, int(ch * 0.40 - city.height / 2)))
    nick = text_img(info["nick"], "ExtraBold", int(h * 0.2), fg, spacing=3)
    nick.putalpha(nick.getchannel("A").point(lambda v: int(v * 0.8)))
    im.alpha_composite(nick, (108, int(ch * 0.72 - nick.height / 2)))
    yr = text_img(years, "Black", int(h * 0.27), (20, 20, 26))
    pw, ph = yr.width + 40, yr.height + 14
    pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=ph // 2, fill=(255, 255, 255, 255))
    pill.alpha_composite(yr, (20, 7))
    im.alpha_composite(pill, (cw - pw - 26, int(ch / 2 - ph / 2)))
    # flash blanc à l'arrivée
    if 0.6 < p < 1.6:
        fl = Image.new("RGBA", (cw, ch), (255, 255, 255, 0))
        fl.putalpha(mask.point(lambda v: int(v * 0.55 * (1 - (p - 0.6)))))
        im.alpha_composite(fl)
    blit(c, im, (x0 + x1) / 2, y0 + h / 2, scale=sc, alpha=a)


def vivid_bg():
    base = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(base)
    top, bot = (60, 18, 140), (14, 8, 40)
    for y in range(H):
        f = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[k] * (1 - f) + bot[k] * f) for k in range(3)) + (255,))
    glow = Image.new("RGBA", (W + 600, H + 600), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse([0, 0, 1100, 1000], fill=(255, 40, 160, 120))
    g.ellipse([600, 1300, 1680, 2500], fill=(255, 130, 0, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(190))
    random.seed(3); grains = []
    for _ in range(4):
        nz = Image.effect_noise((W // 2, H // 2), 60).resize((W, H)).convert("L")
        gr = Image.new("RGBA", (W, H), (255, 255, 255, 0)); gr.putalpha(nz.point(lambda v: max(0, v - 150) // 7)); grains.append(gr)
    return base, glow, Image.new("RGBA", (W, H), (0, 0, 0, 0)), grains


def timer(c, T, t):
    if t < T.Tb - 0.2: return
    a = min(1, (t - T.Tb + 0.2) / 0.3) * (1 - min(1, max(0, (t - T.Te - 0.4) / 0.3)))
    if a <= 0: return
    frac = max(0.0, min(1.0, 1 - (t - T.Tb) / T.Dur))
    left = min(T.Dur, max(0, math.ceil(T.Te - t)))
    last = left <= 3 and t < T.Te
    f = 1 - frac
    col = (int(40 + 215 * min(1, f * 2)), int(230 - 180 * max(0, f * 2 - 1)), 70) if not last else (255, 40, 80)
    x0, x1, h = 230, 900, 34
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0, BAR_Y - h / 2, x1, BAR_Y + h / 2], radius=h // 2, fill=(255, 255, 255, int(40 * a)))
    if frac > 0:
        d.rounded_rectangle([x0, BAR_Y - h / 2, x0 + max(h, (x1 - x0) * frac), BAR_Y + h / 2], radius=h // 2, fill=col + (int(255 * a),))
    c.alpha_composite(lay)
    ph = (t - T.Tb) % 1.0
    pulse = 1 + (0.25 if last else 0.1) * max(0, 1 - ph / 0.25)
    blit(c, qmark_cache(150, col, str(left)), 135, BAR_Y, alpha=a, scale=pulse)


_qc = {}
def qmark_cache(size, col, label):
    k = (size, col, label)
    if k not in _qc:
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.ellipse([0, 0, size - 1, size - 1], fill=(20, 20, 26, 255), outline=col + (255,), width=8)
        ti = text_img(label, "Black", int(size * 0.5), WHITE)
        im.alpha_composite(ti, ((size - ti.width) // 2, int(size * 0.47 - ti.height / 2)))
        _qc[k] = im
    return _qc[k]


QM = None
def frame(t, P, T, infos, parts):
    global QM
    QM = QM or qmark(520, (255, 196, 0))
    im = bg_at(t, parts)
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # --- intro (gros titre + ? + niveau), puis le titre remonte en en-tête
    if V2:
        # en-tête fixe dès la 1re image : accroche + question + niveau
        pop = 0.85 + 0.15 * ease_back(min(1, t / 0.3))
        text(c, T.hook_txt, "Black", 62, WHITE, W / 2, 158, scale=pop, maxw=940)
        text(c, "QUI EST CE JOUEUR ?", "Black", 96, (255, 196, 0), W / 2, 252, scale=pop, maxw=960)
        level_badge(c, P, W / 2, 352, scale=0.8 * pop, s=46)
    mv = 1.0 if V2 else (ease_out((t - T.I) / 0.4) if t > T.I else 0.0)
    ia = 0.0 if V2 else min(1, t / 0.25)
    y_t1 = 560 + (170 - 560) * mv; y_t2 = 690 + (262 - 690) * mv
    s_t = 1 - 0.45 * mv
    pop = ease_back(min(1, t / 0.45))
    text(c, "QUI EST", "Black", 150, WHITE, W / 2, y_t1, alpha=ia, scale=pop * s_t)
    text(c, "CE JOUEUR ?", "Black", 150, (255, 196, 0), W / 2, y_t2, alpha=ia, scale=pop * s_t, maxw=960)
    blit(c, QM, W / 2, 1120 + 300 * mv, alpha=ia * (1 - mv), scale=0.9 + 0.1 * ease_back(min(1, t / 0.6)))
    lt = T.cues.get("L", (T.I - 0.8, 0))[0]
    if not V2 and t >= lt:
        q = (t - lt) / 0.35
        bx_y = 1500 + (362 - 1500) * mv
        level_badge(c, P, W / 2, bx_y, alpha=min(1, q), scale=(0.6 + 0.4 * ease_back(min(1, q))) * (1 - 0.3 * mv))
    # --- silhouette du joueur (indice visuel), visible dès la 1re image
    if SIL is not None:
        da = 1 - 0.7 * ease_out((t - T.Te - 0.3) / 0.4) if t > T.Te + 0.3 else 1.0
        blit(c, SIL, W / 2, SIL_Y, alpha=da, scale=(0.92 + 0.08 * ease_back(min(1, t / 0.35))) * (1 + 0.012 * math.sin(t * 2.4)))
    # --- cartes
    dim = 1 - 0.7 * ease_out((t - T.Te - 0.3) / 0.4) if t > T.Te + 0.3 else 1.0
    for i, (info, yrs) in enumerate(infos):
        if i: arrow(c, i, T.card_t(i), t, len(infos), dim)
        card(c, i, info, yrs, T.card_t(i), t, len(infos), dim)
    timer(c, T, t)
    # --- fin : appel au commentaire
    if t > T.Te + 0.3:
        q = (t - T.Te - 0.3) / 0.45
        a = min(1, q); sc = 0.7 + 0.3 * ease_back(min(1, q))
        panel(c, [90, 620, 990, 1290], (40, 14, 90, 245), alpha=a, r=40, outline=(255, 196, 0, 255))
        blit(c, qmark(300, (255, 196, 0)), W / 2, 820, alpha=a, scale=sc)
        text(c, "ÉCRIS TA RÉPONSE", "Black", 76, WHITE, W / 2, 1050, alpha=a, scale=sc, maxw=820)
        text(c, "EN COMMENTAIRE", "Black", 76, (255, 196, 0), W / 2, 1140, alpha=a, scale=sc, maxw=820)
        by = 1220 + 14 * math.sin((t - T.Te) * 7)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).polygon([(W / 2 - 34, by), (W / 2 + 34, by), (W / 2, by + 40)], fill=WHITE + (int(255 * a),))
        c.alpha_composite(lay)
    im.alpha_composite(c)
    return im.convert("RGB")


# ---------------- son
def _read(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return x.reshape(-1, w.getnchannels()).mean(1)


def _tick(f, d=0.09):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 70) + 0.3 * np.random.default_rng(1).standard_normal(len(t)) * np.exp(-t * 400))


def _pop(d=0.18):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(420 + 700 * (1 - np.exp(-t * 40))) / SR) * np.exp(-t * 20)


def _buzz(d=0.7):
    t = np.arange(int(d * SR)) / SR
    return np.tanh(2.5 * np.sign(np.sin(2 * np.pi * 110 * t)) * 0.4 + np.sin(2 * np.pi * 55 * t)) * np.exp(-t * 4) * 0.6


def mix(T, voice1, voice2, out_wav):
    n = int((T.total + 0.1) * SR); buf = np.zeros(n, np.float32)
    def add(x, at, g):
        i = int(at * SR); x = x[: max(0, n - i)]; buf[i:i + len(x)] += g * x
    add(_read(voice1), 0.0, 1.0); add(_read(voice2), T.To, 1.0)
    lt = T.cues.get("L", (None,))[0]
    if lt is not None and not V2: add(_pop(), lt, 0.16)
    for i in range(T.n): add(_pop(), max(0.0, T.card_t(i)), 0.11)
    for k in range(T.Dur):
        last = T.Dur - k <= 3
        add(_tick(2600 if last else (1900 if k % 2 == 0 else 1400)), T.Tb + k, 0.15 if last else 0.09)
    add(_buzz(), T.Te, 0.16)
    buf = np.tanh(buf * 1.1) * 0.95
    st = (np.stack([buf, buf], 1) * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())


# ---------------- voix (en cache dans le dépôt : mêmes phrases chaque jour)
VOICE_DIR = os.path.join(HERE, "voice")


def voice(key, segs, outdir):
    os.makedirs(VOICE_DIR, exist_ok=True)
    key = f"{key}_{os.environ.get('ELEVENLABS_VOICE_ID', 'x').strip()[:6]}"  # une voix différente = un autre cache
    wav, meta = os.path.join(VOICE_DIR, key + ".wav"), os.path.join(VOICE_DIR, key + ".json")
    if os.path.exists(wav) and os.path.exists(meta):
        m = json.load(open(meta)); return wav, [tuple(c) for c in m["cues"]], m["total"]
    tmp = os.path.join(outdir, key + "_raw.wav")
    cues, total = tts.synth(segs, tmp, LIVELY)
    if not os.environ.get("ELEVENLABS_API_KEY"):
        return tmp, cues, total  # mode test : on ne met pas de silence en cache
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "1", wav], check=True)
    json.dump({"cues": cues, "total": total}, open(meta, "w"))
    return wav, cues, total


# ---------------- miniature
def make_cover(P, out):
    lab, col = LEVELS[P["level"]]
    base, glow, _, grains = vivid_bg()
    im = base.copy(); im.alpha_composite(glow.crop((300, 300, 300 + W, 300 + H))); im.alpha_composite(grains[0])
    text(im, "QUI EST", "Black", 150, WHITE, W / 2, 520)
    text(im, "CE JOUEUR ?", "Black", 150, (255, 196, 0), W / 2, 670, maxw=960)
    if SIL is not None:
        f = 520 / SIL.height
        big = SIL.resize((int(SIL.width * f), int(SIL.height * f)), Image.LANCZOS)
        blit(im, big, W / 2, 1010)
    else:
        blit(im, qmark(470, (255, 196, 0)), W / 2, 1010)
    level_badge(im, P, W / 2, 1330, s=58)
    n = n_franchises(P)
    text(im, f"{n} FRANCHISE" + ("S" if n > 1 else ""), "Black", 64, WHITE, W / 2, 1460, spacing=6)
    text(im, "NBA DAILY NEWS", "ExtraBold", 36, (200, 190, 230), W / 2, 1790, spacing=8)
    im.convert("RGB").save(out, quality=92)
    return out


# ---------------- légendes
TIMES = {"facile": "12h30", "moyen": "18h", "difficile": "21h"}


def n_franchises(P):
    return len({team_info(t)["nick"].split(" / ")[-1] for t, _ in P["teams"]})


def captions(P):
    lab = LEVELS[P["level"]][0].lower(); n = n_franchises(P)
    fr = f"{n} franchise" + ("s" if n > 1 else "")
    hook = random.Random(P["id"]).choice([
        "Tu le reconnais rien qu'à sa silhouette ? 👀",
        "Si tu ne trouves pas celui-là, rends ton maillot 😅",
        "Seuls les vrais fans trouvent ce joueur 👀",
        "Silhouette + équipes… tu l'as en combien de secondes ? ⏱️",
    ]) if SIL is not None else "Seuls les vrais fans trouvent ce joueur 👀"
    base = f"{hook} Niveau {lab} · {fr}. Ta réponse en commentaire 👇"
    tk = ["#NBA", "#quizNBA", "#basketball", "#NBAFrance", "#devinelejoueur"]
    ig = ["#NBA", "#quizNBA", "#basketball", "#basket", "#NBAFrance", "#NBADailyNews", "#devinelejoueur", "#quiz", "#nbatrivia", "#sport"]
    return dict(
        tiktok=f"{base}\n\n{' '.join(tk)}",
        instagram=f"{base}\n\nAbonne-toi pour les quiz de chaque jour 🔔\n\n{' '.join(ig)}",
        youtube_title=f"Qui est ce joueur NBA ? 🤔 Niveau {lab} ({fr}) #Shorts",
        youtube=f"{base}\n\n#Shorts #NBA #quizNBA",
    )


def short_message(P):
    lab = LEVELS[P["level"]][0]
    return (f"**🧩 Quiz {lab.lower()}** — 🔒 réponse : ||{P['name']}||\n"
            f"📸 Instagram + ▶️ YouTube : publication automatique à {TIMES[P['level']]}.\n"
            f"🎵 TikTok : la vidéo arrive dans tes brouillons ; description à copier dans le message suivant 👇")


def message(P):
    lab = LEVELS[P["level"]][0]; c = captions(P)
    return (f"**🧩 Quiz {lab.lower()} — à poster vers {TIMES[P['level']]}**\n"
            f"🔒 Réponse (pour toi) : ||{P['name']}||\n\n"
            f"🎵 **TikTok** :\n```{c['tiktok']}```\n"
            f"📸 **Instagram** :\n```{c['instagram']}```\n"
            f"🖼️ Miniature jointe : « Modifier la couverture » → Importer.\n\n"
            f"▶️ **YouTube Shorts** — titre :\n```{c['youtube_title']}```\ndescription :\n```{c['youtube']}```")


# ---------------- programme
def render_quiz(P, outdir, sil_src=None):
    global SIL
    os.makedirs(outdir, exist_ok=True)
    global SIL_H, SIL_Y
    n = len(P["teams"])
    SIL_H = 430 if n <= 2 else (370 if n == 3 else 300)
    SIL_Y = 410 + (SIL_H + 40) / 2
    SIL = silhouette(P, SIL_H, src=sil_src) if os.environ.get("QUIZ_SILHOUETTE", "1") == "1" else None
    lab = LEVELS[P["level"]][0].lower()
    if V2:
        k = random.Random(P["id"] + os.environ.get("QUIZ_DAY", "")).randrange(len(HOOKS))
        hook_voice, hook_txt = HOOKS[k]
        v1, cues1, len1 = voice(f"v3_hook{k}_{P['level']}", [("H", "[excited] " + hook_voice), ("L", f"Niveau {lab} !")], outdir)
    else:
        hook_txt = ""
        v1, cues1, len1 = voice(f"intro_{P['level']}", [("H", "Attention… seuls les VRAIS fans vont trouver ce joueur !"), ("L", f"Niveau : {lab} !")], outdir)
    v2, _, len2 = voice("v3_outro", [("E", "[excited] Alors… tu l'as trouvé ?! Balance ta réponse en commentaire !")], outdir)
    T = TL(P, cues1, len1, len2); T.hook_txt = hook_txt
    infos = [(team_info(tm), yrs) for tm, yrs in P["teams"]]
    parts = vivid_bg()
    silent = os.path.join(outdir, f"silent_{P['id']}.mp4")
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-maxrate", "1500k", "-bufsize", "3M",
                           "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i in range(int(T.total * FPS)):
        pr.stdin.write(frame(i / FPS, P, T, infos, parts).tobytes())
    pr.stdin.close(); pr.wait()
    audio = os.path.join(outdir, f"mix_{P['id']}.wav")
    mix(T, v1, v2, audio)
    final = os.path.join(outdir, f"quiz_{P['level']}_{P['id']}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
    cover = make_cover(P, os.path.join(outdir, f"miniature_{P['level']}_{P['id']}.jpg"))
    return final, cover


USED = os.path.join(HERE, "used.json")


def daily(day, post=True, outdir="out_quiz"):
    """Quiz du jour (par défaut 1 seul, niveau facile — QUIZ_LEVELS pour en faire plus), jamais deux fois le même joueur."""
    players = json.load(open(os.path.join(HERE, "players.json"), encoding="utf-8"))
    used = json.load(open(USED)) if os.path.exists(USED) else []
    rnd = random.Random(day)
    today = [u for u in used if u["date"] == day]
    for lvl in os.environ.get("QUIZ_LEVELS", "facile").split(","):
        if any(u["level"] == lvl for u in today):
            continue  # déjà fait aujourd'hui (relance)
        done = {u["id"] for u in used}
        pool = [p for p in players if p["level"] == lvl and p["id"] not in done]
        if not pool:  # liste épuisée : on repart des plus anciens
            order = [u["id"] for u in used if u["level"] == lvl]
            pool = [p for p in players if p["level"] == lvl and p["id"] == order[0]] if order else [p for p in players if p["level"] == lvl]
            used = [u for u in used if not (u["level"] == lvl and u["id"] == pool[0]["id"])]
        P = rnd.choice(pool)
        video, cover = render_quiz(P, outdir)
        print("Quiz", lvl, ":", P["name"], video)
        if post and os.environ.get("DISCORD_BOT_TOKEN"):
            auto = os.environ.get("AUTO_PUBLISH") == "1"
            mid = discord_post.post(video, short_message(P) if auto else message(P), cover,
                                    captions(P)["tiktok"] if auto else None)
            if auto:
                from publish import queue
                c = captions(P)
                queue.add(f"quiz_{day}_{lvl}", video, cover, c["instagram"], c["youtube_title"], c["youtube"],
                          {"facile": "12:30", "moyen": "18:00", "difficile": "21:00"}[lvl], mid)
        used.append({"date": day, "level": lvl, "id": P["id"]})
        json.dump(used, open(USED, "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--player", help="un seul quiz pour ce joueur (test), sans toucher à l'historique")
    ap.add_argument("--date", help="jour AAAA-MM-JJ (heure de Paris), vide = aujourd'hui")
    ap.add_argument("--no-post", action="store_true")
    ap.add_argument("--queue-at", help="avec --player : met la vidéo en file de publication auto à HH:MM (Paris) au lieu de l'envoyer sur Discord")
    a = ap.parse_args()
    try:
        if a.player:
            P = next(p for p in json.load(open(os.path.join(HERE, "players.json"), encoding="utf-8")) if a.player in (p["id"], p["name"]))
            v, c = render_quiz(P, "out_quiz")
            if a.queue_at:
                from publish import queue
                cap = captions(P); day = dt.datetime.now(ZoneInfo("Europe/Paris")).date().isoformat()
                queue.add(f"quiz_{day}_{P['level']}", v, c, cap["instagram"], cap["youtube_title"], cap["youtube"], a.queue_at)
                print("En file de publication :", P["name"], a.queue_at)
            elif not a.no_post and os.environ.get("DISCORD_BOT_TOKEN"):
                discord_post.post(v, message(P), c)
        else:
            day = a.date or dt.datetime.now(ZoneInfo("Europe/Paris")).date().isoformat()
            daily(day, not a.no_post)
    except Exception:
        err = traceback.format_exc(); print(err)
        discord_post.notify(f"⚠️ Les quiz n'ont pas pu être générés.\n```{err[-1500:]}```")
        sys.exit(1)
