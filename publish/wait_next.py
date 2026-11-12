"""Attend l'heure de la prochaine publication Instagram/YouTube si elle tombe dans les 4 h
(lancé après un passage déclenché par la fabrication d'une vidéo : publication à l'heure pile, sans dépendre des retards de GitHub)."""
import datetime as dt, json, os, sys, time

MAX = dt.timedelta(hours=4)
q = json.load(open(os.path.join(os.path.dirname(__file__), "queue.json"), encoding="utf-8"))
now = dt.datetime.now(dt.timezone.utc)
nxt = None
for e in q:
    at = dt.datetime.fromisoformat(e["at"])
    st = e.get("status", {})
    if at > now and at - now <= MAX and any(st.get(k) not in ("ok", "annulé", "échec", "trop tard") for k in ("instagram", "youtube", "facebook") if not e.get("platforms") or k in e["platforms"]):
        nxt = at if nxt is None or at < nxt else nxt
if nxt is None:
    print("Rien à publier dans les 4 h : pas d'attente."); sys.exit(0)
s = (nxt - now).total_seconds() + 20
print(f"Attente jusqu'à {nxt.isoformat()} ({s / 60:.0f} min)"); sys.stdout.flush()
time.sleep(s)
open(os.environ.get("GITHUB_ENV", os.devnull), "a").write("WAITED=1\n")
