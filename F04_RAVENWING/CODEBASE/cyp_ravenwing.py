"""
F04 RAVENWING — Déclencheur sandbox
Télécharge vidéo DEATHWING depuis release → upload audio → trigger ravenwing_assemble.yml → print URL
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
LEDGER_PATH = BASE / "cypher_ledger.json"
REPO = "kioka8877-ux/CYPHER"
AUDIO_PATH = BASE / "SHARED" / "IN" / "audio_raw.mp3"


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


def upload_audio(run_id: str):
    """Upload audio_raw.mp3 sur la release existante."""
    if not AUDIO_PATH.exists():
        print(f"[RAVENWING] Avertissement : {AUDIO_PATH} absent — vidéo sera muette")
        return False
    tag = f"cyp-{run_id}"
    gh([
        "gh", "release", "upload", tag,
        "--repo", REPO,
        str(AUDIO_PATH),
        "--clobber",
    ])
    print(f"[RAVENWING] audio_raw.mp3 uploadé → release {tag}")
    return True


def upload_timeline(run_id: str):
    """Upload timeline_clock.json si disponible."""
    ledger = load_ledger()
    clock = ledger.get("timeline_clock")
    if not clock:
        print("[RAVENWING] Pas de timeline_clock — sync audio basique")
        return False
    tag = f"cyp-{run_id}"
    clock_path = BASE / "F01_LION" / "OUT" / "timeline_clock.json"
    clock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(clock_path, "w") as f:
        json.dump(clock, f, indent=2)
    gh([
        "gh", "release", "upload", tag,
        "--repo", REPO,
        str(clock_path),
        "--clobber",
    ])
    print("[RAVENWING] timeline_clock.json uploadé")
    return True


def trigger_workflow(run_id: str, has_audio: bool) -> str:
    """Déclenche ravenwing_assemble.yml et retourne l'URL du run."""
    gh([
        "gh", "workflow", "run", "ravenwing_assemble.yml",
        "--repo", REPO,
        "--field", f"run_id={run_id}",
        "--field", f"has_audio={'true' if has_audio else 'false'}",
    ])
    import time
    time.sleep(4)
    r = gh(
        ["gh", "run", "list", "--workflow", "ravenwing_assemble.yml",
         "--repo", REPO, "--limit", "1", "--json", "url"],
        capture=True,
    )
    runs = json.loads(r.stdout)
    return runs[0]["url"] if runs else f"https://github.com/{REPO}/actions"


def main():
    ledger = load_ledger()
    run_id = ledger.get("run_id")
    if not run_id:
        sys.exit("[RAVENWING] Erreur : pas de run_id dans le ledger — lance d'abord gate3")

    deathwing_run = ledger.get("gh_runs", {}).get("deathwing")
    if not deathwing_run:
        sys.exit("[RAVENWING] Erreur : DEATHWING n'a pas encore tourné — lance gate3")

    print(f"[RAVENWING] Run {run_id} — assemblage final")
    has_audio = upload_audio(run_id)
    upload_timeline(run_id)

    print("[RAVENWING] Déclenchement workflow assemblage...")
    url = trigger_workflow(run_id, has_audio)

    ledger.setdefault("gh_runs", {})["ravenwing"] = url
    save_ledger(ledger)

    print(f"\n[RAVENWING] Workflow lancé : {url}")
    print("[RAVENWING] Surveille le run → quand vert, lance : close")


if __name__ == "__main__":
    main()
