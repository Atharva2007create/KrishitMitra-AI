import { StatusBar } from "expo-status-bar";
import * as ImagePicker from "expo-image-picker";
import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

type Language = "en" | "hi" | "mr";
type Screen =
  | "login"
  | "help"
  | "home"
  | "weather"
  | "market"
  | "guidance"
  | "ask"
  | "crop"
  | "advisory"
  | "faqs"
  | "upload"
  | "history"
  | "notifications"
  | "profile";
type Category = {
  id: string;
  code: string;
  slug: string;
  title: string;
  description: string;
  faq_count: number;
};
type Profile = {
  full_name: string;
  preferred_language: Language;
  state: string;
  district: string;
  taluka: string;
  village?: string;
};
type Cycle = {
  id: string;
  crop_name: string;
  sowing_date: string;
  expected_harvest_date?: string;
  status: string;
  estimated_crop_stage?: string;
};
type Chat = {
  id: string;
  title?: string;
  updated_at: string;
  is_archived: boolean;
};
type Citation = { organization: string; document_title: string };
type Faq = {
  id: string;
  question: string;
  answer: string;
  evidence_status: string;
  citations: Citation[];
};
type Message = {
  id: string;
  sender_type: "USER" | "ASSISTANT";
  content: string;
  evidence_status?: string;
  citations?: Citation[];
};
const API = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  REGION = process.env.EXPO_PUBLIC_AWS_REGION ?? "ap-south-1",
  CLIENT_ID = process.env.EXPO_PUBLIC_COGNITO_CLIENT_ID ?? "",
  COGNITO =
    process.env.EXPO_PUBLIC_COGNITO_ENDPOINT ??
    `https://cognito-idp.${REGION}.amazonaws.com`;
