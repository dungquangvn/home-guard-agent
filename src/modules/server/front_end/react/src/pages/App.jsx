import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "../components/Navbar";
import LiveVideo from "./LiveVideo";
import Logs from "./Logs";
import RecordedVideos from "./RecordedVideos";
import SecurityChat from "./SecurityChat";

export default function App() {
    return (
        <BrowserRouter>
            <Navbar />

            <Routes>
                <Route path="/" element={<LiveVideo />} />
                <Route path="/logs" element={<Logs />} />
                <Route path="/recorded" element={<RecordedVideos />} />
                <Route path="/chat" element={<SecurityChat />} />
            </Routes>
        </BrowserRouter>
    );
}
