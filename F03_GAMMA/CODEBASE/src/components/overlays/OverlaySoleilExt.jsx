// overlays/OverlaySoleilExt.jsx — Rayons de soleil + lens flare
import React from "react";
import { AbsoluteFill, interpolate } from "remotion";

export function OverlaySoleilExt({ intensite, frame, fps }) {
  const cycle = fps * 4;
  const t = frame % cycle;

  // Pulsation lente des rayons
  const pulse = interpolate(t, [0, cycle * 0.5, cycle], [0.88, 1.0, 0.88], { extrapolateRight: "clamp" });
  const baseOpacity = [0, 0.25, 0.4, 0.6][intensite] || 0.4;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Rayonnement global chaud */}
      <div style={{
        position: "absolute", inset: 0,
        background: "radial-gradient(ellipse at 75% 8%, rgba(255, 230, 100, 0.45), rgba(255, 200, 60, 0.08) 55%, transparent 75%)",
        opacity: baseOpacity * pulse,
      }} />

      {/* Halo lens flare */}
      <div style={{
        position: "absolute",
        top: "-5%",
        right: "10%",
        width: "35%",
        height: "35%",
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(255, 255, 200, 0.35), transparent 65%)",
        opacity: baseOpacity * pulse * 0.7,
      }} />

      {/* Rayon diagonal */}
      <div style={{
        position: "absolute",
        top: 0, left: 0, right: 0, bottom: 0,
        background: "linear-gradient(135deg, rgba(255, 240, 100, 0.18) 0%, transparent 45%)",
        opacity: baseOpacity * pulse,
      }} />
    </AbsoluteFill>
  );
}
