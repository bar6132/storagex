const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// [FIX: SEC-001] getAuthHeader() removed — authentication is now handled via
// httpOnly cookies set by the backend. The browser sends them automatically on
// every request when credentials: "include" is specified.
// OLD:
// const getAuthHeader = (): Record<string, string> => {
//   if (typeof window !== "undefined") {
//     const token = localStorage.getItem("storagex_token");
//     return token ? { "Authorization": `Bearer ${token}` } : {};
//   }
//   return {};
// };

// [FIX: SEC-003] Central fetch wrapper with automatic 401 → refresh → retry flow.
// On any 401 response:
//   1. Calls /users/refresh (sends the refresh_token httpOnly cookie automatically).
//   2. If refresh succeeds → retries the original request (new access_token cookie is now set).
//   3. If refresh fails (expired/revoked) → redirects to /login.
// This replaces the need for any manual token management in components.
const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const res = await fetch(url, { ...options, credentials: "include" });

  if (res.status === 401) {
    const refreshRes = await fetch(`${API_URL}/users/refresh`, {
      method: "POST",
      credentials: "include",
    });

    if (refreshRes.ok) {
      // New access_token cookie has been set — retry the original request.
      return fetch(url, { ...options, credentials: "include" });
    }

    // Refresh token is also expired or invalid — full session over, go to login.
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  return res;
};

export const ApiService = {
  // [FIX: SEC-001] Login no longer stores the token in localStorage.
  // Backend sets httpOnly cookies via Set-Cookie headers — credentials: "include"
  // is required so the browser accepts and stores those cookies cross-origin.
  // OLD: localStorage.setItem("storagex_token", data.access_token) was done in login/page.tsx
  async login(formData: FormData): Promise<Response> {
    const params = new URLSearchParams();
    formData.forEach((value, key) => {
      params.append(key, value.toString());
    });
    return await fetch(`${API_URL}/users/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(),
      credentials: "include", // Required to receive the Set-Cookie headers from the backend
    });
  },

  async register(userData: object): Promise<Response> {
    return await fetch(`${API_URL}/users/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData),
      credentials: "include",
    });
  },

  // [FIX: SEC-001] New — returns current user info from the server.
  // Replaces the old pattern of localStorage.getItem + jwtDecode to identify the user.
  // Components call this on mount to check auth state and get user ID / isAdmin.
  async getMe(): Promise<Response> {
    return await fetchWithAuth(`${API_URL}/users/me`);
  },

  // [FIX: SEC-003] New — manually triggers a token refresh.
  // Normally called automatically by fetchWithAuth on 401. Exposed here for
  // explicit use if needed (e.g., proactive refresh before a long upload).
  async refreshToken(): Promise<Response> {
    return await fetch(`${API_URL}/users/refresh`, {
      method: "POST",
      credentials: "include",
    });
  },

  // [FIX: SEC-001] New — clears both auth cookies on logout via the server.
  // httpOnly cookies cannot be deleted by JavaScript, so the backend must do it.
  // OLD: logout was handled by localStorage.removeItem("storagex_token") in Navbar.tsx
  async logout(): Promise<Response> {
    return await fetch(`${API_URL}/users/logout`, {
      method: "POST",
      credentials: "include",
    });
  },

  async getFeed(): Promise<Response> {
    // OLD: headers: getAuthHeader()
    return await fetchWithAuth(`${API_URL}/videos/feed`);
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

    // OLD: headers: getAuthHeader()
    return await fetchWithAuth(`${API_URL}/videos/upload`, {
      method: "POST",
      body: formData,
    });
  },

  async getMyVideos(): Promise<Response> {
    // OLD: headers: getAuthHeader()
    return await fetchWithAuth(`${API_URL}/videos/my-videos`);
  },

  async deleteVideo(videoId: string): Promise<Response> {
    // OLD: headers: getAuthHeader()
    return await fetchWithAuth(`${API_URL}/videos/${videoId}`, {
      method: "DELETE",
    });
  },

  async getAllVideosAdmin(): Promise<Response> {
    // OLD: headers: getAuthHeader()
    return await fetchWithAuth(`${API_URL}/videos/admin/all`);
  },

  async adminGetUsers(): Promise<Response> {
    // OLD: headers: getAuthHeader()
    return await fetchWithAuth(`${API_URL}/users/admin/users`);
  },

  async adminDeleteUser(userId: number): Promise<Response> {
    // OLD: headers: getAuthHeader()
    return await fetchWithAuth(`${API_URL}/users/admin/users/${userId}`, {
      method: "DELETE",
    });
  },

  async adminPromoteUser(userId: number): Promise<Response> {
    // OLD: headers: getAuthHeader()
    return await fetchWithAuth(`${API_URL}/users/admin/users/${userId}/make-admin`, {
      method: "PATCH",
    });
  },

  async searchVideos(query: string, category: string): Promise<Response> {
    const params = new URLSearchParams();
    if (query) params.append("q", query);
    if (category && category !== "All") params.append("category", category);

    return await fetch(`${API_URL}/videos/search?${params.toString()}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });
  },

  async getPlayUrl(videoId: string): Promise<Response> {
    // OLD: headers: getAuthHeader()
    return await fetchWithAuth(`${API_URL}/videos/play/${videoId}`);
  },

  async generateSummary(videoId: string, force: boolean = false): Promise<Response> {
    // OLD: headers: getAuthHeader()
    return await fetchWithAuth(`${API_URL}/videos/${videoId}/summarize?force=${force}`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },
};
