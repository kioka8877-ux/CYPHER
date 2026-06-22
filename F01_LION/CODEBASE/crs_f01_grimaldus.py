"""
crs_f01_grimaldus.py — Frégate F01 GRIMALDUS
=============================================
Transcription audio via faster-whisper (local, gratuit).
Produit timing.json avec timestamps mot-par-mot et détection des mots forts.

Usage:
    python crs_f01_grimaldus.py --input /path/to/IN/ --output /path/to/OUT/ [--fps 30] [--model medium]

Dépendances (installées dans le notebook) :
    faster-whisper >= 1.0.0
"""

import argparse
import json
import os
import sys

# ─── Constantes ───────────────────────────────────────────────────────────────

DEFAULT_FPS    = 30
DEFAULT_MODEL  = "medium"
AUDIO_FILENAME = "audio_clean.mp3"
OUTPUT_FILENAME = "timing.json"

# Mots de liaison / stopwords français à NE PAS marquer comme forts
FR_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
    "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
    "et", "ou", "mais", "donc", "or", "ni", "car",
    "que", "qui", "quoi", "dont", "où",
    "à", "au", "aux", "en", "sur", "sous", "dans", "par", "pour",
    "avec", "sans", "entre", "vers", "chez", "dès",
    "est", "sont", "était", "ont", "a", "ai", "as",
    "ce", "cet", "cette", "ces", "mon", "ton", "son", "ma", "ta", "sa",
    "se", "si", "ne", "pas", "plus", "très", "bien", "aussi",
    "c", "j", "m", "n", "s", "t", "y",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def to_frames(seconds: float, fps: int) -> int:
    return round(seconds * fps)

def is_strong_word(word: str, duration: float, avg_duration: float) -> bool:
    """
    Détecte si un mot est 'fort' (doit être mis en valeur dans les sous-titres).
    Stratégies combinées :
      1. Le mot est entre crochets [mot] dans le texte (balisage opérateur)
      2. Le mot est en MAJUSCULES dans la transcription
      3. Le mot est significativement plus long que la moyenne (1.8x)
      4. Le mot a >= 7 caractères ET n'est pas un stopword
    """
    clean = word.strip("[].,!?;:\"'«»…-").lower()

    # Stratégie 1 : balisage explicite [mot]
    if word.startswith("[") and word.endswith("]"):
        return True

    # Stratégie 2 : MAJUSCULES
    if word.isupper() and len(word) > 1:
        return True

    # Stratégie 3 : durée exceptionnelle
    if avg_duration > 0 and duration > avg_duration * 1.8:
        return True

    # Stratégie 4 : mot long non-stopword
    if len(clean) >= 7 and clean not in FR_STOPWORDS:
        return True

    return False

# ─── Transcription ────────────────────────────────────────────────────────────

