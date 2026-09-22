import React, { useState, useEffect } from 'react';
import {
  Server,
  Database,
  ShieldAlert,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import { adminApi, AuditLogEntry, SystemStatus } from '../api/adminApi';
import { LoadingSkeleton } from '../components/LoadingSkeleton';

export const AdminSystem: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      setRefreshing(true);
      const [sysRes, logsRes] = await Promise.all([
        adminApi.getSystemStatus(),
        adminApi.getAuditLogs(1, 50),
      ]);

      if (sysRes.success && sysRes.data) setStatus(sysRes.data);
      if (logsRes.success && logsRes.data) setAuditLogs(logsRes.data);
    } catch (err) {
      console.error('Failed to load system diagnostics:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">System Diagnostics & Audit Logs</h1>
            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 border border-purple-300 dark:border-purple-800">
              Admin Exclusive
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Runtime system parameters, retention rules, and immutable security audit trails.
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-medium transition-colors shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh Diagnostics
        </button>
      </div>

      {/* System Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-medium">
            <Server className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span>Environment</span>
          </div>
          <p className="text-lg font-bold text-slate-900 dark:text-white mt-1 capitalize">
            {status?.environment || 'Development'}
          </p>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Build v{status?.version || '1.0.0'}
          </p>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-medium">
            <Database className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Database Backend</span>
          </div>
          <p className="text-lg font-bold text-slate-900 dark:text-white mt-1 font-mono text-xs truncate">
            {status?.database_url_masked || 'PostgreSQL / SQLite'}
          </p>
          <div className="flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400 mt-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Connected & Schema Migrated</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-medium">
            {status?.demo_mode ? (
              <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            )}
            <span>Data Ingestion Mode</span>
          </div>
          <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            {status?.demo_mode ? 'Active (Demo Mode)' : 'Live AWS'}
          </p>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            {status?.demo_mode ? 'Deterministic synthetic telemetry' : 'Real AWS Cost Explorer API'}
          </p>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-xs font-medium">
            <Server className="w-4 h-4 text-purple-600 dark:text-purple-400" />
            <span>Retention Period</span>
          </div>
          <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            {status?.report_retention_days ?? 90} Days
          </p>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Automated artifact pruning enabled
          </p>
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Security & Audit Event Log</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Immutable record of authentication, optimization actions, reports, and administrative operations.
            </p>
          </div>
          <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-2.5 py-1 rounded-full font-medium">
            {auditLogs.length} Events Logged
          </span>
        </div>

        {loading ? (
          <div className="p-6">
            <LoadingSkeleton rows={5} />
          </div>
        ) : auditLogs.length === 0 ? (
          <div className="p-8 text-center text-slate-500 dark:text-slate-400 text-sm">
            No audit log entries found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs uppercase font-medium text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3">Timestamp</th>
                  <th className="px-5 py-3">User</th>
                  <th className="px-5 py-3">Action</th>
                  <th className="px-5 py-3">Resource</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">IP Address</th>
                  <th className="px-5 py-3">Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-xs font-mono">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3 whitespace-nowrap text-slate-500 dark:text-slate-400">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-5 py-3 text-slate-900 dark:text-white font-sans">
                      {log.user_email || 'System / Anonymous'}
                    </td>
                    <td className="px-5 py-3">
                      <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-semibold text-[11px]">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-600 dark:text-slate-300">
                      {log.resource_type} {log.resource_id ? `#${log.resource_id}` : ''}
                    </td>
                    <td className="px-5 py-3 font-sans">
                      <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${log.status === 'success' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' :
                          log.status === 'failure' ? 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300' :
                            'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300'
                        }`}>
                        {log.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-500 dark:text-slate-400">
                      {log.ip_address || '127.0.0.1'}
                    </td>
                    <td className="px-5 py-3 text-slate-500 dark:text-slate-400 font-mono text-[10px] max-w-xs truncate">
                      {log.details ? JSON.stringify(log.details) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

