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
- **Publication** : voir « Rythme » ci-dessous (5 par semaine, lun/mar/mer/ven/sam 12:30) (Instagram + YouTube + Facebook auto ; brouillon TikTok
  à la même heure, avec sur Discord : vidéo + miniature, puis la description seule, puis 1 récapitulatif des autres réseaux), en plus du chiffre de la nuit, des duels et de l'exercice.

## Miniature (v2, 10/11)
Fond aux couleurs de l'équipe (table TEAM dans top10/main.py, ou champ JSON `color`), rayons, joueur détouré avec contour blanc
+ ombre, badge rond « 5 », nom géant jaune incliné, bandeau rouge (champ JSON optionnel `cover_tag`, défaut « LE N°1 VA TE CHOQUER »).
Nouveau joueur hors table : ajouter sa couleur dans TEAM.

## Programme des joueurs (photos fournies par Mathieu dans top10/assets/)
Rythme (décidé par Mathieu le 23 nov. 2026, quiz supprimé) : 5 épisodes par semaine, LUNDI, MARDI, MERCREDI, VENDREDI et
SAMEDI à 12:30. Préparés le samedi (→ lun), le dimanche (→ mar), le lundi (→ mer), le mercredi (→ ven) et le jeudi (→ sam),
toujours sur le prochain créneau libre à au moins 2 jours. (Avant : 3 par semaine lun/mer/ven, décidé le 14 nov.) Ordre de passage par défaut : Si un joueur est très réclamé en commentaire ou fait l'actualité
de la semaine, on peut le faire passer devant. Joueur traité = on le coche [x].
- [x] Victor Wembanyama — wemby.png (épisodes 1 et 2)
- [x] LeBron James — lebron.png (épisode du 18 nov. 2026)
- [x] Stephen Curry — curry.png (épisode du lun. 16 nov. 2026)
- [x] Luka Dončić — doncic.png (épisode du ven. 20 nov. 2026)
- [x] Giannis Antetokounmpo — giannis.png (épisode du lun. 23 nov. 2026 ; joue au Heat depuis l'été 2026 → `color` Heat dans le JSON)
- [x] Shai Gilgeous-Alexander — sga.png (épisode du mer. 25 nov. 2026)
- [ ] Anthony Edwards — edwards.png
- [ ] Nikola Jokić — jokic.png
- [ ] Kevin Durant — durant.png
- [ ] Cooper Flagg — flagg.png
- [ ] Kyrie Irving — kyrie.png
- [ ] Joel Embiid — embiid.png (ajouté le 14/11 : photo arrivée le 12/11)
- [ ] Jayson Tatum — tatum.png (ajouté le 14/11)
- [ ] Rudy Gobert — gobert.png (ajouté le 14/11, Français)
- [ ] Ja Morant — morant.png (ajouté le 14/11)
- [ ] Devin Booker — booker.png (ajouté le 14/11)
- [ ] Jaylen Brown — brown.png (ajouté le 14/11)
- [ ] Trae Young — trae.png (ajouté le 14/11)
- [ ] Jalen Brunson — brunson.png (ajouté le 14/11)
- [ ] Donovan Mitchell — mitchell.png (ajouté le 14/11)
(Photos aussi présentes mais jugées pas assez « grand public » pour la série : banchero, coulibaly, cunningham, maxey,
reaves, risacher, sarr, towns — à utiliser seulement s'ils font l'actualité.)
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
3. Publication : relancer avec `queue_at = AAAA-MM-JJ 12:30` → aperçu Discord (❌ = annuler) et publication auto.

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
Option `end` : ["LIGNE 1", "LIGNE 2"] remplace la question de l'écran de fin (défaut « LEQUEL T'A LE PLUS / SURPRIS ? »).
Avec 3 barres dans `bars`, ne pas mettre de `note` (elle tombe sur les sous-titres).
Types de visuels : `big` (grand nombre animé), `bars` (comparaison en barres, `frac` entre 0 et 1),
`versus` (choix barré → choix retenu), `list` (titre + 3 cases), `emoji` (emoji + bandeaux). Option `shout`
(texte géant jaune qui claque vers 3,4 s). Textes courts, en MAJUSCULES, 30 caractères max par ligne.
`nba_id` : identifiant Basketball-Reference présent dans quiz/nba_ids.json, ou identifiant NBA direct.

