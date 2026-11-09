"""Prototype « histoire d'horreur à choix » : voix off, décors sombres animés, sous-titres mot à mot, choix A/B final.
usage : python -m horreur.main --out docs/proto"""
import argparse, math, os, re, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from chiffre import tts
from chiffre.render import W, H, FPS, WHITE, blit, ease_out, ease_back
from top10.main import outlined, words_from_last, chunks

RED = (220, 30, 40)
FILE = "vol_714_partie_1"
SEGS = [
    ("S1", "[whispers] Vol sept cent quatorze. Trois heures du matin. Tout l'avion dort… sauf moi."),
    ("S2", "[nervous] Au-dessus du siège quatorze C, la petite lumière s'allume. Puis s'éteint. Puis se rallume. [whispers] Ce siège est vide depuis le décollage."),
    ("S3", "Une hôtesse remonte l'allée. Je ne l'avais jamais vue. Elle s'arrête à ma hauteur… et me sourit. [whispers] Elle ne cligne pas des yeux."),
    ("S4", "Je tourne la tête vers le hublot. Pas de nuages. Pas d'étoiles. Aucune lumière en bas. [whispers] Rien."),
    ("S5", "Et là, l'interphone grésille. [whispers] Mesdames et messieurs… merci de rester assis. Nous n'avons jamais décollé."),
    ("CH", "[nervous] À toi de choisir. A : je me lève et je vais au cockpit. B : je réveille l'homme assis à côté de moi. Écris A ou B en commentaire… la suite arrive demain."),
]
VP = (540, 860)  # point de fuite de l'allée


# ---------------------------------------------------------------- décors (dessinés une fois, un peu plus grands pour le zoom)
def cabin(lit=False):
    S = 1.15; w, h = int(W * S), int(H * S)
    im = Image.new("RGB", (w, h), (6, 8, 14)); d = ImageDraw.Draw(im)
    vx, vy = VP[0] * S, VP[1] * S
    # plafond / sol / parois en perspective
    d.polygon([(0, 0), (w, 0), (vx + 120, vy - 140), (vx - 120, vy - 140)], fill=(14, 18, 28))
    d.polygon([(0, h), (w, h), (vx + 90, vy + 60), (vx - 90, vy + 60)], fill=(10, 11, 18))
    d.polygon([(w * 0.36, h), (w * 0.64, h), (vx + 22, vy + 60), (vx - 22, vy + 60)], fill=(30, 14, 18))  # moquette de l'allée
    # rangées de sièges (de loin vers près), de part et d'autre de l'allée
    def row(k):
        f = (k / 14) ** 2.2
        y = vy + 60 + (h - vy - 60) * (1 - f)
        ah = 22 + (w * 0.14 - 22) * (1 - f)          # demi-largeur de l'allée à cette profondeur
        sw, sh = 40 + 430 * (1 - f), 30 + 560 * (1 - f)
        return y, ah, sw, sh
    for k in range(14, 0, -1):
        y, ah, sw, sh = row(k)
        for side in (-1, 1):
            x = vx + side * (ah + 8 + sw / 2)
            col = (40, 38, 30) if (lit and k == 8 and side == 1) else (24, 28, 40)
            d.rounded_rectangle([x - sw / 2, y - sh, x + sw / 2, y], radius=int(sw * 0.16), fill=col, outline=(4, 5, 9), width=3)
            d.rounded_rectangle([x - sw * 0.42, y - sh * 1.08, x + sw * 0.42, y - sh * 0.86], radius=int(sw * 0.12), fill=(32, 36, 50), outline=(4, 5, 9), width=2)  # appui-tête
            hx = vx + side * (ah + sw * 1.25); ww, wh = sw * 0.18, sh * 0.26
            if 0 < hx < w:
                d.rounded_rectangle([hx - ww / 2, y - sh * 1.35 - wh, hx + ww / 2, y - sh * 1.35], radius=int(ww * 0.45), fill=(2, 3, 6), outline=(30, 34, 46), width=2)
    # coffres à bagages
    d.polygon([(0, h * 0.18), (vx - 120, vy - 140), (vx - 100, vy - 100), (0, h * 0.32)], fill=(20, 24, 36))
    d.polygon([(w, h * 0.18), (vx + 120, vy - 140), (vx + 100, vy - 100), (w, h * 0.32)], fill=(20, 24, 36))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    if lit:  # cône de lumière sur le siège 14C (rangée de droite)
        y, ah, sw, sh = row(8); x = vx + ah + 8 + sw / 2
        L = Image.new("L", (w, h), 0); dl = ImageDraw.Draw(L)
        dl.polygon([(x - 14, y - sh * 1.7), (x + 14, y - sh * 1.7), (x + sw * 0.55, y - sh * 0.2), (x - sw * 0.55, y - sh * 0.2)], fill=140)
        dl.ellipse([x - 16, y - sh * 1.72 - 10, x + 16, y - sh * 1.72 + 10], fill=255)
        L = L.filter(ImageFilter.GaussianBlur(18))
        im = Image.composite(Image.new("RGB", (w, h), (255, 226, 160)), im, L)
    return im


