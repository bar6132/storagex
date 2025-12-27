const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const getAuthHeader = (): Record<string, string> => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("storagex_token");
    return token ? { "Authorization": `Bearer ${token}` } : {};
  }
  return {};
};

export const ApiService = {
  
  // async login(formData: FormData): Promise<Response> {
  //   return await fetch(`${API_URL}/token`, {
  //     method: "POST",
  //     body: formData, 
  //   });
  // },
  async login(formData: FormData): Promise<Response> {
  const params = new URLSearchParams();
  formData.forEach((value, key) => {
    params.append(key, value.toString());
  });

  return await fetch(`${API_URL}/users/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: params.toString(),
  });
  },

  async register(userData: object): Promise<Response> {
    return await fetch(`${API_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData),
    });
  },

  async uploadVideo(file: File, title: string): Promise<Response> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title); 

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

  async getJobStatus(jobId: string): Promise<Response> {
    return await fetch(`${API_URL}/videos/status/${jobId}`, {
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
  async adminDeleteUser(id: number): Promise<Response> {
    return await fetch(`${API_URL}/users/admin/users/${id}`, {
      method: "DELETE",
      headers: getAuthHeader(),
    });
  },
  async adminPromoteUser(id: number): Promise<Response> {
    return await fetch(`${API_URL}/users/admin/users/${id}/make-admin`, {
      method: "PATCH",
      headers: getAuthHeader(),
    });
  },

};

