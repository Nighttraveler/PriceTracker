import axios from "axios"

const baseURL =
  typeof window === "undefined"
    ? (process.env.API_URL ?? "http://localhost:5000")
    : (import.meta.env.VITE_API_URL ?? "http://localhost:5000")

export const api = axios.create({ baseURL, timeout: 10000 })
