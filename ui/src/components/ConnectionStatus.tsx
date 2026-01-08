import { Button, Chip, Stack, Typography } from "@mui/material";
import { useUiStore } from "../store/state";

export const ConnectionStatus = () => {
  const { status, lastMessageTs, muteUntil, mute, clearMute, states } = useUiStore();
  const lastAge = lastMessageTs ? Date.now() - lastMessageTs : 0;
  const isMuted = muteUntil ? muteUntil > Date.now() : false;

  return (
    <Stack direction={{ xs: "column", md: "row" }} spacing={2} alignItems="center">
      <Chip
        label={status}
        color={status === "CONNECTED" ? "success" : status === "RECONNECTING" ? "warning" : "error"}
      />
      <Typography variant="body2">WS 延迟: {Math.round(lastAge)} ms</Typography>
      <Typography variant="body2">Symbols: {Object.keys(states).length}</Typography>
      <Stack direction="row" spacing={1}>
        <Button size="small" variant={isMuted ? "outlined" : "contained"} onClick={() => mute(5)}>
          Mute 5m
        </Button>
        <Button size="small" variant={isMuted ? "outlined" : "contained"} onClick={() => mute(30)}>
          Mute 30m
        </Button>
        <Button size="small" variant="text" onClick={clearMute}>
          Unmute
        </Button>
      </Stack>
    </Stack>
  );
};
