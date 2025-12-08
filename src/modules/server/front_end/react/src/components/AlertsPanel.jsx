export default function AlertsPanel({ alerts }) {
return (
<div className="space-y-3 max-h-64 overflow-y-auto">
{alerts.map(a => (
<div key={a.id} className="p-3 bg-red-100 rounded-xl border border-red-300">
<p className="font-semibold text-red-700">{a.message}</p>
<p className="text-xs text-gray-500">{a.time}</p>
</div>
))}
</div>
);
}