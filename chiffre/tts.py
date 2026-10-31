"""Voix off : ElevenLabs avec horodatage des caractères (pour caler les animations).
Sans clé ElevenLabs (tests), produit un silence de la bonne durée estimée."""
import base64
import os
import subprocess
import requests

MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")


def synth(segments, out_wav):
    """segments: [(cue, texte)]. Écrit out_wav (48 kHz stéréo) et renvoie [(cue, debut_s, fin_s)] + durée totale."""
    text = " ".join(t for _, t in segments)
    bounds, pos = [], 0
    for cue, t in segments:
        bounds.append((cue, pos, pos + len(t)))
        pos += len(t) + 1
    key, voice = os.environ.get("ELEVENLABS_API_KEY"), os.environ.get("ELEVENLABS_VOICE_ID")
    if key and voice:
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps",
                          headers={"xi-api-key": key, "Content-Type": "application/json"},
                          json={"text": text, "model_id": MODEL,
                                "voice_settings": {"stability": 0.4, "similarity_boost": 0.75, "style": 0.3, "use_speaker_boost": True}},
                          timeout=120)
        r.raise_for_status()
        js = r.json()
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
