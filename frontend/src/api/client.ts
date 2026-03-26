import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

export const http = axios.create({
  baseURL: apiBaseUrl,
  timeout: 60000,
});

