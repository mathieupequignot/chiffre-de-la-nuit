"""Voix off : ElevenLabs avec horodatage des caractères (pour caler les animations).
Sans clé ElevenLabs (tests), produit un silence de la bonne durée estimée."""
import base64
import os
import subprocess
import requests

MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")


def synth(segments, out_wav, voice_settings=None):
    """segments: [(cue, texte)]. Écrit out_wav (48 kHz stéréo) et renvoie [(cue, debut_s, fin_s)] + durée totale."""
    text = " ".join(t for _, t in segments)
    bounds, pos = [], 0
    for cue, t in segments:
        bounds.append((cue, pos, pos + len(t)))
        pos += len(t) + 1
    key, voice = os.environ.get("ELEVENLABS_API_KEY"), os.environ.get("ELEVENLABS_VOICE_ID")
    if key and voice:
        errors = []
        js = None
        # on essaie plusieurs modèles : certaines voix de la bibliothèque n'acceptent que certains modèles
        for model in dict.fromkeys([MODEL, "eleven_multilingual_v2", "eleven_v3", "eleven_turbo_v2_5", "eleven_flash_v2_5"]):
            for settings in (voice_settings or {"stability": 0.4, "similarity_boost": 0.75, "style": 0.3, "use_speaker_boost": True}, None):
                body = {"text": text, "model_id": model}
                if settings:
                    body["voice_settings"] = settings
                r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice.strip()}/with-timestamps",
                                  headers={"xi-api-key": key.strip(), "Content-Type": "application/json"}, json=body, timeout=180)
                if r.ok:
                    js = r.json(); print("Voix générée avec le modèle", model); break
                errors.append(f"{model} -> {r.status_code} {r.text[:300]}")
                if r.status_code in (401, 404):
                    break
            if js or (errors and errors[-1].split(" -> ")[1][:3] in ("401", "404")):
                break
        if js is None:
            raise RuntimeError("ElevenLabs a refusé la demande :\n" + "\n".join(errors))
        mp3 = out_wav.replace(".wav", ".mp3")
        open(mp3, "wb").write(base64.b64decode(js["audio_base64"]))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", "48000", "-ac", "2", out_wav], check=True)
        al = js.get("alignment") or js.get("normalized_alignment")
        starts, ends = al["character_start_times_seconds"], al["character_end_times_seconds"]
        n = len(starts)
        cues = [(c, starts[min(a, n - 1)], ends[min(max(b - 1, 0), n - 1)]) for c, a, b in bounds]
        total = ends[-1]
    else:  # mode test : ~14 caractères par seconde, pauses entre phrases
        cues, t = [], 0.0
        for c, a, b in bounds:
            d = (b - a) / 14.0
            cues.append((c, t, t + d)); t += d + 0.35
        total = t
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{total:.2f}", out_wav], check=True)
    return cues, total