def window_view():
    im = Image.new("RGB", (int(W * 1.15), int(H * 1.15)), (18, 20, 28)); d = ImageDraw.Draw(im)
    cx, cy = im.width / 2, im.height * 0.46
    d.rounded_rectangle([cx - 380, cy - 560, cx + 380, cy + 560], radius=360, fill=(40, 44, 56))
    d.rounded_rectangle([cx - 320, cy - 500, cx + 320, cy + 500], radius=310, fill=(0, 0, 0))
    return im.filter(ImageFilter.GaussianBlur(1.5)), (cx, cy)


def figure(scale):
    """Silhouette de l'hôtesse : tête, chignon, corps ; deux yeux pâles."""
    s = scale; im = Image.new("RGBA", (int(260 * s) + 4, int(820 * s) + 4), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = im.width / 2
    d.ellipse([cx - 60 * s, 30 * s, cx + 60 * s, 175 * s], fill=(3, 3, 5, 255))
    d.ellipse([cx - 30 * s, 0, cx + 30 * s, 55 * s], fill=(3, 3, 5, 255))
    d.polygon([(cx - 40 * s, 165 * s), (cx + 40 * s, 165 * s), (cx + 125 * s, 520 * s), (cx + 95 * s, 820 * s), (cx - 95 * s, 820 * s), (cx - 125 * s, 520 * s)], fill=(3, 3, 5, 255))
    for ex in (-24, 24):
        d.ellipse([cx + ex * s - 9 * s, 92 * s, cx + ex * s + 9 * s, 104 * s], fill=(235, 235, 220, 255))
    return im


GRAIN = [Image.fromarray(np.random.default_rng(i).integers(0, 255, (H // 2, W // 2), dtype=np.uint8)).resize((W, H)) for i in range(8)]
VIG = None


def vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    dd = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
    a = np.clip((dd - 0.45) * 1.6, 0, 1) * 235
    v = Image.new("RGBA", (W, H), (0, 0, 0, 255)); v.putalpha(Image.fromarray(a.astype(np.uint8))); return v


def zoomed(base, z, cx=None, cy=None):
    cx = base.width / 2 if cx is None else cx; cy = base.height / 2 if cy is None else cy
    cw, ch = W / z, H / z
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return base.resize((W, H), Image.BILINEAR, box=box)


# ---------------------------------------------------------------- sous-titres (mot actif en rouge)
def captions(c, t, groups):
    for g in groups:
        a, b = g[0][1], g[-1][2] + 0.15
        if a - 0.05 <= t < b:
            ims = []
            for w_, ws, we in g:
                col = RED if ws - 0.03 <= t < we + 0.08 else WHITE
                ims.append((outlined(w_.upper().strip("…«»"), "Black", 78, col, 9), ws - 0.03 <= t, ws))
            tot = sum(i.width for i, _, _ in ims) + 18 * (len(ims) - 1); sc = min(1, 980 / tot); x = W / 2 - tot * sc / 2
            for im, on, ws in ims:
                pop = 0.88 + 0.12 * ease_back(min(1, (t - ws) / 0.16)) if on else 1
                blit(c, im, x + im.width * sc / 2, 1430, scale=sc * pop, alpha=1 if on else 0)
                x += (im.width + 18) * sc
            return


def card(lbl, txt, col):
    im = Image.new("RGBA", (900, 250), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 899, 249], radius=36, fill=(12, 12, 16, 235), outline=col + (255,), width=6)
    d.ellipse([30, 45, 190, 205], fill=col + (255,))
    l = outlined(lbl, "Black", 120, WHITE, 0); im.alpha_composite(l, (110 - l.width // 2, 125 - l.height // 2))
    lines = txt.split("\n")
    for i, ln in enumerate(lines):
        t_ = outlined(ln, "Black", 52, WHITE, 0)
        k = min(1, 650 / t_.width); t_ = t_.resize((int(t_.width * k), int(t_.height * k)))
        im.alpha_composite(t_, (225, int(125 - len(lines) * 34 + i * 70)))
    return im


# ---------------------------------------------------------------- image
def frame(t, cues, groups, A):
    k = next((c for c, s, e in cues if s - 0.25 <= t < e + 0.45), cues[-1][0] if t > cues[-1][1] else cues[0][0])
    s0, e0 = next((s, e) for c, s, e in cues if c == k); p = max(0, t - s0 + 0.25); d = max(0.5, e0 - s0)
    fl = 1.0
    if k in ("S1", "S2", "S3"):
        base = A["lit"] if (k == "S2" and int(p * 2.2) % 3 != 1) or k == "S3" else A["cab"]
        c = zoomed(base, 1.0 + 0.05 * (p / d) + (0.03 if k == "S3" else 0)).convert("RGBA")
        if k == "S1": fl = 0.75 + 0.25 * min(1, p / 1.5)
        if k == "S3":
            sc = 0.25 + 0.95 * ease_out(min(1, p / d)) ** 1.6
            fig = A["fig"].resize((int(A["fig"].width * sc), int(A["fig"].height * sc)))
            blit(c, fig, W / 2 + 10, VP[1] - 60 + fig.height / 2 * 0.98)
    elif k == "S4":
        base, (cx, cy) = A["win"]
        c = zoomed(base, 1.0 + 0.12 * ease_out(min(1, p / d))).convert("RGBA")
        if 1.4 < p < 1.55 or 1.7 < p < 1.78:
            c.alpha_composite(Image.new("RGBA", (W, H), (200, 210, 255, 60)))
    elif k == "S5":
        c = zoomed(A["cab"], 1.08 + 0.1 * (p / d)).convert("RGBA")
        fl = 0.55 + 0.45 * (1 if int(t * 12) % 5 else 0.3)
        last = p > d * 0.55
        if last:
            r = 0.45 * (0.6 + 0.4 * math.sin(t * 9))
            c.alpha_composite(Image.new("RGBA", (W, H), (150, 0, 10, int(255 * r))))
        tx = outlined("« NOUS N'AVONS JAMAIS DÉCOLLÉ »", "Black", 64, RED if last else WHITE, 8)
        blit(c, tx, W / 2, 560, scale=min(1, 980 / tx.width), alpha=ease_out((p - d * 0.55) / 0.3))
    else:  # choix
        c = zoomed(A["cab"], 1.15).convert("RGBA"); fl = 0.45
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)))
        h1 = outlined("À TOI DE CHOISIR", "Black", 96, WHITE, 10)
        blit(c, h1, W / 2, 420, scale=0.85 + 0.15 * ease_back(min(1, p / 0.4)))
        blit(c, A["cA"], W / 2, 690, alpha=ease_out((p - 1.0) / 0.4))
        blit(c, A["cB"], W / 2, 980, alpha=ease_out((p - 3.2) / 0.4))
        cm = outlined("ÉCRIS A OU B EN COMMENTAIRE", "Black", 54, (255, 214, 10), 8)
        blit(c, cm, W / 2, 1220, scale=min(1, 980 / cm.width), alpha=ease_out((p - 5.2) / 0.4))
    if fl < 1:
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - fl)))))
    # bandeau titre permanent
    tg = A["tag"]; blit(c, tg, W / 2, 175)
    c.alpha_composite(A["vig"])
    g = GRAIN[int(t * FPS) % len(GRAIN)]
    c = Image.blend(c.convert("RGB"), Image.merge("RGB", (g, g, g)), 0.06)
    cc = c.convert("RGBA"); captions(cc, t, groups)
    if t < 0.4:
        cc.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - t / 0.4)))))
    return cc.convert("RGB")


