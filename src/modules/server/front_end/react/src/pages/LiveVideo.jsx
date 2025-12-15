import LightToggle from "../components/Light";
export default function LiveVideo() {
return (
    <div className="flex flex-col items-center py-10">
        <div className="flex flex-row">
            <img
                className="w-[900px] h-[500px] bg-gray-900 rounded-lg"
                src="http://127.0.0.1:5000/video"
                alt="Camera Live"
            />
            
            <LightToggle />
            
        </div>
    </div>
    );
}