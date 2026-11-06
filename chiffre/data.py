"""Récupère les matchs terminés de la nuit et les stats des joueurs via API-NBA (api-sports.io, v2)."""
import datetime as dt
import json
import os
import time
import requests

BASE = "https://v2.nba.api-sports.io"


_last = [0.0]


def _get(path, params):
    """Offre gratuite : 10 requêtes par minute -> une requête toutes les 7 s, et on réessaie si l'API dit d'attendre."""
    for attempt in range(5):
        wait = 7.0 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        r = requests.get(BASE + path, params=params, headers={"x-apisports-key": os.environ["API_NBA_KEY"]}, timeout=30)
        r.raise_for_status()
        js = r.json()
        errs = js.get("errors")
        if errs and "rateLimit" in (errs if isinstance(errs, dict) else {}):
            time.sleep(65)
            continue
        if errs:
            raise RuntimeError(f"API-NBA: {errs}")
        return js.get("response", [])
    raise RuntimeError("API-NBA : limite de requêtes toujours atteinte après plusieurs essais")


def _num(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def night_window(paris_day):
    """Matchs de la nuit précédant `paris_day` : de 12h UTC la veille à 12h UTC le jour J."""
    end = dt.datetime.combine(paris_day, dt.time(12, 0), tzinfo=dt.timezone.utc)
    return end - dt.timedelta(days=1), end


def fetch_night(paris_day):
    """Retourne une liste de matchs normalisés : {id, home, away, home_pts, away_pts, players:[...]}"""
    start, end = night_window(paris_day)
    games = []
    for day in {start.date(), end.date()}:
        for g in _get("/games", {"date": day.isoformat()}):
            t = dt.datetime.fromisoformat(g["date"]["start"].replace("Z", "+00:00"))
            finished = str(g.get("status", {}).get("long", "")).lower() in ("finished", "final") or g.get("status", {}).get("short") == 3
            if start <= t < end and finished and not any(x["id"] == g["id"] for x in games):
                games.append(dict(id=g["id"], home=g["teams"]["home"]["code"], away=g["teams"]["visitors"]["code"],
                                  home_pts=_num(g["scores"]["home"]["points"]), away_pts=_num(g["scores"]["visitors"]["points"])))
    for g in games:
        g["players"] = []
        for p in _get("/players/statistics", {"game": g["id"]}):
            g["players"].append(dict(
                pid=p["player"].get("id"), first=p["player"]["firstname"], last=p["player"]["lastname"], team=p["team"]["code"],
                pts=_num(p.get("points")), reb=_num(p.get("totReb")), ast=_num(p.get("assists")),
                stl=_num(p.get("steals")), blk=_num(p.get("blocks")), tov=_num(p.get("turnovers")),
                fgm=_num(p.get("fgm")), fga=_num(p.get("fga")), tpm=_num(p.get("tpm")), tpa=_num(p.get("tpa")),
                ftm=_num(p.get("ftm")), fta=_num(p.get("fta")), pm=_num(p.get("plusMinus")), min=str(p.get("min") or "")))
    return games


def load_fixture(path):
    return json.load(open(path, encoding="utf-8"))


def season_context(p, game_id, paris_day):
    """Contexte pour l'accroche : record de points de la saison (1 requête). Ne lève jamais d'erreur."""
    try:
        if not p.get("pid"):
            return {}
        season = paris_day.year if paris_day.month >= 9 else paris_day.year - 1
        logs = [g for g in _get("/players/statistics", {"id": p["pid"], "season": season})
                if g.get("game", {}).get("id") != game_id and _num(g.get("min", "0").split(":")[0] if isinstance(g.get("min"), str) else g.get("min")) > 0]
        prev = [_num(g.get("points")) for g in logs]
        return {"games_before": len(prev), "season_high_pts": len(prev) >= 3 and p["pts"] > max(prev),
                "prev_high": max(prev) if prev else None}
    except Exception as e:
        print("contexte indisponible :", e)
        return {}
