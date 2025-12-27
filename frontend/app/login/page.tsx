"use client";
import { useState } from "react";
import { ApiService } from "@/lib/services";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);

    try {
      const res = await ApiService.login(formData);
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("storagex_token", data.access_token);
        router.push("/dashboard");
      } else {
        alert("Login failed! Check your credentials.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="w-full max-w-md p-8 border-2 border-black rounded-xl shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
        <h1 className="text-3xl font-black text-black mb-6 text-center">LOGIN</h1>
        
        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <div>
            <label className="block text-black font-bold mb-1">Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-3 border-2 border-black rounded text-black font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="user@example.com"
              required
            />
          </div>
          
          <div>
            <label className="block text-black font-bold mb-1">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 border-2 border-black rounded text-black font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="••••••••"
              required
            />
          </div>

          <button 
            type="submit" 
            className="w-full bg-black text-white font-bold py-3 rounded mt-4 hover:bg-gray-800 transition"
          >
            SIGN IN
          </button>
        </form>

        <p className="mt-6 text-center text-black font-medium">
          Don't have an account?{" "}
          <Link href="/register" className="text-blue-700 underline font-bold">
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}