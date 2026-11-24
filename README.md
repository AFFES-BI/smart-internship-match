# smart-internship-match

## Tableau de bord

[Ouvrir le tableau de bord](https://affes-bi.github.io/smart-internship-match/dashboard.html)

Ce tableau de bord aide à décider quelles offres de stage regarder en priorité et quelles
compétences combler. Il affiche trois familles d'indicateurs : la santé du pipeline (offres
analysées, part d'offres où l'IA a extrait des compétences), l'efficacité de la recherche
(répartition des scores de matching, compétences trouvées et manquantes, offres à ouvrir en
premier) et les résultats de mes candidatures (saisis à la main). Les offres viennent de
l'API Adzuna (50 offres récupérées en un seul appel, quota gratuit limité), structurées par
un modèle local (Ollama) puis comparées à mon profil par `scripts/match_offers.py`. Les
descriptions Adzuna sont tronquées à 500 caractères, ce qui limite le score (voir le rapport).

Offres : [Jobs by Adzuna](https://www.adzuna.fr) (The Adzuna API).

## Rapport

[Consulter mon rapport](REPORT.md)
