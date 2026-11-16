"""Rapport du soir : vues de chaque vidéo publiée la veille, réseau par réseau, envoyé sur Discord (image + résumé).
python -m publish.report [--date AAAA-MM-JJ] [--no-post]
Chaque réseau est facultatif : s'il ne répond pas, sa colonne affiche « – » et le rapport part quand même."""
import argparse
import datetime as dt
import json
import os
import re
from zoneinfo import ZoneInfo

import requests

PARIS = ZoneInfo("Europe/Paris")
G = "https://graph.facebook.com/v23.0"
HERE = os.path.dirname(os.path.abspath(__file__))
NETS = [("tiktok", "TikTok"), ("instagram", "Insta"), ("youtube", "YouTube"), ("facebook", "Facebook")]
KIND = [("chiffre_", "Chiffre de la nuit"), ("quiz_", "Quiz"), ("top5_", "5 trucs fous"), ("duel_", "Duel"),
        ("drill_", "Drill"), ("saviez_", "Le savais-tu"), ("top10_", "10 trucs fous")]


# ---------- vues par réseau (None = indisponible)
def ig_views(mid):
    tok = os.environ.get("IG_TOKEN", "").strip()
    if not (tok and mid):
        return None
    from publish.instagram import _base
    for metric in ("views", "plays"):
        j = requests.get(f"{_base()}/{mid}/insights", params={"metric": metric, "access_token": tok}, timeout=30).json()
        if j.get("data"):
            return int(j["data"][0]["values"][0]["value"])
    print("Instagram", mid, j.get("error", {}).get("message"))
    return None


def fb_views(vid):
    tok = os.environ.get("FB_PAGE_TOKEN", "").strip()
    if not (tok and vid):
        return None
    j = requests.get(f"{G}/{vid}/video_insights", params={"metric": "blue_reels_play_count,fb_reels_total_plays",
                                                          "access_token": tok}, timeout=30).json()
    vals = {d["name"]: d["values"][0]["value"] for d in j.get("data", []) if d.get("values")}
    for k in ("blue_reels_play_count", "fb_reels_total_plays"):
        if k in vals:
            return int(vals[k])
    print("Facebook", vid, j.get("error", {}).get("message"))
    return None


def yt_views(ids):
    ids = [i for i in ids if i]
    if not ids:
        return {}
    try:
        from publish import youtube
        h = {"Authorization": f"Bearer {youtube._access_token()}"}
        j = requests.get("https://www.googleapis.com/youtube/v3/videos", headers=h,
                         params={"part": "statistics", "id": ",".join(ids[:50])}, timeout=30).json()
        if "error" not in j:
            return {it["id"]: int(it["statistics"].get("viewCount", 0)) for it in j.get("items", [])}
        print("YouTube API :", j["error"].get("message"), "-> compteur public de la page")
    except Exception as e:
        print("YouTube API :", e, "-> compteur public de la page")
    out = {}   # repli : compteur public affiché sur la page de la vidéo
    for i in ids:
        try:
            html = requests.get(f"https://www.youtube.com/watch?v={i}", timeout=30,
                                headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "fr-FR"},
                                cookies={"CONSENT": "YES+1"}).text
            m = re.search(r'"viewCount":"(\d+)"', html)
            if m:
                out[i] = int(m.group(1))
        except Exception as e:
            print("YouTube page", i, e)
    return out


def tt_videos(day):
    """Vidéos TikTok publiées ce jour-là (nécessite le droit video.list ; activé avec TT_STATS=1)."""
    if os.environ.get("TT_STATS") != "1":
        return None
    try:
        from publish import tiktok
        h = {"Authorization": f"Bearer {tiktok._access_token()}", "Content-Type": "application/json"}
        out, cursor = [], None
        for _ in range(5):
            body = {"max_count": 20, **({"cursor": cursor} if cursor else {})}
            j = requests.post("https://open.tiktokapis.com/v2/video/list/?fields=id,title,video_description,create_time,view_count",
                              headers=h, json=body, timeout=30).json()
            if j.get("error", {}).get("code") not in (None, "ok"):
                print("TikTok :", j["error"]); return None
            vids = j.get("data", {}).get("videos", [])
            out += vids
            if not j["data"].get("has_more") or not vids or min(v["create_time"] for v in vids) < day_start(day).timestamp():
                break
            cursor = j["data"].get("cursor")
        a, b = day_start(day).timestamp(), day_start(day + dt.timedelta(days=1)).timestamp()
        return [v for v in out if a <= v["create_time"] < b]
    except Exception as e:
        print("TikTok :", e); return None


