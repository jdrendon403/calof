import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { time as timeApi } from "../api/client";
import { useAuth } from "./AuthContext";

const TimeContext = createContext(null);

export function TimeProvider({ children }) {
  const { user } = useAuth();
  const [activeEntry, setActiveEntry] = useState(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef(null);

  const startTimeRef = useRef(null);

  const updateElapsed = useCallback(() => {
    if (startTimeRef.current)
      setElapsedSeconds(Math.floor((Date.now() - startTimeRef.current) / 1000));
  }, []);

  const fetchCurrent = useCallback(async () => {
    try {
      const res = await timeApi.current();
      if (res.active && res.entry) {
        setActiveEntry(res.entry);
        startTimeRef.current = new Date(res.entry.hora_inicio).getTime();
        updateElapsed();
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = setInterval(updateElapsed, 1000);
      } else {
        setActiveEntry(null);
        setElapsedSeconds(0);
        startTimeRef.current = null;
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch {
      setActiveEntry(null);
      setElapsedSeconds(0);
      startTimeRef.current = null;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, [updateElapsed]);

  useEffect(() => {
    if (user) {
      fetchCurrent();
    } else {
      setActiveEntry(null);
      setElapsedSeconds(0);
      startTimeRef.current = null;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [user, fetchCurrent]);

  const start = async (projectId) => {
    setLoading(true);
    try {
      const entry = await timeApi.start(projectId);
      setActiveEntry(entry);
      startTimeRef.current = new Date(entry.hora_inicio).getTime();
      setElapsedSeconds(0);
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(updateElapsed, 1000);
    } finally {
      setLoading(false);
    }
  };

  const stop = async () => {
    setLoading(true);
    try {
      await timeApi.stop();
      setActiveEntry(null);
      setElapsedSeconds(0);
      startTimeRef.current = null;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } finally {
      setLoading(false);
    }
  };

  const formatElapsed = (s) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return [h, m, sec].map((n) => String(n).padStart(2, "0")).join(":");
  };

  return (
    <TimeContext.Provider
      value={{
        activeEntry,
        elapsedSeconds,
        formatElapsed,
        start,
        stop,
        loading,
        refresh: fetchCurrent,
      }}
    >
      {children}
    </TimeContext.Provider>
  );
}

export function useTime() {
  const ctx = useContext(TimeContext);
  if (!ctx) throw new Error("useTime must be used within TimeProvider");
  return ctx;
}
