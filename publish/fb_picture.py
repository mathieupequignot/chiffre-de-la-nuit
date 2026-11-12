"""Copie la photo de profil Instagram (@nbadailynews0) sur la Page Facebook NBA Daily News."""
import os, requests
from publish.instagram import _base
from publish import facebook as F
ig = requests.get(f"{_base()}/{os.environ['IG_USER_ID'].strip()}", params={"fields": "profile_picture_url", "access_token": os.environ["IG_TOKEN"].strip()}, timeout=30).json()
url = ig.get("profile_picture_url")
print("photo Instagram trouvée :", bool(url))
if not url:  # repli : via le token de Page
    ig = requests.get(f"{F.G}/17841467952496168", params={"fields": "profile_picture_url", "access_token": F._tok()}, timeout=30).json(); url = ig.get("profile_picture_url")
    print("photo via token de Page :", bool(url), ig.get("error", {}).get("message"))
r = requests.post(f"{F.G}/{F.PAGE_ID}/picture", data={"picture": url, "access_token": F._tok()}, timeout=60)
print("Facebook :", r.status_code, r.text[:300])
r.raise_for_status()
