// src/pages/RecordedVideos.jsx
import { useEffect, useState } from "react";
import RecordedVideoList from "../components/VideoRecordPageComponent/RecordedVideoList";
import LoadingBar from "../components/LoadingBar";

export default function RecordedVideos() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);

  const fetchRecordedVideos = async () => {
    try {
      setLoading(true);

      const res = await fetch("http://127.0.0.1:5000/video_records");
      const data = await res.json();

      setVideos(data);
    } catch (err) {
      console.error("Error fetching recorded videos:", err);
    } finally {
      setTimeout(() => setLoading(false), 600);
    }
  };

  useEffect(() => {
    fetchRecordedVideos();
  }, []);

  return (
    <div className="p-6">
      <LoadingBar loading={loading} />
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Recorded Videos</h1>

        <button
          onClick={fetchRecordedVideos}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700"
        >
          {loading ? "Đang cập nhật..." : "Cập nhật"}
        </button>
      </div>

         {videos.length === 0 ? (
            <div className="text-gray-600 text-center mt-10">
              Không có video nào được lưu.
            </div>
          ) : (
            <RecordedVideoList videos={videos} page={page} setPage={setPage} />
          )}
      
    </div>
  );
}
