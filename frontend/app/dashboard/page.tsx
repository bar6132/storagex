"use client";
import { useEffect, useState } from "react";
import { ApiService } from "@/lib/services";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const [videos, setVideos] = useState<any[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState(""); 
  const [isUploading, setIsUploading] = useState(false);
  const [selectedVideoUrl, setSelectedVideoUrl] = useState<string | null>(null); 
  const [isAdmin, setIsAdmin] = useState(false);
  const router = useRouter();
  
  useEffect(() => {
    const token = localStorage.getItem("storagex_token");
    if (!token) {
      router.push("/login");
    } else {
      fetchVideos();
    }
  }, [router]);

  useEffect(() => {
    const hasProcessingVideos = videos.some(v => v.status === "pending" || v.status === "processing");
    if (hasProcessingVideos) {
      const interval = setInterval(fetchVideos, 5000);
      return () => clearInterval(interval);
    }
  }, [videos]);

  const fetchVideos = async () => {
  try {
    const adminRes = await ApiService.getAllVideosAdmin();
    if (adminRes.ok) {
      const data = await adminRes.json();

      setVideos(data);
      setIsAdmin(true);
      return; 
    } 

    const res = await ApiService.getMyVideos();
    if (res.ok) {
      const data = await res.json();
      setVideos(data);
      setIsAdmin(false);
    }
  } catch (e) {
    console.error("Fetch error:", e);
  }
};

  const handleUpload = async () => {
    if (!file || !title) return alert("Please provide both a title and a video file.");
    setIsUploading(true);
    try {
      const res = await ApiService.uploadVideo(file, title); 
      if (res.ok) {
        setFile(null);
        setTitle("");
        fetchVideos();
      } else {
        alert("Upload failed");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (videoId: string) => {
    if (!confirm("Delete this video?")) return;
    const res = await ApiService.deleteVideo(videoId);
    if (res.ok) setVideos(videos.filter((v) => v.id !== videoId));
  };

  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-6xl mx-auto">
        
        <div className="flex items-center gap-4">
          <h1 className="text-4xl font-black text-black">MY STORAGE</h1>
          {videos.length > 1 && videos[0].owner_id !== videos[videos.length - 1].owner_id && (
            <span className="bg-red-600 text-white text-xs font-black px-2 py-1 rounded border-2 border-black">
              ADMIN VIEW
            </span>
          )}
        </div>
        
        <div className="mb-12 p-6 border-2 border-black rounded-xl bg-gray-50 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
          <h2 className="text-xl font-bold text-black mb-4">Upload New Video</h2>
          <div className="flex flex-col gap-4">
            <input 
              type="text" 
              placeholder="Enter a nice title for your video..." 
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="p-3 border-2 border-black rounded text-black font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 w-full"
            />
            <div className="flex flex-col md:flex-row gap-4">
                <input 
                  type="file" 
                  accept="video/*" 
                  onChange={(e) => setFile(e.target.files?.[0] || null)} 
                  className="flex-1 p-2 border-2 border-black rounded bg-white text-black font-medium file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-bold file:bg-black file:text-white hover:file:bg-gray-800" 
                />
                <button 
                  onClick={handleUpload} 
                  disabled={!file || !title || isUploading}
                  className={`px-8 py-3 rounded font-bold text-white border-2 border-black transition shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-y-1 active:shadow-none ${
                    isUploading ? "bg-gray-500" : "bg-blue-600 hover:bg-blue-700"
                  }`}
                >
                  {isUploading ? "UPLOADING..." : "UPLOAD NOW"}
                </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {videos.map((v) => (

              <div key={v.id} className="bg-white border-2 border-black rounded-xl p-5 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-1 transition-transform">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1 truncate mr-2">
                    <p className="text-lg font-black text-black truncate" title={v.title}>
                      {v.title || "Untitled"}
                    </p>
                    <p className="text-xs font-bold text-black mt-1 truncate">
                      File: {v.filename}
                    </p>
                  </div>

                  <div className="flex gap-2">
                    {v.is_deleted && isAdmin && (
                      <span className="bg-red-600 text-white text-[10px] font-black px-2 py-1 rounded border border-black shadow-[1px_1px_0px_0px_rgba(0,0,0,1)]">
                        USER DELETED
                      </span>
                    )}
                    <span className={`text-xs uppercase font-black px-2 py-1 rounded border border-black ${
                        v.status === 'completed' ? 'bg-green-300 text-black' : 
                        v.status === 'failed' ? 'bg-red-300 text-black' : 'bg-yellow-200 text-black'
                    }`}>
                      {v.status}
                    </span>
                  </div>
                </div>
              <div className="flex items-center justify-between mt-6 pt-4 border-t-2 border-gray-100">
                <button 
                  onClick={() => handleDelete(v.id)} 
                  className="text-sm font-bold text-red-600 hover:text-red-800"
                >
                  DELETE
                </button>
                
                {v.status === 'completed' && (
                  <button 
                    onClick={() => {
                      if (!v.s3_key) return alert("Video path missing");
                      const url = `http://localhost:9000/processed-videos/${v.s3_key}`;
                      console.log("Loading:", url);
                      setSelectedVideoUrl(url);
                    }}
                    className="px-4 py-2 bg-black text-white text-sm font-bold rounded hover:bg-gray-800 transition"
                  >
                    PLAY VIDEO
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {videos.length === 0 && !isUploading && (
          <div className="text-center py-20">
            <h3 className="text-2xl font-black text-black mb-2">No Videos Yet</h3>
            <p className="text-black font-medium">Upload your first video above to get started!</p>
          </div>
        )}

      </div>

      {selectedVideoUrl && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="relative w-full max-w-5xl bg-black border-2 border-gray-800 rounded-xl overflow-hidden shadow-2xl">
            <button 
              onClick={() => setSelectedVideoUrl(null)} 
              className="absolute top-4 right-4 text-white text-4xl font-bold hover:text-gray-300 z-10 bg-black/50 rounded-full w-12 h-12 flex items-center justify-center"
            >
              &times;
            </button>
            
            <video 
              key={selectedVideoUrl} 
              controls 
              autoPlay 
              crossOrigin="anonymous"
              className="w-full aspect-video"
            >
              <source src={selectedVideoUrl} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      )}
    </div>
  );
}