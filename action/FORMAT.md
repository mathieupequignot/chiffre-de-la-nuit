# Format « L'ACTION QUI A TOUT CHANGÉ » — mode d'emploi et carnet

Lu (et mis à jour) à chaque épisode. Une action mythique de l'histoire de la NBA, racontée comme un thriller et
reconstituée sur un terrain 3D stylisé : pions aux couleurs des équipes, caméra qui bouge, voix « Mathieu NBA »,
gros titre en deux lignes, sous-titres mot à mot, nappe sonore maison. Validé par Mathieu le 27 nov. 2026
(« plus propre que les autres » → contenu principal).

## Rythme
**3 épisodes par semaine : DIMANCHE 12:30, MERCREDI 20:00 et JEUDI 12:30** (heure de Paris) — les créneaux libres de
la semaine (pas de « 5 trucs » le dimanche et le jeudi, pas de duel le mercredi). Décidé le 27 nov. 2026.
Préparés 2 jours avant par la tâche programmée : le vendredi (→ dim.), le lundi (→ mer.), le mardi (→ jeu.).
Créneau visé = le prochain dim./mer./jeu. à au moins 2 jours ; s'il a déjà une entrée `action_*` dans
publish/queue.json ce jour-là, prendre le créneau libre suivant (jamais deux épisodes le même jour), à l'heure de ce
jour (12:30 le dimanche et le jeudi, 20:00 le mercredi).
Exception : épisode 1 (Ray Allen) publié le ven. 27 nov. 2026 à 18:00 (exercice du jour décalé à 19:00).