def transcribe(audio_path: str, model_size: str, fps: int) -> dict:
    """Lance faster-whisper et retourne le timing.json structuré."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[ERREUR] faster-whisper non installé. Lancez : pip install faster-whisper")
        sys.exit(1)

    print(f"[GRIMALDUS] Chargement du modèle Whisper '{model_size}'...")
    import ctranslate2
    device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    print(f"[GRIMALDUS] Device : {device} / compute_type : {compute_type}")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    print(f"[GRIMALDUS] Transcription de : {audio_path}")
    segments_iter, info = model.transcribe(
        audio_path,
        language=None,           # Auto-détection de la langue
        word_timestamps=True,    # OBLIGATOIRE pour le timing mot par mot
        vad_filter=True,         # Filtre Voice Activity Detection
        vad_parameters=dict(min_silence_duration_ms=300),
    )

    detected_lang = info.language
    duration_sec  = info.duration
    total_frames  = to_frames(duration_sec, fps)

    print(f"[GRIMALDUS] Langue détectée : {detected_lang} (confiance : {info.language_probability:.2%})")
    print(f"[GRIMALDUS] Durée audio : {duration_sec:.2f}s = {total_frames} frames @ {fps}fps")

    # ─── Collecte des segments et mots ─────────────────────────────────────
    all_segments = []
    all_words    = []

    for seg in segments_iter:
        seg_words = []
        if seg.words:
            for w in seg.words:
                seg_words.append({
                    "word":        w.word.strip(),
                    "start":       round(w.start, 4),
                    "end":         round(w.end, 4),
                    "probability": round(w.probability, 4),
                })

        all_segments.append({
            "id":          len(all_segments),
            "text":        seg.text.strip(),
            "start":       round(seg.start, 4),
            "end":         round(seg.end, 4),
            "start_frame": to_frames(seg.start, fps),
            "end_frame":   to_frames(seg.end, fps),
            "words":       seg_words,
        })

        all_words.extend(seg_words)

    # ─── Calcul durée moyenne des mots (pour détection mots forts) ─────────
    durations = [w["end"] - w["start"] for w in all_words if w["end"] > w["start"]]
    avg_duration = sum(durations) / len(durations) if durations else 0.0

    # ─── Enrichissement : frames + is_strong ───────────────────────────────
    enriched_words = []
    for w in all_words:
        dur = w["end"] - w["start"]
        strong = is_strong_word(w["word"], dur, avg_duration)
        enriched_words.append({
            "word":        w["word"],
            "start":       w["start"],
            "end":         w["end"],
            "start_frame": to_frames(w["start"], fps),
            "end_frame":   to_frames(w["end"], fps),
            "probability": w["probability"],
            "is_strong":   strong,
        })

    # ─── Idem pour les mots dans les segments ──────────────────────────────
    for seg in all_segments:
        enriched_seg_words = []
        for w in seg["words"]:
            dur = w["end"] - w["start"]
            strong = is_strong_word(w["word"], dur, avg_duration)
            enriched_seg_words.append({
                "word":        w["word"],
                "start":       w["start"],
                "end":         w["end"],
                "start_frame": to_frames(w["start"], fps),
                "end_frame":   to_frames(w["end"], fps),
                "probability": w["probability"],
                "is_strong":   strong,
            })
        seg["words"] = enriched_seg_words

    strong_count = sum(1 for w in enriched_words if w["is_strong"])
    print(f"[GRIMALDUS] {len(enriched_words)} mots transcrits, {strong_count} mots forts détectés.")

    return {
        "meta": {
            "fps":              fps,
            "duration_seconds": round(duration_sec, 4),
            "total_frames":     total_frames,
            "audio_path":       audio_path,
            "model":            model_size,
            "language":         detected_lang,
            "language_probability": round(info.language_probability, 4),
            "word_count":       len(enriched_words),
            "strong_word_count": strong_count,
        },
        "words":    enriched_words,
        "segments": all_segments,
    }

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="F01 GRIMALDUS — Transcription audio")
    parser.add_argument("--input",  required=True, help="Chemin vers le dossier IN/")
    parser.add_argument("--output", required=True, help="Chemin vers le dossier OUT/")
    parser.add_argument("--fps",    type=int, default=DEFAULT_FPS)
    parser.add_argument("--model",  default=DEFAULT_MODEL,
                        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"])
    args = parser.parse_args()

    audio_path  = os.path.join(args.input, AUDIO_FILENAME)
    output_path = os.path.join(args.output, OUTPUT_FILENAME)

    # ─── Validation des entrées ─────────────────────────────────────────────
    if not os.path.isfile(audio_path):
        print(f"[ERREUR] Fichier audio introuvable : {audio_path}")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)

    print()
    print("═══════════════════════════════════════════")
    print("  F01 GRIMALDUS — Transcription en cours")
    print("═══════════════════════════════════════════")

    # ─── Transcription ──────────────────────────────────────────────────────
    timing = transcribe(audio_path, args.model, args.fps)

    # ─── Écriture du JSON ───────────────────────────────────────────────────
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(timing, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"[GRIMALDUS] timing.json écrit → {output_path} ({size_kb:.1f} KB)")
    print()
    print("═══════════════════════════════════════════")
    print("  GRIMALDUS — MISSION ACCOMPLIE")
    print("═══════════════════════════════════════════")
    print()

if __name__ == "__main__":
    main()
