import { useEffect, useState } from "react";

export default function LiveVideo() {

    return (
        <div className="flex flex-col items-center py-10">
            <img className="w-[900px] h-[500px] bg-gray-900 rounded-lg flex items-center justify-center"
            src="http://127.0.0.1:5000/video"
            alt="Camera Live">
            </img>
        </div>
    );
}
