"use client";

import { useEffect, useState } from "react";

type BackendState = "checking" | "connected" | "offline";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [backendState, setBackendState] = useState<BackendState>("checking");

  useEffect(() => {
    const controller = new AbortController();

    async function checkBackend() {
      try {
        const response = await fetch(`${apiBaseUrl}/health`, { signal: controller.signal });
        setBackendState(response.ok ? "connected" : "offline");
      } catch {
        if (!controller.signal.aborted) setBackendState("offline");
      }
    }

    void checkBackend();
    return () => controller.abort();
  }, []);

  return (
    <main>
      <section className="shell" aria-labelledby="page-title">
        <div className="mark" aria-hidden="true">KM</div>
        <p className="eyebrow">Phase 1 foundation</p>
        <h1 id="page-title">KrishiMitra AI</h1>
        <p className="lede">Responsive web development environment</p>
        <div className="status" role="status" aria-live="polite">
          <span className={`dot dot--${backendState}`} aria-hidden="true" />
          Backend status: <strong>{backendState}</strong>
        </div>
        <p className="note">Business features intentionally begin in later phases.</p>
      </section>
    </main>
  );
}
