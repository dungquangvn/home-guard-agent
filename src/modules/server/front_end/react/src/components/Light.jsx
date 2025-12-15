import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

const ON_THRESHOLD = 55;
const OFF_THRESHOLD = 75;

export default function LightToggle() {
  const [isLightOn, setIsLightOn] = useState(false);
  const [avgBrightness, setAvgBrightness] = useState(70); // Khởi tạo giá trị

  // Hàm thăm dò API
  const fetchBrightness = async () => {
    try {
      // Gọi API mới
      const response = await fetch('http://127.0.0.1:5000/brightness'); 
      const data = await response.json();
      
      if (data.avg_brightness !== undefined) {
        setAvgBrightness(data.avg_brightness);
      }
    } catch (error) {
      console.error("Lỗi khi fetch độ sáng:", error);
    }
  };

  // Sử dụng useEffect để thiết lập chế độ thăm dò (Polling)
  useEffect(() => {
    // Gọi fetch lần đầu tiên ngay lập tức
    fetchBrightness(); 

    // Thiết lập interval để gọi fetch mỗi 1-2 giây
    const intervalId = setInterval(fetchBrightness, 1500); // 1.5 giây

    // Dọn dẹp interval khi component unmount
    return () => clearInterval(intervalId);
  }, []); // [] đảm bảo effect chỉ chạy 1 lần khi mount

  // Logic điều khiển đèn (Sử dụng Hysteresis)
  useEffect(() => {
    if (!isLightOn && avgBrightness < ON_THRESHOLD) {
      // Nếu đèn tắt VÀ quá tối
      setIsLightOn(true);
    } else if (isLightOn && avgBrightness > OFF_THRESHOLD) {
      // Nếu đèn bật VÀ quá sáng
      setIsLightOn(false);
    }
  }, [avgBrightness, isLightOn]);

  // Hiển thị giá trị độ sáng hiện tại để debug
  return (
    <>
      <div className="text-xl text-white mb-2">
        Độ sáng hiện tại: {avgBrightness.toFixed(2)}
      </div>
      <div
        className="cursor-pointer"
        title={isLightOn ? "Tắt đèn" : "Bật đèn"}
      >
        <AnimatePresence mode="wait">
            <motion.img
            key={isLightOn ? "on" : "off"}
            src={isLightOn ? "/imgs/light_on.png" : "/imgs/light_off.png"}
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
    </>
  );
}