import os,requests
H={"xi-api-key":os.environ["ELEVENLABS_API_KEY"].strip()}
for u in ["https://api.elevenlabs.io/v1/user/subscription","https://api.elevenlabs.io/v1/voices/"+os.environ["ELEVENLABS_VOICE_ID"].strip(),"https://api.elevenlabs.io/v1/shared-voices?language=fr&page_size=3"]:
    r=requests.get(u,headers=H,timeout=30); print(u.split('/v1/')[1][:40], r.status_code, r.text[:300])
