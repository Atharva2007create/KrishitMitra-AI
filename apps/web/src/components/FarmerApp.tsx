"use client";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { api, sendOtp, verifyOtp } from "@/lib/api";
import { t } from "@/lib/i18n";
import type {
  AssistanceResponse,
  Category,
  ChatSession,
  CropCycle,
  Faq,
  Farm,
  Language,
  Me,
  Message,
  Screen,
} from "@/lib/types";

type Props = {
  token: string;
  language: Language;
  setLanguage: (value: Language) => void;
  screen: Screen;
  setScreen: (value: Screen) => void;
  me: Me | null;
  farms: Farm[];
  cycles: CropCycle[];
  activeCycle?: CropCycle;
  categories: Category[];
  chats: ChatSession[];
  loading: boolean;
  error: string;
  authenticated: (token: string) => void;
  logout: () => void;
};
const icon: Record<string, string> = {
  SOWING_SEEDS: "🌱",
  SOIL_LAND: "🟫",
  FERTILIZERS_NUTRIENTS: "🧪",
  IRRIGATION_DRAINAGE: "💧",
  PESTS: "🐛",
  DISEASES: "🦠",
  CROP_SYMPTOMS: "🍃",
  WEEDS: "🌿",
  FLOWERING_PODS: "🌼",
  HARVESTING: "🌾",
  POST_HARVEST: "📦",
  WEATHER: "🌦",
  MARKET: "₹",
  OTHER: "💬",
};
const visibleSlugs = new Set([
  "sowing-and-seeds",
  "soil-and-land",
  "fertilizers-and-nutrients",
  "irrigation-and-drainage",
  "pests",
  "diseases",
  "crop-symptoms",
  "weeds",
  "flowering-and-pods",
  "harvesting",
  "weather",
  "market-and-selling",
]);

function LanguageSwitcher({
  value,
  onChange,
}: {
  value: Language;
  onChange: (value: Language) => void;
}) {
  return (
    <div className="languages" aria-label="Language">
      <button
        className={value === "en" ? "active" : ""}
        onClick={() => onChange("en")}
      >
        English
      </button>
      <button
        className={value === "hi" ? "active" : ""}
        onClick={() => onChange("hi")}
      >
        हिंदी
      </button>
      <button
        className={value === "mr" ? "active" : ""}
        onClick={() => onChange("mr")}
      >
        मराठी
      </button>
    </div>
  );
}
function Logo() {
  return (
    <div className="logo">
      <span className="logo-leaf">✓</span>
      <span>
        KrishiMitra <b>AI</b>
      </span>
    </div>
  );
}
function StatusCard({
  title,
  text,
  tone = "green",
}: {
  title: string;
  text: string;
  tone?: string;
}) {
  return (
    <div className={`status-card ${tone}`}>
      <span className="status-icon">
        {tone === "red" ? "!" : tone === "orange" ? "i" : "✓"}
      </span>
      <div>
        <strong>{title}</strong>
        <p>{text}</p>
      </div>
    </div>
  );
}
function SourceList({
  citations,
}: {
  citations: AssistanceResponse["citations"];
}) {
  if (!citations.length) return null;
  return (
    <div className="sources">
      <strong>Government sources</strong>
      {citations.map((item, index) => (
        <a
          key={`${item.organization}-${index}`}
          href={item.source_url ?? undefined}
          target="_blank"
          rel="noreferrer"
        >
          <span>✓</span>
          <div>
            <b>{item.organization}</b>
            <small>
              {item.document_title}
              {item.page_start ? ` · Page ${item.page_start}` : ""}
            </small>
          </div>
        </a>
      ))}
    </div>
  );
}

function Login({
  language,
  setLanguage,
  setScreen,
  authenticated,
}: Pick<Props, "language" | "setLanguage" | "setScreen" | "authenticated">) {
  const c = t(language);
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [session, setSession] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (!session) {
        const value = await sendOtp(phone);
        if (!value.Session)
          throw new Error("Cognito did not start an SMS OTP challenge.");
        setSession(value.Session);
      } else authenticated(await verifyOtp(phone, otp, session));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="auth-page">
      <div className="auth-hero">
        <Logo />
        <div className="hero-copy">
          <span>🌿 Smart farming support for Tur</span>
          <h1>
            AI-Powered Guidance
            <br />
            for Better Tur Farming
          </h1>
          <p>
            Ask questions, understand crop problems, check official information
            and make informed farm decisions.
          </p>
          <div className="trust-row">
            <span>✓ Government knowledge</span>
            <span>✓ Your data stays private</span>
          </div>
        </div>
        <div className="field-art" aria-hidden="true">
          🌱　🌿　🌾
        </div>
      </div>
      <section className="login-card">
        <LanguageSwitcher value={language} onChange={setLanguage} />
        <div className="farmer-badge">🌱</div>
        <h2>Farmer Login</h2>
        <p>Secure access with your mobile number</p>
        <form onSubmit={submit}>
          <label>
            {c.phone}
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+91 98765 43210"
              inputMode="tel"
              required
              disabled={Boolean(session)}
            />
          </label>
          {session && (
            <label>
              {c.otp}
              <input
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="Enter 6-digit OTP"
                inputMode="numeric"
                required
                autoFocus
              />
            </label>
          )}
          <button className="primary wide" disabled={busy}>
            {busy ? c.loading : session ? c.verify : c.sendOtp}
          </button>
        </form>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button className="link-button" onClick={() => setScreen("help")}>
          {c.needHelp}
        </button>
        <div className="secure-note">
          🔒 {c.secure}
          <small>We never ask for your password</small>
        </div>
      </section>
    </main>
  );
}
function Help({ setScreen }: Pick<Props, "setScreen">) {
  return (
    <main className="help-page">
      <button className="back" onClick={() => setScreen("login")}>
        ← Back to login
      </button>
      <section className="help-card">
        <Logo />
        <h1>How can we help?</h1>
        <p>Select the issue you are facing while signing in.</p>
        <div className="help-list">
          <article>
            <span>📱</span>
            <div>
              <b>OTP not received</b>
              <p>
                Check your phone number, network signal and SMS inbox, then
                request a new OTP.
              </p>
            </div>
          </article>
          <article>
            <span>🌐</span>
            <div>
              <b>Choose your language</b>
              <p>
                You can select English, हिंदी or मराठी before login and change
                it later.
              </p>
            </div>
          </article>
          <article>
            <span>🛠</span>
            <div>
              <b>Login troubleshooting</b>
              <p>
                OTP codes expire quickly. Use only the newest code sent by
                Cognito.
              </p>
            </div>
          </article>
          <article>
            <span>❓</span>
            <div>
              <b>Frequently asked questions</b>
              <p>Never share your OTP with anyone, including support staff.</p>
            </div>
          </article>
        </div>
        <StatusCard
          title="Support contacts are being configured"
          text="No placeholder phone number or email is presented as an official support channel."
          tone="orange"
        />
      </section>
    </main>
  );
}

