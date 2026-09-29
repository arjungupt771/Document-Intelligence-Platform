import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useApi } from "../lib/api.js";
import { useToast } from "../lib/ToastContext.jsx";
import AnswerText from "../components/AnswerText.jsx";

export default function AskPage() {
  const api = useApi();
  const toast = useToast();
  const [searchParams] = useSearchParams();

  const [query, setQuery] = useState("");
  const [documentId, setDocumentId] = useState(searchParams.get("document_id") || "");
  const [documentType, setDocumentType] = useState("");
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  async function ask() {
    if (!query.trim()) { toast.err("Enter a question."); return; }
    setLoading(true);
    setResult(null);
    try {
      const data = await api.qa.ask({
        query: query.trim(),
        document_id: documentId.trim() || null,
        document_type: documentType || null,
        top_k: Number(topK) || 5,
      });
      setResult(data);
      toast.ok("Answer received.");
    } catch (e) {
      toast.err(e.message);
    } finally {
      setLoading(false);
    }
  }

  const claims = result?.unsupported_claims || [];
  const sources = result?.sources || [];

  return (
    <div className="page-fade">
      <div className="view-head"><div className="view-head-text">
        <h1>Ask</h1>
        <p className="lede">Grounded Q&amp;A over indexed documents. Leave document ID blank to search everything.</p>
      </div></div>

      <section className="panel">
        <div className="field">
          <label htmlFor="ask-query">Question</label>
          <textarea id="ask-query" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="What is the payment due date?" />
        </div>
        <div className="row">
          <div className="field">
            <label htmlFor="ask-doc-id">Document ID (optional)</label>
            <input id="ask-doc-id" type="text" value={documentId} onChange={(e) => setDocumentId(e.target.value)} placeholder="uuid" />
          </div>
          <div className="field">
            <label htmlFor="ask-doc-type">Document type (optional)</label>
            <select id="ask-doc-type" value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
              <option value="">any</option>
              <option value="invoice">invoice</option>
              <option value="purchase_order">purchase_order</option>
              <option value="contract">contract</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="ask-top-k">Top K</label>
            <input id="ask-top-k" type="number" min="1" max="20" value={topK} onChange={(e) => setTopK(e.target.value)} />
          </div>
        </div>
        <button className="action" onClick={ask} disabled={loading}>
          {loading ? <span className="spinner" /> : <span>Ask</span>}
        </button>

        {result && (
          <div className="result-box">
            <div className="answer-head">
              <span className="eyebrow">Answer</span>
              <div className="badge-row">
                <span className={"badge " + (result.grounded ? "green" : "rust")}>
                  {result.grounded ? "grounded" : "ungrounded"}
                </span>
                <span className={"badge " + (result.verified ? "green" : "amber")}>
                  {result.verified ? "verified" : "unverified"}
                </span>
              </div>
            </div>

            <AnswerText text={result.answer} />

            {result.verification_reason && (
              <div className={"verdict " + (result.verified ? "ok" : "warn")}>
                {result.verification_reason}
              </div>
            )}

            {claims.length > 0 && (
              <details className="claims">
                <summary>Unsupported claims ({claims.length})</summary>
                <ul>
                  {claims.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </details>
            )}

            <div className="divider" />

            <details className="sources" open={sources.length > 0 && sources.length <= 3}>
              <summary>Sources ({sources.length})</summary>
              {sources.length ? (
                sources.map((s, i) => (
                  <div key={i} className="source-item">
                    <div className="meta">
                      #{i + 1} · {s.document_type}
                      {s.page_number != null ? ` · page ${s.page_number}` : ""}
                      {s.score != null ? ` · score ${s.score.toFixed(3)}` : ""}
                      <br />
                      <span className="src-id">{s.document_id}</span>
                    </div>
                    <div className="src-text">{s.text}</div>
                  </div>
                ))
              ) : (
                <div className="empty">No sources retrieved.</div>
              )}
            </details>
          </div>
        )}
      </section>
    </div>
  );
}