## Carnet (un bloc par épisode, le plus récent en haut)
### Épisode 7 — SGA (« 5 trucs fous sur SGA ») — programmé le mer. 25 nov. 2026, 12:30
- Équipe vérifiée : Thunder (CBS Sports nov. 2026 ; AP 22/10/2026). Couleur `sga` déjà dans TEAM.
- Faits : mère sur 400 m aux JO de Barcelone 1992 pour Antigua-et-Barbuda (Olympics.com, Wikipedia, Heavy) ; recalé de
  l'équipe JV de St. Thomas More en 1re année de lycée (News On 6/KOTV, On3) ; MVP + meilleur marqueur + MVP des Finales
  en 2025, comme Jordan, Shaq, Kareem (CBS, SI) ; 141 matchs de suite à 20 pts+, record de Chamberlain (126) battu,
  série arrêtée le 22/10/2026 (AP/AJC, NBC Sports, Fox/AP) ; n°1 : son père garde le trophée de MVP de la finale de
  conférence Ouest 2025, « You acting like it's yours! » (SI, AOL, Yardbarker). Écarté : Ares qui fait presque tomber le
  trophée de MVP des Finales (une seule source solide). Durée **40,0 s** (1er rendu 40,8 s : hook et 3 faits raccourcis ;
  ~150 mots de voix = limite, viser 140).
