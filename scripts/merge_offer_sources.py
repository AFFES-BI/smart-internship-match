import json, os

# Normalise les offres de TOUTES les sources vers un schema commun.
# Source actuelle : Adzuna (remplace France Travail, cf. mail du prof).
# Pour ajouter une source, ecrire une fonction normalize_xxx() et l'ajouter dans main().

RAW_PATH = "data/offers/raw_offers.json"
MERGED_PATH = "data/offers/merged_offers.json"

# ATTENTION : decision a confirmer avant de publier quoi que ce soit.
# True = ces offres peuvent apparaitre dans docs/data/matches.json (depot public).
# A verifier dans les conditions d'utilisation d'Adzuna (attribution "Jobs by Adzuna"
# a afficher sur le dashboard).
ADZUNA_PUBLISHABLE = True

def normalize_adzuna(raw_offers):
    normalized = []
    for o in raw_offers:
        normalized.append({
            "id": f"adz_{o['id']}",
            "source": "adzuna",
            "title": o.get("title"),
            "company": (o.get("company") or {}).get("display_name"),
            "location": (o.get("location") or {}).get("display_name"),
            "description": o.get("description", ""),
            "url": o.get("redirect_url"),
            "date_posted": o.get("created"),
            "category": (o.get("category") or {}).get("label"),
            "contract_type": o.get("contract_type"),
            "salary_min": o.get("salary_min"),
            "salary_max": o.get("salary_max"),
            "salary_is_predicted": o.get("salary_is_predicted"),
            "publishable": ADZUNA_PUBLISHABLE,
        })
    return normalized

def main():
    with open(RAW_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    merged = normalize_adzuna(raw["offers"])
    print(f"{len(merged)} offres normalisees (source: adzuna)")

    os.makedirs("data/offers", exist_ok=True)
    with open(MERGED_PATH, "w", encoding="utf-8") as f:
        json.dump({"offers": merged}, f, indent=2, ensure_ascii=False)
    print(f"Ecrit: {MERGED_PATH} -- gitignore, local uniquement")

if __name__ == "__main__":
    main()
