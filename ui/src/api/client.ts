import axios from "axios";

const client = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const fetchSymbols = async () => {
  const response = await client.get("/api/v1/symbols");
  return response.data;
};

export const fetchState = async (symbol: string) => {
  const response = await client.get("/api/v1/state", { params: { symbol } });
  return response.data;
};

export const fetchEvents = async (symbol?: string) => {
  const response = await client.get("/api/v1/events", { params: { symbol } });
  return response.data;
};

export const fetchTimeseries = async (symbol: string, range: string) => {
  const response = await client.get("/api/v1/timeseries", { params: { symbol, range } });
  return response.data;
};

export const fetchEventPacks = async () => {
  const response = await client.get("/api/v1/event-packs");
  return response.data;
};
