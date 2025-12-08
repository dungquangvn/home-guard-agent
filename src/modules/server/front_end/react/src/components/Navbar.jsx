import { NavLink } from "react-router-dom";

export default function Navbar() {
    return (
        <nav className="w-full bg-white shadow px-6 py-4 flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-800">Camera Live</h1>

            <div className="flex gap-6">
                <NavLink
                    to="/"
                    className={({ isActive }) =>
                        `${isActive ? "text-blue-600 font-semibold" : "text-gray-700"} hover:text-blue-600`
                    }
                >
                    Live Video
                </NavLink>

                <NavLink
                    to="/logs"
                    className={({ isActive }) =>
                        `${isActive ? "text-blue-600 font-semibold" : "text-gray-700"} hover:text-blue-600`
                    }
                >
                    Logs
                </NavLink>

                <NavLink
                    to="/recorded"
                    className={({ isActive }) =>
                        `${isActive ? "text-blue-600 font-semibold" : "text-gray-700"} hover:text-blue-600`
                    }
                >
                    Recorded Videos
                </NavLink>
            </div>
        </nav>
    );
}