function Header({
  language,
  setLanguage,
  name,
  setScreen,
}: Pick<Props, "language" | "setLanguage" | "setScreen"> & { name?: string }) {
  return (
    <header className="app-header">
      <Logo />
      <nav>
        <button onClick={() => setScreen("home")}>Home</button>
        <button onClick={() => setScreen("history")}>Guidance</button>
        <button onClick={() => setScreen("faqs")}>Questions</button>
      </nav>
      <div className="header-actions">
        <LanguageSwitcher value={language} onChange={setLanguage} />
        <button
          className="round"
          onClick={() => setScreen("notifications")}
          aria-label="Notifications"
        >
          🔔
        </button>
        <button className="avatar" onClick={() => setScreen("profile")}>
          👨🏽‍🌾 <span>{name ?? "Farmer"}</span>
        </button>
      </div>
    </header>
  );
}
function Sidebar({ screen, setScreen }: Pick<Props, "screen" | "setScreen">) {
  const items: Array<[Screen, string, string]> = [
    ["home", "⌂", "Home"],
    ["ask", "✦", "Ask My Question"],
    ["crop", "🌱", "Crop Cycle"],
    ["weather", "☀", "Weather"],
    ["market", "₹", "Market Prices"],
    ["guidance", "🐛", "Crop Guidance"],
    ["faqs", "?", "Popular Questions"],
    ["upload", "▧", "Upload Image"],
    ["history", "◴", "Recent Guidance"],
    ["notifications", "♢", "Notifications"],
    ["profile", "♙", "My Profile"],
  ];
  return (
    <aside className="sidebar">
      {items.map(([id, glyph, label]) => (
        <button
          key={id}
          className={screen === id ? "selected" : ""}
          onClick={() => setScreen(id)}
        >
          <span>{glyph}</span>
          {label}
        </button>
      ))}
    </aside>
  );
}
function Shell({
  props,
  children,
  title,
  subtitle,
}: {
  props: Props;
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="app">
      <Header
        language={props.language}
        setLanguage={props.setLanguage}
        setScreen={props.setScreen}
        name={props.me?.profile?.full_name}
      />
      <div className="app-body">
        <Sidebar screen={props.screen} setScreen={props.setScreen} />
        <main className="content">
          <div className="page-heading">
            <div>
              <h1>{title}</h1>
              {subtitle && <p>{subtitle}</p>}
            </div>
            <span className="official-pill">✓ Government Knowledge</span>
          </div>
          {props.error && (
            <StatusCard
              title="Connection issue"
              text={props.error}
              tone="red"
            />
          )}
          {children}
        </main>
      </div>
      <nav className="mobile-nav">
        <button onClick={() => props.setScreen("home")}>
          ⌂<span>Home</span>
        </button>
        <button onClick={() => props.setScreen("guidance")}>
          ✦<span>Guidance</span>
        </button>
        <button onClick={() => props.setScreen("history")}>
          ◴<span>History</span>
        </button>
        <button onClick={() => props.setScreen("profile")}>
          ♙<span>Profile</span>
        </button>
      </nav>
    </div>
  );
}

