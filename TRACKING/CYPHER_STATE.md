# CYPHER — STATE

## Identité
- Repo : kioka8877-ux/CYPHER
- Moteur : ManimCE + ATLAS (kioka8877-ux/ATLAS)
- Oracle : Claude in sandbox (gates uniquement humain)
- Registre : cypher_ledger.json

## Frégates
| Frégate | Rôle | Runner | Statut |
|---|---|---|---|
| F01_LION | Orchestrateur / narrateur | Sandbox | ✅ |
| F02_CALIBAN | Traducteur dict→acier ManimCE + preview HTML | Sandbox | ✅ |
| F03_DEATHWING | Cristallisation headless (render lourd) | GH Actions | ✅ |
| F04_RAVENWING | Assembleur FFmpeg + interpolation géo-caméra | GH Actions | ✅ |
| F05_LUTHER | Effacement métadata, empreinte zéro | GH Actions | ✅ |

## Progression globale
- [x] Structure repo créée (3a91780)
- [x] Docs de suivi (58a5446)
- [x] CYPHER_STYLE.py (palette Dark Angels)
- [x] cypher_ledger.json schema
- [x] CYPHER_EXECUTEUR.py (orchestrateur gates, stubs)
- [x] F01_LION v1 (oracle AI Gateway — remplacé)
- [x] F01_LION v2 (Whisper transcription + timing.json + config.json — spec operateur complète)
- [x] CYPHER_EXECUTEUR.py cmd_start mis a jour (audio/format/style-carte/visuals)
- [ ] F02_CALIBAN v2 (preview HTML theme Imperivm — en cours)
- [x] F03_DEATHWING workflow + code (cyp_deathwing.py + deathwing_render.yml)
- [x] F04_RAVENWING workflow + code (cyp_ravenwing.py + ravenwing_assemble.yml)
- [x] F05_LUTHER workflow + code (cyp_luther.py + luther_purge.yml — port depuis CRUSADER)
- [x] Fix LION — requests + system-in-messages + haiku-4.5 (test Gate 1 OK : Constantinople 8 events)
- [ ] Test Gate 2 (CALIBAN) bout-en-bout

## Contraintes physiques
- Isolation subprocess stricte : ManimCE et manimgl ne cohabitent jamais dans le même processus
- CALIBAN appelle ATLAS, ne réimplémente pas la logique géo
- Internet accès confirmé (tuiles géo temps réel)
- Coût estimé : ~10k-15k tokens/production propre

## Palette Dark Angels
- Fond : #050B08
- Alerte : #B30006
- Territoire neutre : #1A2E25

## Réinstallation sandbox (Manim / ATLAS)
Voir kioka8877-ux/ATLAS — TRACKING/ATLAS_STATE.md pour la procédure complète Chemin B (extraction .deb manuelle).
