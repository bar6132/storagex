"use client";
import { useEffect, useState, useRef } from "react";
import { ApiService } from "@/lib/services";
import { useRouter } from "next/navigation";
import Navbar from "@/app/components/Navbar"; 
import { jwtDecode } from "jwt-decode"; 

export default function DashboardPage() {
  const [videos, setVideos] = useState<any[]>([]);
  
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState(""); 
  const [description, setDescription] = useState(""); 
  const [category, setCategory] = useState("Other");  
  const [isShared, setIsShared] = useState(false);    
  const [resolution, setResolution] = useState("720p"); 
  const [isUploading, setIsUploading] = useState(false);

  const [viewMode, setViewMode] = useState<'private' | 'feed'>('private'); 

  const [selectedVideoUrl, setSelectedVideoUrl] = useState<string | null>(null); 
  const [isMounted, setIsMounted] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false); 
  
  const ws = useRef<WebSocket | null>(null);
  const router = useRouter();

  useEffect(() => {
    setIsMounted(true);
    const token = localStorage.getItem("storagex_token");
    
    if (!token) {
      router.push("/login");
      return;
    } 

    try {
      const decoded: any = jwtDecode(token);
      const userId = decoded.sub_id || decoded.id; 
      if (userId) connectWebSocket(userId);
    } catch (e) {
      console.error("Token error", e);
    }

    fetchVideos(); 

    return () => {
      if (ws.current) ws.current.close();
    };
  }, [router]);

  useEffect(() => {
    if (isMounted) fetchVideos();
  }, [viewMode]); 

  const connectWebSocket = (userId: number) => {
    const wsUrl = `ws://localhost:8000/ws/${userId}`;
    const socket = new WebSocket(wsUrl);
    socket.onopen = () => console.log("WS Connected");
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "video_update") {
        setVideos((prev) => prev.map((v) => 
          v.id === data.video_id ? { ...v, status: data.status } : v
        ));
      }
    };
    ws.current = socket;
  };

  const fetchVideos = async () => {
    try {
      if (viewMode === 'private') {
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
      } else {
        const res = await ApiService.getFeed();
        if (res.ok) {
          setVideos(await res.json());
        }
      }
    } catch (e) { console.error(e); }
  };

  const handleUpload = async () => {
    if (!file || !title) return alert("Please provide title and file.");
    setIsUploading(true);
    try {
      const res = await ApiService.uploadVideo(file, title, description, category, isShared, resolution); 
      if (res.ok) {
        setFile(null); setTitle(""); setDescription(""); setCategory("Other"); setIsShared(false);
        setViewMode('private');
        fetchVideos(); 
      } else { 
        const errorData = await res.json();
        alert(errorData.detail || "Upload failed"); 
      }
    } catch (err) { alert("Network error."); } 
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
    <div className="min-h-screen bg-white text-black">
      <Navbar videos={videos} isAdmin={isAdmin} />

      <div className="max-w-6xl mx-auto p-8">
        <div className="flex flex-col md:flex-row items-center justify-between mb-8 gap-4">
          <div className="flex items-center gap-4">
            <h1 className="text-4xl font-black text-black tracking-tight">STORAGE<span className="text-blue-600">X</span></h1>
            {isAdmin && viewMode === 'private' && (
              <span className="bg-red-600 text-white text-xs font-black px-2 py-1 border-2 border-black">ADMIN</span>
            )}
          </div>

          <div className="flex bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
            <button 
              onClick={() => setViewMode('private')}
              className={`px-6 py-2 font-black uppercase transition-all ${viewMode === 'private' ? 'bg-black text-white' : 'bg-white text-black hover:bg-gray-100'}`}
            >
              My Files
            </button>
            <div className="w-0.5 bg-black"></div>
            <button 
              onClick={() => setViewMode('feed')}
              className={`px-6 py-2 font-black uppercase transition-all ${viewMode === 'feed' ? 'bg-black text-white' : 'bg-white text-black hover:bg-gray-100'}`}
            >
              Global Feed 🌍
            </button>
          </div>
        </div>
        
        {viewMode === 'private' && (
          <div className="mb-12 p-6 border-4 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
            <h2 className="text-xl font-bold text-black mb-4 uppercase italic tracking-widest">Upload Video</h2>
            <div className="flex flex-col gap-4">
              <div className="flex gap-4">
                <input 
                  type="text" 
                  placeholder="Video Title..." 
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="flex-1 p-3 border-2 border-black font-bold text-black placeholder-black outline-none focus:bg-yellow-50"
                />
                <select 
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="p-3 border-2 border-black font-bold bg-white text-black"
                >
                  <option value="Other">Other</option>
                  <option value="Gaming">Gaming 🎮</option>
                  <option value="Tech">Tech 💻</option>
                  <option value="Vlog">Vlog 📸</option>
                </select>
              </div>

              <textarea 
                placeholder="Description (Optional)..." 
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="p-3 border-2 border-black font-bold text-black placeholder-black outline-none focus:bg-yellow-50 h-20 resize-none"
              />
              
              <div className="flex flex-col md:flex-row gap-4 items-end justify-between">
                  <div className="flex-1 w-full">
                    <input 
                      type="file" 
                      accept="video/*" 
                      onChange={(e) => setFile(e.target.files?.[0] || null)} 
                      className="w-full p-2 border-2 border-black bg-gray-100 text-black font-bold file:bg-black file:text-white file:border-0 file:px-4 file:mr-4 file:font-black cursor-pointer" 
                    />
                  </div>

                  <div className="flex items-center gap-2 border-2 border-black p-2 bg-yellow-100">
                    <input 
                      type="checkbox" 
                      id="shareToggle"
                      checked={isShared}
                      onChange={(e) => setIsShared(e.target.checked)}
                      className="w-5 h-5 accent-black"
                    />
                    <label htmlFor="shareToggle" className="font-black text-xs uppercase cursor-pointer text-black">Share to Feed? 🌍</label>
                  </div>

                  <button 
                    onClick={handleUpload} 
                    disabled={!file || !title || isUploading}
                    className={`px-8 py-3 border-2 border-black font-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] active:translate-y-1 active:shadow-none transition-all ${
                      isUploading ? "bg-gray-400 text-black" : "bg-blue-600 text-white hover:bg-blue-700"
                    }`}
                  >
                    {isUploading ? "UPLOADING..." : "PROCESS"}
                  </button>
              </div>
            </div>
          </div>
        )}

        <h3 className="text-2xl font-black mb-6 border-b-4 border-black inline-block pr-8 text-black">
          {viewMode === 'private' ? 'MY LIBRARY' : 'COMMUNITY FEED'}
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {videos.length === 0 && (
            <p className="text-black font-bold italic col-span-full text-center py-10">No videos found here yet.</p>
          )}

          {videos.map((v) => (
            <div key={v.id} className="bg-white border-4 border-black p-5 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-1 transition-all flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-2">
                   <span className="text-[10px] font-black bg-gray-200 text-black px-2 py-1 border border-black uppercase">{v.category || "Other"}</span>
                   <span className={`text-[10px] font-black px-2 py-1 border border-black uppercase text-black ${
                      v.status === 'completed' ? 'bg-green-400' : 
                      v.status === 'failed' ? 'bg-red-500 text-white' : 'bg-yellow-300 animate-pulse'
                    }`}>{v.status}</span>
                </div>

                <h4 className="text-xl font-black text-black leading-tight mb-1 truncate">{v.title}</h4>
                <p className="text-xs font-bold text-black line-clamp-2 mb-4 min-h-[2.5rem]">
                  {v.description || "No description provided."}
                </p>

                <div className="flex flex-col gap-1 text-[10px] font-bold text-black border-t-2 border-dashed border-gray-300 pt-2">
                   <p>SIZE: {(v.file_size / (1024 * 1024)).toFixed(1)} MB</p>
                   <p>DATE: {new Date(v.created_at).toLocaleDateString()}</p>
                   {v.is_shared && viewMode === 'private' && <p className="text-blue-600">🌍 PUBLIC</p>}
                </div>
              </div>
              
              <div className="flex items-center justify-between mt-4 pt-4 border-t-2 border-black">
                {(viewMode === 'private' || isAdmin) && (
                   <button onClick={() => handleDelete(v.id)} className="text-xs font-black text-red-600 hover:bg-red-50 px-2 py-1 transition-colors uppercase">DELETE</button>
                )}
                
                {v.status === 'completed' && (
                  <button 
                    onClick={() => setSelectedVideoUrl(`http://localhost:9000/processed-videos/${v.s3_key}`)}
                    className="ml-auto bg-black text-white px-6 py-2 text-xs font-black border-2 border-black shadow-[2px_2px_0px_0px_rgba(100,100,100,1)] hover:shadow-none hover:translate-y-[2px] transition-all"
                  >
                    PLAY ▶
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedVideoUrl && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
          <div className="relative w-full max-w-5xl border-4 border-white shadow-[0px_0px_50px_rgba(255,255,255,0.2)] bg-black">
            <button 
              onClick={() => setSelectedVideoUrl(null)} 
              className="absolute -top-12 right-0 text-white font-black text-xl hover:text-red-500 transition-colors"
            >
              CLOSE [X]
            </button>
            <video key={selectedVideoUrl} controls autoPlay className="w-full h-auto max-h-[80vh]">
              <source src={selectedVideoUrl} type="video/mp4" />
            </video>
          </div>
        </div>
      )}
    </div>
  );
}