/**
 * WorldTitle.jsx — Titre animé avec alternance top/right
 *
 * Rotation stricte :
 *   index pair  → titre AU-DESSUS du visuel, tombe du dessus (drop-Y)
 *   index impair → titre À DROITE du visuel, glisse depuis la droite (slide-X)
 *
 * Fallback : si segment.world_title absent → premiers 4 mots du sous-titre.
 *
 * Paramètres depuis roadmap.style :
 *   world_title_visible  – true/false (défaut false)
 *   world_title_font     – police (défaut font_primary)
 *   world_title_size     – taille px (défaut 28)
 *   world_title_color    – couleur (défaut "#FFFFFF")
 *   world_title_speed    – frames d'animation (défaut 12 ≈ 400ms@30fps)
 *   world_title_gap      – espacement titre↔visuel en px (défaut 20)
 */
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export const WorldTitle = ({ segment, style, index = 0, worldW = 0, worldH = 0 }) => {
  const frame = useCurrentFrame();
  const visible = style.world_title_visible ?? false;

  // Fallback : premiers 4 mots du sous-titre si pas de world_title
  const title = segment.world_title
    || (segment.text_subtitles ? segment.text_subtitles.split(" ").slice(0, 4).join(" ") : null);

  if (!visible || !title) return null;

  const font = style.world_title_font ?? style.font_primary ?? "Cinzel";
  const size = style.world_title_size ?? 28;
  const color = style.world_title_color ?? "#FFFFFF";
  const speed = style.world_title_speed ?? 12;
  const gap = style.world_title_gap ?? 20;

  /* —— Animation locale (depuis le début du segment) —— */
  const segStart = segment.start_frame ?? 0;
  const localFrame = frame - segStart;

  const progress = interpolate(localFrame, [0, speed], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const eased = progress * progress * (3 - 2 * progress);

  /* —— Alternance : pair = au-dessus/drop, impair = à droite/slide —— */
  const isAbove = index % 2 === 0;

  let posStyle, transform;

  if (isAbove) {
    // Au-dessus du visuel, centré
    const dropY = interpolate(eased, [0, 1], [-40, 0]);
    posStyle = {
      top: -(gap + size + 4),
      left: 0,
      right: 0,
      textAlign: "center",
    };
    transform = `translateY(${dropY}px)`;
  } else {
    // À droite du visuel, centré verticalement
    const slideX = interpolate(eased, [0, 1], [50, 0]);
    posStyle = {
      left: worldW + gap,
      top: worldH / 2,
    };
    transform = `translateY(-50%) translateX(${slideX}px)`;
  }

  return (
    <div
      style={{
        position: "absolute",
        ...posStyle,
        transform,
        opacity: eased,
        fontFamily: `'${font}', Georgia, serif`,
        fontSize: size,
        color,
        textShadow: "0 2px 12px rgba(0,0,0,0.85), 0 0 4px rgba(0,0,0,0.5)",
        pointerEvents: "none",
        zIndex: 10,
        whiteSpace: "nowrap",
      }}
    >
      {title}
    </div>
  );
};
