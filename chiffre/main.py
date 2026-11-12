"""Point d'entrée : python -m chiffre.main [--date AAAA-MM-JJ] [--fixture chemin.json] [--no-post]"""
import argparse
import datetime as dt
import os
import subprocess
import sys
import traceback
from zoneinfo import ZoneInfo

from . import data, pick, tts, render, discord_post, cover

HERE = os.path.dirname(os.path.abspath(__file__))
SFX_GAIN = 0.5  # volume global des effets sonores (1.0 = niveau des premières vidéos)


def mix(video, voice, TL, out):
    sfxdir = os.path.join(os.path.dirname(out), "sfx")
    if not os.path.exists(os.path.join(sfxdir, "pop.wav")):
        subprocess.run([sys.executable, os.path.join(HERE, "sfx.py"), sfxdir, "2.9"], check=True)
    fx = []
    for sc, (a, b) in TL.S.items():
        if sc != next(iter(TL.S)):
            fx.append(("whoosh", max(0, a - 0.2), 0.35))
    if "H" in TL.S: fx.append(("hit", 0.05, 0.4))
    for a, _ in TL.sub.get("A", [])[:4]:
        fx.append(("hit", max(0.02, a), 0.3))
    if "B" in TL.S: fx.append(("hit", TL.at("B", 0.5), 0.45))
    if "C" in TL.S: fx.append(("hit", TL.at("C", 0.5), 0.3))
    if "D" in TL.S: fx.append(("hit", TL.at("D", 0.6), 0.45))
    if "E" in TL.S: fx += [("hit", TL.at("E", 0.35), 0.3), ("hit", TL.at("E", 0.62), 0.3)]
    if "G" in TL.S: fx.append(("pop", TL.S["G"][0] + 0.25, 0.5))
    inputs = ["-i", video, "-i", voice]
    f = [f"[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,apad=whole_dur={TL.total:.2f}[v]"]
    m = ["[v]"]
    for j, (n, t, g) in enumerate(fx):
        inputs += ["-i", os.path.join(sfxdir, n + ".wav")]
        f.append(f"[{j + 2}:a]volume={g * SFX_GAIN:.3f},adelay={int(t * 1000)}:all=1[f{j}]"); m.append(f"[f{j}]")
    f.append("".join(m) + f"amix=inputs={len(m)}:normalize=0:duration=first,alimiter=limit=0.89[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(f), "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{TL.total:.2f}", "-movflags", "+faststart", out], check=True)


def make_part(D, segs, outdir, name):
    """Voix + animation + effets sonores d'une perf. Renvoie (mp4, durée de la voix)."""
    print("Texte :", " ".join(t for _, t in segs))
    voice = os.path.join(outdir, f"voice_{name}.wav")
    cues, total = tts.synth(segs, voice)
    silent = os.path.join(outdir, f"video_silent_{name}.mp4")
    TL = render.render(D, cues, total, silent)
    out = os.path.join(outdir, f"part_{name}.mp4")
    mix(silent, voice, TL, out)
    return out, total


def concat(part1, voice1, part2, out):
    """Enchaîne les deux perfs du combo (1re partie coupée 0,5 s après la fin de la voix)."""
    t1 = voice1 + 0.5
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", part1, "-i", part2, "-filter_complex",
                    f"[0:v]trim=0:{t1:.2f},setpts=PTS-STARTPTS[v0];[0:a]atrim=0:{t1:.2f},asetpts=PTS-STARTPTS[a0];"
                    "[v0][a0][1:v][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-maxrate", "1500k", "-bufsize", "3M",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)


def run(day, fixture=None, post=True, outdir="out"):
    os.makedirs(outdir, exist_ok=True)
    if not fixture and os.environ.get("CHIFFRE_EARLY") == "1":
        try:
            n = data.unfinished(day)
        except Exception as e:
            n = 0; print("contrôle des matchs en cours impossible :", e)
        if n:
            print(f"Passage anticipé : {n} match(s) encore en cours, on laisse le passage suivant faire le chiffre.")
            return None
    games = data.load_fixture(fixture) if fixture else data.fetch_night(day)
    if not games:
        print("Aucun match terminé cette nuit.")
        if post and os.environ.get("DISCORD_BOT_TOKEN"):
            discord_post.notify("😴 Pas de match NBA cette nuit : pas de chiffre de la nuit aujourd'hui. Rendez-vous demain matin !")
        return None
    # (record de la saison : indisponible avec l'offre gratuite d'API-NBA -> pas de contexte pour l'instant)
    final = os.path.join(outdir, f"chiffre_de_la_nuit_{day.isoformat()}.mp4")
    combo = None
    try:
        combo = pick.build_combo(games, day)
    except Exception as e:  # le combo est un bonus : en cas de souci on retombe sur la vidéo classique
        print("combo ignoré :", e)
    if combo:
        D, s1, D2, s2, caption = combo
        print("COMBO :", D["last"], "+", D2["last"])
        part1, d1 = make_part(D, s1, outdir, "p1")
        part2, _ = make_part(D2, s2, outdir, "p2")
        concat(part1, d1, part2, final)
    else:
        built = pick.build(games, day)
        if not built:
            print("Pas de joueur exploitable.")
            return None
        D, segs, caption = built
        part, _ = make_part(D, segs, outdir, "solo")
        os.replace(part, final)
    thumb = cover.from_D(D, os.path.join(outdir, f"miniature_{day.isoformat()}.jpg"))
    auto = post and os.environ.get("AUTO_PUBLISH") == "1"
    if auto:
        msg = (f"**Le chiffre de la nuit — {D['date_label'].lower()}**\n"
               f"📸 Instagram + ▶️ YouTube : publication automatique à 8h00.\n"
               f"🎵 TikTok : la vidéo arrive dans tes brouillons ; description à copier dans le message suivant 👇")
    else:
        msg = (f"**Le chiffre de la nuit — {D['date_label'].lower()}**\n\n"
           f"🎵 **TikTok** (légende + hashtags) :\n```{caption['tiktok']}```\n"
           f"📸 **Instagram** :\n```{caption['instagram']}```\n"
           f"🖼️ Miniature jointe : à choisir dans « Modifier la couverture » → Importer.\n\n"
           f"▶️ **YouTube Shorts** — titre :\n```{caption['youtube_title']}```\ndescription :\n```{caption['youtube']}```")
    open(os.path.join(outdir, "caption.txt"), "w", encoding="utf-8").write(msg)
    print("Vidéo :", final)
    mid = None
    if post and os.environ.get("DISCORD_BOT_TOKEN"):
        mid = discord_post.post(final, msg, thumb, caption["tiktok"] if auto else None)
    if post and os.environ.get("AUTO_PUBLISH") == "1":
        from publish import queue
        queue.add(f"chiffre_{day.isoformat()}", final, thumb, caption["instagram"], caption["youtube_title"],
                  caption["youtube"], "08:00", mid)
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="jour (heure de Paris) au matin duquel on publie, AAAA-MM-JJ")
    ap.add_argument("--fixture")
    ap.add_argument("--no-post", action="store_true")
    a = ap.parse_args()
    day = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(ZoneInfo("Europe/Paris")).date()
    try:
        run(day, a.fixture, not a.no_post)
    except Exception:
        err = traceback.format_exc()
        print(err)
        discord_post.notify(f"⚠️ Le chiffre de la nuit n'a pas pu être généré aujourd'hui.\n```{err[-1500:]}```")
        sys.exit(1)
