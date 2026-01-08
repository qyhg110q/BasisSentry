import { create } from "zustand";
import type { EventPayload, SymbolState } from "../types";

type UiState = {
  status: "CONNECTED" | "RECONNECTING" | "DISCONNECTED";
  states: Record<string, SymbolState>;
  events: EventPayload[];
  lastMessageTs: number;
  muteUntil: number | null;
  setStatus: (status: UiState["status"]) => void;
  updateStates: (payload: SymbolState[]) => void;
  addEvent: (payload: EventPayload) => void;
  mute: (minutes: number) => void;
  clearMute: () => void;
};

export const useUiStore = create<UiState>((set) => ({
  status: "RECONNECTING",
  states: {},
  events: [],
  lastMessageTs: 0,
  muteUntil: null,
  setStatus: (status) => set({ status }),
  updateStates: (payload) =>
    set((state) => {
      const nextStates = { ...state.states };
      payload.forEach((item) => {
        nextStates[item.symbol] = item;
      });
      return { states: nextStates, lastMessageTs: Date.now() };
    }),
  addEvent: (payload) =>
    set((state) => ({
      events: [payload, ...state.events].slice(0, 200),
      lastMessageTs: Date.now(),
    })),
  mute: (minutes) => set({ muteUntil: Date.now() + minutes * 60 * 1000 }),
  clearMute: () => set({ muteUntil: null }),
}));
