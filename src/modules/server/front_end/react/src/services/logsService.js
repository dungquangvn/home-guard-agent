export const getLogs = async () => {
const res = await fetch('/api/logs');
return res.json();
};