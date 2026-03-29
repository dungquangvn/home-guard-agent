import { NavLink } from "react-router-dom";

export default function Navbar() {
    // Định nghĩa màu Teal/Cyan cho trạng thái Active
    const activeColor = "text-teal-400 font-bold border-b-2 border-teal-400";
    const defaultColor = "text-gray-400 hover:text-teal-400 hover:border-b-2 hover:border-teal-400/50";
    
    return (
        // 1. Nền tối và Viền dưới nhẹ
        <nav className="w-full bg-gray-900 border-b border-gray-700 px-8 py-4 flex items-center justify-between shadow-xl">
            
            {/* Tiêu đề chính */}
            <h1 className="text-2xl font-extrabold text-teal-400 tracking-wider">
                AI CAM HUB
            </h1>

            {/* Danh sách liên kết */}
            <div className="flex gap-10 items-center">
                
                {/* Live Video */}
                <NavLink
                    to="/"
                    className={({ isActive }) =>
                        `py-2 transition duration-200 ${isActive ? activeColor : defaultColor}`
                    }
                >
                    <span className="flex items-center gap-2">
                        {/* Biểu tượng (Icon giả định) */}
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 5H4v6h12V8z" clipRule="evenodd"></path>
                        </svg>
                        Live Video
                    </span>
                </NavLink>

                {/* Logs */}
                <NavLink
                    to="/logs"
                    className={({ isActive }) =>
                        `py-2 transition duration-200 ${isActive ? activeColor : defaultColor}`
                    }
                >
                    <span className="flex items-center gap-2">
                         {/* Biểu tượng (Icon giả định) */}
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                            <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h.01a1 1 0 100-2H10zm3 0a1 1 0 000 2h.01a1 1 0 100-2H13zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H10z" clipRule="evenodd" />
                        </svg>
                        Logs
                    </span>
                </NavLink>

                <NavLink
                    to="/chat"
                    className={({ isActive }) =>
                        `py-2 transition duration-200 ${isActive ? activeColor : defaultColor}`
                    }
                >
                    <span className="flex items-center gap-2">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.29-3.226A6.948 6.948 0 012 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM6 9a1 1 0 100 2h2a1 1 0 100-2H6zm3 0a1 1 0 100 2h5a1 1 0 100-2H9z" clipRule="evenodd"></path>
                        </svg>
                        Security Chat
                    </span>
                </NavLink>

                {/* Recorded Videos */}
                <NavLink
                    to="/recorded"
                    className={({ isActive }) =>
                        `py-2 transition duration-200 ${isActive ? activeColor : defaultColor}`
                    }
                >
                    <span className="flex items-center gap-2">
                         {/* Biểu tượng (Icon giả định) */}
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd"></path>
                        </svg>
                        Recorded Videos
                    </span>
                </NavLink>
            </div>
        </nav>
    );
}
