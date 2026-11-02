import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const app = readFileSync(
  new URL("../src/components/FarmerApp.tsx", import.meta.url),
  "utf8",
);
const api = readFileSync(new URL("../src/lib/api.ts", import.meta.url), "utf8");
const screens = [
  "home",
  "weather",
  "market",
  "guidance",
  "ask",
  "crop",
  "advisory",
  "faqs",
  "upload",
  "history",
  "notifications",
  "profile",
];

test("Phase 6 web exposes every approved authenticated destination", () => {
  for (const screen of screens)
    assert.match(app, new RegExp(`[\"']${screen}[\"']`), `missing ${screen}`);
});

test("Phase 6 web consumes existing backend contracts", () => {
  for (const route of [
    "/me",
    "/farmer/profile",
    "/farms",
    "/crop-cycles",
    "/problem-categories",
    "/chat/sessions",
    "/assistance/sessions",
    "/live/weather",
    "/live/markets",
    "/attachments/upload",
    "/image-analyses/",
  ]) {
    assert.ok(api.includes(route), `missing ${route}`);
  }
});

test("unsupported live panels are represented honestly", () => {
  assert.match(app, /Not available from the current backend contract/);
  assert.doesNotMatch(app, /mock weather|mock market|sample price/i);
});

test("farmer SMS OTP uses Cognito's required challenge response contract", () => {
  assert.match(api, /PREFERRED_CHALLENGE: "SMS_OTP"/);
  assert.match(api, /ChallengeName: "SMS_OTP"/);
  assert.match(api, /SMS_OTP_CODE: otp/);
  assert.doesNotMatch(api, /SMS_OTP: otp/);
});

test("web phone normalization accepts Indian forms and rejects malformed values", () => {
  const source = api.match(
    /export function normalizePhone\(phone: string\) \{[\s\S]*?\n\}/,
  )?.[0];
  assert.ok(source, "normalizePhone implementation is missing");
  const normalizePhone = vm.runInNewContext(
    `(${source.replace("export ", "").replace("phone: string", "phone")})`,
  );
  assert.equal(normalizePhone("9876543210"), "+919876543210");
  assert.equal(normalizePhone("+91 98765 43210"), "+919876543210");
  assert.throws(() => normalizePhone("12345"), /valid 10-digit/);
  assert.throws(() => normalizePhone("91919876543210"), /valid 10-digit/);
});

test("web clears farmer authentication on any backend 401", () => {
  assert.match(api, /response\.status === 401.*unauthorizedHandler/s);
  const page = readFileSync(
    new URL("../src/app/page.tsx", import.meta.url),
    "utf8",
  );
  assert.match(page, /setUnauthorizedHandler/);
  assert.match(page, /removeItem\("krishimitra\.token"\)/);
  assert.match(page, /setScreen\("login"\)/);
});

test("Phase 2 web supports onboarding updates and recoverable farmer workflows", () => {
  for (const route of ["updateProfile", "updateFarm", "updateCycle"])
    assert.match(api, new RegExp(route));
  for (const behavior of [
    "archiveHistory",
    "Retry Analysis",
    "Questions could not be loaded",
  ])
    assert.match(app, new RegExp(behavior));
  assert.match(app, /analysisId && attachmentId/);
  assert.match(app, /Retry checks the same upload/i);
});
