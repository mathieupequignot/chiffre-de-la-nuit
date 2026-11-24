# Série « Duel » (X vs Y, stat par stat) — mode d'emploi et carnet

Lu et mis à jour à chaque épisode. Format validé par Mathieu le 14 nov. 2026 (« j'aime bien le format »).

## La recette (v1 — 14 nov. 2026)
- **2 joueurs, 8 manches**, une stat par manche, ~32–38 s. Score permanent en haut, 8 pastilles de progression.
- **Accroche** (1re seconde) : clash « X VS Y » + voix « X ou Y ? Huit stats, face à face… et le score final va faire débat ! ».
- **Manche** : nom de la stat → les 2 valeurs comptent → la voix annonce le gagnant (« Point X ! ») → case du gagnant
  colorée + 👑, perdant assombri, score qui saute. Le résultat reste affiché ~1 à 1,5 s.
- **Suspense** : ordonner les manches pour qu'aucun joueur ne mène de plus d'1 point.
- **Fin** : score final + verdict (« ÉGALITÉ PARFAITE ! » si 4-4) + « C'EST QUI LE GOAT ? 👇 » → pousse aux commentaires.
  Une égalité 4-4 est idéale pour les commentaires ; un 5-3 est acceptable si les stats ne permettent pas mieux.
- **Visuels** : couleurs d'équipe emblématiques (a = gauche, b = droite, couleurs bien contrastées, ex. rouge vs bleu).
  Photos : uniquement celles de top10/assets/ (fournies par Mathieu). Sans photo pour LES DEUX joueurs, on met
  les deux en silhouette (`nba_id` = identifiant NBA, photo officielle noircie) pour garder un rendu homogène.
- **Publication** (décidé par Mathieu le 23 nov. 2026, quiz supprimé ; avant : 3 par semaine mar/jeu/sam) : 5 duels par
  semaine, LUNDI, MARDI, JEUDI, VENDREDI et SAMEDI à 20:00 (préparés le samedi → lun, le dimanche → mar, le mardi → jeu,
  le mercredi → ven et le jeudi → sam, sur le prochain créneau libre à au moins 2 jours, par une tâche programmée)
  (Instagram + YouTube + Facebook auto ; brouillon TikTok à la même heure avec vidéo + miniature + description sur Discord ;
  aperçu Discord ❌ = annulation). Clé de file : `duel_<file>`.

## Règles absolues
1. Chaque valeur vient de **2 sources fiables** (Basketball-Reference + NBA.com / StatMuse / AP / ESPN). Sources dans le JSON.
2. Stats comparables : saison régulière (ou préciser « PLAYOFFS »), carrière entière. Pour un joueur en activité,
   prendre les totaux du jour (Basketball-Reference) et les arrondir dans la voix (« plus de quarante-trois mille »).
3. Rien de blessant pour un joueur ; le débat porte sur les stats.
4. Le choix des 8 stats est éditorial (on peut viser l'égalité), mais chaque chiffre affiché est exact.
5. Ne pas toucher au chiffre de la nuit, au quiz, ni à la série « 5 trucs fous » (top10/).

## Fabriquer un épisode
1. `duel/episodes/<slug>.json` (modèle : duel/episodes/jordan_lebron.json ; `"format": "duel"` obligatoire).
   Champs d'une manche : label, a, b (texte affiché, ex. "32 292", "30,1", "6/6"), unit (petite ligne), win ("a"/"b"),
   note (bandeau jaune optionnel), count (false si la valeur ne doit pas être animée), voice (nombres en toutes lettres).
2. Aperçu : workflow « Vidéo spéciale (10 trucs fous) » (top10.yml) avec `episode = duel/episodes/<slug>.json`
   → vidéo dans docs/proto/ ; vérifier images + miniature, puis `git rm -r docs/proto` et pousser
   (sinon la mise en file échoue).
3. Publication : relancer avec `queue_at = AAAA-MM-JJ 20:00`.

## Programme des duels (à cocher)
- [x] Michael Jordan vs LeBron James — programmé dim. 15 nov. 2026
- [x] Kobe Bryant vs Michael Jordan — programmé mar. 17 nov. 2026, 20:00
- [x] Magic Johnson vs Larry Bird — programmé jeu. 19 nov. 2026, 20:00
- [x] Shaquille O'Neal vs Kareem Abdul-Jabbar — programmé sam. 21 nov. 2026, 20:00
- [x] LeBron James vs Kobe Bryant — programmé mar. 24 nov. 2026, 20:00
- [x] Stephen Curry vs Kobe Bryant — programmé jeu. 26 nov. 2026, 20:00
- [ ] Tim Duncan vs Shaquille O'Neal
- [ ] Victor Wembanyama vs Shaquille O'Neal (au même nombre de saisons : préciser « APRÈS 3 SAISONS »)
- [ ] Allen Iverson vs Stephen Curry
- [ ] Nikola Jokić vs Shaquille O'Neal
Si un duel fait l'actualité ou est réclamé en commentaire, il peut passer devant.

## Carnet (le plus récent en haut)
### Duel 6 — Curry vs Kobe — programmé le jeu. 26 nov. 2026, 20:00
- Préparé automatiquement le mar. 24 nov. (1er duel non coché ; aucun duel du programme n'a de photo pour les deux joueurs,
  curry.png existe mais pas kobe.png → 2 silhouettes, nba_id 201939 et 977, rendu OK).
- Curry = a (bleu Warriors 0,107,182), Kobe = b (violet Lakers 100,45,155) : bleu/violet assez contrastés à l'écran, score final lisible.
- Manches : points carrière « 26 800+ » vs 33 643 (K), paniers à 3 pts « 4 290+ » vs 1 827 (C), titres 4 vs 5 (K), MVP 2 vs 1 (C),
  record en un match 62 vs 81 (K), lancers francs 91,3 % vs 83,7 % (C, `count: false`), MVP des Finales 1 vs 2 (K),
  3 pts en un match 13 vs 12 (C : 7 nov. 2016 vs Pelicans, record NBA battu ; Kobe 12 le 7 janv. 2003 vs Seattle) → 4-4.
  Écartés : All-Star (12 vs 18), titres de meilleur marqueur (2-2), points/match (24,8 vs 25,0 : trop serré pour un joueur en activité).
- Sources : StatMuse + Basketball-Reference + Land of Basketball + NBA.com (Curry), Statscrew + Land of Basketball + Star Tribune (Kobe),
  StatMuse + ESPN (records en un match), SI + StatMuse (62 pts). Titre 2026 : Knicks (Brunson MVP des Finales) → Curry reste à 4 titres.
- Appris : Curry blessé (abdomen) depuis le 12 nov., ~1 mois → totaux figés, mais planchers « + » gardés par prudence.
  Vidéo de 33,0 s avec des voix courtes : bonne durée. Une dernière manche « record en un match » très serrée (13 vs 12) marche bien
  pour finir en égalité. Note de 34 caractères (« CURRY A BATTU LE RECORD NBA DE KOBE ») tient sur une ligne.
  WebFetch statmuse parfois refusé (permission) ; statscrew.com donne des totaux carrière complets et lisibles.
- Résultats : à relever.
### Duel 5 — Kobe vs LeBron — programmé le mar. 24 nov. 2026, 20:00
- Préparé automatiquement le dim. 22 nov. (1er duel non coché ; aucun duel du programme n'a de photo pour les deux joueurs,
  pas de kobe.png → 2 silhouettes, nba_id 977 et 2544, rendu OK).
- Kobe = a (violet Lakers éclairci 100,45,155 : score final mieux lisible qu'en 85,37,130), LeBron = b (rouge 76ers 237,23,76 :
  LeBron joue à Philadelphie en 2026-27 selon Basketball-Reference et Land of Basketball → éviter #Lakers pour lui).
- Manches : points carrière 33 643 vs « 43 600+ » (L, `count: false`), titres 5 vs 4 (K), MVP 1 vs 4 (L), record en un match 81 vs 61 (K),
  MVP des Finales 2 vs 4 (L), All-Defensive 12 vs 6 (K), All-Star 18 vs 22 (L), meilleur marqueur 2 vs 1 (K) → 4-4.
  Écartés : All-Star MVP (4-3 K), All-NBA (15-21 L), passes, rebonds.
- Sources : Land of Basketball + Basketball-Reference + NBA PR (2016) + StatMuse + Wikiwand + Fox (61 pts).
- Appris : le total de points d'un joueur en activité bouge chaque soir et les sources ne sont pas synchrones (BBR 43 628 après 12 matchs,
  LoB 43 649 après 13) → afficher un plancher vérifié (« 43 600+ ») plutôt qu'un chiffre exact qui sera faux le jour J.
  Ici WebFetch sur ESPN / aws.basketball-reference refusé (permission) : Land of Basketball (profil) + StatMuse restent lisibles.
  Libellé « ALL-DEFENSIVE » + unit « SÉLECTIONS » tient bien ; « FOIS N°1 EN NBA » réutilisable pour tout titre statistique.
  Vidéo de 39,4 s (limite haute) : 1re voix de manche trop longue, à raccourcir la prochaine fois.
- Résultats : à relever.

### Duel 4 — Shaq vs Kareem — programmé le sam. 21 nov. 2026, 20:00
- Préparé automatiquement le jeu. 19 nov. (1er duel non coché ; aucun duel du programme n'a de photo pour les deux joueurs,
  ni Shaq ni Kareem n'en a → 2 silhouettes, nba_id 406 et 76003, rendu OK).
- Shaq = a (violet Lakers 85,37,130), Kareem = b (vert Bucks 0,128,72 : son titre, ses 3 premiers MVP et son record de 55 pts à Milwaukee).
  Or (jaune) évité : texte blanc illisible sur les cases gagnantes.
- Manches : points carrière 28 596 vs 38 387 (K), adresse au tir 58,2 % vs 55,9 % (S, `count: false`), titres 4 vs 6 (K),
  MVP des Finales 3 vs 2 (S), MVP 1 vs 6 (K), record en un match 61 vs 55 (S : 6 mars 2000 vs Clippers / 10 déc. 1971 vs Celtics),
  All-Star 15 vs 19 (K), meilleur % aux tirs de la NBA 10 fois vs 1 (S, record) → 4-4. Rebonds, contres (K) et titres de meilleur marqueur (2-2) écartés.
- Sources : StatMuse + ESPN + Land of Basketball + NBA.com (stats, palmarès), Basketball-Reference + Wikipedia + Guinness (% aux tirs), CBS + Statitudes (records en un match).
  Note : WebFetch direct sur basketball-reference.com bloqué (permission) → miroir aws.basketball-reference.com utilisable.
- Appris : vidéo de 36,7 s. Une `unit` de plus de ~20 caractères devient minuscule (« SAISONS AU MEILLEUR % DE LA NBA ») → viser ≤ 18.
  La `unit` est commune aux deux cases : éviter un pluriel faux (« 1 SAISONS ») → « FOIS N°1 EN NBA ».
  Le score final du joueur a en violet (max(couleur) > 120) reste un peu sombre sur fond noir ; lisible mais à surveiller.
- Résultats : à relever.

### Duel 3 — Magic vs Bird — programmé le jeu. 19 nov. 2026, 20:00
- Préparé automatiquement le mar. 17 nov. (1er duel non coché ; aucun duel du programme n'a de photo pour les deux joueurs,
  ni Magic ni Bird n'en a → 2 silhouettes, nba_id 77142 et 1449, rendu OK).
- Magic = a (violet Lakers 85,37,130), Bird = b (vert Celtics 0,122,51) : bon contraste.
- Manches : points carrière 17 707 vs 21 791 (B), passes 10 141 vs 5 695 (M), titres 5 vs 3 (M), points/match 19,5 vs 24,3 (B),
  MVP des Finales 3 vs 2 (M), rebonds 6 559 vs 8 974 (B), lancers francs 84,8 % vs 88,6 % (B, `count: false`),
  Finales face à face 2 vs 1 (M : 1984 Celtics, 1985 et 1987 Lakers) → 4-4. MVP (3-3) et All-Star (12-12) écartés : égalités.
- Sources : Basketball-Reference + StatMuse + Land of Basketball (stats), NESN + Heavy + NBA.com (titres, Finales).
- Appris : vidéo de 34,5 s avec des voix de manche courtes (≤ ~12 mots) → bonne durée, à garder.
  « LE DUEL MYTHIQUE » (16 car.) touchait déjà la chèvre de la miniature → raccourci en « DUEL MYTHIQUE » ; viser ≤ 14 caractères.
  Une manche « face à face » (Finales entre eux) fait une très bonne dernière manche pour une vraie rivalité.
- Résultats : à relever.

### Duel 2 — Kobe vs Jordan — programmé le mar. 17 nov. 2026, 20:00
- Préparé automatiquement le dim. 15 nov. (1er duel non coché du programme ; aucun des deux n'a de photo → 2 silhouettes).
- Kobe = a (violet Lakers 85,37,130), Jordan = b (rouge Bulls) : contraste correct à l'écran.
- Manches : points carrière 33 643 vs 32 292 (K), points/match 25,0 vs 30,1 (J), titres 5 vs 6 (J), record en un match
  81 vs 69 (K), MVP 1 vs 5 (J), paniers à 3 pts 1 827 vs 581 (K), MVP des Finales 2 vs 6 (J), All-Star 18 vs 14 (K) → 4-4.
  Volontairement d'autres stats que Jordan-LeBron (record en un match, 3 pts, MVP des Finales) pour varier.
- Appris : le bandeau de miniature (`cover_tag`) déborde sous la chèvre 🐐 au-delà de ~17 caractères
  (« QUI EST LE MEILLEUR ? » coupait le « ? ») → garder « QUI EST LE GOAT ? » ou plus court.
- Éviter la note « 2e plus gros match de l'histoire » pour les 81 pts de Kobe sans revérifier le classement du jour.
- Vidéo de 38,9 s (un peu longue : voix des manches à raccourcir si besoin). Résultats : à relever.

### Duel 1 — Jordan vs LeBron — programmé le dim. 15 nov. 2026, 18:30
- Inspiré d'une vidéo TikTok envoyée par Mathieu (format « duel stat par stat »).
- Manches : points carrière (L), points/match (J), titres (J), passes (L), MVP (J), rebonds (L), Finales 6/6 vs 4/10 (J),
  All-Star 14 vs 22 (L) → 4-4. MVP des Finales volontairement absents (6-4 Jordan) : de quoi faire réagir en commentaire.
- Les deux joueurs en silhouette (pas de photo de Jordan fournie). Une photo `jordan.png` permettrait de passer aux visages.
- Résultats : à relever.
