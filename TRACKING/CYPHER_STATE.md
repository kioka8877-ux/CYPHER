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
| F05_LUTHER | Effacement métadata, empreinte zéro | GH Actions | STUB |

## Progression globale
- [x] Structure repo créée (3a91780)
- [x] Docs de suivi (58a5446)
- [x] CYPHER_STYLE.py (palette Dark Angels)
- [x] cypher_ledger.json schema
- [x] CYPHER_EXECUTEUR.py (orchestrateur gates, stubs)
- [x] F01_LION code (cyp_lion.py — oracle AI Gateway + ledger)
- [x] F02_CALIBAN code (cyp_caliban.py — acier.py generator + preview HTML dark-theme)
- [x] F03_DEATHWING workflow + code (cyp_deathwing.py + deathwing_render.yml)
- [x] F04_RAVENWING workflow + code (cyp_ravenwing.py + ravenwing_assemble.yml)
- [ ] F05_LUTHER workflow + code
- [ ] Test production bout-en-bout

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