# ---------- abonnés par réseau (None = indisponible)
def _num(txt):
    """'1,2 k' / '1.2K' / '391' -> int."""
    m = re.search(r"([\d.,\s\u202f\xa0]+)\s*([kKmM])?", txt or "")
    if not m:
        return None
    n = m.group(1).replace("\u202f", "").replace("\xa0", "").replace(" ", "")
    mult = {"k": 1e3, "m": 1e6}.get((m.group(2) or "").lower(), 1)
    if mult > 1:
        return int(float(n.replace(",", ".")) * mult)
    return int(re.sub(r"[.,]", "", n)) if re.sub(r"[.,]", "", n).isdigit() else None


def followers(yt_video_id=None):
    out = {"tiktok": None, "instagram": None, "youtube": None, "facebook": None}
    tok = os.environ.get("IG_TOKEN", "").strip()
    if tok:
        try:
            from publish.instagram import _base
            uid = os.environ.get("IG_USER_ID", "").strip() or "me"
            j = requests.get(f"{_base()}/{uid}", params={"fields": "followers_count", "access_token": tok}, timeout=30).json()
            out["instagram"] = j.get("followers_count")
            if out["instagram"] is None: print("Abonnés Instagram :", j.get("error", {}).get("message"))
        except Exception as e:
            print("Abonnés Instagram :", e)
    ftok = os.environ.get("FB_PAGE_TOKEN", "").strip()
    if ftok:
        try:
            from publish.facebook import PAGE_ID
            j = requests.get(f"{G}/{PAGE_ID}", params={"fields": "followers_count,fan_count", "access_token": ftok}, timeout=30).json()
            out["facebook"] = j.get("followers_count", j.get("fan_count"))
            if out["facebook"] is None: print("Abonnés Facebook :", j.get("error", {}).get("message"))
        except Exception as e:
            print("Abonnés Facebook :", e)
    try:
        from publish import youtube
        h = {"Authorization": f"Bearer {youtube._access_token()}"}
        j = requests.get("https://www.googleapis.com/youtube/v3/channels", headers=h,
                         params={"part": "statistics", "mine": "true"}, timeout=30).json()
        if j.get("items"):
            out["youtube"] = int(j["items"][0]["statistics"].get("subscriberCount", 0))
        else:
            print("Abonnés YouTube API :", j.get("error", {}).get("message"), "-> page publique")
    except Exception as e:
        print("Abonnés YouTube API :", e)
    if out["youtube"] is None and yt_video_id:   # repli : compteur public de la chaîne
        out["youtube"] = yt_public_subs(yt_video_id)
    if os.environ.get("TT_STATS") != "1":   # nécessite le droit user.info.stats (et fait tourner le jeton TikTok)
        return out
    try:
        from publish import tiktok
        h = {"Authorization": f"Bearer {tiktok._access_token()}"}
        j = requests.get("https://open.tiktokapis.com/v2/user/info/?fields=follower_count", headers=h, timeout=30).json()
        fc = j.get("data", {}).get("user", {}).get("follower_count")
        out["tiktok"] = int(fc) if fc is not None else None
        if fc is None: print("Abonnés TikTok :", j.get("error"))
    except Exception as e:
        print("Abonnés TikTok :", e)
    return out


