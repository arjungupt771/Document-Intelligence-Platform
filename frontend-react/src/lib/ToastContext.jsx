import { createContext, useCallback, useContext, useRef, useState } from "react";

const ToastContext = createContext(null);
let nextId = 1;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timers = useRef({});

  const dismiss = useCallback((id) => {
    setToasts((t) => t.filter((toast) => toast.id !== id));
    clearTimeout(timers.current[id]);
    delete timers.current[id];
  }, []);

  const push = useCallback((kind, text) => {
    const id = nextId++;
    setToasts((t) => [...t, { id, kind, text }]);
    timers.current[id] = setTimeout(() => dismiss(id), 4200);
  }, [dismiss]);

  const api = {
    ok: (text) => push("ok", text),
    err: (text) => push("err", text),
  };

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div id="toast-stack">
        {toasts.map((t) => (
          <div key={t.id} className={"toast " + t.kind} onClick={() => dismiss(t.id)}>
            <span className="dot-icon" />
            <span>{t.text}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
