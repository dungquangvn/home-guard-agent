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

    const audio = audioRef.current;
    console.log("detect stranger: " + trigger)
    if (!audio) {
      console.log("audio ref is null");
      return;
    }

    if (trigger) {
      console.log("active alert sounds !!");
      audio.volume = 1.0;    
      audio.currentTime = 0; 
      audio.play().catch((e) => console.log("Play error:", e));
    } else{
      console.log("inactive alert sounds !!");
      audio.volume = 0; 
    }
  }, [trigger]);

  return (
    <audio ref={audioRef} src="/sounds/alerts.mp3" preload="auto" />
  );
}
