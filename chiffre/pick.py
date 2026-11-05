"""Choisit « le chiffre de la nuit » et écrit le texte lu, les données d'écran et la légende."""
import datetime as dt
import random
from .teams import team

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def _double_count(p):
    return sum(v >= 10 for v in (p["pts"], p["reb"], p["ast"], p["stl"], p["blk"]))


def _game_score(p):
    return (p["pts"] + 0.4 * p["fgm"] - 0.7 * p["fga"] - 0.4 * (p["fta"] - p["ftm"]) + 0.5 * p["reb"]
            + p["stl"] + 0.7 * p["ast"] + 0.7 * p["blk"] - p["tov"])


def angle_of(p):
    """Angle du récit + score d'impact. On classe par impact (game score + bonus d'exploit),
    et non plus par catégorie : un 52-24 passe devant un triple-double à 32 points."""
    gs = _game_score(p)
    td = _double_count(p) >= 3
    bonus = (8 if td else 0) + (6 if p["pts"] >= 40 else 0) + (6 if p["pts"] >= 50 else 0) \
        + (6 if p["pts"] >= 20 and p["reb"] >= 20 else 0) + (5 if p["tpm"] >= 8 else 0)
    if td:
        a = "triple_double"
    elif p["pts"] >= 40:
        a = "scorer"
    elif p["pts"] >= 20 and p["reb"] >= 20:
        a = "twenty_twenty"
    elif p["tpm"] >= 8:
        a = "sniper"
    else:
        a = "best"
    return a, gs + bonus


def choose(games):
    best = None
    for g in games:
        for p in g["players"]:
            if p["pts"] == 0 and p["reb"] == 0:
                continue
            a, s = angle_of(p)
            if best is None or s > best[0]:
                best = (s, a, p, g)
    if best is None:
        return None
    _, a, p, g = best
    return a, p, g


def _cover(angle, p):
    """Chiffre, unité et ligne secondaire de la miniature."""
    if angle == "sniper":
        return dict(num=str(p["tpm"]), unit="À 3 POINTS", extra=f"{p['pts']} POINTS · {p['tpm']}/{p['tpa']} DE LOIN")
    if angle in ("triple_double", "twenty_twenty"):
        tag = "TRIPLE-DOUBLE" if angle == "triple_double" else "20-20"
        return dict(num=str(p["pts"]), unit="POINTS", extra=f"+ {p['reb']} REB · {p['ast']} PD · {tag}")
    if p["stl"] + p["blk"] >= 5:
        ex = f"+ {p['blk']} CONTRES · {p['stl']} INTERCEPTIONS"
    else:
        ex = f"+ {p['reb']} REB · {p['ast']} PD"
    return dict(num=str(p["pts"]), unit="POINTS", extra=ex)


