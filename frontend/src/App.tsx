import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AuthProvider, useAuth } from './context/AuthContext';
import { CurrencyProvider } from './context/CurrencyContext';
import { Layout } from './components/Layout';

// Public Pages
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { ForgotPassword } from './pages/ForgotPassword';
import { ResetPassword } from './pages/ResetPassword';
import { VerifyEmail } from './pages/VerifyEmail';
import { AcceptInvite } from './pages/AcceptInvite';
import { AuthCallback } from './pages/AuthCallback';

// Protected Pages
import { Dashboard } from './pages/Dashboard';
import { Costs } from './pages/Costs';
import { Services } from './pages/Services';
import { Accounts } from './pages/Accounts';
import { Regions } from './pages/Regions';
import { Optimization } from './pages/Optimization';
import { Alerts } from './pages/Alerts';
import { Reports } from './pages/Reports';
import { Integrations } from './pages/Integrations';
import { TagGovernance } from './pages/TagGovernance';
import { Settings } from './pages/Settings';

// Admin Pages
import { AdminUsers } from './pages/AdminUsers';
import { AdminSystem } from './pages/AdminSystem';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

import { motion } from 'framer-motion';
import { Sparkles, TrendingUp } from 'lucide-react';

const StartupMotionLoader: React.FC = () => (
  <div className="h-screen w-screen flex items-center justify-center bg-slate-950 text-slate-100 overflow-hidden relative">
    <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(14,165,233,0.12),transparent_70%)]" />
    <motion.div
      initial={{ opacity: 0, scale: 0.88, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="relative z-10 flex flex-col items-center gap-5 text-center px-4"
    >
      <div className="relative flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
          className="w-16 h-16 rounded-2xl border-2 border-transparent border-t-sky-400 border-r-blue-500 shadow-[0_0_25px_rgba(14,165,233,0.3)]"
        />
        <div className="absolute p-3 rounded-xl bg-slate-900 border border-slate-800 text-sky-400 shadow-lg">
          <TrendingUp className="w-6 h-6 animate-pulse" />
        </div>
      </div>
      <div className="space-y-1">
        <motion.h2
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.15 }}
          className="text-base font-bold tracking-tight text-white flex items-center justify-center gap-1.5"
        >
          <span>Cloud Cost Intelligence</span>
          <Sparkles className="w-4 h-4 text-amber-400" />
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.25 }}
          className="text-xs font-semibold text-slate-400 uppercase tracking-widest"
        >
          Initializing FinOps Engine...
        </motion.p>
      </div>
    </motion.div>
  </div>
);

const RootRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <StartupMotionLoader />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Landing />;
};

const PublicOnlyRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <StartupMotionLoader />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

const ProtectedRoute: React.FC<{ children: React.ReactNode; requireAdmin?: boolean }> = ({
  children,
  requireAdmin = false
}) => {
  const { isAuthenticated, isAdmin, isLoading } = useAuth();

  if (isLoading) {
    return <StartupMotionLoader />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <CurrencyProvider>
          <BrowserRouter>
            <Routes>
            {/* Landing / About & Auth Routes */}
            <Route path="/" element={<RootRoute />} />
            <Route path="/about" element={<Landing />} />
            <Route
              path="/login"
              element={
                <PublicOnlyRoute>
                  <Login />
                </PublicOnlyRoute>
              }
            />
            <Route
              path="/register"
              element={
                <PublicOnlyRoute>
                  <Register />
                </PublicOnlyRoute>
              }
            />
            <Route
              path="/forgot-password"
              element={
                <PublicOnlyRoute>
                  <ForgotPassword />
                </PublicOnlyRoute>
              }
            />
            <Route
              path="/reset-password"
              element={
                <PublicOnlyRoute>
                  <ResetPassword />
                </PublicOnlyRoute>
              }
            />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/accept-invite" element={<AcceptInvite />} />
            <Route path="/auth/callback" element={<AuthCallback />} />

            {/* Protected FinOps Application Routes */}
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/costs" element={<Costs />} />
              <Route path="/services" element={<Services />} />
              <Route path="/accounts" element={<Accounts />} />
              <Route path="/regions" element={<Regions />} />
              <Route path="/optimization" element={<Optimization />} />
              <Route path="/tagging" element={<TagGovernance />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/integrations" element={<Navigate to="/accounts" replace />} />
              <Route path="/settings" element={<Settings />} />

              {/* Admin-Exclusive Routes */}
              <Route
                path="/admin/users"
                element={
                  <ProtectedRoute requireAdmin={true}>
                    <AdminUsers />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/system"
                element={
                  <ProtectedRoute requireAdmin={true}>
                    <AdminSystem />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* Catch-all fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </CurrencyProvider>
    </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;

