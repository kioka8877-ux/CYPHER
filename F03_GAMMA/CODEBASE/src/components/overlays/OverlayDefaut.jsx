// overlays/OverlayDefaut.jsx — Grain cinématique + vignette (fallback universel)
import React from "react";
import { AbsoluteFill } from "remotion";

export function OverlayDefaut({ intensite, frame }) {
  const lv = intensite / 3;

  // Grain — seed varie chaque frame pour simuler le bruit pellicule
  const seed = (frame * 7 + 13) % 1000;
  const grainOpacity = (0.04 + lv * 0.08).toFixed(3);

  // Vignette — visible dès frame 1, intensité selon le niveau
  const vigOpacity = (0.25 + lv * 0.30).toFixed(3);

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Grain cinématique via SVG feTurbulence */}
      <svg
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          opacity: grainOpacity,
        }}
      >
        <filter id="crs-grain">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.65"
            numOctaves="3"
            seed={seed}
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#crs-grain)" />
      </svg>

      {/* Vignette radiale — présente dès frame 1 */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at 50% 50%, transparent 45%, rgba(0,0,0,${vigOpacity}) 100%)`,
        }}
      />
    </AbsoluteFill>
  );
}
