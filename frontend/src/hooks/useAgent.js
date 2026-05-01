import { useCallback, useEffect, useRef } from "react";
import { startAgent, getAgentStatus, getItinerary } from "../services/api";
import useStore from "../store/useStore";

export function useAgent() {
  const { preferences, setAgentTaskId, setItinerary, agentStatus } = useStore();
  const pollRef = useRef(null);

  const launchAgent = useCallback(async (place) => {
    try {
      const { data } = await startAgent({
        place_id:     place.id,
        place_name:   place.name,
        country:      place.country  || "",
        city:         place.city     || "",
        lat:          place.lat      || 0,
        lng:          place.lng      || 0,
        budget:       preferences.budget,
        travel_style: preferences.travel_style,
        duration_days:preferences.duration_days,
        diet:         preferences.diet,
        accessibility:preferences.accessibility,
      });
      setAgentTaskId(data.task_id);
    } catch (err) {
      console.error("Failed to start agent:", err);
    }
  }, [preferences, setAgentTaskId]);

  // Poll agent status until completed
  const { agentTaskId } = useStore.getState();

  useEffect(() => {
    if (!agentTaskId || agentStatus === "completed") return;

    pollRef.current = setInterval(async () => {
      try {
        const { data: status } = await getAgentStatus(agentTaskId);
        if (status.status === "completed") {
          const { data: plan } = await getItinerary(agentTaskId);
          setItinerary(plan);
          clearInterval(pollRef.current);
        }
      } catch {
        // silently retry
      }
    }, 3000);

    return () => clearInterval(pollRef.current);
  }, [agentTaskId, agentStatus]);

  return { launchAgent };
}
