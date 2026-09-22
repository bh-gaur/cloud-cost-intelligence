import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  Building2,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  LogOut,
  Mail,
  Lock,
  User as UserIcon,
  TrendingDown,
  ChevronLeft,
  Eye,
  EyeOff,
} from 'lucide-react';
import { organizationApi } from '../api/organizationApi';
import { useAuth } from '../context/AuthContext';
import { ThemeToggle } from '../components/ThemeToggle';
import type { InviteDetails } from '../types';

export const AcceptInvite: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, logout, login, switchOrganization, refetchOrganizations } = useAuth();

  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get('token');

  const [invite, setInvite] = useState<InviteDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states for new or unauthenticated users
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [acceptSuccess, setAcceptSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setError('No invitation token provided. Please verify your invitation link.');
      setLoading(false);
      return;
    }

    const fetchDetails = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await organizationApi.getInviteDetails(token);
        if (res.success && res.data) {
          setInvite(res.data);
        } else {
          setError(res.error?.message || 'Failed to retrieve invitation details.');
        }
      } catch (err: any) {
        setError(err.response?.data?.error?.message || err.message || 'Invalid or expired invitation link.');
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [token]);

  // Authenticated 1-click Accept
  const handleAuthenticatedAccept = async () => {
    if (!token) return;
    try {
      setIsSubmitting(true);
      setError(null);
      const res = await organizationApi.acceptInvite(token);
      if (res.success) {
        setAcceptSuccess(res.data?.message || 'Successfully joined organization!');
        if (invite?.organization_id) {
          try {
            await switchOrganization(invite.organization_id);
          } catch (e) {
            // Non-blocking
          }
        }
        setTimeout(() => {
          navigate('/dashboard');
        }, 1200);
      } else {
        setError(res.error?.message || 'Could not accept invitation.');
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'Failed to accept invitation.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Brand-new user: Register + Set Password + Join Team
  const handleRegisterAndAccept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    if (!fullName.trim()) {
      setError('Please enter your full name.');
      return;
    }
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters long and include numbers and letters.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const res = await organizationApi.acceptInviteAndRegister({
        token,
        full_name: fullName.trim(),
        password,
      });

      if (res.success && res.data) {
        setAcceptSuccess(`Account created! Welcome to ${res.data.organization_name || 'your organization'}.`);
        if (res.data.access_token) {
          localStorage.setItem('access_token', res.data.access_token);
        }
        if (res.data.refresh_token) {
          localStorage.setItem('refresh_token', res.data.refresh_token);
        }
        if (res.data.organization_id) {
          localStorage.setItem('active_org_id', res.data.organization_id);
        }
        await refetchOrganizations();
        setTimeout(() => {
          navigate('/dashboard');
        }, 1200);
      } else {
        setError(res.error?.message || 'Registration failed.');
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'Failed to set password and join.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Existing user: Sign In + Join Team
  const handleLoginAndAccept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !invite) return;
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await login({ email: invite.email, password });
      const res = await organizationApi.acceptInvite(token);
      if (res.success) {
        setAcceptSuccess(`Successfully joined ${invite.organization_name}!`);
        if (invite.organization_id) {
          try {
            await switchOrganization(invite.organization_id);
          } catch (e) {
            // Non-blocking
          }
        }
        setTimeout(() => {
          navigate('/dashboard');
        }, 1200);
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'Authentication error.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSwitchAccount = async () => {
    await logout();
    navigate(`/login?email=${encodeURIComponent(invite?.email || '')}&redirect=${encodeURIComponent(location.pathname + location.search)}`);
  };

  const emailMatches = user && invite && user.email.trim().toLowerCase() === invite.email.trim().toLowerCase();

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

      {/* Main Content Container */}
      <main className="flex-1 flex items-center justify-center p-6 my-4">
        <div className="w-full max-w-md space-y-6">
          {/* Brand Header Badge */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-white dark:bg-[#141417] border border-slate-200 dark:border-zinc-800 shadow-lg p-3">
              <TrendingDown className="w-7 h-7 text-slate-800 dark:text-zinc-200" />
            </div>

            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              Organization Invitation
            </h1>
            <p className="text-xs text-slate-600 dark:text-zinc-400 font-medium">
              Join your team's AWS Cost Intelligence workspace
            </p>
          </div>

          {/* Form Card */}
          <div className="bg-white dark:bg-[#121215] border border-slate-200 dark:border-zinc-800/90 rounded-2xl p-7 shadow-xl dark:shadow-2xl dark:shadow-black/80 relative transition-colors duration-200">
            {loading ? (
              <div className="py-12 flex flex-col items-center justify-center gap-3">
                <div className="w-8 h-8 border-3 border-slate-800 dark:border-zinc-400 border-t-transparent rounded-full animate-spin" />
                <p className="text-xs font-semibold text-slate-600 dark:text-zinc-400 uppercase tracking-wider">
                  Verifying Invitation Token...
                </p>
              </div>
            ) : error && !invite ? (
              <div className="space-y-6 text-center py-4">
                <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-500 dark:text-rose-400 flex items-center justify-center mx-auto">
                  <AlertCircle className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">Invitation Unavailable</h2>
                  <p className="text-xs text-slate-600 dark:text-zinc-400 mt-2 leading-relaxed">
                    {error}
                  </p>
                </div>
                <div className="pt-2">
                  <Link
                    to="/login"
                    className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 shadow-md border border-slate-900 dark:!border-white transition-all"
                  >
                    Go to Sign In
                  </Link>
                </div>
              </div>
            ) : invite?.is_expired || invite?.status === 'EXPIRED' ? (
              <div className="space-y-6 text-center py-4">
                <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto">
                  <Clock className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">Invitation Expired</h2>
                  <p className="text-xs text-slate-600 dark:text-zinc-400 mt-2 leading-relaxed">
                    This invitation has expired. Please request a new invite link from your administrator.
                  </p>
                </div>
                <div className="pt-2">
                  <Link
                    to="/login"
                    className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 shadow-md border border-slate-900 dark:!border-white transition-all"
                  >
                    Return to Sign In
                  </Link>
                </div>
              </div>
            ) : invite?.status === 'ACCEPTED' ? (
              <div className="space-y-6 text-center py-4">
                <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">Already Accepted</h2>
                  <p className="text-xs text-slate-600 dark:text-zinc-400 mt-2 leading-relaxed">
                    This invitation has already been accepted. Sign in to access your organization workspace.
                  </p>
                </div>
                <div className="pt-2">
                  <Link
                    to="/login"
                    className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 shadow-md border border-slate-900 dark:!border-white transition-all"
                  >
                    Sign In to Dashboard
                  </Link>
                </div>
              </div>
            ) : (
              <div className="space-y-5">
                {/* Org Summary Card */}
                <div className="text-center space-y-2 pb-2">
                  <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 text-slate-800 dark:text-zinc-200 flex items-center justify-center mx-auto shadow-sm">
                    <Building2 className="w-6 h-6" />
                  </div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                    Join {invite?.organization_name}
                  </h2>
                  <p className="text-xs text-slate-600 dark:text-zinc-400">
                    You have been invited to join as an <strong className="font-semibold text-slate-800 dark:text-zinc-200">{invite?.role}</strong>
                  </p>
                </div>

                {/* Details Breakdown */}
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-[#09090b] border border-slate-200 dark:border-zinc-800 space-y-2.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600 dark:text-zinc-400 flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5" /> Invited Email
                    </span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      {invite?.email}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600 dark:text-zinc-400 flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5" /> Assigned Role
                    </span>
                    <span className="px-2.5 py-0.5 rounded-md font-bold bg-slate-200 dark:bg-zinc-800 text-slate-800 dark:text-zinc-200 border border-slate-300 dark:border-zinc-700 uppercase tracking-wider text-[10px]">
                      {invite?.role}
                    </span>
                  </div>
                </div>

                {/* Alerts */}
                {error && (
                  <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-300 text-xs flex items-center gap-2.5">
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-500 dark:text-rose-400" />
                    <span>{error}</span>
                  </div>
                )}
                {acceptSuccess && (
                  <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-300 text-xs flex items-center gap-2.5">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                    <span>{acceptSuccess}</span>
                  </div>
                )}

                {/* Case 1: Currently Logged In */}
                {isAuthenticated ? (
                  emailMatches ? (
                    <div className="space-y-3 pt-2">
                      <button
                        onClick={handleAuthenticatedAccept}
                        disabled={isSubmitting || !!acceptSuccess}
                        className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 shadow-md border border-slate-900 dark:!border-white transition-all cursor-pointer disabled:opacity-50"
                      >
                        {isSubmitting ? 'Joining Organization...' : 'Accept Invitation & Enter Workspace'}
                        <ArrowRight className="w-4 h-4 text-white dark:!text-zinc-950" />
                      </button>
                      <p className="text-[11px] text-center text-slate-500 dark:text-zinc-400">
                        Signed in as <span className="font-medium text-slate-800 dark:text-zinc-300">{user?.email}</span>
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4 pt-2">
                      <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-300 text-xs leading-relaxed">
                        You are signed in as <strong className="font-mono">{user?.email}</strong>, but this invitation was sent to <strong className="font-mono">{invite?.email}</strong>.
                      </div>
                      <button
                        onClick={handleSwitchAccount}
                        className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-bold text-slate-800 dark:text-zinc-200 bg-slate-100 hover:bg-slate-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Switch Account to {invite?.email}</span>
                      </button>
                    </div>
                  )
                ) : invite?.user_exists === false ? (
                  /* Case 2: Unauthenticated + Brand New User (Set Name & Password) */
                  <form onSubmit={handleRegisterAndAccept} className="space-y-4 pt-2">
                    <div className="p-3 bg-slate-100 dark:bg-zinc-800/60 border border-slate-200 dark:border-zinc-700 rounded-xl text-xs text-slate-700 dark:text-zinc-300">
                      Complete registration below to join <strong>{invite.organization_name}</strong>.
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 dark:text-zinc-300 uppercase tracking-wider mb-1.5">
                        Full Name
                      </label>
                      <div className="relative rounded-xl shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-zinc-400">
                          <UserIcon className="w-4 h-4" />
                        </div>
                        <input
                          type="text"
                          required
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          placeholder="John Doe"
                          className="block w-full pl-10 pr-3.5 py-2.5 text-sm bg-slate-50 dark:bg-[#09090b] border border-slate-300 dark:border-zinc-800 rounded-xl text-slate-900 dark:text-zinc-100 placeholder-slate-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-zinc-600/40 focus:border-slate-400 dark:focus:border-zinc-500 transition-colors"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 dark:text-zinc-300 uppercase tracking-wider mb-1.5">
                        Set Password
                      </label>
                      <div className="relative rounded-xl shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-zinc-400">
                          <Lock className="w-4 h-4" />
                        </div>
                        <input
                          type={showPassword ? 'text' : 'password'}
                          required
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          placeholder="••••••••••••"
                          className="block w-full pl-10 pr-10 py-2.5 text-sm bg-slate-50 dark:bg-[#09090b] border border-slate-300 dark:border-zinc-800 rounded-xl text-slate-900 dark:text-zinc-100 placeholder-slate-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-zinc-600/40 focus:border-slate-400 dark:focus:border-zinc-500 transition-colors"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 dark:text-zinc-400 hover:text-slate-700 dark:hover:text-zinc-200 transition-colors"
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isSubmitting || !!acceptSuccess}
                      className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-bold text-white bg-slate-900 hover:bg-slate-800 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 shadow-md border border-slate-900 dark:!border-white transition-all cursor-pointer disabled:opacity-50 mt-2"
                    >
                      {isSubmitting ? 'Creating Account & Joining...' : `Set Password & Join ${invite.organization_name}`}
                      <ArrowRight className="w-4 h-4 text-white dark:!text-zinc-950" />
                    </button>
                  </form>
                ) : (
                  /* Case 3: Unauthenticated + Existing User (Enter Password to Sign In) */
                  <form onSubmit={handleLoginAndAccept} className="space-y-4 pt-2">
                    <div className="p-3 bg-slate-100 dark:bg-zinc-800/60 border border-slate-200 dark:border-zinc-700 rounded-xl text-xs text-slate-700 dark:text-zinc-300">
                      An account exists for <strong className="font-mono text-slate-900 dark:text-white">{invite?.email}</strong>. Enter your password to sign in and accept the invitation.
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 dark:text-zinc-300 uppercase tracking-wider mb-1.5">
                        Account Password
                      </label>
                      <div className="relative rounded-xl shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-zinc-400">
                          <Lock className="w-4 h-4" />
                        </div>
                        <input
                          type={showPassword ? 'text' : 'password'}
                          required
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          placeholder="••••••••••••"
                          className="block w-full pl-10 pr-10 py-2.5 text-sm bg-slate-50 dark:bg-[#09090b] border border-slate-300 dark:border-zinc-800 rounded-xl text-slate-900 dark:text-zinc-100 placeholder-slate-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-zinc-600/40 focus:border-slate-400 dark:focus:border-zinc-500 transition-colors"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 dark:text-zinc-400 hover:text-slate-700 dark:hover:text-zinc-200 transition-colors"
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isSubmitting || !!acceptSuccess}
                      className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-bold text-white bg-slate-900 hover:bg-slate-800 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 shadow-md border border-slate-900 dark:!border-white transition-all cursor-pointer disabled:opacity-50 mt-2"
                    >
                      {isSubmitting ? 'Signing In...' : `Sign In & Join ${invite?.organization_name}`}
                      <ArrowRight className="w-4 h-4 text-white dark:!text-zinc-950" />
                    </button>
                  </form>
                )}
              </div>
            )}
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

export default AcceptInvite;
