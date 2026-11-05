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


def add(key, video, cover, instagram, yt_title, yt_desc, at_paris, discord_mid=None):
    """at_paris : 'HH:MM' (aujourd'hui, heure de Paris). Si l'heure est déjà passée, publication au prochain passage."""
    os.makedirs(MEDIA, exist_ok=True)
    v = f"{key}.mp4"; shutil.copy(video, os.path.join(MEDIA, v))
    c = None
    if cover and os.path.exists(cover):
        c = f"{key}.jpg"; shutil.copy(cover, os.path.join(MEDIA, c))
    h, m = map(int, at_paris.split(":"))
    at = dt.datetime.now(PARIS).replace(hour=h, minute=m, second=0, microsecond=0)
    q = [e for e in load() if e["key"] != key]
    q.append(dict(key=key, video=v, cover=c, instagram=instagram, yt_title=yt_title[:100], yt_desc=yt_desc,
                  at=at.isoformat(), discord_mid=discord_mid, status={}))
    save(q)


def url(name):
    return f"{PAGES}/media/{name}"
