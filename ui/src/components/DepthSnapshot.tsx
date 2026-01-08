import { Box, Typography } from "@mui/material";
import type { WallSummary } from "../types";

export const DepthSnapshot = ({ wall }: { wall?: WallSummary | null }) => {
  if (!wall) {
    return <Typography variant="body2">No wall detected in top20.</Typography>;
  }

  return (
    <Box>
      <Typography variant="body2">
        Wall {wall.side.toUpperCase()} @ {wall.wall_price.toFixed(2)}
      </Typography>
      <Typography variant="body2">Notional: {wall.wall_notional.toFixed(0)} USDT</Typography>
      <Typography variant="body2">Share: {(wall.wall_share * 100).toFixed(2)}%</Typography>
      <Typography variant="body2">Best bid/ask: {wall.best_bid.toFixed(2)} / {wall.best_ask.toFixed(2)}</Typography>
    </Box>
  );
};
