"""Quiz « Qui est ce joueur ? » : parcours de franchises + années, compte à rebours, réponse en commentaire.
usage : python -m quiz.main [--player ID] [--no-post]"""
import argparse, json, math, os, random, subprocess, sys, traceback, wave
import numpy as np
from PIL import Image, ImageDraw

from chiffre import tts, discord_post
from chiffre.render import (W, H, FPS, ACCENT, WHITE, GREY, font, text, text_img, blit, panel,
                            build_bg, bg_at, ease_out, ease_back)
from chiffre.teams import team, NICK

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
LEVELS = {"facile": ("FACILE", (52, 211, 120)), "moyen": ("MOYEN", ACCENT), "difficile": ("DIFFICILE", (226, 27, 77))}
CITY = {"LAL": "LOS ANGELES", "LAC": "LOS ANGELES"}
STEP, FINAL = 0.85, 5          # écart entre deux cartes ; secondes de compte à rebours après la dernière carte
CARD_TOP, CARD_BOTTOM, BAR_Y = 450, 1380, 1475


def team_info(t):
    if isinstance(t, dict):  # franchise historique décrite dans players.json
        return t
    d = team(t)
    return dict(city=CITY.get(t, d["name"]), nick=NICK.get(t, "").upper(), bg=d["bg"], stripe=d["stripe"])


# ---------------- timeline
class TL:
    def __init__(self, P, intro_cues, intro_len, outro_len):
        self.cues = {c: (a, b) for c, a, b in intro_cues}
        self.I = intro_len + 0.25
        self.n = len(P["teams"])
        self.Tb = self.I + 0.3                       # début du chrono + 1re carte
        self.Dur = math.ceil(self.n * STEP) + FINAL   # durée totale du chrono (secondes entières)
        self.Te = self.Tb + self.Dur                  # fin du chrono
        self.To = self.Te + 0.35                      # début de la voix de fin
        self.total = self.To + outro_len + 0.9

    def card_t(self, i):
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


def card(c, i, info, years, t0, t, n, dim=1.0):
    p = (t - t0) / 0.35
    if p <= 0: return
    a = min(1, p) * dim
    gap = 16
    h = min(150, (CARD_BOTTOM - CARD_TOP - gap * (n - 1)) / n)
    y0 = CARD_TOP + i * (h + gap); off = (1 - ease_out(p)) * 220
    x0, x1 = 60 + off, 940 + off
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0, y0, x1, y0 + h], radius=26, fill=(26, 26, 33, int(235 * a)))
    d.rounded_rectangle([x0, y0, x0 + 30, y0 + h], radius=14, fill=tuple(info["bg"]) + (int(255 * a),))
    d.rectangle([x0 + 16, y0, x0 + 30, y0 + h], fill=tuple(info["bg"]) + (int(255 * a),))
    d.rectangle([x0 + 30, y0, x0 + 38, y0 + h], fill=tuple(info["stripe"]) + (int(255 * a),))
    c.alpha_composite(lay)
    cy = y0 + h / 2
    text(c, info["city"], "ExtraBold", int(h * 0.36), WHITE, x0 + 72, cy - h * 0.15, anchor="lm", alpha=a, maxw=480)
    text(c, info["nick"], "SemiBold", int(h * 0.22), GREY, x0 + 74, cy + h * 0.24, anchor="lm", alpha=a, spacing=3)
    text(c, years, "Black", int(h * 0.3), ACCENT, x1 - 34, cy, anchor="rm", alpha=a)


