import { useState } from "react";
import LogsItem from "./LogsItem";

export default function LogsList({ logs }) {
  const ITEMS_PER_PAGE = 10;

  const [page, setPage] = useState(1);

  const totalPages = Math.ceil(logs.length / ITEMS_PER_PAGE);

  // Cắt log theo từng trang
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
      <div className="flex justify-center items-center gap-4 mt-5">
        <button
          onClick={handlePrev}
          disabled={page === 1}
          className="px-4 py-2 rounded bg-gray-200 disabled:opacity-40"
        >
          Prev
        </button>

        <span className="text-gray-800 font-medium">
          Page {page} / {totalPages}
        </span>

        <button
          onClick={handleNext}
          disabled={page === totalPages}
          className="px-4 py-2 rounded bg-gray-200 disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  );
}
