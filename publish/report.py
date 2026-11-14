"""Rapport du soir : vues de chaque vidéo publiée la veille, réseau par réseau, envoyé sur Discord (image + résumé).
python -m publish.report [--date AAAA-MM-JJ] [--no-post]
Chaque réseau est facultatif : s'il ne répond pas, sa colonne affiche « – » et le rapport part quand même."""
import argparse
import datetime as dt
import json
import os
import re
from zoneinfo import ZoneInfo

import requests

PARIS = ZoneInfo("Europe/Paris")
G = "https://graph.facebook.com/v23.0"
HERE = os.path.dirname(os.path.abspath(__file__))
NETS = [("tiktok", "TikTok"), ("instagram", "Insta"), ("youtube", "YouTube"), ("facebook", "Facebook")]
KIND = [("chiffre_", "Chiffre de la nuit"), ("quiz_", "Quiz"), ("top5_", "5 trucs fous"), ("duel_", "Duel"),
        ("drill_", "Drill"), ("saviez_", "Le savais-tu"), ("top10_", "10 trucs fous")]


# ---------- vues par réseau (None = indisponible)
def ig_views(mid):
    tok = os.environ.get("IG_TOKEN", "").strip()
    if not (tok and mid):
        return None
    for metric in ("views", "plays"):
        j = requests.get(f"{G}/{mid}/insights", params={"metric": metric, "access_token": tok}, timeout=30).json()
        if j.get("data"):
            return int(j["data"][0]["values"][0]["value"])
    print("Instagram", mid, j.get("error", {}).get("message"))
    return None


def fb_views(vid):
    tok = os.environ.get("FB_PAGE_TOKEN", "").strip()
    if not (tok and vid):
        return None
    j = requests.get(f"{G}/{vid}/video_insights", params={"metric": "blue_reels_play_count,fb_reels_total_plays",
                                                          "access_token": tok}, timeout=30).json()
    vals = {d["name"]: d["values"][0]["value"] for d in j.get("data", []) if d.get("values")}
    for k in ("blue_reels_play_count", "fb_reels_total_plays"):
        if k in vals:
            return int(vals[k])
    j2 = requests.get(f"{G}/{vid}", params={"fields": "views", "access_token": tok}, timeout=30).json()
    if "views" in j2:
        return int(j2["views"])
    print("Facebook", vid, j.get("error", {}).get("message"), j2.get("error", {}).get("message"))
    return None


def yt_views(ids):
    ids = [i for i in ids if i]
    if not ids:
        return {}
    try:
        from publish import youtube
        h = {"Authorization": f"Bearer {youtube._access_token()}"}
        j = requests.get("https://www.googleapis.com/youtube/v3/videos", headers=h,
                         params={"part": "statistics", "id": ",".join(ids[:50])}, timeout=30).json()
        if "error" in j:
            print("YouTube :", j["error"].get("message")); return {}
        return {it["id"]: int(it["statistics"].get("viewCount", 0)) for it in j.get("items", [])}
    except Exception as e:
        print("YouTube :", e); return {}


def tt_videos(day):
    """Vidéos TikTok publiées ce jour-là (nécessite le droit video.list ; activé avec TT_STATS=1)."""
    if os.environ.get("TT_STATS") != "1":
        return None
    try:
        from publish import tiktok
        h = {"Authorization": f"Bearer {tiktok._access_token()}", "Content-Type": "application/json"}
        out, cursor = [], None
        for _ in range(5):
            body = {"max_count": 20, **({"cursor": cursor} if cursor else {})}
            j = requests.post("https://open.tiktokapis.com/v2/video/list/?fields=id,title,video_description,create_time,view_count",
                              headers=h, json=body, timeout=30).json()
            if j.get("error", {}).get("code") not in (None, "ok"):
                print("TikTok :", j["error"]); return None
            vids = j.get("data", {}).get("videos", [])
            out += vids
            if not j["data"].get("has_more") or not vids or min(v["create_time"] for v in vids) < day_start(day).timestamp():
                break
            cursor = j["data"].get("cursor")
        a, b = day_start(day).timestamp(), day_start(day + dt.timedelta(days=1)).timestamp()
        return [v for v in out if a <= v["create_time"] < b]
    except Exception as e:
        print("TikTok :", e); return None


