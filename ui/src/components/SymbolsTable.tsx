import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableSortLabel,
  TextField,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { SymbolState } from "../types";

const formatNumber = (value: number, digits = 4) => value.toFixed(digits);

export const SymbolsTable = ({ states }: { states: SymbolState[] }) => {
  const [orderBy, setOrderBy] = useState<keyof SymbolState>("zscore");
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  const filtered = useMemo(() => {
    return states
      .filter((state) => state.symbol.includes(search.toLowerCase()))
      .sort((a, b) => (b[orderBy] ?? 0) - (a[orderBy] ?? 0));
  }, [states, search, orderBy]);

  return (
    <Paper sx={{ padding: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" marginBottom={2}>
        <Typography variant="h6">Symbols Overview</Typography>
        <TextField
          size="small"
          placeholder="Search symbol"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </Box>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Symbol</TableCell>
            <TableCell>Spot Mid</TableCell>
            <TableCell>Perp Mark</TableCell>
            <TableCell>
              <TableSortLabel
                active={orderBy === "basis_mark"}
                direction="desc"
                onClick={() => setOrderBy("basis_mark")}
              >
                Basis Mark (%)
              </TableSortLabel>
            </TableCell>
            <TableCell>
              <TableSortLabel
                active={orderBy === "zscore"}
                direction="desc"
                onClick={() => setOrderBy("zscore")}
              >
                Z-Score
              </TableSortLabel>
            </TableCell>
            <TableCell>Duration (s)</TableCell>
            <TableCell>Wall Summary</TableCell>
            <TableCell>Last Wall Event</TableCell>
            <TableCell>Last Basis Event</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {filtered.map((state) => (
            <TableRow
              key={state.symbol}
              hover
              sx={{ cursor: "pointer" }}
              onClick={() => navigate(`/symbol/${state.symbol}`)}
            >
              <TableCell>{state.symbol.toUpperCase()}</TableCell>
              <TableCell>{formatNumber(state.spot_mid)}</TableCell>
              <TableCell>{formatNumber(state.perp_mark)}</TableCell>
              <TableCell sx={{ color: Math.abs(state.basis_mark) > 0.02 ? "error.main" : "inherit" }}>
                {formatNumber(state.basis_mark * 100, 3)}
              </TableCell>
              <TableCell>{formatNumber(state.zscore, 2)}</TableCell>
              <TableCell>{state.duration_s}</TableCell>
              <TableCell>
                {state.wall
                  ? `${state.wall.side.toUpperCase()} ${formatNumber(state.wall.wall_price, 2)} (${formatNumber(
                      state.wall.wall_notional,
                      0
                    )})`
                  : "-"}
              </TableCell>
              <TableCell>{state.last_wall_event ?? "-"}</TableCell>
              <TableCell>{state.last_basis_event ?? "-"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  );
};
