# Le chiffre de la nuit

Chaque matin, ce robot :
1. récupère les matchs NBA de la nuit (API-NBA) ;
2. choisit la performance la plus marquante ;
3. écrit le texte et le fait lire par la voix ElevenLabs ;
4. monte une vidéo verticale 1080×1920 ;
5. l'envoie dans le salon Discord de validation avec la légende proposée.

## Lancer un test
Onglet **Actions → Chiffre de la nuit → Run workflow**. Champ « date » vide = aujourd'hui, ou une date `AAAA-MM-JJ`.

## Secrets nécessaires (Settings → Secrets and variables → Actions)
`API_NBA_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`.

## Test sans aucune clé, sur ton ordinateur
`python -m chiffre.main --date 2026-10-31 --fixture fixtures/sample_night.json --no-post`
(la voix est remplacée par un silence).

Polices : Inter (SIL Open Font License). Badges d'équipe originaux, sans logo officiel.