function HomeScreen({ props }: { props: Props }) {
  const c = t(props.language);
  const profile = props.me?.profile;
  const visible = props.categories
    .filter((item) => visibleSlugs.has(item.slug))
    .slice(0, 12);
  const cycle = props.activeCycle;
  return (
    <Shell
      props={props}
      title={`Welcome back${profile?.full_name ? `, ${profile.full_name.split(" ")[0]}` : ""}!`}
      subtitle="Here is your Tur crop overview and trusted guidance"
    >
      <section className="dashboard-top">
        <button className="ask-banner" onClick={() => props.setScreen("ask")}>
          <span className="spark">✦</span>
          <div>
            <h2>{c.ask}</h2>
            <p>Get source-backed guidance for your crop</p>
          </div>
          <b>Ask now →</b>
        </button>
        <article className="weather-mini">
          <div>
            <span>🌤</span>
            <div>
              <small>
                {profile
                  ? `${profile.district}, ${profile.state}`
                  : "Your location"}
              </small>
              <h3>{c.weather}</h3>
            </div>
          </div>
          <StatusCard
            title={c.unavailable}
            text="Live IMD values appear here only when the official source is available."
            tone="orange"
          />
          <button onClick={() => props.setScreen("weather")}>
            View forecast →
          </button>
        </article>
      </section>
      <section className="overview-grid">
        <article className="crop-card card">
          <div className="section-title">
            <div>
              <small>{c.crop}</small>
              <h2>{cycle?.crop_name ?? "Tur"}</h2>
            </div>
            <span className={`state ${cycle ? "live" : "muted"}`}>
              {cycle?.status ?? "Not set"}
            </span>
          </div>
          {cycle ? (
            <>
              <div className="crop-facts">
                <span>
                  <small>Sown</small>
                  <b>{new Date(cycle.sowing_date).toLocaleDateString()}</b>
                </span>
                <span>
                  <small>Stage</small>
                  <b>{cycle.estimated_crop_stage ?? "Not recorded"}</b>
                </span>
                <span>
                  <small>Variety</small>
                  <b>{cycle.crop_variety ?? "Not recorded"}</b>
                </span>
              </div>
              <button onClick={() => props.setScreen("crop")}>
                {c.view} →
              </button>
            </>
          ) : (
            <p>{c.noData}</p>
          )}
        </article>
        <article className="advisory-card card">
          <div className="section-title">
            <div>
              <small>{c.advisory}</small>
              <h2>Source-backed crop guidance</h2>
            </div>
            <span>🌾</span>
          </div>
          <p>
            Open verified FAQs or ask a question to receive guidance supported
            by active government evidence.
          </p>
          <button onClick={() => props.setScreen("advisory")}>
            Open advisory details →
          </button>
        </article>
        <article className="market-mini card">
          <div className="section-title">
            <div>
              <small>Official mandi data</small>
              <h2>{c.market}</h2>
            </div>
            <span>₹</span>
          </div>
          <StatusCard
            title={c.unavailable}
            text="Prices are shown only when AGMARKNET returns verified records."
            tone="orange"
          />
          <button onClick={() => props.setScreen("market")}>
            View all markets →
          </button>
        </article>
      </section>
      <section>
        <div className="section-heading">
          <h2>{c.categories}</h2>
          <p>
            Choose a topic to see common questions and start guided assistance.
          </p>
        </div>
        <div className="category-grid">
          {visible.length ? (
            visible.map((item, index) => (
              <button
                key={item.id}
                style={{ "--delay": `${index * 20}ms` } as React.CSSProperties}
                onClick={() => {
                  sessionStorage.setItem("krishimitra.category", item.id);
                  props.setScreen("guidance");
                }}
              >
                <span>{icon[item.code] ?? "🌿"}</span>
                <b>{item.title}</b>
                <small>{item.description}</small>
              </button>
            ))
          ) : (
            <StatusCard
              title={c.noData}
              text="Problem categories load after successful authentication."
              tone="orange"
            />
          )}
        </div>
      </section>
      <section className="bottom-grid">
        <button
          className="feature-card peach"
          onClick={() => props.setScreen("faqs")}
        >
          <span>❓</span>
          <div>
            <h3>{c.popular}</h3>
            <p>Browse verified answers by topic</p>
          </div>
          →
        </button>
        <button
          className="feature-card lavender"
          onClick={() => props.setScreen("upload")}
        >
          <span>📷</span>
          <div>
            <h3>{c.upload}</h3>
            <p>Use the secure analysis pipeline</p>
          </div>
          →
        </button>
        <button
          className="feature-card blue"
          onClick={() => props.setScreen("history")}
        >
          <span>◴</span>
          <div>
            <h3>{c.recent}</h3>
            <p>Continue your previous conversations</p>
          </div>
          →
        </button>
      </section>
    </Shell>
  );
}

