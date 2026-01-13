"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiService } from "@/lib/services";
import Navbar from "@/app/components/Navbar";

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("videos"); 
  const [videos, setVideos] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const loadData = async () => {
      try {
        const token = localStorage.getItem("storagex_token");
        if (!token) return router.push("/login");

        const vidRes = await ApiService.getAllVideosAdmin();
        if (vidRes.ok) setVideos(await vidRes.json());
        else router.push("/");

        const userRes = await ApiService.adminGetUsers();
        if (userRes.ok) setUsers(await userRes.json());

      } catch (err) {
        console.error("Admin load error:", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [router]);

  const handleDeleteVideo = async (id: string) => {
    if(!confirm("Are you sure? This deletes files from S3 too.")) return;
    await ApiService.deleteVideo(id);
    setVideos(videos.filter(v => v.id !== id));
  };

  const handleDeleteUser = async (id: number) => {
    if(!confirm("Ban this user permanently?")) return;
    await ApiService.adminDeleteUser(id);
    setUsers(users.filter(u => u.id !== id));
  };

  const handlePromoteUser = async (id: number) => {
    await ApiService.adminPromoteUser(id);
    setUsers(users.map(u => u.id === id ? {...u, is_admin: true} : u));
    alert("User is now an Admin.");
  };

  if (loading) return <div className="p-10 text-xl font-bold">Loading Admin Panel...</div>;

  return (
    <div className="min-h-screen bg-gray-100 font-sans text-black">
      <Navbar videos={[]} isAdmin={true} />

      <main className="max-w-7xl mx-auto px-8 py-10">
        <h1 className="text-4xl font-black mb-8 uppercase border-b-4 border-black pb-4">
           🛡️ Admin Dashboard
        </h1>

        <div className="flex gap-4 mb-8">
          <button 
            onClick={() => setActiveTab("videos")}
            className={`px-6 py-3 font-bold text-xl border-4 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all ${activeTab === 'videos' ? 'bg-yellow-300 translate-x-[2px] translate-y-[2px] shadow-none' : 'bg-white hover:-translate-y-1'}`}
          >
            Manage Videos ({videos.length})
          </button>
          <button 
            onClick={() => setActiveTab("users")}
            className={`px-6 py-3 font-bold text-xl border-4 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all ${activeTab === 'users' ? 'bg-blue-300 translate-x-[2px] translate-y-[2px] shadow-none' : 'bg-white hover:-translate-y-1'}`}
          >
            Manage Users ({users.length})
          </button>
        </div>

        <div className="bg-white border-4 border-black p-8 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
          
          {activeTab === "videos" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b-4 border-black text-lg">
                    <th className="p-4">Title</th>
                    <th className="p-4">User Email</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Size</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {videos.map(v => (
                    <tr key={v.id} className="border-b-2 border-gray-200 hover:bg-gray-50">
                      <td className="p-4 font-bold">{v.title}</td>
                      <td className="p-4 font-mono text-sm text-gray-500">
                        {v.owner_email || v.owner_id}
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-1 text-xs border-2 border-black font-bold ${v.status === 'completed' ? 'bg-green-400' : 'bg-yellow-200'}`}>
                          {v.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-4 text-sm">{(v.file_size / 1024 / 1024).toFixed(2)} MB</td>
                      <td className="p-4 text-right">
                        <button 
                          onClick={() => handleDeleteVideo(v.id)}
                          className="bg-red-500 text-white px-4 py-1 font-bold border-2 border-black hover:bg-red-600 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-y-[2px] active:shadow-none"
                        >
                          DELETE
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "users" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b-4 border-black text-lg">
                    <th className="p-4">ID</th>
                    <th className="p-4">Email</th>
                    <th className="p-4">Role</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} className="border-b-2 border-gray-200 hover:bg-gray-50">
                      <td className="p-4 font-mono">{u.id}</td>
                      <td className="p-4 font-bold">{u.email}</td>
                      <td className="p-4">
                        {u.is_admin ? (
                          <span className="bg-purple-400 border-2 border-black px-2 py-1 font-bold text-white text-xs">ADMIN</span>
                        ) : (
                          <span className="bg-gray-200 border-2 border-black px-2 py-1 font-bold text-gray-600 text-xs">USER</span>
                        )}
                      </td>
                      <td className="p-4 text-right flex justify-end gap-2">
                        {!u.is_admin && (
                          <button 
                            onClick={() => handlePromoteUser(u.id)}
                            className="bg-blue-500 text-white px-3 py-1 font-bold border-2 border-black hover:bg-blue-600 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-y-[2px] active:shadow-none"
                          >
                            PROMOTE
                          </button>
                        )}
                        <button 
                          onClick={() => handleDeleteUser(u.id)}
                          className="bg-black text-white px-3 py-1 font-bold border-2 border-gray-800 hover:bg-gray-800 shadow-[2px_2px_0px_0px_rgba(100,100,100,1)] active:translate-y-[2px] active:shadow-none"
                        >
                          BAN
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
        </div>
      </main>
    </div>
  );
}