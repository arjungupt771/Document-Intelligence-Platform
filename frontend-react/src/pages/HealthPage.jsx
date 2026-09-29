import { useState } from "react";
import { useApi } from "../lib/api.js";
import { useConnection } from "../lib/ConnectionContext.jsx";
import { useToast } from "../lib/ToastContext.jsx";

export default function HealthPage() {
  const api = useApi();
  const { setStatus } = useConnection();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);

  async function check() {
    setLoading(true);
    try {
      const result = await api.health.ready();
      setData(result);
      setStatus(result.status);
      toast[result.status === "ready" ? "ok" : "err"]("Overall: " + result.status);
    } catch (e) {
      toast.err(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-fade">
      <div className="view-head"><div className="view-head-text">
        <h1>Health</h1>
        <p className="lede">Liveness and readiness of the API and its dependencies.</p>
      </div></div>

      <section className="panel">
        <button className="action" onClick={check} disabled={loading}>
          {loading ? <span className="spinner" /> : <span>Run health check</span>}
        </button>

        {data && (
          <table style={{ marginTop: 16 }}>
            <thead><tr><th>Component</th><th>Status</th><th>Latency</th><th>Detail</th></tr></thead>
            <tbody>
              {data.checks.map((c) => (
                <tr key={c.name}>
                  <td>{c.name}</td>
                  <td><span className={"badge " + (c.healthy ? "green" : "rust")}>{c.healthy ? "healthy" : "unhealthy"}</span></td>
                  <td className="mono">{c.latency_ms != null ? c.latency_ms + "ms" : "—"}</td>
                  <td>{c.detail || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
