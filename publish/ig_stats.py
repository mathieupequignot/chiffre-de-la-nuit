"""Exporte les stats de tous les posts Instagram en JSON (stdout)."""
import json, os, requests
from publish.instagram import _base
tok, uid = os.environ["IG_TOKEN"].strip(), os.environ["IG_USER_ID"].strip(); G = _base()
acc = requests.get(f"{G}/{uid}", params={"fields": "username,followers_count,media_count", "access_token": tok}, timeout=30).json()
out = {"account": acc, "media": []}
url = f"{G}/{uid}/media"; params = {"fields": "id,caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink", "limit": 50, "access_token": tok}
while url:
    j = requests.get(url, params=params, timeout=30).json(); params = None
    for m in j.get("data", []):
        ins = requests.get(f"{G}/{m['id']}/insights", params={"metric": "views,reach,saved,shares,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time", "access_token": tok}, timeout=30).json()
        if "error" in ins:
            ins = requests.get(f"{G}/{m['id']}/insights", params={"metric": "views,reach,saved,shares,total_interactions", "access_token": tok}, timeout=30).json()
        m["insights"] = {d["name"]: d["values"][0]["value"] for d in ins.get("data", [])} or ins.get("error", {}).get("message")
        out["media"].append(m)
    url = j.get("paging", {}).get("next")
print("IGSTATS" + json.dumps(out, ensure_ascii=False))
