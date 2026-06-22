"""
F01 LION — Dialogue interactif bloquant avec l'opérateur.
Collecte les inputs pas à pas, transcrit l'audio (Whisper),
génère timing.json + config.json dans F01_LION/OUT/
"""

import os, sys, json, zipfile, pathlib

BASE    = pathlib.Path(__file__).resolve().parent.parent   # F01_LION/
IN_DIR  = BASE / "IN"
OUT_DIR = BASE / "OUT"
OUT_DIR.mkdir(parents=True, exist_ok=True)
IN_DIR.mkdir(parents=True, exist_ok=True)

LEDGER_PATH = pathlib.Path(__file__).resolve().parents[3] / "cypher_ledger.json"


# ── helpers ──────────────────────────────────────────────────────────────
def ask(prompt, choices=None, default=None):
    """Prompt bloquant avec validation."""
    while True:
        suffix = ""
        if choices:
            suffix = f" [{'/'.join(choices)}]"
        if default:
            suffix += f" (défaut: {default})"
        val = input(f"\n{prompt}{suffix} : ").strip()
        if not val and default:
            return default
        if choices and val not in choices:
            print(f"  ✗ Choisir parmi : {', '.join(choices)}")
            continue
        if val:
            return val
        print("  ✗ Réponse requise.")


def load_ledger():
    if LEDGER_PATH.exists():
        return json.loads(LEDGER_PATH.read_text())
    return {}


def save_ledger(data):
    LEDGER_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ── transcription Whisper ─────────────────────────────────────────────────
def transcribe(audio_path: pathlib.Path, fps: int = 30):
    print("\n[LION] Transcription Whisper en cours…")
    try:
        from faster_whisper import WhisperModel
        import ctranslate2
        try:
            ctranslate2.get_supported_compute_types("cuda")
            device, ctype = "cuda", "float16"
        except Exception:
            device, ctype = "cpu", "int8"

        model = WhisperModel("medium", device=device, compute_type=ctype)
        segments_gen, _ = model.transcribe(str(audio_path), word_timestamps=True)
        words = []
        for seg in segments_gen:
            for w in (seg.words or []):
                words.append({
                    "word":        w.word.strip(),
                    "start":       round(w.start, 3),
                    "end":         round(w.end,   3),
                    "frame_start": int(w.start * fps),
                    "frame_end":   int(w.end   * fps),
                })
        print(f"[LION] {len(words)} mots transcrits.")
        return words
    except ImportError:
        print("[LION] ✗ faster-whisper absent — pip install faster-whisper")
        sys.exit(1)


# ── segments ──────────────────────────────────────────────────────────────
def build_segments(words, fps=30):
    if not words:
        return []
    groups, cur = [], [words[0]]
    for w in words[1:]:
        if w["start"] - cur[-1]["end"] > 0.5:
            groups.append(cur); cur = [w]
        else:
            cur.append(w)
    groups.append(cur)

    result = []
    for i, g in enumerate(groups):
        result.append({
            "id":          i,
            "text":        " ".join(w["word"] for w in g).strip(),
            "start":       g[0]["start"],
            "end":         g[-1]["end"],
            "frame_start": g[0]["frame_start"],
            "frame_end":   g[-1]["frame_end"],
            "visual_file": None,
            "media_type":  "image",
            "sfx_trigger": i < 3 or i % 3 == 0,
        })
    return result


# ── visuels ZIP ───────────────────────────────────────────────────────────
def extract_visuals_zip(zip_path: pathlib.Path, dest: pathlib.Path):
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest)
    files = sorted([f for f in dest.rglob("*")
                    if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".mp4")])
    print(f"[LION] {len(files)} visuels extraits.")
    return files


def assign_visuals(segments, visual_files):
    if not visual_files:
        return segments
    for i, seg in enumerate(segments):
        vf  = visual_files[i % len(visual_files)]
        ext = vf.suffix.lower()
        seg["visual_file"] = vf.name
        seg["media_type"]  = ("gif" if ext == ".gif"
                               else "video" if ext in (".mp4", ".webm")
                               else "image")
    return segments


