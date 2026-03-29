const getLogStyles = (title = "") => {
  const upper = String(title).toUpperCase();

  if (upper.includes("ERROR")) {
    return { iconBg: "bg-red-600", titleColor: "text-red-300" };
  }

  if (upper.includes("WARNING") || upper.includes("ALERT")) {
    return { iconBg: "bg-yellow-600", titleColor: "text-yellow-300" };
  }

  if (upper.includes("INFO") || upper.includes("VERIFIED")) {
    return { iconBg: "bg-green-600", titleColor: "text-green-300" };
  }

  return { iconBg: "bg-gray-500", titleColor: "text-white" };
};

export default function LogsItem({ log, isSelected = false, onClick }) {
  const { iconBg, titleColor } = getLogStyles(log?.title);
  const hasFile = Boolean(log?.file_path);

  return (
    <article
      className={`rounded-xl border p-4 transition-all ${
        isSelected
          ? "border-teal-400 bg-gray-700/95 shadow-lg shadow-teal-500/10"
          : "border-gray-600 bg-gray-700 hover:border-teal-500/50 hover:shadow-lg"
      }`}
    >
      <button
        type="button"
        onClick={onClick}
        className="w-full text-left"
      >
        <div className="flex items-start gap-4">
          <div className={`mt-2 h-3 w-3 flex-shrink-0 rounded-full ${iconBg}`} />

          <div className="flex-1">
            <p className={`font-semibold ${titleColor}`}>{log?.title || "LOG"}</p>
            <p className="mt-1 text-sm text-gray-300">{log?.description || "Khong co mo ta"}</p>
          </div>

          <span className="whitespace-nowrap text-xs text-gray-400">
            {log?.time || log?.occurrence_time || "--:--:--"}
          </span>
        </div>
      </button>

      {hasFile ? (
        <div className="mt-3 flex justify-end">
          <a
            href={log.file_path}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-semibold text-teal-300 hover:text-teal-200"
          >
            Open attachment
          </a>
        </div>
      ) : null}
    </article>
  );
}