def yt_public_subs(video_id):
    hd = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept-Language": "en-US,en;q=0.9"}
    ck = {"CONSENT": "YES+1", "SOCS": "CAI"}
    pat = [r'"simpleText":"([\d.,]+[KM]?) subscribers?"', r'"content":"([\d.,]+[KM]?) subscribers?"',
           r'"label":"([\d.,]+[KM]?) subscribers?"', r'([\d.,]+[KM]?) subscribers?']
    try:
        html = requests.get(f"https://www.youtube.com/watch?v={video_id}", timeout=30, headers=hd, cookies=ck).text
        pages = [html]
        m = re.search(r'"channelId":"(UC[\w-]{22})"', html)
        if m:
            pages.append(requests.get(f"https://www.youtube.com/channel/{m.group(1)}", timeout=30, headers=hd, cookies=ck).text)
        for page in pages:
            for p in pat:
                m2 = re.search(p, page)
                if m2:
                    return _num(m2.group(1))
        print("Abonnés YouTube : compteur public introuvable", m and m.group(1), len(html))
    except Exception as e:
        print("Abonnés YouTube page :", e)
    return None


# ---------- boutique Shopify (visites + ventes du jour)
SHOP = os.environ.get("SHOPIFY_STORE", "1cvkuk-kx.myshopify.com").strip()
SHOP_API = "2025-10"


def _shop_token():
    """Jeton Admin API : SHOPIFY_TOKEN (shpat_…) ou, pour une appli du Dev Dashboard, SHOPIFY_CLIENT_ID + SHOPIFY_CLIENT_SECRET."""
    if os.environ.get("SHOPIFY_TOKEN", "").strip():
        return os.environ["SHOPIFY_TOKEN"].strip()
    cid, sec = os.environ.get("SHOPIFY_CLIENT_ID", "").strip(), os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()
    if not (cid and sec):
        return None
    j = requests.post(f"https://{SHOP}/admin/oauth/access_token", timeout=30,
                      data={"grant_type": "client_credentials", "client_id": cid, "client_secret": sec}).json()
    if "access_token" not in j:
        print("Shopify jeton :", j)
    return j.get("access_token")


def _shopql(tok, q):
    gql = "query($q: String!) { shopifyqlQuery(query: $q) { tableData { columns { name } rows } parseErrors } }"
    j = requests.post(f"https://{SHOP}/admin/api/{SHOP_API}/graphql.json", timeout=30, json={"query": gql, "variables": {"q": q}},
                      headers={"X-Shopify-Access-Token": tok}).json()
    r = (j.get("data") or {}).get("shopifyqlQuery") or {}
    if j.get("errors") or r.get("parseErrors"):
        print("ShopifyQL :", j.get("errors") or r.get("parseErrors"))
        return None
    rows = (r.get("tableData") or {}).get("rows") or []
    if isinstance(rows, str):
        rows = json.loads(rows)
    return rows[0] if rows else {}


def _f(v):
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return None


def shop_stats(day):
    """{'visits', 'orders', 'sales', 'currency'} pour la journée (None = indisponible)."""
    out = {"visits": None, "orders": None, "sales": None}
    try:
        tok = _shop_token()
        if not tok:
            return None
        d = str(day)
        r = _shopql(tok, f"FROM sessions SHOW sessions SINCE {d} UNTIL {d}")
        if r is not None:
            v = _f(r.get("sessions")) if isinstance(r, dict) else _f(r[0])
            out["visits"] = int(v) if v is not None else 0
        r = _shopql(tok, f"FROM sales SHOW orders, total_sales SINCE {d} UNTIL {d}")
        if r is not None:
            o, t = (r.get("orders"), r.get("total_sales")) if isinstance(r, dict) else (r[0], r[1])
            out["orders"] = int(_f(o) or 0)
            out["sales"] = _f(t) or 0.0
        if out["orders"] is None:   # repli : comptage direct des commandes
            a, b = day_start(day).isoformat(), day_start(day + dt.timedelta(days=1)).isoformat()
            gql = "query($q: String!) { orders(first: 100, query: $q) { nodes { totalPriceSet { shopMoney { amount } } } } }"
            j = requests.post(f"https://{SHOP}/admin/api/{SHOP_API}/graphql.json", timeout=30,
                              json={"query": gql, "variables": {"q": f"created_at:>='{a}' created_at:<'{b}'"}},
                              headers={"X-Shopify-Access-Token": tok}).json()
            nodes = ((j.get("data") or {}).get("orders") or {}).get("nodes")
            if nodes is not None:
                out["orders"] = len(nodes)
                out["sales"] = sum(float(n["totalPriceSet"]["shopMoney"]["amount"]) for n in nodes)
            else:
                print("Shopify commandes :", j.get("errors"))
    except Exception as e:
        print("Shopify :", e)
    return out


