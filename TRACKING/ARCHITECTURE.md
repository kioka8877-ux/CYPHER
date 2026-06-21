# ARCHITECTURE — CYPHER

## Vue d'ensemble
CYPHER est un pipeline de production vidéo géopolitique animée.
Moteur : ManimCE via ATLAS (bibliothèque géo).
L'opérateur humain n'intervient qu'aux gates. Claude opère le reste de manière autonome dans le sandbox.

## Pipeline

```
Opérateur → [GATE 1] → LION → CALIBAN → [GATE 2 preview] → DEATHWING → RAVENWING → [GATE 3] → LUTHER → artefact final
```

### F01_LION (sandbox)
- Reçoit : brief opérateur (sujet, durée, langue, ton)
- Produit : script narratif + spatial_events dans cypher_ledger.json
- Oracle : Claude IS l'oracle (pas d'appel API externe)

### F02_CALIBAN (sandbox)
- Reçoit : cypher_ledger.json complet
- Produit : acier ManimCE (.py) + preview HTML (carte stylée, séquence sous-titrée)
- Règle : appelle ATLAS, ne réimplémente jamais la logique géo
- Gate 2 : opérateur valide le preview avant de déclencher DEATHWING

### F03_DEATHWING (GH Actions)
- Reçoit : acier ManimCE + assets
- Produit : segments vidéo bruts
- Contrainte : processus isolé (ManimCE uniquement, jamais manimgl)

### F04_RAVENWING (GH Actions)
- Reçoit : segments vidéo + timeline_clock (whisper nodes) + overlays
- Produit : vidéo finale synchronisée

### F05_LUTHER (GH Actions)
- Reçoit : vidéo finale
- Produit : artefact propre (zéro métadata, timestamp normalisé)
- Lore : il efface ses traces, toujours

## Schéma cypher_ledger.json
```json
{
  "run_id": "CYP_YYYYMMDD_HHMM",
  "timeline_clock": "whisper_alignment_nodes",
  "spatial_events": {
    "geo_focus": "lat_lon_zoom_sequence",
    "highlights": "territories_color_opacity",
    "overlays": "icon_path_or_vector_anchors"
  },
  "gh_runs": {
    "deathwing": null,
    "ravenwing": null,
    "luther": null
  }
}
```

## Isolation subprocess (contrainte physique)
ManimCE (CYPHER) et manimgl (ANGRON-V2) sont deux dialectes incompatibles.
Ils ne peuvent pas cohabiter dans le même processus Python.
CALIBAN appelle ATLAS via subprocess isolé — jamais via import direct.

## Palette Dark Angels
- Fond : #050B08
- Alerte : #B30006
- Territoire neutre : à définir
