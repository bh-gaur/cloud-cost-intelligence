import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Building2,
  Plus,
  ShieldCheck,
  Copy,
  Check,
  FileCode,
  Download,
  AlertCircle,
  ExternalLink,
  Trash2,
  CheckCircle2,
  X,
  Layers,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { accountApi } from '../api/accountApi';
import { awsApi } from '../api/awsApi';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { ConfirmModal } from '../components/ConfirmModal';
import { formatCurrency } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';

export const Accounts: React.FC = () => {
  const { activeOrg } = useAuth();
  const canManageAccounts = activeOrg?.role === 'OWNER' || activeOrg?.role === 'ADMIN';

  const queryClient = useQueryClient();
  const [isConnectOpen, setIsConnectOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'cfn' | 'tf' | 'manual'>('cfn');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [accountToDisconnect, setAccountToDisconnect] = useState<{ id: string; name: string } | null>(null);

  // Form State
  const [accountName, setAccountName] = useState('');
  const [accountId, setAccountId] = useState('');
  const [roleArn, setRoleArn] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const { data: awsAccountsResp, isLoading: isAwsLoading } = useQuery({
    queryKey: ['awsAccounts'],
    queryFn: awsApi.getAccounts,
  });

  const { data: accountsCostResp, isLoading: isCostLoading } = useQuery({
    queryKey: ['accountsList'],
    queryFn: () => accountApi.getAccounts('30d'),
  });

  const costMap = React.useMemo(() => {
    const map = new Map<string, any>();
    (accountsCostResp?.data || []).forEach((c) => {
      map.set(c.account_id, c);
    });
    return map;
  }, [accountsCostResp]);

  const accounts = (awsAccountsResp?.data || []).map((acc) => {
    const cost = costMap.get(acc.account_id);
    return {
      ...acc,
      monthly_cost: cost?.monthly_cost ?? 0,
      daily_cost: cost?.daily_cost ?? 0,
      status: acc.connection_status || 'CONNECTED',
    };
  });

  const isAccountsLoading = isAwsLoading || isCostLoading;

  const { data: templatesResp } = useQuery({
    queryKey: ['onboardingTemplates', accountId],
    queryFn: async () => {
      const res = await apiClient.get('/aws/onboarding/templates', {
        params: { aws_account_id: accountId || undefined },
      });
      return res.data?.data;
    },
    enabled: isConnectOpen,
  });

  const connectMutation = useMutation({
    mutationFn: async (data: { account_id: string; account_name: string; role_arn: string; external_id: string }) => {
      const res = await apiClient.post('/aws/accounts/connect', data);
      return res.data;
    },
    onSuccess: (res) => {
      setSuccessMsg(res.data?.message || 'AWS Account connected successfully!');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['awsAccounts'] });
      queryClient.invalidateQueries({ queryKey: ['accountsList'] });
      setTimeout(() => {
        setIsConnectOpen(false);
        setSuccessMsg(null);
        setAccountName('');
        setAccountId('');
        setRoleArn('');
      }, 1800);
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.error?.message || err.message || 'Failed to connect AWS Account.');
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: async (accId: string) => {
      const res = await apiClient.delete(`/aws/accounts/${accId}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['awsAccounts'] });
      queryClient.invalidateQueries({ queryKey: ['accountsList'] });
    },
  });
  const externalId = templatesResp?.external_id || '';
  const cfnTemplate = templatesResp?.cloudformation_template;
  const tfTemplate = templatesResp?.terraform_template;
  const manualInstructions = templatesResp?.manual_instructions;

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleDownloadCfn = () => {
    if (!cfnTemplate) return;
    const blob = new Blob([JSON.stringify(cfnTemplate, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cloudcost-scanner-role.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleConnectSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!accountId || !roleArn || !accountName) {
      setErrorMsg('Please fill in all required fields.');
      return;
    }
    connectMutation.mutate({
      account_id: accountId.trim(),
      account_name: accountName.trim(),
      role_arn: roleArn.trim(),
      external_id: externalId,
    });
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Building2 className="w-5 h-5 text-blue-600 dark:text-cyan-400" />
            AWS Multi-Account Management
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Self-service IAM Cross-Account Role onboarding via CloudFormation, Terraform, or STS AssumeRole
          </p>
        </div>

        {canManageAccounts && (
          <button
            onClick={() => {
              setIsConnectOpen(true);
              setErrorMsg(null);
              setSuccessMsg(null);
            }}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 shadow-md shadow-blue-500/20 transition-all cursor-pointer shrink-0"
          >
            <Plus className="w-4 h-4" />
            <span>Connect AWS Account</span>
          </button>
        )}
      </div>

      {/* Account List Grid */}
      {isAccountsLoading ? (
        <LoadingSkeleton rows={4} />
      ) : accounts.length === 0 ? (
        /* Empty State */
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-10 text-center space-y-4 shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-cyan-500/10 text-blue-600 dark:text-cyan-400 flex items-center justify-center mx-auto">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">No AWS Accounts Linked Yet</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Connect your AWS account using a read-only IAM Cross-Account role to enable automatic cost discovery, rightsizing, and FinOps analytics.
            </p>
          </div>
          {canManageAccounts && (
            <button
              onClick={() => setIsConnectOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 rounded-xl transition-colors cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Connect First AWS Account</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {accounts.map((acc: any) => (
            <div
              key={acc.account_id}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 rounded-lg">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                      CONNECTED
                    </span>
                    {canManageAccounts && (
                      <button
                        onClick={() => setAccountToDisconnect({ id: acc.account_id, name: acc.account_name })}
                        title="Disconnect Account"
                        className="p-1 text-slate-400 hover:text-rose-500 transition-colors cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                <h3 className="text-sm font-bold text-slate-900 dark:text-white truncate">
                  {acc.account_name}
                </h3>
                <p className="text-[11px] text-slate-400 font-mono mb-3">ID: {acc.account_id}</p>
                {acc.role_arn && (
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono truncate bg-slate-50 dark:bg-slate-950 p-1.5 rounded border border-slate-100 dark:border-slate-800 mb-3" title={acc.role_arn}>
                    Role: {acc.role_arn}
                  </p>
                )}
              </div>

              <div className="space-y-2 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Monthly Spend:</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {formatCurrency(acc.monthly_cost || 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Daily Average:</span>
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    {formatCurrency(acc.daily_cost || 0)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Connect AWS Account Modal */}
      {isConnectOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative space-y-5 my-8">
            {/* Modal Header */}
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-blue-600 dark:text-cyan-400" />
                  Connect AWS Account
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Deploy a read-only IAM Cross-Account Scanner Role in your AWS account using CloudFormation or Terraform.
                </p>
              </div>
              <button
                onClick={() => setIsConnectOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Alert Messages */}
            {errorMsg && (
              <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
                <span>{errorMsg}</span>
              </div>
            )}
            {successMsg && (
              <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <span>{successMsg}</span>
              </div>
            )}

            {/* Onboarding Steps Tabs */}
            <div className="border-b border-slate-200 dark:border-slate-800 flex gap-2">
              <button
                type="button"
                onClick={() => setActiveTab('cfn')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                  activeTab === 'cfn'
                    ? 'border-blue-600 text-blue-600 dark:border-cyan-400 dark:text-cyan-400'
                    : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-white'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                CloudFormation (Recommended)
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('tf')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                  activeTab === 'tf'
                    ? 'border-blue-600 text-blue-600 dark:border-cyan-400 dark:text-cyan-400'
                    : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-white'
                }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                Terraform Code
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('manual')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
                  activeTab === 'manual'
                    ? 'border-blue-600 text-blue-600 dark:border-cyan-400 dark:text-cyan-400'
                    : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-white'
                }`}
              >
                <Building2 className="w-3.5 h-3.5" />
                Manual IAM Console
              </button>
            </div>

            {/* Tab 1: CloudFormation */}
            {activeTab === 'cfn' && (
              <div className="space-y-3 text-xs bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                <p className="font-semibold text-slate-800 dark:text-slate-200">
                  Step 1: Download CloudFormation template JSON and deploy stack in your AWS Console.
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleDownloadCfn}
                    className="inline-flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-xs cursor-pointer transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Download CFN Template
                  </button>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(JSON.stringify(cfnTemplate, null, 2), 'cfn')}
                    className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-white rounded-lg font-semibold text-xs cursor-pointer transition-colors"
                  >
                    {copiedKey === 'cfn' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedKey === 'cfn' ? 'Copied!' : 'Copy JSON'}
                  </button>
                </div>
              </div>
            )}

            {/* Tab 2: Terraform */}
            {activeTab === 'tf' && (
              <div className="space-y-3 text-xs">
                <p className="font-semibold text-slate-800 dark:text-slate-200">
                  Deploy this HCL snippet in your Terraform repository:
                </p>
                <div className="relative bg-slate-950 text-slate-100 p-3.5 rounded-xl text-[11px] font-mono overflow-x-auto max-h-48 border border-slate-800">
                  <button
                    type="button"
                    onClick={() => copyToClipboard(tfTemplate || '', 'tf')}
                    className="absolute top-2.5 right-2.5 p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md transition-colors cursor-pointer"
                  >
                    {copiedKey === 'tf' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                  <pre>{tfTemplate}</pre>
                </div>
              </div>
            )}

            {/* Tab 3: Manual Setup */}
            {activeTab === 'manual' && (
              <div className="space-y-4 text-xs bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                <div className="space-y-1.5">
                  <p className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-blue-600/10 text-blue-600 dark:text-cyan-400 font-mono text-[11px]">Role Name: CloudCostScannerRole</span>
                  </p>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Create an IAM role named <code className="font-bold text-slate-800 dark:text-slate-200">CloudCostScannerRole</code> in your AWS account and attach the policies below:
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-slate-800 dark:text-slate-200">1. IAM Trust Policy (Custom Trust Policy tab):</span>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(JSON.stringify(manualInstructions?.trust_policy, null, 2), 'trust')}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded font-semibold text-[11px] cursor-pointer"
                    >
                      {copiedKey === 'trust' ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                      {copiedKey === 'trust' ? 'Copied' : 'Copy Trust Policy'}
                    </button>
                  </div>
                  <div className="bg-slate-950 text-slate-100 p-3 rounded-lg text-[11px] font-mono overflow-x-auto max-h-32 border border-slate-800">
                    <pre>{JSON.stringify(manualInstructions?.trust_policy, null, 2)}</pre>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-slate-800 dark:text-slate-200">2. Permissions Policy (Attach Managed: SecurityAudit + ReadOnlyAccess, or Custom Policy):</span>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(JSON.stringify(manualInstructions?.permissions_policy, null, 2), 'perms')}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded font-semibold text-[11px] cursor-pointer"
                    >
                      {copiedKey === 'perms' ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                      {copiedKey === 'perms' ? 'Copied' : 'Copy Permissions Policy'}
                    </button>
                  </div>
                  <div className="bg-slate-950 text-slate-100 p-3 rounded-lg text-[11px] font-mono overflow-x-auto max-h-32 border border-slate-800">
                    <pre>{JSON.stringify(manualInstructions?.permissions_policy, null, 2)}</pre>
                  </div>
                </div>
              </div>
            )}

            {/* Connection Details Form */}
            <form onSubmit={handleConnectSubmit} className="space-y-4 pt-2 border-t border-slate-200 dark:border-slate-800">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    AWS Account Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={accountName}
                    onChange={(e) => setAccountName(e.target.value)}
                    placeholder="e.g. Production AWS Account"
                    className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    AWS Account ID (12 Digits) <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={12}
                    pattern="\d{12}"
                    value={accountId}
                    onChange={(e) => setAccountId(e.target.value)}
                    placeholder="123456789012"
                    className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  CloudCostScannerRole ARN <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={roleArn}
                  onChange={(e) => setRoleArn(e.target.value)}
                  placeholder="arn:aws:iam::123456789012:role/CloudCostScannerRole"
                  className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Tenant External ID (Generated Security Token)
                </label>
                <input
                  type="text"
                  readOnly
                  value={externalId}
                  className="w-full px-3 py-2 text-xs bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-600 dark:text-slate-400 font-mono cursor-not-allowed"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-3">
                <button
                  type="button"
                  onClick={() => setIsConnectOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={connectMutation.isPending}
                  className="px-5 py-2 text-xs font-bold text-white bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 rounded-xl shadow-md transition-all cursor-pointer disabled:opacity-50"
                >
                  {connectMutation.isPending ? 'Verifying STS AssumeRole...' : 'Verify & Connect AWS Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Disconnect Account Confirmation Modal */}
      <ConfirmModal
        isOpen={Boolean(accountToDisconnect)}
        onClose={() => setAccountToDisconnect(null)}
        onConfirm={() => {
          if (accountToDisconnect) {
            disconnectMutation.mutate(accountToDisconnect.id);
            setAccountToDisconnect(null);
          }
        }}
        title="Disconnect AWS Account"
        message={`Are you sure you want to disconnect '${accountToDisconnect?.name || accountToDisconnect?.id}'? Ingestion for this account will stop.`}
        confirmText="Disconnect Account"
        cancelText="Cancel"
        variant="danger"
        isLoading={disconnectMutation.isPending}
      />
    </div>
  );
};

export default Accounts;
