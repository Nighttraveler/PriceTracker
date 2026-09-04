import { QueryClient } from "@tanstack/react-query"
import { AxiosError } from "axios"

// Retry policy tuned to avoid amplifying a backend overload (see the dashboard
// retry-storm incident): never retry server errors (5xx) — the backend is
// already struggling and retrying just adds load — and only retry transient
// network/timeout errors once, with exponential backoff.
function retry(failureCount: number, error: unknown): boolean {
  if (error instanceof AxiosError && error.response) {
    // Got an HTTP response (4xx/5xx): the request reached the server. Don't
    // hammer it — a 5xx during an overload should back off, not retry.
    return false
  }
  // Network error / timeout with no response: retry at most once.
  return failureCount < 1
}

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        retry,
        retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10000),
      },
    },
  })
}

let browserClient: QueryClient | undefined

export function getQueryClient() {
  if (typeof window === "undefined") return createQueryClient()
  if (!browserClient) browserClient = createQueryClient()
  return browserClient
}
