import type { AssistanceResponse, Category, ChatSession, CropCycle, Faq, Farm, ImageAnalysis, Language, MarketResponse, Me, Message, Profile, SourceCapability, WeatherResponse } from "./types";

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const REGION = process.env.NEXT_PUBLIC_AWS_REGION ?? "ap-south-1";
const CLIENT_ID = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID ?? "";
const COGNITO = process.env.NEXT_PUBLIC_COGNITO_ENDPOINT ?? `https://cognito-idp.${REGION}.amazonaws.com`;
export class ApiError extends Error { constructor(public status: number, message: string) { super(message); } }

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}/api/v1${path}`, { ...init, headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...init?.headers } });
  if (!response.ok) {
    const value = await response.json().catch(() => ({})) as { detail?: string | { message?: string }; message?: string };
    const detail = typeof value.detail === "string" ? value.detail : value.detail?.message;
    throw new ApiError(response.status, detail ?? value.message ?? `Request failed (${response.status})`);
  }
  return response.status === 204 ? (undefined as T) : response.json() as Promise<T>;
}

async function cognito(target: string, body: Record<string, unknown>) {
  if (!CLIENT_ID) throw new Error("Cognito client is not configured for this frontend.");
  const response = await fetch(COGNITO, { method: "POST", headers: { "Content-Type": "application/x-amz-json-1.1", "X-Amz-Target": `AWSCognitoIdentityProviderService.${target}` }, body: JSON.stringify(body) });
  const value = await response.json() as Record<string, unknown>;
  if (!response.ok) throw new Error(String(value.message ?? value.__type ?? "Authentication failed"));
  return value;
}

export async function adminSignIn(username: string, password: string) {
  const value = await cognito("InitiateAuth", {
    AuthFlow: "USER_AUTH",
    ClientId: CLIENT_ID,
    AuthParameters: {
      USERNAME: username,
      PASSWORD: password,
      PREFERRED_CHALLENGE: "PASSWORD",
    },
  }) as { AuthenticationResult?: { AccessToken?: string; IdToken?: string } };
  const token = value.AuthenticationResult?.AccessToken ?? value.AuthenticationResult?.IdToken;
  if (!token) throw new Error("Cognito did not return an authentication token.");
  return token;
}

export const adminApi = {
  health: (token: string) => request<{ status: string; role: string }>("/admin/health", token),
  dashboard: (token: string) => request<Record<string, unknown>>("/admin/dashboard", token),
  users: (token: string) => request<Array<Record<string, unknown>>>("/admin/users", token),
  user: (token: string, id: string) => request<Record<string, unknown>>(`/admin/users/${id}`, token),
  sources: (token: string) => request<Array<Record<string, unknown>>>("/admin/sources", token),
  documents: (token: string) => request<Array<Record<string, unknown>>>("/admin/documents", token),
  ingestion: (token: string) => request<Array<Record<string, unknown>>>("/admin/ingestion", token),
  feedback: (token: string) => request<Array<Record<string, unknown>>>("/admin/feedback", token),
  images: (token: string) => request<Array<Record<string, unknown>>>("/admin/image-analyses", token),
  audit: (token: string) => request<Array<Record<string, unknown>>>("/admin/audit-logs", token),
  system: (token: string) => request<Record<string, unknown>>("/admin/system", token),
};

function normalizePhone(phone: string) {
  const trimmed = phone.trim();
  const digits = trimmed.replace(/\D/g, "");
  if (digits.length === 10) return `+91${digits}`;
  if (digits.length === 12 && digits.startsWith("91")) return `+${digits}`;
  return trimmed.startsWith("+") ? `+${digits}` : trimmed;
}

export async function sendOtp(phone: string) {
  return cognito("InitiateAuth", { AuthFlow: "USER_AUTH", ClientId: CLIENT_ID, AuthParameters: { USERNAME: normalizePhone(phone), PREFERRED_CHALLENGE: "SMS_OTP" } }) as Promise<{ ChallengeName?: string; Session?: string }>;
}
export async function verifyOtp(phone: string, otp: string, session: string) {
  const value = await cognito("RespondToAuthChallenge", { ClientId: CLIENT_ID, ChallengeName: "SMS_OTP", Session: session, ChallengeResponses: { USERNAME: normalizePhone(phone), SMS_OTP_CODE: otp } }) as { AuthenticationResult?: { AccessToken?: string; IdToken?: string; RefreshToken?: string } };
  const token = value.AuthenticationResult?.AccessToken ?? value.AuthenticationResult?.IdToken;
  if (!token) throw new Error("Cognito did not return an authentication token.");
  return token;
}

export const api = {
  me: (token: string) => request<Me>("/me", token), profile: (token: string) => request<Profile>("/farmer/profile", token),
  updateProfile: (token: string, body: Partial<Profile>) => request<Profile>("/farmer/profile", token, { method: "PATCH", body: JSON.stringify(body) }),
  farms: (token: string) => request<Farm[]>("/farms", token), cycles: (token: string) => request<CropCycle[]>("/crop-cycles", token),
  categories: (token: string, language: Language) => request<Category[]>(`/problem-categories?language=${language}`, token),
  faqs: (token: string, slug: string, language: Language) => request<Faq[]>(`/problem-categories/${slug}/faqs?language=${language}`, token),
  chats: (token: string) => request<ChatSession[]>("/chat/sessions", token), messages: (token: string, id: string) => request<Message[]>(`/chat/sessions/${id}/messages`, token),
  archiveChat: (token: string, id: string) => request<ChatSession>(`/chat/sessions/${id}`, token, { method: "PATCH", body: JSON.stringify({ is_archived: true }) }),
  startGuided: (token: string, categoryId: string, language: Language, cropCycleId?: string) => request<ChatSession>("/assistance/sessions", token, { method: "POST", body: JSON.stringify({ problem_category_id: categoryId, language, crop_cycle_id: cropCycleId }) }),
  ask: (token: string, id: string, question: string, language: Language, attachmentIds: string[] = []) => request<AssistanceResponse>(`/assistance/sessions/${id}/questions`, token, { method: "POST", body: JSON.stringify({ question, language, attachment_ids: attachmentIds }) }),
  sources: (token: string) => request<{ sources: SourceCapability[] }>("/live/sources", token),
  weather: (token: string, state: string, district: string) => request<WeatherResponse>(`/live/weather?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}`, token),
  markets: (token: string, state: string, district: string) => request<MarketResponse>(`/live/markets?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}`, token),
  createUpload: (token: string, body: Record<string, unknown>) => request<{ attachment_id: string; analysis_id?: string; upload_url: string; form_fields: Record<string, string> }>("/attachments/upload", token, { method: "POST", body: JSON.stringify(body) }),
  completeUpload: (token: string, id: string) => request(`/attachments/${id}/complete`, token, { method: "POST" }),
  analyzeUpload: (token: string, id: string) => request<ImageAnalysis>(`/attachments/${id}/analyze`, token, { method: "POST" }),
  analysis: (token: string, id: string) => request<ImageAnalysis>(`/image-analyses/${id}`, token),
};
