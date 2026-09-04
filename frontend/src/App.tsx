
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header } from './components/layout/Header';
import { Dashboard } from './components/screens/Dashboard';
import { RunDetails } from './components/screens/RunDetails';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-900">
        <Header />
        
        <main className="flex-1 overflow-y-auto px-4 py-8 md:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/run/:batchId" element={<RunDetails />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
