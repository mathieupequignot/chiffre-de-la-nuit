"""Dépose une vidéo dans les brouillons TikTok (Content Posting API, mode « Upload » / scope video.upload).
La description et la couverture s'ajoutent ensuite dans l'appli TikTok (l'API ne les accepte pas en mode brouillon).
Envoi du fichier directement (FILE_UPLOAD) : pas besoin de vérifier un nom de domaine chez TikTok."""
import os
import subprocess
import time
import requests

API = "https://open.tiktokapis.com/v2"
REDIRECT = "https://mathieupequignot.github.io/chiffre-de-la-nuit/callback.html"
# Le jeton de rafraîchissement TikTok change à chaque utilisation : on le garde chiffré dans le dépôt
# (clé = TT_CLIENT_SECRET) et les workflows le recommitent après chaque usage.
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tt_token.enc")


def _openssl(args, data):
    env = {**os.environ, "TTK": os.environ["TT_CLIENT_SECRET"].strip()}
    return subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-a", "-A", *args, "-pass", "env:TTK"],
                          input=data, capture_output=True, check=True, env=env).stdout


def _load_refresh():
    if os.environ.get("TT_REFRESH_TOKEN"):
        return os.environ["TT_REFRESH_TOKEN"].strip()
    return _openssl(["-d"], open(TOKEN_FILE, "rb").read()).decode().strip()


def _save_refresh(tok):
    open(TOKEN_FILE, "wb").write(_openssl([], tok.encode()))


def enabled():
    return bool(os.environ.get("TT_CLIENT_KEY") and os.environ.get("TT_CLIENT_SECRET")
                and (os.environ.get("TT_REFRESH_TOKEN") or os.path.exists(TOKEN_FILE)))


def _token(data):
    r = requests.post(f"{API}/oauth/token/", timeout=30, headers={"Content-Type": "application/x-www-form-urlencoded"},
                      data={"client_key": os.environ["TT_CLIENT_KEY"].strip(),
                            "client_secret": os.environ["TT_CLIENT_SECRET"].strip(), **data})
    j = r.json()
    if "access_token" not in j:
        raise RuntimeError(f"TikTok refuse le jeton : {r.status_code} {j.get('error')} {j.get('error_description')}")
    if j.get("refresh_token"):
        _save_refresh(j["refresh_token"])
    return j["access_token"]


def exchange(code):
    """Première connexion : échange le code reçu sur callback.html contre les jetons."""
    tok = _token({"grant_type": "authorization_code", "code": code.strip(), "redirect_uri": REDIRECT})
    u = requests.get(f"{API}/user/info/", params={"fields": "display_name"},
                     headers={"Authorization": f"Bearer {tok}"}, timeout=30).json()
    return u.get("data", {}).get("user", {}).get("display_name")


def _access_token():
    return _token({"grant_type": "refresh_token", "refresh_token": _load_refresh()})


def upload_draft(video_path):
    tok = _access_token()
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
    size = os.path.getsize(video_path)
    r = requests.post(f"{API}/post/publish/inbox/video/init/", headers=h, timeout=60, json={
        "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}})
    j = r.json()
    if j.get("error", {}).get("code") not in ("ok", None):
        raise RuntimeError(f"TikTok init : {j}")
    pid, url = j["data"]["publish_id"], j["data"]["upload_url"]
    with open(video_path, "rb") as f:
        up = requests.put(url, data=f, timeout=600, headers={
            "Content-Type": "video/mp4", "Content-Length": str(size), "Content-Range": f"bytes 0-{size - 1}/{size}"})
    if up.status_code >= 300:
        raise RuntimeError(f"TikTok envoi : {up.status_code} {up.text[:300]}")
    for _ in range(30):
        s = requests.post(f"{API}/post/publish/status/fetch/", headers=h, json={"publish_id": pid}, timeout=30).json()
        st = s.get("data", {}).get("status")
        if st in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"):
            return pid
        if st == "FAILED":
            raise RuntimeError(f"TikTok a refusé la vidéo : {s}")
        time.sleep(10)
    return pid
