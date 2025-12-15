import { useState, createContext } from "react";

export const DetectStranger = createContext(null);

export function DetectStrangerContext({ children }) {
  const [isDetectingStranger, setIsDetectingStranger] = useState(false);

  return (
    <DetectStranger.Provider
      value={{ isDetectingStranger, setIsDetectingStranger }}
    >
      {children}
    </DetectStranger.Provider>
  );
}
