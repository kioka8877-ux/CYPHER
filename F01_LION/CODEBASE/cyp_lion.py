"""
F01 LION — Collecte des inputs opérateur + upload audio + trigger GH Actions Whisper
Dialogue bloquant. L'opérateur répond une question à la fois.
"""
import datetime
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

import requests

REPO = "kioka8877-ux/CYPHER"
BASE_DIR = Path(__file__).parent.parent.parent  # racine CYPHER/
LEDGER_PATH = BASE_DIR / "cypher_ledger.json"
OUT_DIR = Path(__file__).parent.parent / "OUT"

GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_API = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "Accept-Encoding": "identity",
}


def _ask(prompt, choices=None):
    while True:
        val = input(f"\n{prompt}\n> ").strip()
        if choices and val not in choices:
            print(f"  Choix valides : {', '.join(choices)}")
            continue
        if val:
            return val


def _load_ledger():
    if LEDGER_PATH.exists():
        with open(LEDGER_PATH) as f:
            return json.load(f)
    return {}


def _save_ledger(data):
    with open(LEDGER_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _create_release(run_id):
    url = f"{GH_API}/repos/{REPO}/releases"
    r = requests.post(url, headers=HEADERS, json={
        "tag_name": run_id,
        "name": f"CYPHER Run {run_id}",
        "body": "Run auto-généré par CYPHER_EXECUTEUR",
        "draft": False,
        "prerelease": True,
    })
    r.raise_for_status()
    return r.json()


def _upload_asset(release, filepath, filename):
    upload_url = release["upload_url"].replace("{?name,label}", "")
    with open(filepath, "rb") as f:
        data = f.read()
    r = requests.post(
        upload_url,
        headers={**HEADERS, "Content-Type": "application/octet-stream"},
        params={"name": filename},
        data=data,
    )
    r.raise_for_status()
    return r.json()


def _trigger_workflow(run_id):
    url = f"{GH_API}/repos/{REPO}/actions/workflows/f01_lion.yml/dispatches"
    r = requests.post(url, headers=HEADERS, json={
        "ref": "main",
        "inputs": {"run_id": run_id},
    })
    r.raise_for_status()


def _get_latest_run_url():
    url = f"{GH_API}/repos/{REPO}/actions/workflows/f01_lion.yml/runs"
    for _ in range(10):
        r = requests.get(url, headers=HEADERS, params={"per_page": 3})
        runs = r.json().get("workflow_runs", [])
        if runs:
            run = runs[0]
            return run["html_url"], run["id"]
        time.sleep(3)
    return f"https://github.com/{REPO}/actions", None


def main():
    print("\n" + "═" * 50)
    print("  CYPHER — F01 LION — Collecte des inputs")
    print("═" * 50)

    # 1. Audio
    print("\n[1/5] AUDIO")
    audio_path = _ask("Chemin absolu du fichier audio (.mp3 / .wav / .m4a)")
    audio_path = Path(audio_path).expanduser().resolve()
    if not audio_path.exists():
        sys.exit(f"[LION] Fichier introuvable : {audio_path}")
    print(f"  ✅ Audio : {audio_path.name}  ({audio_path.stat().st_size // 1024} KB)")

    # 2. Format
    fmt = _ask("[2/5] FORMAT — short (< 3 min) ou long (> 3 min) ?", ["short", "long"])

    # 3. Style de carte
    style = _ask(
        "[3/5] STYLE CARTE — dark / light / satellite / terrain / military",
        ["dark", "light", "satellite", "terrain", "military"],
    )

    # 4. Visuels
    print("\n[4/5] VISUELS")
    print("  (A) ZIP fourni — tu as tes images prêtes")
    print("  (B) Recherche internet — tu donnes des instructions")
    print("  (C) Aucun — cartes seules")
    visuals_mode = _ask("Choix ?", ["A", "B", "C"])

    visuals_zip = None
    visuals_search = None

    if visuals_mode == "A":
        zip_path = _ask("Chemin du fichier ZIP")
        zip_path = Path(zip_path).expanduser().resolve()
        if not zip_path.exists():
            sys.exit(f"[LION] ZIP introuvable : {zip_path}")
        visuals_zip = zip_path
        print(f"  ✅ ZIP : {zip_path.name}")
    elif visuals_mode == "B":
        visuals_search = _ask(
            "Décris le type d'images à chercher\n"
            "  ex: 'illustrations Empire ottoman 15e siècle, style gravure'"
        )

    # 5. Sous-titres
    print("\n[5/5] SOUS-TITRES (Entrée = valeur par défaut)")
    fonts = ["Cinzel", "Arrila Black", "Bebas Neue", "Oswald", "Montserrat"]
    print("  Polices : " + " | ".join(fonts))
    font = input("  Police [Cinzel] : ").strip() or "Cinzel"
    font_color = input("  Couleur hex [#FFFFFF] : ").strip() or "#FFFFFF"
    font_size = input("  Taille px [52] : ").strip() or "52"
    position = input("  Position — bottom / center [bottom] : ").strip() or "bottom"
    anim = input("  Animation — ltr / none [ltr] : ").strip() or "ltr"
    visual_scale = input("  Échelle visuels 0.1-1.0 [0.85] : ").strip() or "0.85"

    # run_id
    run_id = "CYP_" + datetime.datetime.now().strftime("%Y%m%d_%H%M")
    print(f"\n[LION] Run ID : {run_id}")

    # Préparer audio MP3
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    in_dir = OUT_DIR.parent / "IN"
    in_dir.mkdir(parents=True, exist_ok=True)

    mp3_dest = in_dir / "audio_raw.mp3"
    if audio_path.suffix.lower() != ".mp3":
        print("[LION] Conversion en MP3 via FFmpeg...")
        ret = os.system(
            f'ffmpeg -y -i "{audio_path}" -ar 16000 -ac 1 -ab 128k "{mp3_dest}" -loglevel quiet'
        )
        if ret != 0:
            shutil.copy(audio_path, mp3_dest)
    else:
        if audio_path.resolve() != mp3_dest.resolve():
            shutil.copy(audio_path, mp3_dest)
    print(f"  ✅ audio_raw.mp3 ({mp3_dest.stat().st_size // 1024} KB)")

    # Visuals
    assets_info = {}
    if visuals_zip:
        zip_dest = in_dir / "visuals.zip"
        shutil.copy(visuals_zip, zip_dest)
        with zipfile.ZipFile(zip_dest) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
        assets_info = {"mode": "zip", "count": len(names), "files": names[:30]}
        print(f"  ✅ visuals.zip — {len(names)} fichiers")
    elif visuals_mode == "B":
        assets_info = {"mode": "search", "instructions": visuals_search}
    else:
        assets_info = {"mode": "none"}

    # config.json
    config = {
        "run_id": run_id,
        "format": fmt,
        "map_style": style,
        "visuals": assets_info,
        "display": {
            "font": font,
            "font_color": font_color,
            "font_size": int(font_size),
            "position": position,
            "animation": anim,
            "visual_scale": float(visual_scale),
        },
    }
    config_path = OUT_DIR / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"  ✅ config.json sauvegardé")

    # GH Release + upload
    if not GH_TOKEN:
        sys.exit("[LION] GH_TOKEN absent — export GH_TOKEN=<ton_token>")

    print("\n[LION] Création release GitHub...")
    release = _create_release(run_id)
    print(f"  ✅ Release {run_id} créée")

    print("[LION] Upload audio_raw.mp3...")
    _upload_asset(release, mp3_dest, "audio_raw.mp3")
    print("  ✅ audio_raw.mp3 uploadé")

    if visuals_zip:
        print("[LION] Upload visuals.zip...")
        _upload_asset(release, in_dir / "visuals.zip", "visuals.zip")
        print("  ✅ visuals.zip uploadé")

    # Trigger workflow
    print(f"\n[LION] Déclenchement f01_lion.yml...")
    _trigger_workflow(run_id)
    time.sleep(4)
    url, gha_run_id = _get_latest_run_url()

    # Mise à jour ledger
    ledger = _load_ledger()
    ledger.update({
        "run_id": run_id,
        "created_at": datetime.datetime.now().isoformat(),
        "status": "f01_running",
        "format": fmt,
        "map_style": style,
        "visuals": assets_info,
        "display": config["display"],
        "gh_runs": {"f01": gha_run_id, "deathwing": None, "ravenwing": None, "luther": None},
        "assets": {"audio_raw": str(mp3_dest), "audio_clean": None},
    })
    _save_ledger(ledger)

    print("\n" + "═" * 50)
    print("  GATE 1 DÉCLENCHÉ — surveille ici :")
    print(f"  {url}")
    print("═" * 50)
    print("\n  Quand le run est vert ✅ :")
    print("  python CYPHER_EXECUTEUR.py gate1_done")
    print()


if __name__ == "__main__":
    main()
