"""Enregistre publish/queue.json (+ token TikTok) sans jamais perdre un statut de publication,
même si un autre workflow a modifié la file entre-temps (sinon : risque de double publication)."""
import json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(ROOT, "publish", "queue.json")
TOK = os.path.join(ROOT, "publish", "tt_token.enc")
DONE = ("ok", "annulé", "échec", "trop tard")


def git(*a, check=True):
    return subprocess.run(["git", *a], cwd=ROOT, check=check, capture_output=True, text=True)


def merge(mine, theirs):
    by = {e["key"]: e for e in mine}
    for e in theirs:
        m = by.get(e["key"])
        if not m:
            continue
        st = e.setdefault("status", {})
        for k, v in m.get("status", {}).items():
            if v in DONE or k not in st:
                st[k] = v
        e.setdefault("ids", {}).update(m.get("ids", {}))
        er = e.setdefault("errors", {})
        for k, v in m.get("errors", {}).items():
            er[k] = max(er.get(k, 0), v)
    return theirs


def main():
    git("config", "user.name", "publish-bot"); git("config", "user.email", "publish-bot@users.noreply.github.com")
    git("add", "-A", "publish/queue.json", "docs/media", check=False)
    if os.path.exists(TOK):
        git("add", "publish/tt_token.enc", check=False)
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        print("Rien à enregistrer."); return
    git("commit", "-m", "Publication : file d'attente")
    for attempt in range(5):
        if git("pull", "--rebase", "-q", check=False).returncode == 0 and git("push", check=False).returncode == 0:
            print("File d'attente enregistrée."); return
        # conflit : on repart de la version distante et on y reporte nos statuts
        git("rebase", "--abort", check=False)
        tmp = tempfile.mkdtemp()
        mine = json.load(open(Q, encoding="utf-8"))
        tok = os.path.join(tmp, "tok")
        if os.path.exists(TOK):
            shutil.copy(TOK, tok)
        git("fetch", "-q", "origin", "main"); git("reset", "-q", "--hard", "origin/main")
        theirs = json.load(open(Q, encoding="utf-8"))
        json.dump(merge(mine, theirs), open(Q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if os.path.exists(tok):
            shutil.copy(tok, TOK)
        git("add", "-A", "publish/queue.json", check=False)
        if os.path.exists(TOK):
            git("add", "publish/tt_token.enc", check=False)
        if git("diff", "--cached", "--quiet", check=False).returncode == 0:
            print("Rien à enregistrer après fusion."); return
        git("commit", "-m", "Publication : file d'attente (fusion)")
        if git("push", check=False).returncode == 0:
            print("File d'attente enregistrée (fusionnée)."); return
    sys.exit("Impossible d'enregistrer la file d'attente après 5 essais")


if __name__ == "__main__":
    main()
