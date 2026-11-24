import csv, json, os, re, time
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3:8b"
TOP_N = 3
MIN_COVERAGE = 0.3

PROMPT_TEMPLATE = """Tu es un(e) assistant(e) de redaction. Redige UNIQUEMENT le paragraphe
d'accroche (3-4 phrases) d'une lettre de motivation en francais, pour l'offre suivante, en
mettant en avant UNIQUEMENT les competences du candidat qui correspondent reellement a l'offre
(n'invente aucune competence ou experience non listee ci-dessous).

Contexte du candidat: eleve ingenieur en genie industriel (ESPRIT, Tunisie), actuellement en
semestre d'echange a l'ENSIM (Le Mans), a la recherche d'un stage de fin d'etudes.
Offre: {title} chez {company}
Missions: {responsibilities}
Competences requises correspondantes chez le candidat: {matched_skills}
Preuves concretes du candidat: {evidence}

N'invente aucune experience professionnelle non mentionnee. Si une competence est indiquee
comme "en cours d'apprentissage", ne dis pas que le candidat la maitrise. Style: direct,
concret, pas de formules creuses.
"""

def load_profile(path="data/profile/my_skills.csv"):
    profile = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            profile[row["skill"]] = row["evidence"]
    return profile

def short_name(skill):
    # "ERP et MES (SAP, MES)" -> "ERP et MES" : plus lisible dans le prompt
    return re.sub(r"\s*\(.*?\)", "", skill).strip()

def call_ollama(prompt, retries=3, backoff=5):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                OLLAMA_URL,
                proxies={"http": None, "https": None},
                json={"model": MODEL, "prompt": prompt, "stream": False},
                timeout=(10, 300),
            )
            resp.raise_for_status()
            return resp.json()["response"].strip()
        except Exception as e:
            last_error = e
            print(f"  Ollama call attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(backoff)
    raise RuntimeError(f"Ollama unreachable after {retries} attempts") from last_error

def main():
    profile = load_profile()
    # matches_all_local.json (toutes sources) : usage personnel et prive, jamais publie.
    with open("data/offers/matches_all_local.json", encoding="utf-8") as f:
        data = json.load(f)

    candidates = [o for o in data["offers"] if o["coverage"] >= MIN_COVERAGE][:TOP_N]
    print(f"Brouillons pour {len(candidates)} offres sur {data['n_offers']} "
          f"(couverture >= {MIN_COVERAGE:.0%}, top {TOP_N})", flush=True)

    os.makedirs("output/cv_drafts", exist_ok=True)
    for offer in candidates:
        evidence = {short_name(s): profile[s] for s in offer["matched"] if s in profile}
        prompt = PROMPT_TEMPLATE.format(
            title=offer["title"], company=offer["company"] or "cette entreprise",
            responsibilities=", ".join(offer["responsibilities"]) or "non precisees dans l'extrait de l'offre",
            matched_skills=", ".join(short_name(s) for s in offer["matched"]),
            evidence=json.dumps(evidence, ensure_ascii=False),
        )
        print(f"  Brouillon pour: {offer['title']} @ {offer['company']}...", flush=True)
        paragraph = call_ollama(prompt)
        out_path = f"output/cv_drafts/offer_{offer['id']}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"Offre: {offer['title']} @ {offer['company']}\n"
                    f"Competences utilisees: {', '.join(short_name(s) for s in offer['matched'])}\n\n"
                    f"{paragraph}\n")
        print(f"    -> {out_path}", flush=True)

    print("\nRappel: output/cv_drafts/ est ignore par git -- brouillons personnels, "
          "a relire et corriger soi-meme, jamais a committer.")

if __name__ == "__main__":
    main()
