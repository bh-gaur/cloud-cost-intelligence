import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  DollarSign,
  TrendingDown,
  AlertTriangle,
  FileText,
  Tag,
  Download,
  ArrowUpRight,
  ArrowDownRight,
  Layers,
  Building2,
  Globe2,
  Calendar,
  Sparkles,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { useDashboardContext } from '../components/Layout';
import { dashboardApi } from '../api/dashboardApi';
import { serviceApi } from '../api/serviceApi';
import { accountApi } from '../api/accountApi';
import { regionApi } from '../api/regionApi';
import { optimizationApi } from '../api/optimizationApi';
import { reportApi } from '../api/reportApi';
import { KpiCard } from '../components/KpiCard';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { getServiceColor } from '../constants/serviceColors';
import { formatCurrency, toNumber } from '../utils/formatters';

const TrendTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const val = payload[0]?.value ?? 0;
    return (
      <div className="bg-slate-900 border border-slate-700 p-2.5 rounded-lg shadow-xl text-xs text-white">
        <p className="font-semibold text-slate-400 mb-1">{label}</p>
        <p className="font-bold text-sky-400">
          Spend: ${Number(val).toFixed(2)}
        </p>
      </div>
    );
  }
  return null;
};

const PieCustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const item = payload[0];
    return (
      <div className="bg-slate-900 border border-slate-700 p-2.5 rounded-lg shadow-xl text-xs text-white">
        <p className="font-semibold text-slate-400 mb-1">{item.name}</p>
        <p className="font-bold" style={{ color: item.payload?.color || '#38bdf8' }}>
          Cost: ${Number(item.value).toFixed(2)}
        </p>
      </div>
    );
  }
  return null;
};

const ScatterCustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const rawData = payload[0]?.payload || {};
    const dateVal = rawData.date || 'Cost Point';
    const costVal = rawData.total_cost ?? 0;
    return (
      <div className="bg-slate-900 border border-slate-700 p-2.5 rounded-lg shadow-xl text-xs text-white">
        <p className="font-semibold text-slate-400 mb-1">{dateVal}</p>
        <p className="font-bold text-sky-400">
          Spend: ${Number(costVal).toFixed(2)}
        </p>
      </div>
    );
  }
  return null;
};