def build(games, paris_day, seed=None):
    ch = choose(games)
    if not ch:
        return None
    angle, p, g = ch
    rnd = random.Random(seed or paris_day.isoformat())
    me, opp = team(p["team"]), team(g["away"] if p["team"] == g["home"] else g["home"])
    my_pts = g["home_pts"] if p["team"] == g["home"] else g["away_pts"]
    op_pts = g["away_pts"] if p["team"] == g["home"] else g["home_pts"]
    win = my_pts > op_pts
    full = f"{p['first']} {p['last']}"
    y = dt.date.fromordinal(paris_day.toordinal() - 1)
    j = lambda d: "1ER" if d == 1 else str(d)
    date_label = f"NUIT DU {j(y.day)} AU {j(paris_day.day)} {MOIS[paris_day.month - 1].upper()}" if y.month == paris_day.month \
        else f"NUIT DU {j(y.day)} {MOIS[y.month - 1].upper()} AU {j(paris_day.day)} {MOIS[paris_day.month - 1].upper()}"

    # ---- statistiques mises en avant (scène A) + bandeau
    if angle == "sniper":
        rows = [(p["tpm"], "À 3 POINTS"), (p["pts"], "POINTS"), (p["tpa"], "TENTATIVES")]
        hook = [f"{p['tpm']} paniers à 3 points.", f"{p['pts']} points.", f"Sur seulement {p['tpa']} tentatives de loin."]
    elif angle == "twenty_twenty":
        rows = [(p["pts"], "POINTS"), (p["reb"], "REBONDS"), (p["ast"], "PASSES")]
        hook = [f"{p['pts']} points.", f"{p['reb']} rebonds.", f"{p['ast']} passes."]
    elif p["blk"] >= 4 and p["blk"] > p["ast"]:
        rows = [(p["pts"], "POINTS"), (p["reb"], "REBONDS"), (p["blk"], "CONTRES")]
        hook = [f"{p['pts']} points.", f"{p['reb']} rebonds.", f"{p['blk']} contres."]
    else:
        rows = [(p["pts"], "POINTS"), (p["reb"], "REBONDS"), (p["ast"], "PASSES")]
        hook = [f"{p['pts']} points.", f"{p['reb']} rebonds.", f"{p['ast']} passes."]
    banner = None
    if p["tov"] <= 1 and p["fga"] >= 10:
        banner = "1 SEULE BALLE PERDUE" if p["tov"] == 1 else "0 BALLE PERDUE"
        hook.append("Et une seule balle perdue." if p["tov"] == 1 else "Et zéro balle perdue.")
    elif p["stl"] + p["blk"] >= 5:
        banner = f"{p['stl']} INTERCEPTIONS · {p['blk']} CONTRES"
        hook.append(f"Et {p['stl'] + p['blk']} ballons volés ou contrés.")

    exploit = {"triple_double": ("un triple-double monstrueux", "TRIPLE-DOUBLE"),
               "scorer": (f"un carton à {p['pts']} points", f"{p['pts']} POINTS"),
               "twenty_twenty": ("un 20-20 rarissime", "20-20"),
               "sniper": (f"{p['tpm']} tirs primés", f"{p['tpm']} À 3 PTS"),
               "best": ("le meilleur match de la nuit", "MVP DE LA NUIT")}[angle]

    segs = [("A", s) for s in hook]
    segs.append(("B", f"Cette nuit, {full} a signé {exploit[0]} {me['avec']} {opp['face']}."))
    fg = None
    if p["fga"] >= 8 and p["fgm"] / p["fga"] >= 0.5:
        fg = (p["fgm"], p["fga"])
        segs.append(("C", rnd.choice(["Et surtout, avec une efficacité folle : {m} tirs réussis sur {a}.",
                                      "Le tout avec une adresse redoutable : {m} tirs réussis sur {a}.",
                                      "Et quelle efficacité : {m} sur {a} aux tirs."]).format(m=p["fgm"], a=p["fga"])))
    pm = None
    if p["pm"] >= 10 and win:
        pm = p["pm"]
        segs.append(("D", f"Quand il était sur le terrain, {me['name'].title()} a dominé de {pm} points."))
    w_hi, w_lo = max(my_pts, op_pts), min(my_pts, op_pts)
    segs.append(("E", f"Résultat : victoire {w_hi} à {w_lo}." if win else f"Mais ça n'a pas suffi : défaite {w_lo} à {w_hi}."))
    last = p["last"].upper()
    punch = rnd.choice([
        (f"{last}", "EN MODE PATRON", "La ligue est prévenue.", f"{p['last']} en mode patron… la ligue est prévenue."),
        ("QUELLE", "PERFORMANCE", "On en reparle demain.", "Quelle performance… on en reparlera."),
        (f"{last}", "INARRÊTABLE", "Qui va l'arrêter ?", f"{p['last']}, inarrêtable… mais qui va l'arrêter ?"),
    ]) if win else (f"{last}", "SEUL CONTRE TOUS", "Ça ne suffit pas toujours.", f"{p['last']} seul contre tous… et parfois, ça ne suffit pas.")
    segs.append(("F", punch[3]))
    segs.append(("G", "Abonne-toi pour ne rater aucun chiffre de la nuit."))

    D = dict(date_label=date_label, angle=angle, first=p["first"].upper(), last=p["last"].upper(), me=me, opp=opp,
             my_pts=my_pts, op_pts=op_pts, win=win, home=g["home"], away=g["away"], home_pts=g["home_pts"], away_pts=g["away_pts"],
             rows=rows, banner=banner, stamp=exploit[1], line=f"{p['pts']} PTS  ·  {p['reb']} REB  ·  {p['ast']} PD",
             fg=fg, pm=pm, punch=punch[:3], cover=_cover(angle, p))
    import re
    tag = lambda t: "#" + re.sub(r"[^0-9A-Za-zÀ-ÿ]", "", t)
    who, mine, theirs = tag(p["last"]), tag(me["nick"]), tag(opp["nick"])
    base = f"{full} : {exploit[0]} cette nuit ({p['pts']} pts, {p['reb']} reb, {p['ast']} pd) {me['avec']} {opp['face']}. 🏀"
    tags = {
        "tiktok": [who, "#NBA", mine, "#basketball", "#NBAFrance"],
        "instagram": [who, "#NBA", mine, theirs, "#basketball", "#basket", "#NBAFrance", "#NBADailyNews", "#nbastats", "#sport"],
        "youtube": ["#Shorts", "#NBA", who],
    }
    caption = dict(
        text=base,
        tiktok=f"{base}\n\n{' '.join(tags['tiktok'])}",
        instagram=f"{base}\n\nAbonne-toi pour le chiffre de chaque nuit 🔔\n\n{' '.join(tags['instagram'])}",
        youtube_title=f"{full} : {exploit[0]} ! 🏀 #Shorts"[:100],
        youtube=f"{base}\n\n{' '.join(tags['youtube'])}",
    )
    return D, segs, caption
