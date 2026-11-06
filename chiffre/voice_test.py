"""Génère des extraits de voix à comparer (modèles, voix, écriture). Sorties dans docs/voix/."""
import base64, json, os, requests
K = os.environ["ELEVENLABS_API_KEY"].strip(); CUR = os.environ["ELEVENLABS_VOICE_ID"].strip()
H = {"xi-api-key": K, "Content-Type": "application/json"}
OUT = "docs/voix"; os.makedirs(OUT, exist_ok=True)

ROBOT = ("Le meilleur joueur de la nuit, c'est lui. 27 points. 13 rebonds. 2 passes. Cette nuit, Wendell Carter Junior a signé "
         "le meilleur match de la nuit avec Orlando face à Phoenix. Le tout avec une adresse redoutable : 10 tirs réussis sur 12.")
NATUREL = ("Le meilleur joueur de la nuit… c'est lui. Wendell Carter Junior ! 27 points, 13 rebonds… et à 10 sur 12 au tir, "
           "s'il vous plaît ! Bon… Orlando a quand même perdu contre Phoenix. Mais franchement, quel match !")
V3 = ("[excited] Le meilleur joueur de la nuit… c'est lui. Wendell Carter Junior ! 27 points, 13 rebonds… "
      "[impressed] et à 10 sur 12 au tir, s'il vous plaît ! [sighs] Bon… Orlando a quand même perdu contre Phoenix. "
      "[excited] Mais franchement, quel match !")


def tts(voice, text, model, settings, name):
    body = {"text": text, "model_id": model}
    if settings: body["voice_settings"] = settings
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}", headers=H, json=body, timeout=180)
    if r.ok:
        open(f"{OUT}/{name}.mp3", "wb").write(r.content); print("OK", name)
    else:
        print("ÉCHEC", name, r.status_code, r.text[:200])


# voix actuelle
info = requests.get(f"https://api.elevenlabs.io/v1/voices/{CUR}", headers=H, timeout=30).json()
print("Voix actuelle :", info.get("name"), info.get("labels"))
#tts(CUR, ROBOT, "eleven_multilingual_v2", {"stability": 0.4, "similarity_boost": 0.75, "style": 0.3, "use_speaker_boost": True}, "1_actuel")
#tts(CUR, NATUREL, "eleven_multilingual_v2", {"stability": 0.35, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True}, "2_actuel_texte_naturel")
#tts(CUR, V3, "eleven_v3", {"stability": 0.5}, "3_actuel_v3")

# voix françaises de la bibliothèque (hommes, style commentateur / narration)
sv = requests.get("https://api.elevenlabs.io/v1/shared-voices", headers=H, timeout=30, params={
    "language": "fr", "gender": "male", "page_size": 30, "sort": "usage_character_count_1y"}).json().get("voices", [])
cands = [v for v in sv if v.get("accent") in (None, "", "parisian", "standard", "french", "france") or "fr" in str(v.get("locale", "")).lower()]
print("Candidates :", [(v["name"], v.get("accent"), v.get("use_case"), v.get("descriptive")) for v in cands[:12]])
k = 4
for v in cands[:12]:
    if k > 6: break
    vid = v["voice_id"]
    add = requests.post(f"https://api.elevenlabs.io/v1/voices/add/{v['public_owner_id']}/{vid}", headers=H,
                        json={"new_name": f"FR test {v['name']}"[:40]}, timeout=30)
    use = add.json().get("voice_id", vid) if add.ok else vid
    if not add.ok: print("ajout impossible", v["name"], add.status_code, add.text[:150])
    tts(use, V3, "eleven_v3", {"stability": 0.5}, f"{k}_{v['name'].split()[0].lower()}_v3")
    if os.path.exists(f"{OUT}/{k}_{v['name'].split()[0].lower()}_v3.mp3"):
        json.dump({"name": v["name"], "voice_id": use, "desc": v.get("description", "")[:200]}, open(f"{OUT}/{k}.json", "w"), ensure_ascii=False)
        k += 1
