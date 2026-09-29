import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import ConnectionPage from "./pages/ConnectionPage.jsx";
import DocumentsPage from "./pages/DocumentsPage.jsx";
import DocumentDetailPage from "./pages/DocumentDetailPage.jsx";
import AskPage from "./pages/AskPage.jsx";
import InsightsPage from "./pages/InsightsPage.jsx";
import DriftPage from "./pages/DriftPage.jsx";
import HealthPage from "./pages/HealthPage.jsx";

// HashRouter is used deliberately: this is served as static files (see the
// nginx snippet in the README) with no server-side rewrite rule for SPA
// routes. Hash-based routing needs no server config at all.
export default function App() {
  return (
    <HashRouter>
      <div className="shell">
        <Sidebar />
        <main>
          <Routes>
            <Route path="/" element={<Navigate to="/documents" replace />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/documents/:id" element={<DocumentDetailPage />} />
            <Route path="/ask" element={<AskPage />} />
            <Route path="/insights" element={<InsightsPage />} />
            <Route path="/drift" element={<DriftPage />} />
            <Route path="/health" element={<HealthPage />} />
            <Route path="/connection" element={<ConnectionPage />} />
            <Route path="*" element={<Navigate to="/documents" replace />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  );
}
