export function asUtcDate(value: string): Date {
  // Backend timestamps are stored as UTC-naive values for SQLite compatibility.
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
}

export function formatUtcTimestamp(value?: string | null): string {
  if (!value) return "N/A";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "UTC",
  }).format(asUtcDate(value)) + " UTC";
}

export function formatUtcTime(value?: string | null): string {
  if (!value) return "N/A";
  return new Intl.DateTimeFormat(undefined, {
    timeStyle: "medium",
    timeZone: "UTC",
  }).format(asUtcDate(value)) + " UTC";
}