- Améliorations testées (2) : (1) **accroche « avertissement »** (« Attention : tu ne verras plus jamais SGA pareil »)
  + aperçu du n°1 (« c'est la faute de son père ») : étude Virlo sur 1 977 listicles sport (oct.–nov. 2026), les hooks
  avertissement / affirmation forte font le plus souvent 2× les vues habituelles du compte. (2) **hashtags mixtes**
  (11 : niche + génériques #pourtoi #fyp) : OpusClip (13,5 M de TikToks 2026) voit des vues médianes ~2,5× plus hautes
  avec un mélange niche + générique qu'avec des hashtags de niche seuls (corrélation). Question de fin oui/non conservée.
- Stats Instagram (21 nov. 13:15, 408 abonnés) : **Dončić = 46 likes / 3 commentaires** en ~1 j → premiers commentaires
  de la série : la question oui/non fonctionne, on la garde. Curry 47 / 0, LeBron 26 / 0, Wemby 2 = 29 / 0,
  Wemby 1 = 25 / 0. Duels : Jordan-LeBron 58 / 36, Kobe-Jordan 24 / 10, Magic-Bird 18 / 1. Chiffre de la nuit Wemby 33,
  autres 1–15 ; quiz 0–8. → les « 5 trucs » restent la 2e série en likes, derrière les duels pour les commentaires.
- Pas d'alerte photos : 14 joueurs non traités avec photo.

### Épisode 6 — Giannis (« 5 trucs fous sur Giannis ») — programmé le lun. 23 nov. 2026, 12:30
- Équipe vérifiée : Miami Heat (échangé cet été contre Herro, Ware, Jaquez, Jakucionis + 3 premiers tours ; AP 18/11,
  Yahoo, NBA.com Heat). Il retrouve les Bucks le 18/11 → joueur d'actualité. `color` Heat [152,0,46] dans le JSON
  (la table TEAM garde le vert Bucks, non modifiée). La photo fournie le montre en maillot Bucks : OK, mais une photo
  au Heat serait mieux.
- Faits : vendait des lunettes de soleil dans les rues d'Athènes avec Thanasis (Olympics.com, NBC Sports) ; MVP + DPOY
  la même saison 2019-20, seuls Jordan et Olajuwon avant (AP via Fox 6, Audacy) ; 50 pts au match 6 de la finale 2021,
  1er titre des Bucks en 50 ans (AP/Bangor Daily News, Sky Sports) ; Giannis, Thanasis, Kostas = 1er trio de frères
  champions NBA (CBS News, Eurohoops) ; n°1 : rookie, il envoie son argent à sa famille, plafond de retrait atteint,
  court vers la salle en plein hiver, un couple le reconnaît et le dépose (SI ×2, Complex, NBC Sports).
- Améliorations testées (2) : (1) **accroche d'actualité** (« Giannis, le patron du Heat ? ») : les guides sport 2026
  (fluxnote) conseillent d'ouvrir sur le contexte le plus fort ; l'actu (transfert + retour à Milwaukee) donne une
  raison de regarder maintenant. (2) **vidéo plus courte** : ~140 mots de voix → **34,5 s** (Dončić 37 s, LeBron 40 s) ;
  les mêmes guides donnent < 30 s comme meilleur taux de complétion pour le sport. Question de fin oui/non conservée
  (« Giannis au Heat : oui ou non ? ») pour confirmer l'effet testé sur Dončić.
- Rendu : l'emoji 🕶️ s'affichait en petit pictogramme noir presque invisible (variante texte) → remplacé par 😎.
  À éviter : emojis avec sélecteur de variante (FE0F). Titre de l'accroche qui frôle le haut de la tête : acceptable.
- 1er passage de programmation en échec (installation ffmpeg/apt > 8 min côté GitHub) → relancé, OK.
- Stats Instagram (18 nov. 13:20, 396 abonnés) : Curry = **47 likes** / 0 com. (2 j, record de la série) ; LeBron =
  8 / 0 en ~2 h ; Wemby 2 = 29 / 0 ; Wemby 1 = 25 / 0. Duels : Jordan-LeBron 56 / **33 com.**, Kobe-Jordan 20 / 8 en
  ~17 h. Chiffre Giannis 35 / 2. → les « 5 trucs » sont la série qui fait le plus de likes après les duels, mais
  toujours 0 commentaire : la question débat (Dončić, puis Giannis) reste LA piste à mesurer.
- Pas d'alerte photos : 15 joueurs non traités avec photo.

### Épisode 5 — Dončić (« 5 trucs fous sur Luka ») — programmé le ven. 20 nov. 2026, 12:30
- Faits : pro au Real Madrid à 16 ans, plus jeune de l'histoire du club (Eurohoops, Bleacher Report) ; MVP de l'Euroligue
  à 19 ans, record (CBS, STA, Arizona Sports) ; 73 points à Atlanta en 2024, seuls Chamberlain et Kobe au-dessus (Yahoo,
  Fox 4, TSN) ; lancer franc raté exprès → égalisation, 60-21-10 inédit (CBS/AP, SI, ESPN) ; n°1 : faux enterrement avec
  cercueil par des fans de Dallas après l'échange aux Lakers, 2 fév. 2025 (Fox News, SI, Complex). Équipe actuelle
  vérifiée : Lakers (43 pts contre Phoenix la nuit du 15/11, en pleine série de 40 pts → joueur d'actualité).
  Durée 37,0 s (1er rendu 40,2 s : 2 phrases raccourcies).
- Amélioration testée (1) : **question de fin fermée et clivante** (« Luka top 3 de la NBA : oui ou non ? ») au lieu de
  « Lequel t'a le plus surpris ? », à l'écran (nouvelle option JSON `end`), à la voix et dans la légende. Pourquoi : les
  « 5 trucs » ont 0 commentaire, alors que le Duel Jordan/LeBron (« C'est qui le GOAT pour toi ? ») en a 20 ; les guides
  2026 (socialk.it) : un avis tranché à donner en un mot = le commentaire le plus facile. Relance au milieu et aperçu du
  n°1 dans l'accroche conservés.
- Code : `end` dans top10/main.py (défaut inchangé, Duel non concerné). Avec 3 barres, la `note` chevauchait les
  sous-titres → enlevée sur cet épisode.
- Stats Instagram (16 nov. 13:20, 393 abonnés) : Curry = 8 likes / 0 com. en ~1,5 h ; Wemby 2 = 29 likes / 0 com. ;
  Duel Jordan-LeBron = 46 likes / **20 com.** ; chiffre Dončić 33 / 1, chiffre Giannis 35 / 2, drill Mikan 22 / 0,
  quiz 2–4. → les « 5 trucs » sont au niveau des bons chiffres en likes mais toujours à 0 commentaire : le débat
  binaire est la piste n°1. À relever : effet de la question oui/non sur cet épisode.
- Pas d'alerte photos : 16 joueurs non traités avec photo.

### Épisode 4 — Curry (« 5 trucs fous sur Curry ») — programmé le lun. 16 nov. 2026, 12:30
- Faits : né dans le même hôpital que LeBron à Akron (NBA.com Warriors, NBC Sports, Bleacher Report) ; 402 trois-points
  en 2015-16, ancien record 286… le sien (ESPN, AP/ABC, Guinness) ; rencontre Ayesha à 15 ans à l'église, elle le trouve
  « pas pour elle » (ET, The Knot) ; 1er joueur à 4 000 trois-points, mars 2025 (ESPN, CBS, AP/ABC) ; n°1 : la réunion
  ratée de Nike en 2013 (« Steph-on » + diapo au nom de Kevin Durant) → Under Armour (NBC Sports/Dell Curry, Fox, Complex).
  Écarté : « seule Davidson lui a offert une bourse » (Virginia Tech/Greenberg contestent → doute = on enlève).
  Durée 38,1 s (151 mots de voix, outro raccourcie).
- Amélioration testée (1) : **relance au milieu** (« Et reste jusqu'au bout pour le un ! » au début du n°3, ~14 s) :
  les guides rétention 2026 (socialk.it, joyspace) conseillent un « re-hook » vers 30–40 % de la vidéo, là où
  l'attention chute. Hook gardé avec aperçu du n°1 (« c'est une gaffe énorme »), comme LeBron.
- Stats Instagram (14 nov., 391 abonnés) : Wemby 1 = 25 likes / 0 com. (2 j) ; Wemby 2 = 28 likes / 0 com. en ~4 h
  → au niveau des meilleurs chiffres de la nuit Wemby (15–51) et 3–5× les autres vidéos (chiffre hors Wemby 5–18,
  quiz 2–12, drills 5–10). Point faible : **0 commentaire** malgré l'appel en fin de vidéo (les quiz en ont 1–2) →
  piste pour un prochain épisode : une question fermée et facile (« Tu en connaissais combien sur 5 ? »).
  Insights (vues) toujours inaccessibles (#10).
- Programme : 9 joueurs ajoutés (photos arrivées le 12/11). Pas d'alerte photos : 17 joueurs non traités avec photo.

### Épisode 3 — LeBron (« 5 trucs fous sur LeBron ») — programmé le mer. 18 nov. 2026, 18:30
- Faits : salaire 52,6 M$ → 3,9 M$ aux Sixers (Fortune, CBS, IBTimes) ; 83 jours d'école manqués en CM1
  (The 74, FutureEd, GMA, ESPN) ; gaucher qui tire de la droite (Complex, GiveMeSport) ; jamais de 27-7-7 en saison
  régulière (AP, ESPN via Sportskeeda, LarryBrownSports) ; n°1 : gorgée du vin d'un fan en plein match contre
  Chicago le 2 nov., « c'était correct » (AP, 6abc, SI). Durée finale 40,2 s (limite haute : viser ~150 mots de voix).
- Amélioration testée (1) : **accroche avec aperçu du n°1** (« …et le numéro un s'est passé ce mois-ci, en plein
  match ! ») : écart de curiosité dès les 3 premières secondes ; les études 2026 sur les hooks TikTok (opus.pro,
  34 k clips) montrent que l'algorithme juge en ~1,5 s et que les hooks « résultat/aperçu » font ~2× plus de vues.
  À comparer avec les épisodes Wemby (hook sans teasing).
- Code : dans le visuel `emoji`, l'emoji est réduit (×0,75) quand il y a un bandeau en haut ET en bas
  (le verre chevauchait le bandeau). Option `shout` à éviter avec `emoji` + `top` (chevauchement à y≈610).
- Code : vidéo de 20 Mo refusée par Discord (413, limite ~10 Mo) → `schedule` envoie désormais un aperçu allégé
  en 720p (~7 Mo) si l'envoi pleine qualité échoue ; la publication reste en pleine qualité.
- docs/proto supprimé : ses fichiers suivis (aperçus d'autres séries) faisaient échouer le commit de mise en file
  (`rm -rf docs/proto` + `pull --rebase`). Un 1er message Discord LeBron (sans file) est orphelin : seul le 2e compte.
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
