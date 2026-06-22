"""
F03 DEATHWING — Déclencheur sandbox
Upload render_spec.json + visuels sur GH Release → trigger deathwing_render.yml → print URL
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE         = Path(__file__).parent.parent.parent
LEDGER_PATH  = BASE / "cypher_ledger.json"
REPO         = "kioka8877-ux/CYPHER"
RENDER_SPEC  = BASE / "F02_CALIBAN" / "OUT" / "render_spec.json"
VISUALS_DIR  = BASE / "F01_LION" / "OUT" / "visuals"


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


def upload_assets(run_id: str) -> str:
    """Upload render_spec.json + visuels sur la release GH. Retourne le tag."""
    tag = f"cyp-{run_id}"
    gh(["gh", "release", "delete", tag, "--repo", REPO, "--yes"], check=False)

    # Collecter les fichiers à uploader
    assets = [str(RENDER_SPEC)]
    if VISUALS_DIR.exists():
        for f in VISUALS_DIR.iterdir():
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".mp4", ".webm"):
                assets.append(str(f))

    gh([
        "gh", "release", "create", tag,
        "--repo", REPO,
        "--title", f"CYPHER run {run_id}",
        "--notes", "Assets intermédiaires CYPHER — auto-généré",
        *assets,
    ])
    print(f"[DEATHWING] {len(assets)} assets uploadés → release {tag}")
    return tag


def trigger_workflow(run_id: str) -> str:
    """Déclenche deathwing_render.yml et retourne l'URL du run."""
    gh([
        "gh", "workflow", "run", "deathwing_render.yml",
        "--repo", REPO,
        "--field", f"run_id={run_id}",
    ])
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
    if not RENDER_SPEC.exists():
        sys.exit("[DEATHWING] Erreur : render_spec.json introuvable. Lance gate2 d'abord.")

    ledger = load_ledger()
    run_id = ledger.get("run_id")
    if not run_id:
        sys.exit("[DEATHWING] Erreur : run_id absent du ledger. Lance start d'abord.")

    print(f"[DEATHWING] Run {run_id} — upload render_spec + visuels...")
    upload_assets(run_id)

    print("[DEATHWING] Trigger GitHub Actions...")
    url = trigger_workflow(run_id)

    ledger["gh_runs"]["deathwing"] = url
    ledger["status"] = "deathwing_running"
    save_ledger(ledger)

    print(f"\n[DEATHWING] Render en cours :\n  {url}")
    print("\n[CYPHER] Surveille le run. Quand il est vert → gate4")


if __name__ == "__main__":
    main()
