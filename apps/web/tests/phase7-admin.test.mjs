import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const component = readFileSync(new URL("../src/components/AdminApp.tsx", import.meta.url), "utf8");
const api = readFileSync(new URL("../src/lib/api.ts", import.meta.url), "utf8");
const page = readFileSync(new URL("../src/app/admin/page.tsx", import.meta.url), "utf8");

test("admin page exposes all required operational modules", () => {
  for (const label of ["Overview", "Farmers & users", "Government sources", "Knowledge documents", "Ingestion jobs", "Farmer feedback", "Image analyses", "System health", "Audit log"]) {
    assert.match(component, new RegExp(label.replaceAll("&", "\\&")));
  }
  assert.match(page, /<AdminApp \/>/);
});

test("admin privilege is verified by the backend before console access", () => {
  assert.match(component, /await adminApi\.health\(candidate\)/);
  assert.match(component, /health\.role !== "ADMIN"/);
  assert.match(api, /\/admin\/health/);
  assert.match(component, /if \(health\.role !== "ADMIN"\).*setVerified\(true\)/s);
});

test("admin sign-in uses the Cognito password challenge configured by infrastructure", () => {
  assert.match(api, /AuthFlow: "USER_AUTH"/);
  assert.match(api, /PREFERRED_CHALLENGE: "PASSWORD"/);
});

test("admin logout clears separate authentication state", () => {
  assert.match(component, /removeItem\("krishimitra\.admin\.token"\)/);
  assert.match(component, /setVerified\(false\)/);
});

test("admin API consumes every protected backend view", () => {
  for (const route of ["dashboard", "users", "sources", "documents", "ingestion", "feedback", "image-analyses", "audit-logs", "system"]) {
    assert.match(api, new RegExp(`/admin/${route}`));
  }
});
