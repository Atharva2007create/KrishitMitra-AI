"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { adminApi, adminSignIn, ApiError, api } from "@/lib/api";

type Section = "dashboard" | "users" | "sources" | "documents" | "ingestion" | "feedback" | "images" | "system" | "audit";
type Row = Record<string, unknown>;

const NAV: Array<{ id: Section; label: string; icon: string }> = [
  { id: "dashboard", label: "Overview", icon: "◫" },
  { id: "users", label: "Farmers & users", icon: "♙" },
  { id: "sources", label: "Government sources", icon: "⌂" },
  { id: "documents", label: "Knowledge documents", icon: "▤" },
  { id: "ingestion", label: "Ingestion jobs", icon: "↻" },
  { id: "feedback", label: "Farmer feedback", icon: "♡" },
  { id: "images", label: "Image analyses", icon: "▧" },
  { id: "system", label: "System health", icon: "◉" },
  { id: "audit", label: "Audit log", icon: "≡" },
];

const TITLES: Record<Section, { title: string; note: string }> = {
  dashboard: { title: "Operations overview", note: "A current view of the KrishiMitra service" },
  users: { title: "Farmers & users", note: "Accounts, profiles, farms and crop cycles" },
  sources: { title: "Government sources", note: "Authoritative sources available to the evidence pipeline" },
  documents: { title: "Knowledge documents", note: "Documents collected for retrieval and citation" },
  ingestion: { title: "Ingestion jobs", note: "Processing status and failures" },
  feedback: { title: "Farmer feedback", note: "Farmer ratings and comments" },
  images: { title: "Image analyses", note: "Operational status without exposing stored images" },
  system: { title: "System health", note: "Database and source readiness" },
  audit: { title: "Audit log", note: "Recent sensitive administrative activity" },
};

