"use client";
import { useEffect, useState } from "react"; 
import { ApiService } from "@/lib/services"; 
import Navbar from "@/app/components/Navbar"; 
import Link from "next/link";

export default function HomePage() {
  const [videos, setVideos] = useState<any[]>([]);

  useEffect(() => {
    const token = localStorage.getItem("storagex_token");
    if (token) {
      ApiService.getMyVideos()
        .then((res) => {
          if (res.ok) return res.json();
        })
        .then((data) => {
          if (data) setVideos(data);
        })
        .catch((err) => console.error("Homepage fetch error:", err));
    }
  }, []);

  return (
    <div className="min-h-screen bg-white font-sans text-black">
      <Navbar videos={videos} />

      <main className="max-w-6xl mx-auto px-8 py-20 flex flex-col items-center text-center">
        <div className="mb-6 bg-yellow-300 border-2 border-black px-4 py-1 font-black text-sm uppercase shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
          Distributed Video Processing
        </div>
        
        <h1 className="text-6xl md:text-8xl font-black mb-8 leading-none">
          TRANSCODE AT <br />
          <span className="text-blue-600">LIGHT SPEED.</span>
        </h1>
        
        <p className="max-w-2xl text-xl font-bold mb-12 text-gray-800">
          Upload your high-res videos and let our distributed worker cluster 
          handle the heavy lifting. StorageX compresses, transcodes, and delivers.
        </p>

        <div className="flex flex-wrap gap-6 justify-center">
          <Link 
            href="/register" 
            className="text-2xl bg-blue-600 text-white px-10 py-5 border-4 border-black font-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-1 hover:shadow-[12px_12px_0px_0px_rgba(0,0,0,1)] transition-all active:translate-y-1 active:shadow-none"
          >
            GET STARTED FREE
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-32 w-full">
          {[
            { title: "FFMPEG POWERED", desc: "Professional grade transcoding engine." },
            { title: "S3 STORAGE", desc: "Secure, distributed object storage via MinIO." },
            { title: "RABBITMQ QUEUE", desc: "Asynchronous task processing for zero lag." }
          ].map((feature, i) => (
            <div key={i} className="p-8 border-4 border-black rounded-none bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] text-left">
              <h3 className="text-xl font-black mb-2">{feature.title}</h3>
              <p className="font-bold text-gray-700">{feature.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}