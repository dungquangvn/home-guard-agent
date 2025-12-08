
import RecordedVideoItem from "./RecordedVideoItem";

export default function RecordedVideoList({ videos, page, setPage }) {
  const itemsPerPage = 10;
  const totalPages = Math.ceil(videos.length / itemsPerPage);

  const startIndex = (page - 1) * itemsPerPage;
  const limitedVideos = videos.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4">
        {limitedVideos.map((item) => (
          <RecordedVideoItem key={item.id} item={item} />
        ))}
      </div>

      {/* Pagination */}
      <div className="flex justify-center items-center gap-4 mt-4">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-4 py-2 rounded-md bg-gray-200 text-gray-700 disabled:bg-gray-100"
        >
          Trước
        </button>

        <span className="font-semibold">
          Trang {page}/{totalPages}
        </span>

        <button
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page === totalPages}
          className="px-4 py-2 rounded-md bg-gray-200 text-gray-700 disabled:bg-gray-100"
        >
          Sau
        </button>
      </div>
    </div>
  );
}
