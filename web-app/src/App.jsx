import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import HistoricPerformance from './pages/HistoricPerformance';
import Login from './pages/Login';
import Thresholds from './pages/Thresholds';
import TradeTargets from './pages/TradeTargets';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import { Toaster } from 'sonner';

function App() {
  return (
    <AuthProvider>
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/thresholds"
            element={
              <ProtectedRoute>
                <Thresholds />
              </ProtectedRoute>
            }
          />
          <Route
            path="/targets"
            element={
              <ProtectedRoute>
                <TradeTargets />
              </ProtectedRoute>
            }
          />
          <Route
            path="/historic"
            element={
              <ProtectedRoute>
                <HistoricPerformance />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
