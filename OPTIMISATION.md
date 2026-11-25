# Labo d'optimisation — NBA Daily News

Demandé par Mathieu le 23 nov. 2026 : « améliorer le contenu en continu en fonction de ce qui se fait sur chaque réseau,
en automatisant complètement, quitte à changer le contenu, pour obtenir les meilleures stats possibles ».
Ce fichier est lu et mis à jour par la tâche programmée « Labo d'optimisation » (2 fois par semaine).

## Objectif
Maximiser, dans cet ordre : **vues** (TikTok, YouTube, Instagram, Facebook), **abonnés gagnés**, **commentaires/partages**,
puis ventes de la boutique (programmes Playground Lab liés aux exercices).

## Compte rendu
Un seul message Discord par passage, via le workflow « Message Discord » (`discord-msg.yml`, entrée `message`).

## Données disponibles
- `publish/perf_history.json` : vues de chaque vidéo à ~J+1, réseau par réseau (rempli chaque soir par le rapport de 21h),
  avec format, heure, accroche. C'est la source principale.
- `publish/stats_history.json` : abonnés par réseau et par jour.
- Workflow « Stats Instagram » (ig-stats.yml, ligne IGSTATS du journal) : likes et commentaires Instagram par vidéo
  (les vues Instagram ne sont pas accessibles : permission #10).
- Recherche web : tendances par réseau (TikTok, YouTube Shorts, Reels, Facebook), comptes basket sans visage FR/EN.

## Leviers autorisés (le labo peut les changer lui-même)
1. **Accroches, textes, durée, ordre, visuels, légendes, hashtags** de chaque format : directement dans le code
   (chiffre/pick.py, chiffre/main.py, top10/main.py, duel, drill) ou via les consignes des séries (top10/SERIE.md,
   duel/SERIE.md : section « Consignes du labo »).
2. **Heures de publication** (dans les crons des workflows et les créneaux des SERIE.md).
3. **Répartition entre formats** (ex. plus de duels, moins d'exercices) et **arrêt d'un format** qui sous-performe
   nettement depuis 2 semaines, ou **test d'un nouveau format** (prototype d'abord, puis 1 à 2 publications de test).
   Pour changer le rythme des séries « 5 trucs fous » et « Duel », mettre aussi à jour leur tâche programmée
   (prompt + jours) pour qu'elles restent cohérentes avec la file d'attente.
4. **Réglages par réseau** : légende propre à TikTok / Instagram / YouTube (titre, hashtags, longueur, question finale).

## Méthode (une expérience = une variable)
- Au plus **2 changements par passage** (et un seul par format), sinon on ne sait plus ce qui a marché.
- Chaque changement est noté dans le journal ci-dessous avec : hypothèse, ce qui change, mesure attendue, date du bilan.
- Bilan après ≥ 5 vidéos ou 7 jours : comparer à la médiane du même format sur les 2 semaines d'avant (même réseau).
  **Gagnant** (≥ +20 %) → on garde ; **perdant** (≤ −20 %) → on revient en arrière ; entre les deux → on garde le
  plus simple. Tenir compte des effets joueur (Wemby, LeBron… font toujours plus de vues).
- Toujours vérifier le rendu (aperçu vidéo + images extraites) avant qu'un changement de code parte en production.

## Garde-fous (jamais)
- Publier un fait ou un chiffre non vérifié (≥ 2 sources fiables), une rumeur, ou quelque chose de blessant.
- Utiliser une photo trouvée sur le web, une image de match, une musique protégée.
- Toucher aux secrets, aux comptes, aux jetons, aux réglages des réseaux, à la boutique (prix, produits).
- Casser une chaîne de publication : en cas de doute, ne rien changer et le signaler.
- Supprimer l'historique, le carnet des séries ou ce journal.
- Changer les messages Discord de publication décidés par Mathieu le 23 nov. (TikTok à l'heure de la vidéo :
  vidéo + miniature, puis la description seule ; 1 récapitulatif pour les autres réseaux).

## Décisions de Mathieu à respecter
- 23 nov. 2026 : quiz « qui est ce joueur » arrêté (le moins performant).
- 23 nov. 2026 : plus de « double dose » dans le chiffre de la nuit (accroche moins prenante). Réactivable (CHIFFRE_COMBO=1)
  seulement si une nouvelle accroche est testée et que les chiffres le justifient.
- 14 nov. 2026 : miniature v2 des « 5 trucs fous » validée (on peut l'améliorer, pas la dégrader).

## Journal du labo (le plus récent en haut)
### 25 nov. 2026 (mer.) — 1er passage
**Mesure.** Vues : seules celles de YouTube sont lisibles (Instagram #10, Facebook read_insights, TikTok non relevé) ;
`perf_history.json` n'a que 9 vidéos (22–24 nov.) → données trop maigres pour YouTube seul. Instagram (likes, ig-stats
du 25 nov. 20:45, 426 abonnés, +37 depuis le 15 nov.) sert donc de mesure principale.
- **YouTube (vues ~J+1)** : chiffre 967 (Wemby-Herro), 867 (Murray-Adebayo), **1** (McDaniels, 24 nov. : anomalie
  probable du compteur public ou vidéo bloquée → à surveiller) ; drill 646 / 140 / 588 ; quiz 785 ; « 5 trucs » Giannis
  248 ; duel Kobe-LeBron 231. → sur YouTube, les formats courts du quotidien font ~3× les séries.
- **Instagram, médiane des likes, 7 derniers jours (18–25 nov.) vs 2 semaines d'avant (4–17 nov.)** :
  chiffre 12 vs 15 (−20 %) ; « 5 trucs » 32,5 vs 29 (+12 %) ; duel 18 vs 41,5 (**−57 %**, commentaires 36 → 10 → 1 → 0 → 0) ;
  exercice 11 vs 7 (+57 %, retreat 39 et two-ball 22 en tête).
- Meilleures : Jordan-LeBron 59 likes / 36 com., Wemby 43 pts 51, « 5 trucs » Dončić 48, Wemby-Herro 44, Tatum 39 en 13 h.
  Pires : pull-up 2, Harden-Sengun 4, Flagg 4, quiz 2–4, Kobe-LeBron 11.
- **Effet joueur** (chiffre, likes) : superstar ≈ 15 (Dončić 34/18/10, Tatum 39, Giannis 12, Curry 15, SGA 10), Wemby 15–51,
  autres ≈ 6 même sur 50 pts (Cunningham 52 pts → 6, Harden 51 pts → 4). C'est le 1er facteur, loin devant l'accroche.
- Heure / accroche / durée : pas d'effet lisible (créneaux fixes par format, joueur qui écrase tout).
**Verdicts.** Aucune expérience du labo à trancher (1er passage). Chiffre en solo depuis le 24 nov. : trop tôt.
**Veille (25 nov.).** Virlo sports (6 oct.–16 nov. 2026, 14 933 vidéos) : accroches « tu » 27,6 % à 2× les vues, action
dès la 1re image 26,5 %, tutoriels 31,6 % (bon signe pour les exercices) ; commentaire d'actu : « affirmation choc » 28,3 %.
YouTube Shorts : priorité au contenu original (pas de reprise de clips), Shorts > ~30 jours peu poussés (théorie Joos, SEJ).
Reels (SocialPilot, sept. 2026) : 1re image décisive, partages en DM très pondérés, légendes à mots-clés > hashtags,
comptes « agrégateurs » pénalisés. Facebook Reels (NestScale, oct. 2026) : 15–30 s, 3–5 hashtags précis.
**Changements (2).**
1. *Chiffre de la nuit — priorité aux superstars* (chiffre/pick.py, `STARS` + `is_star`) : bonus +5 au score d'impact
   (comme les Français ; Wemby +8) pour ~22 stars grand public (LeBron, Curry, Dončić, Giannis, SGA, Jokić, Edwards, Durant,
   Tatum, Embiid, Flagg, Kyrie, Morant, Booker, J. Brown, Trae, Brunson, D. Mitchell, Harden, A. Davis, Leonard, Lillard),
   prénom vérifié (pas Seth Curry ni Bronny). Hypothèse : à perf proche, une star fait ~2,5× plus. Testé sur la nuit
   d'exemple (rendu OK). Mesure : médiane likes Instagram du chiffre (réf. 15) et vues YouTube J+1 (réf. ~900).
   **Bilan : mer. 2 déc.**
2. *Duel — accroche « affirmation choc » en « tu »* (duel/SERIE.md, « Consignes du labo ») à partir du duel préparé le
   jeu. 26 nov. (publié sam. 28). Hypothèse : la question « X ou Y ? » s'use ; une affirmation chiffrée + retournement
   retient mieux. Mesure : médiane likes Instagram (réf. 18 sur 7 j, 41,5 avant), commentaires, vues YouTube (réf. 231).
   **Bilan : dim. 6 déc.**
**Idées en attente.** Duels plus courts (YouTube) ou photos des deux joueurs (jordan.png, kobe.png… à demander à Mathieu) ;
exercices : plus de dribble « sous pression » (retreat, two-ball en tête) ; accès aux vues Instagram/Facebook/TikTok
(permissions des applis : à faire par Mathieu, le labo n'y touche pas) ; question de fin « réponds en 1 mot » pour les duels.

### 23 nov. 2026 — mise en place
- Historique durable des vues par vidéo créé (`publish/perf_history.json`, rempli chaque soir à partir du 24 nov.).
- Point de départ (likes Instagram, 9–21 nov.) : duels 18–58 likes et jusqu'à 36 commentaires ; « 5 trucs fous » 25–47 ;
  chiffre de la nuit Wemby 33–51, autres joueurs 1–18 ; exercices 6–25 ; quiz 0–12 (arrêté).
- Programme en vigueur : chiffre 8:00 tous les jours ; « 5 trucs fous » lun/mar/mer/ven/sam 12:30 ;
  exercice 18:00 tous les jours ; duels lun/mar/jeu/ven/sam 20:00.
