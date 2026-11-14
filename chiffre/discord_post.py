"""Envoie la vidéo du jour et sa légende dans le salon Discord de validation."""
import json
import os
import requests

API = "https://discord.com/api/v10"


def _h():
    return {"Authorization": f"Bot {os.environ['DISCORD_BOT_TOKEN']}"}


def _gateway_once():
    """Discord exige qu'un bot se soit connecté au moins une fois au « gateway » avant de pouvoir poster."""
    import websocket  # websocket-client
    url = requests.get(f"{API}/gateway/bot", headers=_h(), timeout=30).json()["url"]
    ws = websocket.create_connection(f"{url}/?v=10&encoding=json", timeout=30)
    try:
        json.loads(ws.recv())  # HELLO
        ws.send(json.dumps({"op": 2, "d": {"token": os.environ["DISCORD_BOT_TOKEN"], "intents": 0,
                                           "properties": {"os": "linux", "browser": "chiffre", "device": "chiffre"}}}))
        for _ in range(20):
            msg = json.loads(ws.recv())
            if msg.get("t") == "READY":
                break
    finally:
        ws.close()


def post(video_path, content, cover_path=None, tiktok=None):
    """Envoie la vidéo (+ miniature) avec un court message, puis, si fourni, la description TikTok
    seule dans un second message (appui long → Copier le texte sur téléphone)."""
    try:
        _gateway_once()
    except Exception as e:  # non bloquant : déjà connecté auparavant
        print("gateway:", e)
    ch = os.environ["DISCORD_CHANNEL_ID"]
    files = {"files[0]": ("chiffre_de_la_nuit.mp4", open(video_path, "rb"), "video/mp4")}
    if cover_path and os.path.exists(cover_path):
        files["files[1]"] = ("miniature.jpg", open(cover_path, "rb"), "image/jpeg")
    try:
        r = requests.post(f"{API}/channels/{ch}/messages", headers=_h(),
                          data={"payload_json": json.dumps({"content": content[:1990]})}, files=files, timeout=120)
    finally:
        for _, fh, _ in files.values(): fh.close()
    r.raise_for_status()
    mid = r.json()["id"]
    if tiktok:
        requests.post(f"{API}/channels/{ch}/messages", headers=_h(), json={"content": tiktok[:2000]}, timeout=30)
    return mid


def notify(content):
    ch = os.environ.get("DISCORD_CHANNEL_ID")
    if ch and os.environ.get("DISCORD_BOT_TOKEN"):
        requests.post(f"{API}/channels/{ch}/messages", headers=_h(), json={"content": content[:1990]}, timeout=30)


def notify_file(content, path, name="miniature.jpg"):
    """Message + une image jointe (ex. miniature à enregistrer pour TikTok)."""
    ch = os.environ.get("DISCORD_CHANNEL_ID")
    if not (ch and os.environ.get("DISCORD_BOT_TOKEN")):
        return
    with open(path, "rb") as fh:
        r = requests.post(f"{API}/channels/{ch}/messages", headers=_h(),
                          data={"payload_json": json.dumps({"content": content[:1990]})},
                          files={"files[0]": (name, fh, "image/jpeg")}, timeout=60)
    r.raise_for_status()
