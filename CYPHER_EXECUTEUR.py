"""
CYPHER_EXECUTEUR — télécommande sandbox
Opérateur intervient uniquement aux gates. Claude opère tout le reste.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

LEDGER = Path(__file__).parent / "cypher_ledger.json"
REPO = "kioka8877-ux/CYPHER"
GH_TOKEN = os.environ.get("GH_TOKEN", "")


def load_ledger():
    with open(LEDGER) as f:
        return json.load(f)


def save_ledger(data):
    with open(LEDGER, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cmd_start(args):
    """GATE 1 — brief opérateur → LION génère le script + spatial_events."""
    lion = Path(__file__).parent / "F01_LION" / "CODEBASE" / "cyp_lion.py"
    cmd = [
        sys.executable, str(lion),
        "--subject", args.subject,
        "--duration", str(args.duration),
        "--language", args.language,
        "--tone", args.tone,
    ]
    print(f"[CYPHER] GATE 1 — LION oracle en cours...")
    result = subprocess.run(cmd, env={**os.environ})
    if result.returncode != 0:
        sys.exit("[CYPHER] LION a échoué — vérifier les logs")
    print("\n[CYPHER] GATE 1 terminé. Valide le script dans le ledger puis lance: gate2")


def cmd_gate2(args):
    """GATE 2 — CALIBAN génère acier.py + preview HTML opérateur."""
    caliban = Path(__file__).parent / "F02_CALIBAN" / "CODEBASE" / "cyp_caliban.py"
    cmd = [sys.executable, str(caliban), "--serve", "--port", str(args.port)]
    print("[CYPHER] GATE 2 — CALIBAN en cours (acier + preview)...")
    result = subprocess.run(cmd, env={**os.environ})
    if result.returncode != 0:
        sys.exit("[CYPHER] CALIBAN a échoué — vérifier les logs")


def cmd_gate3(args):
    """GATE 3 — déclencher DEATHWING sur GH Actions."""
    deathwing = Path(__file__).parent / "F03_DEATHWING" / "CODEBASE" / "cyp_deathwing.py"
    print("[CYPHER] GATE 3 — DEATHWING render en cours...")
    result = subprocess.run([sys.executable, str(deathwing)], env={**os.environ})
    if result.returncode != 0:
        sys.exit("[CYPHER] DEATHWING a échoué — vérifier les logs")


def cmd_gate4(args):
    """GATE 4 — déclencher RAVENWING (assemblage final)."""
    ravenwing = Path(__file__).parent / "F04_RAVENWING" / "CODEBASE" / "cyp_ravenwing.py"
    print("[CYPHER] GATE 4 — RAVENWING assemblage en cours...")
    result = subprocess.run([sys.executable, str(ravenwing)], env={**os.environ})
    if result.returncode != 0:
        sys.exit("[CYPHER] RAVENWING a échoué — vérifier les logs")


def cmd_close(args):
    """CLOSE — déclencher LUTHER (purge metadata) → print URL → instructions download."""
    luther = Path(__file__).parent / "F05_LUTHER" / "CODEBASE" / "cyp_luther.py"
    print("[CYPHER] CLOSE — LUTHER purge finale...")
    result = subprocess.run([sys.executable, str(luther)], env={**os.environ})
    if result.returncode != 0:
        sys.exit("[CYPHER] LUTHER a échoué — vérifier les logs")
    ledger = load_ledger()
    run_id = ledger.get("current_run_id", "")
    ledger["status"] = "victoria_aeterna"
    save_ledger(ledger)
    tag = f"cyp-{run_id}" if run_id else "cyp-???"
    print(f"\n[CYPHER] Quand LUTHER est vert, télécharge l'artefact final :")
    print(f"  gh release download {tag} --repo {REPO} --pattern clean_final.mp4 --dir .")
    print(f"\n[CYPHER] VICTORIA AETERNA")


def main():
    parser = argparse.ArgumentParser(prog="CYPHER_EXECUTEUR")
    sub = parser.add_subparsers(dest="cmd")

    p_start = sub.add_parser("start")
    p_start.add_argument("--subject", required=True)
    p_start.add_argument("--duration", type=int, default=90)
    p_start.add_argument("--language", default="fr")
    p_start.add_argument("--tone", default="dramatique")

    p_gate2 = sub.add_parser("gate2")
    p_gate2.add_argument("--port", type=int, default=8090)
    sub.add_parser("gate3")
    sub.add_parser("gate4")
    sub.add_parser("close")

    args = parser.parse_args()
    dispatch = {
        "start": cmd_start,
        "gate2": cmd_gate2,
        "gate3": cmd_gate3,
        "gate4": cmd_gate4,
        "close": cmd_close,
    }
    if args.cmd not in dispatch:
        parser.print_help()
        sys.exit(1)
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
