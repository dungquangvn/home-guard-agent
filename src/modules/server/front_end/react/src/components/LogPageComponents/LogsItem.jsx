import React from "react";

export default function LogsItem({ log }) {
  return (
    <div className="flex items-start gap-4 p-4 bg-white shadow rounded-xl border border-gray-100 hover:shadow-md transition-all">
      {/* Icon */}
      <div className="w-3 h-3 mt-2 rounded-full bg-red-500"></div>

      {/* Nội dung */}
      <div className="flex-1">
        <p className="font-semibold text-gray-800">{log.title}</p>
        <p className="text-sm text-gray-500 mt-1">{log.description}</p>
      </div>

      {/* Thời gian */}
      <span className="text-xs text-gray-400 whitespace-nowrap">
        {log.time}
      </span>
    </div>
  );
}
