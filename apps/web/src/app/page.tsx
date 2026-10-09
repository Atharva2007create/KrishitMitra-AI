"use client";
import { useEffect, useMemo, useState } from "react";
import { FarmerApp } from "@/components/FarmerApp";
import { api } from "@/lib/api";
import type {
  Category,
  ChatSession,
  CropCycle,
  Farm,
  Language,
  Me,
  Screen,
} from "@/lib/types";

export default function Home() {
  const [token, setToken] = useState("");
  const [language, setLanguage] = useState<Language>("en");
  const [screen, setScreen] = useState<Screen>("login");
  const [me, setMe] = useState<Me | null>(null);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [cycles, setCycles] = useState<CropCycle[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    queueMicrotask(() => {
      const saved = localStorage.getItem("krishimitra.token") ?? "";
      const savedLanguage = localStorage.getItem(
        "krishimitra.language",
      ) as Language | null;
      if (savedLanguage && ["en", "hi", "mr"].includes(savedLanguage))
        setLanguage(savedLanguage);
      if (saved) {
        setToken(saved);
        setScreen("home");
      }
    });
  }, []);
  useEffect(() => {
    localStorage.setItem("krishimitra.language", language);
  }, [language]);
  useEffect(() => {
    if (!token) return;
    let active = true;
    Promise.all([
      api.me(token),
      api.farms(token),
      api.cycles(token),
      api.categories(token, language),
      api.chats(token),
    ])
      .then(([identity, farmRows, cycleRows, categoryRows, chatRows]) => {
        if (!active) return;
        setMe(identity);
        setFarms(farmRows);
        setCycles(cycleRows);
        setCategories(categoryRows);
        setChats(chatRows);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setError(
          reason instanceof Error
            ? reason.message
            : "Unable to load your farmer account.",
        );
        if ((reason as { status?: number }).status === 401) logout();
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [token, language]);
  function authenticated(value: string) {
    localStorage.setItem("krishimitra.token", value);
    setLoading(true);
    setError("");
    setToken(value);
    setScreen("home");
  }
  function logout() {
    localStorage.removeItem("krishimitra.token");
    setToken("");
    setMe(null);
    setScreen("login");
  }
  const activeCycle = useMemo(
    () => cycles.find((item) => item.status === "ACTIVE") ?? cycles[0],
    [cycles],
  );
  return (
    <FarmerApp
      {...{
        token,
        language,
        setLanguage,
        screen,
        setScreen,
        me,
        farms,
        cycles,
        activeCycle,
        categories,
        chats,
        loading,
        error,
        authenticated,
        logout,
      }}
    />
  );
}
