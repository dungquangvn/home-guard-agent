import { useEffect, useRef } from "react";

export default function AudioAlert({ trigger }) {
  const audioRef = useRef(null);

  useEffect(() => {
    
    if (audioRef.current) {
      audioRef.current.volume = 0; 
      audioRef.current.play().catch(() => {});
    }
  }, []);

  useEffect(() => {
    if (trigger) {
    
      const audio = audioRef.current;
      if (!audio) return;
      audio.volume = 1.0;    
      audio.currentTime = 0; 
      audio.play().catch((e) => console.log("Play error:", e));
    } else{
      audioRef.current.volume = 0; 
    }
  }, [trigger]);

  return (
    <audio ref={audioRef} src="/sounds/alerts.mp3" preload="auto" />
  );
}
