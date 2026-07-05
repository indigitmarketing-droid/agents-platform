import "./index.css";
import { Composition } from "remotion";
import { EasyDentEdit } from "./Composition";

// Source: 720x1280, 24fps, 513 frames (~21.375s).
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="EasyDentEdit"
      component={EasyDentEdit}
      durationInFrames={513}
      fps={24}
      width={720}
      height={1280}
    />
  );
};