# ── main ──────────────────────────────────────────────────────────────────
def main():
    print("\n" + "═"*54)
    print("  F01 LION — Collecte des inputs opérateur")
    print("═"*54)

    ledger = load_ledger()

    # ── 1. Audio ─────────────────────────────────────────
    print("\n[1/5] FICHIER AUDIO")
    print(f"  → Déposez le fichier dans : {IN_DIR}")
    audio_name = ask("Nom ou chemin du fichier audio (.mp3 / .wav)")
    audio_path = pathlib.Path(audio_name)
    if not audio_path.is_absolute():
        audio_path = IN_DIR / audio_name
    if not audio_path.exists():
        print(f"  ✗ Introuvable : {audio_path}")
        sys.exit(1)
    print(f"  ✓ {audio_path.name}")

    # ── 2. Format ────────────────────────────────────────
    print("\n[2/5] FORMAT")
    fmt = ask("Format de la vidéo", choices=["short", "long"], default="short")
    width, height = (1080, 1920) if fmt == "short" else (1920, 1080)
    print(f"  ✓ {fmt}  {width}×{height}")

    # ── 3. Style de carte ─────────────────────────────────
    print("\n[3/5] STYLE DE CARTE")
    print("  Options : dark | light | satellite | terrain | military")
    map_style = ask("Style de carte", default="dark")

    # ── 4. Visuels ────────────────────────────────────────
    print("\n[4/5] VISUELS")
    print("  (A) Fournir un ZIP d'images")
    print("  (B) Instructions de recherche internet")
    print("  (C) Aucun visuel maintenant")
    visual_mode = ask("Mode visuels", choices=["A", "B", "C"], default="C")

    visual_files = []
    search_instr = ""
    visuals_dir  = OUT_DIR / "visuals"

    if visual_mode == "A":
        zip_name = ask("Nom ou chemin du fichier ZIP")
        zip_path = pathlib.Path(zip_name)
        if not zip_path.is_absolute():
            zip_path = IN_DIR / zip_name
        if not zip_path.exists():
            print(f"  ✗ ZIP introuvable : {zip_path}")
            sys.exit(1)
        visual_files = extract_visuals_zip(zip_path, visuals_dir)

    elif visual_mode == "B":
        search_instr = ask("Instructions de recherche (style, époque, type d'images…)")

    # ── 5. Sous-titres ────────────────────────────────────
    print("\n[5/5] OPTIONS SOUS-TITRES  (modifiables dans Gate 2)")
    font_family  = ask("Police principale", default="Cinzel")
    font_color   = ask("Couleur du texte (hex)", default="#FFFFFF")
    font_size    = ask("Taille du texte (px)", default="48")
    sub_pos      = ask("Position des sous-titres", choices=["bottom", "center"], default="bottom")
    sub_anim     = ask("Animation", choices=["slide", "fade", "none"], default="slide")
    visual_scale = ask("Taille des visuels (0.1 – 1.0)", default="1.0")

    # ── Transcription ─────────────────────────────────────
    fps   = 30
    words = transcribe(audio_path, fps)
    total_frames = (max(w["frame_end"] for w in words) + fps) if words else fps

    # ── Segments ──────────────────────────────────────────
    segments = build_segments(words, fps)
    print(f"[LION] {len(segments)} segments générés.")

    if visual_files:
        segments = assign_visuals(segments, visual_files)

    # ── timing.json ───────────────────────────────────────
    timing = {
        "meta": {
            "audio_file":   audio_path.name,
            "duration":     round(words[-1]["end"] if words else 0, 2),
            "total_frames": total_frames,
            "fps":          fps,
            "format":       fmt,
            "width":        width,
            "height":       height,
        },
        "words":    words,
        "segments": segments,
    }

    # ── config.json ───────────────────────────────────────
    config = {
        "format":       fmt,
        "width":        width,
        "height":       height,
        "map_style":    map_style,
        "visual_mode":  visual_mode,
        "search_instr": search_instr,
        "display": {
            "font_family":  font_family,
            "font_color":   font_color,
            "font_size":    int(font_size),
            "position":     sub_pos,
            "animation":    sub_anim,
            "visual_scale": float(visual_scale),
        },
        "visuals_dir": str(visuals_dir) if visual_files else None,
    }

    # ── écriture ──────────────────────────────────────────
    timing_path = OUT_DIR / "timing.json"
    config_path = OUT_DIR / "config.json"
    timing_path.write_text(json.dumps(timing, indent=2, ensure_ascii=False))
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))

    # ── ledger ────────────────────────────────────────────
    ledger.update({
        "lion_done":   True,
        "timing_path": str(timing_path),
        "config_path": str(config_path),
        "format":      fmt,
        "map_style":   map_style,
    })
    save_ledger(ledger)

    # ── rapport ───────────────────────────────────────────
    print("\n" + "═"*54)
    print("  GATE 1 — RAPPORT LION  ✓")
    print("═"*54)
    print(f"  Audio         : {audio_path.name}")
    print(f"  Format        : {fmt}  ({width}×{height})")
    print(f"  Carte         : {map_style}")
    print(f"  Mots transcrits: {len(words)}")
    print(f"  Segments      : {len(segments)}")
    print(f"  Frames totales: {total_frames}")
    print(f"  → {timing_path}")
    print(f"  → {config_path}")
    if visual_files:
        print(f"  Visuels       : {len(visual_files)} fichiers")
    elif visual_mode == "B":
        print(f"  Visuels       : recherche prévue dans Gate 2")
    print("\n  Vérifiez timing.json + config.json puis dites GO pour Gate 2.")
    print("═"*54 + "\n")


if __name__ == "__main__":
    main()
