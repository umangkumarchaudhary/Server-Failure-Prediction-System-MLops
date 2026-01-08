import axios from "axios";

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || "/api/v1",
    headers: {
        "Content-Type": "application/json",
    },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
        const token = localStorage.getItem("access_token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
});

// Handle 401 errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && typeof window !== "undefined") {
            localStorage.removeItem("access_token");
            window.location.href = "/login";
        }
        return Promise.reject(error);
    }
);

// Auth
export const authApi = {
    getMe: () => api.get("/auth/me"),
};

// Assets
export const assetsApi = {
    list: (params?: { skip?: number; limit?: number; type?: string; risk_level?: string }) =>
        api.get("/assets", { params }),
    get: (id: string) => api.get(`/assets/${id}`),
    create: (data: { name: string; type: string; tags?: string[]; location?: string }) =>
        api.post("/assets", data),
    update: (id: string, data: Partial<{ name: string; type: string; tags: string[]; location: string }>) =>
        api.put(`/assets/${id}`, data),
    delete: (id: string) => api.delete(`/assets/${id}`),
};

// Predictions
export const predictionsApi = {
    getForAsset: (assetId: string, limit?: number) =>
        api.get(`/predictions/asset/${assetId}`, { params: { limit } }),
    get: (id: string) => api.get(`/predictions/${id}`),
    getExplanation: (id: string) => api.get(`/predictions/${id}/explain`),
};

// Alerts
export const alertsApi = {
    list: (params?: { skip?: number; limit?: number; status?: string; severity?: string }) =>
        api.get("/alerts", { params }),
    get: (id: string) => api.get(`/alerts/${id}`),
    update: (id: string, data: { status: string }) => api.patch(`/alerts/${id}`, data),
};

// Dashboard
export const dashboardApi = {
    getStats: () => api.get("/dashboard/stats"),
};

export default api;