## La recette (v2 — 27 nov. 2026)
- **40 à 50 s**, ~120 à 150 mots de voix, 10 à 13 scènes de 2 à 5 s (une relance toutes les 4–5 s).
- **Structure** : accroche (temps qui reste / situation désespérée, dès la 1re seconde) → contexte (date, enjeu,
  score) → montée (ce qui se passe, action par action) → relance « Et là… regarde bien X » (le joueur clé s'allume,
  les autres s'estompent) → le geste décisif au ralenti (bandes noires, battements de cœur) → l'explosion (flash,
  « DEDANS ! », foule) → « pas un hasard » / anecdote (replay vu de haut avec étapes numérotées) → conséquence
  (titre, record…) → **question de débat oui/non** (« Le plus grand tir de l'histoire des finales : oui ou non ? »).
- **Titre en deux lignes à chaque scène** : petite ligne blanche (contexte) + grande ligne colorée (3 mots max,
  ~22 caractères max). Jaune = suspense, rouge = danger/échec, vert = réussite, blanc = neutre.
- **Score + chrono** en haut ; n'afficher un chrono QUE s'il est vérifié par les sources (sinon `clock` absent).
- Mention « RECONSTITUTION SIMPLIFIÉE » pendant l'action (champ `chip`), « REPLAY · RECONSTITUTION » sur le replay.
- Miniature : 2 lignes (« LE TIR QUI A » / « TOUT CHANGÉ ») + bandeau rouge court (année + chiffre clé), image du
  geste décisif (champ `cover`).

## Règles absolues
1. **Chaque fait de la voix et des titres est vérifié par au moins 2 sources fiables** (NBA.com, ESPN, AP, SI,
   The Athletic, L'Équipe, Basketball-Reference, Andscape, theScore…), listées dans le JSON (`sources`). Dans le
   doute (deux sources qui se contredisent sur une seconde ou un score), on enlève le détail ou on reste général.
2. Les positions des joueurs sont une **reconstitution simplifiée** : fidèles au déroulé raconté (qui passe à qui,
   d'où part le tir), sans prétendre à la précision au pied près. Ne pas nommer un joueur dont le rôle n'est pas
   vérifié (les autres pions restent sans nom ni numéro).
3. Aucune image de match, aucune photo, aucun logo d'équipe ou de la NBA, aucune musique protégée (sons générés).
4. Rien de blessant envers un joueur ou une équipe (l'humour et la dramaturgie visent la situation).
5. Au plus 1 ou 2 améliorations par épisode, notées dans le carnet.

## Fabriquer un épisode
1. Écrire `action/episodes/<slug>.json` (schéma ci-dessous ; partir de `ray_allen_2013.json`).
2. Test local rapide (sans voix) : `python -m action.main --episode action/episodes/<slug>.json --out /tmp/x
   --frames "k:CUE:0.5,…"` → images + `cover.jpg` ; vérifier cadrages, pions visibles, ballon, titres.
3. Aperçu avec voix : workflow « Prototype « L'action qui a tout changé » » (action.yml) avec `episode=…` (sans
   queue_at) → docs/proto/<file>.mp4 + .jpg ; vérifier une quinzaine d'images ; puis `git rm -r docs/proto`.
4. Programmation : relancer action.yml avec `episode=…` et `queue_at=AAAA-MM-JJ HH:MM` (12:30 ou 20:00 selon le jour) → aperçu Discord (❌ = annuler)
   et mise en file (Instagram + YouTube + Facebook auto, brouillon TikTok sur Discord). Vérifier publish/queue.json.

## Schéma JSON
Repère du terrain (en pieds) : panier en (0, 5.25), cercle à 3,05 m (z = 10) ; ligne de fond y = 0 ; x de −25
(gauche) à +25 (droite) vu depuis le milieu de terrain ; milieu de terrain y = 47 ; ligne à 3 points : coins à
x = ±22 (jusqu'à y = 14), arc de rayon 23,75 ; raquette x ∈ [−8, 8], y ∈ [0, 19] ; lancer franc y = 19.
- `file` (clé de publication, commence par `action_`), `title`, `teams` {A, B : `code`, `color` [R,G,B], `num`
  (couleur des numéros), `shorts` optionnel}. A = équipe à gauche du score, couleur de la raquette par défaut.
- `floor_text` (inscription au sol, ex. « FINALE NBA 2013 »), `rope_scene` / `empty_scene` (optionnels : scène où
  les cordes jaunes apparaissent / où les tribunes se vident, et qui restent ensuite).
- `players` : {id : {`team`, `num`, `label` (étiquette jaune, seulement pour les joueurs nommés), `pos` [x, y]}}.
- `scenes` (dans l'ordre) : `cue`, `small`, `big`, `color`, `voice` (balises [excited], [surprised] avec parcimonie),
  `score` [A, B], `clock`, `cam` (nom de plan ou {"from": plan, "to": plan} ; plan = nom ou [[pos], [cible], focale]),
  `moves` {id : {`to` [x,y], `p` [début, fin] en fraction de scène, `from` optionnel}}, `jumps` {id : [p0, p1, hauteur]},
  `arms` {id : [p0, p1]} (bras levés), `celebrate` [ids], `ball` (liste d'opérations, voir ci-dessous), `labels`
  (true / false / [ids]), `focus` [ids] (les autres s'estompent), `glow` [ids], `chip`, `slowmo`, `cut`, `shake`,
  `flash`, `swish`, `confetti`, `rim_shake` [p0, p1], `paths` [{`pts`, `color`, `p`}], `steps` [[p, "1 · REBOND",
  [x,y,z]]], `sfx` [["clang", p] | ["heartbeat"] | ["swish", p] | ["roar", p] | ["chord", p]].
- Ballon : `{"do": "dribble"|"hold"|"pass"|"arc"|"shot"|"through"|"at", "p": [début, fin], …}` — `who`, `h`
  (hauteur de main), `from`/`to` (id de joueur, "rim" ou [x,y,z]), `apex`, `result` ("make"/"miss"), `at`.
- Plans de caméra prêts : wide, wide_close, wide_left, wide_right, high_left, high_right, top, top_left, top_right,
  paint, rim, wing_left, wing_right, corner_left, corner_right, side_left, side_right, top_key, celebrate.
- `cover` {`scene`, `p`, `lines` [2 lignes], `band`}, `caption`, `yt_title`, `hashtags`, `source_names`, `sources` (URLs).

## Programme des actions (une coche = épisode fait)
Critère : action ultra-connue, avec un vrai suspense et un geste lisible en reconstitution. Priorité au public FR.
- [x] Ray Allen, tir dans le coin, finale 2013 match 6 (Heat–Spurs) — ven. 27 nov. 2026
- [ ] Michael Jordan, « The Last Shot », finale 1998 match 6 (interception sur Malone puis tir sur Russell)
- [ ] LeBron James, le contre sur Iguodala, finale 2016 match 7
- [ ] Kyrie Irving, le 3 points sur Curry, finale 2016 match 7
- [ ] Kawhi Leonard, le tir au buzzer qui rebondit 4 fois, demi-finale de conférence 2019 match 7 (Sixers)
- [ ] Damian Lillard, le tir de loin au buzzer contre OKC, 1er tour 2019 match 5
- [ ] Vince Carter, le dunk par-dessus Frédéric Weis, JO de Sydney 2000 (France !)
- [ ] Derek Fisher, le tir à 0,4 seconde, demi-finale de conférence 2004 (Spurs)
- [ ] Reggie Miller, 8 points en 9 secondes au Madison Square Garden, 1995
- [ ] Michael Jordan, « The Shot » sur Craig Ehlo, 1989
- [ ] Robert Horry, le 3 points au buzzer contre Sacramento, finale de conférence 2002 match 4
- [ ] Tracy McGrady, 13 points en 33 secondes contre les Spurs, 2004
- [ ] Larry Bird, l'interception contre les Pistons, finale de conférence 1987 match 5
- [ ] Magic Johnson, le « junior sky hook », finale 1987 match 4
- [ ] Stephen Curry, le tir de très loin en prolongation à OKC, 2016
- [ ] Giannis Antetokounmpo, le contre sur Ayton, finale 2021 match 4
Quand il reste moins de 5 actions non cochées, en ajouter (moments très connus, toutes époques).

## Carnet (un bloc par épisode, le plus récent en haut)
### Épisode 1 — Ray Allen 2013 — publié le ven. 27 nov. 2026, 18:00
- Faits (NBA.com, Andscape, SI, theScore, Yahoo Sports) : Spurs +5 à 28,2 s ; cordes jaunes sorties, milliers de fans
  partis ; 3 pts de LeBron (−2) ; Leonard 1 lancer franc sur 2 (+3) ; LeBron rate, rebond offensif de Bosh ; Allen
  recule dans le coin droit, tire à 5,2 s ; 95-95, Miami gagne 103-100 en prolongation puis le match 7 ; Allen
  travaillait ce recul vers le coin à l'entraînement (NBA.com ; Yahoo « after practice » ; Bosh via theScore).
  Écartés : horaires 19,4 s / 20,1 s (sources en désaccord), Duncan sur le banc, « meilleur shooteur à 3 pts de
  l'histoire » à l'époque (non trouvé).
- Version 1 (45 s) → version 2 (43 s) après retour de Mathieu : pions avec bras/jambes, traînée du ballon, cercle qui
  tremble, replay en 4 étapes, nappe sonore (tic-tac + basse jusqu'au tir, silence au ralenti, accord final),
  miniature. Scènes calées sur les mots prononcés (horodatage ElevenLabs).
- Résultats : à relever (stats Instagram) au prochain épisode.
