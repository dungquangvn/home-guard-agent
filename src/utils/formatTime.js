export function formatTime(date) {
const d = new Date(date);
return `${d.getHours()}:${d.getMinutes()}:${d.getSeconds()} ${d.toLocaleDateString()}`;
}