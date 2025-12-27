"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Navbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("storagex_token");
    setIsLoggedIn(!!token);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("storagex_token");
    setIsLoggedIn(false);
    router.push("/");
  };

  return (
    <nav className="w-full border-b-4 border-black bg-white py-4 px-8 flex justify-between items-center sticky top-0 z-50">
      <Link href="/" className="text-2xl font-black text-black tracking-tighter hover:opacity-80">
        STORAGE<span className="text-blue-600">X</span>
      </Link>

      <div className="flex gap-6 items-center">
        {isLoggedIn ? (
          <>
            <Link href="/dashboard" className="text-black font-bold hover:underline">
              DASHBOARD
            </Link>
            <button 
              onClick={handleLogout}
              className="bg-red-500 text-white px-4 py-2 border-2 border-black font-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-y-1 active:shadow-none transition-all"
            >
              LOGOUT
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className="text-black font-bold hover:underline">
              LOGIN
            </Link>
            <Link 
              href="/register" 
              className="bg-black text-white px-4 py-2 border-2 border-black font-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-y-1 active:shadow-none transition-all"
            >
              SIGN UP
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}