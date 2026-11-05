"""Test détaillé d'un dépôt en brouillon TikTok."""
import os, sys, time, requests
from publish import tiktok
path = sys.argv[1]
tok = tiktok._access_token()
h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
size = os.path.getsize(path)
r = requests.post(f"{tiktok.API}/post/publish/inbox/video/init/", headers=h, timeout=60, json={
    "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}})
print("init :", r.status_code, r.text[:300].replace(r.json().get("data", {}).get("upload_url", "§"), "<url>"))
j = r.json(); pid, url = j["data"]["publish_id"], j["data"]["upload_url"]
data = open(path, "rb").read()
up = requests.put(url, data=data, timeout=600, headers={"Content-Type": "video/mp4", "Content-Length": str(size),
                                                          "Content-Range": f"bytes 0-{size - 1}/{size}"})
print("put :", up.status_code, up.text[:300])
for i in range(24):
    s = requests.post(f"{tiktok.API}/post/publish/status/fetch/", headers=h, json={"publish_id": pid}, timeout=30).text
    print(i * 10, "s :", s[:250]); 
    if "SEND_TO_USER_INBOX" in s or "FAILED" in s: break
    time.sleep(10)
