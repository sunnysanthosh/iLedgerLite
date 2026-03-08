// Centralised API URL config — all values come from environment variables.
// Set via .env.local for local dev, or Kubernetes ConfigMap / GitHub Actions env for staging/prod.
//
// Copy .env.local.example to .env.local and adjust values before running locally.
// Never commit .env.local (it is git-ignored).
export const config = {
  authUrl:         process.env.NEXT_PUBLIC_AUTH_URL         ?? 'http://localhost:8001',
  userUrl:         process.env.NEXT_PUBLIC_USER_URL         ?? 'http://localhost:8002',
  txnUrl:          process.env.NEXT_PUBLIC_TXN_URL          ?? 'http://localhost:8003',
  ledgerUrl:       process.env.NEXT_PUBLIC_LEDGER_URL       ?? 'http://localhost:8004',
  reportUrl:       process.env.NEXT_PUBLIC_REPORT_URL       ?? 'http://localhost:8005',
  aiUrl:           process.env.NEXT_PUBLIC_AI_URL           ?? 'http://localhost:8006',
  notificationUrl: process.env.NEXT_PUBLIC_NOTIFICATION_URL ?? 'http://localhost:8007',
  syncUrl:         process.env.NEXT_PUBLIC_SYNC_URL         ?? 'http://localhost:8008',
} as const
