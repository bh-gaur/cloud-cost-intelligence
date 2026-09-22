import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Lock,
  Mail,
  AlertCircle,
  ArrowRight,
  TrendingDown,
  Sparkles,
  ShieldCheck,
  ChevronLeft,
  Key,
  Eye,
  EyeOff,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ThemeToggle } from '../components/ThemeToggle';
import { apiClient } from '../api/client';
import { authApi } from '../api/authApi';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { data: authConfig } = useQuery({
    queryKey: ['authConfig'],
    queryFn: async () => {
      try {
        const res = await apiClient.get('/auth/config');
        return res.data?.data;
      } catch {
        return null;
      }
    },
    staleTime: 1000 * 60 * 5,
  });

  const handleGoogleSignIn = async () => {
    setError(null);
    setLoading(true);

    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || authConfig?.google_client_id;

    if (googleClientId) {
      // Initiate real Google OAuth Authorization Flow
      const redirectUri = `${window.location.origin}/auth/callback`;
      const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
        `client_id=${encodeURIComponent(googleClientId)}&` +
        `redirect_uri=${encodeURIComponent(redirectUri)}&` +
        `response_type=code&` +
        `scope=${encodeURIComponent('openid email profile')}&` +
        `prompt=select_account`;
      window.location.href = googleAuthUrl;
      return;
    }

    // Fallback for demo testing when no Google Client ID is configured
    try {
      const res = await authApi.googleAuth({ code: 'demo' });
      if (res.data?.access_token) {
        localStorage.setItem('access_token', res.data.access_token);
        if (res.data.refresh_token) {
          localStorage.setItem('refresh_token', res.data.refresh_token);
        }
        window.location.href = '/dashboard';
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'Google Sign-In failed.');
    } finally {
      setLoading(false);
    }
  };

  const { data: healthResp } = useQuery({
    queryKey: ['healthState'],
    queryFn: async () => {
      const res = await apiClient.get('/health');
      return res.data?.data;
    },
    staleTime: 1000 * 60 * 5,
  });

  const searchParams = new URLSearchParams(location.search);
  const isDemoParam = searchParams.get('demo') === 'true';
  const showDemoOptions = isDemoParam || (healthResp?.demo_mode === true);
  const redirectUrl = searchParams.get('redirect') || '/dashboard';
  const emailParam = searchParams.get('email');

  useEffect(() => {
    if (emailParam && !isDemoParam) {
      setEmail(emailParam);
    }
  }, [emailParam, isDemoParam]);

  // Pre-fill demo credentials if query param ?demo=true is set
  useEffect(() => {
    if (isDemoParam) {
      setEmail('admin@cloudcost.local');
      setPassword('Admin123!@#');
    }
  }, [isDemoParam]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login({ email, password });
      navigate(redirectUrl);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoAdmin = () => {
    setEmail('admin@cloudcost.local');
    setPassword('Admin123!@#');
  };

  const fillDemoUser = () => {
    setEmail('user@cloudcost.local');
    setPassword('User123!@#');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#09090b] dark:text-zinc-100 font-sans flex flex-col justify-between selection:bg-slate-300 dark:selection:bg-zinc-700 selection:text-slate-900 dark:selection:text-white relative overflow-hidden transition-colors duration-200">
      {/* Subtle Ambient Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[400px] bg-gradient-to-b from-slate-200/40 via-slate-100/10 dark:from-zinc-800/15 dark:via-zinc-900/5 to-transparent blur-3xl pointer-events-none -z-10" />

      {/* Top Header Bar */}
      <header className="px-6 py-6 max-w-7xl mx-auto w-full flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 text-slate-600 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-white transition-colors group">
          <ChevronLeft className="w-4 h-4 text-slate-500 dark:text-zinc-400 group-hover:-translate-x-1 transition-transform" />
          <span className="text-xs font-bold uppercase tracking-wider">Back to Platform Overview</span>
        </Link>
        <ThemeToggle />
      </header>

      {/* Main Login Form Container */}
      <main className="flex-1 flex items-center justify-center p-6 my-4">
        <div className="w-full max-w-md space-y-6">
          {/* Brand Header Badge */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-white border border-slate-200 dark:bg-[#141417] dark:border-zinc-800 shadow-lg p-3">
              <TrendingDown className="w-7 h-7 text-slate-800 dark:text-zinc-200" />
            </div>

            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              Welcome back
            </h1>
            <p className="text-xs text-slate-600 dark:text-zinc-400 font-medium">
              Sign in to your FinOps workspace
            </p>
          </div>

          {/* Form Card */}
          <div className="bg-white border border-slate-200 shadow-xl dark:bg-[#121215] dark:border-zinc-800/90 rounded-2xl p-7 dark:shadow-2xl dark:shadow-black/80 relative transition-colors duration-200">
            {error && (
              <div className="mb-5 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-300 text-xs flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-500 dark:text-rose-400" />
                <span>{error}</span>
              </div>
            )}

            <form className="space-y-4" onSubmit={handleLogin}>
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-zinc-300 uppercase tracking-wider mb-1.5">
                  Work Email
                </label>
                <div className="relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-zinc-400">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="block w-full pl-10 pr-3.5 py-2.5 text-sm bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 dark:bg-[#09090b] dark:border-zinc-800 dark:text-zinc-100 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-zinc-600/40 focus:border-slate-400 dark:focus:border-zinc-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-bold text-slate-700 dark:text-zinc-300 uppercase tracking-wider">
                    Password
                  </label>
                  <Link
                    to="/forgot-password"
                    className="text-[11px] font-semibold text-slate-600 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-zinc-200 transition-colors"
                  >
                    Forgot password?
                  </Link>
                </div>
                <div className="relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-zinc-400">
                    <Lock className="h-4 w-4" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="block w-full pl-10 pr-10 py-2.5 text-sm bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 dark:bg-[#09090b] dark:border-zinc-800 dark:text-zinc-100 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-zinc-600/40 focus:border-slate-400 dark:focus:border-zinc-500 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 dark:text-zinc-400 hover:text-slate-700 dark:hover:text-zinc-200 transition-colors"
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl text-sm font-bold text-white bg-slate-900 hover:bg-slate-800 border border-slate-900 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 dark:!border-white shadow-md transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 mt-2 cursor-pointer"
              >
                {loading ? 'Signing in...' : 'Sign In'}
                <ArrowRight className="w-4 h-4 text-white dark:!text-zinc-950" />
              </button>
            </form>

            <div className="my-5 flex items-center gap-3">
              <div className="flex-1 h-px bg-slate-200 dark:bg-zinc-800/80" />
              <span className="text-[11px] text-slate-500 dark:text-zinc-500 font-medium uppercase tracking-wider">or continue with</span>
              <div className="flex-1 h-px bg-slate-200 dark:bg-zinc-800/80" />
            </div>

            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={loading}
              className="w-full flex justify-center items-center gap-3 py-2.5 px-4 rounded-xl text-xs font-bold text-slate-800 bg-white border border-slate-300 hover:bg-slate-100 dark:text-white dark:bg-[#18181b] dark:border-zinc-700 dark:hover:bg-zinc-800 transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              Continue with Google
            </button>

            {/* Quick Demo Credentials Section - Rendered in Demo Mode */}
            {showDemoOptions && (
              <div className="mt-6 pt-5 border-t border-slate-200 dark:border-zinc-800">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[11px] font-bold text-slate-600 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
                    Quick One-Click Demo Access
                  </span>
                  <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    DEMO MODE
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2.5">
                  <button
                    type="button"
                    onClick={fillDemoAdmin}
                    className="px-3 py-2 text-xs font-semibold text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-200 dark:text-zinc-200 dark:bg-zinc-800/70 dark:hover:bg-zinc-800 dark:border-zinc-700/80 rounded-xl transition-all text-left flex items-center justify-between group cursor-pointer"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Key className="w-3.5 h-3.5 text-slate-600 dark:text-zinc-300 shrink-0" />
                      <span className="truncate">Demo Admin</span>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={fillDemoUser}
                    className="px-3 py-2 text-xs font-semibold text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-200 dark:text-zinc-300 dark:bg-zinc-900/90 dark:hover:bg-zinc-800 dark:border-zinc-800 rounded-xl transition-all text-left flex items-center justify-between group cursor-pointer"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <ShieldCheck className="w-3.5 h-3.5 text-slate-600 dark:text-zinc-400 shrink-0" />
                      <span className="truncate">Demo User</span>
                    </div>
                  </button>
                </div>
              </div>
            )}

            {/* Registration Link */}
            <div className="mt-6 text-center pt-2">
              <Link
                to="/register"
                className="text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-white transition-colors inline-flex items-center gap-1"
              >
                <span>Don't have an account? Create an organization</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 px-6 max-w-7xl mx-auto w-full text-center text-xs text-slate-500 dark:text-zinc-500">
        <p>AWS Cost Intelligence & FinOps Platform • Enterprise Multi-Tenancy Architecture</p>
      </footer>
    </div>
  );
};

export default Login;
