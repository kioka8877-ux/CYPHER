/**
 * TacticalArrow.jsx — Marque tracée pendant le vol (spec 22/06)
 *
 * Spring réservé UNIQUEMENT à la marque :
 *   - Ligne Bézier quadratique centre → coin teaser N+1
 *   - Dessinée progressivement via spring (mass 0.4 / stiffness 210 / damping 14)
 *   - strokeDashoffset animé par le spring → effet "tracé à la main"
 *   - Fade out quand la caméra commence à voyager (transition)
 *   - Pointe de flèche rouge #FF1A1A
 */
import React from "react";
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const SPRING_CFG = { mass: 0.4, stiffness: 210, damping: 14 };
const STROKE_COLOR = "#FF1A1A";
const STROKE_W = 4;
const PATH_LEN = 1200; // surestimé volontairement — dasharray le clamp

export const TacticalArrow = ({
  fromX,
  fromY,
  toX,
  toY,
  transStart,
  transFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  /* ── Spring dessine la marque (stable phase) ── */
  const draw = spring({ frame, fps, config: SPRING_CFG });

  /* ── Fade out pendant le vol caméra ── */
  const tf = transFrames || 12;
  const ts = transStart != null ? transStart : Infinity;
  const fade = interpolate(
    frame,
    [ts, ts + Math.floor(tf * 0.4)],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  if (fade <= 0) return null;

  /* ── Courbe Bézier quadratique — légère sinusoïde ── */
  const cpX = fromX + (toX - fromX) * 0.5;
  const cpY = toY; // contrôle tiré vers la hauteur cible
  const d = `M ${fromX} ${fromY} Q ${cpX} ${cpY} ${toX} ${toY}`;

  return (
    <svg
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        overflow: "visible",
        pointerEvents: "none",
        opacity: fade,
      }}
    >
      <defs>
        <marker
          id="mark-head"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill={STROKE_COLOR} />
        </marker>
      </defs>
      <path
        d={d}
        fill="none"
        stroke={STROKE_COLOR}
        strokeWidth={STROKE_W}
        strokeLinecap="round"
        strokeDasharray={PATH_LEN}
        strokeDashoffset={PATH_LEN * (1 - draw)}
        markerEnd="url(#mark-head)"
      />
    </svg>
  );
};
