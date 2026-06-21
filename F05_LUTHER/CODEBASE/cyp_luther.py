"""
F05 LUTHER — Déclencheur sandbox
Télécharge youtube_final.mp4 depuis release → trigger luther_purge.yml → print URL
Empreinte zéro : strip total métadonnées via ffmpeg -c copy -map_metadata -1
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
LEDGER_PATH = BASE / "cypher_ledger.json"
REPO = "kioka8877-ux/CYPHER"


def load_ledger():
    with open(LEDGER_PATH) as f:
        return json.load(f)


def save_ledger(data):
    with open(LEDGER_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def gh(cmd, check=True, capture=False):
    env = {**os.environ, "GH_TOKEN": os.environ.get("GH_TOKEN", "")}
    kwargs = dict(env=env, check=check)
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    return subprocess.run(cmd, **kwargs)


def trigger_workflow(run_id: str, production_date: str) -> str:
    """Déclenche luther_purge.yml et retourne l'URL du run."""
    gh([
        "gh", "workflow", "run", "luther_purge.yml",
        "--repo", REPO,
        "--field", f"run_id={run_id}",
        "--field", f"production_date={production_date}",
    ])
    time.sleep(4)
    result = gh(
        ["gh", "run", "list", "--repo", REPO,
         "--workflow", "luther_purge.yml",
         "--limit", "1", "--json", "url,databaseId"],
        capture=True,
    )
    runs = json.loads(result.stdout)
    if runs:
        return runs[0]["url"]
    return f"https://github.com/{REPO}/actions"


def main():
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        print("[LUTHER] Erreur : GH_TOKEN manquant")
        sys.exit(1)

    ledger = load_ledger()
    run_id = ledger.get("current_run_id")
    if not run_id:
        print("[LUTHER] Erreur : current_run_id absent du ledger")
        sys.exit(1)

    tag = f"cyp-{run_id}"
    production_date = ledger.get("production_date", "")
    if not production_date:
        from datetime import date
        production_date = date.today().isoformat()

    print()
    print("═" * 50)
    print("  F05 LUTHER — Effacement en cours")
    print("═" * 50)
    print(f"  Run ID       : {run_id}")
    print(f"  Release tag  : {tag}")
    print(f"  Date prod.   : {production_date}")
    print()

    # Vérifier que youtube_final.mp4 est sur la release
    result = gh(
        ["gh", "release", "view", tag, "--repo", REPO, "--json", "assets"],
        capture=True, check=False,
    )
    assets = []
    if result.returncode == 0:
        data = json.loads(result.stdout)
        assets = [a["name"] for a in data.get("assets", [])]

    if "youtube_final.mp4" not in assets:
        print(f"[LUTHER] Erreur : youtube_final.mp4 absent de la release {tag}")
        print(f"  Assets présents : {assets}")
        sys.exit(1)

    print(f"[LUTHER] youtube_final.mp4 confirmé sur release {tag}")

    # Déclencher le workflow
    print("[LUTHER] Déclenchement luther_purge.yml...")
    url = trigger_workflow(run_id, production_date)

    # Mettre à jour le ledger
    ledger.setdefault("gh_runs", {})["f05"] = url
    save_ledger(ledger)

    print()
    print(f"  LUTHER DÉCLENCHÉ : {url}")
    print()
    print("  Surveille le run — quand vert :")
    print("  clean_final.mp4 disponible sur la release GitHub")
    print("  Empreinte zéro garantie.")
    print()


if __name__ == "__main__":
    main()
