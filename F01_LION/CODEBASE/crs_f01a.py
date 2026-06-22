"""
crs_f01a.py — Frégate F01-A CASTELLAN-AUDIO
=============================================
Analyse et traitement audio pré-transcription.
Détecte les silences via FFmpeg, propose un viewer interactif
pour décider de les conserver ou supprimer avant F01-B (Whisper).

Usage:
    python crs_f01a.py --input /path/to/IN/ --output /path/to/OUT/ [--port 5001]

IN  : audio_raw.mp3
OUT : audio_clean.mp3 + silence_map.json

Dépendances :
    flask >= 2.0
    ffmpeg (installé sur le système)
"""

import argparse
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

# ─── Constantes ───────────────────────────────────────────────────────────────

DEFAULT_PORT     = 5001
AUDIO_IN         = "audio_raw.mp3"
AUDIO_OUT        = "audio_clean.mp3"
SILENCE_MAP      = "silence_map.json"
VIEWER_FILENAME  = "crs_f01a_viewer.html"
WAVEFORM_SAMPLES = 300

# ─── FFmpeg helpers ───────────────────────────────────────────────────────────

def ffmpeg(*args):
    """Lance FFmpeg, retourne (stdout, stderr, returncode)."""
    cmd = ["ffmpeg", "-y"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def get_duration(audio_path: str) -> float:
    """Retourne la durée audio en secondes."""
    _, stderr, _ = ffmpeg("-i", audio_path, "-f", "null", "-")
    for line in stderr.splitlines():
        if "Duration:" in line:
            try:
                ts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = ts.split(":")
                return round(float(h) * 3600 + float(m) * 60 + float(s), 4)
            except Exception:
                pass
    return 0.0


def detect_silences(audio_path: str, threshold_db: float = -40.0, min_duration: float = 0.5) -> list:
    """Détecte les silences via FFmpeg silencedetect. Retourne liste [{start, end, duration}]."""
    _, stderr, _ = ffmpeg(
        "-i", audio_path,
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_duration}",
        "-f", "null", "-"
    )
    silences = []
    current_start = None
    for line in stderr.splitlines():
        if "silence_start" in line:
            try:
                current_start = float(line.split("silence_start:")[1].strip())
            except Exception:
                pass
        elif "silence_end" in line and current_start is not None:
            try:
                parts = line.split("silence_end:")[1].split("|")
                end = float(parts[0].strip())
                dur = float(parts[1].split(":")[1].strip()) if len(parts) > 1 else end - current_start
                silences.append({
                    "start":    round(current_start, 4),
                    "end":      round(end, 4),
                    "duration": round(dur, 4),
                })
                current_start = None
            except Exception:
                pass
    return silences


