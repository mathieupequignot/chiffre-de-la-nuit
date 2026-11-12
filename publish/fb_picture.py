"""Récupère la photo de profil Instagram (@nbadailynews0) dans docs/avatar.jpg (pour la Page Facebook)."""
import os, requests
from publish.instagram import _base
ig = requests.get(f"{_base()}/{os.environ['IG_USER_ID'].strip()}", params={"fields": "profile_picture_url", "access_token": os.environ["IG_TOKEN"].strip()}, timeout=30).json()
img = requests.get(ig["profile_picture_url"], timeout=60); img.raise_for_status()
open("docs/avatar.jpg", "wb").write(img.content); print("avatar", len(img.content), "octets")
