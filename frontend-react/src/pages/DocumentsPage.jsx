import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApi } from "../lib/api.js";
import { useToast } from "../lib/ToastContext.jsx";
import DataTable from "../components/DataTable.jsx";
import { UploadIcon } from "../components/icons.jsx";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_EXT = [".pdf", ".docx"];
const PAGE_SIZE = 20;

function formatBytes(n) {
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / (1024 * 1024)).toFixed(2) + " MB";
}

export default function DocumentsPage() {
  const api = useApi();
  const toast = useToast();
  const navigate = useNavigate();

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [offset, setOffset] = useState(0);
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
    const [stage, setStage] = useState(""); 
  const fileInputRef = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.documents.list({
        document_type: typeFilter || undefined,
        status: statusFilter || undefined,
        limit: PAGE_SIZE,
        offset,
      });
      setRows(data.items);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [api, typeFilter, statusFilter, offset]);

  useEffect(() => { load(); }, [load]);

  function handleFile(file) {
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!ALLOWED_EXT.includes(ext)) { toast.err("Unsupported file type — use .pdf or .docx."); return; }
    if (file.size > MAX_FILE_SIZE) { toast.err(`File exceeds the 10 MB limit (${formatBytes(file.size)}).`); return; }
    if (file.size === 0) { toast.err("File is empty."); return; }
    setSelectedFile(file);
  }

    async function doUpload() {
    if (!selectedFile) { toast.err("Choose a file first."); return; }
    setUploading(true);
    try {
      setStage("uploading");
      const data = await api.documents.upload(selectedFile);
      toast.ok("Uploaded — " + data.filename);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setOffset(0);
      load();

      // Uploading only stores the file. Processing parses, classifies, extracts and
      // indexes it -- without this step Ask and Insights have nothing to work with.
      // The very first run also loads the embedding model, so it can take a while.
      setStage("processing");
      try {
        const result = await api.documents.process(data.document_id);
        toast.ok(`Processed as ${result.document_type} (${result.chunks_indexed} chunks indexed).`);
      } catch (e) {
        toast.err("Uploaded, but processing failed: " + e.message);
      }
      load();
    } catch (e) {
      toast.err(e.message);
    } finally {
      setUploading(false);
      setStage("");
    }
  }

  const columns = [
    { key: "document_id", label: "Document ID", mono: true, render: (r) => r.document_id.slice(0, 8) + "…" },
    { key: "filename", label: "Filename", sortable: true },
    { key: "document_type", label: "Type", sortable: true, render: (r) => <span className="badge slate">{r.document_type}</span> },
    { key: "status", label: "Status", sortable: true, render: (r) => <span className="badge slate">{r.status}</span> },
    { key: "size_bytes", label: "Size", sortable: true, render: (r) => formatBytes(r.size_bytes) },
    { key: "created_at", label: "Uploaded", sortable: true, render: (r) => new Date(r.created_at).toLocaleString() },
  ];

  return (
    <div className="page-fade">
      <div className="view-head"><div className="view-head-text">
        <h1>Documents</h1>
        <p className="lede">PDF or DOCX, up to 10 MB. Click a row for extraction and insight detail.</p>
      </div></div>

      <section className="panel">
        <div
          className={"dropzone" + (dragOver ? " drag-over" : "")}
          role="button"
          tabIndex={0}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && fileInputRef.current?.click()}
          onDragEnter={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragOver={(e) => e.preventDefault()}
          onDragLeave={(e) => { e.preventDefault(); setDragOver(false); }}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); }}
        >
          <UploadIcon />
          <div className="dz-title">Drop a file here, or click to choose</div>
          <div className="dz-sub">.pdf or .docx · max 10 MB</div>
          <input ref={fileInputRef} type="file" accept=".pdf,.docx" onChange={(e) => e.target.files.length && handleFile(e.target.files[0])} style={{ display: "none" }} />
        </div>

        {selectedFile && (
          <div className="file-chip">
            <div><span className="name">{selectedFile.name}</span><span className="size">{formatBytes(selectedFile.size)}</span></div>
            <button onClick={() => { setSelectedFile(null); if (fileInputRef.current) fileInputRef.current.value = ""; }}>Remove</button>
          </div>
        )}

        <div className="btn-group" style={{ marginTop: 16 }}>
          <button className="action" onClick={doUpload} disabled={!selectedFile || uploading}>
            {uploading ? <span>{stage === "processing" ? "Processing… (first run loads the model)" : "Uploading…"}</span> : <span>Upload &amp; process</span>}
          </button>
        </div>
      </section>

      <section className="panel">
        <h2>All documents</h2>
        <div className="filter-bar">
          <div className="field">
            <label>Type</label>
            <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setOffset(0); }}>
              <option value="">any</option>
              <option value="invoice">invoice</option>
              <option value="purchase_order">purchase_order</option>
              <option value="contract">contract</option>
              <option value="unknown">unknown</option>
            </select>
          </div>
          <div className="field">
            <label>Status</label>
            <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setOffset(0); }}>
              <option value="">any</option>
              <option value="uploaded">uploaded</option>
              <option value="queued">queued</option>
              <option value="processing">processing</option>
              <option value="ready">ready</option>
              <option value="failed">failed</option>
            </select>
          </div>
          <button className="ghost" onClick={load}>Refresh</button>
        </div>

        <DataTable
          columns={columns}
          rows={rows}
          getRowKey={(r) => r.document_id}
          onRowClick={(r) => navigate(`/documents/${r.document_id}`)}
          loading={loading}
          error={error}
          emptyMessage="No documents match these filters."
          pagination={{
            offset,
            hasMore: rows.length === PAGE_SIZE,
            onPrev: () => setOffset((o) => Math.max(0, o - PAGE_SIZE)),
            onNext: () => setOffset((o) => o + PAGE_SIZE),
          }}
        />
      </section>
    </div>
  );
}
