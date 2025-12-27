"use client";
import { useState } from "react";
import { ApiService } from "@/lib/services";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await ApiService.register({ email, password });
      if (res.ok) {
        alert("Account created! Please login.");
        router.push("/login");
      } else {
        const errorData = await res.json();
        alert(`Registration failed: ${errorData.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="w-full max-w-md p-8 border-2 border-black rounded-xl shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
        <h1 className="text-3xl font-black text-black mb-6 text-center">CREATE ACCOUNT</h1>
        
        <form onSubmit={handleRegister} className="flex flex-col gap-4">
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
            className="w-full bg-blue-600 text-white font-bold py-3 rounded mt-4 hover:bg-blue-700 transition border-2 border-black"
          >
            REGISTER
          </button>
        </form>

        <p className="mt-6 text-center text-black font-medium">
          Already have an account?{" "}
          <Link href="/login" className="text-blue-700 underline font-bold">
            Login here
          </Link>
        </p>
      </div>
    </div>
  );
}