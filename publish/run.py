"""Publie les vidéos en attente dont l'heure est arrivée (Instagram, puis YouTube quand il sera branché).
Une réaction ❌ de ta part sur le message Discord de la vidéo annule sa publication."""
import datetime as dt
import os
import traceback
import requests

from chiffre import discord_post
from . import queue, instagram, tiktok

API = "https://discord.com/api/v10"


def cancelled(mid):
    if not (mid and os.environ.get("DISCORD_BOT_TOKEN")):
        return False
    h = discord_post._h(); ch = os.environ["DISCORD_CHANNEL_ID"]
    me = requests.get(f"{API}/users/@me", headers=h, timeout=30).json()["id"]
    users = requests.get(f"{API}/channels/{ch}/messages/{mid}/reactions/%E2%9D%8C", headers=h, timeout=30)
    return users.ok and any(u["id"] != me for u in users.json())


def live(e, wait=420):
    """Instagram va chercher la vidéo sur GitHub Pages : on attend (jusqu'à 7 min) qu'elle y soit publiée,
    sinon Instagram renvoie l'erreur 2207076."""
    import time
    t0 = time.time()
    while True:
        try:
            if all(requests.head(queue.url(f), timeout=20, allow_redirects=True).status_code == 200
                   for f in [e["video"]] + ([e["cover"]] if e.get("cover") else [])):
                return True
        except Exception:
            pass
        if time.time() - t0 > wait:
            return False
        time.sleep(20)


def platforms():
    p = {}
    if instagram.enabled():
        p["instagram"] = lambda e: instagram.publish_reel(queue.url(e["video"]), e["instagram"], queue.url(e["cover"]) if e["cover"] else None)
    try:
        from . import youtube
        if youtube.enabled():
            p["youtube"] = lambda e: youtube.upload(os.path.join(queue.MEDIA, e["video"]), e["yt_title"], e["yt_desc"],
                                                  os.path.join(queue.MEDIA, e["cover"]) if e["cover"] else None)
    except ImportError:
        pass
    return p


def main():
    now = dt.datetime.now(queue.PARIS)
    q = queue.load(); plats = platforms()
    # TikTok : dépôt en brouillon dès que la vidéo est prête (sans attendre l'heure), tu publies depuis l'appli
    if tiktok.enabled():
        for e in q:
            at = dt.datetime.fromisoformat(e["at"])
            if e["status"].get("tiktok") in ("ok", "échec") or now - at > dt.timedelta(hours=20) or at - now > dt.timedelta(hours=5):
                continue  # trop tard, ou trop tôt (le brouillon arrive au plus 5 h avant l'heure prévue)
            try:
                e.setdefault("ids", {})["tiktok"] = tiktok.upload_draft(os.path.join(queue.MEDIA, e["video"]))
                e["status"]["tiktok"] = "ok"
                discord_post.notify(f"📥 Brouillon TikTok prêt : {e['key']} — à publier vers {at.strftime('%H:%M')} depuis TikTok (boîte de réception)."
                                    + (" Description dans le message suivant 👇" if e.get("tiktok_caption") else ""))
                if e.get("tiktok_caption"):
                    discord_post.notify(e["tiktok_caption"])
            except Exception:
                err = traceback.format_exc(); print(err)
                n = e.setdefault("errors", {}).get("tiktok", 0) + 1; e["errors"]["tiktok"] = n
                if n >= 2:
                    e["status"]["tiktok"] = "échec"
                    discord_post.notify(f"⚠️ Brouillon TikTok impossible pour {e['key']} — poste-la à la main.\n```{err[-800:]}```")
            queue.save(q)
    for e in q:
        at = dt.datetime.fromisoformat(e["at"])
        if at > now:
            continue
        todo = [k for k in plats if e["status"].get(k) not in ("ok", "annulé", "échec", "trop tard")]
        if not todo:
            continue
        if now - at > dt.timedelta(hours=20):
            for k in todo: e["status"][k] = "trop tard"
            continue
        if cancelled(e.get("discord_mid")):
            for k in todo: e["status"][k] = "annulé"
            discord_post.notify(f"🚫 Publication annulée (❌) : {e['key']}")
            continue
        if "instagram" in todo and not live(e):
            print(f"{e['key']} : vidéo pas encore en ligne sur GitHub Pages, Instagram au prochain passage")
            todo = [k for k in todo if k != "instagram"]
        for k in todo:
            try:
                pid = plats[k](e)
                e["status"][k] = "ok"; e.setdefault("ids", {})[k] = pid
                discord_post.notify(f"✅ Publié sur **{k.capitalize()}** : {e['key']}")
            except Exception:
                err = traceback.format_exc(); print(err)
                n = e.setdefault("errors", {}).get(k, 0) + 1; e["errors"][k] = n
                if n >= 2:
                    e["status"][k] = "échec"
                    discord_post.notify(f"⚠️ Échec de la publication **{k}** pour {e['key']} — publie-la à la main.\n```{err[-800:]}```")
        queue.save(q)
    # ménage : on garde 3 jours
    keep = [e for e in q if now - dt.datetime.fromisoformat(e["at"]) < dt.timedelta(days=3)]
    used = {e["video"] for e in keep} | {e["cover"] for e in keep if e["cover"]}
    for f in os.listdir(queue.MEDIA):
        if f not in used and f != ".keep":
            os.remove(os.path.join(queue.MEDIA, f))
    queue.save(keep)


if __name__ == "__main__":
    main()