function LiveScreen({
  props,
  kind,
}: {
  props: Props;
  kind: "weather" | "market";
}) {
  const c = t(props.language);
  const profile = props.me?.profile;
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(Boolean(props.token && profile));
  useEffect(() => {
    if (!props.token || !profile) return;
    const call =
      kind === "weather"
        ? api.weather(props.token, profile.state, profile.district)
        : api.markets(props.token, profile.state, profile.district);
    call
      .then((value) => setData(value as unknown as Record<string, unknown>))
      .catch((reason: unknown) =>
        setError(
          reason instanceof Error
            ? reason.message
            : "Official source unavailable",
        ),
      )
      .finally(() => setBusy(false));
  }, [kind, props.token, profile]);
  const rows =
    (data?.[kind === "weather" ? "observations" : "prices"] as
      Array<Record<string, unknown>> | undefined) ?? [];
  return (
    <Shell
      props={props}
      title={
        kind === "weather"
          ? "Weather Forecast & Advisory"
          : "Market Prices & Selling Insights"
      }
      subtitle={
        profile
          ? `${profile.district}, ${profile.state}`
          : "Complete your profile to use location-aware services"
      }
    >
      <section className={`live-hero ${kind}`}>
        <div>
          <span>{kind === "weather" ? "🌦" : "₹"}</span>
          <div>
            <small>Official source status</small>
            <h2>
              {busy ? c.loading : rows.length ? "Available" : "Unavailable"}
            </h2>
            <p>
              {data?.retrieved_at
                ? `Retrieved ${new Date(String(data.retrieved_at)).toLocaleString()}`
                : "Freshness appears with official data"}
            </p>
          </div>
        </div>
        <b>{kind === "weather" ? "IMD" : "AGMARKNET"}</b>
      </section>
      {error && (
        <StatusCard
          title={c.unavailable}
          text={`${error}. ${c.sourceNote}`}
          tone="orange"
        />
      )}
      {!busy && !error && !rows.length && (
        <StatusCard title={c.noData} text={c.sourceNote} tone="orange" />
      )}
      <div className="metric-grid">
        {rows.map((row, index) =>
          kind === "weather" ? (
            <article className="metric-card" key={index}>
              <span>🌤</span>
              <h3>{String(row.station_name ?? "Weather station")}</h3>
              <b>
                {row.temperature_c != null
                  ? `${String(row.temperature_c)}°C`
                  : "Not reported"}
              </b>
              <p>
                Humidity{" "}
                {String(row.relative_humidity_percent ?? "not reported")}%
              </p>
              <p>Rain {String(row.rainfall_24h_mm ?? "not reported")} mm</p>
              <small>
                {row.observed_at
                  ? new Date(String(row.observed_at)).toLocaleString()
                  : "Timestamp unavailable"}
              </small>
            </article>
          ) : (
            <article className="metric-card" key={index}>
              <span>🏪</span>
              <h3>{String(row.market ?? "Market")}</h3>
              <b>
                {row.modal_price != null
                  ? `₹${String(row.modal_price)}`
                  : "Not reported"}
              </b>
              <p>
                Min ₹{String(row.minimum_price ?? "—")} · Max ₹
                {String(row.maximum_price ?? "—")}
              </p>
              <small>
                {row.arrival_date
                  ? new Date(String(row.arrival_date)).toLocaleDateString()
                  : "Date unavailable"}
              </small>
            </article>
          ),
        )}
      </div>
      <section className="info-columns">
        <article className="card">
          <h2>
            {kind === "weather"
              ? "Crop-specific advisory"
              : "Cautious selling guidance"}
          </h2>
          <p>
            {kind === "weather"
              ? "Weather-based farm advice is shown only when supported by a current official observation and approved crop evidence."
              : "Compare dates, distance, transport cost and quality. A high quoted price does not guarantee the best net return."}
          </p>
        </article>
        <article className="card">
          <h2>{kind === "weather" ? "Seven-day forecast" : "Price trend"}</h2>
          <StatusCard
            title="Not available from the current backend contract"
            text="This area remains visible without estimated or fabricated values."
            tone="orange"
          />
        </article>
      </section>
    </Shell>
  );
}

