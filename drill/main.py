"""Vidéo « exercice de la semaine » (Playground Lab) : un drill réel tiré d'un programme, puis CTA « programme en bio ».
Aucune publication : la vidéo est seulement rendue (aperçu à valider par Mathieu).
usage : python -m drill.main --out docs/proto [--drill pound]"""
import argparse, math, os, re, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw

from chiffre import tts
from chiffre.render import W, H, FPS, ACCENT, WHITE, text, blit, panel, build_bg, bg_at, ease_out, ease_back
from top10.main import outlined, chunks, words_from_last, captions, emoji, YEL, SILVER

SR = 48000
CYAN = (41, 224, 255)
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

DRILLS = {
    "pound": dict(
        file="drill_pound_dribble", program="DRIBBLE 30", mock="dribble30.png", header="POUND DRIBBLE · 3 HAUTEURS",
        hook=("TA MAIN FAIBLE", "TE LÂCHE ?"),
        segs=[
            ("H", "[excited] Ta main faible te lâche dès qu'on te met la pression ? Fais ce drill."),
            ("D1", "Pound dribble, trois hauteurs. Dix dribbles à hauteur de cheville…"),
            ("D2", "dix à hauteur de genou…"),
            ("D3", "et dix à hauteur de hanche."),
            ("K1", "Le ballon doit claquer au sol : tu le pousses avec les doigts, pas avec la paume."),
            ("K2", "Et tu commences toujours par ta main faible."),
            ("X", "Trop facile ? Fais-le les yeux fermés, cinq secondes à chaque hauteur."),
            ("S", "Enregistre la vidéo pour ta prochaine séance."),
            ("C", "[excited] Ce drill, c'est le jour un de Dribble trente : trente jours pour devenir shifty. Le programme complet est en bio."),
        ]),
}
TAG = {"DRIBBLE 30": "30 JOURS POUR DEVENIR SHIFTY", "SHOOT 30": "30 JOURS POUR DEVENIR UN SHOOTER FIABLE"}
VOICE_TAG = {"DRIBBLE 30": ("Dribble trente", "trente jours pour devenir shifty"),
             "SHOOT 30": ("Shoot trente", "trente jours pour devenir un shooter fiable")}
DRILLS["pound"]["id"] = "pound"
DRILLS["pound"]["caption"] = ("Ta main faible te lâche sous pression ? 🏀 Pound dribble 3 hauteurs : 10 à la cheville, 10 au genou, "
                              "10 à la hanche. Commence par ta main faible.")
import json as _json
for _d in _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "drills.json"), encoding="utf-8")):
    name, tag = VOICE_TAG[_d["program"]]
    _d["segs"] = [tuple(x) for x in _d["segs"]] + [
        ("SV", "Enregistre la vidéo pour ta prochaine séance."),
        ("C", f"[excited] Ce drill est dans {name} : {tag}. Le programme complet est en bio.")]
    _d["file"] = "drill_" + _d["id"].replace("-", "_")
    _d["mock"] = "dribble30.png" if _d["program"] == "DRIBBLE 30" else "shoot30.png"
    _d["diagram"] = ("dribble_" if _d["program"] == "DRIBBLE 30" else "shoot_") + _d["code"] + ".png"
    _d["hook"] = tuple(_d["hook"])
    DRILLS[_d["id"]] = _d
D = DRILLS["pound"]
LEVELS = {"D1": ("CHEVILLE", 1240), "D2": ("GENOU", 1070), "D3": ("HANCHE", 880)}
FLOOR = 1330


class TL:
    def __init__(self, cues, total):
        self.c = {k: (a, b) for k, a, b in cues}
        self.total = total + 1.6
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
        return "C", t, 1


