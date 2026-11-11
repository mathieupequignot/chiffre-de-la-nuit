"""Publication d'un Reel via l'API Instagram (connexion Instagram, graph.instagram.com)."""
import os
import time
import requests

def _base():
    """Jeton IGAA… (connexion Instagram) -> graph.instagram.com ; jeton EAA… (Facebook) -> graph.facebook.com."""
    tok = os.environ.get("IG_TOKEN", "").strip()
    host = "graph.facebook.com" if tok.startswith("EA") else "graph.instagram.com"
    return f"https://{host}/v23.0"


def enabled():
    return bool(os.environ.get("IG_TOKEN") and os.environ.get("IG_USER_ID"))


def already_posted(caption, hours=24):
    """Garde-fou anti-doublon : un post avec la même légende existe déjà dans les dernières 24 h ? -> son id."""
    import datetime as dt
    tok, uid = os.environ["IG_TOKEN"].strip(), os.environ["IG_USER_ID"].strip()
    try:
        j = requests.get(f"{_base()}/{uid}/media", params={"fields": "id,caption,timestamp", "limit": 15, "access_token": tok}, timeout=30).json()
        now = dt.datetime.now(dt.timezone.utc)
        for m in j.get("data", []):
            t = dt.datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
            if now - t < dt.timedelta(hours=hours) and (m.get("caption") or "").strip() == caption.strip():
                return m["id"]
    except Exception as e:
        print("contrôle anti-doublon Instagram impossible :", e)
    return None


def publish_reel(video_url, caption, cover_url=None):
    tok, uid = os.environ["IG_TOKEN"].strip(), os.environ["IG_USER_ID"].strip()
    G = _base()
    dup = already_posted(caption)
    if dup:
        print("Déjà publié sur Instagram (même légende) : pas de doublon.")
        return dup
    data = {"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true", "access_token": tok}
    if cover_url:
        data["cover_url"] = cover_url
    r = requests.post(f"{G}/{uid}/media", data=data, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram media: {r.status_code} {r.text[:300]}")
    cid = r.json()["id"]
    for _ in range(60):  # traitement de la vidéo par Instagram (jusqu'à ~10 min)
        s = requests.get(f"{G}/{cid}", params={"fields": "status_code,status", "access_token": tok}, timeout=30).json()
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram a refusé la vidéo : {s}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram n'a pas fini de traiter la vidéo à temps")
    r = requests.post(f"{G}/{uid}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram publish: {r.status_code} {r.text[:300]}")
    return r.json()["id"]


def refresh_token():
    """Prolonge le jeton longue durée (60 jours). Renvoie (jeton, secondes restantes)."""
    if os.environ["IG_TOKEN"].strip().startswith("EA"):
        return os.environ["IG_TOKEN"].strip(), None  # jeton Facebook système : pas de rafraîchissement
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": os.environ["IG_TOKEN"]}, timeout=30)
    r.raise_for_status()
    j = r.json()
    return j["access_token"], j.get("expires_in")