# ---------------------------------------------------------------- son : nappe grave, battements, grésillement, coup final
def ambience(total, cues, out):
    sr = 48000; n = int(total * sr) + sr; t = np.arange(n) / sr
    rng = np.random.default_rng(1)
    drone = 0.06 * np.sin(2 * np.pi * 49 * t) + 0.05 * np.sin(2 * np.pi * 51.5 * t) + 0.03 * np.sin(2 * np.pi * 98.3 * t)
    drone *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t)
    hum = np.convolve(rng.normal(0, 1, n), np.ones(400) / 400, "same") * 0.9  # bruit de cabine sourd
    y = drone + hum
    C = {c: (s, e) for c, s, e in cues}
    # battements de cœur à partir de S3, qui accélèrent
    s3, e5 = C["S3"][0], C["S5"][1]
    tb = s3; bpm = 62
    while tb < e5:
        for dt, a in ((0, 0.5), (0.22, 0.32)):
            i = int((tb + dt) * sr); L = int(0.16 * sr)
            if i + L < n:
                tt = np.arange(L) / sr
                y[i:i + L] += a * np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 28)
        bpm = min(110, bpm + 2.5); tb += 60 / bpm
    # grésillement d'interphone pendant S5
    a, b = int(C["S5"][0] * sr), int(C["S5"][1] * sr)
    y[a:b] += rng.normal(0, 0.035, b - a) * (rng.random(b - a) > 0.6)
    # coup sourd sur « jamais décollé »
    i = int((C["S5"][0] + (C["S5"][1] - C["S5"][0]) * 0.55) * sr); L = int(1.6 * sr)
    tt = np.arange(L) / sr
    y[i:i + L] += 0.9 * np.sin(2 * np.pi * (70 - 30 * tt) * tt) * np.exp(-tt * 2.2) + rng.normal(0, 0.08, L) * np.exp(-tt * 6)
    y = np.clip(y, -1, 1)
    st = (np.stack([y, y], 1) * 32767 * 0.8).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(st.tobytes())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="out_horreur"); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    vw = os.path.join(a.out, "voix.wav")
    cues, total = tts.synth(SEGS, vw, speed=float(os.environ.get("HORROR_SPEED", "1.04")))
    total += 2.0
    ws = words_from_last()
    if not ws:
        for k, s, e in cues:
            txt = re.sub(r"\[[^\]]*\]", "", dict(SEGS)[k]).split()
            ws += [(w_, s + (e - s) * i / len(txt), s + (e - s) * (i + 1) / len(txt)) for i, w_ in enumerate(txt)]
    groups = chunks(ws)
    tag = Image.new("RGBA", (560, 92), (0, 0, 0, 0)); dt = ImageDraw.Draw(tag)
    dt.rounded_rectangle([0, 0, 559, 91], radius=24, fill=(150, 0, 12, 230))
    tt = outlined("VOL 714 · PARTIE 1", "Black", 50, WHITE, 0); tag.alpha_composite(tt, ((560 - tt.width) // 2, (92 - tt.height) // 2))
    A = {"cab": cabin(), "lit": cabin(True), "win": window_view(), "fig": figure(1.0), "vig": vignette(), "tag": tag,
         "cA": card("A", "Je vais au\ncockpit", RED), "cB": card("B", "Je réveille\nmon voisin", (40, 110, 230))}
    silent = os.path.join(a.out, "video.mp4")
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-maxrate", "4M", "-bufsize", "8M", "-pix_fmt", "yuv420p", silent],
                          stdin=subprocess.PIPE)
    for i in range(int(total * FPS)):
        pr.stdin.write(frame(i / FPS, cues, groups, A).tobytes())
    pr.stdin.close(); pr.wait()
    amb = os.path.join(a.out, "amb.wav"); ambience(total, cues, amb)
    final = os.path.join(a.out, FILE + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", vw, "-i", amb, "-filter_complex",
                    "[1:a]volume=1.0[v];[2:a]volume=0.55[b];[v][b]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", final], check=True)
    frame(cues[2][1] + 3.0, cues, groups, A).save(os.path.join(a.out, FILE + ".jpg"), quality=90)
    print("Vidéo :", final, f"{total:.1f}s")


if __name__ == "__main__":
    main()
