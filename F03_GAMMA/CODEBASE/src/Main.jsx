// src/Main.jsx — F03 SIGISMUND
// Composition principale : Audio + Background + Séquences par segment.
//
// ── Gestion des silences ────────────────────────────────────────────────────
// Chaque Sequence s'étend jusqu'au début de la suivante (extendedEnd).
// Pendant un silence audio, aucun nouveau segment ne démarre : le dernier
// segment actif reste affiché (freeze du dernier visuel) jusqu'au segment
// suivant ou jusqu'à la fin de la vidéo.
//
// Ce comportement est TOUJOURS actif, que F01-A ait conservé ou supprimé
// les silences — si des silences subsistent dans l'audio, F03 les gère
// visuellement sans blanc ni fond nu.
// ─────────────────────────────────────────────────────────────────────────────

import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { Background } from "./components/Background";
import { Scene } from "./components/Scene";

export const Main = ({ timing, roadmap }) => {
  const { durationInFrames } = useVideoConfig();

  return (
    <AbsoluteFill>
      {/* Fond permanent (couleur + grain + vignette) */}
      <Background style={roadmap.style} />

      {/* Séquences — une par segment de roadmap.
          extendedEnd = début du segment suivant (ou fin totale si dernier).
          Garantit : aucune frame sans visuel, même pendant les silences. */}
      {roadmap.timeline.map((seg, idx) => {
        const nextSeg     = roadmap.timeline[idx + 1];
        const extendedEnd = nextSeg ? nextSeg.start_frame : durationInFrames;
        const dur         = extendedEnd - seg.start_frame;
        if (dur <= 0) return null;

        // Correspondance 1-à-1 : timeline[idx] ↔ timing.segments[idx]
        // Find timing segments by time range overlap (gamma chunks don't map 1:1 to timing segments)
        const segStart = seg.start !== undefined ? seg.start : (seg.start_frame / (timing?.meta?.fps || 30));
        const segEnd = seg.end !== undefined ? seg.end : (seg.end_frame / (timing?.meta?.fps || 30));
        const overlappingTiming = timing?.segments?.filter(ts => {
          const tsStart = ts.start !== undefined ? ts.start : 0;
          const tsEnd = ts.end !== undefined ? ts.end : 0;
          return tsStart < segEnd && tsEnd > segStart;
        }) || [];
        const timingSeg = overlappingTiming.length > 0 ? {
          ...overlappingTiming[0],
          words: overlappingTiming.flatMap(ts => ts.words || [])
        } : null;

        return (
          <Sequence
            key={seg.id}
            from={seg.start_frame}
            durationInFrames={dur}
            layout="none"
          >
            <Scene
              segment={seg}
              timingSeg={timingSeg}
              style={roadmap.style}
              durationInFrames={dur}
            />
          </Sequence>
        );
      })}

      {/* Piste audio */}
      {timing && <Audio src={staticFile("audio_clean.mp3")} />}
    </AbsoluteFill>
  );
};
