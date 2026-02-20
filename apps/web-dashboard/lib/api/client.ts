import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios"

// Service base URLs from environment (see .env.local.example)
export const SERVICE_URLS = {
  auth:         process.env.NEXT_PUBLIC_AUTH_URL         ?? "http://localhost:8001",
  user:         process.env.NEXT_PUBLIC_USER_URL         ?? "http://localhost:8002",
  transaction:  process.env.NEXT_PUBLIC_TXN_URL          ?? "http://localhost:8003",
  ledger:       process.env.NEXT_PUBLIC_LEDGER_URL       ?? "http://localhost:8004",
  report:       process.env.NEXT_PUBLIC_REPORT_URL       ?? "http://localhost:8005",
  ai:           process.env.NEXT_PUBLIC_AI_URL           ?? "http://localhost:8006",
  notification: process.env.NEXT_PUBLIC_NOTIFICATION_URL ?? "http://localhost:8007",
}

// Factory: one axios instance per service base URL, all sharing the same interceptors
function makeClient(baseURL: string): AxiosInstance {
  const instance = axios.create({ baseURL, timeout: 10_000 })

  // ── Request: attach access token ─────────────────────────────────────────
  instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    // Dynamic import to avoid circular deps — store is available client-side only
    if (typeof window !== "undefined") {
      const raw = localStorage.getItem("ledgerlite-auth")
      if (raw) {
        const state = JSON.parse(raw) as { state?: { accessToken?: string } }
        const token = state?.state?.accessToken
        if (token) config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  })

  // ── Response: 401 → refresh → retry once ─────────────────────────────────
  instance.interceptors.response.use(
    (r) => r,
    async (err) => {
      const original = err.config as InternalAxiosRequestConfig & { _retry?: boolean }
      if (err.response?.status === 401 && !original._retry) {
        original._retry = true
        try {
          const raw = localStorage.getItem("ledgerlite-auth")
          if (raw) {
            const state = JSON.parse(raw) as { state?: { refreshToken?: string } }
            const refreshToken = state?.state?.refreshToken
            if (refreshToken) {
              const res = await axios.post(`${SERVICE_URLS.auth}/auth/refresh`, {
                refresh_token: refreshToken,
              })
              const { access_token, refresh_token } = res.data
              // Update persisted store directly
              const current = JSON.parse(localStorage.getItem("ledgerlite-auth") ?? "{}")
              current.state = { ...current.state, accessToken: access_token, refreshToken: refresh_token }
              localStorage.setItem("ledgerlite-auth", JSON.stringify(current))
              original.headers.Authorization = `Bearer ${access_token}`
              return instance(original)
            }
          }
        } catch {
          // Refresh failed — clear auth and redirect to login
          localStorage.removeItem("ledgerlite-auth")
          if (typeof window !== "undefined") window.location.href = "/login"
        }
      }
      return Promise.reject(err)
    }
  )

  return instance
}

export const authClient         = makeClient(SERVICE_URLS.auth)
export const userClient         = makeClient(SERVICE_URLS.user)
export const transactionClient  = makeClient(SERVICE_URLS.transaction)
export const ledgerClient       = makeClient(SERVICE_URLS.ledger)
export const reportClient       = makeClient(SERVICE_URLS.report)
export const aiClient           = makeClient(SERVICE_URLS.ai)
export const notificationClient = makeClient(SERVICE_URLS.notification)
