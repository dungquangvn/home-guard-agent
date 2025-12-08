export default function RecordedVideoItem({ item }) {
  return (
    <a href={item.videoUrl} target="_blank">
      <div className="bg-white shadow-md rounded-xl p-4 border border-gray-200 flex-block flex-col gap-3 h-[100px]">

        <div>
          <h2 className="text-lg font-semibold text-gray-800">{item.title}</h2>
          <p className="text-sm text-gray-500">{item.extractedTime}</p>
        </div>

        {/* VIDEO */}
        {/* <div className="w-[50%] flex justify-center">
          <video
              src={item.videoUrl}
              controls
              className="rounded-md"
            />
        </div> */}
      </div>
    </a>
  );
}
