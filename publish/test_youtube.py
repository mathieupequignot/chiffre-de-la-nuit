"""Test : envoie une courte vidéo en PRIVÉ sur la chaîne pour vérifier les accès YouTube."""
import os, subprocess
from chiffre import discord_post
from . import youtube

os.environ["YT_PRIVACY"] = "private"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x14141a:s=1080x1920:d=4",
                "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest", "-vf",
                "drawtext=text='TEST AUTOMATISATION':fontcolor=orange:fontsize=70:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "test.mp4"], check=True)
vid = youtube.upload("test.mp4", "Test automatisation (privé) #Shorts", "Vidéo de test, à supprimer.")
print("OK, vidéo privée :", vid)
discord_post.notify(f"🧪 Test YouTube réussi : vidéo privée envoyée (https://youtube.com/shorts/{vid}). Tu peux la supprimer dans YouTube Studio.")
