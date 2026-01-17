"use client";
import { useEffect } from "react";

interface AISidebarProps {
  isOpen: boolean;
  onClose: () => void;
  video: { title: string; summary: string } | null;
}

export default function AISidebar({ isOpen, onClose, video }: AISidebarProps) {
  useEffect(() => {
    if (isOpen) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "unset";
    return () => { document.body.style.overflow = "unset"; };
  }, [isOpen]);

  if (!isOpen || !video) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex justify-end font-sans">
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={onClose}
      />

      <div className="relative w-full md:max-w-md h-full bg-white border-l-4 border-black shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        
        <div className="flex items-start justify-between p-6 border-b-4 border-black bg-indigo-50">
           <div>
             <span className="inline-block px-2 py-1 mb-2 text-[10px] font-black text-white bg-indigo-600 uppercase tracking-widest border border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
               ✨ AI Analysis
             </span>
             <h2 className="text-2xl font-black text-black leading-tight">{video.title}</h2>
           </div>
           <button 
             onClick={onClose}
             className="ml-4 p-2 text-black hover:bg-red-500 hover:text-white transition-all border-2 border-transparent hover:border-black active:translate-y-1"
             title="Close"
           >
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={4} stroke="currentColor" className="w-6 h-6">
               <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
             </svg>
           </button>
        </div>

        <div className="p-8 overflow-y-auto flex-1 bg-white">
          <div className="prose prose-lg">
             <p className="text-lg font-medium text-gray-800 leading-relaxed whitespace-pre-wrap">
               {video.summary}
             </p>
          </div>
        </div>

        <div className="p-6 border-t-4 border-black bg-gray-100">
          <button 
            onClick={onClose}
            className="w-full py-4 bg-black text-white font-black uppercase tracking-widest hover:bg-gray-800 transition-colors border-2 border-black shadow-[4px_4px_0px_0px_rgba(255,255,255,1)]"
          >
            Close Insight
          </button>
        </div>
      </div>
    </div>
  );
}