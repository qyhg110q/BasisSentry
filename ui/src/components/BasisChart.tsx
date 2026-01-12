import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TimeseriesPoint } from "../types";

export const BasisChart = ({ data }: { data: TimeseriesPoint[] }) => {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data}>
        <XAxis dataKey="ts" hide />
        <YAxis yAxisId="left" />
        <YAxis yAxisId="right" orientation="right" />
        <Tooltip />
        <Line yAxisId="left" type="monotone" dataKey="spot_mid" stroke="#1976d2" dot={false} />
        <Line yAxisId="left" type="monotone" dataKey="perp_mark" stroke="#9c27b0" dot={false} />
        <Line yAxisId="right" type="monotone" dataKey="basis_mark" stroke="#d32f2f" dot={false} />
        <Line yAxisId="right" type="monotone" dataKey="zscore" stroke="#ffa000" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
};