const labels = {
  en: {
    ask: "Ask My Question",
    weather: "Weather",
    market: "Market Prices",
    crop: "Active Crop Cycle",
    popular: "Popular Questions",
    upload: "Upload Crop Image",
    recent: "Recent Guidance",
    profile: "My Profile",
    unavailable: "Official data unavailable",
  },
  hi: {
    ask: "अपना प्रश्न पूछें",
    weather: "मौसम",
    market: "मंडी भाव",
    crop: "सक्रिय फसल चक्र",
    popular: "लोकप्रिय प्रश्न",
    upload: "फसल की फोटो अपलोड करें",
    recent: "हाल की सलाह",
    profile: "मेरी प्रोफ़ाइल",
    unavailable: "आधिकारिक डेटा उपलब्ध नहीं है",
  },
  mr: {
    ask: "माझा प्रश्न विचारा",
    weather: "हवामान",
    market: "बाजारभाव",
    crop: "सक्रिय पीक चक्र",
    popular: "लोकप्रिय प्रश्न",
    upload: "पिकाचा फोटो अपलोड करा",
    recent: "अलीकडील मार्गदर्शन",
    profile: "माझे प्रोफाइल",
    unavailable: "अधिकृत माहिती उपलब्ध नाही",
  },
};
async function auth(target: string, body: Record<string, unknown>) {
  if (!CLIENT_ID) throw new Error("Cognito client is not configured.");
  const r = await fetch(COGNITO, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-amz-json-1.1",
      "X-Amz-Target": `AWSCognitoIdentityProviderService.${target}`,
    },
    body: JSON.stringify(body),
  });
  const v = await r.json();
  if (!r.ok) throw new Error(v.message ?? "Authentication failed");
  return v;
}
async function request<T>(
  path: string,
  token: string,
  init?: RequestInit,
): Promise<T> {
  const r = await fetch(`${API}/api/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...init?.headers,
    },
  });
  if (!r.ok) {
    const v = await r.json().catch(() => ({}));
    throw new Error(
      typeof v.detail === "string"
        ? v.detail
        : (v.detail?.message ?? `Request failed (${r.status})`),
    );
  }
  return r.json() as Promise<T>;
}
function Logo() {
  return (
    <View style={s.logo}>
      <View style={s.logoMark}>
        <Text style={s.white}>✓</Text>
      </View>
      <Text style={s.logoText}>
        KrishiMitra <Text style={s.greenText}>AI</Text>
      </Text>
    </View>
  );
}
function Languages({
  value,
  onChange,
}: {
  value: Language;
  onChange: (v: Language) => void;
}) {
  return (
    <View style={s.languages}>
      {(["en", "hi", "mr"] as Language[]).map((v) => (
        <Pressable
          key={v}
          onPress={() => onChange(v)}
          style={[s.lang, value === v && s.langOn]}
        >
          <Text style={value === v ? s.langOnText : s.small}>
            {v === "en" ? "English" : v === "hi" ? "हिंदी" : "मराठी"}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}
function Card({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone?: "green" | "peach" | "lav" | "blue";
}) {
  return <View style={[s.card, tone && s[tone]]}>{children}</View>;
}
function Empty({ title, text }: { title: string; text: string }) {
  return (
    <View style={s.empty}>
      <Text style={s.info}>i</Text>
      <View style={s.flex}>
        <Text style={s.bold}>{title}</Text>
        <Text style={s.muted}>{text}</Text>
      </View>
    </View>
  );
}
function Header({
  name,
  setScreen,
}: {
  name?: string;
  setScreen: (v: Screen) => void;
}) {
  return (
    <View style={s.header}>
      <Logo />
      <Pressable onPress={() => setScreen("notifications")}>
        <Text style={s.headerIcon}>🔔</Text>
      </Pressable>
      <Pressable style={s.avatar} onPress={() => setScreen("profile")}>
        <Text>👨🏽‍🌾</Text>
        <Text style={s.avatarText}>{name?.split(" ")[0] ?? "Farmer"}</Text>
      </Pressable>
    </View>
  );
}
function Bottom({ setScreen }: { setScreen: (v: Screen) => void }) {
  return (
    <View style={s.bottom}>
      {[
        ["home", "⌂", "Home"],
        ["guidance", "✦", "Guidance"],
        ["history", "◴", "History"],
        ["profile", "♙", "Profile"],
      ].map(([id, glyph, label]) => (
        <Pressable
          key={id}
          onPress={() => setScreen(id as Screen)}
          style={s.bottomItem}
        >
          <Text style={s.bottomGlyph}>{glyph}</Text>
          <Text style={s.bottomLabel}>{label}</Text>
        </Pressable>
      ))}
    </View>
  );
}
function Shell({
  children,
  title,
  language,
  setLanguage,
  setScreen,
  name,
}: {
  children: React.ReactNode;
  title: string;
  language: Language;
  setLanguage: (v: Language) => void;
  setScreen: (v: Screen) => void;
  name?: string;
}) {
  return (
    <SafeAreaView style={s.safe}>
      <StatusBar style="dark" />
      <Header name={name} setScreen={setScreen} />
      <ScrollView
        contentContainerStyle={s.content}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={s.pageTitle}>{title}</Text>
        {children}
      </ScrollView>
      <Bottom setScreen={setScreen} />
    </SafeAreaView>
  );
}
function Login({
  language,
  setLanguage,
  onLogin,
  setScreen,
}: {
  language: Language;
  setLanguage: (v: Language) => void;
  onLogin: (v: string) => void;
  setScreen: (v: Screen) => void;
}) {
  const [phone, setPhone] = useState(""),
    [otp, setOtp] = useState(""),
    [session, setSession] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit() {
    setBusy(true);
    try {
      if (!session) {
        const v = await auth("InitiateAuth", {
          AuthFlow: "USER_AUTH",
          ClientId: CLIENT_ID,
          AuthParameters: { USERNAME: phone, PREFERRED_CHALLENGE: "SMS_OTP" },
        });
        if (!v.Session) throw new Error("SMS OTP challenge did not start.");
        setSession(v.Session);
      } else {
        const v = await auth("RespondToAuthChallenge", {
          ClientId: CLIENT_ID,
          ChallengeName: "SMS_OTP",
          Session: session,
          ChallengeResponses: { USERNAME: phone, SMS_OTP: otp },
        });
        const token =
          v.AuthenticationResult?.AccessToken ??
          v.AuthenticationResult?.IdToken;
        if (!token) throw new Error("Authentication token was not returned.");
        onLogin(token);
      }
    } catch (e) {
      Alert.alert("Login", e instanceof Error ? e.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }
  return (
    <SafeAreaView style={s.login}>
      <StatusBar style="dark" />
      <View style={s.loginHero}>
        <Logo />
        <Text style={s.kicker}>🌿 Smart Tur farming support</Text>
        <Text style={s.loginTitle}>
          AI-Powered Guidance for Better Tur Farming
        </Text>
        <Text style={s.field}>🌱　🌿　🌾</Text>
      </View>
      <ScrollView contentContainerStyle={s.loginCard}>
        <Languages value={language} onChange={setLanguage} />
        <Text style={s.profileIcon}>🌱</Text>
        <Text style={s.centerTitle}>Farmer Login</Text>
        <Text style={s.centerMuted}>Secure access with your mobile number</Text>
        <Text style={s.label}>Mobile number</Text>
        <TextInput
          style={s.input}
          value={phone}
          onChangeText={setPhone}
          keyboardType="phone-pad"
          placeholder="+91 98765 43210"
          editable={!session}
        />
        {session && (
          <>
            <Text style={s.label}>One-time password</Text>
            <TextInput
              style={s.input}
              value={otp}
              onChangeText={setOtp}
              keyboardType="number-pad"
              placeholder="Enter 6-digit OTP"
            />
          </>
        )}
        <Pressable style={s.primary} onPress={submit} disabled={busy}>
          <Text style={s.whiteBold}>
            {busy ? "Please wait…" : session ? "Verify & Login" : "Send OTP"}
          </Text>
        </Pressable>
        <Pressable onPress={() => setScreen("help")}>
          <Text style={s.helpLink}>Need Help?</Text>
        </Pressable>
        <Empty
          title="Secure OTP login"
          text="We never ask for your password."
        />
      </ScrollView>
    </SafeAreaView>
  );
}

export default function App() {
  const [token, setToken] = useState(""),
    [language, setLanguage] = useState<Language>("en"),
    [screen, setScreen] = useState<Screen>("login"),
    [profile, setProfile] = useState<Profile | null>(null),
    [cycles, setCycles] = useState<Cycle[]>([]),
    [categories, setCategories] = useState<Category[]>([]),
    [chats, setChats] = useState<Chat[]>([]),
    [selected, setSelected] = useState<Category | null>(null);
  const L = labels[language];
  useEffect(() => {
    if (!token) return;
    Promise.all([
      request<{ profile?: Profile }>("/me", token),
      request<Cycle[]>("/crop-cycles", token),
      request<Category[]>(`/problem-categories?language=${language}`, token),
      request<Chat[]>("/chat/sessions", token),
    ])
      .then(([me, cats, groups, history]) => {
        setProfile(me.profile ?? null);
        setCycles(cats);
        setCategories(groups);
        setChats(history);
      })
      .catch((e) => Alert.alert("KrishiMitra", e.message));
  }, [token, language]);
  const shell = { language, setLanguage, setScreen, name: profile?.full_name };
  if (!token && screen !== "help")
    return (
      <Login
        {...{
          language,
          setLanguage,
          onLogin: (v: string) => {
            setToken(v);
            setScreen("home");
          },
          setScreen,
        }}
      />
    );
  if (screen === "help")
    return (
      <SafeAreaView style={s.safe}>
        <ScrollView contentContainerStyle={s.content}>
          <Pressable onPress={() => setScreen("login")}>
            <Text style={s.back}>← Back to login</Text>
          </Pressable>
          <Logo />
          <Text style={s.pageTitle}>How can we help?</Text>
          {[
            [
              "📱",
              "OTP not received",
              "Check your number, signal and SMS inbox.",
            ],
            ["🌐", "Language selection", "Choose English, हिंदी or मराठी."],
            ["🛠", "Troubleshooting", "Use only the newest OTP code."],
            ["❓", "Account safety", "Never share an OTP with anyone."],
          ].map(([i, h, p]) => (
            <Card key={h}>
              <Text style={s.icon}>{i}</Text>
              <Text style={s.bold}>{h}</Text>
              <Text style={s.muted}>{p}</Text>
            </Card>
          ))}
          <Empty
            title="Support contacts are being configured"
            text="Placeholder contacts are not shown as official support."
          />
        </ScrollView>
      </SafeAreaView>
    );
  if (screen === "home")
    return (
      <Shell
        {...shell}
        title={`Welcome${profile ? `, ${profile.full_name.split(" ")[0]}` : ""}!`}
      >
        <Pressable style={s.ask} onPress={() => setScreen("ask")}>
          <Text style={s.askIcon}>✦</Text>
          <View style={s.flex}>
            <Text style={s.askTitle}>{L.ask}</Text>
            <Text style={s.muted}>
              Government-evidence-backed crop guidance
            </Text>
          </View>
          <Text>→</Text>
        </Pressable>
        <View style={s.row}>
          <Pressable
            style={[s.card, s.green, s.flex]}
            onPress={() => setScreen("crop")}
          >
            <Text style={s.kicker}>{L.crop}</Text>
            <Text style={s.bold}>
              {cycles.find((c) => c.status === "ACTIVE")?.crop_name ??
                "No active cycle"}
            </Text>
            <Text style={s.muted}>
              {cycles.find((c) => c.status === "ACTIVE")
                ?.estimated_crop_stage ?? "Add crop stage details"}
            </Text>
          </Pressable>
          <Pressable
            style={[s.card, s.blue, s.flex]}
            onPress={() => setScreen("weather")}
          >
            <Text style={s.icon}>🌦</Text>
            <Text style={s.bold}>{L.weather}</Text>
            <Text style={s.muted}>{L.unavailable}</Text>
          </Pressable>
        </View>
        <Pressable
          style={[s.card, s.peach]}
          onPress={() => setScreen("market")}
        >
          <Text style={s.icon}>₹</Text>
          <Text style={s.bold}>{L.market}</Text>
          <Text style={s.muted}>
            Verified market records appear only when available.
          </Text>
        </Pressable>
        <Text style={s.section}>What can we help you with?</Text>
        <View style={s.categoryGrid}>
          {categories.slice(0, 12).map((c, i) => (
            <Pressable
              key={c.id}
              style={[
                s.category,
                i % 4 === 1 && s.peach,
                i % 4 === 2 && s.lav,
                i % 4 === 3 && s.blue,
              ]}
              onPress={() => {
                setSelected(c);
                setScreen("guidance");
              }}
            >
              <Text style={s.icon}>
                {c.code.includes("PEST")
                  ? "🐛"
                  : c.code.includes("IRRIGATION")
                    ? "💧"
                    : "🌿"}
              </Text>
              <Text style={s.categoryText}>{c.title}</Text>
            </Pressable>
          ))}
        </View>
        {[
          ["advisory", "🌾", "Advisory Details"],
          ["faqs", "❓", L.popular],
          ["upload", "📷", L.upload],
          ["history", "◴", L.recent],
        ].map(([id, i, h]) => (
          <Pressable
            key={id}
            style={s.feature}
            onPress={() => setScreen(id as Screen)}
          >
            <Text style={s.icon}>{i}</Text>
            <Text style={[s.bold, s.flex]}>{h}</Text>
            <Text>→</Text>
          </Pressable>
        ))}
      </Shell>
    );
  if (screen === "weather" || screen === "market")
    return <Live {...shell} token={token} profile={profile} kind={screen} />;
  if (screen === "guidance" || screen === "ask")
    return (
      <ChatScreen
        {...shell}
        token={token}
        category={
          screen === "ask"
            ? (categories.find((c) => c.slug.includes("other")) ??
              categories[0])
            : (selected ??
              categories.find((c) => c.slug.includes("pest")) ??
              categories[0])
        }
        chats={chats}
        general={screen === "ask"}
      />
    );
  if (screen === "faqs")
    return <FaqScreen {...shell} token={token} categories={categories} />;
  if (screen === "upload")
    return (
      <Upload {...shell} token={token} categories={categories} chats={chats} />
    );
  if (screen === "crop")
    return (
      <InfoScreen
        {...shell}
        title={L.crop}
        icon="🌱"
        rows={
          cycles.length
            ? cycles.map((c) => ({
                title: `${c.crop_name} · ${c.status}`,
                text: `Sown ${new Date(c.sowing_date).toLocaleDateString()} · ${c.estimated_crop_stage ?? "Stage not recorded"}`,
              }))
            : [
                {
                  title: "No active crop cycle",
                  text: "Create a Tur crop cycle before crop-specific guidance.",
                },
              ]
        }
        action={() => setScreen("guidance")}
        actionLabel="Ask Guidance for This Crop"
      />
    );
  if (screen === "advisory")
    return (
      <InfoScreen
        {...shell}
        title="Advisory Details"
        icon="🌾"
        rows={[
          {
            title: "Why this matters",
            text: "Advice must match your crop stage and active government evidence.",
          },
          {
            title: "What you should do",
            text: "Ask a guided question to receive qualified guidance.",
          },
          {
            title: "Save status",
            text: "No advisory-save contract exists, so no save is fabricated.",
          },
        ]}
        action={() => setScreen("guidance")}
        actionLabel="Ask Follow-up Question"
      />
    );
  if (screen === "history")
    return (
      <InfoScreen
        {...shell}
        title={L.recent}
        icon="◴"
        rows={
          chats.length
            ? chats.map((c) => ({
                title: c.title ?? "Tur crop question",
                text: new Date(c.updated_at).toLocaleString(),
              }))
            : [
                {
                  title: "No recent guidance",
                  text: "Your conversations will appear here.",
                },
              ]
        }
      />
    );
  if (screen === "notifications")
    return (
      <InfoScreen
        {...shell}
        title="Notifications"
        icon="🔔"
        rows={[
          { title: "Today", text: "No new verified notifications." },
          { title: "Yesterday", text: "No notifications" },
          { title: "Earlier", text: "No notifications" },
        ]}
      />
    );
  return (
    <Shell {...shell} title={L.profile}>
      <Card tone="green">
        <Text style={s.profileIcon}>👨🏽‍🌾</Text>
        <Text style={s.centerTitle}>
          {profile?.full_name ?? "Farmer profile"}
        </Text>
        <Text style={s.centerMuted}>
          {profile
            ? [profile.village, profile.taluka, profile.district, profile.state]
                .filter(Boolean)
                .join(", ")
            : "Complete your farmer profile"}
        </Text>
      </Card>
      <Text style={s.section}>Language Preferences</Text>
      <Card>
        <Languages value={language} onChange={setLanguage} />
      </Card>
      {[
        ["crop", "🌱", "Crop Cycles"],
        ["history", "◴", "Saved Guidance"],
        ["help", "?", "Help & Support"],
      ].map(([id, i, h]) => (
        <Pressable
          key={id}
          style={s.feature}
          onPress={() => setScreen(id as Screen)}
        >
          <Text style={s.icon}>{i}</Text>
          <Text style={[s.bold, s.flex]}>{h}</Text>
          <Text>→</Text>
        </Pressable>
      ))}
      <Pressable
        style={s.logout}
        onPress={() => {
          setToken("");
          setScreen("login");
        }}
      >
        <Text style={s.logoutText}>↪ Logout</Text>
      </Pressable>
    </Shell>
  );
}

function Live({
  token,
  profile,
  kind,
  ...shell
}: {
  token: string;
  profile: Profile | null;
  kind: "weather" | "market";
  language: Language;
  setLanguage: (v: Language) => void;
  setScreen: (v: Screen) => void;
  name?: string;
}) {
  const [data, setData] = useState<Record<string, unknown>[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(Boolean(profile));
  useEffect(() => {
    if (!profile) return;
    const p =
      kind === "weather"
        ? `/live/weather?state=${encodeURIComponent(profile.state)}&district=${encodeURIComponent(profile.district)}`
        : `/live/markets?state=${encodeURIComponent(profile.state)}&district=${encodeURIComponent(profile.district)}`;
    request<Record<string, unknown>>(p, token)
      .then((v) =>
        setData(
          (v[kind === "weather" ? "observations" : "prices"] as Record<
            string,
            unknown
          >[]) ?? [],
        ),
      )
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  }, [token, profile, kind]);
  return (
    <Shell
      {...shell}
      title={
        kind === "weather"
          ? "Weather Forecast & Advisory"
          : "Market Prices & Selling Insights"
      }
    >
      <Card tone={kind === "weather" ? "blue" : "green"}>
        <Text style={s.icon}>{kind === "weather" ? "🌦" : "₹"}</Text>
        <Text style={s.bold}>
          {profile
            ? `${profile.district}, ${profile.state}`
            : "Location required"}
        </Text>
        <Text style={s.muted}>
          {busy
            ? "Loading official source…"
            : data.length
              ? "Official records available"
              : "Official source unavailable"}
        </Text>
      </Card>
      {busy && <ActivityIndicator color="#087f45" />}
      {error ? (
        <Empty
          title="Official live data unavailable"
          text={`${error}. No values are estimated.`}
        />
      ) : (
        data.map((r, i) => (
          <Card key={i}>
            <Text style={s.bold}>
              {String(
                r[kind === "weather" ? "station_name" : "market"] ??
                  "Official record",
              )}
            </Text>
            <Text style={s.muted}>
              {kind === "weather"
                ? `${String(r.temperature_c ?? "Not reported")}°C · Humidity ${String(r.relative_humidity_percent ?? "—")}%`
                : `Modal ₹${String(r.modal_price ?? "not reported")} · Min ₹${String(r.minimum_price ?? "—")} · Max ₹${String(r.maximum_price ?? "—")}`}
            </Text>
          </Card>
        ))
      )}
      <Text style={s.section}>
        {kind === "weather" ? "Seven-day forecast" : "Historical trend"}
      </Text>
      <Empty
        title="Not available from the current backend contract"
        text="The approved area remains visible without fabricated values."
      />
    </Shell>
  );
}
function ChatScreen({
  token,
  category,
  chats,
  general,
  ...shell
}: {
  token: string;
  category?: Category;
  chats: Chat[];
  general: boolean;
  language: Language;
  setLanguage: (v: Language) => void;
  setScreen: (v: Screen) => void;
  name?: string;
}) {
  const [faqs, setFaqs] = useState<Faq[]>([]),
    [messages, setMessages] = useState<Message[]>([]),
    [question, setQuestion] = useState(""),
    [sessionId, setSessionId] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    if (category)
      request<Faq[]>(
        `/problem-categories/${category.slug}/faqs?language=${shell.language}`,
        token,
      )
        .then(setFaqs)
        .catch(() => setFaqs([]));
  }, [category, token, shell.language]);
  async function openHistory(id: string) {
    setBusy(true);
    try {
      setMessages(
        await request<Message[]>(`/chat/sessions/${id}/messages`, token),
      );
      setSessionId(id);
    } catch (e) {
      Alert.alert(
        "Chat History",
        e instanceof Error ? e.message : "Unable to open conversation",
      );
    } finally {
      setBusy(false);
    }
  }
  async function ask(text = question) {
    if (!category || !text.trim()) return;
    setBusy(true);
    try {
      let id = sessionId;
      if (!id) {
        id = (
          await request<{ id: string }>("/assistance/sessions", token, {
            method: "POST",
            body: JSON.stringify({
              problem_category_id: category.id,
              language: shell.language,
            }),
          })
        ).id;
        setSessionId(id);
      }
      setMessages((v) => [
        ...v,
        { id: `local-${Date.now()}`, sender_type: "USER", content: text },
      ]);
      setQuestion("");
      const r = await request<{
        message_id: string;
        answer: string;
        evidence_status: string;
        citations: Citation[];
      }>(`/assistance/sessions/${id}/questions`, token, {
        method: "POST",
        body: JSON.stringify({
          question: text,
          language: shell.language,
          attachment_ids: [],
        }),
      });
      setMessages((v) => [
        ...v,
        {
          id: r.message_id,
          sender_type: "ASSISTANT",
          content: r.answer,
          evidence_status: r.evidence_status,
          citations: r.citations,
        },
      ]);
    } catch (e) {
      Alert.alert(
        "Guidance",
        e instanceof Error ? e.message : "Unable to answer",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <Shell
      {...shell}
      title={general ? "Ask My Question" : (category?.title ?? "Crop Guidance")}
    >
      <ScrollView horizontal style={s.quick}>
        {faqs.slice(0, 5).map((f) => (
          <Pressable
            key={f.id}
            style={s.quickButton}
            onPress={() => ask(f.question)}
          >
            <Text style={s.quickText}>{f.question}</Text>
          </Pressable>
        ))}
      </ScrollView>
      {!messages.length && (
        <View style={s.chatEmpty}>
          <Text style={s.profileIcon}>🌾</Text>
          <Text style={s.centerTitle}>How can KrishiMitra help?</Text>
          <Text style={s.centerMuted}>
            Answers are limited by available official evidence.
          </Text>
        </View>
      )}
      {messages.map((m) => (
        <View
          key={m.id}
          style={[s.message, m.sender_type === "USER" && s.userMessage]}
        >
          <Text style={s.messageWho}>
            {m.sender_type === "USER" ? "You" : "KrishiMitra AI"}
          </Text>
          <Text style={s.messageText}>{m.content}</Text>
          {m.evidence_status && (
            <Text style={s.evidence}>
              {m.evidence_status.replaceAll("_", " ")}
            </Text>
          )}
          {m.citations?.map((c, i) => (
            <Text key={i} style={s.citation}>
              ✓ {c.organization} · {c.document_title}
            </Text>
          ))}
        </View>
      ))}
      {busy && <ActivityIndicator color="#087f45" />}
      <View style={s.composer}>
        <Pressable
          onPress={() => shell.setScreen("upload")}
          style={s.composerButton}
        >
          <Text>＋</Text>
        </Pressable>
        <TextInput
          style={s.composerInput}
          value={question}
          onChangeText={setQuestion}
          placeholder="Ask about your Tur crop…"
          multiline
        />
        <Pressable style={s.composerButton}>
          <Text>🎙</Text>
        </Pressable>
        <Pressable onPress={() => ask()} style={s.send}>
          <Text style={s.white}>➤</Text>
        </Pressable>
      </View>
      <Text style={s.section}>Chat History</Text>
      {chats.slice(0, 5).map((c) => (
        <Pressable key={c.id} onPress={() => openHistory(c.id)}>
          <Card>
            <Text style={s.bold}>{c.title ?? "Farmer question"}</Text>
            <Text style={s.muted}>
              {new Date(c.updated_at).toLocaleString()}
            </Text>
          </Card>
        </Pressable>
      ))}
    </Shell>
  );
}
function FaqScreen({
  token,
  categories,
  ...shell
}: {
  token: string;
  categories: Category[];
  language: Language;
  setLanguage: (v: Language) => void;
  setScreen: (v: Screen) => void;
  name?: string;
}) {
  const [rows, setRows] = useState<Faq[]>([]),
    [search, setSearch] = useState(""),
    [open, setOpen] = useState("");
  useEffect(() => {
    Promise.all(
      categories.map((c) =>
        request<Faq[]>(
          `/problem-categories/${c.slug}/faqs?language=${shell.language}`,
          token,
        ).catch(() => []),
      ),
    ).then((v) => setRows(v.flat()));
  }, [categories, token, shell.language]);
  return (
    <Shell {...shell} title="Popular Questions">
      <TextInput
        style={s.input}
        value={search}
        onChangeText={setSearch}
        placeholder="Search questions…"
      />
      {rows
        .filter((f) => f.question.toLowerCase().includes(search.toLowerCase()))
        .map((f) => (
          <Pressable
            key={f.id}
            style={s.faq}
            onPress={() => setOpen(open === f.id ? "" : f.id)}
          >
            <Text style={s.faqQ}>?　{f.question}</Text>
            {open === f.id && (
              <>
                <Text style={s.muted}>{f.answer}</Text>
                {f.citations.map((c, i) => (
                  <Text key={i} style={s.citation}>
                    ✓ {c.organization} · {c.document_title}
                  </Text>
                ))}
              </>
            )}
          </Pressable>
        ))}
      {!rows.length && (
        <Empty
          title="No verified questions"
          text="Some categories remain empty when evidence is insufficient."
        />
      )}
    </Shell>
  );
}
function Upload({
  token,
  categories,
  chats,
  ...shell
}: {
  token: string;
  categories: Category[];
  chats: Chat[];
  language: Language;
  setLanguage: (v: Language) => void;
  setScreen: (v: Screen) => void;
  name?: string;
}) {
  const [asset, setAsset] = useState<ImagePicker.ImagePickerAsset | null>(null),
    [state, setState] = useState("Select an image to begin"),
    [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null);
  async function pick(camera: boolean) {
    const p = camera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!p.granted) {
      setState("Permission was not granted.");
      return;
    }
    const r = camera
      ? await ImagePicker.launchCameraAsync({
          mediaTypes: ["images"],
          quality: 0.9,
        })
      : await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ["images"],
          quality: 0.9,
        });
    if (!r.canceled && r.assets[0]) setAsset(r.assets[0]);
  }
  async function analyze() {
    if (!asset) return;
    try {
      setState("Preparing secure upload…");
      let chatId = chats.find((c) => !c.is_archived)?.id;
      if (!chatId) {
        const c =
          categories.find((x) => x.slug.includes("other")) ?? categories[0];
        if (!c) throw new Error("No guided category is available.");
        chatId = (
          await request<{ id: string }>("/assistance/sessions", token, {
            method: "POST",
            body: JSON.stringify({
              problem_category_id: c.id,
              language: shell.language,
            }),
          })
        ).id;
      }
      const name = asset.fileName ?? `crop-${Date.now()}.jpg`,
        mime = asset.mimeType ?? "image/jpeg";
      const u = await request<{
        attachment_id: string;
        analysis_id?: string;
        upload_url: string;
        form_fields: Record<string, string>;
      }>("/attachments/upload", token, {
        method: "POST",
        body: JSON.stringify({
          chat_session_id: chatId,
          attachment_type: "IMAGE",
          source_type: "CAMERA",
          file_name: name,
          mime_type: mime,
          file_size: asset.fileSize ?? 1,
        }),
      });
      const form = new FormData();
      Object.entries(u.form_fields).forEach(([k, v]) => form.append(k, v));
      form.append("file", {
        uri: asset.uri,
        name,
        type: mime,
      } as unknown as Blob);
      setState("Uploading securely…");
      const r = await fetch(u.upload_url, { method: "POST", body: form });
      if (!r.ok) throw new Error("Secure upload failed");
      await request(`/attachments/${u.attachment_id}/complete`, token, {
        method: "POST",
      });
      const queued = await request<{ id?: string; status?: string }>(
        `/attachments/${u.attachment_id}/analyze`,
        token,
        {
          method: "POST",
        },
      );
      const analysisId = u.analysis_id ?? queued.id;
      if (!analysisId) throw new Error("Analysis identifier was not returned");
      setState("Analyzing image…");
      for (let attempt = 0; attempt < 20; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        const value = await request<Record<string, unknown>>(
          `/image-analyses/${analysisId}`,
          token,
        );
        setAnalysis(value);
        const status = String(value.status ?? "PROCESSING");
        setState(status.replaceAll("_", " "));
        if (["COMPLETED", "FAILED", "IMAGE_INSUFFICIENT"].includes(status))
          break;
      }
    } catch (e) {
      setState(e instanceof Error ? e.message : "Analysis failed");
    }
  }
  return (
    <Shell {...shell} title="Upload Crop Image">
      <Card>
        <Pressable style={s.uploadBox} onPress={() => pick(false)}>
          {asset ? (
            <Image source={{ uri: asset.uri }} style={s.preview} />
          ) : (
            <>
              <Text style={s.uploadIcon}>📷</Text>
              <Text style={s.centerTitle}>Upload a clear crop image</Text>
              <Text style={s.centerMuted}>
                JPEG, PNG or WebP · Maximum 10 MB
              </Text>
            </>
          )}
        </Pressable>
        <View style={s.row}>
          <Pressable style={s.secondary} onPress={() => pick(false)}>
            <Text style={s.secondaryText}>Choose Device</Text>
          </Pressable>
          <Pressable style={s.secondary} onPress={() => pick(true)}>
            <Text style={s.secondaryText}>Take Photo</Text>
          </Pressable>
        </View>
        <Pressable
          style={[s.primary, !asset && s.disabled]}
          onPress={analyze}
          disabled={!asset}
        >
          <Text style={s.whiteBold}>Analyze Image</Text>
        </Pressable>
      </Card>
      <Empty title="Analysis status" text={state} />
      {analysis && (
        <Card tone="green">
          <Text style={s.bold}>Visible observations</Text>
          <Text style={s.muted}>
            {JSON.stringify(
              analysis.observed_symptoms ?? analysis.quality_assessment ?? {},
              null,
              2,
            )}
          </Text>
          <Text style={s.muted}>
            Candidate issues are possibilities, not confirmed diagnoses.
          </Text>
        </Card>
      )}
    </Shell>
  );
}
function InfoScreen({
  title,
  icon,
  rows,
  action,
  actionLabel,
  ...shell
}: {
  title: string;
  icon: string;
  rows: { title: string; text: string }[];
  action?: () => void;
  actionLabel?: string;
  language: Language;
  setLanguage: (v: Language) => void;
  setScreen: (v: Screen) => void;
  name?: string;
}) {
  return (
    <Shell {...shell} title={title}>
      <Card>
        <Text style={s.profileIcon}>{icon}</Text>
        {rows.map((r, i) => (
          <View key={i} style={s.infoRow}>
            <Text style={s.bold}>{r.title}</Text>
            <Text style={s.muted}>{r.text}</Text>
          </View>
        ))}
        {action && (
          <Pressable style={s.primary} onPress={action}>
            <Text style={s.whiteBold}>{actionLabel}</Text>
          </Pressable>
        )}
      </Card>
    </Shell>
  );
}
const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#fffdf5" },
  flex: { flex: 1 },
  white: { color: "#fff" },
  whiteBold: { color: "#fff", fontWeight: "900" },
  greenText: { color: "#087f45" },
  small: { fontSize: 11, color: "#647064" },
  bold: { fontSize: 14, fontWeight: "900", color: "#17233d" },
  muted: { fontSize: 11, color: "#647064", lineHeight: 16, marginTop: 4 },
  green: { backgroundColor: "#edf9ed" },
  peach: { backgroundColor: "#fff0df" },
  lav: { backgroundColor: "#f0ecff" },
  blue: { backgroundColor: "#e8f5ff" },
  logo: { flexDirection: "row", alignItems: "center", gap: 7 },
  logoMark: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#087f45",
    alignItems: "center",
    justifyContent: "center",
  },
  logoText: { fontWeight: "900", fontSize: 17, color: "#17233d" },
  languages: {
    flexDirection: "row",
    alignSelf: "center",
    gap: 4,
    marginVertical: 10,
  },
  lang: { paddingHorizontal: 10, paddingVertical: 7, borderRadius: 7 },
  langOn: { backgroundColor: "#e7f6e9" },
  langOnText: { fontSize: 11, color: "#087f45", fontWeight: "900" },
  login: { flex: 1, backgroundColor: "#fff" },
  loginHero: {
    height: 255,
    padding: 20,
    backgroundColor: "#e8f6dd",
    overflow: "hidden",
  },
  kicker: {
    fontSize: 10,
    fontWeight: "900",
    color: "#087f45",
    textTransform: "uppercase",
    marginTop: 12,
  },
  loginTitle: {
    fontSize: 31,
    lineHeight: 35,
    fontWeight: "900",
    color: "#17233d",
    marginTop: 8,
    maxWidth: 330,
  },
  field: {
    position: "absolute",
    bottom: -16,
    left: 10,
    right: 10,
    textAlign: "center",
    fontSize: 76,
    opacity: 0.5,
  },
  loginCard: {
    marginTop: -20,
    padding: 22,
    paddingBottom: 40,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    backgroundColor: "#fff",
  },
  profileIcon: { fontSize: 42, textAlign: "center", marginTop: 8 },
  centerTitle: {
    fontSize: 19,
    fontWeight: "900",
    color: "#17233d",
    textAlign: "center",
    marginTop: 10,
  },
  centerMuted: {
    fontSize: 12,
    color: "#647064",
    textAlign: "center",
    lineHeight: 18,
  },
  label: {
    fontSize: 12,
    fontWeight: "800",
    color: "#17233d",
    marginTop: 14,
    marginBottom: 5,
  },
  input: {
    borderWidth: 1.5,
    borderColor: "#a9b8ad",
    borderRadius: 9,
    padding: 12,
    backgroundColor: "#fff",
  },
  primary: {
    marginTop: 12,
    borderRadius: 9,
    padding: 14,
    alignItems: "center",
    backgroundColor: "#087f45",
  },
  helpLink: {
    textAlign: "center",
    color: "#087f45",
    fontWeight: "800",
    padding: 14,
  },
  header: {
    height: 58,
    paddingHorizontal: 12,
    flexDirection: "row",
    alignItems: "center",
    borderBottomWidth: 1,
    borderBottomColor: "#dfe7df",
    backgroundColor: "#fff",
    gap: 8,
  },
  headerIcon: { fontSize: 19 },
  avatar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    borderWidth: 1,
    borderColor: "#d8e2d9",
    padding: 6,
    borderRadius: 18,
  },
  avatarText: { fontSize: 11, fontWeight: "700" },
  content: { padding: 12, paddingBottom: 85, gap: 10 },
  pageTitle: {
    fontSize: 23,
    fontWeight: "900",
    color: "#17233d",
    marginBottom: 4,
  },
  back: { fontWeight: "800", marginBottom: 16 },
  bottom: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    height: 64,
    flexDirection: "row",
    borderTopWidth: 1,
    borderTopColor: "#d7e0d8",
    backgroundColor: "#fff",
  },
  bottomItem: { flex: 1, alignItems: "center", justifyContent: "center" },
  bottomGlyph: { color: "#087f45", fontSize: 18, fontWeight: "900" },
  bottomLabel: { fontSize: 9, color: "#087f45" },
  card: {
    borderWidth: 1.4,
    borderColor: "#42594c",
    borderRadius: 12,
    padding: 14,
    backgroundColor: "#fff",
  },
  empty: {
    flexDirection: "row",
    gap: 10,
    borderWidth: 1,
    borderColor: "#e0be88",
    borderRadius: 9,
    padding: 12,
    backgroundColor: "#fff6e8",
  },
  info: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: "#d78918",
    color: "#fff",
    fontWeight: "900",
    textAlign: "center",
    paddingTop: 2,
  },
  ask: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderWidth: 1.5,
    borderColor: "#2d503c",
    borderRadius: 13,
    padding: 15,
    backgroundColor: "#e9f8e7",
  },
  askIcon: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: "#087f45",
    color: "#fff",
    fontSize: 20,
    textAlign: "center",
    paddingTop: 8,
  },
  askTitle: { fontWeight: "900", fontSize: 16, color: "#17233d" },
  row: { flexDirection: "row", gap: 8 },
  section: { fontSize: 16, fontWeight: "900", marginTop: 12, color: "#17233d" },
  categoryGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  category: {
    width: "48.7%",
    minHeight: 95,
    borderWidth: 1.2,
    borderColor: "#42594c",
    borderRadius: 10,
    padding: 11,
    backgroundColor: "#fff",
  },
  categoryText: {
    fontSize: 12,
    fontWeight: "800",
    color: "#17233d",
    marginTop: 7,
  },
  feature: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderWidth: 1.2,
    borderColor: "#aebcaf",
    borderRadius: 10,
    padding: 12,
    backgroundColor: "#fff",
  },
  icon: { fontSize: 22 },
  quick: { maxHeight: 55 },
  quickButton: {
    borderWidth: 1,
    borderColor: "#a7b8aa",
    borderRadius: 16,
    paddingHorizontal: 11,
    paddingVertical: 7,
    marginRight: 6,
    backgroundColor: "#fff",
  },
  quickText: { fontSize: 10, color: "#17233d" },
  chatEmpty: { paddingVertical: 45, alignItems: "center" },
  message: {
    alignSelf: "flex-start",
    maxWidth: "88%",
    borderWidth: 1,
    borderColor: "#b8c6ba",
    borderRadius: 11,
    padding: 11,
    backgroundColor: "#fff",
  },
  userMessage: { alignSelf: "flex-end", backgroundColor: "#e7f6e9" },
  messageWho: { fontSize: 9, fontWeight: "900", color: "#087f45" },
  messageText: { fontSize: 12, lineHeight: 18, color: "#17233d", marginTop: 4 },
  evidence: { fontSize: 9, fontWeight: "900", color: "#9a5a00", marginTop: 7 },
  citation: { fontSize: 9, color: "#087f45", marginTop: 5 },
  composer: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 5,
    marginTop: 8,
  },
  composerButton: {
    width: 38,
    height: 38,
    borderWidth: 1,
    borderColor: "#aebcaf",
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#fff",
  },
  composerInput: {
    flex: 1,
    minHeight: 38,
    maxHeight: 90,
    borderWidth: 1,
    borderColor: "#aebcaf",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: "#fff",
  },
  send: {
    width: 38,
    height: 38,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#087f45",
  },
  faq: {
    borderWidth: 1.2,
    borderColor: "#aebcaf",
    borderRadius: 9,
    padding: 12,
    backgroundColor: "#fff",
  },
  faqQ: { fontSize: 12, fontWeight: "800", color: "#17233d" },
  uploadBox: {
    minHeight: 250,
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: "#82a98d",
    borderRadius: 11,
    alignItems: "center",
    justifyContent: "center",
    padding: 15,
    backgroundColor: "#f6fcf5",
  },
  uploadIcon: { fontSize: 42 },
  preview: { width: "100%", height: 250, resizeMode: "contain" },
  secondary: {
    flex: 1,
    borderWidth: 1.2,
    borderColor: "#087f45",
    borderRadius: 8,
    padding: 11,
    alignItems: "center",
  },
  secondaryText: { fontSize: 11, color: "#087f45", fontWeight: "800" },
  disabled: { opacity: 0.45 },
  infoRow: {
    borderBottomWidth: 1,
    borderBottomColor: "#e1e7e2",
    paddingVertical: 12,
  },
  logout: {
    marginTop: 10,
    borderWidth: 1,
    borderColor: "#d99ba1",
    borderRadius: 9,
    padding: 14,
    alignItems: "center",
    backgroundColor: "#fff7f7",
  },
  logoutText: { color: "#a62935", fontWeight: "900" },
});
