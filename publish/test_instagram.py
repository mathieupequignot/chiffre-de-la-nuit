"""Vérifie le jeton Instagram sans rien publier : nom du compte + quota de publication."""
import os
import requests
from publish.instagram import _base

tok, uid = os.environ["IG_TOKEN"].strip(), os.environ["IG_USER_ID"].strip()
G = _base()
print("Type de jeton :", "Facebook (EAA)" if tok.startswith("EA") else "Instagram (IGAA)" if tok.startswith("IG") else "inconnu")
print("API :", G)
r = requests.get(f"{G}/{uid}", params={"fields": "username,media_count", "access_token": tok}, timeout=30)
print("Compte :", r.status_code, r.text[:300])
r2 = requests.get(f"{G}/{uid}/content_publishing_limit", params={"fields": "quota_usage,config", "access_token": tok}, timeout=30)
print("Quota :", r2.status_code, r2.text[:300])
r.raise_for_status()
r2.raise_for_status()
print("OK : le jeton peut publier sur @" + r.json().get("username", "?"))
