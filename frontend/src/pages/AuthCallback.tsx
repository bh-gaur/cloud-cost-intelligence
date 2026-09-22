import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authApi } from '../api/authApi';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const AuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleGoogleCallback = async () => {
      const searchParams = new URLSearchParams(location.search);
      const code = searchParams.get('code');

      if (!code) {
        setError('No authorization code received from Google OAuth.');
        return;
      }

      try {
        const res = await authApi.googleAuth({
          code,
          redirect_uri: `${window.location.origin}/auth/callback`,
        });

        if (res.data?.access_token) {
          localStorage.setItem('access_token', res.data.access_token);
          if (res.data.refresh_token) {
            localStorage.setItem('refresh_token', res.data.refresh_token);
          }
          window.location.href = '/dashboard';
        } else {
          setError('Failed to retrieve access token from Google authentication response.');
        }
      } catch (err: any) {
        setError(err.response?.data?.error?.message || err.message || 'Google OAuth exchange failed.');
      }
    };

    handleGoogleCallback();
  }, [location, navigate]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#09090b] dark:text-zinc-100 flex flex-col items-center justify-center p-4 transition-colors duration-200">
      <div className="max-w-md w-full bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800 rounded-2xl p-8 text-center shadow-2xl backdrop-blur-xl">
        {error ? (
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-500 dark:text-rose-400 mx-auto flex items-center justify-center">
              <AlertCircle className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Google Login Failed</h2>
            <p className="text-xs text-rose-600 dark:text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-xl p-3">{error}</p>
            <button
              onClick={() => navigate('/login')}
              className="w-full py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 border border-slate-900 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 dark:!border-white transition-all shadow-md cursor-pointer"
            >
              Back to Login
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-slate-800 dark:text-zinc-200 mx-auto flex items-center justify-center">
              <RefreshCw className="w-6 h-6 animate-spin" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Completing Google Authentication</h2>
            <p className="text-xs text-slate-500 dark:text-zinc-400">Exchanging OAuth credentials & verifying identity with Cloud Cost Intelligence...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthCallback;
