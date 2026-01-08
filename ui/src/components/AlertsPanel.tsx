import { Box, Chip, Paper, Stack, Typography } from "@mui/material";
import { useUiStore } from "../store/state";

const severityFor = (eventType?: string) => {
  if (!eventType) return "info" as const;
  if (eventType === "WALL_REMOVE") return "error" as const;
  if (eventType === "BASIS_SPIKE") return "warning" as const;
  return "info" as const;
};

export const AlertsPanel = () => {
  const { events, muteUntil } = useUiStore();
  const isMuted = muteUntil ? muteUntil > Date.now() : false;

  return (
    <Paper sx={{ padding: 2 }}>
      <Stack direction="row" spacing={1} alignItems="center" marginBottom={1}>
        <Typography variant="h6">Alerts</Typography>
        {isMuted && <Chip label="Muted" color="default" size="small" />}
      </Stack>
      <Stack spacing={1} maxHeight={280} overflow="auto">
        {events.map((event, idx) => (
          <Box
            key={`${event.symbol}-${event.ts}-${idx}`}
            sx={{
              border: "1px solid",
              borderColor: severityFor(event.event_type) === "error" ? "error.main" : "divider",
              borderRadius: 1,
              padding: 1,
              backgroundColor: severityFor(event.event_type) === "error" ? "rgba(244,67,54,0.08)" : "inherit",
            }}
          >
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip label={event.event_type} size="small" color={severityFor(event.event_type)} />
              <Typography variant="body2">{event.symbol.toUpperCase()}</Typography>
              <Typography variant="caption">{new Date(event.ts).toLocaleTimeString()}</Typography>
            </Stack>
            <Typography variant="caption" color="text.secondary">
              {event.event_reason}
            </Typography>
          </Box>
        ))}
      </Stack>
    </Paper>
  );
};
