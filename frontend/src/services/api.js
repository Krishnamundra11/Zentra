import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Auth ──────────────────────────────────────────────────────────────────────
export const register = (email, password) =>
  api.post("/auth/register", { email, password });

export const login = (email, password) =>
  api.post(
    "/auth/login",
    new URLSearchParams({ username: email, password }),
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  );

// ── Recognition ───────────────────────────────────────────────────────────────
export const uploadImage = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/recognition/upload", form);
};

export const getRecognitionStatus = (taskId) =>
  api.get(`/recognition/${taskId}`);

export const openProgressSocket = (taskId, onEvent) => {
  const wsBase = BASE_URL.replace(/^http/, "ws");
  const ws = new WebSocket(`${wsBase}/recognition/ws/${taskId}`);
  ws.onmessage = (msg) => {
    try { onEvent(JSON.parse(msg.data)); } catch {}
  };
  return ws;
};

// ── Agent ─────────────────────────────────────────────────────────────────────
export const startAgent = (payload) => api.post("/agent/start", payload);

export const getAgentStatus = (taskId) =>
  api.get(`/agent/${taskId}/status`);

export const getItinerary = (taskId) =>
  api.get(`/agent/itinerary/${taskId}`);

// ── Recommendations ───────────────────────────────────────────────────────────
export const getAttractions = (placeId, lat, lng) =>
  api.get("/recommend/attractions", { params: { place_id: placeId, lat, lng } });

export const getHotels = (placeId, lat, lng, budget) =>
  api.get("/recommend/hotels", { params: { place_id: placeId, lat, lng, budget } });

export const getFood = (placeId, lat, lng, diet) =>
  api.get("/recommend/food", { params: { place_id: placeId, lat, lng, diet } });

export default api;
