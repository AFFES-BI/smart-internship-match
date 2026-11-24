import csv, json, os, re, time, unicodedata

# ---------------------------------------------------------------------------
# KPI de matching -- choix de conception (a justifier dans le rapport) :
#   1. Comparaison : insensible a la casse ET par mots entiers, en tenant compte des
#      noms entre parentheses des familles de competences du profil.
#      "Kaizen" trouve donc "Lean et amelioration continue (..., Kaizen, ...)".
#   2. Couverture = competences demandees que j'ai / competences demandees.
#      Offre sans aucune competence extraite -> couverture 0 (on ne peut pas affirmer
#      qu'elle me correspond sans information).
#   3. Score = somme des (niveau/5) des competences trouvees / competences demandees.
#      Une competence maitrisee (niveau 4-5) compte plus qu'une competence debutante.
#   4. Ajout (apres constat : 42 offres sur 50 sans competence extraite, descriptions
#      tronquees a 500 caracteres) : 2e signal = competences du profil mentionnees dans
#      le titre/la description meme si l'IA ne les a pas extraites ("text_only").
# ---------------------------------------------------------------------------

def load_profile(path="data/profile/my_skills.csv"):
    profile = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            profile[row["skill"]] = {"level": int(row["level"]), "evidence": row["evidence"]}
    return profile

def normalize(text):
    # minuscules, sans accents, espaces simplifies : "Prédictive " == "predictive"
    text = unicodedata.normalize("NFKD", text.strip().lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text)

def raw_aliases(skill_name):
    """Noms (casse d'origine) sous lesquels une ligne du profil peut apparaitre."""
    names = []
    base = re.sub(r"\(.*?\)", "", skill_name).strip()
    if base:
        names.append(base)
    for group in re.findall(r"\((.*?)\)", skill_name):
        names += [p.strip() for p in group.split(",") if p.strip()]
    return names

def profile_aliases(skill_name):
    """'Lean et amelioration continue (Lean Manufacturing, 5S)' ->
    {'lean et amelioration continue', 'lean manufacturing', '5s'}"""
    return {normalize(a) for a in raw_aliases(skill_name)}

def text_matches(profile, text):
    """Signal 2 : lignes du profil mentionnees dans le titre/la description de l'offre.
    Les sigles courts en majuscules (SAP, ERP, MES, IA) sont cherches en respectant la
    casse : 'MES' (systeme de production) ne doit pas matcher 'mes missions'."""
    if not text:
        return []
    norm_text = normalize(text)
    hits = []
    for name in profile:
        for alias in raw_aliases(name):
            if alias.isupper() and len(alias) <= 4:
                found = re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text) is not None
            else:
                found = contains_words(norm_text, normalize(alias))
            if found:
                hits.append(name)
                break
    return hits

def contains_words(haystack, needle):
    """True si `needle` apparait comme mot(s) entier(s) dans `haystack`."""
    return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None

def skill_matches(required, aliases):
    return any(required == a or contains_words(required, a) or contains_words(a, required)
               for a in aliases)

def score_offer(profile, required_skills, text=""):
    # Signal 1 : competences extraites par l'IA, nettoyees et dedoublonnees (casse ignoree).
    required = []
    for s in required_skills or []:
        n = normalize(str(s))
        if n and n not in required:
            required.append(n)

    aliases_by_skill = {name: profile_aliases(name) for name in profile}
    matched_profile = []   # lignes du profil trouvees (cles de `profile`, pour draft_cv)
    points = 0.0
    n_matched = 0
    gaps = []

    for req in required:
        hit = next((name for name, al in aliases_by_skill.items() if skill_matches(req, al)), None)
        if hit is None:
            gaps.append(req)
            continue
        n_matched += 1
        points += profile[hit]["level"] / 5      # pondere par mon niveau
        if hit not in matched_profile:
            matched_profile.append(hit)

    # Signal 2 : competences du profil mentionnees dans le titre/la description mais
    # non extraites par l'IA. Elles comptent comme "demandees ET trouvees" : le texte ne
    # permet de detecter que ce que je possede deja, jamais de nouveaux manques.
    text_only = [k for k in text_matches(profile, text) if k not in matched_profile]
    for k in text_only:
        n_matched += 1
        points += profile[k]["level"] / 5
        matched_profile.append(k)

    # Cas 2 : rien d'extrait ET rien detecte dans le texte -> couverture et score a 0.
    demanded = len(required) + len(text_only)
    if demanded == 0:
        return {"score": 0.0, "coverage": 0.0, "matched": [], "gaps": [], "text_only": []}

    return {
        "score": round(points / demanded, 4),
        "coverage": round(n_matched / demanded, 4),
        "matched": matched_profile,
        "gaps": gaps,
        "text_only": text_only,
    }

def build_output(results, profile):
    gap_counts = {}
    matched_counts = {}
    for r in results:
        for g in r["gaps"]:
            gap_counts[g] = gap_counts.get(g, 0) + 1
        for s in r["matched"]:
            matched_counts[s] = matched_counts.get(s, 0) + 1
    top_gaps = sorted(gap_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
    top_matched = sorted(matched_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
    n_with_comp = sum(1 for r in results if r.get("compensation_mentioned"))
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        # Mention exigee par les conditions d'utilisation d'Adzuna pour afficher leurs annonces.
        "attribution": "Offres : The Adzuna API (https://www.adzuna.fr)",
        "n_offers": len(results),
        "offers": results,
        "top_skill_gaps": [{"skill": s, "count": c} for s, c in top_gaps],
        "top_matched_skills": [{"skill": s, "count": c, "level": profile[s]["level"]} for s, c in top_matched],
        "n_offers_with_compensation": n_with_comp,
    }

def main():
    profile = load_profile()
    with open("data/offers/structured_offers.json", encoding="utf-8") as f:
        data = json.load(f)

    # Descriptions completes (500 car. max) pour le signal 2 : pas conservees dans structured_offers.json.
    with open("data/offers/merged_offers.json", encoding="utf-8") as f:
        descriptions = {o["id"]: o.get("description", "") for o in json.load(f)["offers"]}

    results = []
    for offer in data["offers"]:
        text = f"{offer['title']} {descriptions.get(offer['id'], '')}"
        m = score_offer(profile, offer["required_skills"], text)
        results.append({**offer, **m})

    results.sort(key=lambda r: r["score"], reverse=True)
    for r in results:
        print(f"  {r['score']:.3f}  {r['title']} @ {r['company']}  ({r['source']}, "
              f"couverture {r['coverage']:.0%}, trouvees: {r['matched']}, manquantes: {r['gaps']})")

    # Deux sorties : tout (local, gitignore) et uniquement les offres publiables (commit).
    os.makedirs("data/offers", exist_ok=True)
    with open("data/offers/matches_all_local.json", "w", encoding="utf-8") as f:
        json.dump(build_output(results, profile), f, indent=2, ensure_ascii=False)
    print(f"Ecrit: data/offers/matches_all_local.json ({len(results)} offres) -- gitignore, local uniquement")

    public_results = [r for r in results if r.get("publishable", False)]
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/matches.json", "w", encoding="utf-8") as f:
        json.dump(build_output(public_results, profile), f, indent=2, ensure_ascii=False)
    print(f"Ecrit: docs/data/matches.json ({len(public_results)} sur {len(results)} offres -- sources publiables)")

if __name__ == "__main__":
    main()
