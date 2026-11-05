"""Applique (ou réapplique) une miniature à une vidéo YouTube existante et affiche la réponse de YouTube."""
import sys
import requests
from publish.youtube import _access_token

vid, path = sys.argv[1], sys.argv[2]
h = {"Authorization": f"Bearer {_access_token()}"}
with open(path, "rb") as f:
    r = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                      headers={**h, "Content-Type": "image/jpeg"}, data=f, timeout=60)
print("thumbnails.set :", r.status_code, r.text[:500])
v = requests.get("https://www.googleapis.com/youtube/v3/videos", headers=h,
                 params={"part": "snippet,status,processingDetails", "id": vid}, timeout=30).json()
it = (v.get("items") or [{}])[0]
print("statut :", it.get("status")); print("traitement :", it.get("processingDetails"))
print("miniatures :", {k: t["url"] for k, t in it.get("snippet", {}).get("thumbnails", {}).items()})
