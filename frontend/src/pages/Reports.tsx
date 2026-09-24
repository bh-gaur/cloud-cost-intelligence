import React, { useState, useEffect } from 'react';
import {
  FileBarChart2,
  Download,
  Trash2,
  Plus,
  Clock,
  ShieldCheck,
  X,
  AlertTriangle,
} from 'lucide-react';
import { reportApi } from '../api/reportApi';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { ConfirmModal } from '../components/ConfirmModal';
import type { ReportItem } from '../types';
import { useAuth } from '../context/AuthContext';
import { useDashboardContext } from '../components/Layout';

export const Reports: React.FC = () => {
  const { activeOrg } = useAuth();
  const { accounts } = useDashboardContext();
  const role = activeOrg?.role?.toUpperCase();
  const canCreateReport = role === 'OWNER' || role === 'ADMIN' || role === 'FINOPS_MANAGER' || role === 'ANALYST';
  const canDownloadReport = role === 'OWNER' || role === 'ADMIN' || role === 'FINOPS_MANAGER' || role === 'ANALYST';
  const canDeleteReport = role === 'OWNER' || role === 'ADMIN';

  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<ReportItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Form state
  const [format, setFormat] = useState<'csv' | 'json' | 'html' | 'pdf'>('pdf');
  const [customName, setCustomName] = useState('');
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const res = await reportApi.getReports();
      if (res.success && res.data) {
        setReports(res.data);
      }
    } catch (err) {
      console.error('Failed to fetch reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setGenerating(true);
      const res = await reportApi.generateReport({
        format,
        start_date: startDate,
        end_date: endDate,
        name: customName.trim() || undefined,
      });
      if (res.success) {
        setModalOpen(false);
        setCustomName('');
        await fetchReports();
      }
    } catch (err) {
      console.error('Failed to generate report:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = (report: ReportItem) => {
    const token = localStorage.getItem('access_token');
    const url = reportApi.getDownloadUrl(report.id);

    fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `${report.name || 'cost_report'}.${report.format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(blobUrl);
      })
      .catch((err) => console.error('Download error:', err));
  };

  const confirmDeleteReport = async () => {
    if (!deleteTarget) return;
    try {
      setIsDeleting(true);
      const res = await reportApi.deleteReport(deleteTarget.id);
      if (res.success || (res as any)?.status === 'SUCCESS' || (res as any)?.data) {
        setReports((prev) => prev.filter((r) => r.id !== deleteTarget.id));
        setDeleteTarget(null);
      }
    } catch (err: any) {
      console.error('Delete error:', err);
      alert(err.response?.data?.error?.message || 'Failed to delete report.');
    } finally {
      setIsDeleting(false);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Reports Center</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Generate and download multi-format cost intelligence reports (CSV, JSON, HTML, PDF).
          </p>
        </div>
        {canCreateReport && (
          <button
            onClick={() => setModalOpen(true)}
            disabled={accounts.length === 0}
            title={accounts.length === 0 ? "Connect an AWS account first" : "Generate New Report"}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg font-medium text-sm transition-colors shadow-sm cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Generate New Report
          </button>
        )}
      </div>

      {/* No Accounts Connected Alert */}
      {accounts.length === 0 && (
        <div className="flex items-center gap-3 p-4 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/80 rounded-xl text-amber-800 dark:text-amber-200 text-xs shadow-xs">
          <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0" />
          <div className="flex-1">
            <span className="font-semibold">No AWS Accounts Connected: </span>
            <span>You must connect at least one AWS account before generating or scheduling cost intelligence reports.</span>
          </div>
          <a
            href="/accounts"
            className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-semibold text-xs transition-colors shrink-0"
          >
            Connect Account
          </a>
        </div>
      )}

      {/* Retention Policy Notice */}
      <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl">
        <div className="flex items-center gap-3">
          <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <div className="text-xs">
            <span className="font-semibold text-slate-900 dark:text-white">Retention Policy Active: </span>
            <span className="text-slate-600 dark:text-slate-400">
              Generated reports are retained for 90 days (`REPORT_RETENTION_DAYS=90`) and automatically pruned.
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
          <ShieldCheck className="w-4 h-4" />
          <span>Automated Compliance</span>
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Generated Reports Archive</h2>
          <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-2.5 py-1 rounded-full font-medium">
            {reports.length} Reports
          </span>
        </div>

        {loading ? (
          <div className="p-6">
            <LoadingSkeleton rows={5} />
          </div>
        ) : reports.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={<FileBarChart2 className="w-8 h-8 text-blue-500" />}
              title="No Reports Generated"
              description="Click 'Generate New Report' to produce executive cost summaries or detailed breakdowns."
              actionText="Generate Report"
              onAction={() => setModalOpen(true)}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs uppercase font-medium text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3">Report Name</th>
                  <th className="px-5 py-3">Format</th>
                  <th className="px-5 py-3">Reporting Period</th>
                  <th className="px-5 py-3">Created At</th>
                  <th className="px-5 py-3">File Size</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-xs">
                {reports.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3 font-semibold text-slate-900 dark:text-white">
                      {r.name}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold uppercase ${r.format === 'csv' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' :
                          r.format === 'json' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' :
                            r.format === 'pdf' ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300' :
                              'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300'
                        }`}>
                        {r.format}
                      </span>
                    </td>
                    <td className="px-5 py-3 font-mono text-slate-500 dark:text-slate-400">
                      {r.start_date} → {r.end_date}
                    </td>
                    <td className="px-5 py-3 text-slate-500 dark:text-slate-400">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td className="px-5 py-3 font-mono text-slate-500 dark:text-slate-400">
                      {formatFileSize(r.file_size_bytes)}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${r.status === 'COMPLETED' || r.status === 'completed'
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                          : r.status === 'FAILED' || r.status === 'failed'
                            ? 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
                            : 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                        }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {canDownloadReport && (
                          <button
                            onClick={() => handleDownload(r)}
                            className="p-1.5 text-slate-600 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                            title="Download Report"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                        )}
                        {canDeleteReport && (
                          <button
                            onClick={() => setDeleteTarget(r)}
                            className="p-1.5 text-slate-600 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                            title="Delete Report"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Generate Report Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Generate Cost Report</h3>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleGenerate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Report Custom Name (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Q3 Executive FinOps Summary"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder-slate-400"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Output Format
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {(['csv', 'json', 'html', 'pdf'] as const).map((fmt) => (
                    <button
                      type="button"
                      key={fmt}
                      onClick={() => setFormat(fmt)}
                      className={`py-2 text-xs font-bold uppercase rounded-lg border transition-all ${format === fmt
                          ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                          : 'bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700'
                        }`}
                    >
                      {fmt}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generating}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition-colors"
                >
                  {generating ? 'Generating...' : 'Generate Report'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Report Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={confirmDeleteReport}
        title="Delete Report"
        message={`Are you sure you want to permanently delete '${deleteTarget?.name || 'this report'}'? This action cannot be undone.`}
        confirmText="Delete Report"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
};

