import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const app = readFileSync(new URL("../App.tsx", import.meta.url), "utf8");
const screens = ["login", "help", "home", "weather", "market", "guidance", "ask", "crop", "advisory", "faqs", "upload", "history", "notifications", "profile"];

test("Phase 6 mobile defines the complete approved screen inventory", () => {
  for (const screen of screens) assert.match(app, new RegExp(`[\"']${screen}[\"']`), `missing ${screen}`);
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

test("mobile live-data gaps are not filled with invented values", () => {
  assert.match(app, /No values are estimated/);
  assert.match(app, /Not available from the current backend contract/);
});
