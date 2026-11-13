"""Format « Duel » : 2 joueurs comparés stat par stat (manches, score permanent, verdict en commentaire).
Épisode décrit en JSON (duel/episodes/<slug>.json). Lancement : python -m top10.main --episode duel/episodes/x.json
(top10.main redirige ici quand le JSON contient "format": "duel") ou python -m duel.main --episode ...
Photos : uniquement celles de top10/assets/ (fournies par Mathieu) ; sinon silhouette tirée de la photo officielle NBA."""
import argparse, json, math, os, re, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from chiffre import tts
from chiffre.render import W, H, FPS, WHITE, font, text, text_img, blit, panel, build_bg, bg_at, ease_out, ease_back
from top10.main import (outlined, emoji, chunks, words_from_last, captions, whoosh, pop, ding, _sine, _rays,
                        _outline_sticker, _fit, YEL, SILVER, SR)

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "top10", "assets")
J = {}
SIDES = ("a", "b")


# ---------------------------------------------------------------- joueurs
def _silhouette(nba_id, h):
    """Buste noir cerclé de la couleur d'équipe, à partir de la photo officielle (fond transparent)."""
    import io, requests
    try:
        r = requests.get(f"https://cdn.nba.com/headshots/nba/latest/1040x760/{nba_id}.png", timeout=20)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        print("photo officielle indisponible :", e)
        return None


def player_img(P, h):
    """Image détourée du joueur : photo de top10/assets si fournie, sinon silhouette (photo officielle noircie)."""
    src, real = None, False
    if P.get("photo") and os.path.exists(os.path.join(ASSETS, P["photo"])):
        src, real = Image.open(os.path.join(ASSETS, P["photo"])).convert("RGBA"), True
    elif P.get("nba_id"):
        src = _silhouette(P["nba_id"], h)
    if src is None:
        return None
    a = src.getchannel("A").point(lambda v: 255 if v > 90 else 0)
    box = a.getbbox()
    if not box:
        return None
    src = src.crop(box); a = a.crop(box)
    k = h / src.height
    src = src.resize((max(1, int(src.width * k)), h), Image.LANCZOS); a = a.resize(src.size, Image.LANCZOS)
    col = tuple(P["color"])
    pad = 40
    A = Image.new("L", (src.width + 2 * pad, src.height + pad), 0); A.paste(a, (pad, pad))
    edge = A.filter(ImageFilter.MaxFilter(15))
    out = Image.new("RGBA", A.size, col + (0,)); out.putalpha(edge.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.95)))
    ring = Image.new("RGBA", A.size, col + (255,)); ring.putalpha(edge); out.alpha_composite(ring)
    if real and not P.get("silhouette"):
        body = Image.new("RGBA", A.size, (0, 0, 0, 0)); body.paste(src, (pad, pad), src)
    else:  # silhouette sombre teintée
        body = Image.new("RGBA", A.size, tuple(int(c * 0.18) + 8 for c in col) + (255,)); body.putalpha(A)
    out.alpha_composite(body)
    # fondu bas
    f = Image.new("L", out.size, 255); d = ImageDraw.Draw(f)
    for y in range(out.height):
        v = max(0.0, (y - out.height * 0.78) / (out.height * 0.22))
        d.line([0, y, out.width, y], fill=int(255 * (1 - min(1, v))))
    out.putalpha(Image.composite(out.getchannel("A"), Image.new("L", out.size, 0), f))
    return out


def dim(im, k):
    """Assombrit une image (perdant de la manche)."""
    if k >= 0.999:
        return im
    a = im.getchannel("A")
    rgb = Image.eval(im.convert("RGB"), lambda v: int(v * k))
    out = rgb.convert("RGBA"); out.putalpha(a)
    return out


# ---------------------------------------------------------------- minutage
class TL:
    def __init__(self, cues, total, order):
        self.c = {k: (a, b) for k, a, b in cues}
        self.total = total + 1.6
        self.span = {}
        hold = lambda k: 0.4 if k.startswith("r") or k == "E" else -0.12  # le gagnant reste affiché un peu plus
        for i, k in enumerate(order):
            a = 0.0 if i == 0 else self.c[k][0] + hold(k)
            b = self.c[order[i + 1]][0] + hold(order[i + 1]) if i + 1 < len(order) else self.total
            self.span[k] = (a, b)
        self.order = order

    def at(self, t):
        for k, (a, b) in self.span.items():
            if a <= t < b:
                return k, t - a, b - a
        return self.order[-1], t, 1


