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
    """GATE 1 — dialogue interactif LION (bloquant).
    L'opérateur répond aux questions une par une dans le terminal.
    """
    lion = Path(__file__).parent / "F01_LION" / "CODEBASE" / "cyp_lion.py"
    print("[CYPHER] GATE 1 — LION démarre le dialogue opérateur…\n")
    result = subprocess.run([sys.executable, str(lion)], env={**os.environ})
    if result.returncode != 0:
        sys.exit("[CYPHER] LION a échoué — vérifier les logs")
    print("\n[CYPHER] GATE 1 terminé.")
    print("  → Valide F01_LION/OUT/timing.json + config.json")
    print("  → Puis : python CYPHER_EXECUTEUR.py gate2")


def cmd_gate1_done(args):
    """Télécharge timing.json + audio_clean.mp3 depuis l'artifact GH f01-output."""
    ledger = load_ledger()
    run_id = ledger.get("run_id", "")
    gha_run_id = ledger.get("gh_runs", {}).get("f01")
    if not run_id:
        sys.exit("[CYPHER] Aucun run_id dans le ledger — lance d'abord 'start'")
    if not gha_run_id:
        sys.exit("[CYPHER] gh_runs.f01 absent — l'URL du run GH n'a pas été sauvegardée")

    import os, requests, zipfile, io
    token = os.environ.get("GH_TOKEN", "")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Accept-Encoding": "identity",
    }
    repo = "kioka8877-ux/CYPHER"
    out_dir = Path(__file__).parent / "F01_LION" / "OUT"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Trouver l'artifact f01-output
    url = f"https://api.github.com/repos/{repo}/actions/runs/{gha_run_id}/artifacts"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    artifacts = r.json().get("artifacts", [])
    artifact = next((a for a in artifacts if a["name"] == "f01-output"), None)
    if not artifact:
        sys.exit(f"[CYPHER] Artifact 'f01-output' introuvable sur le run {gha_run_id}")

    # Télécharger le ZIP de l'artifact
    print(f"[CYPHER] Téléchargement artifact f01-output ({artifact['size_in_bytes'] // 1024} KB)...")
    dl_url = artifact["archive_download_url"]
    r2 = requests.get(dl_url, headers=headers, allow_redirects=True)
    r2.raise_for_status()

    # Extraire
    with zipfile.ZipFile(io.BytesIO(r2.content)) as zf:
        zf.extractall(out_dir)
    print(f"  ✅ Extraits dans {out_dir}")

    # Vérifier
    for fname in ("timing.json", "audio_clean.mp3"):
        fpath = out_dir / fname
        if fpath.exists():
            print(f"  ✅ {fname} ({fpath.stat().st_size // 1024} KB)")
        else:
            print(f"  ⚠️  {fname} ABSENT")

    # Mise à jour ledger
    ledger["status"] = "f01_done"
    ledger.setdefault("assets", {})["audio_clean"] = str(out_dir / "audio_clean.mp3")
    save_ledger(ledger)

    print("\n[CYPHER] GATE 1 validé — timing.json et audio_clean.mp3 en place.")
    print("  → Lance : python CYPHER_EXECUTEUR.py gate2")


def cmd_gate2(args):
    """GATE 2 — CALIBAN preview HTML Imperivm + config_final.json."""
    caliban = Path(__file__).parent / "F02_CALIBAN" / "CODEBASE" / "cyp_caliban.py"
    cmd = [sys.executable, str(caliban), "--port", str(args.port)]
    print("[CYPHER] GATE 2 — CALIBAN preview (thème Imperivm)...")
    print(f"[CYPHER] Ouvre → http://localhost:{args.port}")
    print("[CYPHER] Ajuste les paramètres et clique VALIDER pour Gate 3")
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
    run_id = ledger.get("run_id", "")
    ledger["status"] = "victoria_aeterna"
    save_ledger(ledger)
    tag = f"cyp-{run_id}" if run_id else "cyp-???"
    print(f"\n[CYPHER] Quand LUTHER est vert, télécharge l'artefact final :")
    print(f"  gh release download {tag} --repo {REPO} --pattern clean_final.mp4 --dir .")
    print(f"\n[CYPHER] VICTORIA AETERNA")


def main():
    parser = argparse.ArgumentParser(prog="CYPHER_EXECUTEUR")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("start")  # dialogue interactif — aucun arg CLI requis
    sub.add_parser("gate1_done")  # télécharge artifacts f01 après run GH

    p_gate2 = sub.add_parser("gate2")
    p_gate2.add_argument("--port", type=int, default=8090)
    sub.add_parser("gate3")
    sub.add_parser("gate4")
    sub.add_parser("close")

    args = parser.parse_args()
    dispatch = {
        "start": cmd_start,
        "gate1_done": cmd_gate1_done,
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
