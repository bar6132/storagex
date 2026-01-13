const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const getAuthHeader = (): Record<string, string> => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("storagex_token");
    return token ? { "Authorization": `Bearer ${token}` } : {};
  }
  return {};
};

export const ApiService = {
  async login(formData: FormData): Promise<Response> {
    const params = new URLSearchParams();
    formData.forEach((value, key) => {
      params.append(key, value.toString());
    });
    return await fetch(`${API_URL}/users/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(),
    });
  },

  async register(userData: object): Promise<Response> {
    return await fetch(`${API_URL}/users/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData),
    });
  },

  async getFeed(): Promise<Response> {
    return await fetch(`${API_URL}/videos/feed`, {
      method: "GET",
      headers: getAuthHeader(),
    });
  },

  async uploadVideo(
    file: File, 
    title: string, 
    description: string,    
    category: string,       
    isShared: boolean,      
    resolution: string
  ): Promise<Response> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title); 
    
    formData.append("description", description);
    formData.append("category", category);
    formData.append("is_shared", isShared.toString());
    
    formData.append("resolution", resolution);

    return await fetch(`${API_URL}/videos/upload`, {
      method: "POST",
      headers: getAuthHeader(),
      body: formData,
    });
  },

  async getMyVideos(): Promise<Response> {
    return await fetch(`${API_URL}/videos/my-videos`, {
      method: "GET",
      headers: getAuthHeader(),
    });
  },

  async deleteVideo(videoId: string): Promise<Response> {
    return await fetch(`${API_URL}/videos/${videoId}`, {
      method: "DELETE",
      headers: getAuthHeader(),
    });
  },

  async getAllVideosAdmin(): Promise<Response> {
    return await fetch(`${API_URL}/videos/admin/all`, {
      method: "GET",
      headers: getAuthHeader(),
    });
  },

  async adminGetUsers(): Promise<Response> {
    return await fetch(`${API_URL}/users/admin/users`, {
      method: "GET",
      headers: getAuthHeader(),
    });
  },

  async adminDeleteUser(userId: number): Promise<Response> {
    return await fetch(`${API_URL}/users/admin/users/${userId}`, {
      method: "DELETE",
      headers: getAuthHeader(),
    });
  },

  async adminPromoteUser(userId: number): Promise<Response> {
    return await fetch(`${API_URL}/users/admin/users/${userId}/make-admin`, {
      method: "PATCH",
      headers: getAuthHeader(),
    });
  },

async searchVideos(query: string, category: string): Promise<Response> {
    const params = new URLSearchParams();
    if (query) params.append("q", query);
    if (category && category !== "All") params.append("category", category);

    return await fetch(`${API_URL}/videos/search?${params.toString()}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
  },

  async getPlayUrl(videoId: string): Promise<Response> {
    return await fetch(`${API_URL}/videos/play/${videoId}`, {
      method: "GET",
      headers: getAuthHeader(), 
    });
  }
};

