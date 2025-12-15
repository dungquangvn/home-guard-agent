import { useEffect, useState } from "react";
import LogsList from "../components/LogPageComponents/LogsList";
import LoadingBar from "../components/LoadingBar";

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  // --- Hàm fetchLogsFromServer giữ nguyên ---
  const fetchLogsFromServer = async () => {
    setLoading(true);
    try {
      // Dùng URL tuyệt đối
      const response = await fetch("http://127.0.0.1:5000/logs");
      const data = await response.json();
      
      // Giả định API trả về mảng log, nếu không, có thể là data.logs
      setLogs(data); 
      
    } catch (error) {
      console.error("Lỗi tải logs:", error);
      // Có thể đặt setLogs([]) nếu lỗi
    } finally {
      // Loại bỏ setTimeout nếu không cần thiết, hoặc giảm thời gian
      setTimeout(() => setLoading(false), 300); 
    }
  };

  // --- useEffect giữ nguyên ---
  useEffect(() => {
    fetchLogsFromServer();
  }, []);

  return (
    // 1. Thay đổi nền chính: Dark Mode
    <div className="min-h-screen bg-gray-900 text-white p-6"> 

      {/* Loading bar nằm phía trên */}
      <LoadingBar loading={loading} />

      {/* 2. Header và nút bấm nằm trong một container nổi bật */}
      <div className="bg-gray-800 p-6 rounded-t-2xl shadow-xl border-b border-gray-700">
          <div className="flex justify-between items-center">
            
            {/* Tiêu đề: Nổi bật, dùng màu của Log/Event (ví dụ: Đỏ) */}
            <h1 className="text-3xl font-bold text-red-400">System Logs & Events</h1>

            {/* Nút Cập nhật */}
            <button
              onClick={fetchLogsFromServer}
              // Thay đổi màu nút: Dùng màu Teal (như Dashboard) hoặc màu nổi bật
              className={`px-6 py-2 rounded-xl shadow transition 
                        ${loading 
                            ? "bg-gray-600 text-gray-400 cursor-not-allowed" 
                            : "bg-teal-600 hover:bg-teal-500 text-white"}`
                        }
              disabled={loading}
            >
              {loading ? "Đang tải..." : "Tải lại Logs"}
            </button>
          </div>
      </div>

      {/* 3. Container chứa danh sách Logs */}
      <div className="bg-gray-800 rounded-b-2xl shadow-2xl min-h-[70vh] p-4 border border-gray-700">
          
        {logs.length === 0 ? (
          <div className="text-gray-500 text-center mt-10 p-4">
            {loading ? "Đang chờ dữ liệu..." : "Không có log nào để hiển thị."}
          </div>
        ) : (
          // Component LogsList sẽ cần được sửa đổi để sử dụng phong cách Dark Mode
          <LogsList logs={logs} />
        )}
      </div>
      
    </div>
  );
}