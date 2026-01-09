import { Button, Chip, Slider, Stack, Typography } from "@mui/material";
import { useUiStore } from "../store/state";

export const ConnectionStatus = () => {
  const { status, lastMessageTs, muteUntil, mute, clearMute, states, volume, setVolume } = useUiStore();
  const lastAge = lastMessageTs ? Date.now() - lastMessageTs : 0;
  const isMuted = muteUntil ? muteUntil > Date.now() : false;

  const playTone = (nextVolume: number) => {
    const AudioCtx = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioCtx) return;
    const context = new AudioCtx();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = 880;
    gain.gain.value = nextVolume;
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start();
    setTimeout(() => {
      oscillator.stop();
      context.close();
    }, 200);
  };

  return (
    <Stack direction={{ xs: "column", md: "row" }} spacing={2} alignItems="center">
      <Chip
        label={status}
        color={status === "CONNECTED" ? "success" : status === "RECONNECTING" ? "warning" : "error"}
      />
      <Typography variant="body2">WS 延迟: {Math.round(lastAge)} ms</Typography>
      <Typography variant="body2">Symbols: {Object.keys(states).length}</Typography>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ minWidth: 200 }}>
        <Typography variant="body2">Volume</Typography>
        <Slider
          size="small"
          value={Math.round(volume * 100)}
          min={0}
          max={100}
          onChange={(_, value) => {
            const next = (Array.isArray(value) ? value[0] : value) / 100;
            setVolume(next);
            playTone(next);
          }}
          sx={{ width: 120 }}
        />
      </Stack>
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
