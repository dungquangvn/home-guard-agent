import React from "react";

// Hàm xác định màu sắc dựa trên tiêu đề (cấp độ) log
const getLogStyles = (title) => {
  const level = title.toUpperCase();
  switch (level) {
    case 'ERROR': 
      return { iconBg: 'bg-red-600', text: 'text-red-400', titleColor: 'text-red-300' };
    case 'WARNING': 
      return { iconBg: 'bg-yellow-600', text: 'text-yellow-400', titleColor: 'text-yellow-300' };
    case 'INFO': 
      return { iconBg: 'bg-green-600', text: 'text-green-400', titleColor: 'text-green-300' };
    default: 
      return { iconBg: 'bg-gray-500', text: 'text-gray-400', titleColor: 'text-white' };
  }
};

export default function LogsItem({ log }) {
  // Lấy style động
  const { iconBg, titleColor, text } = getLogStyles(log.title);
  
  // Áp dụng Dark Mode styling cho LogItemComponent
  const LogItemComponent = (
    <div 
      className="flex items-start gap-4 p-4 bg-gray-700 rounded-xl 
                 border border-gray-600 hover:shadow-lg hover:border-teal-500/50 
                 transition-all cursor-pointer" // Thêm cursor-pointer
    >
      {/* Icon (Màu động) */}
      <div className={`w-3 h-3 mt-2 rounded-full ${iconBg} flex-shrink-0`}></div>

      {/* Nội dung */}
      <div className="flex-1">
        {/* Title (Màu động) */}
        <p className={`font-semibold ${titleColor}`}>{log.title}</p> 
        {/* Description */}
        <p className="text-sm text-gray-400 mt-1">{log.description}</p>
      </div>

      {/* Thời gian */}
      <span className="text-xs text-gray-500 whitespace-nowrap">
        {log.time}
      </span>
    </div>
  );

  return (
    <>
      {/* Nếu có file_path, bọc trong thẻ <a> */}
      {log.file_path ? (
        <a 
          href={log.file_path} 
          target="_blank" 
          rel="noopener noreferrer"
          className="block" // Dùng block để thẻ <a> chiếm toàn bộ chiều rộng
        >
          {LogItemComponent}
        </a>
      ) : (
        LogItemComponent
      )}
    </>
  );
}