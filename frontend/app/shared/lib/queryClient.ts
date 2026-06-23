import { QueryClient } from "@tanstack/react-query"

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 60 * 1000, retry: 1 },
    },
  })
}

let browserClient: QueryClient | undefined

export function getQueryClient() {
  if (typeof window === "undefined") return createQueryClient()
  if (!browserClient) browserClient = createQueryClient()
  return browserClient
}
