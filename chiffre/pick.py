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


# Joueurs français (priorité : ce sont eux que le public FR suit le plus)
FRENCH = {"wembanyama", "gobert", "sarr", "risacher", "coulibaly", "salaun", "salaün", "yabusele", "batum", "diabate",
          "diabaté", "cissoko", "dieng", "essengue", "traore", "traoré", "beringer", "raynaud", "penda", "dadiet", "ajinca",
          "fournier", "ntilikina", "hayes", "lessort", "okobo", "luwawu-cabarrot", "doumbouya", "mahinmi"}


def is_french(p):
    import unicodedata
    last = "".join(c for c in unicodedata.normalize("NFD", p["last"].lower()) if unicodedata.category(c) != "Mn")
    return last in FRENCH or p["last"].lower() in FRENCH


def is_wemby(p):
    return "wembanyama" in p["last"].lower()


def angle_of(p):
    """Angle du récit + score d'impact. On classe par impact (game score + bonus d'exploit),
    et non plus par catégorie : un 52-24 passe devant un triple-double à 32 points."""
    gs = _game_score(p)
    td = _double_count(p) >= 3
    bonus = (8 if td else 0) + (6 if p["pts"] >= 40 else 0) + (6 if p["pts"] >= 50 else 0) \
        + (6 if p["pts"] >= 20 and p["reb"] >= 20 else 0) + (5 if p["tpm"] >= 8 else 0) \
        + (8 if is_wemby(p) else (5 if is_french(p) else 0))  # Wemby et les Français passent devant à niveau proche
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


def ranking(games):
    """Toutes les perfs classées par impact : [(score, angle, joueur, match)]."""
    out = []
    for g in games:
        for p in g["players"]:
            if p["pts"] == 0 and p["reb"] == 0:
                continue
            a, s = angle_of(p)
            out.append((s, a, p, g))
    return sorted(out, key=lambda x: -x[0])


def choose_combo(games):
    """Deuxième grosse perf de la nuit, dans un AUTRE match : un vrai exploit (triple-double, 40 pts, 20-20, 8 paniers à 3)
    ou une perf presque aussi forte que la n°1 (30 pts et plus, au moins 85 % de son impact). Sinon None."""
    r = ranking(games)
    if len(r) < 2:
        return None
    s1, _, _, g1 = r[0]
    for s, a, p, g in r[1:]:
        if g["id"] == g1["id"]:
            continue
        if a != "best" or (p["pts"] >= 30 and s >= 0.85 * s1):
            return a, p, g
        return None
    return None


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


def hook_of(angle, p, ctx, rnd):
    """Accroche de la 1re seconde : (phrase lue, lignes affichées en grand)."""
    last = "Wemby" if is_wemby(p) else p["last"]
    L = last.upper()
    if ctx.get("season_high_pts"):
        return f"Record de la saison pour {last} cette nuit !", ["RECORD DE LA SAISON", f"POUR {L}"]
    if is_french(p) and not is_wemby(p):
        return rnd.choice([("Un Français a régalé cette nuit en NBA !", ["UN FRANÇAIS", "A RÉGALÉ CETTE NUIT"]),
                           (f"Cocorico : {last} a fait le show cette nuit !", ["COCORICO !", f"{L} A FAIT LE SHOW"])])
    if p["pts"] >= 50:
        return f"{last} a passé la barre des 50 points !", [f"{L} À {p['pts']} POINTS", "?!"]
    if angle == "twenty_twenty":
        return f"{p['pts']} points et {p['reb']} rebonds… tu as déjà vu ça ?", [f"{p['pts']} POINTS", f"ET {p['reb']} REBONDS ?!"]
    if angle == "triple_double":
        return rnd.choice([(f"{last} a tout fait cette nuit.", [f"{L}", "A TOUT FAIT CETTE NUIT"]),
                           (f"Triple-double pour {last}, et quel triple-double !", ["TRIPLE-DOUBLE", f"POUR {L}"])])
    if angle == "sniper":
        return f"{last} était en feu derrière l'arc !", [f"{L} EN FEU", "À 3 POINTS"]
    if angle == "scorer":
        return rnd.choice([(f"Tu as vu ce que {last} a fait cette nuit ?", ["T'AS VU", f"{L} CETTE NUIT ?"]),
                           (f"{last} était injouable cette nuit.", [f"{L}", "INJOUABLE CETTE NUIT"])])
    return rnd.choice([("Le meilleur joueur de la nuit, c'est lui.", ["LE MVP DE LA NUIT", "C'EST LUI"]),
                       (f"Personne n'a fait mieux que {last} cette nuit.", ["PERSONNE N'A FAIT", f"MIEUX QUE {L}"])])


