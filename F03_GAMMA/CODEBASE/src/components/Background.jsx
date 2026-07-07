// src/components/Background.jsx — F03 SIGISMUND v3
// Fond permanent : couleur papier + grain animé + vignette.
//
// ── Polices locales ──────────────────────────────────────────────────────────
// PLUS de Google Fonts. PLUS de delayRender. PLUS d'appel réseau.
// Les fichiers .woff2 sont embarqués dans l'image Docker (/crusader-fonts/)
// et copiés dans public/fonts/ avant chaque rendu.
// Le CSS @font-face ci-dessous est synchrone et deterministe.
//
// Polices disponibles :
//   Cinzel, Playfair Display, Lato, Oswald, Roboto Slab, Inter
//   Arial / Arial Black (système — MS Core Fonts)
//   Helvetica / Nimbus Sans L (système — fonts-urw-base35)
// ─────────────────────────────────────────────────────────────────────────────

import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from "remotion";

// CSS @font-face : référence les woff2 depuis public/fonts/ (servi par Remotion)
// Syntaxe url('./fonts/...') → résolu par le serveur statique Remotion
// = http://localhost:PORT/fonts/... → public/fonts/...
const FONT_FACES = `
  /* Cinzel — titres & accents stylistiques */
  @font-face {
    font-family: 'Cinzel';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Cinzel-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Cinzel';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Cinzel-Bold.woff2') format('woff2');
  }

  /* Playfair Display — sous-titres élégants */
  @font-face {
    font-family: 'Playfair Display';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/PlayfairDisplay-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Playfair Display';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/PlayfairDisplay-Bold.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Playfair Display';
    font-weight: 400;
    font-style: italic;
    font-display: swap;
    src: url('./fonts/PlayfairDisplay-Italic.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Playfair Display';
    font-weight: 700;
    font-style: italic;
    font-display: swap;
    src: url('./fonts/PlayfairDisplay-BoldItalic.woff2') format('woff2');
  }

  /* Lato — corps de texte, lisibilité */
  @font-face {
    font-family: 'Lato';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Lato-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Lato';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Lato-Bold.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Lato';
    font-weight: 400;
    font-style: italic;
    font-display: swap;
    src: url('./fonts/Lato-Italic.woff2') format('woff2');
  }

  /* Oswald — condensé, impact visuel */
  @font-face {
    font-family: 'Oswald';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Oswald-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Oswald';
    font-weight: 600;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Oswald-SemiBold.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Oswald';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Oswald-Bold.woff2') format('woff2');
  }

  /* Roboto Slab — serif moderne */
  @font-face {
    font-family: 'Roboto Slab';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/RobotoSlab-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Roboto Slab';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/RobotoSlab-Bold.woff2') format('woff2');
  }

  /* Inter — alternative moderne Arial / Arial Black */
  @font-face {
    font-family: 'Inter';
    font-weight: 400;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Inter-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Inter';
    font-weight: 700;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Inter-Bold.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Inter';
    font-weight: 900;
    font-style: normal;
    font-display: swap;
    src: url('./fonts/Inter-Black.woff2') format('woff2');
  }
`;

export const Background = ({ style }) => {
  const frame = useCurrentFrame();

  // Grain animé : seed change toutes les 3 frames → effet pellicule naturel
  const grainSeed    = Math.floor(frame / 3) % 64;
  const grainOpacity = style.grain_intensity ?? 0.15;

  return (
    <AbsoluteFill>
      {/* @font-face — injection synchrone, zéro réseau */}
      <style>{FONT_FACES}</style>

      {/* Fond (image ou couleur unie) */}
      {style.background_image && style.background_image !== "solid" ? (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          <Img
            src={staticFile(style.background_image)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${style.background_scale ?? 1})`,
              transformOrigin: "center center",
            }}
          />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill style={{ backgroundColor: style.background_color }} />
      )}

      {/* Grain (film grain via SVG feTurbulence) */}
      {grainOpacity > 0 && (
        <AbsoluteFill
          style={{
            opacity: grainOpacity,
            mixBlendMode: "overlay",
            pointerEvents: "none",
          }}
        >
          <svg
            width="100%"
            height="100%"
            xmlns="http://www.w3.org/2000/svg"
            style={{ display: "block" }}
          >
            <filter id={`grain-${grainSeed}`}>
              <feTurbulence
                type="fractalNoise"
                baseFrequency="0.75"
                numOctaves="4"
                seed={grainSeed}
                stitchTiles="stitch"
              />
              <feColorMatrix type="saturate" values="0" />
            </filter>
            <rect
              width="100%"
              height="100%"
              filter={`url(#grain-${grainSeed})`}
            />
          </svg>
        </AbsoluteFill>
      )}

      {/* Vignette */}
      {style.vignette && (
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.70) 100%)",
            pointerEvents: "none",
          }}
        />
      )}
    </AbsoluteFill>
  );
};
