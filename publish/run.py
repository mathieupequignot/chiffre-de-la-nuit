"""Publie les vidéos en attente dont l'heure est arrivée (Instagram, Facebook, YouTube + brouillon TikTok à la même heure).
Discord : à l'heure de la vidéo, 1 message TikTok (vidéo + miniature) + la description seule, puis 1 récapitulatif pour les autres réseaux.
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
        from . import facebook
        if facebook.enabled():
            p["facebook"] = lambda e: facebook.publish_reel(queue.url(e["video"]), e["instagram"])
    except ImportError:
        pass
    try:
        from . import youtube
        if youtube.enabled():
            p["youtube"] = lambda e: youtube.upload(os.path.join(queue.MEDIA, e["video"]), e["yt_title"], e["yt_desc"],
                                                  os.path.join(queue.MEDIA, e["cover"]) if e["cover"] else None)
    except ImportError:
        pass
    return p


NAMES = {"instagram": "Instagram", "youtube": "YouTube", "facebook": "Facebook", "tiktok": "TikTok"}
FINAL = ("ok", "annulé", "échec", "trop tard")


def title(e):
    t = (e.get("yt_title") or "").replace("#Shorts", "").strip()
    return t or e["key"]


def send_tiktok(e, at):
    """À l'heure de la vidéo : brouillon TikTok + UN message clair (vidéo + miniature jointes),
    puis la description seule dans le message suivant (appui long → Copier)."""
    draft = None
    if tiktok.enabled():
        for essai in (1, 2):
            try:
                e.setdefault("ids", {})["tiktok"] = tiktok.upload_draft(os.path.join(queue.MEDIA, e["video"]))
                draft = True; break
            except Exception:
                err = traceback.format_exc(); print(err); draft = err.strip().splitlines()[-1][:200]
    e["status"]["tiktok"] = "ok" if draft is True else "manuel"
    etat = ("📥 Brouillon déposé dans ta boîte de réception TikTok : ouvre-le et publie." if draft is True else
            f"⚠️ Brouillon TikTok impossible ({draft}) : poste la vidéo ci-jointe à la main." if draft else
            "📲 Poste la vidéo ci-jointe à la main.")
    msg = (f"🎵 **TIKTOK — {title(e)}**\n"
           f"{etat}\n"
           + ("🖼️ Miniature ci-jointe : enregistre-la puis choisis-la comme couverture.\n" if e.get("cover") else "")
           + ("📝 Description à copier dans le message suivant 👇" if e.get("tiktok_caption") else ""))
    vid = os.path.join(queue.MEDIA, e.get("discord_video") or e["video"])
    cover = os.path.join(queue.MEDIA, e["cover"]) if e.get("cover") else None
    try:
        discord_post.post(vid, msg, cover)
    except Exception as ex:  # vidéo trop lourde pour Discord : lien de téléchargement
        print("Vidéo Discord impossible :", ex)
        msg += f"\n🎬 Vidéo (trop lourde pour Discord) : {queue.url(e['video'])}"
        try:
            discord_post.notify_file(msg, cover) if cover and os.path.exists(cover) else discord_post.notify(msg)
        except Exception:
            discord_post.notify(msg)
    if e.get("tiktok_caption"):
        discord_post.notify(e["tiktok_caption"])


def report(e, at):
    """Un seul message récapitulatif par vidéo, une fois tous les réseaux traités."""
    lines = []
    for k, st in e["status"].items():
        if k == "tiktok":
            continue
        if st == "ok":
            pid = e.get("ids", {}).get(k)
            lien = f" — https://youtube.com/shorts/{pid}" if k == "youtube" and pid else ""
            lines.append(f"✅ {NAMES.get(k, k)}{lien}")
        elif st == "annulé":
            lines.append(f"🚫 {NAMES.get(k, k)} : annulé")
        else:
            why = e.get("why", {}).get(k, "")
            lines.append(f"⚠️ {NAMES.get(k, k)} : {st} — à publier à la main" + (f" ({why})" if why else ""))
    if lines:
        discord_post.notify(f"📣 **{title(e)}** — publication de {at.strftime('%H:%M')}\n" + "\n".join(lines))


def main():
    now = dt.datetime.now(queue.PARIS)
    q = queue.load(); plats = platforms()
    for e in q:
        at = dt.datetime.fromisoformat(e["at"])
        if at > now:
            continue
        wants_tt = (not e.get("platforms") or "tiktok" in e["platforms"]) and "tiktok" not in e["status"]
        todo = [k for k in plats if e["status"].get(k) not in FINAL
                and (not e.get("platforms") or k in e["platforms"])]
        if not todo and not wants_tt:
            if not e.get("reported") and e["status"]:
                e["reported"] = True; queue.save(q)
            continue
        if now - at > dt.timedelta(hours=20):
            for k in todo: e["status"][k] = "trop tard"
            if wants_tt: e["status"]["tiktok"] = "trop tard"
            e["reported"] = True; queue.save(q)
            continue
        if cancelled(e.get("discord_mid")):
            for k in todo: e["status"][k] = "annulé"
            if wants_tt: e["status"]["tiktok"] = "annulé"
            e["reported"] = True
            discord_post.notify(f"🚫 Publication annulée (❌) : {title(e)}")
            queue.save(q)
            continue
        if wants_tt:
            try:
                send_tiktok(e, at)
            except Exception:
                print(traceback.format_exc())
            queue.save(q)
        if any(k in todo for k in ("instagram", "facebook")) and not live(e):
            print(f"{e['key']} : vidéo pas encore en ligne sur GitHub Pages, Instagram/Facebook au prochain passage")
            todo = [k for k in todo if k not in ("instagram", "facebook")]
        for k in todo:
            try:
                pid = plats[k](e)
                e["status"][k] = "ok"; e.setdefault("ids", {})[k] = pid
            except Exception:
                err = traceback.format_exc(); print(err)
                n = e.setdefault("errors", {}).get(k, 0) + 1; e["errors"][k] = n
                if n >= 2:
                    e["status"][k] = "échec"
                    e.setdefault("why", {})[k] = err.strip().splitlines()[-1][:200]
        # message récapitulatif unique quand tous les réseaux visés sont traités
        if not e.get("reported") and all(e["status"].get(k) in FINAL for k in plats
                                         if not e.get("platforms") or k in e["platforms"]):
            e["reported"] = True
            try:
                report(e, at)
            except Exception:
                print(traceback.format_exc())
        queue.save(q)
    # ménage : on garde 3 jours
    keep = [e for e in q if now - dt.datetime.fromisoformat(e["at"]) < dt.timedelta(days=3)]
    used = {e["video"] for e in keep} | {e["cover"] for e in keep if e["cover"]} | {e["discord_video"] for e in keep if e.get("discord_video")}
    for f in os.listdir(queue.MEDIA):
        if f not in used and f != ".keep":
            os.remove(os.path.join(queue.MEDIA, f))
    queue.save(keep)


if __name__ == "__main__":
    main()
