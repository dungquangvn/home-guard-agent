import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "../components/Navbar";
import LiveVideo from "./LiveVideo";
import Logs from "./Logs";
import RecordedVideos from "./RecordedVideos";
import Alert from "../components/AlertComponents/Alert";

export default function App() {
    return (
        <BrowserRouter>

            <Alert></Alert>
            <Navbar />

            <Routes>
                <Route path="/" element={<LiveVideo />} />
                <Route path="/logs" element={<Logs />} />
                <Route path="/recorded" element={<RecordedVideos />} />
            </Routes>
        </BrowserRouter>
    );
}
