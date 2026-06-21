# CHANGELOG — CYPHER

## [Unreleased]

## [0.1.0] — 2026-06-21
### Added
- Structure repo complète : 5 frégates (LION/CALIBAN/DEATHWING/RAVENWING/LUTHER)
- SHARED/IN/sfx, SHARED/OUT, STYLE/, TRACKING/
- Stubs : cyp_*.py, CYPHER_STYLE.py, cypher_ledger.json, CYPHER_EXECUTEUR.py
- Stubs workflows GH Actions : deathwing_render.yml, ravenwing_assemble.yml, luther_purge.yml
- Docs de suivi : CYPHER_STATE.md, CHANGELOG.md, ARCHITECTURE.md

## [0.4.0] — 2026-06-21
### Added
- F03_DEATHWING : cyp_deathwing.py (upload acier.py GH Release → trigger workflow → print URL)
- deathwing_render.yml : apt-get cairo/pango/ffmpeg + pip manim==0.20.1 + ATLAS from GitHub + render headless + upload artifact + upload release
- CYPHER_EXECUTEUR.py : cmd_gate3 fonctionnel (appelle cyp_deathwing.py)

## Prochaine étape
- F04_RAVENWING : workflow + cyp_ravenwing.py (assemblage FFmpeg final)
