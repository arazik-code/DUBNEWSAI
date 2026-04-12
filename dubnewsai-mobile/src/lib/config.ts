const FALLBACK_API_URL = "https://dubnewsai-api-production.up.railway.app/api/v1";
const FALLBACK_WS_URL = "wss://dubnewsai-api-production.up.railway.app";
const FALLBACK_APP_NAME = "DUBNEWSAI";
const FALLBACK_APP_VERSION = "1.0.0";

function trimUrl(value: string) {
  return value.replace(/\/+$/, "");
}

export const appConfig = {
  appName: process.env.EXPO_PUBLIC_APP_NAME?.trim() || FALLBACK_APP_NAME,
  appVersion: process.env.EXPO_PUBLIC_APP_VERSION?.trim() || FALLBACK_APP_VERSION,
  apiUrl: trimUrl(process.env.EXPO_PUBLIC_API_URL?.trim() || FALLBACK_API_URL),
  wsUrl: trimUrl(process.env.EXPO_PUBLIC_WS_URL?.trim() || FALLBACK_WS_URL),
};
