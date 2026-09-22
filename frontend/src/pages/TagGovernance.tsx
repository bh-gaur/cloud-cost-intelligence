import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Tag,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  Copy,
  Check,
  Terminal,
  FileCode,
  Search,
  Filter,
  Sparkles,
  X,
  Layers,
  HardDrive,
  Database,
  Cpu,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { useDashboardContext } from '../components/Layout';
import { taggingApi, UntaggedResource } from '../api/taggingApi';
import { KpiCard } from '../components/KpiCard';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { formatCurrency, toNumber } from '../utils/formatters';

export const TagGovernance: React.FC = () => {
  const { selectedAccount } = useDashboardContext();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedService, setSelectedService] = useState('ALL');
  const [selectedMissingTag, setSelectedMissingTag] = useState('ALL');

  // Remediation Modal State
  const [activeRemediation, setActiveRemediation] = useState<UntaggedResource | null>(null);
  const [customTagValues, setCustomTagValues] = useState<Record<string, string>>({});
  const [copiedType, setCopiedType] = useState<'cli' | 'tf' | null>(null);
  const [activeTab, setActiveTab] = useState<'cli' | 'tf'>('cli');

  const { data: govResp, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['tagGovernance', selectedAccount],
    queryFn: () => taggingApi.getGovernance(selectedAccount),
  });

  const data = govResp?.data;
  const overallScore = toNumber(data?.overall_compliance_percentage);
  const untaggedSpend = toNumber(data?.untagged_spend);
  const totalSpend = toNumber(data?.total_spend);
  const untaggedResources = data?.resources || [];
  const serviceBreakdowns = data?.service_breakdowns || [];
  const missingByKey = data?.missing_by_tag_key || {};
  const requiredTags = data?.required_tags || ['Environment', 'Owner', 'Project', 'Team'];

  // Filter resources
  const filteredResources = useMemo(() => {
    return untaggedResources.filter((res) => {
      const matchesSearch =
        searchQuery === '' ||
        res.resource_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        res.resource_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        res.service.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesService =
        selectedService === 'ALL' ||
        res.service.toLowerCase().includes(selectedService.toLowerCase());

      const matchesMissingTag =
        selectedMissingTag === 'ALL' ||
        res.missing_tags.includes(selectedMissingTag);

      return matchesSearch && matchesService && matchesMissingTag;
    });
  }, [untaggedResources, searchQuery, selectedService, selectedMissingTag]);

  const openRemediationModal = (res: UntaggedResource) => {
    setActiveRemediation(res);
    const initialTags: Record<string, string> = {};
    res.missing_tags.forEach((t) => {
      if (t === 'Environment') initialTags[t] = 'production';
      else if (t === 'Owner') initialTags[t] = 'finops-team';
      else initialTags[t] = `default-${t.toLowerCase()}`;
    });
    setCustomTagValues(initialTags);
  };

  const handleCopy = (text: string, type: 'cli' | 'tf') => {
    navigator.clipboard.writeText(text);
    setCopiedType(type);
    setTimeout(() => setCopiedType(null), 2000);
  };

  // Dynamically generate CLI and Terraform code in the modal based on custom tag inputs
  const dynamicCli = useMemo(() => {
    if (!activeRemediation) return '';
    const svc = activeRemediation.service.toLowerCase();
    const tagArgs = Object.entries(customTagValues)
      .map(([k, v]) => `Key=${k},Value=${v}`)
      .join(' ');

    if (svc.includes('s3') || svc.includes('bucket')) {
      const tagSet = Object.entries(customTagValues)
        .map(([k, v]) => `{Key=${k},Value=${v}}`)
        .join(',');
      return `aws s3api put-bucket-tagging --bucket ${activeRemediation.resource_id} --tagging 'TagSet=[${tagSet}]' --region ${activeRemediation.region}`;
    } else if (svc.includes('rds')) {
      return `aws rds add-tags-to-resource --resource-name ${activeRemediation.resource_id} --tags ${tagArgs} --region ${activeRemediation.region}`;
    } else {
      return `aws ec2 create-tags --resources ${activeRemediation.resource_id} --tags ${tagArgs} --region ${activeRemediation.region}`;
    }
  }, [activeRemediation, customTagValues]);

  const dynamicTf = useMemo(() => {
    if (!activeRemediation) return '';
    const lines = ['  tags = {'];
    Object.entries(customTagValues).forEach(([k, v]) => {
      lines.push(`    "${k}" = "${v}"`);
    });
    lines.push('  }');
    return `# Add inside the ${activeRemediation.resource_type} block:\n${lines.join('\n')}`;
  }, [activeRemediation, customTagValues]);

  const getServiceIcon = (service: string) => {
    const s = service.toLowerCase();
    if (s.includes('s3') || s.includes('bucket')) return <Database className="w-4 h-4 text-emerald-500" />;
    if (s.includes('ec2') || s.includes('compute')) return <Cpu className="w-4 h-4 text-amber-500" />;
    if (s.includes('ebs') || s.includes('volume')) return <HardDrive className="w-4 h-4 text-purple-500" />;
    if (s.includes('rds') || s.includes('aurora')) return <Database className="w-4 h-4 text-blue-500" />;
    return <Layers className="w-4 h-4 text-slate-400" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Tag Governance & Explorer
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-cyan-400 border border-blue-200 dark:border-blue-800">
              Policy Compliance
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Enforce mandatory cost allocation tags across AWS infrastructure and remediate untagged spend.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-xl transition-all shadow-2xs cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-blue-500' : ''}`} />
          <span>{isFetching ? 'Scanning Tags...' : 'Refresh Tags'}</span>
        </button>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={3} />
      ) : (
        <>
          {/* Top Scorecard KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              title="Tagging Coverage"
              value={`${overallScore.toFixed(1)}%`}
              subtitle={`${(100 - overallScore).toFixed(1)}% untagged gap`}
              icon={<Tag className="w-5 h-5 text-purple-500" />}
            />
            <KpiCard
              title="Untagged Monthly Spend"
              value={formatCurrency(untaggedSpend)}
              subtitle={`Out of ${formatCurrency(totalSpend)} total`}
              icon={<ShieldAlert className="w-5 h-5 text-rose-500" />}
            />
            <KpiCard
              title="Untagged Cloud Resources"
              value={`${data?.untagged_resources_count || 0}`}
              subtitle={`From ${data?.total_resources || 0} total evaluated`}
              icon={<HardDrive className="w-5 h-5 text-amber-500" />}
            />
            <KpiCard
              title="Required Policy Tags"
              value={`${requiredTags.length}`}
              subtitle={requiredTags.join(', ')}
              icon={<ShieldCheck className="w-5 h-5 text-emerald-500" />}
            />
          </div>

          {/* Missing Tags Heatmap Bar */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Filter className="w-4 h-4 text-blue-500" />
                Missing Tags by Policy Key
              </h3>
              <span className="text-xs text-slate-400">Click a tag to filter resources</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {requiredTags.map((key) => {
                const count = missingByKey[key] || 0;
                const isSelected = selectedMissingTag === key;
                return (
                  <button
                    key={key}
                    onClick={() => setSelectedMissingTag(isSelected ? 'ALL' : key)}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/40 shadow-xs'
                        : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                        {key}
                      </span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          count > 0
                            ? 'bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400'
                            : 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400'
                        }`}
                      >
                        {count > 0 ? `${count} missing` : '100% compliant'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                      Mandatory FinOps classification
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Service Compliance Breakdown */}
          {serviceBreakdowns.length > 0 && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-500" />
                Tagging Compliance by AWS Service
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {serviceBreakdowns.map((sb) => {
                  const pct = toNumber(sb.compliance_percentage);
                  return (
                    <div
                      key={sb.service}
                      className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/60 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getServiceIcon(sb.service)}
                          <span className="text-xs font-bold text-slate-900 dark:text-white truncate max-w-[140px]">
                            {sb.service}
                          </span>
                        </div>
                        <span
                          className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                            pct >= 80
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                              : pct >= 50
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                              : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                          }`}
                        >
                          {pct.toFixed(1)}%
                        </span>
                      </div>

                      <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-rose-500'
                          }`}
                          style={{ width: `${Math.min(pct, 100)}%` }}
                        />
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                        <span>
                          Untagged: <strong className="text-slate-700 dark:text-slate-300">{sb.untagged_resources}</strong> / {sb.total_resources}
                        </span>
                        <span>
                          At Risk: <strong className="text-rose-600 dark:text-rose-400">{formatCurrency(sb.untagged_spend)}</strong>
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Filterable Untagged Resource Explorer Table */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-rose-500" />
                  Untagged Resource Explorer
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Showing {filteredResources.length} of {untaggedResources.length} resources requiring tag remediation
                </p>
              </div>

              {/* Filters */}
              <div className="flex flex-wrap items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by ID or name..."
                    className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 w-44 sm:w-56"
                  />
                </div>

                <select
                  value={selectedService}
                  onChange={(e) => setSelectedService(e.target.value)}
                  className="px-2.5 py-1.5 text-xs font-semibold bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-700 dark:text-slate-300 focus:outline-none"
                >
                  <option value="ALL">All Services</option>
                  {serviceBreakdowns.map((s) => (
                    <option key={s.service} value={s.service}>
                      {s.service}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {filteredResources.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={<ShieldCheck className="w-8 h-8 text-emerald-500" />}
                  title="No Untagged Resources Found"
                  description="All evaluated infrastructure matches your required tagging policy filters."
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-50/80 dark:bg-slate-800/60 uppercase font-semibold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="px-5 py-3">Resource Name / ID</th>
                      <th className="px-5 py-3">Service & Region</th>
                      <th className="px-5 py-3">Missing Policy Tags</th>
                      <th className="px-5 py-3 text-right">Est. Monthly Spend</th>
                      <th className="px-5 py-3 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {filteredResources.map((res) => (
                      <tr
                        key={res.resource_id}
                        className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors"
                      >
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-2">
                            {getServiceIcon(res.service)}
                            <div>
                              <div className="font-bold text-slate-900 dark:text-white font-mono text-xs truncate max-w-xs" title={res.resource_name}>
                                {res.resource_name}
                              </div>
                              <div className="text-[11px] text-slate-400 font-mono">
                                {res.resource_id}
                              </div>
                            </div>
                          </div>
                        </td>

                        <td className="px-5 py-3.5">
                          <div className="font-semibold text-slate-800 dark:text-slate-200">
                            {res.service}
                          </div>
                          <div className="text-[11px] text-slate-400">
                            {res.region} • Account {res.account_id.slice(-4)}
                          </div>
                        </td>

                        <td className="px-5 py-3.5">
                          <div className="flex flex-wrap gap-1">
                            {res.missing_tags.map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-0.5 rounded-md font-bold text-[10px] bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900/60"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </td>

                        <td className="px-5 py-3.5 text-right font-bold text-slate-900 dark:text-white">
                          {formatCurrency(res.monthly_spend)}
                        </td>

                        <td className="px-5 py-3.5 text-center">
                          <button
                            onClick={() => openRemediationModal(res)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-blue-600 dark:text-cyan-400 bg-blue-50 dark:bg-blue-950/50 hover:bg-blue-100 dark:hover:bg-blue-900/50 rounded-lg border border-blue-200 dark:border-blue-900/80 transition-all cursor-pointer"
                          >
                            <Terminal className="w-3.5 h-3.5" />
                            <span>Remediate</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* 1-Click Remediation Code Modal */}
      {activeRemediation && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-blue-600 dark:text-cyan-400" />
                  Tag Remediation Generator
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                  {activeRemediation.resource_name} ({activeRemediation.service})
                </p>
              </div>
              <button
                onClick={() => setActiveRemediation(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Custom Tag Inputs */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
                Define Values for Missing Tags:
              </label>
              <div className="grid grid-cols-2 gap-2">
                {activeRemediation.missing_tags.map((tagKey) => (
                  <div key={tagKey} className="space-y-1">
                    <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                      {tagKey}
                    </span>
                    <input
                      type="text"
                      value={customTagValues[tagKey] || ''}
                      onChange={(e) =>
                        setCustomTagValues((prev) => ({
                          ...prev,
                          [tagKey]: e.target.value,
                        }))
                      }
                      className="w-full px-2.5 py-1.5 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-900 dark:text-white font-mono"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Code Toggle Tabs */}
            <div className="space-y-2">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setActiveTab('cli')}
                    className={`px-3 py-1.5 text-xs font-bold border-b-2 transition-all cursor-pointer ${
                      activeTab === 'cli'
                        ? 'border-blue-500 text-blue-600 dark:text-cyan-400'
                        : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
                    }`}
                  >
                    AWS CLI Command
                  </button>
                  <button
                    onClick={() => setActiveTab('tf')}
                    className={`px-3 py-1.5 text-xs font-bold border-b-2 transition-all cursor-pointer ${
                      activeTab === 'tf'
                        ? 'border-blue-500 text-blue-600 dark:text-cyan-400'
                        : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
                    }`}
                  >
                    Terraform HCL
                  </button>
                </div>

                <button
                  onClick={() => handleCopy(activeTab === 'cli' ? dynamicCli : dynamicTf, activeTab)}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 dark:text-cyan-400 hover:underline cursor-pointer"
                >
                  {copiedType === activeTab ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      <span className="text-emerald-500">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Code</span>
                    </>
                  )}
                </button>
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl overflow-x-auto text-xs font-mono text-emerald-400">
                <pre>{activeTab === 'cli' ? dynamicCli : dynamicTf}</pre>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setActiveRemediation(null)}
                className="px-4 py-2 text-xs font-bold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-xl transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TagGovernance;
