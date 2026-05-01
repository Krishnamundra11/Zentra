import { useCallback, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { uploadImage, openProgressSocket } from "../services/api";
import useStore from "../store/useStore";

export function useRecognition() {
  const navigate    = useNavigate();
  const wsRef       = useRef(null);
  const {
    taskId,
    recognitionStatus,
    setTaskId,
    setRecognitionResult,
    appendWsEvent,
  } = useStore();

  const upload = useCallback(async (file) => {
    const { data } = await uploadImage(file);
    setTaskId(data.task_id);
    navigate(`/results/${data.task_id}`);
  }, [setTaskId, navigate]);

  useEffect(() => {
    if (!taskId || recognitionStatus !== "pending") return;

    const ws = openProgressSocket(taskId, (ev) => {
      appendWsEvent(ev);
      const { event, data } = ev;
      if (["matched", "likely", "unknown"].includes(event)) {
        setRecognitionResult({ ...data, status: event });
        ws.close();
      }
    });

    wsRef.current = ws;
    return () => ws?.close();
  }, [taskId]);

  return { upload };
}