function Guidance({
  props,
  general = false,
}: {
  props: Props;
  general?: boolean;
}) {
  const preferred = sessionStorage.getItem("krishimitra.category");
  const selectedCategory = useMemo(
    () =>
      general
        ? props.categories.find((item) => item.slug.includes("other"))
        : (props.categories.find((item) => item.id === preferred) ??
          props.categories.find((item) => item.slug.includes("pest")) ??
          props.categories[0]),
    [general, preferred, props.categories],
  );
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [faqs, setFaqs] = useState<Faq[]>([]);
  const [drawer, setDrawer] = useState(!general);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!props.token || !selectedCategory) return;
    api
      .faqs(props.token, selectedCategory.slug, props.language)
      .then(setFaqs)
      .catch(() => setFaqs([]));
  }, [props.token, props.language, selectedCategory]);
  async function start() {
    if (!props.token || !selectedCategory) return "";
    const value = await api.startGuided(
      props.token,
      selectedCategory.id,
      props.language,
      props.activeCycle?.id,
    );
    setSessionId(value.id);
    setMessages([]);
    return value.id;
  }
  async function chooseHistory(id: string) {
    setSessionId(id);
    setBusy(true);
    setDrawer(false);
    try {
      setMessages(await api.messages(props.token, id));
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Unable to open history",
      );
    } finally {
      setBusy(false);
    }
  }
  async function ask(text = question) {
    if (!text.trim() || !selectedCategory) return;
    setBusy(true);
    setError("");
    try {
      const id = sessionId || (await start());
      if (!id) return;
      const user: Message = {
        id: `local-${crypto.randomUUID()}`,
        chat_session_id: id,
        sender_type: "USER",
        content: text,
        language: props.language,
        created_at: new Date().toISOString(),
      };
      setMessages((old) => [...old, user]);
      setQuestion("");
      const result = await api.ask(props.token, id, text, props.language);
      setMessages((old) => [
        ...old,
        {
          id: result.message_id,
          chat_session_id: id,
          sender_type: "ASSISTANT",
          content: result.answer,
          language: result.language,
          evidence_status: result.evidence_status,
          citations: result.citations,
          created_at: result.created_at,
        },
      ]);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Unable to send question",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <Shell
      props={props}
      title={
        general
          ? "Ask My Question"
          : (selectedCategory?.title ?? "Crop Guidance")
      }
      subtitle={
        general
          ? "Tur guidance with your crop, location and language context"
          : "Guided help backed by verified agricultural sources"
      }
    >
      <div className={`chat-layout ${drawer ? "drawer-open" : ""}`}>
        <aside className={`chat-drawer ${drawer ? "open" : ""}`}>
          <div>
            <h3>Chat History</h3>
            <button onClick={() => setDrawer(false)}>×</button>
          </div>
          <button className="primary wide" onClick={() => void start()}>
            ＋ New Chat
          </button>
          <button className="exit-chat" onClick={() => props.setScreen("home")}>
            ← Exit guidance
          </button>
          <div className="history-list">
            {props.chats
              .filter((item) => !item.is_archived)
              .map((item) => (
                <div key={item.id}>
                  <button onClick={() => void chooseHistory(item.id)}>
                    <b>{item.title ?? "Farmer question"}</b>
                    <small>
                      {new Date(item.updated_at).toLocaleDateString()}
                    </small>
                  </button>
                  <button
                    aria-label="Archive"
                    onClick={() => void api.archiveChat(props.token, item.id)}
                  >
                    ×
                  </button>
                </div>
              ))}
          </div>
        </aside>
        <section className="chat-panel">
          <div className="chat-toolbar">
            <button onClick={() => setDrawer(!drawer)}>
              ☰ <span>History</span>
            </button>
            <div>
              <span className="topic-icon">
                {icon[selectedCategory?.code ?? "OTHER"] ?? "🌿"}
              </span>
              <div>
                <h2>
                  {general ? "Your Tur assistant" : selectedCategory?.title}
                </h2>
                <small>Government evidence mode</small>
              </div>
            </div>
            <button onClick={() => void start()}>＋ New</button>
          </div>
          <div className="quick-questions">
            <span>Common questions</span>
            {faqs.slice(0, 5).map((item) => (
              <button key={item.id} onClick={() => void ask(item.question)}>
                {item.question}
              </button>
            ))}
          </div>
          <div className="messages">
            {!messages.length && (
              <div className="empty-chat">
                <span>🌾</span>
                <h3>How can KrishiMitra help?</h3>
                <p>
                  Select a common question or write your own. Answers are
                  limited by available official evidence.
                </p>
              </div>
            )}
            {messages.map((item) => (
              <article
                key={item.id}
                className={`message ${item.sender_type.toLowerCase()}`}
              >
                <small>
                  {item.sender_type === "USER" ? "You" : "KrishiMitra AI"}
                </small>
                <p>{item.content}</p>
                {item.evidence_status && (
                  <span
                    className={`evidence ${item.evidence_status.toLowerCase()}`}
                  >
                    {item.evidence_status.replaceAll("_", " ")}
                  </span>
                )}
                {item.citations && <SourceList citations={item.citations} />}
              </article>
            ))}
            {busy && (
              <div className="typing">
                KrishiMitra is checking official evidence…
              </div>
            )}
            {error && (
              <StatusCard title="Unable to continue" text={error} tone="red" />
            )}
          </div>
          <form
            className="composer"
            onSubmit={(event) => {
              event.preventDefault();
              void ask();
            }}
          >
            <button
              type="button"
              aria-label="Attach image"
              onClick={() => props.setScreen("upload")}
            >
              ＋
            </button>
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about your Tur crop…"
            />
            <button
              type="button"
              aria-label="Voice input"
              title="Voice input requires browser permission"
            >
              🎙
            </button>
            <button className="send" aria-label="Send" disabled={busy}>
              ➤
            </button>
          </form>
        </section>
      </div>
    </Shell>
  );
}

