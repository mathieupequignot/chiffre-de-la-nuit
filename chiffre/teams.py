"""Équipes NBA : nom affiché, formules pour le texte lu, couleurs des badges (originaux, sans logo officiel)."""
W = (255, 255, 255)

# code: (nom écran, "avec ...", "face à ...", fond badge, texte badge, liseré)
_T = {
    "ATL": ("ATLANTA", "avec Atlanta", "face à Atlanta", (200, 16, 46), W, (253, 185, 39)),
    "BOS": ("BOSTON", "avec Boston", "face à Boston", (0, 122, 51), W, (139, 111, 78)),
    "BKN": ("BROOKLYN", "avec Brooklyn", "face à Brooklyn", (20, 20, 20), W, (140, 145, 150)),
    "CHA": ("CHARLOTTE", "avec Charlotte", "face à Charlotte", (29, 17, 96), W, (0, 120, 140)),
    "CHI": ("CHICAGO", "avec Chicago", "face à Chicago", (206, 17, 65), W, (20, 20, 20)),
    "CLE": ("CLEVELAND", "avec Cleveland", "face à Cleveland", (134, 0, 56), (253, 187, 48), (4, 30, 66)),
    "DAL": ("DALLAS", "avec Dallas", "face à Dallas", (0, 83, 188), W, (0, 43, 92)),
    "DEN": ("DENVER", "avec Denver", "face à Denver", (13, 34, 64), (254, 197, 36), (139, 35, 50)),
    "DET": ("DETROIT", "avec Detroit", "face à Detroit", (200, 16, 46), W, (29, 66, 138)),
    "GSW": ("GOLDEN STATE", "avec Golden State", "face à Golden State", (29, 66, 138), (255, 199, 44), (255, 199, 44)),
    "HOU": ("HOUSTON", "avec Houston", "face à Houston", (206, 17, 65), W, (20, 20, 20)),
    "IND": ("INDIANA", "avec Indiana", "face à Indiana", (0, 45, 98), (253, 187, 48), (190, 192, 194)),
    "LAC": ("CLIPPERS", "avec les Clippers", "face aux Clippers", (200, 16, 46), W, (29, 66, 148)),
    "LAL": ("LAKERS", "avec les Lakers", "face aux Lakers", (85, 37, 130), (253, 185, 39), (253, 185, 39)),
    "MEM": ("MEMPHIS", "avec Memphis", "face à Memphis", (93, 118, 169), W, (18, 23, 63)),
    "MIA": ("MIAMI", "avec Miami", "face à Miami", (152, 0, 46), W, (249, 160, 27)),
    "MIL": ("MILWAUKEE", "avec Milwaukee", "face à Milwaukee", (0, 71, 27), (240, 235, 210), (0, 125, 197)),
    "MIN": ("MINNESOTA", "avec Minnesota", "face à Minnesota", (12, 35, 64), W, (35, 97, 146)),
    "NOP": ("NEW ORLEANS", "avec La Nouvelle-Orléans", "face à La Nouvelle-Orléans", (0, 22, 65), W, (225, 58, 62)),
    "NYK": ("NEW YORK", "avec New York", "face à New York", (0, 107, 182), W, (245, 132, 38)),
    "OKC": ("OKLAHOMA CITY", "avec Oklahoma City", "face à Oklahoma City", (0, 125, 195), W, (239, 59, 36)),
    "ORL": ("ORLANDO", "avec Orlando", "face à Orlando", (0, 125, 197), W, (196, 206, 211)),
    "PHI": ("PHILADELPHIE", "avec Philadelphie", "face à Philadelphie", (0, 107, 182), W, (237, 23, 76)),
    "PHX": ("PHOENIX", "avec Phoenix", "face à Phoenix", (29, 17, 96), W, (229, 95, 32)),
    "POR": ("PORTLAND", "avec Portland", "face à Portland", (224, 58, 62), W, (20, 20, 20)),
    "SAC": ("SACRAMENTO", "avec Sacramento", "face à Sacramento", (91, 43, 130), W, (99, 113, 122)),
    "SAS": ("SAN ANTONIO", "avec San Antonio", "face à San Antonio", (196, 206, 211), (20, 20, 20), (20, 20, 20)),
    "TOR": ("TORONTO", "avec Toronto", "face à Toronto", (206, 17, 65), W, (20, 20, 20)),
    "UTA": ("UTAH", "avec Utah", "face à Utah", (0, 43, 92), W, (249, 160, 27)),
    "WAS": ("WASHINGTON", "avec Washington", "face à Washington", (0, 43, 92), W, (227, 24, 55)),
}


NICK = {"ATL": "Hawks", "BOS": "Celtics", "BKN": "Nets", "CHA": "Hornets", "CHI": "Bulls", "CLE": "Cavaliers",
        "DAL": "Mavericks", "DEN": "Nuggets", "DET": "Pistons", "GSW": "Warriors", "HOU": "Rockets", "IND": "Pacers",
        "LAC": "Clippers", "LAL": "Lakers", "MEM": "Grizzlies", "MIA": "Heat", "MIL": "Bucks", "MIN": "Timberwolves",
        "NOP": "Pelicans", "NYK": "Knicks", "OKC": "Thunder", "ORL": "Magic", "PHI": "Sixers", "PHX": "Suns",
        "POR": "Blazers", "SAC": "Kings", "SAS": "Spurs", "TOR": "Raptors", "UTA": "Jazz", "WAS": "Wizards"}


def team(code):
    n, avec, face, bg, fg, stripe = _T.get(code, (code, f"avec {code}", f"face à {code}", (60, 60, 70), W, (150, 150, 160)))
    return dict(code=code, name=n, avec=avec, face=face, bg=bg, fg=fg, stripe=stripe, nick=NICK.get(code, code))
