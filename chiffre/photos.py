"""Photos des joueurs fournies par Mathieu (top10/assets/*.png, détourées) : utilisées par le chiffre de la nuit
quand le joueur du jour en fait partie. Ajouter un joueur = déposer son PNG détouré + une ligne dans NAMES."""
import os
import re
import unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "top10", "assets")
NAMES = {  # prénom + nom (sans accents, minuscules) -> fichier
    "victor wembanyama": "wemby", "lebron james": "lebron", "stephen curry": "curry", "luka doncic": "doncic",
    "giannis antetokounmpo": "giannis", "shai gilgeous-alexander": "sga", "anthony edwards": "edwards",
    "nikola jokic": "jokic", "kevin durant": "durant", "cooper flagg": "flagg", "kyrie irving": "kyrie",
    "jalen brunson": "brunson", "donovan mitchell": "mitchell", "devin booker": "booker", "tyrese maxey": "maxey",
    "cade cunningham": "cunningham", "jayson tatum": "tatum", "jaylen brown": "brown", "joel embiid": "embiid",
    "trae young": "trae", "ja morant": "morant", "paolo banchero": "banchero", "karl-anthony towns": "towns",
    "austin reaves": "reaves", "rudy gobert": "gobert", "zaccharie risacher": "risacher", "alex sarr": "sarr",
    "alexandre sarr": "sarr", "bilal coulibaly": "coulibaly",
}


def _norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z\- ]", "", s).strip()


def find(first, last):
    key = NAMES.get(_norm(f"{first} {last}"))
    p = key and os.path.join(ASSETS, key + ".png")
    return Image.open(p).convert("RGBA") if p and os.path.exists(p) else None


def fit(ph, bw, bh):
    k = min(bw / ph.width, bh / ph.height)
    return ph.resize((max(1, int(ph.width * k)), max(1, int(ph.height * k))), Image.LANCZOS)


def sticker(ph, px=10):
    """Contour blanc + ombre portée."""
    pad = px * 4
    a = ph.getchannel("A").point(lambda v: 255 if v > 60 else 0)
    A = Image.new("L", (ph.width + 2 * pad, ph.height + 2 * pad), 0); A.paste(a, (pad, pad))
    st = A.filter(ImageFilter.MaxFilter(2 * (px // 2) + 1)).filter(ImageFilter.MaxFilter(2 * (px // 2) + 1)).filter(ImageFilter.GaussianBlur(1.2))
    out = Image.new("RGBA", A.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", A.size, (0, 0, 0, 255)); sh.putalpha(st.filter(ImageFilter.GaussianBlur(20)).point(lambda v: int(v * 0.8)))
    out.alpha_composite(sh, (12, 18))
    wl = Image.new("RGBA", A.size, (255, 255, 255, 255)); wl.putalpha(st); out.alpha_composite(wl)
    out.alpha_composite(ph, (pad, pad))
    return out


def head_box(ph):
    a = np.array(ph.getchannel("A")) > 40
    rows = np.where(a.any(1))[0]; top = int(rows[0]) if len(rows) else 0
    full = ph.height / ph.width > 1.25
    side = int(ph.height * 0.17) if full else (int(ph.height * 0.62) if ph.height < ph.width else int(ph.width * 0.46))
    band = a[top:top + max(4, int(side * 0.6))]
    xs = np.where(band.any(0))[0]
    cx = int(xs.mean()) if len(xs) else ph.width // 2
    x0 = max(0, min(ph.width - side, cx - side // 2)); y0 = max(0, top - int(side * 0.06))
    return (x0, y0, x0 + side, y0 + side)


def avatar(ph, size, ring):
    face = ph.crop(head_box(ph)).resize((size - 16, size - 16), Image.LANCZOS)
    av = Image.new("RGBA", (size, size), (0, 0, 0, 0)); ImageDraw.Draw(av).ellipse([0, 0, size - 1, size - 1], fill=tuple(ring) + (255,))
    bg = Image.new("RGBA", face.size, (30, 30, 40, 255)); bg.alpha_composite(face)
    m = Image.new("L", face.size, 0); ImageDraw.Draw(m).ellipse([0, 0, face.width - 1, face.height - 1], fill=255)
    av.paste(bg, (8, 8), m)
    return av


def prepare(first, last, ring):
    ph = find(first, last)
    if ph is None:
        return None
    full = ph.height / ph.width > 1.25
    return {"raw": ph, "hook": sticker(fit(ph, 900, 820 if full else 700)), "avatar": avatar(ph, 300, ring)}
