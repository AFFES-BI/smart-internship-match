import argparse, json, os, time
from datetime import datetime, timezone, timedelta

# Controle de sante de MA recherche de stage (monitoring, CM4 : declencheur -> lancement -> verification).
# Ce n'est pas un test de code : il repond a "quelque chose cloche-t-il dans ma recherche ?".
# Chaque lancement est ajoute a docs/data/monitoring_log.json (trace des lancements reels).
#
# Seuils choisis (a justifier dans le rapport) :
#   - donnees : plus de 7 jours -> a actualiser (le prof demande max. 1 actualisation/semaine)
#   - au moins 1 offre avec un score >= 0.30, sinon la recherche ne me sert a rien
#   - au moins 30 % des offres avec une information exploitable (competences extraites ou detectees)
#   - candidature sans reponse depuis plus de 10 jours -> relancer

STALE_DAYS = 7
MIN_GOOD_SCORE = 0.30
MIN_INFO_SHARE = 0.30
NO_RESPONSE_DAYS = 10

def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def parse_date(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc) if "T" in s \
        else datetime.fromisoformat(s).replace(tzinfo=timezone.utc)

def run_checks(matches, tracker, now):
    checks = []
    offers = matches.get("offers", [])

    # 1. Fraicheur des donnees
    gen = matches.get("generated_at")
    if gen:
        age = (now - parse_date(gen)).days
        status = "WARN" if age > STALE_DAYS else "OK"
        checks.append({"name": "donnees_a_jour", "status": status,
                       "detail": f"donnees vieilles de {age} jour(s) (seuil : {STALE_DAYS})"})
    else:
        checks.append({"name": "donnees_a_jour", "status": "ALERT", "detail": "date de generation absente"})

    # 2. Au moins une bonne offre
    good = [o for o in offers if o.get("score", 0) >= MIN_GOOD_SCORE]
    checks.append({"name": "offres_bien_classees",
                   "status": "OK" if good else "ALERT",
                   "detail": f"{len(good)} offre(s) avec un score >= {MIN_GOOD_SCORE} sur {len(offers)}"})

    # 3. Part d'offres exploitables (le piege decouvert : descriptions tronquees)
    informative = [o for o in offers if o.get("required_skills") or o.get("text_only")]
    share = len(informative) / len(offers) if offers else 0
    checks.append({"name": "offres_exploitables",
                   "status": "OK" if share >= MIN_INFO_SHARE else "WARN",
                   "detail": f"{share:.0%} des offres ont une information exploitable (seuil : {MIN_INFO_SHARE:.0%}) "
                             f"-- un score 0 peut vouloir dire 'pas d'information'"})

    # 4. Candidatures sans reponse
    apps = tracker.get("applications", [])
    if not apps:
        checks.append({"name": "candidatures_sans_reponse", "status": "INFO",
                       "detail": "aucune candidature enregistree dans applications.json"})
    else:
        late = []
        for a in apps:
            if a.get("response", "none") == "none" and a.get("sent_on"):
                waited = (now - parse_date(a["sent_on"])).days
                if waited > NO_RESPONSE_DAYS:
                    late.append(f"{a.get('offer_id', '?')} ({waited} j)")
        checks.append({"name": "candidatures_sans_reponse",
                       "status": "ALERT" if late else "OK",
                       "detail": (f"{len(late)} sans reponse depuis plus de {NO_RESPONSE_DAYS} j : " + ", ".join(late))
                                 if late else f"aucune candidature en attente depuis plus de {NO_RESPONSE_DAYS} j"})
    return checks

def overall(checks):
    statuses = {c["status"] for c in checks}
    return "ALERT" if "ALERT" in statuses else "WARN" if "WARN" in statuses else "OK"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", default="docs/data/matches.json")
    ap.add_argument("--apps", default="docs/data/applications.json")
    ap.add_argument("--log", default="docs/data/monitoring_log.json")
    ap.add_argument("--now", help="date de reference ISO (tests uniquement)")
    ap.add_argument("--no-log", action="store_true", help="ne pas enregistrer ce lancement (tests)")
    args = ap.parse_args()

    now = parse_date(args.now) if args.now else datetime.now(timezone.utc)
    checks = run_checks(load(args.matches, {}), load(args.apps, {}), now)
    result = {"run_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "status": overall(checks), "checks": checks}

    print(f"Controle du {result['run_at']} -> {result['status']}")
    for c in checks:
        print(f"  [{c['status']:5}] {c['name']}: {c['detail']}")

    if not args.no_log:
        log = load(args.log, {"runs": []})
        log["runs"].append(result)
        os.makedirs(os.path.dirname(args.log), exist_ok=True)
        with open(args.log, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
        print(f"Lancement enregistre dans {args.log} ({len(log['runs'])} au total)")

if __name__ == "__main__":
    main()
