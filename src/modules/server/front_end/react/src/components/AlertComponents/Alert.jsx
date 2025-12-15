import { useEffect, useState, useContext } from "react";
import { io } from "socket.io-client";
import useLongPolling from "./useLongPolling";
import AudioAlert from "./AudioAlert";
import { DetectStranger } from "../../context/DetectStrangerContext";

export default function Alert() {
  const [toasts, setToasts] = useState([]);
  const {isDetectingStranger, setIsDetectingStranger} = useContext(DetectStranger)

  useLongPolling((message) => {
    setToasts(prev => [...prev, message]);
  }, setIsDetectingStranger);
  


  return (
    <>
    <AudioAlert trigger={isDetectingStranger}></AudioAlert>
    <div style={{ position: "fixed", top: 20, right: 20, zIndex: 1000 }}>
      {toasts.map((toast) => (
        <div key={toast.id} style={{
          backgroundColor: "red",
          color: "white",
          padding: "10px 20px",
          borderRadius: 8,
          marginBottom: 10,
          minWidth: 250,
          boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}>
          <span>{toast.ms}</span>
          <button onClick={() => {
            setToasts((prev) => prev.filter((t) => t.id !== toast.id));
            setIsDetectingStranger(false);
          }}
                  style={{
                    marginLeft: 10,
                    background: "white",
                    color: "red",
                    border: "none",
                    cursor: "pointer",
                    borderRadius: 4,
                    padding: "2px 6px"
                  }}>X</button>
        </div>
      ))}
      
    </div>
    </>
  );
}
