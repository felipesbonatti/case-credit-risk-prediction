import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import DashboardLayout from "./components/DashboardLayout";
import Overview from "./pages/Overview";
import AnaliseIndividual from "./pages/AnaliseIndividual";
import AnaliseLote from "./pages/AnaliseLote";
import Metricas from "./pages/Metricas";

function Router() {
  return (
    <DashboardLayout>
      <Switch>
        <Route path={"/"} component={Overview} />
        <Route path={"/analise"} component={AnaliseIndividual} />
        <Route path={"/lote"} component={AnaliseLote} />
        <Route path={"/metricas"} component={Metricas} />
        <Route path={"/404"} component={NotFound} />
        <Route component={NotFound} />
      </Switch>
    </DashboardLayout>
  );
}

// NOTE: About Theme
// - First choose a default theme according to your design style (dark or light bg), than change color palette in index.css
//   to keep consistent foreground/background color across components
// - If you want to make theme switchable, pass `switchable` ThemeProvider and use `useTheme` hook

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider
        defaultTheme="dark"
      >
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
