import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  TrendingDown,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ChevronDown,
  Filter,
  Copy,
  Check,
  Terminal,
  ShieldCheck,
  Zap,
  Layers,
} from 'lucide-react';
import { optimizationApi } from '../api/optimizationApi';
import { useDashboardContext } from '../components/Layout';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { formatCurrency } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';

export const Optimization: React.FC = () => {
  const { activeOrg } = useAuth();
  const canManage = activeOrg?.role === 'OWNER' || activeOrg?.role === 'ADMIN' || activeOrg?.role === 'FINOPS_MANAGER';

  const queryClient = useQueryClient();
  const { selectedAccount } = useDashboardContext();
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [confidenceFilter, setConfidenceFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const { data: recsResp, isLoading } = useQuery({
    queryKey: ['recommendations', selectedAccount, priorityFilter, confidenceFilter, statusFilter],
    queryFn: () =>
      optimizationApi.getRecommendations({
        accountId: selectedAccount,
        priority: priorityFilter,
        confidence: confidenceFilter,
        status: statusFilter,
      }),
  });

  const { data: summaryResp } = useQuery({
    queryKey: ['optSummary', selectedAccount],
    queryFn: () => optimizationApi.getSummary(selectedAccount),
  });

  const runMutation = useMutation({
    mutationFn: () => optimizationApi.triggerEvaluation(selectedAccount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
      queryClient.invalidateQueries({ queryKey: ['optSummary'] });
    },
  });

  const handleCopyCode = (id: string, code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const recs = recsResp?.data || [];
  const summary = summaryResp?.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <span>AWS Cost Optimization & Scanner</span>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/60 flex items-center gap-1">
              <Zap className="w-3 h-3 text-emerald-500" /> Deep Scanner Active
            </span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Real-time multi-account scanning for EC2, EBS, RDS, S3, NAT Gateways & ELB waste with 1-click CLI remediation
          </p>
        </div>

        {canManage && (
          <button
            onClick={() => runMutation.mutate()}
            disabled={runMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${runMutation.isPending ? 'animate-spin' : ''}`} />
            <span>{runMutation.isPending ? 'Scanning Live AWS Infrastructure...' : 'Run Live Deep Scan'}</span>
          </button>
        )}
      </div>

      {runMutation.isSuccess && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/60 rounded-xl text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Deep scan completed successfully. Recommendations and potential savings refreshed.</span>
        </div>
      )}

      {/* Savings Scorecard Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Potential Monthly Savings
          </span>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
            {formatCurrency(summary?.total_monthly_savings)}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Estimated monthly recurring reduction</p>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Potential Annual Savings
          </span>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
            {formatCurrency(summary?.total_annual_savings)}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Full 12-month run-rate impact</p>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Opportunities Discovered
          </span>
          <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
            {recs.length}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Across EC2, EBS, RDS, S3, & VPC</p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <Filter className="w-3.5 h-3.5" />
          <span>Filters:</span>
        </div>

        {/* Priority Filter */}
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="px-2.5 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Priorities</option>
          <option value="HIGH">High Priority</option>
          <option value="MEDIUM">Medium Priority</option>
          <option value="LOW">Low Priority</option>
        </select>

        {/* Confidence Filter */}
        <select
          value={confidenceFilter}
          onChange={(e) => setConfidenceFilter(e.target.value)}
          className="px-2.5 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Confidence Levels</option>
          <option value="Observed">Observed (100% Deterministic)</option>
          <option value="Estimated">Estimated (Metric-backed)</option>
          <option value="Potential">Potential (Architectural)</option>
        </select>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-2.5 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Validation Statuses</option>
          <option value="Requires validation">Requires Validation</option>
          <option value="Insufficient data">Insufficient Data</option>
        </select>
      </div>

      {/* Recommendations Cards */}
      {isLoading ? (
        <LoadingSkeleton rows={6} />
      ) : recs.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-12 text-center shadow-sm max-w-2xl mx-auto space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto border border-emerald-100 dark:border-emerald-800/60 shadow-inner">
            <Zap className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            No Optimization Findings Yet
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            Run a deep live scan against your connected AWS infrastructure to detect idle EC2 instances, unattached EBS volumes, gp2-to-gp3 upgrades, non-prod Multi-AZ databases, and networking waste.
          </p>
          {canManage && (
            <div className="pt-2">
              <button
                onClick={() => runMutation.mutate()}
                disabled={runMutation.isPending}
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl transition-all shadow-md hover:shadow-lg disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${runMutation.isPending ? 'animate-spin' : ''}`} />
                <span>{runMutation.isPending ? 'Scanning Live AWS Infrastructure...' : 'Run Live Deep Scan Now'}</span>
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {recs.map((r) => (
            <div
              key={r.id}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div className="flex-1 space-y-2.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        r.priority === 'HIGH'
                          ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-200 dark:border-rose-900/50'
                          : r.priority === 'MEDIUM'
                          ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200 dark:border-amber-900/50'
                          : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                      }`}
                    >
                      {r.priority}
                    </span>

                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400 border border-blue-200 dark:border-blue-900/50">
                      {r.confidence} Confidence
                    </span>

                    {r.production_safety_score !== undefined && r.production_safety_score !== null && (
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded flex items-center gap-1 border ${
                          r.production_safety_score >= 90
                            ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
                            : r.production_safety_score >= 70
                            ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border-amber-200 dark:border-amber-800'
                            : 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400 border-rose-200 dark:border-rose-800'
                        }`}
                      >
                        <ShieldCheck className="w-3 h-3" />
                        Safety: {r.production_safety_score}/100
                      </span>
                    )}

                    {r.implementation_effort && (
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                        Effort: {r.implementation_effort}
                      </span>
                    )}

                    <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono">
                      {r.rule_id}
                    </span>

                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      {r.service}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    {r.rule_name} —{' '}
                    <code className="text-xs font-mono font-normal text-blue-600 dark:text-blue-400">
                      {r.resource_name || r.resource_id}
                    </code>
                  </h4>

                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    <strong className="text-slate-900 dark:text-white">Finding:</strong> {r.reason}
                  </p>

                  <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg text-xs space-y-1">
                    <p className="text-slate-700 dark:text-slate-300 font-medium">
                      💡 <strong>Recommendation:</strong> {r.recommendation}
                    </p>
                    <p className="text-slate-500 dark:text-slate-400 text-[11px]">
                      🛠 <strong>Required Action:</strong> {r.action_required}
                    </p>
                  </div>

                  {/* CLI Remediation Snippet */}
                  {r.remediation_code && (
                    <div className="mt-2 rounded-lg bg-slate-950 text-slate-200 p-3 text-xs font-mono border border-slate-800 relative group">
                      <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-800/80 text-[11px] text-slate-400 font-sans">
                        <span className="flex items-center gap-1.5 text-slate-300 font-medium font-mono text-[10px]">
                          <Terminal className="w-3.5 h-3.5 text-emerald-400" /> CLI Remediation
                        </span>
                        <button
                          onClick={() => handleCopyCode(r.id, r.remediation_code!)}
                          className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                          title="Copy command to clipboard"
                        >
                          {copiedId === r.id ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-400" />
                              <span className="text-emerald-400">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy CLI</span>
                            </>
                          )}
                        </button>
                      </div>
                      <div className="overflow-x-auto text-[11px] text-emerald-300 whitespace-pre-wrap select-all font-mono">
                        {r.remediation_code}
                      </div>
                    </div>
                  )}
                </div>

                {/* Savings Pill */}
                <div className="md:text-right shrink-0 bg-emerald-50/60 dark:bg-emerald-950/20 p-4 rounded-xl border border-emerald-100 dark:border-emerald-900/30">
                  <span className="text-[11px] font-semibold text-emerald-800 dark:text-emerald-400 uppercase tracking-wider block">
                    Est. Monthly Savings
                  </span>
                  <div className="text-xl font-bold text-emerald-700 dark:text-emerald-400 mt-0.5">
                    {formatCurrency(r.estimated_monthly_savings)}
                  </div>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    {formatCurrency(r.estimated_annual_savings)} / year ({r.savings_percentage}%)
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};


