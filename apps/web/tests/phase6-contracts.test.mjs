import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const app = readFileSync(new URL("../src/components/FarmerApp.tsx", import.meta.url), "utf8");
const api = readFileSync(new URL("../src/lib/api.ts", import.meta.url), "utf8");
const screens = ["home", "weather", "market", "guidance", "ask", "crop", "advisory", "faqs", "upload", "history", "notifications", "profile"];

test("Phase 6 web exposes every approved authenticated destination", () => {
  for (const screen of screens) assert.match(app, new RegExp(`[\"']${screen}[\"']`), `missing ${screen}`);
});

test("Phase 6 web consumes existing backend contracts", () => {
  for (const route of ["/me", "/farmer/profile", "/farms", "/crop-cycles", "/problem-categories", "/chat/sessions", "/assistance/sessions", "/live/weather", "/live/markets", "/attachments/upload", "/image-analyses/"]) {
    assert.ok(api.includes(route), `missing ${route}`);
  }
});

test("unsupported live panels are represented honestly", () => {
  assert.match(app, /Not available from the current backend contract/);
  assert.doesNotMatch(app, /mock weather|mock market|sample price/i);
});
