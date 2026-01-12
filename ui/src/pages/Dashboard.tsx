import { Box, Grid, Typography } from "@mui/material";
import { useEffect } from "react";
import { fetchSymbols } from "../api/client";
import { createStream } from "../api/ws";
import { AlertsPanel } from "../components/AlertsPanel";
import { ConnectionStatus } from "../components/ConnectionStatus";
import { SymbolsTable } from "../components/SymbolsTable";
import { useUiStore } from "../store/state";

export const Dashboard = () => {
  const { states, updateStates, setStatus, addEvent } = useUiStore();

  useEffect(() => {
    fetchSymbols().then((data) => {
      if (data?.states) {
        updateStates(data.states);
      }
    });
    const stop = createStream(
      (message) => {
        if (message.type === "state_update") {
          updateStates(message.data);
        }
        if (message.type === "event") {
          addEvent(message.data);
        }
      },
      (status) => setStatus(status)
    );
    return () => stop();
  }, [updateStates, setStatus, addEvent]);

  return (
    <Box display="flex" flexDirection="column" gap={2}>
      <ConnectionStatus />
      <Grid container spacing={2}>
        <Grid item xs={12} lg={8}>
          <SymbolsTable states={Object.values(states)} />
        </Grid>
        <Grid item xs={12} lg={4}>
          <AlertsPanel />
        </Grid>
      </Grid>
      <Typography variant="caption" color="text.secondary">
        UI updates every second. Click a symbol row to open detail view.
      </Typography>
    </Box>
  );
};
