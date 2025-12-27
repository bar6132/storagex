"use client";
import { useEffect, useState } from "react";
import { ApiService } from "@/lib/services";
import Navbar from "@/app/components/Navbar";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<any[]>([]);

  useEffect(() => { fetchUsers(); }, []);

  const fetchUsers = async () => {
    const res = await ApiService.adminGetUsers(); 
    if (res.ok) setUsers(await res.json());
  };

  const handleDeleteUser = async (id: number) => {
    if (!confirm("Delete this user and ALL their data?")) return;
    const res = await ApiService.adminDeleteUser(id);
    if (res.ok) fetchUsers();
  };

  const handleMakeAdmin = async (id: number) => {
    const res = await ApiService.adminPromoteUser(id);
    if (res.ok) fetchUsers();
  };

  return (
    <div className="min-h-screen bg-white text-black">
      <Navbar />
      <div className="max-w-6xl mx-auto p-8">
        <h1 className="text-4xl font-black mb-8 underline decoration-blue-500">USER MANAGEMENT</h1>
        
        <div className="border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-black text-white">
              <tr>
                <th className="p-4 border-r border-white">ID</th>
                <th className="p-4 border-r border-white">EMAIL</th>
                <th className="p-4 border-r border-white">ROLE</th>
                <th className="p-4">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b-2 border-black hover:bg-gray-50">
                  <td className="p-4 font-bold border-r border-black">{u.id}</td>
                  <td className="p-4 font-bold border-r border-black">{u.email}</td>
                  <td className="p-4 border-r border-black">
                    <span className={`px-2 py-1 font-black text-xs border-2 border-black ${u.is_admin ? 'bg-green-400' : 'bg-gray-200'}`}>
                      {u.is_admin ? "ADMIN" : "USER"}
                    </span>
                  </td>
                  <td className="p-4 flex gap-4">
                    {!u.is_admin && (
                      <button onClick={() => handleMakeAdmin(u.id)} className="text-blue-600 font-black hover:underline">MAKE ADMIN</button>
                    )}
                    <button onClick={() => handleDeleteUser(u.id)} className="text-red-600 font-black hover:underline">DELETE USER</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}