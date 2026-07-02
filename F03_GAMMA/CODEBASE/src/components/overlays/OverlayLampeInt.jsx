// overlays/OverlayLampeInt.jsx — Lueur ambre pulsante (lampe / bougie)
import React from "react";
import { AbsoluteFill, interpolate } from "remotion";

export function OverlayLampeInt({ intensite, frame, fps }) {
  const cycle = fps * 2.5;
  const t = frame % cycle;

  // Pulsation douce sinusoidale simulée
  const pulse = interpolate(t, [0, cycle * 0.5, cycle], [0.85, 1.0, 0.85], { extrapolateRight: "clamp" });

  const baseOpacity = [0, 0.3, 0.45, 0.62][intensite] || 0.45;
  const opacity = baseOpacity * pulse;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Lueur radiale ambre bas-gauche */}
      <div style={{
        position: "absolute",
        bottom: "8%",
        left: "5%",
        width: "50%",
        height: "55%",
        background: "radial-gradient(ellipse at 30% 80%, rgba(255, 180, 50, 0.55), rgba(255, 140, 20, 0.15) 50%, transparent 75%)",
        opacity,
        mixBlendMode: "screen",
      }} />
    </AbsoluteFill>
  );
}