def win_times(T):
    """Instant où le gagnant de chaque manche est annoncé (≈ début de la dernière phrase de la manche)."""
    out = {}
    for i, R in enumerate(J["rounds"]):
        k = f"r{i}"
        a, b = T.c[k]
        txt = re.sub(r"\[[^\]]*\]", "", R["voice"]).strip()
        parts = re.split(r"(?<=[.…!?])\s+", txt)
        frac = 1 - len(parts[-1]) / max(1, len(txt)) if len(parts) > 1 else 0.7
        out[k] = a + (b - a) * frac  # instant réel dans la voix
    return out


def scores_at(t, WT):
    s = {"a": 0, "b": 0}
    for i, R in enumerate(J["rounds"]):
        if t >= WT[f"r{i}"] + 0.25:
            s[R["win"]] += 1
    return s


# ---------------------------------------------------------------- dessin
def _count(v, e):
    """Anime '43 500', '30,1', '6' ; préfixe éventuel ('+ de ') conservé."""
    m = re.fullmatch(r"(\D*?)(\d[\d ]*)(?:,(\d+))?(.*)", v)
    if not m:
        return v
    pre, ent, dec, post = m.group(1), m.group(2).replace(" ", ""), m.group(3), m.group(4)
    x = float(ent + "." + (dec or "0")) * e
    if dec:
        s = f"{x:.{len(dec)}f}".replace(".", ",")
    else:
        s = f"{int(round(x)):,}".replace(",", " ")
    return pre + s + post


def header(c, t, s, IM, k, p, WT, pulse):
    A, B = J["players"]["a"], J["players"]["b"]
    # bandeaux couleur d'équipe derrière les portraits
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon([(0, 150), (W / 2 + 40, 150), (W / 2 - 40, 840), (0, 840)], fill=tuple(A["color"]) + (70,))
    d.polygon([(W / 2 + 40, 150), (W, 150), (W, 840), (W / 2 - 40, 840)], fill=tuple(B["color"]) + (70,))
    c.alpha_composite(lay.filter(ImageFilter.GaussianBlur(3)))
    # portraits (le perdant de la manche s'assombrit)
    win = None
    if k.startswith("r"):
        i = int(k[1:])
        if t >= WT[k]:
            win = J["rounds"][i]["win"]
    for side, x in (("a", 280), ("b", 800)):
        im = IM.get(side)
        if im is None:
            continue
        kk = 1.0 if win in (None, side) else 0.35
        sc = 1.0 + (0.05 * ease_back(min(1, (t - WT.get(k, 1e9)) / 0.3)) if win == side else 0)
        blit(c, dim(im, kk), x, 840, anchor="mb", scale=sc)
    # plaques de nom
    for side, x in (("a", 225), ("b", 855)):
        P = J["players"][side]
        panel(c, [x - 165, 770, x + 165, 860], tuple(P["color"]) + (255,), 1, r=26)
        text(c, P["name"], "Black", 64, WHITE, x, 815, maxw=290)
    # score central
    panel(c, [W / 2 - 150, 700, W / 2 + 150, 880], (10, 10, 14, 245), 1, r=34, outline=(255, 255, 255, 60))
    for side, x in (("a", W / 2 - 70), ("b", W / 2 + 70)):
        z = 1 + 0.35 * pulse.get(side, 0)
        text(c, str(s[side]), "Black", 118, YEL if pulse.get(side, 0) > 0.05 else WHITE, x, 790, scale=z)
    text(c, "-", "Black", 90, SILVER, W / 2, 784)
    # progression des manches
    n = len(J["rounds"]); cur = int(k[1:]) if k.startswith("r") else (n if k == "E" else -1)
    for i in range(n):
        x = W / 2 + (i - (n - 1) / 2) * 46
        R = J["rounds"][i]
        done = i < cur or (i == cur and t >= WT[f"r{i}"] + 0.25)
        col = tuple(J["players"][R["win"]]["color"]) if done else ((255, 255, 255) if i == cur else (70, 70, 80))
        d = Image.new("RGBA", (34, 34), (0, 0, 0, 0)); ImageDraw.Draw(d).ellipse([2, 2, 31, 31], fill=col + (255,),
                                                                                   outline=(255, 255, 255, 200), width=3 if i == cur else 0)
        blit(c, d, x, 120)


