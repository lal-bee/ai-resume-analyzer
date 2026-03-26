import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const http = axios.create({
  baseURL: apiBaseUrl,
  timeout: 60000,
});

