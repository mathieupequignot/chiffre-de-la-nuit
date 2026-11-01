"""Récupère sur Wikipédia (anglais) l'historique de carrière (années + équipes NBA) de chaque joueur de players.json.
Lien joueur -> page via Wikidata (identifiant Basketball-Reference, propriété P2685). Écrit quiz/wiki_careers.json."""
import html, json, os, re, time
import requests

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "nba-daily-news-quiz/1.0 (github.com/mathieupequignot/chiffre-de-la-nuit)"}
players = json.load(open(os.path.join(HERE, "players.json"), encoding="utf-8"))
ids = " ".join(f'"{p["id"]}"' for p in players)
q = f"""SELECT ?bref ?article WHERE {{ VALUES ?bref {{ {ids} }} ?item wdt:P2685 ?bref .
 ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> . }}"""
r = requests.get("https://query.wikidata.org/sparql", params={"query": q, "format": "json"}, headers=UA, timeout=60)
r.raise_for_status()
titles = {b["bref"]["value"]: b["article"]["value"].rsplit("/", 1)[1] for b in r.json()["results"]["bindings"]}
out = {}
for p in players:
    t = titles.get(p["id"])
    if not t:
        out[p["id"]] = {"error": "pas de page"}; continue
    rr = requests.get("https://en.wikipedia.org/w/api.php", headers=UA, timeout=60,
                      params={"action": "parse", "page": requests.utils.unquote(t), "prop": "text", "section": 0,
                              "format": "json", "redirects": 1})
    txt = rr.json().get("parse", {}).get("text", {}).get("*", "")
    m = re.search(r"Career history(.*?)(Career highlights|Stats at|Medals|</table>)", txt, re.S)
    rows = []
    if m:
        for yrs, team in re.findall(r'<th[^>]*infobox-label[^>]*>(.*?)</th>\s*<td[^>]*infobox-data[^>]*>(.*?)</td>', m.group(1), re.S):
            clean = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
            rows.append([clean(yrs), clean(team)])
    out[p["id"]] = {"page": t, "career": rows}
    time.sleep(0.3)
json.dump(out, open(os.path.join(HERE, "wiki_careers.json"), "w"), ensure_ascii=False, indent=1)
print(sum(1 for v in out.values() if v.get("career")), "/", len(out), "parcours récupérés")
