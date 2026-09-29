import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useApi } from "../lib/api.js";
import { useToast } from "../lib/ToastContext.jsx";
import InsightList from "../components/InsightList.jsx";

function formatBytes(n) {
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / (1024 * 1024)).toFixed(2) + " MB";
}

export default function DocumentDetailPage() {
  const { id } = useParams();
  const api = useApi();
  const toast = useToast();
  const navigate = useNavigate();

  const [doc, setDoc] = useState(null);
  const [loadingDoc, setLoadingDoc] = useState(true);
  const [docError, setDocError] = useState(null);

  const [insights, setInsights] = useState([]);
  const [loadingInsights, setLoadingInsights] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [processing, setProcessing] = useState(false);

  const loadDoc = useCallback(async () => {
    setLoadingDoc(true);
    setDocError(null);
    try {
      setDoc(await api.documents.get(id));
    } catch (e) {
      setDocError(e.message);
    } finally {
      setLoadingDoc(false);
    }
  }, [api, id]);

  const loadInsights = useCallback(async () => {
    setLoadingInsights(true);
    try {
      setInsights(await api.insights.forDocument(id));
    } catch (e) {
      toast.err(e.message);
    } finally {
      setLoadingInsights(false);
    }
  }, [api, id, toast]);

  useEffect(() => { loadDoc(); loadInsights(); }, [loadDoc, loadInsights]);

  async function analyze() {
    setAnalyzing(true);
    try {
      const data = await api.insights.analyze(id);
      setInsights(data);
      toast.ok(`${data.length} insight(s) generated.`);
    } catch (e) {
      toast.err(e.message);
    } finally {
      setAnalyzing(false);
    }
  }

  async function processDoc() {
    setProcessing(true);
    try {
      const result = await api.documents.process(id);
      toast.ok(`Processed as ${result.document_type} (${result.chunks_indexed} chunks indexed).`);
      loadDoc();
    } catch (e) {
      toast.err(e.message);
      loadDoc();
    } finally {
      setProcessing(false);
    }
  }

  async function remove() {
    if (!window.confirm("Delete this document? This cannot be undone.")) return;
    setDeleting(true);
    try {
      await api.documents.remove(id);
      toast.ok("Document deleted.");
      navigate("/documents");
    } catch (e) {
      toast.err(e.message);
    } finally {
      setDeleting(false);
    }
  }

  if (loadingDoc) return <div className="page-fade"><div className="empty">Loading…</div></div>;
  if (docError) return <div className="page-fade"><div className="empty" style={{ color: "var(--rust)" }}>{docError}</div></div>;

  return (
    <div className="page-fade">
      <div className="view-head">
        <div className="view-head-text">
          <h1>{doc.filename}</h1>
          <p className="lede mono" style={{ fontSize: 12 }}>{doc.document_id}</p>
        </div>
        <div className="btn-group">
          <button className="ghost" onClick={() => navigate(`/ask?document_id=${doc.document_id}`)}>Ask about this document</button>
          <button className="ghost" onClick={remove} disabled={deleting} style={{ color: "var(--rust)" }}>
            {deleting ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>

      <section className="panel">
        <h2>Metadata</h2>
        <dl className="kv-list" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0 20px" }}>
          <div><dt>Type</dt><dd><span className="badge slate">{doc.document_type}</span></dd></div>
          <div><dt>Status</dt><dd><span className="badge slate">          {doc.status !== "ready" && (
            <button className="action" onClick={processDoc} disabled={processing || doc.status === "processing"}>
              {processing ? <span className="spinner" /> : <span>{doc.status === "failed" ? "Retry processing" : "Process document"}</span>}
            </button>
          )}</span></dd></div>
          <div><dt>Size</dt><dd>{formatBytes(doc.size_bytes)}</dd></div>
          <div><dt>Content type</dt><dd>{doc.content_type}</dd></div>
          <div><dt>Uploaded</dt><dd>{new Date(doc.created_at).toLocaleString()}</dd></div>
          <div><dt>Last updated</dt><dd>{new Date(doc.updated_at).toLocaleString()}</dd></div>
        </dl>
      </section>

      <section className="panel">
        <h2>Insights</h2>
        <div className="btn-group" style={{ marginBottom: 16 }}>
          <button className="action" onClick={analyze} disabled={analyzing}>
            {analyzing ? <span className="spinner" /> : <span>Analyze document</span>}
          </button>
          <button className="ghost" onClick={loadInsights}>Refresh</button>
        </div>
        {loadingInsights ? <div className="empty">Loading…</div> : <InsightList insights={insights} emptyMessage="No insights yet — run Analyze." />}
      </section>
    </div>
  );
}
