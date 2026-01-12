import { Box, Button, Grid, Paper, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchTimeseries } from "../api/client";
import { BasisChart } from "../components/BasisChart";
import { DepthSnapshot } from "../components/DepthSnapshot";
import { WallChart } from "../components/WallChart";
import { useUiStore } from "../store/state";
import type { TimeseriesPoint } from "../types";

export const SymbolDetail = () => {
  const { symbol } = useParams();
  const state = useUiStore((store) => (symbol ? store.states[symbol] : undefined));
  const [range, setRange] = useState("5m");
  const [series, setSeries] = useState<TimeseriesPoint[]>([]);

  useEffect(() => {
    if (!symbol) return;
    fetchTimeseries(symbol, range).then((data) => setSeries(data.series ?? []));
  }, [symbol, range]);

  if (!symbol) {
    return <Typography>Symbol not found.</Typography>;
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h5">{symbol.toUpperCase()} Detail</Typography>
      <Paper sx={{ padding: 2 }}>
        <Stack direction="row" spacing={1} marginBottom={2}>
          {[
            { label: "5m", value: "5m" },
            { label: "15m", value: "15m" },
            { label: "1h", value: "1h" },
            { label: "6h", value: "6h" },
          ].map((item) => (
            <Button
              key={item.value}
              size="small"
              variant={range === item.value ? "contained" : "outlined"}
              onClick={() => setRange(item.value)}
            >
              {item.label}
            </Button>
          ))}
        </Stack>
        <BasisChart data={series} />
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ padding: 2 }}>
            <Typography variant="subtitle1">Wall Strength</Typography>
            <WallChart data={series} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={5}>
          <Paper sx={{ padding: 2 }}>
            <Typography variant="subtitle1">Depth Snapshot</Typography>
            <DepthSnapshot wall={state?.wall} />
          </Paper>
        </Grid>
      </Grid>

      <Paper sx={{ padding: 2 }}>
        <Typography variant="subtitle1">Wall Explanation</Typography>
        <Typography variant="body2" color="text.secondary">
          Latest event: {state?.last_wall_event ?? "-"}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Latest basis event: {state?.last_basis_event ?? "-"}
        </Typography>
      </Paper>
    </Stack>
  );
};