# ---------------------------------------------------------------- dessin
def ball_img(r):
    im = Image.new("RGBA", (2 * r + 8, 2 * r + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([4, 4, 2 * r + 4, 2 * r + 4], fill=(255, 107, 26, 255), outline=(20, 12, 8, 255), width=max(2, r // 14))
    lw = max(2, r // 16); c = r + 4
    d.line([4, c, 2 * r + 4, c], fill=(20, 12, 8, 255), width=lw)
    d.line([c, 4, c, 2 * r + 4], fill=(20, 12, 8, 255), width=lw)
    d.arc([4 - r * 0.55, 4, 4 + r * 0.95, 2 * r + 4], -62, 62, fill=(20, 12, 8, 255), width=lw)
    d.arc([2 * r + 4 - r * 0.95, 4, 2 * r + 4 + r * 0.55, 2 * r + 4], 118, 242, fill=(20, 12, 8, 255), width=lw)
    return im


BALL = ball_img(70)


def bounce_y(t, top, period):
    """Position du ballon : rebond entre top et le sol (FLOOR)."""
    ph = (t % period) / period
    h = 1 - (2 * ph - 1) ** 2          # 0 au sol, 1 en haut
    return FLOOR - 70 - (FLOOR - 70 - top) * h, ph


def squash(y):
    return 0.86 if y > FLOOR - 82 else 1.0


def glow_text(c, txt, size, col, x, y, alpha=1, scale=1):
    im = outlined(txt, "Black", size, col, 10)
    blit(c, im, x, y, alpha=alpha, scale=scale * min(1, 980 / im.width))


def header(c, p):
    a = min(1, p / 0.3)
    panel(c, [90, 120, 990, 210], (10, 14, 26, 220), a, r=45, outline=CYAN + (160,))
    text(c, "DRILL DE LA SEMAINE", "Black", 34, CYAN, W / 2, 148, alpha=a)
    text(c, D["header"], "Black", 40, WHITE, W / 2, 188, alpha=a, maxw=820)


def scene_levels(c, k, t, p):
    cur = LEVELS[k][1]
    for kk, (lab, y) in LEVELS.items():
        done = list(LEVELS).index(kk) < list(LEVELS).index(k)
        on = kk == k
        col = ACCENT if on else ((52, 211, 120) if done else (120, 126, 140))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for x in range(150, 930, 26):
            d.line([x, y, x + 13, y], fill=col + (230 if on else 120,), width=4 if on else 3)
        c.alpha_composite(lay)
        text(c, ("✓ " if done else "") + lab, "Black", 54 if on else 42, col, 160, y - 38, anchor="lm", alpha=1)
    # sol
    panel(c, [110, FLOOR, 970, FLOOR + 8], (255, 255, 255, 90), 1, r=4)
    # ballon : plus c'est bas, plus c'est rapide
    period = {"D1": 0.26, "D2": 0.36, "D3": 0.48}[k]
    y, ph = bounce_y(t, cur, period)
    s = squash(y)
    blit(c, BALL, 780, y, scale=1.15)
    # compteur 1 → 10
    beat = 1 + 0.06 * max(0.0, 1 - ph * 4)          # petit « pop » à chaque rebond
    glow_text(c, "10 ×", 210, YEL, W / 2, 545, scale=beat)
    text(c, "MAIN FAIBLE D'ABORD", "Black", 40, CYAN, W / 2, 700, alpha=0.9)


def card(c, l1, l2, p, col=ACCENT, y=760):
    a = min(1, p / 0.25); z = 0.9 + 0.1 * ease_back(min(1, p / 0.35))
    panel(c, [90, y - 170, 990, y + 170], (12, 16, 30, 235), a, r=40, outline=col + (200,))
    glow_text(c, l1, 92, WHITE, W / 2, y - 55, alpha=a, scale=z)
    glow_text(c, l2, 92, col, W / 2, y + 60, alpha=a, scale=z)


def mini_bounce(c, t, x=W / 2, top=1000, period=0.3):
    y, _ = bounce_y(t, top, period)
    blit(c, BALL, x, y, scale=0.8)
    panel(c, [x - 160, FLOOR, x + 160, FLOOR + 8], (255, 255, 255, 80), 1, r=4)


MOCK = None
DIAG = None


def diagram_panel(c, p):
    global DIAG
    if DIAG is None:
        im = Image.open(os.path.join(ASSETS, D["diagram"])).convert("RGBA")
        im = im.resize((900, int(900 * im.height / im.width)), Image.LANCZOS)
        m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=40, fill=255)
        im.putalpha(m); DIAG = im
    e = ease_out(min(1, p / 0.4))
    blit(c, DIAG, W / 2, 560, alpha=e)
    text(c, "EXTRAIT DU PROGRAMME " + D["program"], "Black", 30, CYAN, W / 2, 560 + DIAG.height / 2 + 34, alpha=e)


def generic_step(c, k, p, first):
    header(c, p if first else 1)
    diagram_panel(c, p if first else 1)
    l1, l2 = D["cards"][k]
    col = {"K": CYAN, "X": YEL}.get(k, ACCENT)
    card(c, l1, l2, p, col=col, y=1160)


def cta(c, t, p):
    global MOCK
    if MOCK is None:
        m = Image.open(os.path.join(ASSETS, D["mock"])).convert("RGBA")
        MOCK = m.resize((900, 900), Image.LANCZOS)
    e = ease_out(min(1, p / 0.5))
    blit(c, MOCK, W / 2, 800 + (1 - e) * 300, alpha=e)
    glow_text(c, D["program"], 120, YEL, W / 2, 250, alpha=min(1, p / 0.3), scale=0.9 + 0.1 * ease_back(min(1, p / 0.4)))
    text(c, TAG[D["program"]], "Black", 52, WHITE, W / 2, 360, alpha=min(1, p / 0.4), maxw=900)
    b = ease_out((p - 1.2) / 0.4)
    pulse = 1 + 0.05 * math.sin(t * 7) * (p > 1.6)
    panel(c, [250, 1270, 830, 1390], ACCENT + (255,), b, r=60)
    text(c, "LIEN EN BIO", "Black", 70, (10, 10, 14), W / 2, 1330, alpha=b, scale=pulse)


def frame(t, T, parts, groups):
    c = bg_at(t, parts)
    k, p, d = T.at(t)
    if k == "H":
        z = 0.82 + 0.18 * ease_back(min(1, (t + 0.05) / 0.35))
        glow_text(c, D["hook"][0], 130, WHITE, W / 2, 470, scale=z)
        glow_text(c, D["hook"][1], 150, YEL, W / 2, 640, scale=z)
        mini_bounce(c, t, top=980, period=0.32)
    elif k in ("S1", "S2", "S3") or (k in ("K", "X") and "cards" in D):
        generic_step(c, k, p, k == "S1")
    elif k in LEVELS:
        header(c, p if k == "D1" else 1)
        scene_levels(c, k, t, p)
    elif k == "K1":
        header(c, 1); card(c, "LE BALLON CLAQUE", "LES DOIGTS, PAS LA PAUME", p)
        mini_bounce(c, t, top=1080, period=0.28)
    elif k == "K2":
        header(c, 1); card(c, "TOUJOURS", "MAIN FAIBLE D'ABORD", p, col=CYAN)
        mini_bounce(c, t, top=1080, period=0.32)
    elif k == "X":
        header(c, 1); card(c, "NIVEAU SUPÉRIEUR", "YEUX FERMÉS · 5 S", p, col=YEL)
        e = emoji("😌", 150)
        if e is not None:
            blit(c, e, W / 2, 1130, alpha=min(1, p / 0.3))
    elif k in ("S", "SV"):
        card(c, "ENREGISTRE", "POUR TA PROCHAINE SÉANCE", p, col=CYAN, y=700)
        e = emoji("📌", 150)
        if e is not None:
            blit(c, e, W / 2, 1050, scale=0.9 + 0.1 * ease_back(min(1, p / 0.3)))
    else:
        cta(c, t, p)
    captions(c, t, groups)
    return c.convert("RGB")


# ---------------------------------------------------------------- son
def _sine(f, d, decay=8):
    tt = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * f * tt) * np.exp(-decay * tt)


def whoosh(d=0.45):
    n = int(d * SR); x = np.random.default_rng(1).normal(0, 1, n)
    y = np.convolve(x, np.ones(30) / 30, mode="same") * np.sin(np.linspace(0, np.pi, n)) ** 2
    return y / (np.abs(y).max() + 1e-9)


def thump():
    a = _sine(85, 0.12, 30); a[:int(0.08 * SR)] += 0.4 * _sine(170, 0.08, 45); return a


def mix(voice_wav, T, out_wav):
    with wave.open(voice_wav) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, w.getnchannels()).mean(1) / 32768
    n = int(T.total * SR); out = np.zeros(n, np.float32); out[:len(v)] += v[:n]

    def add(x, t, g):
        i = int(t * SR)
        if i >= n: return
        x = x[: n - i]; out[i:i + len(x)] += x * g

    for k, (a, b) in T.span.items():
        if k != "H":
            add(whoosh(), max(0, a - 0.1), 0.08)
        if k in LEVELS:                       # rebonds du ballon, discrets
            period = {"D1": 0.26, "D2": 0.36, "D3": 0.48}[k]
            t0 = a - (a % period)
            tt = t0
            while tt < b:
                if tt >= a:
                    add(thump(), tt, 0.10)
                tt += period
    out = np.clip(out, -1, 1)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())


def _ribbon(c, txt):
    ti = outlined(txt, "Black", 60, WHITE, 0)
    rib = Image.new("RGBA", (ti.width + 70, ti.height + 40), (235, 64, 52, 255)); rib.alpha_composite(ti, (35, 20))
    sh = Image.new("RGBA", (rib.width + 12, rib.height + 12), (0, 0, 0, 0)); sh.paste((0, 0, 0, 255), (12, 12, rib.width + 12, rib.height + 12)); sh.alpha_composite(rib)
    blit(c, sh, W / 2, 700, rot=3, scale=min(1, 960 / sh.width))


def cover(out):
    from top10.main import _rays
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - 1150) / H * 1.1) ** 2)
    k = np.clip(1 - d * 1.6, 0, 1)[..., None]
    base = np.array([8, 10, 18], float); hi = np.array([255, 120, 30], float) * 0.85
    c = Image.fromarray((base + (hi - base) * k ** 1.4).astype(np.uint8), "RGB").convert("RGBA")
    c.alpha_composite(_rays((W, H), (W // 2, 1150), (255, 255, 255), alpha=26))
    # titre
    t1 = outlined(D["hook"][0], "Black", 128, WHITE, 12)
    blit(c, t1, W / 2, 300, scale=min(1, 1000 / t1.width))
    t2 = outlined(D["hook"][1], "Black", 230, YEL, 16)
    blit(c, t2, W / 2, 500, scale=min(1, 1020 / t2.width), rot=-4)
    if "diagram" in D:
        im = Image.open(os.path.join(ASSETS, D["diagram"])).convert("RGBA")
        im = im.resize((960, int(960 * im.height / im.width)), Image.LANCZOS)
        m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=44, fill=255)
        im.putalpha(m); blit(c, im, W / 2, 1110, rot=-2)
        _ribbon(c, "LE DRILL " + ("POUR DEVENIR SHIFTY" if D["program"] == "DRIBBLE 30" else "POUR DEVENIR SHOOTER"))
        panel(c, [250, 1520, 830, 1620], CYAN + (255,), 1, r=50)
        text(c, D["header"], "Black", 52, (8, 10, 18), W / 2, 1570, maxw=540)
        c.convert("RGB").save(out, quality=92)
        return
    # schéma 3 hauteurs + ballon avec traînée
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    for lab, y, col in (("HANCHE", 900, (255, 255, 255)), ("GENOU", 1080, (255, 255, 255)), ("CHEVILLE", 1260, YEL)):
        for x in range(110, 980, 30):
            dr.line([x, y, x + 16, y], fill=col + (200,), width=6)
        c.alpha_composite(lay); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
        tl = outlined(lab, "Black", 54, col, 6)
        blit(c, tl, 130 + tl.width / 2, y - 45)
    panel(c, [90, 1400, 990, 1412], (255, 255, 255, 160), 1, r=6)
    for i, (yb, a) in enumerate(((930, 0.18), (1080, 0.3), (1220, 0.5))):
        blit(c, BALL, 790, yb, scale=1.25, alpha=a)
    blit(c, BALL, 790, 1320, scale=1.45)
    ten = outlined("10×", "Black", 150, WHITE, 12)
    blit(c, ten, 540, 1165, rot=-6)
    _ribbon(c, "LE DRILL POUR DEVENIR SHIFTY")
    # pastille
    panel(c, [300, 1520, 780, 1620], CYAN + (255,), 1, r=50)
    text(c, "3 MIN PAR JOUR", "Black", 56, (8, 10, 18), W / 2, 1570)
    c.convert("RGB").save(out, quality=92)


HASHTAGS = "#basket #basketball #handles #basketballdrills #entrainementbasket #hooper #playground"


def caption():
    tags = HASHTAGS if D["program"] == "DRIBBLE 30" else HASHTAGS.replace("#handles", "#shooting").replace("#hooper", "#shooter")
    return (f"{D['caption']} 👇\n\nEnregistre pour ta prochaine séance 📌\n\n"
            f"Le programme complet {D['program']} ({TAG[D['program']].lower()}) : lien en bio 🔗\n\n{tags}")


STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")


def next_drill():
    done = _json.load(open(STATE)).get("done", []) if os.path.exists(STATE) else []
    order = [k for k in DRILLS if k != "pound"]
    for k in order:
        if k not in done:
            return k
    return order[len(done) % len(order)]   # tout fait : on recommence la boucle


def mark_done(k):
    st = _json.load(open(STATE)) if os.path.exists(STATE) else {"done": []}
    if k not in st["done"]:
        st["done"].append(k)
    _json.dump(st, open(STATE, "w"), ensure_ascii=False, indent=1)


def schedule(video, cover_path, at):
    """File de publication (Instagram + YouTube auto, brouillon TikTok) + aperçu Discord (❌ = annulation)."""
    from publish import queue
    from chiffre import discord_post
    cap = caption()
    yt_title = f"{D['hook'][0].capitalize()} {D['hook'][1].lower()} Le drill {D['header'].title()} 🏀 #Shorts"
    msg = (f"**🏀 Exercice de la semaine : {D['header']}** ({D['program']}) — publication automatique le {at} "
           f"(Instagram + YouTube ; brouillon TikTok quelques heures avant). Mets ❌ sur ce message pour l'annuler.")
    mid = None
    if os.environ.get("DISCORD_BOT_TOKEN"):
        try:
            mid = discord_post.post(video, msg[:1900], cover_path)
        except Exception as ex:   # vidéo trop lourde pour Discord, etc. : on programme quand même
            print("Aperçu Discord impossible :", ex)
            discord_post.notify(msg[:1800] + "\n(Vidéo trop lourde pour l'aperçu Discord.)")
    key = "drill_" + D["id"]
    queue.add(key, video, cover_path, cap, yt_title, f"{cap}\n\n#Shorts", at, mid, cap)
    mark_done(D["id"])
    print("Programmé :", key, at)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="out_drill"); ap.add_argument("--drill", default="pound")
    ap.add_argument("--queue-at", help="'AAAA-MM-JJ HH:MM' (Paris) : programme la publication")
    a = ap.parse_args()
    global D
    D = DRILLS[next_drill() if a.drill == "next" else a.drill]
    os.makedirs(a.out, exist_ok=True)
    vw = os.path.join(a.out, "voix_drill.wav")
    cues, total = tts.synth(D["segs"], vw)
    T = TL(cues, total)
    groups = chunks(words_from_last())
    if not groups:
        ws = []
        for k, s, e in cues:
            txt = re.sub(r"\[[^\]]*\]", "", dict(D["segs"])[k]).split()
            for i, w_ in enumerate(txt):
                ws.append((w_, s + (e - s) * i / len(txt), s + (e - s) * (i + 1) / len(txt)))
        groups = chunks(ws)
    parts = build_bg((20, 60, 110))
    silent = os.path.join(a.out, "video_drill.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-maxrate", "2.4M", "-bufsize", "4.8M", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i in range(int(T.total * FPS)):
        p.stdin.write(frame(i / FPS, T, parts, groups).tobytes())
    p.stdin.close(); p.wait()
    aud = os.path.join(a.out, "audio_drill.wav"); mix(vw, T, aud)
    final = os.path.join(a.out, D["file"] + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", aud, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-shortest", final], check=True)
    os.remove(silent)
    cover(os.path.join(a.out, D["file"] + ".jpg"))
    open(os.path.join(a.out, D["file"] + ".txt"), "w", encoding="utf-8").write(caption())
    print("Vidéo :", final, f"{T.total:.1f}s")
    if a.queue_at:
        schedule(final, os.path.join(a.out, D["file"] + ".jpg"), a.queue_at)


if __name__ == "__main__":
    main()
