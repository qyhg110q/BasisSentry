import { Paper, Stack, Typography } from "@mui/material";
import { AlertsPanel } from "../components/AlertsPanel";

export const Alerts = () => {
  return (
    <Stack spacing={2}>
      <Typography variant="h5">Alerts Center</Typography>
      <Paper sx={{ padding: 2 }}>
        <AlertsPanel />
      </Paper>
    </Stack>
  );
};
