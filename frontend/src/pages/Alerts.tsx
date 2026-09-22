import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BellRing,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  Info,
  ShieldCheck,
  Plus,
  Trash2,
  Send,
  Mail,
  Webhook,
  MessageSquare,
  X,
  AlertCircle,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { alertApi } from '../api/alertApi';
import { KpiCard } from '../components/KpiCard';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { ConfirmModal } from '../components/ConfirmModal';
import type { AnomalyEvent, BudgetRecord } from '../types';
import { useAuth } from '../context/AuthContext';

export const Alerts: React.FC = () => {
  const { activeOrg } = useAuth();
  const canManageIntegrations = activeOrg?.role === 'OWNER' || activeOrg?.role === 'ADMIN';

  const queryClient = useQueryClient();
  const [anomalies, setAnomalies] = useState<AnomalyEvent[]>([]);
  const [budgets, setBudgets] = useState<BudgetRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);

  // Deletion Modal state
  const [channelToDelete, setChannelToDelete] = useState<{ id: string; name: string } | null>(null);

  // Integration Modal State
  const [isAddIntegrationOpen, setIsAddIntegrationOpen] = useState(false);
  const [channelType, setChannelType] = useState<'slack' | 'webhook' | 'email'>('slack');
  const [channelName, setChannelName] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [emailRecipients, setEmailRecipients] = useState('');
  const [integrationError, setIntegrationError] = useState<string | null>(null);
  const [integrationSuccess, setIntegrationSuccess] = useState<string | null>(null);

  // Fetch Notification Integrations
  const { data: integrationsResp, isLoading: isIntegrationsLoading } = useQuery({
    queryKey: ['notificationIntegrations'],
    queryFn: async () => {
      const res = await apiClient.get('/integrations');
      return res.data?.data || [];
    },
  });

  const createIntegrationMutation = useMutation({
    mutationFn: async (data: { name: string; channel_type: string; config: any }) => {
      const res = await apiClient.post('/integrations', data);
      return res.data;
    },
    onSuccess: () => {
      setIntegrationSuccess('Notification channel added successfully!');
      setIntegrationError(null);
      queryClient.invalidateQueries({ queryKey: ['notificationIntegrations'] });
      setTimeout(() => {
        setIsAddIntegrationOpen(false);
        setIntegrationSuccess(null);
        setChannelName('');
        setWebhookUrl('');
        setEmailRecipients('');
      }, 1500);
    },
    onError: (err: any) => {
      setIntegrationError(err.response?.data?.error?.message || err.message || 'Failed to add channel.');
    },
  });

  const testIntegrationMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await apiClient.post(`/integrations/${id}/test`);
      return res.data;
    },
    onSuccess: (res) => {
      alert(res.data?.message || 'Test notification sent successfully!');
      queryClient.invalidateQueries({ queryKey: ['notificationIntegrations'] });
    },
    onError: (err: any) => {
      alert(`Test notification failed: ${err.response?.data?.error?.message || err.message}`);
    },
  });

  const deleteIntegrationMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await apiClient.delete(`/integrations/${id}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notificationIntegrations'] });
    },
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [anomRes, budRes] = await Promise.all([
        alertApi.getAnomalies(),
        alertApi.getBudgets(),
      ]);

      if (anomRes.success && anomRes.data) setAnomalies(anomRes.data);
      if (budRes.success && budRes.data) setBudgets(budRes.data);
    } catch (err) {
      console.error('Failed to load alert data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleScan = async () => {
    try {
      setScanning(true);
      setScanMessage(null);
      const res = await alertApi.triggerScan();
      if (res.success && res.data) {
        setScanMessage(res.data.message || `Scan completed. Found ${res.data.anomalies_count} anomalies.`);
        await fetchData();
      }
    } catch (err) {
      console.error('Scan error:', err);
      setScanMessage('Failed to run anomaly scan.');
    } finally {
      setScanning(false);
    }
  };

  const handleAddIntegrationSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!channelName) {
      setIntegrationError('Please provide a channel name.');
      return;
    }

    const config =
      channelType === 'email'
        ? { recipients: emailRecipients.split(',').map((r) => r.trim()).filter(Boolean) }
        : { webhook_url: webhookUrl.trim() };

    createIntegrationMutation.mutate({
      name: channelName.trim(),
      channel_type: channelType,
      config,
    });
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-300 border-red-300 dark:border-red-800';
      case 'WARNING':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border-amber-300 dark:border-amber-800';
      default:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border-blue-300 dark:border-blue-800';
    }
  };

  const integrations = integrationsResp || [];
  const criticalCount = anomalies.filter((a) => a.severity.toUpperCase() === 'CRITICAL').length;
  const exceededBudgetsCount = budgets.filter((b) => Number(b.percentage_consumed) >= 100).length;

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Alerts & Anomaly Detection</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Real-time spend anomaly detection, AWS Budgets threshold tracking, and multi-channel alert dispatch.
          </p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl font-medium text-sm transition-colors shadow-sm cursor-pointer shrink-0"
        >
          <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
          {scanning ? 'Scanning Anomaly Engine...' : 'Scan for Anomalies'}
        </button>
      </div>

      {scanMessage && (
        <div className="flex items-center gap-2 p-4 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 rounded-xl text-sm text-blue-800 dark:text-blue-300">
          <Info className="w-5 h-5 flex-shrink-0" />
          <span>{scanMessage}</span>
        </div>
      )}

      {/* KPI Overview */}
      {loading && anomalies.length === 0 && budgets.length === 0 ? (
        <LoadingSkeleton rows={3} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Total Anomalies"
            value={anomalies.length.toString()}
            icon={<AlertTriangle className="w-5 h-5 text-amber-500" />}
          />
          <KpiCard
            title="Critical Incidents"
            value={criticalCount.toString()}
            icon={<BellRing className="w-5 h-5 text-rose-500" />}
          />
          <KpiCard
            title="Active Budgets"
            value={budgets.length.toString()}
            icon={<CheckCircle2 className="w-5 h-5 text-blue-500" />}
          />
          <KpiCard
            title="Budgets Exceeded"
            value={exceededBudgetsCount.toString()}
            icon={<AlertTriangle className="w-5 h-5 text-red-500" />}
          />
        </div>
      )}

      {/* NEW: Notification Channels & Destinations Section */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <BellRing className="w-5 h-5 text-blue-600 dark:text-cyan-400" />
              Per-Organization Alert Channels
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Configure Slack Webhooks, Custom Webhooks, and Email alert destinations directly for your organization.
            </p>
          </div>
          {canManageIntegrations && (
            <button
              onClick={() => {
                setIsAddIntegrationOpen(true);
                setIntegrationError(null);
                setIntegrationSuccess(null);
              }}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold text-white bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 dark:hover:bg-slate-700 rounded-xl transition-colors cursor-pointer shrink-0"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Alert Channel
            </button>
          )}
        </div>

        {isIntegrationsLoading ? (
          <LoadingSkeleton rows={2} />
        ) : integrations.length === 0 ? (
          <div className="p-6 text-center space-y-2 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800">
            <MessageSquare className="w-6 h-6 text-slate-400 mx-auto" />
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300">No Alert Channels Configured</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Add a Slack Webhook or Email destination to receive instant notifications when spend anomalies or budget limits occur.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {integrations.map((item: any) => (
              <div
                key={item.id}
                className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/60 dark:bg-slate-950/60 space-y-3 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {item.channel_type === 'slack' && <MessageSquare className="w-4 h-4 text-emerald-500" />}
                      {item.channel_type === 'webhook' && <Webhook className="w-4 h-4 text-indigo-500" />}
                      {item.channel_type === 'email' && <Mail className="w-4 h-4 text-blue-500" />}
                      <span className="text-xs font-bold text-slate-900 dark:text-white">{item.name}</span>
                    </div>
                    {canManageIntegrations && (
                      <button
                        onClick={() => setChannelToDelete({ id: item.id, name: item.name })}
                        className="text-slate-400 hover:text-rose-500 transition-colors p-1 cursor-pointer"
                        title="Delete Channel"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono truncate">
                    {item.channel_type === 'email'
                      ? `Recipients: ${item.config?.recipients?.join(', ') || 'Default'}`
                      : item.config?.webhook_url || 'URL Configured'}
                  </p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-slate-800 text-[11px]">
                  <span
                    className={`px-2 py-0.5 rounded-full font-bold ${
                      item.test_status === 'SUCCESS'
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                        : 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                    }`}
                  >
                    {item.test_status}
                  </span>
                  <button
                    onClick={() => testIntegrationMutation.mutate(item.id)}
                    disabled={testIntegrationMutation.isPending}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 dark:text-cyan-400 hover:underline cursor-pointer"
                  >
                    <Send className="w-3 h-3" />
                    Send Test
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Integration Modal */}
      {isAddIntegrationOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <BellRing className="w-4 h-4 text-blue-600 dark:text-cyan-400" />
                Add Notification Integration
              </h3>
              <button
                onClick={() => setIsAddIntegrationOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {integrationError && (
              <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                <span>{integrationError}</span>
              </div>
            )}
            {integrationSuccess && (
              <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 text-emerald-700 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                <span>{integrationSuccess}</span>
              </div>
            )}

            <form onSubmit={handleAddIntegrationSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Channel Type
                </label>
                <select
                  value={channelType}
                  onChange={(e) => setChannelType(e.target.value as any)}
                  className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                >
                  <option value="slack">Slack Webhook</option>
                  <option value="webhook">Custom HTTP Webhook</option>
                  <option value="email">Email Notification List</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Integration Name
                </label>
                <input
                  type="text"
                  required
                  value={channelName}
                  onChange={(e) => setChannelName(e.target.value)}
                  placeholder="e.g. FinOps Incident Slack Channel"
                  className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </div>

              {channelType !== 'email' ? (
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Webhook URL <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="url"
                    required
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                    placeholder="https://hooks.slack.com/services/..."
                    className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Email Recipients (Comma Separated)
                  </label>
                  <input
                    type="text"
                    required
                    value={emailRecipients}
                    onChange={(e) => setEmailRecipients(e.target.value)}
                    placeholder="finops@company.com, admin@company.com"
                    className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddIntegrationOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-xl transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createIntegrationMutation.isPending}
                  className="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 rounded-xl shadow transition-colors cursor-pointer disabled:opacity-50"
                >
                  {createIntegrationMutation.isPending ? 'Saving...' : 'Save Channel'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* AWS Budgets Section */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
          AWS Budgets Performance
        </h2>
        {loading && budgets.length === 0 ? (
          <LoadingSkeleton rows={2} />
        ) : budgets.length === 0 ? (
          <EmptyState
            icon={<CheckCircle2 className="w-8 h-8 text-emerald-500" />}
            title="No Active Budgets"
            description="Budgets will populate automatically when AWS accounts are connected."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {budgets.map((b) => {
              const limit = Number(b.budget_limit);
              const actual = Number(b.current_spend);
              const pct = limit > 0 ? (actual / limit) * 100 : Number(b.percentage_consumed) || 0;
              const isExceeded = pct >= 100;
              const isWarn = pct >= 80 && pct < 100;

              return (
                <div
                  key={b.id}
                  className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-900/50 space-y-3"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-slate-900 dark:text-white text-sm">{b.budget_name}</h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400">Account: {b.account_id}</p>
                    </div>
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${isExceeded ? 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300 border-red-300' :
                        isWarn ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border-amber-300' :
                          'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border-emerald-300'
                      }`}>
                      {pct.toFixed(1)}%
                    </span>
                  </div>

                  <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${isExceeded ? 'bg-red-500' : isWarn ? 'bg-amber-500' : 'bg-emerald-500'
                        }`}
                      style={{ width: `${Math.min(pct, 100)}%` }}
                    />
                  </div>

                  <div className="grid grid-cols-2 text-xs pt-1 border-t border-slate-200 dark:border-slate-800">
                    <div>
                      <span className="text-slate-500 dark:text-slate-400">Actual Spend:</span>
                      <p className="font-semibold text-slate-900 dark:text-white">
                        ${actual.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500 dark:text-slate-400">Budget Limit:</span>
                      <p className="font-semibold text-slate-900 dark:text-white">
                        ${limit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Anomalies Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-200 dark:border-slate-800">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Cost Anomaly Timeline</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Statistical deviation alerts triggered by unusual spikes in cloud resource consumption.
          </p>
        </div>

        {loading && anomalies.length === 0 ? (
          <div className="p-6">
            <LoadingSkeleton rows={5} />
          </div>
        ) : anomalies.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={<ShieldCheck className="w-8 h-8 text-emerald-500" />}
              title="Zero Cost Anomalies Detected"
              description="Spending across all AWS services is within expected statistical baseline boundaries."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs uppercase font-medium text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3">Timestamp / Date</th>
                  <th className="px-5 py-3">Incident Title / Service</th>
                  <th className="px-5 py-3">Severity</th>
                  <th className="px-5 py-3 text-right">Detected Cost</th>
                  <th className="px-5 py-3 text-right">Expected Cost</th>
                  <th className="px-5 py-3 text-right">Deviation %</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono text-xs">
                {anomalies.map((a) => {
                  const detected = Number(a.detected_value);
                  const expected = a.expected_value ? Number(a.expected_value) : null;
                  const diffPct = a.difference_percentage ? Number(a.difference_percentage) : null;
                  const formattedDetected = detected < 1.0 ? `$${detected.toFixed(4)}` : `$${detected.toFixed(2)}`;
                  const formattedExpected = expected !== null ? (expected < 1.0 ? `$${expected.toFixed(4)}` : `$${expected.toFixed(2)}`) : '-';

                  return (
                    <tr key={a.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-3 whitespace-nowrap text-slate-900 dark:text-white">
                        {new Date(a.created_at).toLocaleDateString(undefined, { timeZone: 'UTC', year: 'numeric', month: 'short', day: 'numeric' })}
                      </td>
                      <td className="px-5 py-3 font-sans">
                        <div className="font-semibold text-slate-900 dark:text-white">{a.title}</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          {a.service || 'General Cloud'} • Account: {a.account_id}
                        </div>
                        {a.message && (
                          <div className="text-[11px] text-slate-400 dark:text-slate-500 mt-1 line-clamp-1" title={a.message}>
                            {a.message}
                          </div>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${getSeverityBadge(a.severity)}`}>
                          {a.severity.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-right font-bold text-red-600 dark:text-red-400">
                        {formattedDetected}
                      </td>
                      <td className="px-5 py-3 text-right text-slate-600 dark:text-slate-400">
                        {formattedExpected}
                      </td>
                      <td className="px-5 py-3 text-right font-semibold text-red-600 dark:text-red-400">
                        {diffPct ? `+${diffPct.toFixed(1)}%` : '-'}
                      </td>
                      <td className="px-5 py-3">
                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 capitalize font-sans">
                          {a.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Channel Confirmation Modal */}
      <ConfirmModal
        isOpen={Boolean(channelToDelete)}
        onClose={() => setChannelToDelete(null)}
        onConfirm={() => {
          if (channelToDelete) {
            deleteIntegrationMutation.mutate(channelToDelete.id);
            setChannelToDelete(null);
          }
        }}
        title="Delete Notification Channel"
        message={`Are you sure you want to delete '${channelToDelete?.name || 'this channel'}'? Alerts will no longer be dispatched to this channel.`}
        confirmText="Delete Channel"
        cancelText="Cancel"
        variant="danger"
        isLoading={deleteIntegrationMutation.isPending}
      />
    </div>
  );
};

export default Alerts;
