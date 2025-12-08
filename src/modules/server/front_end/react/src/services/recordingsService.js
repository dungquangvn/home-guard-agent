export const getRecordings = async () => {
const res = await fetch('/api/recordings');
return res.json();
};