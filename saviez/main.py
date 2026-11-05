"""Série « Le saviez-tu ? » : une histoire NBA racontée en motion design (prototype : draft 2009 / Curry).
usage : python -m saviez.main [--no-post]"""
import argparse, math, os, subprocess, sys, traceback, wave
import numpy as np
from PIL import Image, ImageDraw

from chiffre import tts, discord_post
from chiffre.render import W, H, FPS, WHITE, GREY, font, text, text_img, blit, panel, ease_out, ease_back
from chiffre.teams import team
from quiz.main import vivid_bg, bg_at, _vivid, _lum, _pop, _buzz, LIVELY, SR  # noqa

YEL = (255, 196, 0)
RED = (255, 60, 90)
SEGS = [
    ("H", "En 2009, une équipe NBA a laissé passer Stephen Curry… deux fois de suite !"),
    ("D1", "Draft 2009. Choix numéro 5 : Minnesota prend Ricky Rubio."),
    ("D2", "Choix numéro 6 : encore Minnesota… Jonny Flynn."),
    ("D3", "Choix numéro 7 : Golden State prend… Stephen Curry."),
    ("K", "Juste derrière, les Knicks, qui avaient Curry en tête de liste, se font doubler. Le Madison Square Garden siffle !"),
    ("F", "Flynn, lui, ne jouera que trois saisons en NBA."),
    ("C", "Et Curry ? Quatre titres, deux MVP, et le record absolu de paniers à trois points."),
    ("E", "Et toi, tu connaissais cette histoire ? Abonne-toi pour plus d'histoires NBA !"),
]
PICKS = [(1, "BLAKE GRIFFIN", "LAC"), (2, "HASHEEM THABEET", "MEM"), (3, "JAMES HARDEN", "OKC"), (4, "TYREKE EVANS", "SAC"),
         (5, "RICKY RUBIO", "MIN"), (6, "JONNY FLYNN", "MIN"), (7, "STEPHEN CURRY", "GSW")]
TOP, ROW_H, GAP = 430, 104, 16


def tag(c, s, x, y, col, fg=(15, 15, 20), size=34, alpha=1.0, scale=1.0, rot=0):
    ti = text_img(s, "Black", size, fg)
    im = Image.new("RGBA", (ti.width + 40, ti.height + 22), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=14, fill=col + (255,))
    im.alpha_composite(ti, (20, 11))
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    blit(c, im, x, y, alpha=alpha, scale=scale)


