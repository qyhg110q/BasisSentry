import { AppBar, Box, Button, Container, Toolbar, Typography } from "@mui/material";
import { BrowserRouter, Route, Routes, Link } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { SymbolDetail } from "./pages/SymbolDetail";
import { Alerts } from "./pages/Alerts";
import { EventPack } from "./pages/EventPack";

export const App = () => {
  return (
    <BrowserRouter>
      <AppBar position="sticky" color="default" elevation={1}>
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
          <Typography variant="h6">BasisSentry UI</Typography>
          <Box display="flex" gap={1}>
            <Button component={Link} to="/" size="small">
              Dashboard
            </Button>
            <Button component={Link} to="/alerts" size="small">
              Alerts
            </Button>
            <Button component={Link} to="/event-packs" size="small">
              Event Packs
            </Button>
          </Box>
        </Toolbar>
      </AppBar>
      <Container sx={{ paddingY: 3 }} maxWidth="xl">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/symbol/:symbol" element={<SymbolDetail />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/event-packs" element={<EventPack />} />
        </Routes>
      </Container>
    </BrowserRouter>
  );
};
