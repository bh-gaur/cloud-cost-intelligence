import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { ThemeToggle } from './ThemeToggle';
import { Sparkles, CheckCircle2, Building2, RefreshCw, Check } from 'lucide-react';
import { User } from '../types';
import { useAuth } from '../context/AuthContext';
import { useCurrency } from '../context/CurrencyContext';
import { costApi } from '../api/costApi';

interface HeaderProps {
  user?: User | null;
  isDemoMode?: boolean;
  lastSync?: string;
  selectedAccount?: string;
  onAccountChange?: (accountId: string) => void;
  accounts?: Array<{ account_id: string; account_name: string }>;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  isDemoMode = true,
  lastSync,
  selectedAccount = 'all',
  onAccountChange,
  accounts = [],
}) => {
  const { organizations, activeOrgId, activeOrg, switchOrganization } = useAuth();
  const { currency, setCurrency, exchangeRate, isRateLive } = useCurrency();
  const queryClient = useQueryClient();
  const [syncing, setSyncing] = useState(false);
  const [syncSuccess, setSyncSuccess] = useState<string | null>(null);

  const handleOrgChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newOrgId = e.target.value;
    if (newOrgId && newOrgId !== activeOrgId) {
      await switchOrganization(newOrgId);
      queryClient.invalidateQueries();
    }
  };

  const handleFetchLiveCosts = async () => {
    if (accounts.length === 0 && !isDemoMode) {
      alert("No AWS account connected to your organization. Please connect an AWS account under 'AWS Accounts' first.");
      return;
    }
    setSyncing(true);
    setSyncSuccess(null);
    try {
      const res = await costApi.syncLiveCosts(30);
      setSyncSuccess(res.data?.message || 'Synchronized live costs');
      queryClient.invalidateQueries();
      setTimeout(() => setSyncSuccess(null), 4000);
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to sync live costs from AWS');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 flex items-center justify-between transition-colors">
      <div className="flex items-center gap-4">
        {/* Organization Selector */}
        {organizations.length > 0 && (
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-slate-400 dark:text-slate-500" />
            <label htmlFor="org-select" className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              Org:
            </label>
            <select
              id="org-select"
              value={activeOrgId || ''}
              onChange={handleOrgChange}
              className="text-xs font-medium bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-slate-400"
            >
              {organizations.map((org) => (
                <option key={org.organization_id} value={org.organization_id}>
                  {org.organization_name} ({org.role})
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="h-4 w-px bg-slate-200 dark:bg-slate-800" />

        {/* Account Selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="account-select" className="text-xs font-semibold text-slate-500 dark:text-slate-400">
            Scope:
          </label>
          <select
            id="account-select"
            value={selectedAccount}
            onChange={(e) => onAccountChange?.(e.target.value)}
            className="text-xs font-medium bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-slate-400"
          >
            <option value="all">All AWS Accounts (Consolidated)</option>
            {accounts.map((acc) => (
              <option key={acc.account_id} value={acc.account_id}>
                {acc.account_name} ({acc.account_id.slice(-4)})
              </option>
            ))}
          </select>
        </div>

        {/* Mode Status Indicator */}
        {isDemoMode ? (
          <span className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span className="font-medium text-[11px]">Demo Mode</span>
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-medium text-[11px]">AWS Connected</span>
          </span>
        )}
      </div>

      {/* Right Tools: Sync Live Costs Button, Theme Toggle, User */}
      <div className="flex items-center gap-3">
        {syncSuccess ? (
          <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/40 px-3 py-1.5 rounded-lg border border-emerald-200 dark:border-emerald-800/80">
            <Check className="w-3.5 h-3.5 text-emerald-500" />
            <span>{syncSuccess}</span>
          </div>
        ) : (
          <button
            onClick={handleFetchLiveCosts}
            disabled={syncing}
            title="Triggers cost synchronization (Optimized with Local Cache to minimize AWS Cost Explorer API charges)"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition-all disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin text-blue-500' : 'text-slate-500 dark:text-slate-400'}`} />
            <span>{syncing ? 'Fetching Live AWS Costs...' : 'Fetch Live Cost'}</span>
          </button>
        )}

        {/* Currency Switcher ($ USD / ₹ INR) */}
        <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg border border-slate-200 dark:border-slate-700">
          <button
            type="button"
            onClick={() => {
              setCurrency('USD');
              queryClient.invalidateQueries();
            }}
            title="Display telemetry in US Dollars ($ USD)"
            className={`px-2 py-1 text-[11px] font-semibold rounded-md transition-all ${
              currency === 'USD'
                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-2xs'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            $ USD
          </button>
          <button
            type="button"
            onClick={() => {
              setCurrency('INR');
              queryClient.invalidateQueries();
            }}
            title={`Display telemetry in Indian Rupees (₹ INR - ${isRateLive ? 'Live' : 'Cached'} Rate: ₹${exchangeRate.toFixed(2)}/$)`}
            className={`px-2 py-1 text-[11px] font-semibold rounded-md transition-all ${
              currency === 'INR'
                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-2xs'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            ₹ INR
          </button>
        </div>

        <ThemeToggle />

        <div className="h-6 w-px bg-slate-200 dark:bg-slate-800" />

        {/* User Badge */}
        <div className="flex items-center gap-2 pl-1">
          <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-100 font-bold flex items-center justify-center text-xs uppercase border border-slate-300 dark:border-slate-600">
            {user?.email?.charAt(0) || 'U'}
          </div>
          <div className="hidden lg:block text-left">
            <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 leading-tight">
              {user?.full_name || user?.email?.split('@')[0] || 'User'}
            </p>
            <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
              {activeOrg?.role || user?.role || 'USER'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

