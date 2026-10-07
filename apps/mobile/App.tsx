import { StatusBar } from "expo-status-bar";
import { useEffect, useState } from "react";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";

type BackendState = "checking" | "connected" | "offline";

const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const statusColors: Record<BackendState, string> = {
  checking: "#a46b00",
  connected: "#16843c",
  offline: "#c53030",
};

export default function App() {
  const [backendState, setBackendState] = useState<BackendState>("checking");

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${apiBaseUrl}/health`, { signal: controller.signal })
      .then((response) => setBackendState(response.ok ? "connected" : "offline"))
      .catch(() => {
        if (!controller.signal.aborted) setBackendState("offline");
      });
    return () => controller.abort();
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <View style={styles.card}>
        <View style={styles.mark}><Text style={styles.markText}>KM</Text></View>
        <Text style={styles.eyebrow}>Phase 1 foundation</Text>
        <Text accessibilityRole="header" style={styles.title}>KrishiMitra AI</Text>
        <Text style={styles.subtitle}>Mobile development environment</Text>
        <View accessibilityLiveRegion="polite" style={styles.status}>
          <View style={[styles.dot, { backgroundColor: statusColors[backendState] }]} />
          <Text style={styles.statusText}>Backend status: {backendState}</Text>
        </View>
        <Text style={styles.note}>Business features intentionally begin in later phases.</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#eff8f0", justifyContent: "center", padding: 20 },
  card: { backgroundColor: "#ffffff", borderColor: "#dce7de", borderRadius: 24, borderWidth: 1, padding: 28 },
  mark: { alignItems: "center", backgroundColor: "#236b3a", borderRadius: 14, height: 48, justifyContent: "center", width: 48 },
  markText: { color: "#ffffff", fontSize: 16, fontWeight: "800" },
  eyebrow: { color: "#236b3a", fontSize: 12, fontWeight: "800", letterSpacing: 1.2, marginBottom: 8, marginTop: 24, textTransform: "uppercase" },
  title: { color: "#142319", fontSize: 42, fontWeight: "800", letterSpacing: -1.5 },
  subtitle: { color: "#526157", fontSize: 18, marginBottom: 28, marginTop: 10 },
  status: { alignItems: "center", backgroundColor: "#f8fbf8", borderColor: "#dce7de", borderRadius: 14, borderWidth: 1, flexDirection: "row", minHeight: 50, paddingHorizontal: 16 },
  dot: { borderRadius: 6, height: 12, marginRight: 10, width: 12 },
  statusText: { color: "#142319", fontSize: 16, textTransform: "capitalize" },
  note: { color: "#526157", fontSize: 13, marginTop: 16 },
});
