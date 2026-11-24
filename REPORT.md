# Rapport — TP1 Smart Internship Match

## 1. Objectif et contexte

Construire un outil d'aide à la décision pour ma recherche de stage de fin d'études en génie industriel (avec un volet IA) : collecter de vraies offres, les structurer, les comparer à mes compétences, aider à agir (prioriser, rédiger une accroche), puis suivre les résultats. L'IA n'est utilisée que là où elle apporte quelque chose (structurer du texte libre, rédiger un brouillon) ; le suivi de mes candidatures reste un tableau que je contrôle (principe de l'humain dans la boucle, CM5).

## 2. Acquisition des données (CM3)

- **Source prévue** : API « Offres d'emploi v2 » de France Travail. Elle n'était pas disponible pour mon compte (absente de la liste des API proposées). Le prof a indiqué par mail d'utiliser une alternative (Adzuna ou Jooble).
- **Source utilisée** : API Adzuna (compte gratuit limité à **25 appels au total**). Un seul appel a suffi : 50 offres récupérées sur 700 correspondant à la recherche « stage industriel ».
- **Respect des règles** : pas de planification automatique (consigne du prof, quota limité) ; workflow GitHub Actions à lancement manuel uniquement ; mention « Jobs by Adzuna » affichée avec les offres (exigence des conditions d'utilisation d'Adzuna).
- **Limite de la source** : les descriptions sont tronquées à **500 caractères** ; la rémunération n'est connue que pour 6 offres sur 50.
- **Provenance et confidentialité** : mes clés API sont dans les Secrets GitHub ; mon profil de compétences (`my_skills.csv`) et les brouillons de lettre restent en local (hors dépôt public).

## 3. Structuration avec l'IA (CM5)

Un modèle local (Ollama, `qwen3:8b`) extrait pour chaque offre : compétences, missions, expérience demandée, rémunération citée. Il ne doit extraire que ce qui est écrit.

- Temps réel mesuré : environ **1 minute par offre** sur mon PC (le modèle ne tient qu'en partie sur la carte graphique), soit le double des valeurs du manuel.
- **Compromis vitesse/qualité mesuré** : désactiver le mode « réflexion » du modèle divise le temps par 5 (10 s au lieu de 54 s sur un test) mais l'IA a alors rangé des tâches dans la liste des compétences. J'ai gardé le mode d'origine pour la qualité.
- **Résultat** : seulement **8 offres sur 50 (16 %)** ont au moins une compétence extraite. Cause : texte tronqué à 500 caractères, et offres industrielles qui parlent de domaines (supply chain, méthodes, qualité) plutôt que d'outils.

## 4. Le KPI de matching (CM2)

Un KPI est un choix, pas un fait neutre. Mes choix pour `score_offer` :

1. **Comparaison des noms** : insensible à la casse et aux accents, par mots entiers, et en tenant compte des noms entre parenthèses de mes familles de compétences (« Kaizen » retrouve « Lean et amélioration continue (…, Kaizen, …) »).
2. **Couverture** = compétences demandées que j'ai ÷ compétences demandées. Si rien n'est extrait, la couverture vaut 0.
3. **Score** = somme des (niveau/5) des compétences trouvées ÷ compétences demandées : une compétence maîtrisée pèse plus qu'une débutante.
4. **Ajout après constat des données** : un 2e signal cherche mes compétences dans le titre et la description quand l'IA n'a rien extrait. Il ne peut qu'ajouter des matches (jamais de manques), car le texte ne révèle que ce que je possède déjà.

**Résultat** : 5 offres sur 50 ont un match (Thales « Ingénieur IA & SAP », Renault « contrôle qualité par IA », etc.), 4 ont un score ≥ 0,3. Les 45 autres sont à 0, le plus souvent faute d'information, pas faute de pertinence.

**Faux positif trouvé et corrigé** : mon expression « chef de projet » dans « Gestion de projet » faisait remonter en tête une offre où le texte dit « tu accompagneras le chef de projet » (ce n'est pas moi le chef de projet). Je l'ai retirée. Leçon : une recherche par mots-clés ne comprend pas le sens de la phrase.

## 5. Erreurs de l'IA repérées (esprit critique, CM5)

Sur les 3 brouillons d'accroche de lettre générés (contraints à n'utiliser que mes preuves) :

- **Exagérations de niveau** : « mon *expertise* en IA », « m'a permis de *maîtriser* » alors que mon niveau déclaré est 2/5 (Renault) ; « mon *expertise* en ERP et MES » (METAVONICS).
- **Informations inventées** : « algorithmes d'apprentissage automatique » et « traitement des données » approfondis à l'ENSIM (Renault) ; connaissances ERP/MES « approfondies lors de mon semestre d'échange » et « analyse de données » (METAVONICS) : rien de cela n'est dans mon profil.
- Le brouillon Thales était le plus fidèle.

Interprétation : même avec un prompt qui interdit d'inventer, le modèle transforme « j'ai utilisé » en « je maîtrise » et ajoute des détails plausibles. La relecture humaine est indispensable ; ces brouillons ne sont pas utilisables tels quels.

## 6. Tableau de bord (CM1/CM2) — choix de graphiques

Public : moi. Décisions : quelles offres ouvrir en premier, quelles compétences combler, et puis-je faire confiance au classement.

| Élément | Pour quelle décision | Pourquoi ce type |
|---|---|---|
| Cartes de chiffres (santé du pipeline) | Puis-je me fier au classement ? | Un chiffre unique se lit d'un coup d'œil ; on cherche une valeur, pas une tendance |
| Histogramme des scores | Combien d'offres sans info vs bons matchs | Montre la forme de la distribution, qu'un simple classement cache |
| Barres horizontales : compétences trouvées | Ce qui m'est le plus utile | Noms longs, comparaison de quantités |
| Barres horizontales : compétences manquantes | Pistes d'apprentissage | Idem ; à lire comme piste (peu de répétitions pour l'instant) |
| Tableau des offres prioritaires | Quelles offres ouvrir | On veut lire des titres et cliquer, pas comparer des surfaces |
| Cartes résultats (candidatures, réponses) | Ma recherche aboutit-elle ? | Chiffres simples, alimentés à la main |

Indicateur qui n'est pas « plus de candidatures, plus vite » : **la part d'offres exploitables** (qualité de l'information avant de décider). Je l'ai gardé parce qu'il m'évite de lire un score de 0 comme « offre sans rapport » alors qu'il signifie souvent « pas d'information ».

## 7. Monitoring (CM4)

Script `scripts/check_search_health.py`, qui répond à « quelque chose cloche-t-il dans ma recherche ? » avec quatre contrôles et des seuils justifiés :

- données de plus de 7 jours (le prof demande au maximum une actualisation par semaine) ;
- au moins une offre avec un score ≥ 0,30 ;
- au moins 30 % d'offres avec une information exploitable ;
- candidature sans réponse depuis plus de 10 jours.

Chaque lancement est ajouté à `docs/data/monitoring_log.json`.

- **Test** : sur une fausse candidature envoyée il y a 30 jours, le contrôle lève bien une alerte (test non enregistré dans le journal).
- **Lancement réel n°1 (24/11/2026)** : statut WARN. Il a détecté que seulement **20 %** des offres ont une information exploitable (seuil 30 %) : c'est exactement la limite des descriptions tronquées.
- **Lancement réel n°2** : prévu après la prochaine actualisation hebdomadaire des données ou après l'ajout de mes premières candidatures, pour que le contrôle ait quelque chose de nouveau à détecter ; il sera ajouté au journal `docs/data/monitoring_log.json`.

## 8. Limites et suite

- Descriptions tronquées → score peu discriminant ; une source avec texte complet améliorerait le KPI.
- Une seule requête de recherche et une seule source ; le quota gratuit (25 appels) interdit de multiplier les essais.
- Profil : mes compétences IA/données sont de niveau débutant (en cours d'apprentissage à l'ENSIM) ; à mettre à jour au fil du semestre avec de vraies preuves.
- Suivi de candidatures encore vide : les indicateurs de résultats (candidatures, taux de réponse) restent à 0 tant que je n'ai pas candidaté.
- L'énoncé `project1_internship_job_search.md`, cité par le manuel, n'est pas disponible sur UMTICE : ce rapport et le dashboard suivent le manuel du TP.
