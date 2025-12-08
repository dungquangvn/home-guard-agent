import { useState, useEffect } from 'react';
import { getAlerts } from '../../services/alertService';


export default function useAlerts() {
const [alerts, setAlerts] = useState([]);
useEffect(() => {
async function fetchAlerts() {
const data = await getAlerts();
setAlerts(data);
}
fetchAlerts();
}, []);
return alerts;
}