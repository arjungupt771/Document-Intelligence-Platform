import { useCallback, useEffect, useState } from "react";
import { useApi } from "../lib/api.js";
import { useToast } from "../lib/ToastContext.jsx";
import DataTable from "../components/DataTable.jsx";
import InsightList from "../components/InsightList.jsx";

const PAGE_SIZE = 20;

export default function InsightsPage() {
  const api = useApi();
  const toast = useToast();

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [offset, setOffset] = useState(0);
  const [severity, setSeverity] = useState("");
  const [type, setType] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.insights.list({
        severity: severity || undefined,
        insight_type: type || undefined,
        limit: PAGE_SIZE,
        offset,
      });
      setRows(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [api, severity, type, offset]);

  useEffect(() => { load(); }, [load]);

  const columns = [
    { key: "title", label: "Title", sortable: true },
    { key: "type", label: "Type", sortable: true, render: (r) => <span className="badge slate">{r.type}</span> },
    {
      key: "severity", label: "Severity", sortable: true,
      render: (r) => <span className={"badge " + (r.severity === "high" || r.severity === "critical" ? "rust" : r.severity === "medium" ? "amber" : "green")}>{r.severity}</span>,
    },
    { key: "confidence", label: "Confidence", sortable: true, mono: true, render: (r) => (r.confidence * 100).toFixed(0) + "%" },
    { key: "priority_score", label: "Priority", sortable: true, mono: true, render: (r) => r.priority_score != null ? r.priority_score.toFixed(2) : "—" },
  ];

  // Compare
  const [docA, setDocA] = useState("");
  const [docB, setDocB] = useState("");
  const [comparing, setComparing] = useState(false);
  const [compareResults, setCompareResults] = useState(null);

  async function runCompare() {
    if (!docA.trim() || !docB.trim()) { toast.err("Enter both document IDs."); return; }
    setComparing(true);
    try {
      const data = await api.insights.compare(docA.trim(), docB.trim());
      setCompareResults(data);
      toast.ok(`${data.length} insight(s).`);
    } catch (e) { toast.err(e.message); } finally { setComparing(false); }
  }

  // Trend
  const [trendType, setTrendType] = useState("invoice");
  const [trending, setTrending] = useState(false);
  const [trendResults, setTrendResults] = useState(null);

  async function runTrend() {
    setTrending(true);
    try {
      const data = await api.insights.trend(trendType);
      setTrendResults(data);
      toast.ok(`${data.length} insight(s).`);
    } catch (e) { toast.err(e.message); } finally { setTrending(false); }
  }

  return (
    <div className="page-fade">
      <div className="view-head"><div className="view-head-text">
        <h1>Insights</h1>
        <p className="lede">Analyst-generated risk, anomaly, and financial insights across all documents.</p>
      </div></div>

      <section className="panel">
        <h2>All insights</h2>
        <div className="filter-bar">
          <div className="field">
            <label>Severity</label>
            <select value={severity} onChange={(e) => { setSeverity(e.target.value); setOffset(0); }}>
              <option value="">any</option>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="critical">critical</option>
            </select>
          </div>
          <div className="field">
            <label>Type</label>
            <select value={type} onChange={(e) => { setType(e.target.value); setOffset(0); }}>
              <option value="">any</option>
              <option value="completeness">completeness</option>
              <option value="financial">financial</option>
              <option value="anomaly">anomaly</option>
              <option value="risk">risk</option>
              <option value="cross_document">cross_document</option>
              <option value="trend">trend</option>
            </select>
          </div>
          <button className="ghost" onClick={load}>Refresh</button>
        </div>
        <DataTable
          columns={columns}
          rows={rows}
          getRowKey={(r) => r.id}
          loading={loading}
          error={error}
          emptyMessage="No insights match these filters."
          pagination={{
            offset,
            hasMore: rows.length === PAGE_SIZE,
            onPrev: () => setOffset((o) => Math.max(0, o - PAGE_SIZE)),
            onNext: () => setOffset((o) => o + PAGE_SIZE),
          }}
        />
      </section>

      <section className="panel">
        <h2>Compare two documents</h2>
        <div className="row">
          <div className="field"><label>Document A</label><input type="text" value={docA} onChange={(e) => setDocA(e.target.value)} placeholder="uuid" /></div>
          <div className="field"><label>Document B</label><input type="text" value={docB} onChange={(e) => setDocB(e.target.value)} placeholder="uuid" /></div>
        </div>
        <button className="action" onClick={runCompare} disabled={comparing}>{comparing ? <span className="spinner" /> : <span>Compare</span>}</button>
        {compareResults && <div style={{ marginTop: 16 }}><InsightList insights={compareResults} /></div>}
      </section>

      <section className="panel">
        <h2>Trend by document type</h2>
        <div className="row">
          <div className="field">
            <label>Document type</label>
            <select value={trendType} onChange={(e) => setTrendType(e.target.value)}>
              <option value="invoice">invoice</option>
              <option value="purchase_order">purchase_order</option>
              <option value="contract">contract</option>
            </select>
          </div>
        </div>
        <button className="action" onClick={runTrend} disabled={trending}>{trending ? <span className="spinner" /> : <span>Analyze trend</span>}</button>
        {trendResults && <div style={{ marginTop: 16 }}><InsightList insights={trendResults} /></div>}
      </section>
    </div>
  );
}
