import json, os, sys, time
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3:8b"
MERGED_PATH = "data/offers/merged_offers.json"
OUT_PATH = "data/offers/structured_offers.json"

PROMPT_TEMPLATE = """Extract ONLY these things from this job/internship description text
(it may be in French or English). The text may be cut off after 500 characters: only use what is written.
Return ONLY valid JSON with keys:
- required_skills: array of concrete named tools/technologies/hard skills mentioned (e.g. "Python", "SolidWorks", "SAP", "Lean") -- do not include generic soft skills or the job title
- responsibilities: array of the actual tasks/missions described
- experience_required: a short string quoting the explicit experience requirement stated in the text (e.g. "2 years", "no experience required", "Bac+5", "enrolled in a Master's program"), or null if the text does not explicitly state one. Do NOT infer this from the job title, from words like "Senior"/"Lead" in the title, or from general seniority tone -- only from an actual requirement sentence in the text.
- compensation_mentioned: a short verbatim quote of any salary/compensation/gratification FIGURE explicitly stated in the text (e.g. "600 euros/mois"), or null if no concrete number is stated anywhere in the text. Read the ENTIRE text, including the end, before concluding there is none.

Do not extract title, company, or location -- those come from elsewhere and are not in this text.
No explanation, just the JSON object.

TEXT:
{text}
"""

def call_ollama(prompt, retries=3, backoff=5):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                OLLAMA_URL,
                proxies={"http": None, "https": None},
                json={"model": MODEL, "prompt": prompt, "format": "json", "stream": False},
                timeout=(10, 180),
            )
            resp.raise_for_status()
            return json.loads(resp.json()["response"])
        except Exception as e:
            last_error = e
            print(f"  Ollama call attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(backoff)
    raise RuntimeError(f"Ollama unreachable or model not available after {retries} attempts") from last_error

def save(structured):
    os.makedirs("data/offers", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "offers": structured}, f, indent=2, ensure_ascii=False)

def main():
    # Usage : python scripts/extract_offers.py [N]   (N = nombre max d'offres a traiter, pour tester)
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    with open(MERGED_PATH, encoding="utf-8") as f:
        merged = json.load(f)

    # Reprise : les offres deja extraites ne sont pas refaites (utile si on interrompt le script).
    structured = []
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as f:
            structured = json.load(f)["offers"]
    done = {o["id"] for o in structured}

    todo = [o for o in merged["offers"] if o["id"] not in done]
    if limit:
        todo = todo[:limit]
    print(f"{len(done)} deja faites, {len(todo)} a traiter")

    for i, offer in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {offer['id']}: {offer['title']}", flush=True)
        extracted = call_ollama(PROMPT_TEMPLATE.format(text=offer.get("description", "")))
        structured.append({
            "id": offer["id"],
            "source": offer["source"],
            "title": offer["title"],
            "company": offer.get("company"),
            "location": offer.get("location"),
            "url": offer.get("url"),
            "date_posted": offer.get("date_posted"),
            "publishable": offer.get("publishable", False),
            "salary_min": offer.get("salary_min"),
            "salary_max": offer.get("salary_max"),
            "required_skills": extracted.get("required_skills", []),
            "responsibilities": extracted.get("responsibilities", []),
            "experience_required": extracted.get("experience_required"),
            "compensation_mentioned": extracted.get("compensation_mentioned"),
        })
        save(structured)  # sauvegarde apres chaque offre

    print(f"Ecrit: {OUT_PATH} ({len(structured)} offres) -- gitignore, local uniquement")

if __name__ == "__main__":
    main()
