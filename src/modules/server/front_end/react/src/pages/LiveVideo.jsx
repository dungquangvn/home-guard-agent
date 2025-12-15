import LightToggle from "../components/Light";
export default function LiveVideo() {
return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-8">
      
      {/* Tiêu đề chính */}
      <h1 className="text-4xl font-extrabold mb-10 text-teal-400 tracking-wider">
        Smart Surveillance Hub
      </h1>

      {/* -------------------- CONTAINER CHÍNH (Camera + Control) -------------------- */}
      {/* Grid 2 cột: Cột video lớn (2/3) và Cột điều khiển nhỏ (1/3) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full max-w-6xl">
        
        {/* Cột 1: Video Live Stream */}
        <div className="lg:col-span-2">
          <div 
            className="bg-gray-800 rounded-2xl shadow-2xl 
                       overflow-hidden border-2 border-teal-500/50 
                       transform hover:scale-[1.01] transition duration-300"
          >
            <h2 className="p-4 text-xl font-semibold border-b border-gray-700 bg-gray-700/50">
              Live Feed
            </h2>
            <div className="relative w-full aspect-video">
              <img
                className="w-full h-full object-cover" 
                src="http://127.0.0.1:5000/video" // Đảm bảo tên route đúng
                alt="Camera Live"
              />
            </div>
          </div>
        </div>

        {/* Cột 2: Control Module */}
        <div className="lg:col-span-1 flex flex-col justify-center">
          
          <div 
            className="bg-gray-800 p-8 rounded-2xl shadow-xl 
                       border border-gray-700 hover:border-yellow-500 
                       transition duration-300 transform hover:shadow-yellow-500/20"
          >
            <h3 className="text-xl font-bold mb-6 text-yellow-400 text-center">
              Automatic Light Control
            </h3>
            
            {/* Component LightToggle */}
            <div className="flex flex-col items-center space-y-4">
                <LightToggle />
            </div>
            
          </div>
        </div>

      </div>
      
      {/* Thông tin chân trang hoặc debug */}
      <footer className="mt-10 text-gray-500 text-sm">
        System Status: Online | Latency: Real-time
      </footer>
    </div>
  );
}