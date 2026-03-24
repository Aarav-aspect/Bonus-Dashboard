import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Thresholds from './pages/Thresholds';
import TradeTargets from './pages/TradeTargets';
import KpiDetails from './pages/KpiDetails';
import AccountManagement from './pages/AccountManagement';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/layout/ProtectedRoute';
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
            path="/kpi-details"
            element={
              <ProtectedRoute>
                <KpiDetails />
              </ProtectedRoute>
            }
          />
          <Route
            path="/account-management"
            element={
              <ProtectedRoute>
                <AccountManagement />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
