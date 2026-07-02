/**
 * BetaMain.jsx — Composition principale CRUSADER Beta (v2.1 – sinusoidal camera)
 *
 * Passe l'intégralité de la timeline et du style au WorldScene sinusoïdal.
 * Sous-titres gérés par BetaSubtitle (indépendant des Sequences).
 */
import React from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import { Background } from "./components/Background";
import { WorldScene } from "./components/WorldScene";
import { BetaSubtitle } from "./components/BetaSubtitle";

export const BetaMain = ({ timing, roadmap }) => {
  return (
    <AbsoluteFill>
      <Background style={roadmap.style} />
      <WorldScene timeline={roadmap.timeline} style={roadmap.style} />
      <BetaSubtitle
        timeline={roadmap.timeline}
        style={roadmap.style}
        timing={timing}
      />
      <Audio src={staticFile("audio_clean.mp3")} />
    </AbsoluteFill>
  );
};
