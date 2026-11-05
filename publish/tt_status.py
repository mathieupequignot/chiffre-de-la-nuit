"""Affiche l'état TikTok d'un envoi (publish_id)."""
import sys, requests
from publish import tiktok
tok = tiktok._access_token()
h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
print("statut :", requests.post(f"{tiktok.API}/post/publish/status/fetch/", headers=h, json={"publish_id": sys.argv[1]}, timeout=30).text[:600])
print("compte :", requests.get(f"{tiktok.API}/user/info/", params={"fields": "display_name,username"}, headers={"Authorization": f"Bearer {tok}"}, timeout=30).text[:300])
