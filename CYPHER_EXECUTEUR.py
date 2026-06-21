"""
CYPHER_EXECUTEUR — télécommande sandbox
Opérateur intervient uniquement aux gates. Claude opère tout le reste.
"""
import argparse
import json
import os
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
    print("[CYPHER] GATE 1 — LION en cours...")
    # TODO: appeler cyp_lion.py
    print("[CYPHER] Implémenter F01_LION")


def cmd_gate2(args):
    """GATE 2 — valider le preview CALIBAN avant DEATHWING."""
    print("[CYPHER] GATE 2 — preview CALIBAN...")
    # TODO: appeler cyp_caliban.py + ouvrir preview HTML
    print("[CYPHER] Implémenter F02_CALIBAN")


def cmd_gate3(args):
    """GATE 3 — déclencher DEATHWING sur GH Actions."""
    print("[CYPHER] GATE 3 — trigger DEATHWING...")
    # TODO: workflow_dispatch deathwing_render.yml
    print("[CYPHER] Implémenter trigger DEATHWING")


def cmd_gate4(args):
    """GATE 4 — déclencher RAVENWING + LUTHER sur GH Actions."""
    print("[CYPHER] GATE 4 — trigger RAVENWING → LUTHER...")
    # TODO: workflow_dispatch ravenwing_assemble.yml
    print("[CYPHER] Implémenter trigger RAVENWING")


def cmd_close(args):
    """CLOSE — télécharger artefact final + archiver ledger."""
    print("[CYPHER] CLOSE — téléchargement artefact final...")
    # TODO: gh run download + archiver ledger
    print("[CYPHER] Implémenter CLOSE")


def main():
    parser = argparse.ArgumentParser(prog="CYPHER_EXECUTEUR")
    sub = parser.add_subparsers(dest="cmd")

    p_start = sub.add_parser("start")
    p_start.add_argument("--subject", required=True)
    p_start.add_argument("--duration", type=int, default=90)
    p_start.add_argument("--language", default="fr")
    p_start.add_argument("--tone", default="dramatique")

    sub.add_parser("gate2")
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