def day_start(d):
    return dt.datetime(d.year, d.month, d.day, tzinfo=PARIS)


def _words(t):
    return set(re.findall(r"[a-zà-ÿ0-9]{4,}", (t or "").lower()))


# ---------- rapport
def label(e):
    kind = next((n for p, n in KIND if e["key"].startswith(p)), e["key"].split("_")[0])
    t = re.sub(r"\s*#\w+", "", e.get("yt_title") or "").replace("🤯", "").strip()
    if not t:
        t = (e.get("instagram") or "").split("\n")[0]
    return kind, t[:60]


def collect(day):
    q = json.load(open(os.path.join(HERE, "queue.json"), encoding="utf-8"))
    rows = []
    for e in q:
        at = dt.datetime.fromisoformat(e["at"]).astimezone(PARIS)
        if at.date() != day:
            continue
        if not any(v == "ok" for v in e.get("status", {}).values()):
            continue
        kind, title = label(e)
        rows.append(dict(e=e, at=at, kind=kind, title=title, ids=e.get("ids", {}), v={}))
    rows.sort(key=lambda r: r["at"])
    yt = yt_views([r["ids"].get("youtube") for r in rows])
    tt = tt_videos(day)
    for r in rows:
        st, ids = r["e"].get("status", {}), r["ids"]
        r["v"]["instagram"] = ig_views(ids.get("instagram")) if st.get("instagram") == "ok" else "×"
        r["v"]["facebook"] = fb_views(ids.get("facebook")) if st.get("facebook") == "ok" else "×"
        r["v"]["youtube"] = yt.get(ids.get("youtube")) if st.get("youtube") == "ok" else "×"
        if st.get("tiktok") != "ok":
            r["v"]["tiktok"] = "×"
        elif tt is None:
            r["v"]["tiktok"] = None
        else:   # brouillon publié à la main : on retrouve la vidéo par sa description
            ref = _words(r["e"].get("tiktok_caption") or r["e"].get("instagram"))
            best = max(tt, key=lambda v: len(ref & _words(v.get("video_description") or v.get("title"))), default=None)
            ok = best and len(ref & _words(best.get("video_description") or best.get("title"))) >= 3
            r["v"]["tiktok"] = int(best["view_count"]) if ok else "?"
            if ok:
                tt.remove(best)
    return rows, tt


def fmt(n):
    if n is None: return "–"
    if isinstance(n, str): return n
    if n >= 10000: return f"{n / 1000:.0f}k".replace(".", ",")
    if n >= 1000: return f"{n / 1000:.1f}k".replace(".", ",")
    return str(n)


