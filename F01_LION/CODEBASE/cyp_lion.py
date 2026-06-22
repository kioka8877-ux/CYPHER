"""
F01 LION — Input collector + Whisper transcription + timing/config generator

Inputs operateur :
  --audio          audio.mp3 / .wav  (la voix qui dirige tout)
  --format         short (9:16) | long (16:9)
  --style-carte    osm | satellite | dark | terrain
  --visuals-zip    chemin vers un ZIP d'images (option A — operateur fournit)
  --visuals-search instructions pour chercher sur internet (option B)
  --visual-count   nombre de visuels souhaites (option B, defaut 8)

Outputs :
  F01_LION/OUT/timing.json   timestamps enrichis (camera, pop visuels, pays, SFX)
  F01_LION/OUT/config.json   tout ce que F03 a besoin (format, carte, polices, etc.)

Gate 1 : operateur valide les deux JSONs, puis lance gate2.
"""

import argparse
import json
import os
import sys
import datetime
import zipfile
import shutil
from pathlib import Path

import requests

# ---- Paths -----------------------------------------------------------------
BASE   = Path(__file__).parent.parent.parent   # CYPHER root
IN_DIR = Path(__file__).parent.parent / "IN"
OUT_DIR = Path(__file__).parent.parent / "OUT"
LEDGER = BASE / "cypher_ledger.json"

# ---- AI Gateway ------------------------------------------------------------
AI_BASE = os.environ.get("AI_GATEWAY_BASE_URL", "")
AI_KEY  = os.environ.get("AI_GATEWAY_API_KEY", "")
MODEL   = "anthropic/claude-haiku-4.5"

FORMATS = {
    "short": {"width": 1080, "height": 1920, "fps": 30, "label": "Vertical Shorts 9:16"},
    "long":  {"width": 1920, "height": 1080, "fps": 30, "label": "Horizontal Standard 16:9"},
}

# ---- Ledger ----------------------------------------------------------------

def load_ledger() -> dict:
    if LEDGER.exists():
        with open(LEDGER) as f:
            return json.load(f)
    return {"status": "init"}

