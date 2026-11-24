import json, os, sys, time
import requests

# Source des offres : API Adzuna (remplace France Travail, indisponible -- cf. mail du prof).
# Compte gratuit limite a 25 appels de test AU TOTAL : ce script fait donc UN SEUL appel
# par execution (1 page de 50 offres) et sauvegarde la reponse brute, pour ne jamais
# avoir a refaire la meme requete. A lancer a la main uniquement, jamais en planification.

APP_ID = os.environ["ADZUNA_APP_ID"]
APP_KEY = os.environ["ADZUNA_APP_KEY"]

COUNTRY = "fr"
SEARCH_URL = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"

# A adapter a ton profil (genie industriel + un peu d'IA).
# "what" : tous ces mots doivent apparaitre dans l'offre.
SEARCH_PARAMS = {
    "what": "stage industriel",
    "results_per_page": 50,
    "sort_by": "date",
    "content-type": "application/json",
}

def search_offers():
    params = {**SEARCH_PARAMS, "app_id": APP_ID, "app_key": APP_KEY}
    resp = requests.get(SEARCH_URL, params=params, timeout=(10, 30))
    print(f"HTTP {resp.status_code}")
    if resp.status_code != 200:
        # Pas de nouvelle tentative automatique : chaque appel compte sur 25.
        print("Reponse (debut):", resp.text[:300])
        resp.raise_for_status()
    return resp.json()

def main():
    data = search_offers()
    offers = data.get("results", [])
    print(f"{len(offers)} offres recues sur {data.get('count')} au total pour cette recherche")

    os.makedirs("data/offers", exist_ok=True)
    safe_params = {k: v for k, v in SEARCH_PARAMS.items()}
    with open("data/offers/raw_offers.json", "w", encoding="utf-8") as f:
        json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "source": "adzuna", "search_params": safe_params,
                   "total_count": data.get("count"), "offers": offers},
                  f, indent=2, ensure_ascii=False)
    print("Ecrit: data/offers/raw_offers.json")
    if offers:
        print("Apercu de la premiere offre:")
        print(json.dumps(offers[0], ensure_ascii=False, indent=2)[:1200])

if __name__ == "__main__":
    main()