export const Dashboard: React.FC = () => {
  const { selectedAccount } = useDashboardContext();
  const [trendRange, setTrendRange] = useState<'7d' | '14d' | '30d' | '90d' | 'mtd' | 'custom'>('30d');
  const [chartType, setChartType] = useState<'line' | 'bar' | 'donut' | 'scatter'>('line');

  const todayStr = new Date().toISOString().split('T')[0];
  const defaultStartStr = (() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().split('T')[0];
  })();

  const [startDate, setStartDate] = useState(defaultStartStr);
  const [endDate, setEndDate] = useState(todayStr);

  const customStart = trendRange === 'custom' && startDate ? startDate : undefined;
  const customEnd = trendRange === 'custom' && endDate ? endDate : undefined;

  // Queries
  const { data: summaryResp, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboardSummary', selectedAccount],
    queryFn: () => dashboardApi.getSummary(selectedAccount),
  });

  const { data: kpisResp, isLoading: kpisLoading } = useQuery({
    queryKey: ['dashboardKpis', selectedAccount, customStart, customEnd],
    queryFn: () => dashboardApi.getKpis(selectedAccount, customStart, customEnd),
  });

  const { data: trendsResp, isLoading: trendsLoading } = useQuery({
    queryKey: ['dashboardTrends', selectedAccount, trendRange, chartType, customStart, customEnd],
    queryFn: () => dashboardApi.getTrends(trendRange, chartType, selectedAccount, customStart, customEnd),
  });

  const { data: servicesResp } = useQuery({
    queryKey: ['dashboardServices', selectedAccount, trendRange],
    queryFn: () => serviceApi.getServices(selectedAccount, trendRange),
  });

  const { data: accountsResp } = useQuery({
    queryKey: ['dashboardAccounts', trendRange],
    queryFn: () => accountApi.getAccounts(trendRange),
  });

  const { data: regionsResp } = useQuery({
    queryKey: ['dashboardRegions', trendRange],
    queryFn: () => regionApi.getRegions(trendRange),
  });

  const { data: optSummaryResp } = useQuery({
    queryKey: ['optSummary', selectedAccount],
    queryFn: () => optimizationApi.getSummary(selectedAccount),
  });

  const { data: reportsResp } = useQuery({
    queryKey: ['recentReports'],
    queryFn: reportApi.getReports,
  });

  const summary = summaryResp?.data;
  const kpis = kpisResp?.data;
  const trendPoints = trendsResp?.data?.points || [];
  const services = servicesResp?.data || [];
  const accounts = accountsResp?.data || [];
  const regions = regionsResp?.data || [];
  const optSummary = optSummaryResp?.data;
  const recentReports = (reportsResp?.data || []).slice(0, 4);

  // Top 5 services for charts
  const topServices = services.slice(0, 5);
  const pieData = topServices.map((s) => ({
    name: s.service,
    value: toNumber(s.current_cost),
    color: getServiceColor(s.service),
  }));

  const formatBrowserDate = (dateStr?: string, fallback: string = '') => {
    if (!dateStr) return fallback;
    try {
      const parts = dateStr.split('-');
      if (parts.length === 3) {
        const d = new Date(Date.UTC(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2])));
        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
      }
      return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const formatBrowserDateTime = (dateStr?: string, fallback: string = 'Recently') => {
    if (!dateStr) return fallback;
    try {
      let cleanStr = String(dateStr).trim();
      if (cleanStr.includes(' ') && !cleanStr.includes('T')) {
        cleanStr = cleanStr.replace(' ', 'T');
      }
      // If the string does not have a timezone indicator (Z or +HH:MM/-HH:MM), treat it as UTC
      if (!cleanStr.endsWith('Z') && !/[+-]\d{2}(:\d{2})?$/.test(cleanStr)) {
        cleanStr += 'Z';
      }
      const d = new Date(cleanStr);
      if (isNaN(d.getTime())) return fallback;
      return (
        d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) +
        ' at ' +
        d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit', hour12: true })
      );
    } catch {
      return dateStr;
    }
  };

  const todayFormatted = formatBrowserDate(summary?.today_date, 'Latest Available');
  const yesterdayFormatted = formatBrowserDate(summary?.yesterday_date, 'Prior Day');
  const previousDayFormatted = formatBrowserDate(summary?.previous_day_date, 'Baseline Day');
  const lastSyncTimeFormatted = summary?.last_sync_at 
    ? formatBrowserDateTime(summary.last_sync_at, todayFormatted)
    : 'Never (No accounts)';
  const currentMonthName = new Date().toLocaleDateString(undefined, { month: 'short' });
  const currentMonthYear = new Date().toLocaleDateString(undefined, { month: 'long', year: 'numeric' });

  const hasNoAccounts = summary?.account_context === 'No Accounts Connected' || summary?.account_context === 'No AWS Accounts Connected';

  return (
    <div className="space-y-6">
      {hasNoAccounts && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-amber-900 dark:text-amber-200 text-xs shadow-xs">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0" />
            <div>
              <span className="font-semibold text-sm block sm:inline mr-2">No AWS Accounts Connected</span>
              <span>Connect an AWS account via CloudFormation or IAM Role to start pulling live cost, anomaly, and optimization data.</span>
            </div>
          </div>
          <Link to="/accounts" className="px-3 py-1.5 bg-amber-600 text-white hover:bg-amber-700 font-medium rounded-lg text-xs whitespace-nowrap transition-colors shadow-2xs">
            Connect Account &rarr;
          </Link>
        </div>
      )}

      {/* 1. TOP: Day-over-Day Cost Indicators (Section 9) */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              AWS Cost Overview
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Real-time daily cost comparison, verified against finalized AWS billing intervals
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs">
            <Calendar className="w-3.5 h-3.5 text-blue-500" />
            <span>Scope: <strong className="text-slate-700 dark:text-slate-200 font-semibold">{summary?.account_context || 'All AWS Accounts'}</strong></span>
            <span className="text-slate-300 dark:text-slate-700">|</span>
            <span>Last Synced: <strong className="text-slate-700 dark:text-slate-200 font-semibold">{lastSyncTimeFormatted}</strong></span>
            <span className="text-[10px] uppercase font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-1.5 py-0.5 rounded border border-blue-200 dark:border-blue-900">DB Cache</span>
          </div>
        </div>

        {summaryLoading ? (
          <LoadingSkeleton rows={1} />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Today's / Latest Cost */}
            <KpiCard
              title="Latest Synced Spend"
              dateBadge={todayFormatted}
              value={formatCurrency(summary?.today_cost)}
              diff={formatCurrency(Math.abs(toNumber(summary?.today_vs_yesterday?.difference)))}
              percentage={summary?.today_vs_yesterday?.percentage_change}
              direction={summary?.today_vs_yesterday?.direction}
              subtitle={`vs. ${yesterdayFormatted}`}
              secondaryText="Most recent finalized AWS daily billing record"
              icon={<DollarSign className="w-5 h-5 text-blue-500" />}
            />

            {/* Yesterday's Cost */}
            <KpiCard
              title="Prior Day Spend"
              dateBadge={yesterdayFormatted}
              value={formatCurrency(summary?.yesterday_cost)}
              diff={formatCurrency(Math.abs(toNumber(summary?.yesterday_vs_previous_day?.difference)))}
              percentage={summary?.yesterday_vs_previous_day?.percentage_change}
              direction={summary?.yesterday_vs_previous_day?.direction}
              subtitle={`vs. ${previousDayFormatted}`}
              secondaryText="Day-over-day variance compared to prior baseline"
              icon={<DollarSign className="w-5 h-5 text-indigo-500" />}
            />

            {/* Previous Day Cost */}
            <KpiCard
              title="Baseline Reference Day"
              dateBadge={previousDayFormatted}
              value={formatCurrency(summary?.previous_day_cost)}
              subtitle="Reference Benchmark Day"
              secondaryText="Includes verified AWS Cost Explorer API usage ($1.12)"
              icon={<DollarSign className="w-5 h-5 text-slate-400" />}
            />
          </div>
        )}
      </div>

      {/* 2. SECONDARY METRICS: MTD, Projected, Savings, Tagging (Section 67) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Month-to-Date Spend"
          dateBadge={`1 ${currentMonthName} – ${todayFormatted}`}
          value={formatCurrency(kpis?.month_to_date_spend)}
          subtitle="Cumulative month total"
          icon={<DollarSign className="w-4 h-4 text-emerald-500" />}
        />
        <KpiCard
          title="Projected Month-End"
          dateBadge={`End of ${currentMonthYear}`}
          value={formatCurrency(kpis?.projected_month_end_spend)}
          subtitle="Based on current daily burn rate"
          icon={<ArrowUpRight className="w-4 h-4 text-amber-500" />}
        />
        <KpiCard
          title="Potential Monthly Savings"
          dateBadge="Scanner Recommendations"
          value={formatCurrency(kpis?.potential_monthly_savings)}
          subtitle="Identified across S3, EC2 & RDS"
          icon={<TrendingDown className="w-4 h-4 text-emerald-500" />}
        />
        <KpiCard
          title="Tagging Coverage"
          dateBadge={toNumber(kpis?.month_to_date_spend) > 0 ? `${formatCurrency(kpis?.untagged_spend, 0)} untagged` : 'No resources synced'}
          value={toNumber(kpis?.month_to_date_spend) > 0 ? `${(100 - toNumber(kpis?.untagged_percentage)).toFixed(1)}%` : 'N/A'}
          subtitle="Cost allocation compliance"
          icon={<Tag className="w-4 h-4 text-purple-500" />}
        />
      </div>

      {/* Active Anomalies Alert Banner if any (Section 21) */}
      {(kpis?.anomalies_detected || 0) > 0 && (
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 dark:bg-amber-900/60 text-amber-700 dark:text-amber-300 rounded-lg">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-amber-900 dark:text-amber-200">
                {kpis?.anomalies_detected} Unusual Spend Spikes Detected
              </h4>
              <p className="text-xs text-amber-700 dark:text-amber-400">
                Statistical anomalies flagged in recent EC2 and VPC Data Transfer metrics.
              </p>
            </div>
          </div>
          <a
            href="/alerts"
            className="px-3 py-1.5 text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors"
          >
            Review Anomalies
          </a>
        </div>
      )}

      {/* 3. COST TREND: Interactive Multi-View Chart (Section 11) */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              AWS Spend Trend
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Daily AWS cloud cost evolution over time
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Chart Type Selector */}
            <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 p-1 bg-slate-50 dark:bg-slate-800">
              {(['line', 'bar', 'donut', 'scatter'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setChartType(t)}
                  className={`px-2.5 py-1 text-xs font-semibold rounded-md capitalize transition-colors ${chartType === t
                    ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                    }`}
                >
                  {t}
                </button>
              ))}
            </div>

            {/* Range Selector */}
            <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 p-1 bg-slate-50 dark:bg-slate-800">
              {(['7d', '14d', '30d', '90d', 'mtd', 'custom'] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setTrendRange(r)}
                  className={`px-2.5 py-1 text-xs font-semibold rounded-md uppercase transition-colors ${trendRange === r
                    ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                    }`}
                >
                  {r}
                </button>
              ))}
            </div>

            {/* Custom Date Inputs when range === 'custom' */}
            {trendRange === 'custom' && (
              <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-1 text-xs">
                  <span className="text-slate-500 text-[10px] uppercase font-semibold pl-1">From</span>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="px-2 py-0.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded text-slate-900 dark:text-white"
                  />
                </div>
                <div className="flex items-center gap-1 text-xs">
                  <span className="text-slate-500 text-[10px] uppercase font-semibold">To</span>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="px-2 py-0.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded text-slate-900 dark:text-white"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="h-72 w-full">
          {trendsLoading ? (
            <LoadingSkeleton rows={4} />
          ) : chartType === 'line' ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendPoints} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.5} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                <Tooltip content={<TrendTooltip />} />
                <Line
                  type="monotone"
                  dataKey="total_cost"
                  stroke="#2563eb"
                  strokeWidth={2.5}
                  dot={{ r: 2 }}
                  activeDot={{ r: 6 }}
                  name="Total AWS Spend"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : chartType === 'bar' ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendPoints} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.5} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                <Tooltip content={<TrendTooltip />} />
                <Bar dataKey="total_cost" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Daily Spend" />
              </BarChart>
            </ResponsiveContainer>
          ) : chartType === 'donut' ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={100}
                  paddingAngle={3}
                  label={({ name, percent }) => `${name.slice(0, 15)}... (${(percent * 100).toFixed(0)}%)`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<PieCustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.5} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
                <YAxis dataKey="total_cost" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                <Tooltip content={<ScatterCustomTooltip />} />
                <Scatter name="Cost Point" data={trendPoints} fill="#2563eb" />
              </ScatterChart>
            </ResponsiveContainer>
          )}


        </div>
      </div>

      {/* 4. SERVICE BREAKDOWN & ACCOUNT BREAKDOWN (Section 14 & 15) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Service Cost Breakdown Table */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Top AWS Services
              </h3>
            </div>
            <a href="/services" className="text-xs font-semibold text-blue-600 hover:text-blue-500">
              View All Services →
            </a>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 uppercase font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Service</th>
                  <th className="py-2.5 px-3">Cost</th>
                  <th className="py-2.5 px-3">% of Total</th>
                  <th className="py-2.5 px-3">Change</th>
                  <th className="py-2.5 px-3">Trend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {topServices.map((svc) => (
                  <tr key={svc.service} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-medium flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: getServiceColor(svc.service) }}
                      />
                      <span className="truncate max-w-[200px]" title={svc.service}>
                        {svc.service}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-bold text-slate-900 dark:text-white">
                      {formatCurrency(svc.current_cost)}
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">
                      {toNumber(svc.percentage_of_total).toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center gap-0.5 font-semibold ${svc.trend === 'UP'
                          ? 'text-rose-600 dark:text-rose-400'
                          : svc.trend === 'DOWN'
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-slate-500'
                          }`}
                      >
                        {svc.trend === 'UP' ? '+' : ''}
                        {toNumber(svc.percentage_change).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">
                      {svc.trend === 'UP' && <ArrowUpRight className="w-4 h-4 text-rose-500" />}
                      {svc.trend === 'DOWN' && <ArrowDownRight className="w-4 h-4 text-emerald-500" />}
                      {svc.trend === 'FLAT' && <span className="text-slate-400">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Multi-Account Breakdown */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                AWS Accounts
              </h3>
            </div>
            <a href="/accounts" className="text-xs font-semibold text-blue-600 hover:text-blue-500">
              Details →
            </a>
          </div>

          <div className="space-y-3">
            {accounts.map((acc) => (
              <div
                key={acc.account_id}
                className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-800"
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                    {acc.account_name}
                  </span>
                  <span className="text-xs font-bold text-slate-900 dark:text-white">
                    {formatCurrency(acc.monthly_cost)}
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-blue-600 h-full rounded-full"
                    style={{ width: `${Math.min(100, toNumber(acc.percentage_of_total))}%` }}
                  />
                </div>
                <div className="flex justify-between items-center text-[10px] text-slate-400 mt-1">
                  <span>ID: ...{acc.account_id.slice(-4)}</span>
                  <span>{toNumber(acc.percentage_of_total).toFixed(1)}% of total</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 5. OPTIMIZATION OPPORTUNITIES & RECENT REPORTS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* FinOps Optimization Opportunities */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                FinOps Optimization Opportunities
              </h3>
            </div>
            <a href="/optimization" className="text-xs font-semibold text-blue-600 hover:text-blue-500">
              View All {optSummary?.total_recommendations || 0} Recommendations →
            </a>
          </div>

          <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 rounded-xl border border-emerald-100 dark:border-emerald-900/40 mb-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-emerald-800 dark:text-emerald-300 font-medium">
                Total Identified Potential Monthly Savings
              </p>
              <h4 className="text-2xl font-bold text-emerald-700 dark:text-emerald-400 mt-0.5">
                {formatCurrency(optSummary?.total_monthly_savings)}
                <span className="text-xs font-normal text-emerald-600"> / month</span>
              </h4>
            </div>
            <div className="text-right">
              <span className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">
                Annual Potential
              </span>
              <p className="text-sm font-bold text-emerald-700 dark:text-emerald-400">
                {formatCurrency(optSummary?.total_annual_savings)}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-lg">
              <span className="text-rose-600 font-bold">
                {formatCurrency(optSummary?.by_priority?.HIGH, 0)}
              </span>
              <p className="text-[10px] text-slate-400 mt-0.5 uppercase">High Priority</p>
            </div>
            <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-lg">
              <span className="text-amber-600 font-bold">
                {formatCurrency(optSummary?.by_priority?.MEDIUM, 0)}
              </span>
              <p className="text-[10px] text-slate-400 mt-0.5 uppercase">Medium Priority</p>
            </div>
            <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-lg">
              <span className="text-blue-600 font-bold">
                {formatCurrency(optSummary?.by_confidence?.Observed, 0)}
              </span>
              <p className="text-[10px] text-slate-400 mt-0.5 uppercase">Observed Waste</p>
            </div>
          </div>
        </div>

        {/* Recent Generated Reports */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Recent Executive Reports
              </h3>
            </div>
            <a href="/reports" className="text-xs font-semibold text-blue-600 hover:text-blue-500">
              Manage Reports →
            </a>
          </div>

          <div className="space-y-2.5">
            {recentReports.map((rep) => (
              <div
                key={rep.id}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-xs"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/40 text-blue-600 rounded-md">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h5 className="font-semibold text-slate-900 dark:text-white truncate max-w-[220px]">
                      {rep.name}
                    </h5>
                    <p className="text-[10px] text-slate-400">
                      {rep.format.toUpperCase()} • {(rep.file_size_bytes / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>

                <a
                  href={reportApi.getDownloadUrl(rep.id)}
                  download
                  className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-md transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download</span>
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