HIST = os.path.join(HERE, "stats_history.json")


def save_followers(day, f):
    """Garde un relevé par jour ; renvoie la variation depuis le relevé précédent."""
    try:
        h = json.load(open(HIST, encoding="utf-8"))
    except Exception:
        h = {}
    prev = max((d for d in h if d < str(day)), default=None)
    delta = {k: (v - h[prev][k]) if (prev and isinstance(v, int) and isinstance(h[prev].get(k), int)) else None
             for k, v in f.items()}
    h[str(day)] = {**{k: v for k, v in f.items()}, **{k: h.get(str(day), {}).get(k) for k, v in f.items() if v is None}}
    json.dump(dict(sorted(h.items())), open(HIST, "w", encoding="utf-8"), indent=1)
    return delta


def day_start(d):
    return dt.datetime(d.year, d.month, d.day, tzinfo=PARIS)


def _words(t):
    return set(re.findall(r"[a-zà-ÿ0-9]{4,}", (t or "").lower()))


# ---------- rapport
def label(e):
    kind = next((n for p, n in KIND if e["key"].startswith(p)), e["key"].split("_")[0])
    t = re.sub(r"\s*#\w+", "", e.get("yt_title") or "").replace("🤯", "").strip()
    if not t:
        t = (e.get("instagram") or "").split("\n")[0]
    return kind, t[:60]


def collect(day):
    q = json.load(open(os.path.join(HERE, "queue.json"), encoding="utf-8"))
    rows = []
    for e in q:
        at = dt.datetime.fromisoformat(e["at"]).astimezone(PARIS)
        if at.date() != day:
            continue
        if not any(v == "ok" for v in e.get("status", {}).values()):
            continue
        kind, title = label(e)
        rows.append(dict(e=e, at=at, kind=kind, title=title, ids=e.get("ids", {}), v={}))
    rows.sort(key=lambda r: r["at"])
    yt = yt_views([r["ids"].get("youtube") for r in rows])
    tt = tt_videos(day)
    for r in rows:
        st, ids = r["e"].get("status", {}), r["ids"]
        r["v"]["instagram"] = ig_views(ids.get("instagram")) if st.get("instagram") == "ok" else "×"
        r["v"]["facebook"] = fb_views(ids.get("facebook")) if st.get("facebook") == "ok" else "×"
        r["v"]["youtube"] = yt.get(ids.get("youtube")) if st.get("youtube") == "ok" else "×"
        if st.get("tiktok") != "ok":
            r["v"]["tiktok"] = "×"
        elif tt is None:
            r["v"]["tiktok"] = None
        else:   # brouillon publié à la main : on retrouve la vidéo par sa description
            ref = _words(r["e"].get("tiktok_caption") or r["e"].get("instagram"))
            best = max(tt, key=lambda v: len(ref & _words(v.get("video_description") or v.get("title"))), default=None)
            ok = best and len(ref & _words(best.get("video_description") or best.get("title"))) >= 3
            r["v"]["tiktok"] = int(best["view_count"]) if ok else "?"
            if ok:
                tt.remove(best)
    return rows, tt


def fmt(n):
    if n is None: return "–"
    if isinstance(n, str): return n
    if n >= 10000: return f"{n / 1000:.0f}k".replace(".", ",")
    if n >= 1000: return f"{n / 1000:.1f}k".replace(".", ",")
    return str(n)


