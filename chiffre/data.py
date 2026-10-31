"""Récupère les matchs terminés de la nuit et les stats des joueurs via API-NBA (api-sports.io, v2)."""
import datetime as dt
import json
import os
import requests

BASE = "https://v2.nba.api-sports.io"


def _get(path, params):
    r = requests.get(BASE + path, params=params, headers={"x-apisports-key": os.environ["API_NBA_KEY"]}, timeout=30)
    r.raise_for_status()
    js = r.json()
    if js.get("errors"):
        raise RuntimeError(f"API-NBA: {js['errors']}")
    return js.get("response", [])


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
                first=p["player"]["firstname"], last=p["player"]["lastname"], team=p["team"]["code"],
                pts=_num(p.get("points")), reb=_num(p.get("totReb")), ast=_num(p.get("assists")),
                stl=_num(p.get("steals")), blk=_num(p.get("blocks")), tov=_num(p.get("turnovers")),
                fgm=_num(p.get("fgm")), fga=_num(p.get("fga")), tpm=_num(p.get("tpm")), tpa=_num(p.get("tpa")),
                ftm=_num(p.get("ftm")), fta=_num(p.get("fta")), pm=_num(p.get("plusMinus")), min=str(p.get("min") or "")))
    return games


def load_fixture(path):
    return json.load(open(path, encoding="utf-8"))
