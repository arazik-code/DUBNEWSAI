import { format, formatDistanceToNowStrict } from "date-fns";

export function formatCurrency(value: number, currency = "AED") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: value >= 1000 ? 0 : 2,
  }).format(value || 0);
}

export function formatCompactNumber(value: number) {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value || 0);
}

export function formatPercent(value: number) {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${(value || 0).toFixed(2)}%`;
}

export function formatDateLabel(value: string | Date) {
  return format(new Date(value), "MMM d, yyyy");
}

export function formatRelativeTime(value: string | Date) {
  return formatDistanceToNowStrict(new Date(value), { addSuffix: true });
}

export function sentenceCase(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
