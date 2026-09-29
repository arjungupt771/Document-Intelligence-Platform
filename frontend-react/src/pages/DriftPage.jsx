import { useCallback, useEffect, useState } from "react";
import { useApi } from "../lib/api.js";
import { useToast } from "../lib/ToastContext.jsx";
import DataTable from "../components/DataTable.jsx";

const PAGE_SIZE = 20;

export default function DriftPage() {
  const api = useApi();
  const toast = useToast();

  const [docType, setDocType] = useState("invoice");
  const [establishing, setEstablishing] = useState(false);
  const [checking, setChecking] = useState(false);

  const [results, setResults] = useState([]);
  const [loadingResults, setLoadingResults] = useState(true);
  const [resultsError, setResultsError] = useState(null);

  const [alerts, setAlerts] = useState([]);
  const [loadingAlerts, setLoadingAlerts] = useState(true);

  const loadResults = useCallback(async () => {
    setLoadingResults(true);
    setResultsError(null);
    try {
      setResults(await api.drift.results({ limit: PAGE_SIZE }));
    } catch (e) {
      setResultsError(e.message);
    } finally {
      setLoadingResults(false);
    }
  }, [api]);

  const loadAlerts = useCallback(async () => {
    setLoadingAlerts(true);
    try {
      setAlerts(await api.drift.alerts());
    } catch (e) {
      toast.err(e.message);
    } finally {
      setLoadingAlerts(false);
    }
  }, [api, toast]);

  useEffect(() => { loadResults(); loadAlerts(); }, [loadResults, loadAlerts]);

  async function establish() {
    setEstablishing(true);
    try {
      const data = await api.drift.baseline(docType);
      toast[data.established ? "ok" : "err"](data.established ? "Baseline established." : "No completed extractions found for this type.");
    } catch (e) { toast.err(e.message); } finally { setEstablishing(false); }
  }

  async function check() {
    setChecking(true);
    try {
      await api.drift.check(docType);
      toast.ok("Drift check complete.");
      loadResults();
      loadAlerts();
    } catch (e) { toast.err(e.message); } finally { setChecking(false); }
  }

  async function acknowledge(alertId) {
    try {
      await api.drift.acknowledge(alertId);
      toast.ok("Alert acknowledged.");
      loadAlerts();
    } catch (e) { toast.err(e.message); }
  }

  const severityRank = { none: 0, moderate: 1, significant: 2 };
  const resultColumns = [
    { key: "dimension", label: "Dimension", sortable: true },
    { key: "key", label: "Key", mono: true, sortable: true },
    {
      key: "score", label: "Score", sortable: true,
      render: (r) => {
        const pct = Math.min(100, Math.round(r.score * 200));
        return (
          <div className="drift-bar-row">
            <div className="drift-bar"><span className={r.severity} style={{ width: pct + "%" }} /></div>
            <span className="mono" style={{ fontSize: 11 }}>{r.score}</span>
          </div>
        );
      },
    },
    {
      key: "severity", label: "Severity", sortable: true,
      render: (r) => <span className={"badge " + (r.severity === "none" ? "green" : r.severity === "moderate" ? "amber" : "rust")}>{r.severity}</span>,
    },
  ];
  // client-side severity ordering helper used implicitly via sort on string; good enough given the small enum set

  return (
    <div className="page-fade">
      <div className="view-head"><div className="view-head-text">
        <h1>Drift</h1>
        <p className="lede">Baseline and monitor extraction/retrieval quality over time.</p>
      </div></div>

      <section className="panel">
        <h2>Baseline &amp; check</h2>
        <div className="row">
          <div className="field">
            <label>Document type</label>
            <select value={docType} onChange={(e) => setDocType(e.target.value)}>
              <option value="invoice">invoice</option>
              <option value="purchase_order">purchase_order</option>
              <option value="contract">contract</option>
            </select>
          </div>
        </div>
        <div className="btn-group">
          <button className="action" onClick={establish} disabled={establishing}>
            {establishing ? <span className="spinner" /> : <span>Establish baseline</span>}
          </button>
          <button className="ghost" onClick={check} disabled={checking}>{checking ? "Checking..." : "Run drift check"}</button>
        </div>
      </section>

      <section className="panel">
        <h2>Recent drift results</h2>
        <DataTable
          columns={resultColumns}
          rows={results}
          getRowKey={(r) => r.dimension + r.key + r.score}
          loading={loadingResults}
          error={resultsError}
          emptyMessage="No drift results yet — run a check above."
        />
      </section>

      <section className="panel">
        <h2>Open alerts</h2>
        <button className="ghost" onClick={loadAlerts} style={{ marginBottom: 14 }}>Refresh</button>
        {loadingAlerts ? (
          <div className="empty">Loading…</div>
        ) : !alerts.length ? (
          <div className="empty">No open alerts.</div>
        ) : (
          alerts.map((a) => (
            <div key={a.id} className="insight-card high">
              <div className="title">{a.message}</div>
              <div className="meta-row">{new Date(a.created_at).toLocaleString()}</div>
              <button className="ghost small" style={{ marginTop: 10 }} onClick={() => acknowledge(a.id)}>Acknowledge</button>
            </div>
          ))
        )}
      </section>
    </div>
  );
}
