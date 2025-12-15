import { useContext, useEffect } from "react";

export default function useLongPolling(onMessage, onDetectStranger) {
  
  useEffect(() => {
    let isActive = true;

    let clientId = localStorage.getItem("client_id");
    if (!clientId) {
        clientId = crypto.randomUUID();
        localStorage.setItem("client_id", clientId);
    }

    const poll = async () => {
      while (isActive) {
        try {
          const response = await fetch(`http://127.0.0.1:5000/poll?client_id=${clientId}`);
          const data = await response.json();

          if (data.has_message) {
            console.log("received ms from server: " + data.message)
            onMessage(data.message);
            onDetectStranger(true);
          } else{
            console.log("server doesnt send anything !!")
          }

        } catch (err) {
          console.error("Polling error:", err);
          await new Promise(res => setTimeout(res, 2000)); // retry sau 2s
        }
      }
    };

    poll();

    return () => {
      isActive = false;
    };
  }, [onMessage]);
}
