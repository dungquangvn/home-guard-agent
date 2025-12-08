import { useEffect, useState } from "react";
import LogsList from "../components/LogPageComponents/LogsList";
import LoadingBar from "../components/LoadingBar";

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchLogsFromServer = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:5000/logs");
      const data = await response.json();
      setLogs(data);
    } catch (error) {
      console.error("Lỗi tải logs:", error);
    } finally {
      setTimeout(() => setLoading(false), 600);
    }
  };

  useEffect(() => {
    fetchLogsFromServer();
  }, []);

  return (
    <div className="p-6">

      {/* Loading bar nằm phía trên */}
      <LoadingBar loading={loading} />

      {/* Header */}
      <div className="flex justify-between items-center mb-4 mt-2">
        <h1 className="text-2xl font-bold text-gray-800">Logs</h1>

        <button
          onClick={fetchLogsFromServer}
          className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 shadow transition"
          disabled={loading}
        >
          {loading ? "Đang cập nhật..." : "Cập nhật"}
        </button>
      </div>

      {logs.length === 0 ? (
      <div className="text-gray-600 text-center mt-10">
        Không có log nào để hiển thị.
      </div>
    ) : (
      <LogsList logs={logs} />
    )}
    </div>
  );
}
