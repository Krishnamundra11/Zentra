import { create } from "zustand";

const useStore = create((set, get) => ({
  // ── Auth ──────────────────────────────────────────────────────────────────
  user:        null,
  accessToken: localStorage.getItem("access_token") || null,

  setAuth: (user, token) => {
    localStorage.setItem("access_token", token);
    set({ user, accessToken: token });
  },
  logout: () => {
    localStorage.removeItem("access_token");
    set({ user: null, accessToken: null });
  },

  // ── Recognition ───────────────────────────────────────────────────────────
  taskId:             null,
  recognitionStatus:  "idle",   // idle | pending | matched | likely | unknown
  recognitionResult:  null,
  wsEvents:           [],

  setTaskId: (id) => set({
    taskId: id,
    recognitionStatus: "pending",
    wsEvents: [],
    recognitionResult: null,
  }),

  setRecognitionResult: (result) => set({
    recognitionResult: result,
    recognitionStatus: result.status,
  }),

  appendWsEvent: (ev) => set((s) => ({ wsEvents: [...s.wsEvents, ev] })),

  // ── User Preferences ──────────────────────────────────────────────────────
  preferences: {
    budget:        "mid",
    travel_style:  "couple",
    duration_days: 3,
    diet:          "any",
    accessibility: false,
  },
  setPreferences: (prefs) =>
    set((s) => ({ preferences: { ...s.preferences, ...prefs } })),

  // ── Agent / Itinerary ─────────────────────────────────────────────────────
  agentTaskId:  null,
  agentStatus:  "idle",   // idle | running | completed | error
  itinerary:    null,

  setAgentTaskId: (id) => set({ agentTaskId: id, agentStatus: "running" }),
  setItinerary:   (data) => set({ itinerary: data, agentStatus: "completed" }),
  setAgentError:  (msg)  => set({ agentStatus: "error", agentError: msg }),
}));

export default useStore;
