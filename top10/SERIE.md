# Série « 5 trucs fous sur… » — mode d'emploi et carnet d'apprentissage

Ce fichier est lu (et mis à jour) à chaque nouvel épisode. Il contient la recette du format,
les règles à ne jamais enfreindre et ce qu'on a appris épisode après épisode.

## La recette (v1 — 9 nov. 2026)
- **5 faits**, vidéo de **30 à 40 s**, décompte du n°5 au n°1, barre de progression en haut.
- **Accroche dès la 1re image** : titre géant (« 5 TRUCS FOUS / SUR <JOUEUR> ») + phrase d'accroche
  à la voix (« Tu crois connaître X ? … »). Jamais d'écran vide au début.
- **Sous-titres mot à mot** (mot prononcé en jaune), voix « Mathieu NBA » (eleven_v3, +12 % de vitesse),
  balises d'émotion [excited], [laughs], [surprised] avec parcimonie.
- **Le n°1 est la meilleure chute** : drôle ou improbable (c'est lui qui fait partager). Le n°5 doit déjà
  accrocher (pas de fait banal en ouverture).
- **Mélanger les types de faits** : un chiffre physique, une anecdote d'enfance, une anecdote hors terrain,
  une histoire drôle. Éviter 5 stats d'affilée.
- **Fin** : « Lequel t'a le plus surpris ? » + « Tu choisis le joueur du prochain épisode » (pousse aux commentaires).
- **Joueurs prioritaires** : ceux que le public FR suit (Wemby et les Français, puis LeBron, Curry, Jokić,
  Dončić, Giannis, Edwards, SGA…), ou le joueur le plus réclamé en commentaire.
- **Publication** : 1 épisode par semaine, le samedi vers 18 h 30 (Instagram + YouTube auto, brouillon TikTok
  quelques heures avant), en plus du chiffre de la nuit et du quiz.

## Miniature (v2, 10/11)
Fond aux couleurs de l'équipe (table TEAM dans top10/main.py, ou champ JSON `color`), rayons, joueur détouré avec contour blanc
+ ombre, badge rond « 5 », nom géant jaune incliné, bandeau rouge (champ JSON optionnel `cover_tag`, défaut « LE N°1 VA TE CHOQUER »).
Nouveau joueur hors table : ajouter sa couleur dans TEAM.

## Programme des joueurs (photos fournies par Mathieu dans top10/assets/)
Rythme : 2 épisodes par semaine, mercredi et samedi à 18:30 (préparés le lundi et le jeudi). Passage à 3/semaine
à réévaluer après 2–3 semaines selon les stats. Ordre de passage par défaut : Si un joueur est très réclamé en commentaire ou fait l'actualité
de la semaine, on peut le faire passer devant. Joueur traité = on le coche [x].
- [x] Victor Wembanyama — wemby.png (épisodes 1 et 2)
- [x] LeBron James — lebron.png (épisode du 18 nov. 2026)
- [ ] Stephen Curry — curry.png
- [ ] Luka Dončić — doncic.png
- [ ] Giannis Antetokounmpo — giannis.png
- [ ] Shai Gilgeous-Alexander — sga.png
- [ ] Anthony Edwards — edwards.png
- [ ] Nikola Jokić — jokic.png
- [ ] Kevin Durant — durant.png
- [ ] Cooper Flagg — flagg.png
- [ ] Kyrie Irving — kyrie.png
Critère de choix : uniquement des superstars très connues du grand public (objectif : un maximum de vues).
Si la photo du joueur est présente dans top10/assets/, mettre `"photo": "<fichier>"` dans le JSON de l'épisode.
**Quand il ne reste plus que 4 joueurs non traités avec photo**, le signaler à Mathieu sur Discord pour qu'il en envoie
de nouvelles (avec une proposition de prochains joueurs : superstars actuelles et légendes très connues —
Jordan, Kobe, Shaq, Iverson, Magic, Bird, Dirk, Tony Parker…).

## Règles absolues
1. **Chaque fait est vérifié par au moins 2 sources fiables** (ESPN, The Athletic, L'Équipe, AP, NBA.com,
   CBS, Basketball-Reference, presse nationale…). Les sources sont listées dans le JSON de l'épisode.
   Aucune rumeur, aucun fait « on dit que ». Dans le doute, on enlève le fait.
2. Pas d'image de match ni de musique protégée. Jamais de photo trouvée sur le web par Claude : on utilise uniquement
   les photos fournies par Mathieu (top10/assets/) ; sans photo, silhouette du joueur.
3. Rien de blessant ou de dégradant sur un joueur (l'humour vise la situation, pas la personne).
4. On ne change pas la recette d'un coup : au plus 1 ou 2 améliorations par épisode, notées dans le carnet,
   pour savoir ce qui a marché.

## Fabriquer un épisode
1. Écrire `top10/episodes/<slug>.json` (voir le modèle ci-dessous).
2. Aperçu : lancer le workflow « Vidéo spéciale (10 trucs fous) » avec `episode = top10/episodes/<slug>.json`
   (sans date) → la vidéo arrive dans docs/proto/ ; vérifier les images (textes qui débordent, chevauchements).
3. Publication : relancer avec `queue_at = AAAA-MM-JJ 18:30` → aperçu Discord (❌ = annuler) et publication auto.

### Modèle de JSON
```json
{
  "file": "5_trucs_fous_curry",
  "nba_id": "curryst01",
  "photo": "curry.png",
  "title": ["5 TRUCS FOUS", "SUR CURRY"],
  "header": "5 TRUCS FOUS SUR CURRY",
  "cover": ["5 TRUCS", "FOUS SUR", "CURRY"],
  "hook": "[excited] Tu crois connaître Steph Curry ? Voici cinq trucs complètement fous sur lui.",
  "facts": [
    {"voice": "Numéro cinq. …", "visual": {"type": "big", "value": "1,88", "unit": " m", "label": "…", "sub": "…"}, "sources": ["https://…", "https://…"]},
    {"voice": "Numéro quatre. …", "visual": {"type": "bars", "value": "…", "label": "…", "bars": [["CURRY", "…", 1.0, "accent"], ["…", "…", 0.6, "silver"]], "note": "…"}, "sources": []},
    {"voice": "Numéro trois. …", "visual": {"type": "versus", "no": "…", "yes": "… ✓", "sub": "…"}, "sources": []},
    {"voice": "Numéro deux. …", "visual": {"type": "list", "value": "…", "label": "…", "items": ["…", "…", "…"]}, "sources": []},
    {"voice": "[excited] Et numéro un. …", "visual": {"type": "emoji", "emoji": "😂", "top": "…", "bottom": "…", "shout": "INCROYABLE !"}, "sources": []}
  ],
  "outro": "[excited] Lequel t'a le plus surpris ? Dis-le en commentaire… et dis-moi quel joueur tu veux dans le prochain épisode !",
  "caption": "5 trucs fous sur Curry 🤯 Le n°1 va te faire rire 😂\nLequel t'a le plus surpris ? Et quel joueur pour le prochain épisode ? 👇",
  "yt_title": "5 trucs fous sur Steph Curry 🤯",
  "hashtags": ["#NBA", "#StephenCurry", "#Curry", "#Warriors", "#basketball", "#NBAFrance", "#basket", "#lesaviezvous"],
  "sources": ["ESPN", "AP"]
}
```
Types de visuels : `big` (grand nombre animé), `bars` (comparaison en barres, `frac` entre 0 et 1),
`versus` (choix barré → choix retenu), `list` (titre + 3 cases), `emoji` (emoji + bandeaux). Option `shout`
(texte géant jaune qui claque vers 3,4 s). Textes courts, en MAJUSCULES, 30 caractères max par ligne.
`nba_id` : identifiant Basketball-Reference présent dans quiz/nba_ids.json, ou identifiant NBA direct.

## Carnet (un bloc par épisode, le plus récent en haut)
### Épisode 3 — LeBron (« 5 trucs fous sur LeBron ») — programmé le mer. 18 nov. 2026, 18:30
- Faits : salaire 52,6 M$ → 3,9 M$ aux Sixers (Fortune, CBS, IBTimes) ; 83 jours d'école manqués en CM1
  (The 74, FutureEd, GMA, ESPN) ; gaucher qui tire de la droite (Complex, GiveMeSport) ; jamais de 27-7-7 en saison
  régulière (AP, ESPN via Sportskeeda, LarryBrownSports) ; n°1 : gorgée du vin d'un fan en plein match contre
  Chicago le 2 nov., « c'était correct » (AP, 6abc, SI). Durée 38,4 s.
- Amélioration testée (1) : **accroche avec aperçu du n°1** (« …et le numéro un s'est passé ce mois-ci, en plein
  match ! ») : écart de curiosité dès les 3 premières secondes ; les études 2026 sur les hooks TikTok (opus.pro,
  34 k clips) montrent que l'algorithme juge en ~1,5 s et que les hooks « résultat/aperçu » font ~2× plus de vues.
  À comparer avec les épisodes Wemby (hook sans teasing).
- Code : dans le visuel `emoji`, l'emoji est réduit (×0,75) quand il y a un bandeau en haut ET en bas
  (le verre chevauchait le bandeau). Option `shout` à éviter avec `emoji` + `top` (chevauchement à y≈610).
- Code : vidéo de 20 Mo refusée par Discord (413, limite ~10 Mo) → `schedule` envoie désormais un aperçu allégé
  en 720p (~7 Mo) si l'envoi pleine qualité échoue ; la publication reste en pleine qualité.
- Stats Instagram (12 nov.) : aucun épisode « 5 trucs » encore publié (Wemby 1 décalé au 12 nov. 19:00).
  Repère : les vidéos Wemby du chiffre de la nuit font 39–51 likes, les autres 5–18, les quiz 4–11 →
  la notoriété du joueur pèse énormément. Insights (vues) non accessibles : permission #10 de l'appli.
- Pas d'alerte photos : 9 joueurs non traités avec photo restent.

### Épisodes 1 et 2 — Wemby (« 5 trucs fous », « 5 trucs que tu ignores ») — programmés les 11 et 14 nov. 2026
- Construits d'après l'analyse du 9 nov. : formats viraux sans visage = « 10 trucs bizarres sur X »
  (Why Guy, 180 k–1 M vues), anecdotes coulisses (@nbafacts_fr, 5–170 k), data animée (@justcodingvibes, jusqu'à 1,4 M).
- Version 10 faits (58 s) jugée trop longue par Mathieu → passage à 5 faits (35 s).
- Photo officielle fournie par Mathieu (wemby.png).
- Résultats : à relever.
