import { motion, AnimatePresence } from "framer-motion";
import { useContext, useState, useEffect } from "react";
import { DetectStranger } from "../context/DetectStrangerContext";

export default function LightToggle(isOn) {
    const {isDetectingStranger, setIsDetectingStranger} = useContext(DetectStranger)

return (
    <div
        className="cursor-pointer"
        title={isDetectingStranger ? "Tắt đèn" : "Bật đèn"}
        >
        <AnimatePresence mode="wait">
            <motion.img
                key={isDetectingStranger ? "on" : "off"}
                src={isDetectingStranger ? "/imgs/light_on.png" : "/imgs/light_off.png"}
                alt="Light"
                className="w-20 h-20"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                whileTap={{ scale: 0.9 }}
            />
        </AnimatePresence>
    </div>
    );
}