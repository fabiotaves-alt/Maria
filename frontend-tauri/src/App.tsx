import { ThemeProvider } from './hooks/useTheme';
import { TopBar } from './components/TopBar';
import { Sidebar } from './components/Sidebar';
import { CenterStage } from './components/CenterStage';
import { ChatPanel } from './components/ChatPanel';
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <div className="h-screen w-screen flex flex-col overflow-hidden">
          <TopBar />
          <div className="flex-1 flex overflow-hidden">
            <Sidebar />
            <CenterStage />
            <ChatPanel />
          </div>
        </div>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
