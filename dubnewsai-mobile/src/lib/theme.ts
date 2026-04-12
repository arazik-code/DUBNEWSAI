import { useColorScheme } from "react-native";

const dark = {
  background: "#050816",
  backgroundElevated: "#0B1020",
  surface: "rgba(14, 20, 37, 0.86)",
  surfaceStrong: "#111935",
  surfaceMuted: "#182240",
  border: "rgba(148, 163, 184, 0.18)",
  text: "#F8FAFC",
  textMuted: "#94A3B8",
  textSoft: "#CBD5E1",
  accent: "#F5B83D",
  accentStrong: "#FFCE67",
  accentSoft: "rgba(245, 184, 61, 0.18)",
  cyan: "#42D4FF",
  success: "#31C48D",
  danger: "#F87171",
  overlay: "rgba(4, 8, 18, 0.72)",
  hairline: "rgba(255,255,255,0.06)",
  shadow: "#000000",
};

const light = {
  background: "#F6F7FB",
  backgroundElevated: "#FFFFFF",
  surface: "rgba(255, 255, 255, 0.92)",
  surfaceStrong: "#FFFFFF",
  surfaceMuted: "#EEF2FF",
  border: "rgba(15, 23, 42, 0.08)",
  text: "#081121",
  textMuted: "#5B6B84",
  textSoft: "#334155",
  accent: "#C58B12",
  accentStrong: "#A86F07",
  accentSoft: "rgba(197, 139, 18, 0.14)",
  cyan: "#0EA5E9",
  success: "#0F9D58",
  danger: "#D84A4A",
  overlay: "rgba(255, 255, 255, 0.64)",
  hairline: "rgba(8, 17, 33, 0.06)",
  shadow: "#0F172A",
};

export const radii = {
  xl: 28,
  lg: 22,
  md: 16,
  sm: 12,
  pill: 999,
};

export const spacing = {
  page: 20,
  section: 28,
  gap: 16,
  tight: 10,
};

export function useAppTheme() {
  const scheme = useColorScheme() === "light" ? "light" : "dark";
  const colors = scheme === "light" ? light : dark;
  return {
    scheme,
    colors,
    isDark: scheme === "dark",
    statusBarStyle: scheme === "dark" ? "light" : "dark",
  } as const;
}
