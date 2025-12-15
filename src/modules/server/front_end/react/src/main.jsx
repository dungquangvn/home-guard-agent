import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './pages/App';
import "./styles/input.css"
import { DetectStrangerContext } from './context/DetectStrangerContext';


ReactDOM.createRoot(document.getElementById('root')).render(
<React.StrictMode>
    <DetectStrangerContext>
        <App></App>
    </DetectStrangerContext>
</React.StrictMode>
);