def image(day, rows, out, fol=None, dfol=None, shop=None):
    from PIL import Image, ImageDraw
    from chiffre.render import font
    W, PAD, RH = 1080, 40, 118
    H = 260 + RH * (len(rows) + 1) + (290 if fol else 120) + (250 if shop else 0)
    im = Image.new("RGB", (W, H), (14, 14, 18)); d = ImageDraw.Draw(im)
    OR, WH, GR, GN = (255, 122, 26), (245, 245, 245), (140, 142, 152), (80, 220, 120)
    d.text((PAD, 50), "RAPPORT DES VUES", font=font("Black", 64), fill=OR)
    d.text((PAD, 130), f"Vidéos du {day.strftime('%d/%m/%Y')} · relevé le {dt.datetime.now(PARIS).strftime('%d/%m à %Hh%M')}",
           font=font("SemiBold", 30), fill=GR)
    cols = [560, 690, 820, 950]   # centres des colonnes réseaux
    y = 210
    for (k, n), x in zip(NETS, cols):
        d.text((x, y + 20), n, font=font("ExtraBold", 24), fill=GR, anchor="mm")
    y += 60
    tot = {k: 0 for k, _ in NETS}
    for i, r in enumerate(rows):
        if i % 2 == 0:
            d.rounded_rectangle([PAD - 10, y, W - PAD + 10, y + RH - 10], 18, fill=(24, 24, 30))
        d.text((PAD + 6, y + 14), f"{r['at'].strftime('%Hh%M')} · {r['kind'].upper()}", font=font("ExtraBold", 26), fill=OR)
        t = r["title"]
        while font("SemiBold", 30).getlength(t) > 470 and len(t) > 5: t = t[:-2]
        d.text((PAD + 6, y + 54), t if t == r["title"] else t.rstrip() + "…", font=font("SemiBold", 30), fill=WH)
        best = max([v for v in r["v"].values() if isinstance(v, int)], default=None)
        for (k, _), x in zip(NETS, cols):
            v = r["v"].get(k)
            if isinstance(v, int): tot[k] += v
            d.text((x, y + RH / 2 - 5), fmt(v), font=font("Black", 38), fill=GN if v == best and best else WH, anchor="mm")
        y += RH
    d.line([PAD, y + 5, W - PAD, y + 5], fill=(60, 60, 70), width=3)
    d.text((PAD + 6, y + 50), "TOTAL", font=font("Black", 40), fill=OR, anchor="lm")
    for (k, _), x in zip(NETS, cols):
        has = any(isinstance(r["v"].get(k), int) for r in rows)
        d.text((x, y + 50), fmt(tot[k]) if has else "–", font=font("Black", 40), fill=OR, anchor="mm")
    if fol:
        y += 130
        d.rounded_rectangle([PAD - 10, y, W - PAD + 10, y + 210], 22, fill=(30, 26, 22))
        d.text((PAD + 10, y + 40), "ABONNÉS", font=font("Black", 44), fill=OR, anchor="lm")
        d.text((PAD + 10, y + 95), f"au {dt.datetime.now(PARIS).strftime('%d/%m')}", font=font("SemiBold", 28), fill=GR, anchor="lm")
        d.text((PAD + 10, y + 160), "TOTAL " + fmt(sum(v for v in fol.values() if isinstance(v, int))),
               font=font("Black", 34), fill=WH, anchor="lm")
        for (k, n), x in zip(NETS, cols):
            d.text((x, y + 40), n, font=font("ExtraBold", 26), fill=GR, anchor="mm")
            d.text((x, y + 105), fmt(fol.get(k)), font=font("Black", 44), fill=WH, anchor="mm")
            dv = (dfol or {}).get(k)
            if isinstance(dv, int):
                d.text((x, y + 160), f"{dv:+d}", font=font("ExtraBold", 32), fill=GN if dv > 0 else (GR if dv == 0 else (240, 80, 80)), anchor="mm")
        y += 210
    if shop:
        y += 30
        d.rounded_rectangle([PAD - 10, y, W - PAD + 10, y + 210], 22, fill=(20, 28, 24))
        d.text((PAD + 10, y + 40), "BOUTIQUE", font=font("Black", 44), fill=GN, anchor="lm")
        d.text((PAD + 10, y + 95), f"le {day.strftime('%d/%m')}", font=font("SemiBold", 28), fill=GR, anchor="lm")
        sales = shop.get("sales")
        cells = [("Visites", fmt(shop.get("visits")), 560), ("Ventes", fmt(shop.get("orders")), 755),
                 ("Encaissé", "–" if sales is None else f"{sales:.2f} €".replace(".", ","), 950)]
        for lab, val, x in cells:
            d.text((x, y + 40), lab, font=font("ExtraBold", 26), fill=GR, anchor="mm")
            d.text((x, y + 110), val, font=font("Black", 44), fill=WH, anchor="mm")
    im.save(out, quality=92)
    return out, tot


