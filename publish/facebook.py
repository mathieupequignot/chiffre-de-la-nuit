"""Publication d'un Reel sur la Page Facebook NBA Daily News (API Pages, token de Page permanent)."""
import datetime as dt
import os
import time
import requests

G = "https://graph.facebook.com/v23.0"
PAGE_ID = os.environ.get("FB_PAGE_ID", "1407079352494032")


def enabled():
    return bool(os.environ.get("FB_PAGE_TOKEN", "").strip())


def _tok():
    return os.environ["FB_PAGE_TOKEN"].strip()


def already_posted(caption, hours=24):
    """Garde-fou anti-doublon : un Reel avec la même description dans les dernières 24 h ? -> son id."""
    try:
        j = requests.get(f"{G}/{PAGE_ID}/video_reels", params={"fields": "id,description,created_time", "limit": 15,
                                                                "access_token": _tok()}, timeout=30).json()
        now = dt.datetime.now(dt.timezone.utc)
        for v in j.get("data", []):
            t = dt.datetime.strptime(v["created_time"], "%Y-%m-%dT%H:%M:%S%z")
            if now - t < dt.timedelta(hours=hours) and (v.get("description") or "").strip() == caption.strip():
                return v["id"]
    except Exception as e:
        print("contrôle anti-doublon Facebook impossible :", e)
    return None


def publish_reel(video_url, caption):
    dup = already_posted(caption)
    if dup:
        print("Déjà publié sur Facebook (même description) : pas de doublon.")
        return dup
    tok = _tok()
    r = requests.post(f"{G}/{PAGE_ID}/video_reels", data={"upload_phase": "start", "access_token": tok}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Facebook start: {r.status_code} {r.text[:300]}")
    vid = r.json()["video_id"]
    r = requests.post(f"https://rupload.facebook.com/video-upload/v23.0/{vid}",
                      headers={"Authorization": f"OAuth {tok}", "file_url": video_url}, timeout=120)
    if not r.ok:
        raise RuntimeError(f"Facebook upload: {r.status_code} {r.text[:300]}")
    r = requests.post(f"{G}/{PAGE_ID}/video_reels", data={"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
                                                         "description": caption, "access_token": tok}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Facebook finish: {r.status_code} {r.text[:300]}")
    for _ in range(60):  # traitement (jusqu'à ~10 min)
        s = requests.get(f"{G}/{vid}", params={"fields": "status", "access_token": tok}, timeout=30).json().get("status", {})
        if s.get("video_status") in ("ready", "published") or s.get("publishing_phase", {}).get("status") == "complete":
            return vid
        if s.get("video_status") == "error" or "error" in str(s.get("processing_phase", {}).get("status", "")):
            raise RuntimeError(f"Facebook a refusé la vidéo : {s}")
        time.sleep(10)
    return vid  # encore en traitement : Facebook le publiera à la fin
