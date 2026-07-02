import React from "react";
import { Img, OffthreadVideo, staticFile } from "remotion";

// Utilise l'API officielle staticFile() de Remotion pour résoudre les assets
// du dossier public/. Le hack précédent (`/${f}`) ne fonctionne pas dans le
// runner CI parce que Remotion ne sert pas public/ à la racine en mode bundle.
export const WorldNode = ({ imageFile, mediaType = "image" }) => {
  const src = staticFile(imageFile);
  const style = { width: "100%", height: "100%", objectFit: "cover" };

  if (mediaType === "gif") {
    // @remotion/gif — importé dynamiquement pour éviter l'erreur si absent
    try {
      const { Gif } = require("@remotion/gif");
      return <Gif src={src} style={style} fit="cover" />;
    } catch {
      return <Img src={src} style={style} />;
    }
  }

  if (mediaType === "video") {
    return <OffthreadVideo src={src} style={style} />;
  }

  return <Img src={src} style={style} />;
};
