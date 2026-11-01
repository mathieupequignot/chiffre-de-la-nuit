"""Miniature (couverture) 1080x1920 du chiffre de la nuit : bandeau série, chiffre géant, joueur, date.
Tout le contenu clé reste dans la zone centrale 3:4 (recadrage de la grille TikTok / Instagram)."""
import random
from PIL import Image, ImageDraw, ImageFilter
from .render import font, ACCENT, WHITE, GREY

W, H = 1080, 1920


def _spaced(d, txt, w, size, x, y, fill, sp=0, maxw=980):
    while True:
        f = font(w, size)
        tw = sum(f.getlength(c) for c in txt) + sp * (len(txt) - 1)
        if tw <= maxw or size <= 20: break
        size -= 2
    cx = x - tw / 2
    for c in txt:
        d.text((cx, y), c, font=f, fill=fill, anchor="lm"); cx += f.getlength(c) + sp
    return tw


def _fit(txt, w, size, maxw):
    while font(w, size).getlength(txt) > maxw and size > 20: size -= 4
    return font(w, size)


def make(num, unit, first, last, extra, date, team_col, out):
    im = Image.new("RGB", (W, H), (8, 8, 11))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([-300, -200, 700, 800], fill=tuple(team_col) + (110,))
    gd.ellipse([300, 500, 1400, 1500], fill=ACCENT + (95,))
    g = g.filter(ImageFilter.GaussianBlur(220))
    im.paste(g, (0, 0), g)
    random.seed(1)
    im.paste((255, 255, 255), (0, 0), Image.effect_noise((W, H), 40).point(lambda v: max(0, v - 140) // 5))
    d = ImageDraw.Draw(im)
    t = "LE CHIFFRE DE LA NUIT"; f = font("ExtraBold", 44)
    tw = sum(f.getlength(c) for c in t) + 6 * (len(t) - 1)
    d.rounded_rectangle([W / 2 - tw / 2 - 40, 340, W / 2 + tw / 2 + 40, 430], 45, fill=ACCENT)
    _spaced(d, t, "ExtraBold", 44, W / 2, 386, (12, 12, 16), 6)
    fn = _fit(num, "Black", 560, 900)
    d.text((W / 2 + 8, 830), num, font=fn, fill=(0, 0, 0), anchor="mm")
    d.text((W / 2, 820), num, font=fn, fill=ACCENT, anchor="mm")
    _spaced(d, unit, "ExtraBold", 92, W / 2, 1135, WHITE, 18)
    d.line([W / 2 - 90, 1225, W / 2 + 90, 1225], fill=ACCENT, width=6)
    _spaced(d, first, "SemiBold", 52, W / 2, 1300, GREY, 10)
    d.text((W / 2, 1385), last, font=_fit(last, "Black", 124, 960), fill=WHITE, anchor="mm")
    if extra: _spaced(d, extra, "ExtraBold", 44, W / 2, 1490, ACCENT, 4)
    _spaced(d, date, "SemiBold", 34, W / 2, 1575, GREY, 5)
    _spaced(d, "NBA DAILY NEWS", "ExtraBold", 36, W / 2, 1790, (90, 92, 104), 8)
    im.save(out, quality=92)
    return out


def from_D(D, out):
    c = D["cover"]
    return make(c["num"], c["unit"], D["first"], D["last"], c["extra"], D["date_label"], D["me"]["bg"], out)
