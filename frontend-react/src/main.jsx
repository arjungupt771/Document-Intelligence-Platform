import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import { ConnectionProvider } from "./lib/ConnectionContext.jsx";
import { ToastProvider } from "./lib/ToastContext.jsx";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConnectionProvider>
      <ToastProvider>
        <App />
      </ToastProvider>
    </ConnectionProvider>
  </React.StrictMode>
);
