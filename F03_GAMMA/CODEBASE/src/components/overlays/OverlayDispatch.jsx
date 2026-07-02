// overlays/OverlayDispatch.jsx — Routeur central overlay
import React from "react";
import { OverlayNeonsInt }   from "./OverlayNeonsInt";
import { OverlayLampeInt }   from "./OverlayLampeInt";
import { OverlayPluieExt }   from "./OverlayPluieExt";
import { OverlayVentExt }    from "./OverlayVentExt";
import { OverlaySoleilExt }  from "./OverlaySoleilExt";
import { OverlayVitrePluie } from "./OverlayVitrePluie";
import { OverlayDefaut }     from "./OverlayDefaut";

const MAP = {
  "INTERIEUR:neons":   OverlayNeonsInt,
  "INTERIEUR:lampe":   OverlayLampeInt,
  "INTERIEUR:ecran":   OverlayLampeInt,   // fallback sur lampe (teinte froide gérée en interne)
  "INTERIEUR:sombre":  OverlayDefaut,
  "EXTERIEUR:pluie":   OverlayPluieExt,
  "EXTERIEUR:vent":    OverlayVentExt,
  "EXTERIEUR:soleil":  OverlaySoleilExt,
  "EXTERIEUR:nuit":    OverlayDefaut,
  "VITRE:pluie":       OverlayVitrePluie,
  "VITRE:brouillard":  OverlayVitrePluie,
  "defaut":            OverlayDefaut,
};

export function OverlayDispatch({ type, intensite, frame, fps }) {
  const Component = MAP[type] || OverlayDefaut;
  return <Component intensite={intensite} frame={frame} fps={fps} />;
}