function label(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function display(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function statusClass(value: unknown) {
  const text = String(value ?? "").toLowerCase();
  if (["active", "completed", "trusted", "ok", "connected", "admin"].some((word) => text.includes(word))) return "good";
  if (["failed", "error", "inactive", "revoked"].some((word) => text.includes(word))) return "bad";
  return "neutral";
}

function columns(rows: Row[]) {
  const priority = ["name", "full_name", "title", "action", "source_name", "user_contact", "email", "phone_number", "role", "status", "trust_status", "rating", "is_active", "created_at", "completed_at"];
  const available = new Set(rows.flatMap((row) => Object.keys(row)).filter((key) => !["id", "metadata", "quality_assessment"].includes(key)));
  return [...priority.filter((key) => available.has(key)), ...[...available].filter((key) => !priority.includes(key))].slice(0, 7);
}

export function AdminApp() {
  const [token, setToken] = useState("");
  const [verified, setVerified] = useState(false);
  const [section, setSection] = useState<Section>("dashboard");
  const [data, setData] = useState<unknown>(null);
  const [detail, setDetail] = useState<Row | null>(null);
  const [identity, setIdentity] = useState<{ email?: string | null; phone_number?: string | null } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const logout = useCallback(() => {
    localStorage.removeItem("krishimitra.admin.token");
    setToken(""); setVerified(false); setData(null); setIdentity(null); setDetail(null);
  }, []);

  const verify = useCallback(async (candidate: string) => {
    setLoading(true); setError("");
    try {
      const health = await adminApi.health(candidate);
      if (health.role !== "ADMIN") throw new Error("This account is not authorized for administration.");
      const me = await api.me(candidate);
      localStorage.setItem("krishimitra.admin.token", candidate);
      setToken(candidate); setVerified(true); setIdentity(me);
    } catch (reason) {
      localStorage.removeItem("krishimitra.admin.token");
      setError(reason instanceof ApiError && reason.status === 403 ? "Administrator access is required." : reason instanceof Error ? reason.message : "Unable to verify administrator access.");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    queueMicrotask(() => {
      const saved = localStorage.getItem("krishimitra.admin.token");
      if (saved) void verify(saved); else setLoading(false);
    });
  }, [verify]);

  const load = useCallback(async () => {
    if (!token || !verified) return;
    setLoading(true); setError(""); setDetail(null);
    try {
      const result = section === "dashboard" ? await adminApi.dashboard(token)
        : section === "users" ? await adminApi.users(token)
        : section === "sources" ? await adminApi.sources(token)
        : section === "documents" ? await adminApi.documents(token)
        : section === "ingestion" ? await adminApi.ingestion(token)
        : section === "feedback" ? await adminApi.feedback(token)
        : section === "images" ? await adminApi.images(token)
        : section === "system" ? await adminApi.system(token)
        : await adminApi.audit(token);
      setData(result);
    } catch (reason) {
      if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) logout();
      setError(reason instanceof Error ? reason.message : "Unable to load this admin view.");
    } finally { setLoading(false); }
  }, [logout, section, token, verified]);

  useEffect(() => { queueMicrotask(() => void load()); }, [load]);

  if (!verified) return <AdminLogin loading={loading} error={error} onSignIn={verify} />;

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-brand"><span>कृ</span><div><strong>KrishiMitra</strong><small>ADMIN CONSOLE</small></div></div>
        <nav aria-label="Admin modules">{NAV.map((item) => <button key={item.id} className={section === item.id ? "active" : ""} onClick={() => setSection(item.id)}><i>{item.icon}</i>{item.label}</button>)}</nav>
        <div className="admin-account"><div className="admin-avatar">A</div><div><strong>Administrator</strong><small>{identity?.email ?? identity?.phone_number ?? "Verified account"}</small></div><button title="Sign out" onClick={logout}>↪</button></div>
      </aside>
      <main className="admin-main">
        <header className="admin-topbar"><div><span className="admin-kicker">KRISHIMITRA OPERATIONS</span><h1>{TITLES[section].title}</h1><p>{TITLES[section].note}</p></div><button className="admin-refresh" onClick={() => void load()} disabled={loading}>↻ Refresh</button></header>
        {error && <div className="admin-alert" role="alert">{error}<button onClick={() => void load()}>Try again</button></div>}
        {loading ? <div className="admin-loading"><span /><p>Loading current data…</p></div> : <AdminContent section={section} data={data} onUser={async (id) => { setLoading(true); try { setDetail(await adminApi.user(token, id)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load user."); } finally { setLoading(false); } }} />}
      </main>
      {detail && <DetailPanel value={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}

function AdminLogin({ loading, error, onSignIn }: { loading: boolean; error: string; onSignIn: (token: string) => Promise<void> }) {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); try { await onSignIn(await adminSignIn(email, password)); } catch { /* verification presents the safe error */ } finally { setBusy(false); } }
  return <main className="admin-login"><section><div className="admin-login-mark">कृ</div><span className="admin-kicker">SECURE OPERATIONS</span><h1>KrishiMitra Admin</h1><p>Sign in with an administrator account. Authorization is verified by the server.</p><form onSubmit={submit}><label>Email<input type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} /></label><label>Password<input type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} /></label>{error && <div className="admin-form-error" role="alert">{error}</div>}<button disabled={loading || busy}>{loading || busy ? "Verifying access…" : "Sign in securely"}</button></form><small>Farmer accounts cannot access this console.</small></section><aside><div><span>Evidence-led administration</span><h2>Operate the farmer guidance system with confidence.</h2><p>Monitor trusted sources, ingestion, farmer activity, feedback and system health from one place.</p></div></aside></main>;
}

function AdminContent({ section, data, onUser }: { section: Section; data: unknown; onUser: (id: string) => void }) {
  if (section === "dashboard" && data && typeof data === "object" && !Array.isArray(data)) {
    const dashboard = data as { counts?: Row; ingestion_by_status?: Row; images_by_status?: Row };
    return <><div className="admin-stat-grid">{Object.entries(dashboard.counts ?? {}).map(([key, value]) => <article key={key}><span>{label(key)}</span><strong>{display(value)}</strong><small>Current records</small></article>)}</div><div className="admin-two"><StatusCard title="Ingestion status" values={dashboard.ingestion_by_status ?? {}} /><StatusCard title="Image analysis status" values={dashboard.images_by_status ?? {}} /></div></>;
  }
  if (section === "system" && data && typeof data === "object" && !Array.isArray(data)) {
    const system = data as { status?: unknown; database?: unknown; sources?: Row[] };
    return <><div className="admin-health"><article><span className={`admin-dot ${statusClass(system.status)}`} /><div><small>Application</small><strong>{display(system.status)}</strong></div></article><article><span className={`admin-dot ${statusClass(system.database)}`} /><div><small>Database</small><strong>{display(system.database)}</strong></div></article></div><DataTable rows={system.sources ?? []} /></>;
  }
  const rows = Array.isArray(data) ? data as Row[] : [];
  return <DataTable rows={rows} onRow={section === "users" ? (row) => onUser(String(row.id)) : undefined} />;
}

function StatusCard({ title, values }: { title: string; values: Row }) {
  return <section className="admin-card"><h2>{title}</h2>{Object.keys(values).length ? Object.entries(values).map(([key, value]) => <div className="admin-status-row" key={key}><span><i className={statusClass(key)} />{label(key)}</span><strong>{display(value)}</strong></div>) : <div className="admin-empty compact">No activity recorded</div>}</section>;
}

function DataTable({ rows, onRow }: { rows: Row[]; onRow?: (row: Row) => void }) {
  const keys = useMemo(() => columns(rows), [rows]);
  if (!rows.length) return <div className="admin-empty"><span>✓</span><h2>No records to show</h2><p>The service returned an empty result for this view.</p></div>;
  return <section className="admin-table-card"><div className="admin-table-meta"><strong>{rows.length} record{rows.length === 1 ? "" : "s"}</strong><span>Latest available data</span></div><div className="admin-table-scroll"><table><thead><tr>{keys.map((key) => <th key={key}>{label(key)}</th>)}{onRow && <th>Details</th>}</tr></thead><tbody>{rows.map((row, index) => <tr key={String(row.id ?? index)}>{keys.map((key) => <td key={key}>{["status", "role", "trust_status", "is_active"].includes(key) ? <span className={`admin-pill ${statusClass(row[key])}`}>{display(row[key])}</span> : display(row[key])}</td>)}{onRow && <td><button className="admin-link" onClick={() => onRow(row)}>View profile →</button></td>}</tr>)}</tbody></table></div></section>;
}

function DetailPanel({ value, onClose }: { value: Row; onClose: () => void }) {
  return <div className="admin-drawer-backdrop" onClick={onClose}><aside className="admin-drawer" onClick={(event) => event.stopPropagation()}><header><div><span className="admin-kicker">ACCOUNT DETAIL</span><h2>{display((value.profile as Row | null)?.full_name ?? value.email ?? value.phone_number)}</h2></div><button aria-label="Close" onClick={onClose}>×</button></header><pre>{JSON.stringify(value, null, 2)}</pre></aside></div>;
}