def image(day, rows, out):
    from PIL import Image, ImageDraw
    from chiffre.render import font
    W, PAD, RH = 1080, 40, 118
    H = 260 + RH * (len(rows) + 1) + 120
    im = Image.new("RGB", (W, H), (14, 14, 18)); d = ImageDraw.Draw(im)
    OR, WH, GR, GN = (255, 122, 26), (245, 245, 245), (140, 142, 152), (80, 220, 120)
    d.text((PAD, 50), "RAPPORT DES VUES", font=font("Black", 64), fill=OR)
    d.text((PAD, 130), f"Vidéos du {day.strftime('%d/%m/%Y')} · relevé le {dt.datetime.now(PARIS).strftime('%d/%m à %Hh%M')}",
           font=font("SemiBold", 30), fill=GR)
    cols = [560, 690, 820, 950]   # centres des colonnes réseaux
    y = 210
    for (k, n), x in zip(NETS, cols):
        d.text((x, y + 20), n, font=font("ExtraBold", 28), fill=GR, anchor="mm")
    y += 60
    tot = {k: 0 for k, _ in NETS}
    for i, r in enumerate(rows):
        if i % 2 == 0:
            d.rounded_rectangle([PAD - 10, y, W - PAD + 10, y + RH - 10], 18, fill=(24, 24, 30))
        d.text((PAD + 6, y + 14), f"{r['at'].strftime('%Hh%M')} · {r['kind'].upper()}", font=font("ExtraBold", 26), fill=OR)
        t = r["title"]
        while font("SemiBold", 30).getlength(t) > 470 and len(t) > 5: t = t[:-2]
        d.text((PAD + 6, y + 54), t if t == r["title"] else t.rstrip() + "…", font=font("SemiBold", 30), fill=WH)
        best = max([v for v in r["v"].values() if isinstance(v, int)], default=None)
        for (k, _), x in zip(NETS, cols):
            v = r["v"].get(k)
            if isinstance(v, int): tot[k] += v
            d.text((x, y + RH / 2 - 5), fmt(v), font=font("Black", 38), fill=GN if v == best and best else WH, anchor="mm")
        y += RH
    d.line([PAD, y + 5, W - PAD, y + 5], fill=(60, 60, 70), width=3)
    d.text((PAD + 6, y + 50), "TOTAL", font=font("Black", 40), fill=OR, anchor="lm")
    for (k, _), x in zip(NETS, cols):
        has = any(isinstance(r["v"].get(k), int) for r in rows)
        d.text((x, y + 50), fmt(tot[k]) if has else "–", font=font("Black", 40), fill=OR, anchor="mm")
    im.save(out, quality=92)
    return out, tot


def summary(day, rows, tot, extra_tt):
    if not rows:
        return f"📊 **Rapport du {day.strftime('%d/%m')}** : aucune vidéo publiée ce jour-là."
    allv = sum(v for v in tot.values())
    best = max(rows, key=lambda r: sum(v for v in r["v"].values() if isinstance(v, int)))
    bv = sum(v for v in best["v"].values() if isinstance(v, int))
    by_net = max(((k, n) for k, n in NETS), key=lambda kn: tot[kn[0]])
    sp = lambda n: f"{n:,}".replace(",", " ")
    lines = [f"📊 **Rapport du {day.strftime('%d/%m')}** — {len(rows)} vidéos, **{sp(allv)} vues** au total"]
    if allv:
        lines += [f"🏆 Meilleure vidéo : {best['kind']} — {best['title']} ({sp(bv)} vues)",
                  f"📱 Meilleur réseau : {by_net[1]} ({sp(tot[by_net[0]])} vues)"]
    if any(r["v"].get("tiktok") is None for r in rows):
        lines.append("ℹ️ TikTok : vues pas encore accessibles par l'API (droit « video.list » à activer).")
    if extra_tt:
        lines.append("TikTok, autres vidéos du jour : " + " · ".join(f"{(v.get('title') or '')[:30]} ({fmt(v['view_count'])})" for v in extra_tt[:5]))
    lines.append("« × » = pas publiée sur ce réseau · « – » = chiffre indisponible")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date"); ap.add_argument("--no-post", action="store_true")
    a = ap.parse_args()
    day = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(PARIS).date() - dt.timedelta(days=1)
    rows, extra = collect(day)
    os.makedirs("out_report", exist_ok=True)
    png, tot = image(day, rows, f"out_report/rapport_{day}.jpg")
    msg = summary(day, rows, tot, extra)
    print(msg)
    for r in rows: print(r["kind"], r["title"], r["v"])
    if not a.no_post:
        from chiffre import discord_post
        if rows:
            discord_post.notify_file(msg, png, f"rapport_{day}.jpg")
        else:
            discord_post.notify(msg)


if __name__ == "__main__":
    main()
