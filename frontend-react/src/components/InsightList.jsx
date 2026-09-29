import { EmptyIcon } from "./icons.jsx";

export default function InsightList({ insights, emptyMessage = "Nothing to show yet." }) {
  if (!insights || !insights.length) {
    return (
      <div className="empty">
        <EmptyIcon />
        <div>{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div>
      {insights.map((i) => {
        const sevClass = i.severity === "high" || i.severity === "critical" ? "high" : i.severity === "medium" ? "medium" : "";
        const badgeClass = sevClass === "high" ? "rust" : sevClass === "medium" ? "amber" : "green";
        const pct = Math.round(i.confidence * 100);
        return (
          <div key={i.id} className={"insight-card " + sevClass}>
            <div className="title">{i.title}</div>
            <div className="desc">{i.description}</div>
            <div className="meta-row">
              <span className="badge slate">{i.type}</span>
              <span className={"badge " + badgeClass}>{i.severity}</span>
              <span>
                confidence <span className="conf-bar"><span style={{ width: pct + "%" }} /></span> {pct}%
              </span>
              {i.priority_score != null && <span>priority {i.priority_score.toFixed(2)}</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
