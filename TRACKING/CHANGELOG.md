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

## [0.5.0] — 2026-06-21
### Added
- F05_LUTHER : cyp_luther.py (vérifie release → trigger luther_purge.yml → print URL + cmd download)
- luther_purge.yml : FFmpeg stream copy + -map_metadata -1 + audit post-strip + normalisation timestamp + upload clean_final.mp4 sur release + artifact backup
- CYPHER_EXECUTEUR.py : cmd_close — appelle LUTHER + print commande download post-run
- Port direct depuis CRUSADER alpha/F05_LUTHER (strip éprouvé en production)

## Prochaine étape
- Test production bout-en-bout (start → gate2 → gate3 → gate4 → close)