def round_panel(c, i, p, d, t, WT):
    R = J["rounds"][i]
    k = f"r{i}"
    pin = ease_back(min(1, p / 0.35))
    text(c, f"MANCHE {i + 1}/{len(J['rounds'])}", "Black", 44, SILVER, W / 2, 950, alpha=min(1, p / 0.2))
    t0 = outlined(R["label"], "Black", 96, YEL, 10)
    blit(c, t0, W / 2, 1040, scale=(0.6 + 0.4 * pin) * min(1, 1000 / t0.width))
    e = ease_out((p - 0.4) / 0.8)
    won = t >= WT[k]
    va, vb = R["a"], R["b"]
    for side, x, v in (("a", 280, va), ("b", 800, vb)):
        col = tuple(J["players"][side]["color"])
        win = won and R["win"] == side
        lose = won and R["win"] != side
        b = ease_out((p - 0.35) / 0.3)
        panel(c, [x - 245, 1110, x + 245, 1300], (255, 255, 255, 34 if not win else 0), b * (0.5 if lose else 1), r=30)
        if win:
            panel(c, [x - 245, 1110, x + 245, 1300], col + (255,), b, r=30, outline=YEL + (255,))
        txt = _count(v, e) if R.get("count", True) else v
        text(c, txt, "Black", 112, WHITE, x, 1195, maxw=450, alpha=b * (0.45 if lose else 1),
             scale=1 + (0.12 * ease_back(min(1, (t - WT[k]) / 0.25)) if win else 0))
        if R.get("unit"):
            text(c, R["unit"], "Black", 40, SILVER, x, 1270, alpha=b * (0.45 if lose else 1), maxw=440)
        if win:
            cr = emoji("👑", 96)
            if cr is not None:
                blit(c, cr, x + 200, 1110, rot=-14, scale=0.6 + 0.4 * ease_back(min(1, (t - WT[k]) / 0.3)))
    if R.get("note"):
        text(c, R["note"], "Black", 46, YEL, W / 2, 1365, alpha=ease_out((p - 1.6) / 0.4), maxw=980)


def hook(c, p, IM):
    A, B = J["players"]["a"], J["players"]["b"]
    s = ease_out(p / 0.45)
    for side, x0, x in (("a", -500, 280), ("b", W + 500, 800)):
        im = IM.get(side)
        if im is not None:
            blit(c, im, x0 + (x - x0) * s, 1250, anchor="mb", scale=1.18 + 0.03 * p)
    shake = math.sin(p * 60) * 14 * max(0, 1 - (p - 0.45) / 0.3) if p > 0.45 else 0
    na = outlined(A["name"], "Black", 160, WHITE, 14, tuple(A["color"]))
    nb = outlined(B["name"], "Black", 160, WHITE, 14, tuple(B["color"]))
    blit(c, na, W / 2 - (1 - s) * 700, 250, scale=min(1, 980 / na.width))
    blit(c, nb, W / 2 + (1 - s) * 700, 690, scale=min(1, 980 / nb.width))
    vs = outlined("VS", "Black", 190, YEL, 14)
    blit(c, vs, W / 2 + shake, 470, scale=0.4 + 0.6 * ease_back(min(1, max(0, p - 0.4) / 0.3)), alpha=1 if p > 0.4 else 0)
    b = ease_out((p - 1.0) / 0.35)
    panel(c, [110, 1290, 970, 1410], (10, 10, 14, 235), b, r=32)
    text(c, J.get("hook_tag", "QUI EST LE GOAT ?"), "Black", 66, YEL, W / 2, 1350, alpha=b, maxw=820)


