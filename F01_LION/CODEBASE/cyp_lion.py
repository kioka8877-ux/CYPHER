"""
F01 LION — Orchestrateur / Oracle Sémantique
Reçoit le brief opérateur, génère script + spatial_events via Claude (AI Gateway).
Sauvegarde tout dans cypher_ledger.json.
"""
import argparse
import json
import os
import sys
import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
LEDGER_PATH = BASE / "cypher_ledger.json"

AI_BASE = os.environ.get("AI_GATEWAY_BASE_URL", "")
AI_KEY = os.environ.get("AI_GATEWAY_API_KEY", "")
MODEL = "anthropic/claude-sonnet-4.6"


def load_ledger():
    with open(LEDGER_PATH) as f:
        return json.load(f)


def save_ledger(data):
    with open(LEDGER_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def call_oracle(subject: str, duration: int, language: str, tone: str) -> dict:
    import urllib.request
    import urllib.error

    system_prompt = (
        "Tu es LION, oracle géopolitique. Tu génères des scripts de narration "
        "et des séquences spatiales précises pour des vidéos cartographiques. "
        "Réponds UNIQUEMENT en JSON valide, sans markdown, sans texte hors JSON."
    )

    user_prompt = f"""Génère un script de narration géopolitique et les événements spatiaux.

BRIEF :
- Sujet : {subject}
- Durée cible : {duration} secondes
- Langue : {language}
- Ton : {tone}

FORMAT JSON STRICT :
{{
  "script": "Texte complet voix off (~{duration // 2} mots)",
  "spatial_events": [
    {{
      "t_start": 0.0,
      "t_end": 8.0,
      "geo_focus": {{"lat": 48.85, "lon": 2.35, "zoom": 5}},
      "highlights": [{{"iso": "FR", "color": "#B30006", "opacity": 0.7}}],
      "overlays": []
    }}
  ]
}}

Produis 5 à 12 événements spatiaux couvrant toute la durée.
Codes ISO 3166-1 alpha-2 pour les pays."""

    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": user_prompt}],
        "system": system_prompt,
        "max_tokens": 4096,
        "temperature": 0.7
    }).encode()

    url = f"{AI_BASE}/api/v1/chat/completions"
    req = urllib.request.Request(
        url, data=payload,
        headers={"Authorization": f"Bearer {AI_KEY}", "Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"[LION] Erreur API {e.code}: {e.read().decode()[:300]}")
    except Exception as e:
        sys.exit(f"[LION] Erreur réseau: {e}")

    content = body["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        sys.exit(f"[LION] Réponse non-JSON: {e}\n{content[:500]}")


def validate_output(data: dict) -> bool:
    if "script" not in data or not data["script"].strip():
        print("[LION] ERREUR: champ 'script' manquant ou vide")
        return False
    if "spatial_events" not in data or not isinstance(data["spatial_events"], list):
        print("[LION] ERREUR: champ 'spatial_events' invalide")
        return False
    if len(data["spatial_events"]) < 2:
        print("[LION] AVERTISSEMENT: moins de 2 événements spatiaux")
    return True


def print_summary(data: dict, subject: str, duration: int):
    words = len(data["script"].split())
    n = len(data["spatial_events"])
    print("\n" + "=" * 60)
    print("  LION — RAPPORT")
    print("=" * 60)
    print(f"  Sujet       : {subject}")
    print(f"  Durée cible : {duration}s  |  Mots : {words}  |  Événements : {n}")
    print()
    print("  SCRIPT (extrait) :")
    print(f"  {data['script'][:280]}{'...' if len(data['script']) > 280 else ''}")
    print()
    print("  SPATIAL EVENTS :")
    for i, ev in enumerate(data["spatial_events"][:6]):
        gf = ev.get("geo_focus", {})
        hi = [h.get("iso", "?") for h in ev.get("highlights", [])]
        print(f"  [{i:02d}] {ev.get('t_start', 0):.1f}s–{ev.get('t_end', 0):.1f}s "
              f"| lat={gf.get('lat','?')} lon={gf.get('lon','?')} zoom={gf.get('zoom','?')} "
              f"| {hi}")
    if n > 6:
        print(f"  ... + {n - 6} événements supplémentaires")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="CYPHER F01 LION")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--duration", type=int, default=90)
    parser.add_argument("--language", default="fr")
    parser.add_argument("--tone", default="dramatique",
                        choices=["dramatique", "informatif", "cynique", "didactique"])
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    if not AI_BASE or not AI_KEY:
        sys.exit("[LION] AI_GATEWAY_BASE_URL ou AI_GATEWAY_API_KEY manquant")

    ledger = load_ledger()
    run_id = args.run_id or f"CYP_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
    ledger.update({
        "run_id": run_id,
        "created_at": datetime.datetime.now().isoformat(),
        "status": "lion_running"
    })
    ledger["narrative"].update({
        "subject": args.subject,
        "duration_seconds": args.duration,
        "language": args.language,
        "tone": args.tone
    })
    save_ledger(ledger)

    print(f"[LION] Run {run_id} — oracle en cours...")
    result = call_oracle(args.subject, args.duration, args.language, args.tone)

    if not validate_output(result):
        ledger["status"] = "lion_failed"
        save_ledger(ledger)
        sys.exit("[LION] Sortie invalide")

    ledger["narrative"]["script"] = result["script"]
    ledger["timeline_events"] = result["spatial_events"]
    ledger["spatial_events"]["geo_focus"] = [ev.get("geo_focus") for ev in result["spatial_events"]]
    ledger["spatial_events"]["highlights"] = [ev.get("highlights", []) for ev in result["spatial_events"]]
    ledger["spatial_events"]["overlays"] = [ev.get("overlays", []) for ev in result["spatial_events"]]
    ledger["status"] = "lion_done"
    save_ledger(ledger)

    out_dir = Path(__file__).parent.parent / "OUT"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "lion_output.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print_summary(result, args.subject, args.duration)
    print(f"\n[LION] Sauvegardé → ledger + F01_LION/OUT/lion_output.json")
    print(f"[LION] STATUS: lion_done | run_id: {run_id}")


if __name__ == "__main__":
    main()
