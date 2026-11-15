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
- **Publication** (décidé par Mathieu le 14 nov. 2026) : 3 duels par semaine, MARDI, JEUDI et SAMEDI à 20:00
  (préparés le dimanche, le mardi et le jeudi par une tâche programmée) (Instagram + YouTube auto, brouillon TikTok ~5 h avant,
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
- [ ] Magic Johnson vs Larry Bird
- [ ] Shaquille O'Neal vs Kareem Abdul-Jabbar
- [ ] LeBron James vs Kobe Bryant
- [ ] Stephen Curry vs Kobe Bryant
- [ ] Tim Duncan vs Shaquille O'Neal
- [ ] Victor Wembanyama vs Shaquille O'Neal (au même nombre de saisons : préciser « APRÈS 3 SAISONS »)
- [ ] Allen Iverson vs Stephen Curry
- [ ] Nikola Jokić vs Shaquille O'Neal
Si un duel fait l'actualité ou est réclamé en commentaire, il peut passer devant.

## Carnet (le plus récent en haut)
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
