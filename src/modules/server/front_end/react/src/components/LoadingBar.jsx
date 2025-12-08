export default function LoadingBar({ loading }) {
  return (
    <div className="w-full h-1 bg-transparent relative">
      {loading && (
        <div className="absolute top-0 left-0 h-1 bg-blue-500 animate-loading-bar"></div>
      )}
    </div>
  );
}
