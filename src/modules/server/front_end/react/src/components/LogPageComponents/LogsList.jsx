import { useState } from "react";
import LogsItem from "./LogsItem";

export default function LogsList({ logs }) {
  const ITEMS_PER_PAGE = 10;

  const [page, setPage] = useState(1);

  const totalPages = Math.ceil(logs.length / ITEMS_PER_PAGE);

  // Cắt log theo từng trang (Logic giữ nguyên)
  const slicedLogs = logs.slice(
    (page - 1) * ITEMS_PER_PAGE,
    page * ITEMS_PER_PAGE
  );

  const handlePrev = () => {
    if (page > 1) setPage(page - 1);
  };

  const handleNext = () => {
    if (page < totalPages) setPage(page + 1);
  };

  return (
    <div className="w-full">
      {/* Log List */}
      <div className="space-y-3">
        {slicedLogs.map((log) => (
          <LogsItem key={log.id} log={log} />
        ))}
      </div>

      {/* Pagination */}
      <div className="flex justify-center items-center gap-4 mt-8">
        
        {/* Nút Prev */}
        <button
          onClick={handlePrev}
          disabled={page === 1}
          // Style Dark Mode: nền xám, chữ trắng, hiệu ứng hover
          className="px-4 py-2 rounded-lg bg-gray-600 text-white 
                     hover:bg-gray-500 transition disabled:opacity-30 disabled:cursor-not-allowed"
        >
          &larr; Previous
        </button>

        {/* Trang hiện tại */}
        <span className="text-gray-400 font-medium">
          Trang <span className="text-teal-400 font-bold">{page}</span> / {totalPages}
        </span>

        {/* Nút Next */}
        <button
          onClick={handleNext}
          disabled={page === totalPages}
          // Style Dark Mode: nền xám, chữ trắng, hiệu ứng hover
          className="px-4 py-2 rounded-lg bg-gray-600 text-white 
                     hover:bg-gray-500 transition disabled:opacity-30 disabled:cursor-not-allowed"
        >
          Next &rarr;
        </button>
      </div>
    </div>
  );
}