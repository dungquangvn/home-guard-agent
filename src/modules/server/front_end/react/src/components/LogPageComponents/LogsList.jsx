import LogsItem from "./LogsItem";
import { getLogIdentity } from "../../utils/logIdentity";

export default function LogsList({
  logs,
  page,
  onPageChange,
  itemsPerPage = 10,
  selectedLogIdentity = "",
  onSelectLog,
}) {
  const safePage = Number(page) > 0 ? Number(page) : 1;
  const totalPages = Math.max(1, Math.ceil(logs.length / itemsPerPage));

  const startIndex = (safePage - 1) * itemsPerPage;
  const endIndex = safePage * itemsPerPage;
  const slicedLogs = logs.slice(startIndex, endIndex);

  const handlePrev = () => {
    if (safePage > 1) {
      onPageChange?.(safePage - 1);
    }
  };

  const handleNext = () => {
    if (safePage < totalPages) {
      onPageChange?.(safePage + 1);
    }
  };

  return (
    <div className="w-full">
      <div className="space-y-3">
        {slicedLogs.map((log, index) => {
          const absoluteIndex = startIndex + index;
          const identity = getLogIdentity(log, absoluteIndex);

          return (
            <LogsItem
              key={identity}
              log={log}
              isSelected={identity === selectedLogIdentity}
              onClick={() => onSelectLog?.(log, absoluteIndex)}
            />
          );
        })}
      </div>

      <div className="mt-8 flex items-center justify-center gap-4">
        <button
          onClick={handlePrev}
          disabled={safePage === 1}
          className="rounded-lg bg-gray-600 px-4 py-2 text-white transition hover:bg-gray-500 disabled:cursor-not-allowed disabled:opacity-30"
        >
          &larr; Previous
        </button>

        <span className="font-medium text-gray-400">
          Trang <span className="font-bold text-teal-400">{safePage}</span> / {totalPages}
        </span>

        <button
          onClick={handleNext}
          disabled={safePage === totalPages}
          className="rounded-lg bg-gray-600 px-4 py-2 text-white transition hover:bg-gray-500 disabled:cursor-not-allowed disabled:opacity-30"
        >
          Next &rarr;
        </button>
      </div>
    </div>
  );
}