def timer(c, T, t):
    if t < T.Tb - 0.2: return
    a = min(1, (t - T.Tb + 0.2) / 0.3) * (1 - min(1, max(0, (t - T.Te - 0.4) / 0.3)))
    if a <= 0: return
    frac = max(0.0, min(1.0, 1 - (t - T.Tb) / T.Dur))
    left = min(T.Dur, max(0, math.ceil(T.Te - t)))
    last = left <= 3 and t < T.Te
    col = (226, 27, 77) if last else ACCENT
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
    QM = QM or qmark(520, ACCENT)
    im = bg_at(t, parts)
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # --- intro (gros titre + ? + niveau), puis le titre remonte en en-tête
    mv = ease_out((t - T.I) / 0.4) if t > T.I else 0.0
    ia = min(1, t / 0.25)
    y_t1 = 560 + (170 - 560) * mv; y_t2 = 690 + (262 - 690) * mv
    s_t = 1 - 0.45 * mv
    pop = ease_back(min(1, t / 0.45))
    text(c, "QUI EST", "Black", 150, WHITE, W / 2, y_t1, alpha=ia, scale=pop * s_t)
    text(c, "CE JOUEUR ?", "Black", 150, ACCENT, W / 2, y_t2, alpha=ia, scale=pop * s_t, maxw=960)
    blit(c, QM, W / 2, 1120 + 300 * mv, alpha=ia * (1 - mv), scale=0.9 + 0.1 * ease_back(min(1, t / 0.6)))
    lt = T.cues.get("L", (T.I - 0.8, 0))[0]
    if t >= lt:
        q = (t - lt) / 0.35
        bx_y = 1500 + (362 - 1500) * mv
        level_badge(c, P, W / 2, bx_y, alpha=min(1, q), scale=(0.6 + 0.4 * ease_back(min(1, q))) * (1 - 0.3 * mv))
    # --- cartes
    dim = 1 - 0.7 * ease_out((t - T.Te - 0.3) / 0.4) if t > T.Te + 0.3 else 1.0
    for i, (info, yrs) in enumerate(infos):
        card(c, i, info, yrs, T.card_t(i), t, len(infos), dim)
    timer(c, T, t)
    # --- fin : appel au commentaire
    if t > T.Te + 0.3:
        q = (t - T.Te - 0.3) / 0.45
        a = min(1, q); sc = 0.7 + 0.3 * ease_back(min(1, q))
        panel(c, [90, 620, 990, 1290], (14, 14, 18, 240), alpha=a, r=40, outline=ACCENT + (255,))
        blit(c, qmark(300, ACCENT), W / 2, 820, alpha=a, scale=sc)
        text(c, "ÉCRIS TA RÉPONSE", "Black", 76, WHITE, W / 2, 1050, alpha=a, scale=sc, maxw=820)
        text(c, "EN COMMENTAIRE", "Black", 76, ACCENT, W / 2, 1140, alpha=a, scale=sc, maxw=820)
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
    if lt is not None: add(_pop(), lt, 0.35)
    for i in range(T.n): add(_pop(), T.card_t(i), 0.22)
    for k in range(T.Dur):
        last = T.Dur - k <= 3
        add(_tick(2600 if last else (1900 if k % 2 == 0 else 1400)), T.Tb + k, 0.32 if last else 0.22)
    add(_buzz(), T.Te, 0.35)
    buf = np.tanh(buf * 1.1) * 0.95
    st = (np.stack([buf, buf], 1) * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())


def norm(path):
    out = path.replace(".wav", "_n.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "1", out], check=True)
    return out


# ---------------- programme
def run(pid=None, post=True, outdir="out_quiz"):
    os.makedirs(outdir, exist_ok=True)
    players = json.load(open(os.path.join(HERE, "players.json"), encoding="utf-8"))
    P = next(p for p in players if p["id"] == pid) if pid else random.choice(players)
    lab = LEVELS[P["level"]][0].lower()
    v1, v2 = os.path.join(outdir, "v1.wav"), os.path.join(outdir, "v2.wav")
    cues1, len1 = tts.synth([("H", "Seuls les vrais fans trouvent ce joueur."), ("L", f"Niveau : {lab}.")], v1)
    _, len2 = tts.synth([("E", "Tu l'as trouvé ? Écris ta réponse en commentaire !")], v2)
    T = TL(P, cues1, len1, len2)
    infos = [(team_info(tm), yrs) for tm, yrs in P["teams"]]
    parts = build_bg((70, 60, 110))
    silent = os.path.join(outdir, "silent.mp4")
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-maxrate", "1500k", "-bufsize", "3M",
                           "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i in range(int(T.total * FPS)):
        pr.stdin.write(frame(i / FPS, P, T, infos, parts).tobytes())
    pr.stdin.close(); pr.wait()
    audio = os.path.join(outdir, "mix.wav")
    has_voice = bool(os.environ.get("ELEVENLABS_API_KEY"))
    mix(T, norm(v1) if has_voice else v1, norm(v2) if has_voice else v2, audio)
    final = os.path.join(outdir, f"quiz_{P['id']}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
    tags = "#NBA #quiz #basketball #NBAFrance #NBADailyNews"
    msg = (f"**Quiz — qui est ce joueur ?** (niveau {lab})\n"
           f"🔒 Réponse (à épingler en commentaire plus tard) : ||{P['name']}||\n\n"
           f"🎵 **TikTok / 📸 Instagram** :\n```Seuls les vrais fans trouvent ce joueur 👀 Niveau {lab}. Réponse en commentaire 👇\n\n{tags}```\n"
           f"▶️ **YouTube Shorts** — titre :\n```Qui est ce joueur NBA ? 🤔 (niveau {lab}) #Shorts```")
    print("Vidéo :", final)
    if post and os.environ.get("DISCORD_BOT_TOKEN"):
        discord_post.post(final, msg)
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--player"); ap.add_argument("--no-post", action="store_true")
    a = ap.parse_args()
    try:
        run(a.player, not a.no_post)
    except Exception:
        err = traceback.format_exc(); print(err)
        discord_post.notify(f"⚠️ Le quiz n'a pas pu être généré.\n```{err[-1500:]}```")
        sys.exit(1)