def get_waveform_peaks(audio_path: str, n_samples: int = WAVEFORM_SAMPLES) -> list:
    """Extrait les pics de la waveform via FFmpeg. Retourne liste de floats normalisés 0-1."""
    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as tmp:
        raw_path = tmp.name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-ac", "1", "-ar", "8000", "-f", "f32le", raw_path],
            capture_output=True
        )
        with open(raw_path, "rb") as f:
            data = f.read()
        if not data:
            return [0.0] * n_samples
        samples = struct.unpack(f"{len(data) // 4}f", data)
        chunk = max(len(samples) // n_samples, 1)
        peaks = []
        for i in range(n_samples):
            window = samples[i * chunk: i * chunk + chunk]
            peaks.append(round(float(max(abs(v) for v in window)), 4) if window else 0.0)
        max_peak = max(peaks) if peaks else 1.0
        if max_peak > 0:
            peaks = [round(p / max_peak, 4) for p in peaks]
        return peaks
    except Exception as e:
        print(f"[F01A][WAVEFORM] Erreur : {e}")
        return [0.0] * n_samples
    finally:
        if os.path.exists(raw_path):
            os.unlink(raw_path)


def remove_silences(input_path: str, output_path: str, threshold_db: float, min_duration: float):
    """Supprime les silences de l'audio via FFmpeg silenceremove."""
    _, stderr, rc = ffmpeg(
        "-i", input_path,
        "-af", (
            f"silenceremove=stop_periods=-1"
            f":stop_duration={min_duration}"
            f":stop_threshold={threshold_db}dB"
        ),
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path
    )
    if rc != 0:
        raise RuntimeError(f"FFmpeg silenceremove échoué :\n{stderr[-800:]}")


def copy_audio(input_path: str, output_path: str):
    """Copie l'audio sans modification (silences conservés)."""
    import shutil
    shutil.copy2(input_path, output_path)


# ─── Flask app ────────────────────────────────────────────────────────────────

def create_app(input_dir: str, output_dir: str, viewer_path: str):
    try:
        from flask import Flask, jsonify, request, send_file, abort
    except ImportError:
        print("[ERREUR] Flask non installé. Lancez : pip install flask")
        sys.exit(1)

    app = Flask(__name__)

    audio_in_path    = os.path.join(input_dir,  AUDIO_IN)
    audio_out_path   = os.path.join(output_dir, AUDIO_OUT)
    silence_map_path = os.path.join(output_dir, SILENCE_MAP)

    # ── Routes ─────────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        if not os.path.isfile(viewer_path):
            abort(404, description=f"Viewer introuvable : {viewer_path}")
        return send_file(viewer_path)

    @app.route("/api/status")
    def api_status():
        return jsonify({
            "frigate":          "F01A_CASTELLAN_AUDIO",
            "audio_in_ready":   os.path.isfile(audio_in_path),
            "audio_out_exists": os.path.isfile(audio_out_path),
            "audio_in_path":    audio_in_path,
            "audio_out_path":   audio_out_path,
        })

    @app.route("/api/waveform")
    def api_waveform():
        if not os.path.isfile(audio_in_path):
            return jsonify({"error": f"audio_raw.mp3 introuvable : {audio_in_path}"}), 404
        try:
            peaks    = get_waveform_peaks(audio_in_path)
            duration = get_duration(audio_in_path)
            return jsonify({"peaks": peaks, "samples": len(peaks), "duration": duration})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/analyze")
    def api_analyze():
        if not os.path.isfile(audio_in_path):
            return jsonify({"error": f"audio_raw.mp3 introuvable : {audio_in_path}"}), 404
        try:
            threshold_db  = float(request.args.get("threshold_db",  -40.0))
            min_duration  = float(request.args.get("min_duration",   0.5))
            duration      = get_duration(audio_in_path)
            silences      = detect_silences(audio_in_path, threshold_db, min_duration)
            silence_total = round(sum(s["duration"] for s in silences), 4)
            return jsonify({
                "silences":               silences,
                "silence_count":          len(silences),
                "silence_total_seconds":  silence_total,
                "original_duration":      duration,
                "duration_after_removal": round(max(duration - silence_total, 0.0), 4),
                "threshold_db":           threshold_db,
                "min_duration":           min_duration,
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/process", methods=["POST"])
    def api_process():
        if not os.path.isfile(audio_in_path):
            return jsonify({"error": f"audio_raw.mp3 introuvable : {audio_in_path}"}), 404

        payload         = request.get_json(force=True) or {}
        remove          = payload.get("remove_silences", False)
        threshold_db    = float(payload.get("threshold_db",  -40.0))
        min_dur         = float(payload.get("min_duration",   0.5))

        os.makedirs(output_dir, exist_ok=True)

        try:
            silences      = detect_silences(audio_in_path, threshold_db, min_dur)
            silence_total = round(sum(s["duration"] for s in silences), 4)
            duration_in   = get_duration(audio_in_path)

            # ── Écriture silence_map.json ───────────────────────────────────
            silence_map_data = {
                "mode":                  "removed" if remove else "preserved",
                "threshold_db":          threshold_db,
                "min_duration":          min_dur,
                "silences":              silences,
                "silence_count":         len(silences),
                "silence_total_seconds": silence_total,
                "original_duration":     duration_in,
            }
            with open(silence_map_path, "w", encoding="utf-8") as f:
                json.dump(silence_map_data, f, ensure_ascii=False, indent=2)

            # ── Traitement audio ────────────────────────────────────────────
            if remove:
                remove_silences(audio_in_path, audio_out_path, threshold_db, min_dur)
                mode_label = "SUPPRESSION"
            else:
                copy_audio(audio_in_path, audio_out_path)
                mode_label = "CONSERVATION"

            duration_out = get_duration(audio_out_path)

            print(f"[F01A] Mode {mode_label} — {len(silences)} silences — "
                  f"{duration_in:.1f}s → {duration_out:.1f}s → {audio_out_path}")

            return jsonify({
                "status":            "ok",
                "mode":              "removed" if remove else "preserved",
                "silence_count":     len(silences),
                "duration_in":       duration_in,
                "duration_out":      duration_out,
                "output_audio":      audio_out_path,
                "output_silence_map": silence_map_path,
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="F01-A CASTELLAN-AUDIO — Analyse & traitement audio")
    parser.add_argument("--input",  required=True, help="Chemin vers le dossier IN/  (contient audio_raw.mp3)")
    parser.add_argument("--output", required=True, help="Chemin vers le dossier OUT/ (recevra audio_clean.mp3)")
    parser.add_argument("--viewer", default=None,  help="Chemin vers crs_f01a_viewer.html")
    parser.add_argument("--port",   type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    viewer_path = args.viewer or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), VIEWER_FILENAME
    )

    print()
    print("═══════════════════════════════════════════════════")
    print("  F01-A CASTELLAN-AUDIO — Analyse pré-transcription")
    print("═══════════════════════════════════════════════════")
    print(f"  IN     : {args.input}")
    print(f"  OUT    : {args.output}")
    print(f"  Viewer : {viewer_path}")
    print(f"  Port   : {args.port}")
    print()

    audio_in = os.path.join(args.input, AUDIO_IN)
    if not os.path.isfile(audio_in):
        print(f"[ATTENTION] audio_raw.mp3 introuvable : {audio_in}")
        print("            Démarrage quand même — /api/status indiquera l'état.")

    if not os.path.isfile(viewer_path):
        print(f"[ERREUR] Viewer HTML introuvable : {viewer_path}")
        sys.exit(1)

    app = create_app(args.input, args.output, viewer_path)

    print(f"  Viewer disponible sur : http://localhost:{args.port}/")
    print("═══════════════════════════════════════════════════")
    print()

    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
