import { useEffect, useState } from "react";
import { getLogs } from "../services/logsService";

const VIDEO_API_URL = "http://127.0.0.1:5000/video";

export default function LiveVideo() {
  const [latestLogs, setLatestLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchLatestLogs = async () => {
      try {
        const logs = await getLogs();

        if (isMounted) {
          setLatestLogs(logs.slice(0, 3));
          setLoadingLogs(false);
        }
      } catch (error) {
        console.error("Error fetching latest logs:", error);
        if (isMounted) setLoadingLogs(false);
      }
    };

    fetchLatestLogs();
    const intervalId = setInterval(fetchLatestLogs, 5000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 md:p-8">
      <div className="mx-auto w-full max-w-6xl space-y-6">
        <section className="overflow-hidden rounded-2xl border border-teal-500/40 bg-gray-800 shadow-2xl">
          <div className="border-b border-gray-700 bg-gray-700/50 p-4">
            <h2 className="text-xl font-semibold text-teal-300">Live Feed</h2>
          </div>
          <div className="aspect-video w-full">
            <img
              className="h-full w-full object-cover"
              src={VIDEO_API_URL}
              alt="Camera Live"
            />
          </div>
        </section>

        <section className="rounded-2xl border border-gray-700 bg-gray-800 p-5 shadow-xl">
          <h3 className="mb-4 text-lg font-semibold text-red-300">3 Logs Mới Nhất</h3>

          {loadingLogs ? (
            <p className="text-sm text-gray-400">Đang tải logs...</p>
          ) : latestLogs.length === 0 ? (
            <p className="text-sm text-gray-400">Chưa có log nào.</p>
          ) : (
            <div className="space-y-3">
              {latestLogs.map((log, index) => (
                <div
                  key={log.id ?? `${log.time}-${index}`}
                  className="rounded-lg border border-gray-700 bg-gray-900/50 p-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-semibold text-gray-100">
                      {log.title || "LOG"}
                    </p>
                    <span className="whitespace-nowrap text-xs text-gray-500">
                      {log.time || "--:--:--"}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-gray-300">
                    {log.description || "Không có mô tả"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
