export default function AlertPopup({ alert, onClose }) {
if (!alert) return null;


return (
<div className="fixed top-6 right-6 bg-red-600 text-white p-4 rounded-2xl shadow-2xl animate-bounce">
<p className="font-bold">🚨 Cảnh báo!</p>
<p>{alert.message}</p>
<button onClick={onClose} className="mt-2 px-2 py-1 bg-white text-red-600 rounded-lg">Đóng</button>
</div>
);
}