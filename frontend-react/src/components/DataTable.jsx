import { useMemo, useState } from "react";
import { EmptyIcon, SortIcon } from "./icons.jsx";

/**
 * Generic list table shared by Documents, Insights, Drift results, and Alerts.
 *
 * columns: [{ key, label, sortable?, render?(row) }]
 * rows: array of data objects
 * getRowKey(row): unique key
 * onRowClick(row): optional — makes rows clickable
 * emptyMessage: shown when rows is empty and not loading
 * pagination: { limit, offset, onPrev, onNext, hasMore } — omit to hide pager
 */
export default function DataTable({
  columns,
  rows,
  getRowKey,
  onRowClick,
  loading,
  error,
  emptyMessage = "Nothing here yet.",
  pagination,
}) {
  const [sort, setSort] = useState({ key: null, dir: "asc" });

  const sortedRows = useMemo(() => {
    if (!sort.key) return rows;
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[sort.key];
      const bv = b[sort.key];
      if (av === bv) return 0;
      const result = av > bv ? 1 : -1;
      return sort.dir === "asc" ? result : -result;
    });
    return copy;
  }, [rows, sort]);

  function toggleSort(key) {
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }));
  }

  if (error) return <div className="empty" style={{ color: "var(--rust)", borderColor: "var(--rust-soft)" }}>{error}</div>;

  if (loading) {
    return (
      <table>
        <thead><tr>{columns.map((c) => <th key={c.key}>{c.label}</th>)}</tr></thead>
        <tbody>
          {[...Array(3)].map((_, i) => (
            <tr key={i}>{columns.map((c) => <td key={c.key}><div style={{ height: 12, background: "var(--line)", borderRadius: 2, opacity: 0.5 }} /></td>)}</tr>
          ))}
        </tbody>
      </table>
    );
  }

  if (!sortedRows.length) {
    return (
      <div className="empty">
        <EmptyIcon />
        <div>{emptyMessage}</div>
      </div>
    );
  }

  return (
    <>
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                className={c.sortable ? "sortable" : undefined}
                onClick={c.sortable ? () => toggleSort(c.key) : undefined}
              >
                {c.label}
                {c.sortable && <SortIcon dir={sort.key === c.key ? sort.dir : null} />}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row) => (
            <tr key={getRowKey(row)} className={onRowClick ? "clickable" : undefined} onClick={onRowClick ? () => onRowClick(row) : undefined}>
              {columns.map((c) => (
                <td key={c.key} className={c.mono ? "mono" : undefined}>
                  {c.render ? c.render(row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {pagination && (
        <div className="pagination">
          <span>Showing {pagination.offset + 1}–{pagination.offset + sortedRows.length}</span>
          <div className="btn-group">
            <button className="ghost small" onClick={pagination.onPrev} disabled={pagination.offset === 0}>Previous</button>
            <button className="ghost small" onClick={pagination.onNext} disabled={!pagination.hasMore}>Next</button>
          </div>
        </div>
      )}
    </>
  );
}
