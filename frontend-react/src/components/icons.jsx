const base = { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8 };

export const UploadIcon = () => (
  <svg {...base}><path d="M12 16V4M12 4L7 9M12 4l5 5" /><path d="M4 16v3a2 2 0 002 2h12a2 2 0 002-2v-3" /></svg>
);
export const AskIcon = () => (
  <svg {...base}><path d="M21 11.5a8.5 8.5 0 01-11.4 8L3 21l1.5-6.6A8.5 8.5 0 1121 11.5z" /></svg>
);
export const InsightsIcon = () => (
  <svg {...base}><path d="M3 3v18h18" /><path d="M7 14l4-5 3 3 5-7" /></svg>
);
export const DriftIcon = () => (
  <svg {...base}><path d="M2 12h3l2-7 4 14 3-9 2 5h6" /></svg>
);
export const HealthIcon = () => (
  <svg {...base}><path d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.6l-1-1a5.5 5.5 0 10-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 000-7.8z" /></svg>
);
export const SettingsIcon = () => (
  <svg {...base}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 00.3 1.9l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.9-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1-1.6 1.7 1.7 0 00-1.9.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.9 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1 1.7 1.7 0 00-.3-1.9l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.9.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.9-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.9V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z" /></svg>
);
export const EmptyIcon = () => (
  <svg {...base}><path d="M14 3v4a1 1 0 001 1h4" /><path d="M17 21H7a2 2 0 01-2-2V5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2z" /></svg>
);
export const CloseIcon = () => (
  <svg {...base}><path d="M18 6L6 18M6 6l12 12" /></svg>
);
export const SortIcon = ({ dir }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 11, height: 11, marginLeft: 4, opacity: dir ? 1 : 0.35 }}>
    {dir === "desc" ? <path d="M6 9l6 6 6-6" /> : <path d="M18 15l-6-6-6 6" />}
  </svg>
);
