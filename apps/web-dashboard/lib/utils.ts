import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { format, parseISO } from "date-fns"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Format a decimal string or number as INR currency. */
export function formatCurrency(value: string | number, currency = "INR"): string {
  const num = typeof value === "string" ? parseFloat(value) : value
  if (isNaN(num)) return "—"
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num)
}

/** Parse a decimal string to a JS number for chart/math use. */
export function parseDecimal(value: string | number): number {
  return typeof value === "string" ? parseFloat(value) : value
}

/** Format an ISO date string for display (e.g. "15 Jan 2025"). */
export function formatDate(iso: string): string {
  try {
    return format(parseISO(iso), "d MMM yyyy")
  } catch {
    return iso
  }
}

/** Format an ISO datetime for display (e.g. "15 Jan 2025, 3:42 PM"). */
export function formatDateTime(iso: string): string {
  try {
    return format(parseISO(iso), "d MMM yyyy, h:mm a")
  } catch {
    return iso
  }
}

/** Return today's date as YYYY-MM-DD. */
export function today(): string {
  return format(new Date(), "yyyy-MM-dd")
}

/** Return the first day of the current month as YYYY-MM-DD. */
export function startOfCurrentMonth(): string {
  const d = new Date()
  return format(new Date(d.getFullYear(), d.getMonth(), 1), "yyyy-MM-dd")
}
