import type { UserProfile } from "@/types/api"

/**
 * Returns true if the user has admin access to privileged pages (e.g. Infra Costs).
 *
 * Two ways to grant admin access (either is sufficient):
 *
 * 1. Backend field: `user.is_admin === true`
 *    The backend will set this once the `is_admin` column is added to the users table.
 *
 * 2. Environment allow-list: NEXT_PUBLIC_ADMIN_EMAILS (comma-separated)
 *    Useful before the backend field is available, or for emergency access.
 *    Example .env.local entry:
 *      NEXT_PUBLIC_ADMIN_EMAILS=founder@ledgerlite.app,ops@ledgerlite.app
 */
export function isAdmin(user: UserProfile | null | undefined): boolean {
  if (!user) return false
  if (user.is_admin === true) return true

  const allowList = process.env.NEXT_PUBLIC_ADMIN_EMAILS ?? ""
  if (!allowList) return false

  return allowList
    .split(",")
    .map((e) => e.trim().toLowerCase())
    .includes(user.email.toLowerCase())
}