def ending(c, p, s, IM):
    for side, x in (("a", 280), ("b", 800)):
        im = IM.get(side)
        if im is not None:
            blit(c, im, x, 1260, anchor="mb", scale=1.1)
    A, B = J["players"]["a"], J["players"]["b"]
    z = 0.7 + 0.3 * ease_back(min(1, p / 0.4))
    panel(c, [W / 2 - 330, 200, W / 2 + 330, 520], (10, 10, 14, 245), 1, r=46, outline=YEL + (255,))
    text(c, str(s["a"]), "Black", 230, tuple(A["color"]) if max(A["color"]) > 120 else WHITE, W / 2 - 160, 360, scale=z)
    text(c, str(s["b"]), "Black", 230, WHITE, W / 2 + 160, 360, scale=z)
    text(c, "-", "Black", 160, SILVER, W / 2, 350, scale=z)
    v = J.get("verdict", "ÉGALITÉ !")
    vi = outlined(v, "Black", 150, YEL, 14)
    blit(c, vi, W / 2, 640, scale=min(1, 1000 / vi.width) * (0.8 + 0.2 * ease_back(min(1, max(0, p - 0.5) / 0.3))),
         alpha=1 if p > 0.5 else 0, rot=-3)
    b = ease_out((p - 1.6) / 0.4)
    panel(c, [90, 1290, 990, 1420], YEL + (255,), b, r=34)
    text(c, J.get("cta", "C'EST QUI LE GOAT ? 👇").replace(" 👇", ""), "Black", 70, (15, 15, 20), W / 2 - 50, 1355, alpha=b, maxw=700)
    e = emoji("👇", 74)
    if e is not None and b > 0:
        blit(c, e, 935, 1355 + 8 * math.sin(p * 8), alpha=b)


def frame(t, T, parts, groups, IM, WT):
    c = bg_at(t, parts)
    k, p, d = T.at(t)
    s = scores_at(t, WT)
    if k == "H":
        hook(c, p, IM)
    elif k == "E":
        ending(c, p, s, IM)
    else:
        i = int(k[1:])
        pulse = {}
        dt = t - (WT[k] + 0.25)
        if 0 <= dt < 0.6:
            pulse[J["rounds"][i]["win"]] = 1 - dt / 0.6
        header(c, t, s, IM, k, p, WT, pulse)
        round_panel(c, i, p, d, t, WT)
    captions(c, t, groups)
    return c.convert("RGB")


# ---------------------------------------------------------------- son
def clash():
    n = int(0.5 * SR); x = np.random.default_rng(7).normal(0, 1, n) * np.exp(-np.arange(n) / SR * 9)
    return x * 0.6 + _sine(80, 0.5, 6) * 0.9


def mix(voice_wav, T, WT, out_wav):
    with wave.open(voice_wav) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, w.getnchannels()).mean(1) / 32768
    n = int(T.total * SR); out = np.zeros(n, np.float32); out[:len(v)] += v[:n]

    def add(x, t, g):
        i = int(max(0, t) * SR); x = x[: max(0, n - i)]; out[i:i + len(x)] += x * g

    add(whoosh(0.4), 0.0, 0.14); add(clash(), 0.42, 0.22)
    for k, (a, b) in T.span.items():
        if k.startswith("r"):
            add(whoosh(), a - 0.1, 0.10)
            add(ding(), WT[k] + 0.2, 0.09)
    add(clash(), T.span["E"][0] + 0.05, 0.2); add(pop(), T.span["E"][0] + 0.55, 0.16)
    out = np.clip(out, -1, 1)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- miniature
