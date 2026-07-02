/**
 * WorldScene.jsx — Sinusoidal Camera (v2.1 – spec beta-test3)
 *
 * Tous les worlds positionnés sur une courbe sinusoïdale.
 * La caméra voyage le long de cette courbe.
 *
 * Paramètres configurables via roadmap.style :
 *   world_scale          – taille du visuel actif (0.0–1.0, défaut 0.70)
 *   world_next_scale     – taille des visuels adjacents (défaut world_scale×0.5)
 *   world_opacity        – opacité du visuel actif (défaut 1.0)
 *   world_next_opacity   – opacité des visuels adjacents (défaut 0.3)
 *   camera_amplitude     – amplitude verticale sinusoïde (px, défaut 200)
 *   camera_spacing       – espacement horizontal entre worlds (px, défaut 1500)
 */
import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { WorldNode } from "./WorldNode";
import { WorldTitle } from "./WorldTitle";

const BEZIER_EASE = Easing.bezier(0.42, 0, 0.58, 1);

export const WorldScene = ({ timeline, style }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  /* ── Style params avec défauts ── */
  const worldScale = style.world_scale ?? 0.70;
  const worldNextScale = style.world_next_scale ?? worldScale * 0.5;
  const worldOpacity = style.world_opacity ?? 1.0;
  const worldNextOpacity = style.world_next_opacity ?? 0.3;
  const camAmplitude = style.camera_amplitude ?? 200;
  const camSpacing = style.camera_spacing ?? 1500;

  /* ── Position de chaque world sur la sinusoïde ── */
  const worldPositions = timeline.map((_, i) => ({
    x: i * camSpacing,
    y: camAmplitude * Math.cos(i * Math.PI),
  }));

  /* ── Trouver le segment actif ── */
  let segIdx = 0;
  for (let i = timeline.length - 1; i >= 0; i--) {
    if (frame >= timeline[i].start_frame) {
      segIdx = i;
      break;
    }
  }

  const seg = timeline[segIdx];
  const nextSeg = timeline[segIdx + 1] || null;
  const segEnd = nextSeg ? nextSeg.start_frame : durationInFrames;
  const tf = seg.trans_frames || 12;
  const transStart = segEnd - tf;

  /* ── Camera progress (index flottant le long de la courbe) ── */
  let cameraProgress = segIdx;

  if (frame >= transStart && nextSeg) {
    const rawT = interpolate(
      frame,
      [transStart, segEnd],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );
    cameraProgress = segIdx + BEZIER_EASE(rawT);
  }

  /* ── Position caméra sur la sinusoïde ── */
  const cameraX = cameraProgress * camSpacing;
  const cameraY = camAmplitude * Math.cos(cameraProgress * Math.PI);

  /* ── Translation du container ── */
  const translateX = width / 2 - cameraX;
  const translateY = height / 2 - cameraY;

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          transform: `translate(${translateX}px, ${translateY}px)`,
          willChange: "transform",
        }}
      >
        {timeline.map((s, i) => {
          const pos = worldPositions[i];
          const mediaType = s.media_type || "image";

          /* ── Scale et opacité interpolés selon la distance ── */
          const distance = Math.abs(i - cameraProgress);
          const t = Math.min(distance, 1); // 0 = current, 1 = adjacent+

          const thisScale = worldScale + (worldNextScale - worldScale) * t;
          const thisOpacity =
            (worldOpacity + (worldNextOpacity - worldOpacity) * t) *
            Math.max(0, Math.min(1, 1.5 - distance)); // fade out distant

          const wW = width * thisScale;
          const wH = height * thisScale;

          if (thisOpacity <= 0) return null; // skip invisible worlds

          return (
            <div
              key={s.id}
              style={{
                position: "absolute",
                left: pos.x - wW / 2,
                top: pos.y - wH / 2,
                width: wW,
                height: wH,
                opacity: thisOpacity,
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  borderRadius: 8,
                  overflow: "hidden",
                  boxShadow:
                    thisOpacity > 0.3
                      ? "0 4px 24px rgba(0,0,0,0.5)"
                      : "none",
                }}
              >
                <WorldNode imageFile={s.image_file} mediaType={mediaType} />
              </div>
              <WorldTitle segment={s} style={style} index={i} worldW={wW} worldH={wH} />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
