"""File d'attente des publications automatiques (Instagram, YouTube).
Chaque vidéo produite est copiée dans docs/media/ (servi par GitHub Pages, donc accessible publiquement
par Instagram) et ajoutée à publish/queue.json avec son heure de publication."""
import datetime as dt
import json
import os
import shutil
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "publish", "queue.json")
MEDIA = os.path.join(ROOT, "docs", "media")
PAGES = os.environ.get("PAGES_URL", "https://mathieupequignot.github.io/chiffre-de-la-nuit")
PARIS = ZoneInfo("Europe/Paris")


def load():
    return json.load(open(QUEUE, encoding="utf-8")) if os.path.exists(QUEUE) else []


def save(q):
    json.dump(q, open(QUEUE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def add(key, video, cover, instagram, yt_title, yt_desc, at_paris, discord_mid=None, tiktok_caption=None, platforms=None):
    """at_paris : 'HH:MM' (aujourd'hui) ou 'AAAA-MM-JJ HH:MM' (heure de Paris). Heure passée = publication au prochain passage.
    tiktok_caption : description TikTok envoyée sur Discord quand le brouillon arrive (vidéos programmées à l'avance).
    platforms : liste des plateformes visées (ex. ["facebook"]) ; None = toutes."""
    os.makedirs(MEDIA, exist_ok=True)
    v = f"{key}.mp4"; shutil.copy(video, os.path.join(MEDIA, v))
    c = None
    if cover and os.path.exists(cover):
        c = f"{key}.jpg"; shutil.copy(cover, os.path.join(MEDIA, c))
    day = dt.datetime.now(PARIS)
    if " " in at_paris:
        d, at_paris = at_paris.split(" ")
        day = day.replace(**dict(zip(("year", "month", "day"), map(int, d.split("-")))))
    h, m = map(int, at_paris.split(":"))
    at = day.replace(hour=h, minute=m, second=0, microsecond=0)
    q = [e for e in load() if e["key"] != key]
    q.append(dict(key=key, video=v, cover=c, instagram=instagram, yt_title=yt_title[:100], yt_desc=yt_desc,
                  at=at.isoformat(), discord_mid=discord_mid, status={}, tiktok_caption=tiktok_caption,
                  **({"platforms": platforms} if platforms else {})))
    save(q)


def url(name):
    return f"{PAGES}/media/{name}"
