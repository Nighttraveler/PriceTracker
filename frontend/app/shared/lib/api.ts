import axios from "axios"

const baseURL =
  typeof window === "undefined"
    ? (process.env.API_URL ?? "http://localhost:5000")
    : (import.meta.env.VITE_API_URL ?? "http://localhost:5000")

// Sits above the app's cold-query time (~11s) but below the DB's 30s
// statement_timeout, so the SSR loader waits out a cold cache instead of
// 500-ing, while a genuinely stuck query still fails fast at the DB.
export const api = axios.create({ baseURL, timeout: 20000 })
