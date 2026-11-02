import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const app = readFileSync(new URL("../App.tsx", import.meta.url), "utf8");
const screens = [
  "login",
  "help",
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

test("Phase 6 mobile defines the complete approved screen inventory", () => {
  for (const screen of screens)
    assert.match(app, new RegExp(`[\"']${screen}[\"']`), `missing ${screen}`);
});

test("mobile image analysis follows the secure attachment pipeline", () => {
  const ordered = ["/attachments/upload", "/complete", "/analyze"];
  let cursor = -1;
  for (const route of ordered) {
    const next = app.indexOf(route, cursor + 1);
    assert.ok(next > cursor, `${route} is missing or out of order`);
    cursor = next;
  }
});

test("mobile Cognito OTP uses the documented SMS challenge response", () => {
  assert.match(app, /SMS_OTP_CODE: otp\.trim\(\)/);
  assert.doesNotMatch(app, /SMS_OTP: otp/);
  assert.match(app, /normalizeIndianPhone\(phone\)/);
  assert.match(app, /Resend OTP/);
  assert.match(app, /Change number/);
});

test("mobile live-data gaps are not filled with invented values", () => {
  assert.match(app, /No values are estimated/);
  assert.match(app, /Not available from the current backend contract/);
});

test("mobile phone normalization accepts Indian forms and rejects malformed values", () => {
  const source = app.match(
    /export function normalizeIndianPhone\(phone: string\) \{[\s\S]*?\n\}/,
  )?.[0];
  assert.ok(source, "normalizeIndianPhone implementation is missing");
  const normalizePhone = vm.runInNewContext(
    `(${source.replace("export ", "").replace("phone: string", "phone")})`,
  );
  assert.equal(normalizePhone("9876543210"), "+919876543210");
  assert.equal(normalizePhone("+91 98765 43210"), "+919876543210");
  assert.throws(() => normalizePhone("12345"), /valid 10-digit/);
  assert.throws(() => normalizePhone("91919876543210"), /valid 10-digit/);
});

test("mobile clears farmer authentication on any backend 401", () => {
  assert.match(app, /r\.status === 401.*unauthorizedHandler/s);
  assert.match(app, /setUnauthorizedHandler/);
  assert.match(app, /setToken\(""\)/);
  assert.match(app, /setScreen\("login"\)/);
});

test("Phase 2 mobile supports onboarding updates and recoverable farmer workflows", () => {
  for (const value of [
    "Edit profile",
    "Edit farm",
    "Edit crop cycle",
    "Archive conversation",
    "Retry Analysis",
    "Questions could not be loaded",
  ]) {
    assert.match(app, new RegExp(value));
  }
  assert.match(app, /analysisId && attachmentId/);
  assert.match(app, /Retry checks the same upload/i);
});