def fol_line(fol, dfol):
    if not fol or not any(isinstance(v, int) for v in fol.values()):
        return None
    parts = []
    for k, n in NETS:
        v, dv = fol.get(k), (dfol or {}).get(k)
        parts.append(f"{n} {fmt(v)}" + (f" ({dv:+d})" if isinstance(dv, int) else ""))
    tot = sum(v for v in fol.values() if isinstance(v, int))
    return "👥 Abonnés : " + " · ".join(parts) + f" — total {tot:,}".replace(",", " ")


def shop_line(shop):
    if not shop or all(v is None for v in shop.values()):
        return None
    sales = shop.get("sales")
    return (f"🛒 Boutique : {fmt(shop.get('visits'))} visites · {fmt(shop.get('orders'))} vente(s)"
            + ("" if sales is None else f" · {sales:.2f} €".replace(".", ",")))


def summary(day, rows, tot, extra_tt, fol=None, dfol=None, shop=None):
    fl = "\n".join(x for x in (fol_line(fol, dfol), shop_line(shop)) if x) or None
    if not rows:
        return f"📊 **Rapport du {day.strftime('%d/%m')}** : aucune vidéo publiée ce jour-là." + (f"\n{fl}" if fl else "")
    allv = sum(v for v in tot.values())
    best = max(rows, key=lambda r: sum(v for v in r["v"].values() if isinstance(v, int)))
    bv = sum(v for v in best["v"].values() if isinstance(v, int))
    by_net = max(((k, n) for k, n in NETS), key=lambda kn: tot[kn[0]])
    sp = lambda n: f"{n:,}".replace(",", " ")
    lines = [f"📊 **Rapport du {day.strftime('%d/%m')}** — {len(rows)} vidéos, **{sp(allv)} vues** au total"]
    if fl:
        lines.append(fl)
    if allv:
        lines += [f"🏆 Meilleure vidéo : {best['kind']} — {best['title']} ({sp(bv)} vues)",
                  f"📱 Meilleur réseau : {by_net[1]} ({sp(tot[by_net[0]])} vues)"]
    manque = [n for k, n in NETS if any(r["v"].get(k) is None for r in rows)]
    if manque:
        lines.append(f"ℹ️ Vues pas encore accessibles : {', '.join(manque)} (autorisation de lecture des stats à ajouter).")
    if extra_tt:
        lines.append("TikTok, autres vidéos du jour : " + " · ".join(f"{(v.get('title') or '')[:30]} ({fmt(v['view_count'])})" for v in extra_tt[:5]))
    lines.append("« × » = pas publiée sur ce réseau · « – » = chiffre indisponible")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date"); ap.add_argument("--no-post", action="store_true")
    a = ap.parse_args()
    day = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(PARIS).date() - dt.timedelta(days=1)
    rows, extra = collect(day)
    yid = next((r["ids"].get("youtube") for r in rows if r["ids"].get("youtube")), None)
    if not yid:
        q = json.load(open(os.path.join(HERE, "queue.json"), encoding="utf-8"))
        yid = next((e.get("ids", {}).get("youtube") for e in reversed(q) if e.get("ids", {}).get("youtube")), None)
    fol = followers(yid)
    print("Abonnés :", fol)
    dfol = save_followers(dt.datetime.now(PARIS).date(), fol) if not a.no_post else {}
    os.makedirs("out_report", exist_ok=True)
    shop = shop_stats(day)
    print("Boutique :", shop)
    png, tot = image(day, rows, f"out_report/rapport_{day}.jpg", fol, dfol, shop)
    msg = summary(day, rows, tot, extra, fol, dfol, shop)
    print(msg)
    for r in rows: print(r["kind"], r["title"], r["v"])
    if a.no_post:
        print("(test : rien envoyé sur Discord)")
    else:
        from chiffre import discord_post
        if rows:
            discord_post.notify_file(msg, png, f"rapport_{day}.jpg")
        else:
            discord_post.notify(msg)


if __name__ == "__main__":
    main()
