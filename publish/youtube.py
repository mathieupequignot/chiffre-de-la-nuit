"""Envoi d'un Short sur YouTube (API YouTube Data v3, OAuth avec jeton de rafraîchissement)."""
import json
import os
import requests


def enabled():
    return all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))


def _access_token():
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": os.environ["YT_CLIENT_ID"].strip(), "client_secret": os.environ["YT_CLIENT_SECRET"].strip(),
        "refresh_token": os.environ["YT_REFRESH_TOKEN"].strip(), "grant_type": "refresh_token"})
    if not r.ok:
        raise RuntimeError(f"Google refuse le jeton : {r.status_code} {r.json().get('error')} — {r.json().get('error_description')}")
    return r.json()["access_token"]


def upload(video_path, title, description, cover_path=None):
    tok = _access_token()
    h = {"Authorization": f"Bearer {tok}"}
    meta = {"snippet": {"title": title[:100], "description": description, "categoryId": "17",
                        "tags": ["NBA", "basket", "Shorts"], "defaultLanguage": "fr"},
            "status": {"privacyStatus": os.environ.get("YT_PRIVACY", "public"), "selfDeclaredMadeForKids": False}}
    size = os.path.getsize(video_path)
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                      headers={**h, "Content-Type": "application/json; charset=UTF-8",
                               "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
                      data=json.dumps(meta), timeout=60)
    r.raise_for_status()
    with open(video_path, "rb") as f:
        up = requests.put(r.headers["Location"], headers={**h, "Content-Type": "video/mp4"}, data=f, timeout=600)
    up.raise_for_status()
    vid = up.json()["id"]
    if cover_path and os.path.exists(cover_path):  # nécessite une chaîne validée par téléphone ; sinon on ignore
        try:
            with open(cover_path, "rb") as f:
                requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                              headers={**h, "Content-Type": "image/jpeg"}, data=f, timeout=60).raise_for_status()
        except Exception as e:
            print("miniature YouTube non appliquée :", e)
    return vid