def cover(IMC, out):
    A, B = J["players"]["a"], J["players"]["b"]
    c = Image.new("RGBA", (W, H), (8, 8, 12, 255))
    for side, pts in (("a", [(0, 0), (W / 2 + 120, 0), (W / 2 - 120, H), (0, H)]),
                      ("b", [(W / 2 + 120, 0), (W, 0), (W, H), (W / 2 - 120, H)])):
        col = tuple(J["players"][side]["color"])
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).polygon(pts, fill=col + (255,))
        g = Image.new("L", (1, H)); [g.putpixel((0, y), int(255 * (0.35 + 0.65 * min(1, y / 1400)))) for y in range(H)]
        lay.putalpha(Image.composite(lay.getchannel("A"), Image.new("L", (W, H), 0), g.resize((W, H))))
        c.alpha_composite(lay)
    c.alpha_composite(_rays((W, H), (W // 2, 1000), (255, 255, 255), alpha=26))
    for side, x in (("a", 290), ("b", 800)):
        im = IMC.get(side)
        if im is not None:
            blit(c, im, x, H + 20, anchor="mb")
    sh = Image.new("L", (1, H)); [sh.putpixel((0, y), int(235 * max(0, 1 - y / 900))) for y in range(H)]
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(sh.resize((W, H))); c.alpha_composite(dark)
    na = outlined(A["name"], "Black", 230, WHITE, 16, tuple(A["color"]))
    nb = outlined(B["name"], "Black", 230, WHITE, 16, tuple(B["color"]))
    blit(c, na, W / 2, 260, scale=min(1, 1000 / na.width), rot=-4)
    vs = outlined("VS", "Black", 170, YEL, 14); blit(c, vs, W / 2, 445, rot=-4)
    blit(c, nb, W / 2, 630, scale=min(1, 1000 / nb.width), rot=-4)
    tag = J.get("cover_tag", "QUI EST LE GOAT ?")
    ti = outlined(tag, "Black", 72, WHITE, 0)
    rib = Image.new("RGBA", (ti.width + 70, ti.height + 44), (235, 64, 52, 255)); rib.alpha_composite(ti, (35, 22))
    blit(c, rib, W / 2, 820, rot=3, scale=min(1, 940 / rib.width))
    e = emoji("🐐", 150)
    if e is not None:
        blit(c, e, 960, 790, rot=12)
    c.convert("RGB").save(out, quality=92)


# ---------------------------------------------------------------- principal
def load(path):
    global J
    J = json.load(open(path, encoding="utf-8"))
    return J


def run(episode, out_dir, queue_at=None):
    load(episode)
    os.makedirs(out_dir, exist_ok=True)
    order = ["H"] + [f"r{i}" for i in range(len(J["rounds"]))] + ["E"]
    segs = [("H", J["hook"])] + [(f"r{i}", R["voice"]) for i, R in enumerate(J["rounds"])] + [("E", J["outro"])]
    IM = {s: player_img(J["players"][s], 560) for s in SIDES}
    IMC = {s: player_img(J["players"][s], 1150) for s in SIDES}
    vw = os.path.join(out_dir, "voix.wav")
    cues, total = tts.synth(segs, vw)
    T = TL(cues, total, order)
    WT = win_times(T)
    groups = chunks(words_from_last())
    if not groups:  # mode test sans voix
        ws = []
        for k, a, b in cues:
            txt = re.sub(r"\[[^\]]*\]", "", dict(segs)[k]).split()
            for j, w_ in enumerate(txt):
                ws.append((w_, a + (b - a) * j / len(txt), a + (b - a) * (j + 1) / len(txt)))
        groups = chunks(ws)
    parts = build_bg(tuple(J["players"]["a"]["color"]))
    silent = os.path.join(out_dir, "video.mp4")
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-maxrate", "4M", "-bufsize", "8M",
                           "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i in range(int(T.total * FPS)):
        pr.stdin.write(frame(i / FPS, T, parts, groups, IM, WT).tobytes())
    pr.stdin.close(); pr.wait()
    aud = os.path.join(out_dir, "audio.wav"); mix(vw, T, WT, aud)
    final = os.path.join(out_dir, J["file"] + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", aud, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-shortest", final], check=True)
    cv = os.path.join(out_dir, J["file"] + ".jpg"); cover(IMC, cv)
    with open(os.path.join(out_dir, J["file"] + ".txt"), "w", encoding="utf-8") as f:
        f.write(J["caption"] + "\n\n" + " ".join(J["hashtags"]) + "\n")
    print("Vidéo :", final, f"{T.total:.1f}s")
    if queue_at:
        schedule(final, cv, queue_at)


def schedule(video, cover_path, at):
    """File de publication (Instagram + YouTube auto, brouillon TikTok) + aperçu Discord (❌ = annulation)."""
    from publish import queue
    from chiffre import discord_post
    tags = " ".join(J["hashtags"]); base = J["caption"]
    msg = (f"**⚔️ Duel : {J['players']['a']['name']} vs {J['players']['b']['name']}** — publication automatique le {at} "
           f"(Instagram + YouTube ; brouillon TikTok quelques heures avant). Mets ❌ sur ce message pour l'annuler.")
    mid = None
    if os.environ.get("DISCORD_BOT_TOKEN"):
        try:
            mid = discord_post.post(video, msg[:1900], cover_path)
        except Exception as ex:
            print("Aperçu Discord impossible :", ex)
            discord_post.notify(msg[:1800] + "\n(Vidéo trop lourde pour l'aperçu Discord.)")
    queue.add("duel_" + J["file"], video, cover_path, f"{base}\n\nAbonne-toi pour le prochain duel 🔔\n\n{tags}",
              f"{J['yt_title']} #Shorts", f"{base}\n\n#Shorts {tags}", at, mid, f"{base}\n\n{tags}")
    print("Programmé :", "duel_" + J["file"], at)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="out_duel"); ap.add_argument("--episode", required=True)
    ap.add_argument("--queue-at")
    a = ap.parse_args(); run(a.episode, a.out, a.queue_at)
