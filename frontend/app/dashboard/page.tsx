"use client";
import { useEffect, useState } from "react";
import { ApiService } from "@/lib/services";
import { useRouter } from "next/navigation";
import Navbar from "@/app/components/Navbar"; 

export default function DashboardPage() {
  const [videos, setVideos] = useState<any[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState(""); 
  const [resolution, setResolution] = useState("720p"); 
  const [isUploading, setIsUploading] = useState(false);
  const [selectedVideoUrl, setSelectedVideoUrl] = useState<string | null>(null); 
  const [isMounted, setIsMounted] = useState(false);
  
  const [isAdmin, setIsAdmin] = useState(false); 
  
  const router = useRouter();

  useEffect(() => {
    setIsMounted(true);
    const token = localStorage.getItem("storagex_token");
    if (!token) {
      router.push("/login");
    } else {
      fetchVideos();
    }
  }, [router]);

  useEffect(() => {
    const hasProcessing = videos.some(v => v.status === "pending" || v.status === "processing");
    if (hasProcessing) {
      const interval = setInterval(fetchVideos, 5000);
      return () => clearInterval(interval);
    }
  }, [videos]);

  const fetchVideos = async () => {
    try {
      const adminRes = await ApiService.getAllVideosAdmin();
      
      if (adminRes.ok) {
        setIsAdmin(true);
        setVideos(await adminRes.json());
        return; 
      } 

      const res = await ApiService.getMyVideos();
      if (res.ok) {
        setIsAdmin(false);
        setVideos(await res.json());
      }
    } catch (e) { 
      console.error("Fetch error:", e); 
    }
  };

  const handleUpload = async () => {
    if (!file || !title) return alert("Please provide both a title and a video file.");
    setIsUploading(true);
    try {
      const res = await ApiService.uploadVideo(file, title, resolution); 
      if (res.ok) {
        setFile(null); setTitle("");
        fetchVideos();
      } else { alert("Upload failed: Error or Quota (if not admin)."); }
    } catch (err) { console.error(err); } 
    finally { setIsUploading(false); }
  };

  const handleDelete = async (videoId: string) => {
    if (!confirm("Delete this video?")) return;
    const res = await ApiService.deleteVideo(videoId);
    if (res.ok) {
      setVideos(prev => prev.filter((v) => v.id !== videoId));
    }
  };

  if (!isMounted) return null;

  return (
    <div className="min-h-screen bg-white">
      <Navbar videos={videos} isAdmin={isAdmin} />

      <div className="max-w-6xl mx-auto p-8">
        <div className="flex items-center gap-4 mb-8">
          <h1 className="text-4xl font-black text-black tracking-tight">MY STORAGE</h1>
          {isAdmin && (
            <span className="bg-red-600 text-white text-xs font-black px-2 py-1 rounded border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
              ADMIN VIEW
            </span>
          )}
        </div>
        
        <div className="mb-12 p-6 border-4 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
          <h2 className="text-xl font-bold text-black mb-4 uppercase italic tracking-widest">Upload Video</h2>
          <div className="flex flex-col gap-4">
            <input 
              type="text" 
              placeholder="Title..." 
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="p-3 border-2 border-black font-bold text-black placeholder-black outline-none focus:bg-yellow-50"
            />
            
            <div className="flex flex-col md:flex-row gap-4 items-end">
                <input 
                  type="file" 
                  accept="video/*" 
                  onChange={(e) => setFile(e.target.files?.[0] || null)} 
                  className="flex-1 p-2 border-2 border-black bg-white font-bold text-black file:bg-black file:text-white file:border-0 file:px-4 file:mr-4" 
                />

                <div className="w-full md:w-48">
                  <label className="block text-[10px] font-black mb-1 uppercase tracking-tighter text-black">Target Quality</label>
                  <select 
                    value={resolution}
                    onChange={(e) => setResolution(e.target.value)}
                    className="w-full p-2 border-2 border-black font-bold bg-white text-black"
                  >
                    <option value="1080p">1080p (HD)</option>
                    <option value="720p">720p (SD)</option>
                    <option value="480p">480p (Mobile)</option>
                  </select>
                </div>

                <button 
                  onClick={handleUpload} 
                  disabled={!file || !title || isUploading}
                  className={`px-8 py-3 border-2 border-black font-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] active:translate-y-1 active:shadow-none transition-all ${
                    isUploading ? "bg-gray-400 text-black" : "bg-blue-600 text-white hover:bg-blue-700"
                  }`}
                >
                  {isUploading ? "PROCESS..." : "UPLOAD"}
                </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {videos.map((v) => (
            <div key={v.id} className="bg-white border-4 border-black p-5 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-1 transition-all">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1 truncate">
                  <p className="text-lg font-black text-black truncate">{v.title || "Untitled"}</p>
                  <p className="text-[10px] font-bold text-black uppercase">Size: {(v.file_size / (1024 * 1024)).toFixed(1)} MB</p>
                  {isAdmin && <p className="text-[10px] font-bold text-blue-600 uppercase mt-1">OWNER ID: {v.owner_id}</p>}
                </div>
                <div className="flex gap-2">
                  {v.is_deleted && isAdmin && (
                    <span className="bg-red-600 text-white text-[10px] font-black px-2 py-1 border border-black shadow-[1px_1px_0px_0px_rgba(0,0,0,1)]">DELETED</span>
                  )}
                  <span className={`text-[10px] font-black px-2 py-1 border border-black uppercase text-black ${
                    v.status === 'completed' ? 'bg-green-400' : 'bg-yellow-300'
                  }`}>{v.status}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between mt-6 pt-4 border-t-2 border-black">
                <button onClick={() => handleDelete(v.id)} className="text-xs font-black text-red-600 hover:underline uppercase">DELETE</button>
                {v.status === 'completed' && (
                  <button 
                    onClick={() => setSelectedVideoUrl(`http://localhost:9000/processed-videos/${v.s3_key}`)}
                    className="bg-black text-white px-4 py-2 text-xs font-black border-2 border-black shadow-[2px_2px_0px_0px_rgba(100,100,100,1)]"
                  >PLAY</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedVideoUrl && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-[100] p-4">
          <div className="relative w-full max-w-4xl border-4 border-white shadow-2xl">
            <button onClick={() => setSelectedVideoUrl(null)} className="absolute -top-12 right-0 text-white font-black text-2xl uppercase">Close [X]</button>
            <video key={selectedVideoUrl} controls autoPlay className="w-full">
              <source src={selectedVideoUrl} type="video/mp4" />
            </video>
          </div>
        </div>
      )}
    </div>
  );
}