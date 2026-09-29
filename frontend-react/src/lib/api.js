import { useMemo } from "react";
import { useConnection } from "./ConnectionContext.jsx";

async function rawFetch(base, key, path, opts = {}) {
  if (!base) throw new Error("Set the API base URL in Connection first.");

  const headers = Object.assign({}, opts.headers || {});

  if (opts.auth !== false) {
    if (!key) throw new Error("Set the API key in Connection first.");
    headers["Authorization"] = "Bearer " + key;
  }

  if (opts.body !== undefined && !(opts.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  let res;

  try {
    res = await fetch(base + path, {
      method: opts.method || "GET",
      headers,
      body:
        opts.body instanceof FormData
          ? opts.body
          : opts.body !== undefined
          ? JSON.stringify(opts.body)
          : undefined,
    });
  } catch (_) {
    // fetch only throws on network failure / CORS block, never on HTTP errors.
    throw new Error(
      "Cannot reach the API at " +
        base +
        " — is the backend running, and is this site's origin in CORS_ALLOWED_ORIGINS?"
    );
  }

  if (res.status === 429) {
    const retryAfter = res.headers.get("Retry-After") || "a few";
    throw new Error("Rate limited — retry after " + retryAfter + "s.");
  }

  if (res.status === 401) {
    throw new Error("Unauthorized — check your API key.");
  }

  if (!res.ok) {
    let detail = res.statusText;

    try {
      const j = await res.json();
      detail = j.detail || detail;
    } catch (_) {
      /* body wasn't JSON */
    }

    throw new Error("HTTP " + res.status + ": " + detail);
  }

  if (res.status === 204) return null;

  return res.json();
}

function qs(params) {
  const entries = Object.entries(params || {}).filter(
    ([, v]) => v !== undefined && v !== null && v !== ""
  );

  if (!entries.length) return "";

  return "?" + new URLSearchParams(entries).toString();
}

/**
 * Bound API client.
 * Every list method returns a plain array or a { items, limit, offset } shape,
 * matching what the corresponding endpoint returns — see README's API surface table.
 */
export function useApi() {
  const { base, key } = useConnection();

  return useMemo(() => {
    const f = (path, opts) => rawFetch(base, key, path, opts);

    return {
      health: {
        live: () => f("/health/live", { auth: false }),
        ready: () => f("/health/ready", { auth: false }),
      },

      documents: {
        list: (params) => f("/documents/" + qs(params)),

        get: (id) => f(`/documents/${id}`),

        upload: (file) => {
          const form = new FormData();
          form.append("file", file);

          return f("/documents/", {
            method: "POST",
            body: form,
          });
        },

        remove: (id) =>
          f(`/documents/${id}`, {
            method: "DELETE",
          }),

        // Parse + classify + extract + index.
        // Required before Q&A / insights work on a document.
        process: (id) =>
          f(`/documents/${id}/process`, {
            method: "POST",
          }),
      },

      qa: {
        ask: (payload) =>
          f("/qa/answer", {
            method: "POST",
            body: payload,
          }),
      },

      insights: {
        list: (params) =>
          f("/analyst/insights" + qs(params)),

        forDocument: (documentId) =>
          f(`/analyst/documents/${documentId}/insights`),

        analyze: (documentId) =>
          f(`/analyst/documents/${documentId}/analyze`, {
            method: "POST",
          }),

        compare: (documentIdA, documentIdB) =>
          f("/analyst/compare", {
            method: "POST",
            body: {
              document_id_a: documentIdA,
              document_id_b: documentIdB,
            },
          }),

        trend: (documentType) =>
          f("/analyst/trend", {
            method: "POST",
            body: {
              document_type: documentType,
            },
          }),
      },

      drift: {
        results: (params) =>
          f("/drift/results" + qs(params)),

        alerts: () =>
          f("/drift/alerts"),

        acknowledge: (alertId) =>
          f(`/drift/alerts/${alertId}/acknowledge`, {
            method: "POST",
          }),

        baseline: (documentType) =>
          f("/drift/baseline", {
            method: "POST",
            body: {
              document_type: documentType,
            },
          }),

        check: (documentType) =>
          f("/drift/check", {
            method: "POST",
            body: {
              document_type: documentType,
            },
          }),

        dashboard: () =>
          f("/drift/dashboard"),
      },
    };
  }, [base, key]);
}