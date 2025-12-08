import { useState, useEffect } from 'react';
import { getRecordings } from '../../services/recordingsService';


export default function useRecordings() {
const [recordings, setRecordings] = useState([]);
useEffect(() => {
async function fetchRecordings() {
const data = await getRecordings();
setRecordings(data);
}
fetchRecordings();
}, []);
return recordings;
}