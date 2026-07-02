// overlays/OverlayPluieExt.jsx — Pluie plein écran extérieur
import React from "react";
import { AbsoluteFill, interpolate } from "remotion";

const DROPS = Array.from({ length: 55 }, (_, i) => ({
  id: i,
  x:   (i * 37 + i * i * 3) % 100,
  delay: (i * 17) % 100,
  speed: 0.6 + (i % 5) * 0.12,
  opacity: 0.3 + (i % 4) * 0.12,
  width: 1 + (i % 3) * 0.5,
  height: 10 + (i % 6) * 5,
}));

export function OverlayPluieExt({ intensite, frame, fps }) {
  const baseOpacity = [0, 0.5, 0.75, 1.0][intensite] || 0.75;
  const cycleFps = fps * 1.2;

  // Flash éclair pour intensite 3
  const lightningOpacity = intensite === 3
    ? interpolate(frame % (fps * 4), [0, 2, 4, fps * 4], [0, 0.6, 0, 0], { extrapolateRight: "clamp" })
    : 0;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Brouillard ambiant */}
      <div style={{
        position: "absolute", inset: 0,
        background: "linear-gradient(to bottom, rgba(80, 100, 130, 0.18), rgba(60, 80, 110, 0.08))",
        opacity: baseOpacity,
      }} />

      {/* Gouttes */}
      {DROPS.map(drop => {
        const t = ((frame * drop.speed + drop.delay) % cycleFps) / cycleFps;
        const y = interpolate(t, [0, 1], [-5, 105]);
        return (
          <div key={drop.id} style={{
            position: "absolute",
            left: `${drop.x}%`,
            top: `${y}%`,
            width: `${drop.width}px`,
            height: `${drop.height}px`,
            background: "rgba(180, 210, 240, 0.7)",
            borderRadius: "1px",
            transform: "rotate(-12deg)",
            opacity: drop.opacity * baseOpacity,
          }} />
        );
      })}

      {/* Flash éclair */}
      {lightningOpacity > 0 && (
        <div style={{
          position: "absolute", inset: 0,
          background: "rgba(220, 240, 255, 1)",
          opacity: lightningOpacity,
        }} />
      )}
    </AbsoluteFill>
  );
}
