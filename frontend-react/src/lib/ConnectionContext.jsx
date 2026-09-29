import { createContext, useContext, useState, useCallback } from "react";

const ConnectionContext = createContext(null);

// Default API base: set VITE_API_BASE at build time ("/api" behind the nginx
// proxy in Docker, "http://localhost:8000" for `npm run dev`). A value saved on
// the Connection page always wins.
const DEFAULT_BASE = (import.meta.env.VITE_API_BASE ?? "http://localhost:8000").replace(/\/$/, "");

export function ConnectionProvider({ children }) {
  const [base, setBaseState] = useState(() => localStorage.getItem("di_api_base") || DEFAULT_BASE);
  const [key, setKeyState] = useState(() => localStorage.getItem("di_api_key") || "");
  const [status, setStatus] = useState("not connected"); // "not connected" | "connected" | "unreachable" | "degraded"

  const setBase = useCallback((v) => {
    const trimmed = v.replace(/\/$/, "");
    localStorage.setItem("di_api_base", trimmed);
    setBaseState(trimmed);
  }, []);

  const setKey = useCallback((v) => {
    localStorage.setItem("di_api_key", v);
    setKeyState(v);
  }, []);

  const value = { base, key, setBase, setKey, status, setStatus };
  return <ConnectionContext.Provider value={value}>{children}</ConnectionContext.Provider>;
}

export function useConnection() {
  const ctx = useContext(ConnectionContext);
  if (!ctx) throw new Error("useConnection must be used within ConnectionProvider");
  return ctx;
}