def row(c, i, num, name, code, p, hl=None, dim=1.0):
    if p <= 0: return
    a = min(1, p * 1.8) * dim
    y = TOP + i * (ROW_H + GAP); x0, x1 = 70, 1010
    d = team(code); bg = _vivid(tuple(d["bg"]))
    cw, ch = x1 - x0, ROW_H
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    g.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=24, fill=(28, 22, 52, 235))
    g.rounded_rectangle([0, 0, 150, ch - 1], radius=24, fill=bg + (255,)); g.rectangle([120, 0, 150, ch - 1], fill=bg + (255,))
    nt = text_img(f"#{num}", "Black", 48, (15, 15, 20) if _lum(bg) > 170 else WHITE)
    im.alpha_composite(nt, (75 - nt.width // 2, ch // 2 - nt.height // 2))
    nm = text_img(name, "Black", 46, WHITE)
    im.alpha_composite(nm, (180, int(ch * 0.38 - nm.height / 2)))
    tm = text_img(d["name"], "ExtraBold", 28, (200, 190, 235), spacing=3)
    im.alpha_composite(tm, (182, int(ch * 0.74 - tm.height / 2)))
    if hl:
        o = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        ImageDraw.Draw(o).rounded_rectangle([2, 2, cw - 3, ch - 3], radius=24, outline=hl + (255,), width=7)
        im.alpha_composite(o)
    off = (1 - ease_out(min(1, p))) * 260
    blit(c, im, (x0 + x1) / 2 + off, y + ch / 2, alpha=a, scale=0.7 + 0.3 * ease_back(min(1, p)))


def frame(t, cue, parts, total):
    im = bg_at(t, parts); c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    T = lambda k: cue[k][0]
    tag(c, "LE SAVIEZ-TU ?", W / 2, 150, YEL, size=44, scale=0.9 + 0.1 * ease_back(min(1, t / 0.3)))
    # --- accroche
    if t < T("D1") + 0.3:
        a = 1 - max(0, (t - T("D1")) / 0.3)
        p = lambda d: ease_back(min(1, max(0, (t - d) / 0.35)))
        text(c, "2009", "Black", 300, YEL, W / 2, 620, alpha=a, scale=0.6 + 0.4 * p(0.0))
        text(c, "ILS ONT LAISSÉ PASSER", "Black", 72, WHITE, W / 2, 860, alpha=a * min(1, t / 0.5), maxw=960)
        text(c, "STEPHEN CURRY", "Black", 110, WHITE, W / 2, 970, alpha=a, scale=p(0.6), maxw=980)
        if t > 2.2: tag(c, "2 FOIS DE SUITE", W / 2, 1120, RED, fg=WHITE, size=58, alpha=a, scale=p(2.2), rot=-3)
    # --- tableau de draft
    if T("D1") - 0.1 <= t < T("E"):
        text(c, "DRAFT NBA 2009", "Black", 70, WHITE, W / 2, 300, alpha=min(1, (t - T("D1") + 0.1) / 0.3))
        dim = 0.35 if t > T("C") else 1.0
        starts = [T("D1") - 0.1 + 0.12 * k for k in range(4)] + [T("D1") + 1.6, T("D2") + 0.9, T("D3") + 1.6]
        for i, (num, name, code) in enumerate(PICKS):
            hl = (RED if i in (4, 5) and t > T("D3") + 1.6 else None) or (YEL if i == 6 else None)
            row(c, i, num, name, code, (t - starts[i]) / 0.4, hl, dim=(0.45 if i < 4 and t > T("D1") + 1.6 else 1.0) * dim)
        if T("D2") + 0.9 < t < T("F"):
            tag(c, "ENCORE ?!", 900, TOP + 5 * (ROW_H + GAP) + 10, RED, fg=WHITE, size=36, rot=8,
                scale=ease_back(min(1, (t - T("D2") - 0.9) / 0.3)))
        if t > T("D3") + 1.6:
            q = (t - T("D3") - 1.6)
            if q < 0.25:
                fl = Image.new("RGBA", (W, H), (255, 255, 255, int(120 * (1 - q / 0.25)))); c.alpha_composite(fl)
        # Knicks : 8e choix
        if t >= T("K") and t < T("C"):
            row(c, 7, 8, "KNICKS (NEW YORK)", "NYK", (t - T("K") - 0.2) / 0.4, RED)
            if t > T("K") + 2.6:
                tag(c, "LE GARDEN SIFFLE 😤".replace(" 😤", ""), W / 2, TOP + 8 * (ROW_H + GAP) + 40, RED, fg=WHITE, size=48,
                    scale=ease_back(min(1, (t - T("K") - 2.6) / 0.3)))
        if T("F") <= t < T("C"):
            tag(c, "3 SAISONS EN NBA", 830, TOP + 5 * (ROW_H + GAP) + ROW_H / 2, WHITE, size=34, rot=-4,
                scale=ease_back(min(1, (t - T("F") - 0.4) / 0.3)) if t > T("F") + 0.4 else 0.001)
    # --- palmarès de Curry
    if T("C") <= t < T("E"):
        q = t - T("C")
        panel(c, [70, 520, 1010, 1420], (24, 14, 60, 245), alpha=min(1, q / 0.3), r=40, outline=YEL + (255,))
        text(c, "STEPHEN CURRY", "Black", 76, WHITE, W / 2, 610, alpha=min(1, q / 0.3))
        for k, (big, small, at) in enumerate([("4", "TITRES", 1.1), ("2", "MVP", 2.0), ("N°1", "À 3 POINTS DE L'HISTOIRE", 2.7)]):
            if q > at:
                pp = ease_back(min(1, (q - at) / 0.35)); y = 800 + k * 210
                text(c, big, "Black", 140, YEL, 290, y, scale=pp, anchor="mm")
                text(c, small, "Black", 50, WHITE, 470, y, scale=pp, anchor="lm", maxw=500)
    # --- appel à l'action
    if t >= T("E"):
        q = t - T("E"); pp = ease_back(min(1, q / 0.4))
        text(c, "ET TOI,", "Black", 120, WHITE, W / 2, 760, scale=pp)
        text(c, "TU SAVAIS ?", "Black", 120, YEL, W / 2, 900, scale=pp)
        if q > 1.2: tag(c, "ABONNE-TOI POUR PLUS D'HISTOIRES NBA", W / 2, 1110, YEL, size=40, scale=ease_back(min(1, (q - 1.2) / 0.3)))
    im.alpha_composite(c)
    return im.convert("RGB")


def _read(p):
    with wave.open(p) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return x.reshape(-1, w.getnchannels()).mean(1)


def run(post=True, out="out_saviez"):
    os.makedirs(out, exist_ok=True)
    vw = os.path.join(out, "voix.wav")
    cues, total_v = tts.synth(SEGS, vw, LIVELY)
    cue = {k: (a, b) for k, a, b in cues}
    total = total_v + 1.2
    parts = vivid_bg()
    silent = os.path.join(out, "silent.mp4")
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-maxrate", "1500k", "-bufsize", "3M", "-pix_fmt", "yuv420p", silent],
                          stdin=subprocess.PIPE)
    for i in range(int(total * FPS)):
        pr.stdin.write(frame(i / FPS, cue, parts, total).tobytes())
    pr.stdin.close(); pr.wait()
    # son : voix normalisée + effets discrets
    vn = os.path.join(out, "voix_n.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "1", vn], check=True)
    n = int((total + 0.1) * SR); buf = np.zeros(n, np.float32)
    def add(x, at, g):
        i = int(at * SR); x = x[: max(0, n - i)]; buf[i:i + len(x)] += g * x
    add(_read(vn), 0, 1.0)
    T = lambda k: cue[k][0]
    for at in [T("D1") + 1.6, T("D2") + 0.9, T("D3") + 1.6, T("C") + 1.1, T("C") + 2.0, T("C") + 2.7]:
        add(_pop(), at, 0.14)
    add(_buzz(), T("K") + 2.6, 0.12)
    buf = np.tanh(buf * 1.1) * 0.95
    aw = os.path.join(out, "mix.wav")
    with wave.open(aw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf * 32767).astype(np.int16).tobytes())
    final = os.path.join(out, "le_saviez_tu_curry_2009.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", aw, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
    # miniature = image du hook
    cover = os.path.join(out, "miniature.jpg"); frame(2.6, cue, parts, total).save(cover, quality=92)
    msg = ("**🧠 Le saviez-tu ? (prototype)** — Curry et la draft 2009\n\n"
           "🎵 **TikTok** :\n```Minnesota a laissé passer Stephen Curry… deux fois 🤯 Tu connaissais cette histoire ?\n\n"
           "#NBA #stephencurry #basketball #NBAFrance #lesaviezvous```\n"
           "📸 **Instagram** :\n```Minnesota a laissé passer Stephen Curry… deux fois 🤯 Tu connaissais cette histoire ?\n\n"
           "Abonne-toi pour plus d'histoires NBA 🔔\n\n#NBA #stephencurry #basketball #basket #NBAFrance #NBADailyNews #lesaviezvous #warriors #nbahistory #sport```\n"
           "▶️ **YouTube Shorts** — titre :\n```Ils ont laissé passer Stephen Curry… DEUX FOIS 🤯 #Shorts```")
    print("Vidéo :", final)
    if post and os.environ.get("DISCORD_BOT_TOKEN"):
        discord_post.post(final, msg, cover)
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--no-post", action="store_true")
    a = ap.parse_args()
    try:
        run(not a.no_post)
    except Exception:
        err = traceback.format_exc(); print(err)
        discord_post.notify(f"⚠️ La vidéo « Le saviez-tu » n'a pas pu être générée.\n```{err[-1500:]}```")
        sys.exit(1)