def save_ledger(data: dict):
    with open(LEDGER, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---- Whisper ---------------------------------------------------------------

def transcribe_audio(audio_path: Path) -> dict:
    """Word-level transcription via faster-whisper (CPU). Fallback stub si absent."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("medium", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(audio_path), word_timestamps=True)

        words, full = [], []
        for seg in segments:
            full.append(seg.text.strip())
            for w in (seg.words or []):
                words.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                })

        return {
            "transcript": " ".join(full),
            "duration": round(info.duration, 3),
            "language": info.language,
            "words": words,
        }

    except ImportError:
        print("[LION] faster-whisper absent — stub transcript")
        return {
            "transcript": "(transcription non disponible)",
            "duration": 90.0,
            "language": "fr",
            "words": [],
        }

# ---- AI Gateway helpers ----------------------------------------------------

def _ai(messages: list, max_tokens: int = 4096, temperature: float = 0.3) -> str:
    r = requests.post(
        f"{AI_BASE}/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {AI_KEY}",
            "Content-Type": "application/json",
            "Accept-Encoding": "identity",
        },
        json={
            "model": MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

# ---- timing.json + config.json generator -----------------------------------

def generate_timing_and_config(whisper: dict, fmt: str, style_carte: str, n_visuals: int) -> tuple:
    """
    Appelle AI Gateway avec la transcription Whisper et genere :
      - timing.json : timestamps enrichis (camera, visuels, pays, SFX)
      - config.json : parametres complets de rendu
    """
    fi = FORMATS[fmt]
    total_frames = int(whisper["duration"] * fi["fps"])

    system = (
        "Tu es expert en montage video geopolitique. "
        "Reponds UNIQUEMENT avec les deux blocs JSON demandes, zero texte hors JSON. "
        "Separe les deux blocs par la ligne exacte : ---CONFIG---"
    )

    user = f"""Transcription audio :
TRANSCRIPT : {whisper['transcript']}
DUREE      : {whisper['duration']}s
FORMAT     : {fmt} — {fi['width']}x{fi['height']} @ {fi['fps']}fps ({total_frames} frames)
STYLE CARTE: {style_carte}
N VISUELS  : {n_visuals}

Genere TIMING_JSON (d'abord), puis la ligne ---CONFIG---, puis CONFIG_JSON.

TIMING_JSON :
{{
  "meta": {{"fps": {fi['fps']}, "duration": {whisper['duration']}, "total_frames": {total_frames}}},
  "word_timestamps": [],
  "camera_events": [{{"t": 0.0, "geo_focus": {{"lat": 0.0, "lon": 0.0, "zoom": 5}}, "duration": 5.0}}],
  "visual_events": [{{"t": 0.0, "visual_index": 0, "sfx": true}}],
  "country_events": [{{"t": 0.0, "iso": "FR", "color": "#B30006", "opacity": 0.8, "duration": 8.0}}],
  "sfx_events": [{{"t": 0.0, "type": "swoosh"}}]
}}

CONFIG_JSON :
{{
  "format": "{fmt}",
  "width": {fi['width']},
  "height": {fi['height']},
  "fps": {fi['fps']},
  "map_style": "{style_carte}",
  "map_provider": "osm",
  "visuals": [{{"index": 0, "t_start": 0.0, "t_end": 10.0, "subject": "description", "file": null}}],
  "subtitles": {{
    "font_family": "Cinzel",
    "font_color": "#FFFFFF",
    "font_size": 48,
    "position": "bottom",
    "animation": "left_to_right",
    "animation_speed": 1.0
  }},
  "visual_size": 0.4,
  "background_color": "#050B08"
}}

Regles :
- Genere {n_visuals} entrees dans config.json visuals, reparties sur toute la duree.
- camera_events et country_events doivent etre pertinents au contenu du transcript.
- Codes ISO 3166-1 alpha-2 pour les pays.
"""

    raw = _ai([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])

    if "---CONFIG---" in raw:
        timing_raw, config_raw = raw.split("---CONFIG---", 1)
    else:
        import re
        blocks = re.findall(r'\{[\s\S]+?\}(?=\s*\{|\s*$)', raw)
        if len(blocks) >= 2:
            timing_raw, config_raw = blocks[0], blocks[1]
        else:
            raise ValueError(f"Impossible de parser reponse AI :\n{raw[:500]}")

    for m in ("```json", "```"):
        timing_raw = timing_raw.replace(m, "").strip()
        config_raw = config_raw.replace(m, "").strip()

    timing = json.loads(timing_raw)
    config = json.loads(config_raw)

    # Injecter les vrais timestamps Whisper
    timing["word_timestamps"] = whisper["words"]

    return timing, config

# ---- Visuals: option A (ZIP operateur) ------------------------------------

def handle_visuals_zip(zip_path: Path) -> int:
    assets = IN_DIR / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    exts = {".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webm"}

    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            if not member.endswith("/"):
                name = Path(member).name
                if name and not name.startswith(".") and Path(name).suffix.lower() in exts:
                    (assets / name).write_bytes(z.read(member))

    count = sum(1 for f in assets.iterdir() if f.suffix.lower() in exts)
    print(f"[LION] {count} visuels extraits depuis ZIP → {assets}")
    return count

# ---- Visuals: option B (recherche internet) --------------------------------

def search_visuals(transcript: str, count: int, instructions: str) -> int:
    """Genere des requetes via AI, telecharge depuis Wikimedia Commons."""
    print(f"[LION] Generation de {count} requetes de recherche (AI)...")
    queries_raw = _ai([
        {"role": "system", "content": "Tu generes des requetes de recherche Wikimedia Commons. Une requete par ligne, sans numero."},
        {"role": "user", "content": f"Transcript : {transcript}\nInstructions : {instructions}\nGenere exactement {count} requetes d'images historiques pertinentes."},
    ], max_tokens=400, temperature=0.5)

    queries = [q.strip() for q in queries_raw.split("\n") if q.strip()][:count]
    assets = IN_DIR / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    for i, query in enumerate(queries):
        try:
            resp = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query", "generator": "search",
                    "gsrsearch": f"filetype:bitmap {query}", "gsrlimit": 1,
                    "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 800, "format": "json",
                },
                timeout=15,
            )
            for page in resp.json().get("query", {}).get("pages", {}).values():
                info = page.get("imageinfo", [{}])[0]
                url = info.get("thumburl") or info.get("url")
                if url:
                    img = requests.get(url, timeout=15)
                    if img.status_code == 200:
                        ext = ".jpg" if any(x in url.lower() for x in ("jpg", "jpeg")) else ".png"
                        (assets / f"visual_{i:02d}{ext}").write_bytes(img.content)
                        downloaded += 1
                        print(f"[LION]   visual_{i:02d} ← {query[:55]}")
                        break
        except Exception as e:
            print(f"[LION]   visual_{i:02d} echec : {e}")

    print(f"[LION] {downloaded}/{count} visuels telecharges")
    return downloaded

# ---- Main ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="CYPHER F01 LION")
    parser.add_argument("--audio",          required=True,
                        help="Chemin vers audio.mp3 / .wav")
    parser.add_argument("--format",         required=True, choices=["short", "long"],
                        help="Format video : short (9:16) ou long (16:9)")
    parser.add_argument("--style-carte",    required=True,
                        help="Style carte : osm | satellite | dark | terrain | custom:#hex")
    parser.add_argument("--visuals-zip",    default=None,
                        help="[Option A] Chemin vers un ZIP d'images")
    parser.add_argument("--visuals-search", default=None,
                        help="[Option B] Instructions pour chercher les visuels sur internet")
    parser.add_argument("--visual-count",   type=int, default=8,
                        help="Nombre de visuels souhaites (option B)")
    args = parser.parse_args()

    # Validation environnement
    if not AI_BASE or not AI_KEY:
        sys.exit("[LION] ERREUR : AI_GATEWAY_BASE_URL ou AI_GATEWAY_API_KEY manquant")

    audio_path = Path(args.audio)
    if not audio_path.exists():
        sys.exit(f"[LION] ERREUR : audio introuvable : {audio_path}")

    IN_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Copier audio dans F01_LION/IN/
    audio_dest = IN_DIR / audio_path.name
    if audio_path.resolve() != audio_dest.resolve():
        shutil.copy2(audio_path, audio_dest)
    print(f"[LION] Audio → {audio_dest.name}")

    # Gestion visuels
    visual_count = args.visual_count
    if args.visuals_zip:
        visual_count = handle_visuals_zip(Path(args.visuals_zip))
    elif args.visuals_search:
        visual_count = search_visuals("", visual_count, args.visuals_search)

    # Transcription Whisper
    print(f"[LION] Transcription Whisper ({audio_dest.name})...")
    whisper = transcribe_audio(audio_dest)
    print(f"[LION] OK — {len(whisper['words'])} mots, {whisper['duration']}s, langue={whisper['language']}")

    # Generation timing.json + config.json
    print("[LION] Generation timing.json + config.json via AI Gateway...")
    timing, config = generate_timing_and_config(
        whisper, args.format, args.style_carte, visual_count
    )

    # Sauvegarde
    timing_path = OUT_DIR / "timing.json"
    config_path = OUT_DIR / "config.json"
    timing_path.write_text(json.dumps(timing, indent=2, ensure_ascii=False))
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    print(f"[LION] timing.json → {timing_path}")
    print(f"[LION] config.json → {config_path}")

    # Mise a jour ledger
    run_id = f"CYP_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
    ledger = load_ledger()
    ledger.update({
        "run_id": run_id,
        "created_at": datetime.datetime.now().isoformat(),
        "status": "lion_done",
        "format": args.format,
        "style_carte": args.style_carte,
        "visual_count": visual_count,
        "audio_path": str(audio_dest),
        "whisper": {
            "transcript": whisper["transcript"],
            "duration": whisper["duration"],
            "language": whisper["language"],
            "word_count": len(whisper["words"]),
        },
        "timing_path": str(timing_path),
        "config_path": str(config_path),
    })
    save_ledger(ledger)

    # Rapport
    n_cam = len(timing.get("camera_events", []))
    n_vis = len(timing.get("visual_events", []))
    n_sfx = len(timing.get("sfx_events", []))
    n_pay = len(timing.get("country_events", []))

    print("\n" + "=" * 56)
    print(f"  LION DONE — {run_id}")
    print("=" * 56)
    print(f"  Format       : {args.format}  ({FORMATS[args.format]['label']})")
    print(f"  Duree        : {whisper['duration']}s")
    print(f"  Mots         : {len(whisper['words'])}")
    print(f"  Visuels      : {visual_count}")
    print(f"  Camera evts  : {n_cam}")
    print(f"  Visual evts  : {n_vis}")
    print(f"  Country evts : {n_pay}")
    print(f"  SFX evts     : {n_sfx}")
    print(f"  timing.json  : {timing_path}")
    print(f"  config.json  : {config_path}")
    print("=" * 56)
    print()
    print("[GATE 1] Valide F01_LION/OUT/timing.json + config.json")
    print("         Puis : python CYPHER_EXECUTEUR.py gate2")


if __name__ == "__main__":
    main()