def build(games, paris_day, seed=None, ctx=None, ch=None, mode="solo", other=None):
    """mode : solo (vidéo classique), combo1 (1re perf, sans conclusion), combo2 (2e perf + conclusion commune).
    other : joueur de l'autre partie du combo (pour l'accroche et la conclusion)."""
    ctx = ctx or {}
    ch = ch or choose(games)
    if not ch:
        return None
    angle, p, g = ch
    rnd = random.Random((seed or paris_day.isoformat()) + mode)
    me, opp = team(p["team"]), team(g["away"] if p["team"] == g["home"] else g["home"])
    my_pts = g["home_pts"] if p["team"] == g["home"] else g["away_pts"]
    op_pts = g["away_pts"] if p["team"] == g["home"] else g["home_pts"]
    win = my_pts > op_pts
    full = f"{p['first']} {p['last']}"
    y = dt.date.fromordinal(paris_day.toordinal() - 1)
    j = lambda d: "1ER" if d == 1 else str(d)
    date_label = f"NUIT DU {j(y.day)} AU {j(paris_day.day)} {MOIS[paris_day.month - 1].upper()}" if y.month == paris_day.month \
        else f"NUIT DU {j(y.day)} {MOIS[y.month - 1].upper()} AU {j(paris_day.day)} {MOIS[paris_day.month - 1].upper()}"

    # ---- statistiques mises en avant (scène A) + bandeau — texte écrit « à l'oral »
    if angle == "sniper":
        rows = [(p["tpm"], "À 3 POINTS"), (p["pts"], "POINTS"), (p["tpa"], "TENTATIVES")]
        hook = [f"{p['tpm']} paniers à 3 points…", f"{p['pts']} points au total…", f"et seulement {p['tpa']} tentatives de loin !"]
    elif angle == "twenty_twenty":
        rows = [(p["pts"], "POINTS"), (p["reb"], "REBONDS"), (p["ast"], "PASSES")]
        hook = [f"{p['pts']} points,", f"{p['reb']} rebonds…", f"et {p['ast']} passes en bonus !"]
    elif p["blk"] >= 4 and p["blk"] > p["ast"]:
        rows = [(p["pts"], "POINTS"), (p["reb"], "REBONDS"), (p["blk"], "CONTRES")]
        hook = [f"{p['pts']} points,", f"{p['reb']} rebonds…", f"et {p['blk']} contres !"]
    else:
        rows = [(p["pts"], "POINTS"), (p["reb"], "REBONDS"), (p["ast"], "PASSES")]
        hook = [f"{p['pts']} points,", f"{p['reb']} rebonds…", f"et {p['ast']} passes !"]
    banner = None
    if p["tov"] <= 1 and p["fga"] >= 10:
        banner = "1 SEULE BALLE PERDUE" if p["tov"] == 1 else "0 BALLE PERDUE"
        hook.append("Avec une seule balle perdue, en plus." if p["tov"] == 1 else "Et zéro balle perdue, en plus !")
    elif p["stl"] + p["blk"] >= 5:
        banner = f"{p['stl']} INTERCEPTIONS · {p['blk']} CONTRES"
        hook.append(f"Et {p['stl'] + p['blk']} ballons volés ou contrés derrière !")

    exploit = {"triple_double": ("un triple-double monstrueux", "TRIPLE-DOUBLE"),
               "scorer": (f"un carton à {p['pts']} points", f"{p['pts']} POINTS"),
               "twenty_twenty": ("un 20-20 rarissime", "20-20"),
               "sniper": (f"{p['tpm']} tirs primés", f"{p['tpm']} À 3 PTS"),
               "best": ("le meilleur match de la nuit", "MVP DE LA NUIT")}[angle]

    hook_voice, hook_screen = hook_of(angle, p, ctx, rnd)
    nick = lambda q: "Wemby" if is_wemby(q) else q["last"]
    if mode == "combo1":
        hook_voice = rnd.choice([f"Deux énormes perfs cette nuit ! On commence par {nick(p)}.",
                                 f"Double dose cette nuit : {nick(p)} et {nick(other)} ! D'abord {nick(p)}."])
        hook_screen = ["DOUBLE DOSE", "CETTE NUIT !"]
    elif mode == "combo2":
        hook_voice = rnd.choice([f"Et ce n'est pas tout ! Dans un autre match, {nick(p)} a sorti le grand jeu.",
                                 f"Et ce n'est pas fini : {nick(p)} aussi a régalé !"])
        hook_screen = ["ET CE N'EST", f"PAS TOUT…"]
    segs = [("H", "[excited] " + hook_voice)] + [("A", s) for s in hook]
    segs.append(("B", rnd.choice(["Et ça, c'est {n}, avec {m} {o} !", "Le patron de la soirée ? {n}, avec {m} {o}.",
                                  "Tout ça signé {n}, avec {m} {o} !"]).format(n=full, m=me["avec"].replace("avec ", "", 1), o=opp["face"])))
    fg = None
    if mode == "solo" and p["fga"] >= 8 and p["fgm"] / p["fga"] >= 0.5:
        fg = (p["fgm"], p["fga"])
        segs.append(("C", rnd.choice(["[impressed] Et à {m} sur {a} au tir, s'il vous plaît !",
                                      "[impressed] Avec {m} tirs réussis sur {a}… propre !",
                                      "[impressed] Et quelle adresse : {m} sur {a} au tir !"]).format(m=p["fgm"], a=p["fga"])))
    pm = None
    if mode == "solo" and p["pm"] >= 10 and win:
        pm = p["pm"]
        segs.append(("D", f"Et quand il était sur le terrain, son équipe a fait +{pm} !"))
    w_hi, w_lo = max(my_pts, op_pts), min(my_pts, op_pts)
    segs.append(("E", rnd.choice([f"Au final, victoire {w_hi} à {w_lo} !", f"Et au bout : victoire {w_hi} à {w_lo} !"]) if win
                 else f"[sighs] Mais bon… défaite {w_lo} à {w_hi}."))
    last = p["last"].upper()
    punch = rnd.choice([
        (f"{last}", "EN MODE PATRON", "La ligue est prévenue.", f"{p['last']} en mode patron… la ligue est prévenue !"),
        ("QUELLE", "PERFORMANCE", "On en reparle demain.", "Franchement… quelle performance !"),
        (f"{last}", "INARRÊTABLE", "Qui va l'arrêter ?", f"{p['last']} est inarrêtable… mais qui va l'arrêter ?"),
    ]) if win else (f"{last}", "SEUL CONTRE TOUS", "Ça ne suffit pas toujours.", f"{p['last']} seul contre tous… et parfois, ça ne suffit pas.")
    if mode == "combo2":
        a1, a2 = nick(other).upper(), nick(p).upper()
        punch = rnd.choice([("DEUX MONSTRES", "CETTE NUIT", "Lequel tu prends ?", f"Deux monstres cette nuit… et toi, tu prends qui : {nick(other)} ou {nick(p)} ?"),
                            (f"{a1} OU {a2} ?", "TON MVP DE LA NUIT", "Réponds en commentaire", f"Alors, ton MVP de la nuit : {nick(other)} ou {nick(p)} ? Dis-le en commentaire !")])
    if mode != "combo1":
        segs.append(("F", punch[3]))
        segs.append(("G", "Abonne-toi pour ne rater aucun chiffre de la nuit !"))

    D = dict(date_label=date_label, angle=angle, first=p["first"].upper(), last=p["last"].upper(), me=me, opp=opp,
             my_pts=my_pts, op_pts=op_pts, win=win, home=g["home"], away=g["away"], home_pts=g["home_pts"], away_pts=g["away_pts"],
             rows=rows, banner=banner, stamp=exploit[1], line=f"{p['pts']} PTS  ·  {p['reb']} REB  ·  {p['ast']} PD",
             fg=fg, pm=pm, punch=punch[:3], cover=_cover(angle, p), hook=hook_screen)
    import re
    tag = lambda t: "#" + re.sub(r"[^0-9A-Za-zÀ-ÿ]", "", t)
    who, mine, theirs = tag(p["last"]), tag(me["nick"]), tag(opp["nick"])
    res = f"victoire {w_hi}-{w_lo}" if win else f"défaite {w_lo}-{w_hi}"
    if is_french(p):
        q = rnd.choice(["Le meilleur Français de la NBA en ce moment ? 👇", "Il ira jusqu'où cette saison ? 👇"])
    elif win:
        q = rnd.choice(["Il est le meilleur joueur de la ligue en ce moment ? 👇", "Tu le mets dans ton top 5 actuel ? 👇",
                        "Quelle note sur 10 pour ce match ? 👇"])
    else:
        q = rnd.choice(["Il méritait la victoire ? 👇", "Il lui manque quoi pour gagner ? 👇"])
    base = (f"{hook_voice} 🤯\n{full} : {p['pts']} pts, {p['reb']} reb, {p['ast']} pd {me['avec']} {opp['face']} ({res}).\n\n{q}")
    tags = {
        "tiktok": [who, "#NBA", mine, "#basketball", "#NBAFrance"],
        "instagram": [who, "#NBA", mine, theirs, "#basketball", "#basket", "#NBAFrance", "#NBADailyNews", "#nbastats", "#sport"],
        "youtube": ["#Shorts", "#NBA", who],
    }
    caption = dict(
        text=base,
        tiktok=f"{base}\n\n{' '.join(tags['tiktok'])}",
        instagram=f"{base}\n\nAbonne-toi pour le chiffre de chaque nuit 🔔\n\n{' '.join(tags['instagram'])}",
        youtube_title=f"{hook_voice.rstrip('.!?')} 🤯 #Shorts"[:100],
        youtube=f"{base}\n\n{' '.join(tags['youtube'])}",
    )
    return D, segs, caption


