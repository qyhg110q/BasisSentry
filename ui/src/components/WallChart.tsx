import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TimeseriesPoint } from "../types";

export const WallChart = ({ data }: { data: TimeseriesPoint[] }) => {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <XAxis dataKey="ts" hide />
        <YAxis />
        <Tooltip />
        <Line type="step" dataKey="wall_notional" stroke="#2e7d32" dot={false} />
        <Line type="step" dataKey="wall_price" stroke="#0288d1" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
};
