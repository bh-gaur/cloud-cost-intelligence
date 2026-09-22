import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Mail,
  AlertCircle,
  ArrowRight,
  TrendingDown,
  ChevronLeft,
  CheckCircle2,
} from 'lucide-react';
import { ThemeToggle } from '../components/ThemeToggle';
import { authApi } from '../api/authApi';

export const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await authApi.forgotPassword(email);
      setSubmitted(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Unable to process request.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#09090b] text-slate-900 dark:text-zinc-100 font-sans flex flex-col justify-between selection:bg-slate-300 dark:selection:bg-zinc-700 selection:text-slate-900 dark:selection:text-white relative overflow-hidden transition-colors duration-200">
      {/* Subtle Ambient Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[400px] bg-gradient-to-b from-slate-200/40 dark:from-zinc-800/15 via-slate-100/10 dark:via-zinc-900/5 to-transparent blur-3xl pointer-events-none -z-10" />

      {/* Top Header Bar */}
      <header className="px-6 py-6 max-w-7xl mx-auto w-full flex items-center justify-between">
        <Link to="/login" className="flex items-center gap-2.5 text-slate-600 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-white transition-colors group">
          <ChevronLeft className="w-4 h-4 text-slate-500 dark:text-zinc-400 group-hover:-translate-x-1 transition-transform" />
          <span className="text-xs font-bold uppercase tracking-wider">Back to Sign In</span>
        </Link>
        <ThemeToggle />
      </header>

      {/* Main Forgot Password Container */}
      <main className="flex-1 flex items-center justify-center p-6 my-4">
        <div className="w-full max-w-md space-y-6">
          {/* Brand Header Badge */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-white dark:bg-[#141417] border border-slate-200 dark:border-zinc-800 shadow-lg p-3">
              <TrendingDown className="w-7 h-7 text-slate-800 dark:text-zinc-200" />
            </div>

            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              Reset Password
            </h1>
            <p className="text-xs text-slate-600 dark:text-zinc-400 font-medium">
              Enter your work email to receive password reset instructions
            </p>
          </div>

          {/* Form Card */}
          <div className="bg-white dark:bg-[#121215] border border-slate-200 dark:border-zinc-800/90 rounded-2xl p-7 shadow-xl dark:shadow-2xl dark:shadow-black/80 relative transition-colors duration-200">
            {error && (
              <div className="mb-5 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-300 text-xs flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-500 dark:text-rose-400" />
                <span>{error}</span>
              </div>
            )}

            {submitted ? (
              <div className="space-y-5 text-center py-2">
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">Instructions Sent</h3>
                  <p className="text-xs text-slate-600 dark:text-zinc-400 leading-relaxed">
                    If an account exists for <strong className="text-slate-800 dark:text-zinc-200">{email}</strong>, password reset instructions have been sent to your inbox.
                  </p>
                </div>
                <div className="pt-3">
                  <Link
                    to="/login"
                    className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl text-xs font-bold text-slate-800 dark:text-zinc-200 bg-slate-100 hover:bg-slate-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 transition-colors"
                  >
                    Return to Sign In
                  </Link>
                </div>
              </div>
            ) : (
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-zinc-300 uppercase tracking-wider mb-1.5">
                    Work Email Address
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
                      className="block w-full pl-10 pr-3.5 py-2.5 text-sm bg-slate-50 dark:bg-[#09090b] border border-slate-300 dark:border-zinc-800 rounded-xl text-slate-900 dark:text-zinc-100 placeholder-slate-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-zinc-600/40 focus:border-slate-400 dark:focus:border-zinc-500 transition-colors"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl text-sm font-bold text-white bg-slate-900 hover:bg-slate-800 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 shadow-md border border-slate-900 dark:!border-white transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 mt-2"
                >
                  {loading ? 'Sending Instructions...' : 'Send Reset Instructions'}
                  <ArrowRight className="w-4 h-4 text-white dark:!text-zinc-950" />
                </button>
              </form>
            )}

            {/* Back to Login Link */}
            <div className="mt-6 text-center pt-2">
              <Link
                to="/login"
                className="text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-white transition-colors inline-flex items-center gap-1"
              >
                <span>Remembered your password? Sign in</span>
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

export default ForgotPassword;
