import { useState } from "react";
import { useConnection } from "../lib/ConnectionContext.jsx";
import { useApi } from "../lib/api.js";
import { useToast } from "../lib/ToastContext.jsx";

export default function ConnectionPage() {
  const { base, key, setBase, setKey, setStatus } = useConnection();
  const [baseInput, setBaseInput] = useState(base);
  const [keyInput, setKeyInput] = useState(key);
  const [testing, setTesting] = useState(false);
  const api = useApi();
  const toast = useToast();

  function save() {
    setBase(baseInput);
    setKey(keyInput);
    toast.ok("Connection settings saved.");
  }

  async function test() {
    setTesting(true);
    try {
      await api.health.live();
      setStatus("connected");
      toast.ok("Connected — API is live.");
    } catch (e) {
      setStatus("unreachable");
      toast.err("Could not reach API: " + e.message);
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="page-fade">
      <div className="view-head"><div className="view-head-text">
        <h1>Connection</h1>
        <p className="lede">Set once — stored in this browser only, never sent anywhere but your API.</p>
      </div></div>
      <section className="panel">
        <div className="field">
          <label htmlFor="api-base">API base URL</label>
          <input id="api-base" type="text" value={baseInput} onChange={(e) => setBaseInput(e.target.value)} placeholder="http://localhost:8000" />
        </div>
        <div className="field">
          <label htmlFor="api-key">API key (Bearer token)</label>
          <input id="api-key" type="password" value={keyInput} onChange={(e) => setKeyInput(e.target.value)} placeholder="API_AUTH_KEY value" />
        </div>
        <div className="btn-group">
          <button className="action" onClick={save}><span>Save</span></button>
          <button className="ghost" onClick={test} disabled={testing}>{testing ? "Testing..." : "Test connection"}</button>
        </div>
      </section>
    </div>
  );
}