def build_combo(games, paris_day, seed=None):
    """Deux grosses perfs dans deux matchs différents -> (D1, segs1, D2, segs2, caption, cover) ; None si pas de combo."""
    first = choose(games)
    second = choose_combo(games)
    if not first or not second:
        return None
    p1, p2 = first[1], second[1]
    D1, s1, c1 = build(games, paris_day, seed, ch=first, mode="combo1", other=p2)
    D2, s2, c2 = build(games, paris_day, seed, ch=second, mode="combo2", other=p1)
    import re
    tag = lambda t: "#" + re.sub(r"[^0-9A-Za-zÀ-ÿ]", "", t)
    nick = lambda q: "Wemby" if is_wemby(q) else q["last"]
    line = lambda q, D: (f"{q['first']} {q['last']} : {q['pts']} pts, {q['reb']} reb, {q['ast']} pd "
                         f"{D['me']['avec']} {D['opp']['face']} ({'victoire' if D['win'] else 'défaite'} "
                         f"{max(D['my_pts'], D['op_pts'])}-{min(D['my_pts'], D['op_pts'])}).")
    hook = f"Double dose cette nuit : {nick(p1)} et {nick(p2)} ont régalé !"
    base = f"{hook} 🤯\n{line(p1, D1)}\n{line(p2, D2)}\n\nTon MVP de la nuit : {nick(p1)} ou {nick(p2)} ? 👇"
    who = f"{tag(p1['last'])} {tag(p2['last'])}"
    caption = dict(
        text=base,
        tiktok=f"{base}\n\n{who} #NBA #basketball #NBAFrance",
        instagram=f"{base}\n\nAbonne-toi pour le chiffre de chaque nuit 🔔\n\n{who} #NBA #basketball #basket #NBAFrance #NBADailyNews #nbastats #sport",
        youtube_title=f"{nick(p1)} et {nick(p2)} ont régalé cette nuit 🤯 #Shorts"[:100],
        youtube=f"{base}\n\n#Shorts #NBA {who}",
    )
    # miniature : la perf n°1 en grand, la n°2 en rappel
    cov = dict(D1["cover"])
    cov["extra"] = f"& {p2['last'].upper()} : {D2['cover']['num']} {D2['cover']['unit']}"
    D1["cover"] = cov
    return D1, s1, D2, s2, caption
