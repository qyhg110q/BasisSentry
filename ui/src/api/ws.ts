import type { EventPayload, SymbolState } from "../types";

export type StreamMessage =
  | { type: "state_update"; ts: number; data: SymbolState[] }
  | { type: "event"; ts: number; data: EventPayload };

export const createStream = (
  onMessage: (message: StreamMessage) => void,
  onStatus: (status: "CONNECTED" | "RECONNECTING" | "DISCONNECTED") => void
) => {
  let socket: WebSocket | null = null;
  let reconnectTimer: number | undefined;

  const connect = () => {
    onStatus("RECONNECTING");
    socket = new WebSocket("ws://127.0.0.1:8000/ws/v1/stream");
    socket.onopen = () => {
      onStatus("CONNECTED");
    };
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as StreamMessage;
      onMessage(payload);
    };
    socket.onclose = () => {
      onStatus("RECONNECTING");
      reconnectTimer = window.setTimeout(connect, 2000);
    };
    socket.onerror = () => {
      onStatus("DISCONNECTED");
      socket?.close();
    };
  };

  const stop = () => {
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer);
    }
    socket?.close();
  };

  connect();
  return stop;
};
