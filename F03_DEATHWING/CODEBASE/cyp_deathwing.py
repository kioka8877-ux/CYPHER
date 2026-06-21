"""
F03 DEATHWING — Déclencheur sandbox
Upload acier.py sur GH Release → trigger deathwing_render.yml → print URL
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
LEDGER_PATH = BASE / "cypher_ledger.json"
REPO = "kioka8877-ux/CYPHER"
ACIER_PATH = BASE / "F02_CALIBAN" / "OUT" / "acier.py"


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


def upload_acier(run_id: str) -> str:
    """Upload acier.py sur la release GH taggée avec run_id. Retourne le tag."""
    tag = f"cyp-{run_id}"
    # Supprimer release existante si elle existe (re-run)
    gh(["gh", "release", "delete", tag, "--repo", REPO, "--yes"],
       check=False)
    # Créer la release
    gh([
        "gh", "release", "create", tag,
        "--repo", REPO,
        "--title", f"CYPHER run {run_id}",
        "--notes", "Assets intermédiaires CYPHER — auto-généré",
        str(ACIER_PATH),
    ])
    print(f"[DEATHWING] acier.py uploadé → release {tag}")
    return tag


def trigger_workflow(run_id: str) -> str:
    """Déclenche deathwing_render.yml et retourne l'URL du run."""
    gh([
        "gh", "workflow", "run", "deathwing_render.yml",
        "--repo", REPO,
        "--field", f"run_id={run_id}",
    ])
    # Récupérer l'URL du run le plus récent
    import time; time.sleep(4)
    result = gh(
        ["gh", "run", "list", "--workflow", "deathwing_render.yml",
         "--repo", REPO, "--limit", "1", "--json", "url"],
        capture=True,
    )
    runs = json.loads(result.stdout)
    url = runs[0]["url"] if runs else f"https://github.com/{REPO}/actions"
    return url


def main():
    if not ACIER_PATH.exists():
        sys.exit("[DEATHWING] Erreur : acier.py introuvable. Lance gate2 d'abord.")

    ledger = load_ledger()
    run_id = ledger.get("run_id")
    if not run_id:
        sys.exit("[DEATHWING] Erreur : run_id absent du ledger. Lance start d'abord.")

    print(f"[DEATHWING] Run {run_id} — upload acier...")
    upload_acier(run_id)

    print("[DEATHWING] Trigger GitHub Actions...")
    url = trigger_workflow(run_id)

    ledger["gh_runs"]["deathwing"] = url
    ledger["status"] = "deathwing_running"
    save_ledger(ledger)

    print(f"\n[DEATHWING] Render en cours :\n  {url}")
    print("\n[CYPHER] Surveille le run. Quand il est vert → gate4")


if __name__ == "__main__":
    main()
