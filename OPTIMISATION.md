# Labo d'optimisation — NBA Daily News

Demandé par Mathieu le 23 nov. 2026 : « améliorer le contenu en continu en fonction de ce qui se fait sur chaque réseau,
en automatisant complètement, quitte à changer le contenu, pour obtenir les meilleures stats possibles ».
Ce fichier est lu et mis à jour par la tâche programmée « Labo d'optimisation » (2 fois par semaine).

## Objectif
Maximiser, dans cet ordre : **vues** (TikTok, YouTube, Instagram, Facebook), **abonnés gagnés**, **commentaires/partages**,
puis ventes de la boutique (programmes Playground Lab liés aux exercices).

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
### 23 nov. 2026 — mise en place
- Historique durable des vues par vidéo créé (`publish/perf_history.json`, rempli chaque soir à partir du 24 nov.).
- Point de départ (likes Instagram, 9–21 nov.) : duels 18–58 likes et jusqu'à 36 commentaires ; « 5 trucs fous » 25–47 ;
  chiffre de la nuit Wemby 33–51, autres joueurs 1–18 ; exercices 6–25 ; quiz 0–12 (arrêté).
- Programme en vigueur : chiffre 8:00 tous les jours ; « 5 trucs fous » lun/mar/mer/ven/sam 12:30 ;
  exercice 18:00 tous les jours ; duels lun/mar/jeu/ven/sam 20:00.
