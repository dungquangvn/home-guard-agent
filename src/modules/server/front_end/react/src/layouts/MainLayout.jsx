export default function MainLayout({ children }) {
return (
<div className="min-h-screen bg-gray-100">
<header className="bg-blue-600 text-white p-4 font-bold text-xl">AI-CAM Dashboard</header>
<main className="p-6">{children}</main>
</div>
);
}