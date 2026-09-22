import React, { useState } from 'react';
import {
  Cloud,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Send,
  Server,
  MessageSquare
} from 'lucide-react';
import { awsApi } from '../api/awsApi';
import { notificationApi } from '../api/notificationApi';

export const Integrations: React.FC = () => {
  // AWS Connection state
  const [awsAccountId, setAwsAccountId] = useState('123456789012');
  const [awsRoleArn, setAwsRoleArn] = useState('arn:aws:iam::123456789012:role/CostIntelligenceRole');
  const [awsRegion, setAwsRegion] = useState('us-east-1');
  const [testingAws, setTestingAws] = useState(false);
  const [awsTestResult, setAwsTestResult] = useState<{ success: boolean; message: string } | null>(null);

  // Notification testing states
  const [testingChannel, setTestingChannel] = useState<string | null>(null);
  const [channelResults, setChannelResults] = useState<Record<string, { success: boolean; message: string }>>({});

  const handleTestAws = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setTestingAws(true);
      setAwsTestResult(null);
      const res = await awsApi.testConnection({
        account_id: awsAccountId,
        role_arn: awsRoleArn,
        region: awsRegion,
      });

      if (res.success && res.data) {
        setAwsTestResult({
          success: res.data.is_connected,
          message: res.data.status_message || (res.data.is_connected ? 'Successfully verified STS AssumeRole & Cost Explorer permissions' : 'Connection failed'),
        });
      } else {
        setAwsTestResult({
          success: false,
          message: (res.error as any)?.message || 'Connection failed',
        });
      }
    } catch (err: any) {
      setAwsTestResult({
        success: false,
        message: err.message || 'Error executing connection test',
      });
    } finally {
      setTestingAws(false);
    }
  };

  const handleTestChannel = async (channel: string) => {
    try {
      setTestingChannel(channel);
      const res = await notificationApi.testChannel({ channel_type: channel });
      setChannelResults((prev) => ({
        ...prev,
        [channel]: {
          success: res.success && (res.data?.success ?? true),
          message: res.data?.message || (res.success ? `Test payload delivered successfully to ${channel}` : ((res.error as any)?.message || 'Failed to deliver test payload')),
        },
      }));
    } catch (err: any) {
      setChannelResults((prev) => ({
        ...prev,
        [channel]: {
          success: false,
          message: err.message || 'Delivery error',
        },
      }));
    } finally {
      setTestingChannel(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Cloud & Notification Integrations</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Manage cloud provider credentials, IAM cross-account assume roles, and automated alerting webhooks.
        </p>
      </div>

      {/* Cloud Providers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AWS Active Provider */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-amber-500/10 text-amber-500 rounded-xl">
                <Cloud className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">Amazon Web Services (AWS)</h2>
                  <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                    Active Provider
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Cost Explorer, AWS Budgets, CloudWatch Metrics, and Anomaly Detection integration
                </p>
              </div>
            </div>
          </div>

          <form onSubmit={handleTestAws} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  AWS Account ID
                </label>
                <input
                  type="text"
                  value={awsAccountId}
                  onChange={(e) => setAwsAccountId(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white font-mono"
                  placeholder="12-digit AWS Account ID"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Default Region
                </label>
                <select
                  value={awsRegion}
                  onChange={(e) => setAwsRegion(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white"
                >
                  <option value="us-east-1">US East (N. Virginia) [us-east-1]</option>
                  <option value="us-west-2">US West (Oregon) [us-west-2]</option>
                  <option value="eu-west-1">EU (Ireland) [eu-west-1]</option>
                  <option value="eu-central-1">EU (Frankfurt) [eu-central-1]</option>
                  <option value="ap-southeast-1">Asia Pacific (Singapore) [ap-southeast-1]</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                IAM Cross-Account Role ARN
              </label>
              <input
                type="text"
                value={awsRoleArn}
                onChange={(e) => setAwsRoleArn(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white font-mono"
                placeholder="arn:aws:iam::123456789012:role/CostIntelligenceRole"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <button
                type="submit"
                disabled={testingAws}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${testingAws ? 'animate-spin' : ''}`} />
                {testingAws ? 'Validating STS & Permissions...' : 'Test AWS Connection'}
              </button>

              {awsTestResult && (
                <div className={`flex items-center gap-2 text-xs font-medium ${awsTestResult.success ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                  {awsTestResult.success ? (
                    <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 flex-shrink-0" />
                  )}
                  <span>{awsTestResult.message}</span>
                </div>
              )}
            </div>
          </form>
        </div>

        {/* Multi-Cloud Provider Abstraction Note */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-500/10 text-blue-500 rounded-xl">
                <Server className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-base">Multi-Cloud Provider Abstraction</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">Extensible architectural design</p>
              </div>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              The backend leverages the <code className="px-1 py-0.5 bg-slate-100 dark:bg-slate-800 rounded">BaseCostProvider</code> abstraction interface.
              Google Cloud Platform (GCP BigQuery billing export) and Microsoft Azure (Cost Management API) adapters can be mounted seamlessly without touching the reporting, alerting, or visualization engines.
            </p>
          </div>

          <div className="mt-6 space-y-2 text-xs">
            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Microsoft Azure</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400 font-bold uppercase">Planned</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Google Cloud (GCP)</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400 font-bold uppercase">Planned</span>
            </div>
          </div>
        </div>
      </div>

      {/* Notification Webhooks & Channels */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Alert Dispatch Channels</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Dispatch real-time anomaly alerts and weekly cost summaries across enterprise collaboration tools.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { id: 'email', name: 'Email / SMTP', desc: 'Alert notifications via authenticated SMTP or Amazon SES.' },
            { id: 'slack', name: 'Slack Webhook', desc: 'Interactive Block Kit cost alerts dispatched to #finops-alerts.' },
            { id: 'teams', name: 'Microsoft Teams', desc: 'Adaptive Card notifications for executive engineering channels.' },
            { id: 'google_chat', name: 'Google Chat', desc: 'Structured JSON Card v2 notifications for Google Workspace.' },
          ].map((channel) => (
            <div
              key={channel.id}
              className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl flex flex-col justify-between bg-slate-50/40 dark:bg-slate-900/40 space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  <h3 className="font-semibold text-sm text-slate-900 dark:text-white">{channel.name}</h3>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{channel.desc}</p>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => handleTestChannel(channel.id)}
                  disabled={testingChannel === channel.id}
                  className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 transition-colors shadow-sm disabled:opacity-50"
                >
                  <Send className={`w-3.5 h-3.5 ${testingChannel === channel.id ? 'animate-bounce' : ''}`} />
                  {testingChannel === channel.id ? 'Dispatching...' : 'Send Test Alert'}
                </button>

                {channelResults[channel.id] && (
                  <p className={`text-[11px] text-center font-medium ${channelResults[channel.id].success ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
                    }`}>
                    {channelResults[channel.id].message}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
