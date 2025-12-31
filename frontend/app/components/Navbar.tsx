"use client";
import Link from "next/link";
import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";

export default function Navbar({ videos = [], isAdmin = false }: { videos?: any[], isAdmin?: boolean }) {
  const [isMounted, setIsMounted] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    setIsMounted(true);
    setToken(localStorage.getItem("storagex_token"));
  }, []);

  const isLoggedIn = !!token;
  const storageLimit = 524288000; 

  const totalUsed = useMemo(() => {
    return videos.reduce((acc, v) => acc + (v.file_size || 0), 0);
  }, [videos]);

  const usageMB = (totalUsed / (1024 * 1024)).toFixed(1);
  const limitMB = (storageLimit / (1024 * 1024)).toFixed(0);
  const percent = Math.min((totalUsed / storageLimit) * 100, 100);

  const handleLogout = () => {
    localStorage.removeItem("storagex_token");
    setToken(null);
    router.push("/");
  };

  if (!isMounted) return (
    <nav className="w-full border-b-4 border-black bg-white py-4 px-8 sticky top-0 z-50">
      <div className="text-2xl font-black text-black">STORAGE<span className="text-blue-600">X</span></div>
    </nav>
  );

  return (
    <nav className="w-full border-b-4 border-black bg-white py-4 px-8 flex justify-between items-center sticky top-0 z-50">
      <Link href="/" className="text-2xl font-black text-black tracking-tighter hover:opacity-80">
        STORAGE<span className="text-blue-600">X</span>
      </Link>

      <div className="flex gap-6 items-center">
        {isLoggedIn && !isAdmin && (
          <div className="hidden md:flex flex-col w-48 mx-4">
            <div className="flex justify-between text-[10px] font-black mb-1 text-black uppercase">
              <span>Cloud Usage</span>
              <span>{usageMB}MB / {limitMB}MB</span>
            </div>
            <div className="h-3 w-full border-2 border-black bg-white overflow-hidden shadow-[1px_1px_0px_0px_rgba(0,0,0,1)]">
              <div 
                className={`h-full border-r-2 border-black transition-all duration-700 ${
                  percent > 90 ? 'bg-red-500' : 'bg-blue-500'
                }`}
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        )}

        {isLoggedIn && isAdmin && (
           <div className="hidden md:flex items-center mx-4 bg-yellow-400 border-2 border-black px-2 py-1 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
              <span className="text-[10px] font-black uppercase tracking-widest text-black">UNLIMITED ACCESS</span>
           </div>
        )}

        <div className="flex gap-4 items-center">
          {isLoggedIn ? (
            <>
              <Link href="/dashboard" className="text-black font-bold hover:underline">DASHBOARD</Link>
              <button onClick={handleLogout} className="bg-red-500 text-white px-4 py-2 border-2 border-black font-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-y-1 active:shadow-none transition-all">
                LOGOUT
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-black font-bold hover:underline">LOGIN</Link>
              <Link href="/register" className="bg-black text-white px-4 py-2 border-2 border-black font-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-y-1 active:shadow-none transition-all">
                SIGN UP
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}