function CropScreen({ props }: { props: Props }) {
  const cycle = props.activeCycle;
  const farm = props.farms.find((item) => item.id === cycle?.farm_id);
  const [today] = useState(() => Date.now());
  const days = cycle
    ? Math.max(
        0,
        Math.floor(
          (today - new Date(cycle.sowing_date).getTime()) / 86400000,
        ),
      )
    : 0;
  return (
    <Shell
      props={props}
      title="Active Crop Cycle"
      subtitle="Track the current Tur season and ask crop-specific questions"
    >
      <section className="crop-hero card">
        <div>
          <span className="crop-mark">🌱</span>
          <div>
            <small>{cycle?.status ?? "NO ACTIVE CYCLE"}</small>
            <h2>{cycle?.crop_name ?? "Tur crop cycle not configured"}</h2>
            <p>
              {farm
                ? `${farm.name ?? "Farm"} · ${farm.district}, ${farm.state}`
                : "Add a farm and crop cycle to see details"}
            </p>
          </div>
        </div>
        <button className="primary" onClick={() => props.setScreen("guidance")}>
          Ask Guidance for This Crop
        </button>
      </section>
      {cycle ? (
        <>
          <section className="timeline card">
            <h2>Crop stage timeline</h2>
            <div className="timeline-track">
              <span className="done">
                Sowing
                <small>
                  {new Date(cycle.sowing_date).toLocaleDateString()}
                </small>
              </span>
              <span className="done">
                Growing<small>{days} days</small>
              </span>
              <span className="current">
                {cycle.estimated_crop_stage ?? "Current stage"}
                <small>Today</small>
              </span>
              <span>
                Expected harvest
                <small>
                  {cycle.expected_harvest_date
                    ? new Date(cycle.expected_harvest_date).toLocaleDateString()
                    : "Not set"}
                </small>
              </span>
            </div>
          </section>
          <div className="detail-grid">
            <article className="card">
              <h2>Field details</h2>
              <dl>
                <div>
                  <dt>Area</dt>
                  <dd>
                    {farm
                      ? `${farm.area_value} ${farm.area_unit.toLowerCase()}`
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt>Soil</dt>
                  <dd>{farm?.soil_type ?? "Not recorded"}</dd>
                </div>
                <div>
                  <dt>Irrigation</dt>
                  <dd>{farm?.irrigation_type ?? "Not recorded"}</dd>
                </div>
                <div>
                  <dt>Variety</dt>
                  <dd>{cycle.crop_variety ?? "Not recorded"}</dd>
                </div>
              </dl>
            </article>
            <article className="card">
              <h2>Current advisory</h2>
              <p>
                Open guidance to retrieve advice from active government evidence
                for this crop stage.
              </p>
              <button onClick={() => props.setScreen("advisory")}>
                View advisory details →
              </button>
            </article>
          </div>
        </>
      ) : (
        <StatusCard
          title="No active crop cycle"
          text="Create a Tur crop cycle through the existing farmer data workflow before using crop-specific guidance."
          tone="orange"
        />
      )}
    </Shell>
  );
}

function Advisory({ props }: { props: Props }) {
  return (
    <Shell
      props={props}
      title="Advisory Details"
      subtitle="Source-backed guidance for your active Tur crop"
    >
      <section className="advisory-detail">
        <div className="advisory-main card">
          <div className="alert-title">
            <span>🌾</span>
            <div>
              <small>GUIDANCE STATUS</small>
              <h2>Ask for a current crop-stage advisory</h2>
            </div>
            <span className="state muted">Evidence required</span>
          </div>
          <h3>Why this matters</h3>
          <p>
            Advice must match your current crop stage and the active government
            evidence corpus.
          </p>
          <h3>What you should do</h3>
          <p>
            Use the guided question flow. KrishiMitra will return a qualified
            answer or clearly state when evidence is insufficient.
          </p>
          <h3>Best time to act</h3>
          <p>
            No timing is displayed until the backend returns source-backed
            guidance for your question.
          </p>
          <StatusCard
            title="No advisory record contract exists yet"
            text="The approved layout is preserved without inventing advisory content or save state."
            tone="orange"
          />
          <div className="action-row">
            <button className="secondary" disabled>
              ☆ Save
            </button>
            <button
              className="primary"
              onClick={() => props.setScreen("guidance")}
            >
              Ask Follow-up Question
            </button>
          </div>
        </div>
        <aside>
          <div className="card">
            <h2>Official sources</h2>
            <p>Sources appear here after a grounded answer is returned.</p>
          </div>
          <div className="card">
            <h2>Related questions</h2>
            <button onClick={() => props.setScreen("faqs")}>
              Browse popular questions →
            </button>
          </div>
        </aside>
      </section>
    </Shell>
  );
}

function Faqs({ props }: { props: Props }) {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [rows, setRows] = useState<Faq[]>([]);
  const [selected, setSelected] = useState<Faq | null>(null);
  useEffect(() => {
    if (!props.token || !props.categories.length) return;
    Promise.all(
      props.categories.map((item) =>
        api.faqs(props.token, item.slug, props.language).catch(() => []),
      ),
    ).then((groups) => setRows(groups.flat()));
  }, [props.token, props.categories, props.language]);
  const filtered = rows.filter(
    (item) =>
      (filter === "all" || item.category_slug.includes(filter)) &&
      item.question.toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <Shell
      props={props}
      title="Popular Questions"
      subtitle="Verified answers and guided question discovery"
    >
      <section className="faq-search">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search questions…"
        />
        <div>
          {[
            ["all", "All"],
            ["disease", "Crop Health"],
            ["irrigation", "Irrigation"],
            ["fertilizer", "Fertilizer"],
            ["market", "Market"],
          ].map(([id, label]) => (
            <button
              key={id}
              className={filter === id ? "active" : ""}
              onClick={() => setFilter(id)}
            >
              {label}
            </button>
          ))}
        </div>
      </section>
      <div className="faq-list">
        {filtered.map((item) => (
          <article
            key={item.id}
            className={selected?.id === item.id ? "open" : ""}
          >
            <button
              onClick={() =>
                setSelected(selected?.id === item.id ? null : item)
              }
            >
              <span>?</span>
              <b>{item.question}</b>
              <i>{selected?.id === item.id ? "−" : "+"}</i>
            </button>
            {selected?.id === item.id && (
              <div>
                <p>{item.answer}</p>
                <SourceList citations={item.citations} />
                <button
                  className="primary"
                  onClick={() => props.setScreen("guidance")}
                >
                  Ask a related question
                </button>
              </div>
            )}
          </article>
        ))}
        {!filtered.length && (
          <StatusCard
            title="No verified questions found"
            text="Some categories intentionally remain empty when the evidence corpus is insufficient."
            tone="orange"
          />
        )}
      </div>
    </Shell>
  );
}

function Upload({ props }: { props: Props }) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [question, setQuestion] = useState("");
  const [state, setState] = useState("Select an image to begin");
  const [analysis, setAnalysis] = useState<Awaited<
    ReturnType<typeof api.analysis>
  > | null>(null);
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );
  function select(value?: File) {
    if (!value) return;
    if (
      !new Set(["image/jpeg", "image/png", "image/webp"]).has(value.type) ||
      value.size > 10 * 1024 * 1024
    ) {
      setState("Use a JPEG, PNG or WebP image up to 10 MB.");
      return;
    }
    setFile(value);
    setPreview(URL.createObjectURL(value));
    setState("Ready to upload securely");
  }
  async function analyze() {
    if (!file || !props.token) return;
    let chatId = props.chats.find((item) => !item.is_archived)?.id;
    try {
      setState("Preparing secure upload…");
      if (!chatId) {
        const category =
          props.categories.find((item) => item.slug.includes("other")) ??
          props.categories[0];
        if (!category) throw new Error("No guided category is available.");
        chatId = (
          await api.startGuided(
            props.token,
            category.id,
            props.language,
            props.activeCycle?.id,
          )
        ).id;
      }
      const upload = await api.createUpload(props.token, {
        chat_session_id: chatId,
        attachment_type: "IMAGE",
        source_type: "UPLOAD",
        file_name: file.name,
        mime_type: file.type,
        file_size: file.size,
      });
      const form = new FormData();
      Object.entries(upload.form_fields).forEach(([key, value]) =>
        form.append(key, value),
      );
      form.append("file", file);
      setState("Uploading to private storage…");
      const result = await fetch(upload.upload_url, {
        method: "POST",
        body: form,
      });
      if (!result.ok) throw new Error("Secure upload failed.");
      await api.completeUpload(props.token, upload.attachment_id);
      setState("Queued for visual analysis…");
      await api.analyzeUpload(props.token, upload.attachment_id);
      if (!upload.analysis_id)
        throw new Error("Analysis identifier was not returned.");
      for (let attempt = 0; attempt < 20; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        const value = await api.analysis(props.token, upload.analysis_id);
        setAnalysis(value);
        setState(value.status);
        if (
          ["COMPLETED", "FAILED", "IMAGE_INSUFFICIENT"].includes(value.status)
        )
          break;
      }
      if (question.trim() && chatId)
        await api.ask(props.token, chatId, question, props.language, [
          upload.attachment_id,
        ]);
    } catch (reason) {
      setState(reason instanceof Error ? reason.message : "Analysis failed");
    }
  }
  return (
    <Shell
      props={props}
      title="Upload Crop Image"
      subtitle="Secure image analysis with official-evidence grounding"
    >
      <section className="upload-layout">
        <div className="upload-main card">
          {preview ? (
            <div className="image-preview">
              {/* Blob previews are local-only and cannot use Next's remote image optimizer. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={preview} alt="Selected crop" />
              <div>
                <button onClick={() => input.current?.click()}>Replace</button>
                <button
                  onClick={() => {
                    setFile(null);
                    setPreview("");
                    setAnalysis(null);
                  }}
                >
                  Remove
                </button>
              </div>
            </div>
          ) : (
            <button
              className="drop-zone"
              onClick={() => input.current?.click()}
            >
              <span>📷</span>
              <h2>Upload a clear crop image</h2>
              <p>
                Choose a close, well-lit photo showing the affected plant area.
              </p>
              <b>Choose from Device</b>
              <small>JPEG, PNG or WebP · Maximum 10 MB</small>
            </button>
          )}
          <input
            ref={input}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            hidden
            onChange={(e) => select(e.target.files?.[0])}
          />
          <label>
            Optional question
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="What did you notice on the crop?"
            />
          </label>
          <button
            className="primary wide"
            onClick={() => void analyze()}
            disabled={!file}
          >
            Analyze Image
          </button>
        </div>
        <aside>
          <div className="card">
            <h2>Tips for better results</h2>
            <ul>
              <li>Keep the affected area in focus</li>
              <li>Use natural light where possible</li>
              <li>Include both close and wider views</li>
            </ul>
          </div>
          <StatusCard
            title="Analysis status"
            text={state}
            tone={
              state === "FAILED"
                ? "red"
                : state === "COMPLETED"
                  ? "green"
                  : "orange"
            }
          />
          {analysis && (
            <div className="card result-card">
              <h2>Visible observations</h2>
              <pre>
                {JSON.stringify(
                  analysis.observed_symptoms ?? analysis.quality_assessment,
                  null,
                  2,
                )}
              </pre>
              <p>
                Candidate issues are possibilities, not confirmed diagnoses.
              </p>
            </div>
          )}
        </aside>
      </section>
    </Shell>
  );
}

function History({ props }: { props: Props }) {
  const [filter, setFilter] = useState("all");
  return (
    <Shell
      props={props}
      title="Recent Guidance"
      subtitle="Your source-backed questions and conversations"
    >
      <div className="filter-row">
        {["all", "crop health", "weather", "market"].map((item) => (
          <button
            key={item}
            className={filter === item ? "active" : ""}
            onClick={() => setFilter(item)}
          >
            {item}
          </button>
        ))}
      </div>
      <div className="guidance-grid">
        {props.chats
          .filter(
            (item) =>
              filter === "all" ||
              (item.title ?? "").toLowerCase().includes(filter),
          )
          .map((item) => (
            <button
              key={item.id}
              onClick={() => {
                sessionStorage.setItem("krishimitra.chat", item.id);
                props.setScreen("guidance");
              }}
            >
              <span className="guidance-icon">💬</span>
              <div>
                <small>
                  {item.is_archived ? "Archived guidance" : "Conversation"}
                </small>
                <h3>{item.title ?? "Tur crop question"}</h3>
                <p>
                  {item.last_message_at
                    ? new Date(item.last_message_at).toLocaleString()
                    : "No messages yet"}
                </p>
              </div>
              <b>→</b>
            </button>
          ))}
        {!props.chats.length && (
          <StatusCard
            title="No recent guidance"
            text="Your source-backed conversations will appear here."
            tone="orange"
          />
        )}
      </div>
    </Shell>
  );
}
function Notifications({ props }: { props: Props }) {
  return (
    <Shell
      props={props}
      title="Notifications"
      subtitle="Advisory, weather, market and system updates"
    >
      <div className="notification-groups">
        <section>
          <h2>Today</h2>
          <StatusCard
            title="No new verified notifications"
            text="The backend does not currently expose a notification feed. No alerts are fabricated."
            tone="green"
          />
        </section>
        <section>
          <h2>Yesterday</h2>
          <div className="empty-block">No notifications</div>
        </section>
        <section>
          <h2>Earlier</h2>
          <div className="empty-block">No notifications</div>
        </section>
      </div>
    </Shell>
  );
}
function ProfileScreen({ props }: { props: Props }) {
  const c = t(props.language);
  const profile = props.me?.profile;
  const farm = props.farms[0];
  return (
    <Shell
      props={props}
      title={c.profile}
      subtitle="Your account, farm and crop preferences"
    >
      <section className="profile-summary card">
        <div className="profile-avatar">👨🏽‍🌾</div>
        <div>
          <h2>{profile?.full_name ?? "Farmer profile"}</h2>
          <p>{props.me?.phone_number ?? "Phone verified through Cognito"}</p>
          <span className="verified">✓ OTP account</span>
        </div>
      </section>
      <div className="profile-grid">
        <article className="card tint-green">
          <h2>Personal Details</h2>
          <dl>
            <div>
              <dt>Location</dt>
              <dd>
                {profile
                  ? [
                      profile.village,
                      profile.taluka,
                      profile.district,
                      profile.state,
                    ]
                      .filter(Boolean)
                      .join(", ")
                  : "Not completed"}
              </dd>
            </div>
            <div>
              <dt>Preferred language</dt>
              <dd>{props.language.toUpperCase()}</dd>
            </div>
          </dl>
        </article>
        <article className="card tint-blue">
          <h2>Farm Details</h2>
          <dl>
            <div>
              <dt>Farm</dt>
              <dd>{farm?.name ?? "Not added"}</dd>
            </div>
            <div>
              <dt>Area</dt>
              <dd>{farm ? `${farm.area_value} ${farm.area_unit}` : "—"}</dd>
            </div>
          </dl>
        </article>
        <article className="card tint-peach">
          <h2>Crop Cycles</h2>
          <p>
            {props.cycles.length} recorded crop cycle
            {props.cycles.length === 1 ? "" : "s"}
          </p>
          <button onClick={() => props.setScreen("crop")}>
            View crop cycle →
          </button>
        </article>
        <article className="card tint-lavender">
          <h2>Language Preferences</h2>
          <LanguageSwitcher
            value={props.language}
            onChange={props.setLanguage}
          />
          <p>
            The farmer interface and backend response language use this
            selection.
          </p>
        </article>
      </div>
      <div className="settings-list">
        <button onClick={() => props.setScreen("history")}>
          ◴{" "}
          <span>
            Saved Guidance<small>View previous conversations</small>
          </span>
          →
        </button>
        <button onClick={() => props.setScreen("help")}>
          ?{" "}
          <span>
            Help & Support<small>Login and application help</small>
          </span>
          →
        </button>
        <button>
          🔒{" "}
          <span>
            Privacy & Permissions
            <small>Images remain private and expire according to policy</small>
          </span>
          →
        </button>
        <button className="logout" onClick={props.logout}>
          ↪{" "}
          <span>
            {c.logout}
            <small>Return to farmer login</small>
          </span>
          →
        </button>
      </div>
    </Shell>
  );
}

export function FarmerApp(props: Props) {
  if (!props.token && props.screen !== "help")
    return (
      <Login
        language={props.language}
        setLanguage={props.setLanguage}
        setScreen={props.setScreen}
        authenticated={props.authenticated}
      />
    );
  if (props.screen === "login")
    return (
      <Login
        language={props.language}
        setLanguage={props.setLanguage}
        setScreen={props.setScreen}
        authenticated={props.authenticated}
      />
    );
  if (props.screen === "help") return <Help setScreen={props.setScreen} />;
  if (props.screen === "home") return <HomeScreen props={props} />;
  if (props.screen === "weather" || props.screen === "market")
    return <LiveScreen props={props} kind={props.screen} />;
  if (props.screen === "guidance" || props.screen === "ask")
    return <Guidance props={props} general={props.screen === "ask"} />;
  if (props.screen === "crop") return <CropScreen props={props} />;
  if (props.screen === "advisory") return <Advisory props={props} />;
  if (props.screen === "faqs") return <Faqs props={props} />;
  if (props.screen === "upload") return <Upload props={props} />;
  if (props.screen === "history") return <History props={props} />;
  if (props.screen === "notifications") return <Notifications props={props} />;
  return <ProfileScreen props={props} />;
}
