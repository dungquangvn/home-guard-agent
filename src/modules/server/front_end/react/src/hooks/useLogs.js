import { useState, useEffect } from 'react';
import { getLogs } from '../services/logsService';


export default function useLogs() {
const [logs, setLogs] = useState([]);
useEffect(() => {
async function fetchLogs() {
const data = await getLogs();
setLogs(data);
}
fetchLogs();
}, []);
return logs;
}
