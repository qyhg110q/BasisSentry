import { Box, Paper, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { fetchEventPacks } from "../api/client";

export const EventPack = () => {
  const [packs, setPacks] = useState<{ id: string; path: string }[]>([]);

  useEffect(() => {
    fetchEventPacks().then((data) => setPacks(data.packs ?? []));
  }, []);

  return (
    <Stack spacing={2}>
      <Typography variant="h5">Event Packs</Typography>
      <Paper sx={{ padding: 2 }}>
        <Stack spacing={1}>
          {packs.map((pack) => (
            <Box key={pack.id} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 1, padding: 1 }}>
              <Typography variant="body2">ID: {pack.id}</Typography>
              <Typography variant="caption" color="text.secondary">
                {pack.path}
              </Typography>
            </Box>
          ))}
        </Stack>
      </Paper>
    </Stack>
  );
};
