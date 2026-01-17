"use client";
import { useEffect, useState } from "react";
import Navbar from "@/app/components/Navbar";
import { ApiService } from "@/lib/services"; 
import AISidebar from "@/app/components/AISidebar"; 

export default function PublicFeed() {
  const [videos, setVideos] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [loading, setLoading] = useState(false);
  const [playingUrl, setPlayingUrl] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false); 
  const categories = ["All", "Tech", "Gaming", "Music", "Other"];
  const [activeSummaryVideo, setActiveSummaryVideo] = useState<{title: string, summary: string} | null>(null);

  useEffect(() => {
    const checkAdminStatus = async () => {
      const token = localStorage.getItem("storagex_token");
      if (!token) return;
      try {
        const res = await ApiService.getAllVideosAdmin();
        setIsAdmin(res.ok);
      } catch (err) { setIsAdmin(false); }
    };
    checkAdminStatus();
  }, []);

  useEffect(() => {
    const fetchVideos = async () => {
      setLoading(true);
      try {
        const res = await ApiService.searchVideos(search, category);
        if (res.ok) setVideos(await res.json());
      } catch (e) { console.error("Search failed", e); } 
      finally { setLoading(false); }
    };
    const timeout = setTimeout(fetchVideos, 500);
    return () => clearTimeout(timeout);
  }, [search, category]);

  const handlePlay = async (videoId: string) => {
    try {
      const res = await ApiService.getPlayUrl(videoId);
      if (res.ok) {
        const data = await res.json();
        setPlayingUrl(data.url); 
      } else { alert("Login required to play."); }
    } catch (err) { console.error(err); }
  };

  const handleDownload = async (videoId: string) => {
    try {
      const res = await ApiService.getPlayUrl(videoId);
      if (res.ok) {
        const data = await res.json();
        window.open(data.url, "_blank"); 
      }
    } catch (err) { console.error(err); }
  };

  return (
    <div className="min-h-screen bg-white font-sans text-black relative">
      <Navbar videos={videos} isAdmin={isAdmin} />
      
      <AISidebar 
        isOpen={!!activeSummaryVideo} 
        onClose={() => setActiveSummaryVideo(null)} 
        video={activeSummaryVideo} 
      />

      {playingUrl && (
        <div className="fixed inset-0 z-50 bg-black/90 flex flex-col items-center justify-center p-4 backdrop-blur-sm">
          <button onClick={() => setPlayingUrl(null)} className="absolute top-8 right-8 text-white text-4xl font-bold hover:text-red-500 transition-colors">✕</button>
          <video src={playingUrl} controls autoPlay className="max-w-full max-h-[80vh] border-4 border-white shadow-[0px_0px_50px_rgba(255,255,255,0.3)]" />
        </div>
      )}

      <div className="max-w-6xl mx-auto px-8 py-10">
        <h1 className="text-5xl font-black mb-8 uppercase tracking-tighter">Public Gallery</h1>
        
        <div className="flex flex-col md:flex-row gap-4 mb-12">
          <input type="text" placeholder="Search videos..." className="flex-1 border-4 border-black p-4 font-bold text-xl shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] focus:outline-none focus:translate-x-[2px] focus:translate-y-[2px] transition-all" value={search} onChange={(e) => setSearch(e.target.value)}/>
          <select className="border-4 border-black p-4 font-bold text-xl shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] cursor-pointer bg-white" value={category} onChange={(e) => setCategory(e.target.value)}>
            {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
          </select>
        </div>

        {loading ? (
          <div className="text-2xl font-black text-gray-400 animate-pulse text-center py-20">SEARCHING...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {videos.length === 0 ? (
               <div className="col-span-3 text-center text-gray-500 font-bold text-xl border-4 border-dashed border-gray-300 p-10">NO VIDEOS FOUND</div>
            ) : (
              videos.map((video) => (
                <div key={video.id} className="flex flex-col border-4 border-black p-4 bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-1 hover:shadow-[12px_12px_0px_0px_rgba(0,0,0,1)] transition-all">
                  <div className="flex justify-between items-start mb-4">
                    <span className="bg-gray-200 px-2 py-1 font-bold text-xs border-2 border-black uppercase">{video.category || "General"}</span>
                  </div>

                  <h3 className="text-2xl font-black leading-tight mb-2 truncate">{video.title}</h3>
                  <p className="text-gray-600 font-bold text-sm mb-4 line-clamp-2">{video.description || "No description provided."}</p>
                  
                  {video.summary && (
                    <div className="mb-6">
                      <button 
                        onClick={() => setActiveSummaryVideo({ title: video.title, summary: video.summary })}
                        className="w-full text-xs font-black py-2 border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-y-[2px] transition-all bg-indigo-200 hover:bg-indigo-300 text-black flex justify-center items-center gap-2"
                      >
                         ✨ VIEW AI INSIGHT
                      </button>
                    </div>
                  )}

                  <div className="flex justify-between items-center border-t-2 border-black pt-4 mt-auto">
                    <div className="text-xs font-bold text-gray-500">{new Date(video.created_at).toLocaleDateString()}</div>
                    {video.status === 'completed' && (
                      <div className="flex gap-2">
                        <button onClick={() => handleDownload(video.id)} className="bg-white border-2 border-black text-black px-3 py-2 font-bold hover:bg-gray-100 transition-colors shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-y-[2px]">SAVE</button>
                        <button onClick={() => handlePlay(video.id)} className="bg-black text-white px-4 py-2 font-black border-2 border-black hover:bg-blue-600 transition-colors shadow-[2px_2px_0px_0px_rgba(100,100,100,1)] active:shadow-none active:translate-y-[2px]">PLAY ▶</button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}